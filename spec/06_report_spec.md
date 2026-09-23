# 06 · Report Specification

**Version:** 1.0 · **Date:** 2026-09-23
**Parent:** [00_overview.md](./00_overview.md) · **Consumed by:** [07_agent_spec.md](./07_agent_spec.md), [08_test_plan.md](./08_test_plan.md)

---

## 0. The answer, first

> **The reports are the cheapest thing in the entire build and the thing most likely to close the sale, because they convert a capability into an operating rhythm. Three queries and three templates over a table that already exists.**

---

## 1. The three-tier rhythm

| Cadence | Audience | Question it answers | Content |
|---|---|---|---|
| **Daily** | Asset Manager | *"What changed overnight and what needs my signature today?"* | New triggers fired, drafts awaiting review, ranking movements, cleared blockers |
| **Weekly** | Asset Manager + Surface Manager + Rig coordinator | *"What is the rig doing for the next 14 days, and what is slipping?"* | 14-day rig-requiring schedule, parallel rigless queue, slipping jobs, review activity |
| **Monthly** | **Basin Manager / Executive Director** | *"Is this asset being worked in the right order, and is the system earning its place?"* | **Failures per well per year**, **mean run-life between interventions**, rigless share of interventions, decline-arrest barrels, throughput, outcome vs predicted, where the system was wrong, engineer overrides, job mix |

**Three governing rules keep the rhythm honest:**

1. **Nothing is recomputed for a report.** Weekly and monthly reports are aggregations of the same nightly `well_run` and `decision_log` runs. If the monthly scorecard disagrees with the sum of the dailies, that is a bug, not a reconciliation.
2. **Daily is a queue, weekly is a plan, monthly is a scorecard.** The monthly scorecard must not be allowed to become a longer weekly report because it is the only artefact that looks backwards and grades the system.
3. **The monthly scorecard must show where the system was wrong.** A system that only reports its wins gets read once.

---

## 2. Daily report

The daily report surfaces changes since the previous nightly run and the immediate actions required.

### 2.1 Specification

| ID | Field Name | Source / Derivation | Format / Rule |
|---|---|---|---|
| `RS-001` | **New triggers fired overnight** | `well_run.trigger_a/b/c/d` | Wells with a trigger today but not yesterday. |
| `RS-002` | **Drafts awaiting review** | `well_run` joined with `decision_log` | Grouped by `queue` ('RIG' vs 'RIGLESS'). Count of drafts not yet decided. |
| `RS-003` | **Ranking movements** | `well_run.rank_overall` | Wells that moved up in rank between yesterday and today. |
| `RS-004` | **Cleared blockers** | `well_run.logistics_blocker` (Requires Schema Addition) | Wells where `logistics_blocker` was NOT NULL yesterday and IS NULL today. |

### 2.2 SQL (BigQuery)

```sql
-- Daily Report: New triggers, ranking movements, cleared blockers
WITH yesterday AS (
  SELECT well_id, trigger_a, trigger_b, trigger_c, trigger_d, rank_overall, logistics_blocker
  FROM `project.dataset.well_run`
  WHERE run_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
),
today AS (
  SELECT well_id, trigger_a, trigger_b, trigger_c, trigger_d, rank_overall, logistics_blocker, queue, recommended_job_code
  FROM `project.dataset.well_run`
  WHERE run_date = CURRENT_DATE()
)
SELECT 
  t.well_id,
  t.queue,
  t.recommended_job_code,
  -- New triggers
  (t.trigger_a IS NOT NULL AND y.trigger_a IS NULL) OR
  (t.trigger_b = TRUE AND (y.trigger_b = FALSE OR y.trigger_b IS NULL)) OR
  (t.trigger_c IS NOT NULL AND y.trigger_c IS NULL) OR
  (t.trigger_d = TRUE AND (y.trigger_d = FALSE OR y.trigger_d IS NULL)) AS is_new_trigger,
  -- Ranking movement
  (y.rank_overall - t.rank_overall) AS spots_moved_up,
  -- Cleared blockers
  (y.logistics_blocker IS NOT NULL AND t.logistics_blocker IS NULL) AS blocker_cleared
FROM today t
LEFT JOIN yesterday y ON t.well_id = y.well_id
WHERE 
  -- Filter for only the things we want to show
  (t.trigger_a IS NOT NULL OR t.trigger_b = TRUE OR t.trigger_c IS NOT NULL OR t.trigger_d = TRUE)
ORDER BY t.rank_overall;

-- Drafts awaiting review
SELECT 
  w.queue,
  COUNT(w.well_id) as awaiting_count
FROM `project.dataset.well_run` w
LEFT JOIN `project.dataset.decision_log` d 
  ON w.well_id = d.well_id AND w.run_date = d.run_date
WHERE w.run_date = CURRENT_DATE()
  AND w.queue IN ('RIG', 'RIGLESS')
  AND d.decision_id IS NULL
GROUP BY w.queue;
```

### 2.3 ASCII Mockup

```text
DAILY INTERVENTION BRIEF — Geleki · 23 Sep 2026 · 06:00

NEW OVERNIGHT                3 wells
  GK-112  trigger A fired  ·  38% below own decline, day 9  ·  DRAFT READY
  GK-147  trigger C fired  ·  THP +14% over 6 d, wax        ·  DRAFT READY
  GK-088  trigger B fired  ·  run-life p50 exceeded         ·  DRAFT READY

AWAITING YOUR REVIEW         7 drafts   (2 rig · 5 rigless)
MOVED UP THE RANKING         GK-129  #5 → #2  (water cut +4 pts in 48 h)
BLOCKER CLEARED              GK-177  5½" retainer arrived Nazira — schedulable
```

---

## 3. Weekly report

The weekly report focuses on forward planning and rig capacity utilisation.

### 3.1 Specification

| ID | Field Name | Source / Derivation | Format / Rule |
|---|---|---|---|
| `RS-010` | **14-day rig schedule** | Scheduled jobs from external rig calendar / planner state | Grouped by Rig ID, visualised as a Gantt-style bar. |
| `RS-011` | **Parallel rigless queue** | `well_run.queue = 'RIGLESS'` + `decision_log` | **Consumes zero rig-days and is the commercially important part.** Grouped by job category. |
| `RS-012` | **Slipping jobs** | External scheduler state or un-cleared blockers | Jobs deferred with reasons (e.g., materials, offset analysis). |
| `RS-013` | **Review activity counts** | `decision_log` over last 7 days | Counts of APPROVE/MODIFY/REJECT with summarized reasons. |
| `RS-014` | **Invariant: Capacity constraint** | System validation | **Committed rig-days must never exceed available rig-days.** |

### 3.2 SQL (BigQuery)

```sql
-- Rigless Queue (Approved but not yet executed)
SELECT 
  w.recommended_job_code,
  STRING_AGG(w.well_id, ', ') AS wells,
  COUNT(w.well_id) AS job_count
FROM `project.dataset.well_run` w
JOIN `project.dataset.decision_log` d 
  ON w.well_id = d.well_id AND w.run_date = d.run_date
WHERE w.run_date = CURRENT_DATE()
  AND w.queue = 'RIGLESS'
  AND d.decision = 'APPROVE'
GROUP BY w.recommended_job_code;

-- Review Activity
SELECT 
  decision,
  COUNT(*) AS count,
  ARRAY_AGG(reason_text IGNORE NULLS LIMIT 2) AS sample_reasons
FROM `project.dataset.decision_log`
WHERE decided_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY decision;
```

### 3.3 ASCII Mockup

```text
WEEKLY INTERVENTION PLAN — Geleki · week of 05 Oct 2026
────────────────────────────────────────────────────────────────────
RIG-REQUIRING                              WO-7        WO-3
  Mon 05   GK-129  cement squeeze + reperf  ████████
  Thu 08   GK-204  pump changeout                      ████
  Fri 09   GK-118  rod string repair                   ██████
  committed rig-days 14 of 14 available     ⚠ no slack

RIGLESS — parallel, no rig contention                    9 jobs
  hot oil / scraper        GK-133, GK-147, GK-151, GK-162
  scale squeeze (CT)       GK-109, GK-188
  choke adjustment         GK-171, GK-193
  surface / prime mover    GK-206

SLIPPING                                                 2 jobs
  GK-141   deferred — offsets confirm reservoir decline, no job justified
  GK-177   blocked  — 5½" retainer, Sivasagar transit, ETA 10-11

REVIEW ACTIVITY (last 7 d)   approved 11 · modified 3 · rejected 2
  rejection reasons: "workover due on GK-155 anyway, combine" ×1
                     "water source is injector breakthrough" ×1
```

---

## 4. Monthly ED scorecard

This is the most important section in your document. It grades the system.

### 4.1 Specification

| ID | Field Name | Source / Derivation | Format / Rule |
|---|---|---|---|
| `RS-020` | **Throughput** | `workover_history` | Jobs completed split by rig/rigless. Total rig-days consumed. Mean days from flagged to executed. Each with a 3-month average and trend arrow. |
| `RS-021` | **Outcome** | `well_run` vs `workover_history` | **Failures per well per year** and **mean run-life between interventions** lead — these are the two headline KPIs and ONGC's own WRFM reporting already uses them. Then rigless share of interventions, then decline-arrest barrels with method referenced. Post-job uplift vs predicted, count within tolerance. Jobs that failed to deliver and resulting `P(success)` recalibration. **Deferred barrels per rig-day is the internal ranking objective in `rank_candidates()` and must not be surfaced here as a headline metric.** |
| `RS-022` | **Where the system was wrong** | Cross-join `well_run`, `decision_log`, `workover_history` | False positives with root cause attribution. Missed failures with whether a precursor existed. What was changed as a result. See §5. |
| `RS-023` | **Engineer overrides** | `decision_log` | Counts of REJECT and MODIFY. Most common reason category and whether it implies a value function change. |
| `RS-024` | **Job mix** | `workover_history` | Mix of job categories executed, with deviation from expected taxonomy. |

### 4.2 SQL (BigQuery)

```sql
-- Throughput and Job Mix
SELECT 
  COUNT(w.workover_id) AS jobs_completed,
  SUM(CAST(w.is_rigless AS INT64)) AS rigless_count,
  SUM(CAST(NOT w.is_rigless AS INT64)) AS rig_count,
  SUM(w.rig_days) AS total_rig_days_consumed,
  j.category,
  COUNT(w.workover_id) / SUM(COUNT(w.workover_id)) OVER() AS mix_pct
FROM `project.dataset.workover_history` w
JOIN `project.dataset.job_catalogue` j ON w.job_code = j.job_code
WHERE DATE_TRUNC(w.end_date, MONTH) = DATE_TRUNC(CURRENT_DATE(), MONTH)
GROUP BY j.category;

-- Outcome: Uplift accuracy
WITH jobs AS (
  SELECT 
    w.well_id,
    w.uplift_bopd AS actual_uplift,
    r.expected_oil_bopd,
    r.net_value
  FROM `project.dataset.workover_history` w
  JOIN `project.dataset.well_run` r 
    ON w.well_id = r.well_id 
    AND r.run_date = (SELECT MAX(run_date) FROM `project.dataset.well_run` WHERE well_id = w.well_id AND recommended_job_code = w.job_code)
  WHERE DATE_TRUNC(w.end_date, MONTH) = DATE_TRUNC(CURRENT_DATE(), MONTH)
)
SELECT 
  AVG(actual_uplift) AS mean_actual_uplift,
  COUNTIF(ABS(actual_uplift - expected_oil_bopd) / NULLIF(expected_oil_bopd, 0) <= 0.20) AS count_within_tolerance
FROM jobs;

-- Overrides
SELECT 
  decision,
  COUNT(*) AS count,
  reason_category,
  COUNT(*) AS reason_count
FROM `project.dataset.decision_log`
WHERE DATE_TRUNC(DATE(decided_at, 'Asia/Kolkata'), MONTH)
        = DATE_TRUNC(CURRENT_DATE('Asia/Kolkata'), MONTH)
  AND decision IN ('REJECT', 'MODIFY')
GROUP BY decision, reason_category
ORDER BY count DESC;
```

### 4.3 ASCII Mockup

```text
MONTHLY INTERVENTION REVIEW — Geleki · September 2026        [ILLUSTRATIVE]
═══════════════════════════════════════════════════════════════════════

THROUGHPUT                    this month     3-mo avg     trend
  Jobs completed                     23           19         ▲
    rig-requiring                    16           15         ─
    rigless                           7            4         ▲
  Rig-days consumed                  61           68         ▼
  Mean days flagged → executed     11.4         18.2         ▼

OUTCOME
  Deferred bbl avoided            ~4,800                     [method §4]
  Post-job uplift vs predicted      +7%  (18 of 23 within ±20%)
  Jobs that failed to deliver          3  → P(success) recalibrated

WHERE THE SYSTEM WAS WRONG                        ⚠ read this section
  False positives                      4   flagged, engineer rejected, well fine
      3 × choke change not in the data feed  → FIX: ingest choke log
      1 × genuine model error
  Missed failures                      2   failed with no prior flag
      GK-162  rod part, no precursor in daily data  → expected, 5% class
      GK-118  precursor present 9 d prior, threshold too loose → retuned

ENGINEER OVERRIDES                   rejected 6 · modified 9
  most common reason: "combine with adjacent well, save a rig move"
  → NOT currently in the value function. Candidate change to §4.

JOB MIX (what we executed)   wax treatment 17% · pump 22% · rod 26%
                             water shutoff 13% · surface 13% · scale 4% · other 5%

FAILURE MIX (why they failed)     vs expected taxonomy
  tubing leak     23%   (exp 22)   ─
  rod part        17%   (exp 18)   ─
  wax             16%   (exp 15)   ─
  pump wear       13%   (exp 13)   ─
  surface/power   11%   (exp 12)   ─
  other            8%   (exp  8)   ─
  sudden mech      5%   (exp  5)   ─
  sand             5%   (exp  5)   ─
  scale            2%   (exp  2)   ─
  all codes within ±3pp — no drift
```

> [!IMPORTANT]
> **Job mix and failure mix are different populations and must never be shown as one table.** A water shutoff is a *job*; it is not a failure code. A rod part and a pump wear can both be repaired by the same pulling-unit visit. **The ±3pp drift check in `MS-131` applies to failure codes only** — applying it to job mix would raise a drift alert every time the engineers batched work differently, which is exactly the behaviour we want them to have.
>
> **⚠ The illustrative JOB MIX line above predates the corrected taxonomy and must be regenerated before use.** It carries no tubing-repair category, yet `TUBING_LEAK` is now the largest failure bucket at 22%. It **cannot** be recomputed from the share table for exactly the reason stated above — it must come from the mechanism→job catalogue applied to a generated year.

---

## 5. The 'Where the system was wrong' section

**A system that only reports its wins gets read once.** Four false positives with three traced to a missing choke feed is not an embarrassment, it is a system that knows its own error modes and names the fix.

### 5.1 Error Taxonomy

| Error Type | Definition / Detection |
|---|---|
| **False Positive** | Flagged in `well_run`, rejected in `decision_log`, well remains healthy (no subsequent `workover_history` event within 60 days). |
| **Missed Failure** | `workover_history` event occurs with `failure_code` indicating a predictable mechanism, but no prior flag in `well_run`. |
| **Wrong Mechanism** | Flagged and repaired, but `well_run.mechanism` contradicts `workover_history.failure_code`. |
| **Wrong Job** | Flagged and repaired, but engineer `MODIFY`ed the job code in `decision_log` and it succeeded. |
| **Wrong Timing** | ETTF prediction from `well_run` diverges from actual run-life in `workover_history` by > 30 days. |

### 5.2 Root-Cause Attribution

Every error is categorized into one of four root causes:
1. **Data feed gap:** Missing data from upstream systems (e.g., choke log missing).
2. **Threshold mis-tuning:** `TRIGGER_A_FLAG` too sensitive, leading to noise.
3. **Genuine model error:** The physics or ML logic evaluated correctly on clean data but reached the wrong conclusion.
4. **Expected-unpredictable:** a failure with no recoverable precursor in the available data. This is the **25%** of the taxonomy comprising `SUDDEN_MECH` **5%**, `OTHER` **8%** and `SURFACE` **12%** — *not* a single 25% class. A month with none of these is more suspicious than a month with several.

> [!IMPORTANT]
> **Explicit Zero Rule:** If there were genuinely no errors in a month, the section explicitly states **"0 errors detected this month"**. It is never silently omitted.

---

## 6. Aggregation integrity

| ID | Rule | Description |
|---|---|---|
| `RS-100` | **No Recomputation** | Reports aggregate data purely from `well_run`, `decision_log`, and `workover_history`. They never invoke `predict_failure()` or other tools. |
| `RS-101` | **Exact Equality Test** | The sum of daily new triggers across a month must **EXACTLY EQUAL** the monthly gross trigger count. Tolerances are not acceptable. |
| `RS-102` | **Snapshot Immutability** | Late-arriving production data does not alter past reports. Reports are immutable snapshots of the `well_run` state that produced them. |

---

## 7. Delivery

| Component | Format | Schedule | 
|---|---|---|
| **Daily** | In-agent card / Email | 06:00 IST daily |
| **Weekly** | PDF / Email | 07:00 IST Monday |
| **Monthly** | PDF / Presentation | 08:00 IST, 1st of month |

| ID | Rule | Description |
|---|---|---|
| `RS-200` | **Unattended Operation (`FR-074`)** | The reporting suite executes on a cron schedule without human initiation. |
| `RS-201` | **Failure Handling** | If the nightly `well_run` batch fails, the report must state **"STALE DATA: Nightly run failed"** rather than silently serving yesterday's data. |

---

## 8. The feedback loop

| ID | Rule | Description |
|---|---|---|
| `RS-300` | **Rejections are Gold** | Every `REJECT` and `MODIFY` in `decision_log` mandates a reason. This encodes tacit engineering knowledge. |
| `RS-301` | **Recalibration** | When a job fails to deliver its predicted uplift, the `P(success)` multiplier for that job category is updated downward. |
| `RS-302` | **The 200 Threshold** | After 200 labelled corrections, ONGC owns a machine-readable record of how its best engineers reason, which flows into ranking value function changes and model retraining. |

---

## 9. What the reports deliberately do NOT contain

| Excluded Item | Reason for Exclusion |
|---|---|
| **Absolute rupee cost figures** | None are published. Rankings use relative priorities to rig-days. |
| **Individual engineer metrics** | Tracking "approve rates by engineer" poisons adoption instantly and stops people from entering honest rejection reasons. |
| **Automated dispatch actions** | Visible sign-off is mandatory. The system advises; humans decide. |

---

## 10. Schema additions — **APPLIED 2026-09-23**

These fields were requested by this document and have been **added to [02_data_contract.md](./02_data_contract.md)**. No further action is required.

| Field | Type | Required by | Status |
|---|---|---|---|
| `well_run.logistics_blocker` | `STRING` | `RS-004` cleared-blockers detection — we must know the *current* blocker to detect when it clears | ✅ Applied |
| `well_run.earliest_start_date` | `DATE` | `RS-012` slipping jobs, and `TC-011` material transit arithmetic | ✅ Applied |

> [!NOTE]
> **`RS-004` detects a transition, not a state.** A blocker is "cleared" when `logistics_blocker` was `NOT NULL` yesterday and `IS NULL` today. That is only computable because the column stores the *current* blocker every night rather than an event log — which is why the column, not a table, was the right addition.
