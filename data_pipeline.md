# Data Sourcing Pipeline

**ONGC Assam Asset · Geleki Field** · **Version:** 1.1 · **Date:** 2026-09-23
**Companions:** [`spec/02_data_contract.md`](./spec/02_data_contract.md) *(the schema)* · [`spec/03_synthetic_data_spec.md`](./spec/03_synthetic_data_spec.md) *(the generator)* · [`spec/04_tool_contracts.md`](./spec/04_tool_contracts.md) *(`TC-001` allocation handling)* · [`spec/07_agent_spec.md`](./spec/07_agent_spec.md) *(`AS-017`…`AS-025` disclosure)* · [`build.md`](./build.md) *(the commands)*

> **v1.1 — every `DP-nnn` rule in this document is now bound to an enforceable clause elsewhere in the spec set. See §14 for the index.**

---

## 0. The answer, first

> **The demo is only defensible if the synthetic data enters through exactly the same pipe ONGC's real data will. Swap the loader at the bottom; nothing above it changes. That single design decision is the difference between a rehearsal and a puppet show — and it is the answer to the first question an Executive Director will ask.**

**"Where does this data come from?"** has three parts, and all three must be answerable on screen:

| Question | Answer |
|---|---|
| **Is this our data?** | No. It is synthetic, generated from a seeded, reproducible model — and here is the model |
| **Where would the real data come from?** | Named source system, per field — §6 |
| **What happens when our data is messy?** | These gates, and this is what the agent says when one fails — §10 |

> [!CAUTION]
> **The single largest data-sourcing risk is not availability. It is that most ONGC onshore daily per-well production is *allocated*, not measured.** A back-allocated rate moves when a *neighbour's* well test changes, not because anything happened at that well. Fed naively into a decline-residual trigger, allocation artefacts are indistinguishable from mechanical failure. **§5 is the most important section in this document.**

---

## 1. The principle — one pipeline, two sources

```
   TRACK A — DEMO (today)                    TRACK B — ONGC (production)
   ══════════════════════                    ═══════════════════════════

   generator/  (seeded Python)               EPINET  ·  SCADA / GGS daily reports
   emits SOURCE-SHAPED extracts              Well test records  ·  Workover reports
   mirroring ONGC export formats             Well master / survey  ·  SAP-ICE (MRO)
             │                                            │
             └────────────►  gs://…/landing/  ◄───────────┘
                                   │
                      ╔════════════▼════════════╗
                      ║   THE SWAP POINT        ║   ← everything below is identical
                      ╚════════════╤════════════╝
                                   ▼
                        BigQuery   geleki_raw          source-shaped, untransformed
                                   ▼
                        transforms + DC-nnn gates      IDENTICAL CODE, both tracks
                                   ▼
                        BigQuery   geleki              the 13 contract tables
                                   ▼
                        nightly batch  →  well_run     the spine
                                   ▼
                        tools TC-001 … TC-018
                                   ▼
                        agent  →  Gemini Enterprise
```

### Why this matters more than it looks

The tempting shortcut is to have the generator write straight into the 13 contract tables. **Do not.** Three things break:

| Shortcut cost | Consequence |
|---|---|
| The transform layer is never exercised | On real data it runs for the first time in front of ONGC |
| The quality gates never fire | We never learn what the agent says when a gate fails — and it *will* fail on real data |
| *"What happens when you get our data?"* has no good answer | *"We swap the loader"* becomes *"we rebuild it"* |

> [!TIP]
> **Minimum viable version:** `geleki_raw` → `geleki` can be a set of BigQuery **views**, not materialised tables, for the demo. The point is that the transform *exists as code* and is the only path in. That costs about half a day and buys the entire answer to the integration question.

---

## 2. The swap point — what changes, what does not

| Layer | Track A (demo) | Track B (ONGC) | Changes? |
|---|---|---|---|
| Source | Seeded generator | EPINET, SCADA, workover reports | ✅ **Yes — this is the only layer that changes** |
| Landing | `gs://…/landing/` Parquet | `gs://…/landing/` Parquet | ⚠ Same shape, different producer |
| `geleki_raw` | Source-shaped | Source-shaped | ❌ No |
| Transforms + gates | SQL | SQL | ❌ No |
| `geleki` (13 tables) | Contract | Contract | ❌ No |
| `well_run` nightly | Same batch | Same batch | ❌ No |
| Tools, model, agent, reports | Identical | Identical | ❌ No |

**Roughly 85% of the build is source-agnostic.** That is the number to say out loud.

---

## 3. Layer by layer

### 3.1 Landing — `gs://<bucket>/landing/<source>/<yyyy>/<mm>/<dd>/`

Immutable, append-only, partitioned by ingest date. Never edited in place. Re-running a day overwrites that partition and nothing else.

### 3.2 `geleki_raw` — source-shaped, deliberately ugly

Loaded **without transformation**. Original column names, original types, original units. Every row carries:

```sql
_ingested_at    TIMESTAMP   -- when we received it
_source_system  STRING      -- 'GENERATOR' | 'SCADA' | 'EPINET' | 'WORKOVER_PDF' | 'SAP_ICE'
_source_file    STRING      -- the exact landing object
_batch_id       STRING      -- idempotency key
```

> **Keeping the raw layer ugly is the point.** The moment we clean on ingest, we lose the ability to show what ONGC actually sent us versus what we did to it — and that trace is the lineage story.

### 3.3 Transforms — where unit conversion, typing and the gates live

This is where `tonnes → barrels`, `m³ → bbl`, IST date normalisation, and the `0 → NULL` correction happen. **Every one of them is a place a number can silently become wrong, so every one is tested.**

### 3.4 `geleki` — the 13 contract tables

Exactly as specified in [`spec/02`](./spec/02_data_contract.md). **Any field not in that document does not exist.**

### 3.5 `well_run` — the nightly spine

One row per well per run. **Everything downstream reads this and nothing recomputes it.** This is what makes the demo fast and makes every tooltip traceable to a column.

---

## 4. The reconstruction that decides the project

> [!IMPORTANT]
> **`well_status_history` is ask #1 in `spec/02` §12, and it almost certainly does not exist as a clean table anywhere in ONGC.** Without it there is no survival label, no run-life distribution, no Trigger B, and no deferred-barrel value case. The system does not exist.
>
> **So the pipeline must be able to build it, not just receive it.**

```
  PREFERRED   ONGC supplies well_status_history with reason codes
              └─► load, validate, done

  FALLBACK    Reconstruct:
              1. Detect PRODUCING → NOT-PRODUCING transitions from daily_production
                 (is_producing, runtime_hours, NULL-vs-zero — see §5.3)
              2. Close each episode at the next producing day
              3. Join workover_history on (well_id, date window) for the reason code
              4. Episodes with no matching workover → reason = 'UNKNOWN', flagged
              5. Report the UNKNOWN share. If it exceeds ~30%, say so out loud —
                 the survival labels are that much weaker
```

**Build the fallback path even if ONGC promises the table.** It is the same construction we would use on CalGEM or WOGCC for external validation, so it is not wasted work — and it converts *"we need this from you"* into *"we can derive this, and it is better if you have it."*

---

## 5. ⚠ The allocation problem — the section to read twice

### 5.1 What actually happens at an onshore asset

Wells flow to a Group Gathering Station. **The GGS total is measured. Individual wells are usually not.** The daily per-well figure is the GGS total *apportioned* across wells in the ratio of their last well tests.

| Consequence | Why it is dangerous for us |
|---|---|
| A well's daily rate changes when a **neighbour** is re-tested | Looks like a step change at a well where nothing happened |
| Individual daily values are **not independent measurements** | The effective sample size for a decline fit is far smaller than the row count |
| A single bad well test propagates to **every well on that GGS** | A correlated error across a whole group, not a random one |
| Only `data_source = 'TESTED'` days are real | Typically **one day in 14–30** (`SD-020`) |

**Our schema already carries the distinction** — `daily_production.data_source ∈ {ALLOCATED, TESTED, ESTIMATED}` (`DC-016`). **What was missing is what the pipeline and the triggers do about it.**

### 5.2 The five rules that close it

| Rule | Statement |
|---|---|
| **DP-001** | **The Arps decline fit (`TC-001`) is weighted toward `TESTED` points.** Allocated points inform the trend; tested points anchor it |
| **DP-002** | **A residual computed only from allocated data is capped at `MEDIUM` confidence.** Trigger A may fire, but never at `URGENT` without a tested point or a runtime signal corroborating it |
| **DP-003** | **Allocation-basis changes are detected and excluded.** When a neighbour on the same GGS is re-tested, every well on that GGS gets a step. The pipeline flags the cohort; `TC-001` treats the step as a basis change, **not a rate change** |
| **DP-004** | **`runtime_hours` and `is_producing` are never allocated.** They are observed, and they are therefore the most trustworthy daily fields we have. Where allocation is doubtful, **runtime is the fallback signal** |
| **DP-005** | **The agent states the basis.** *"Trigger A fired on GK-129. Last well test was 9 days ago; the intervening rates are allocated."* |

> [!NOTE]
> **`DP-004` is the quiet insight.** Everyone reaches for rate. But *"did this well run today, and for how many hours"* is directly observed at the wellhead, is not subject to allocation, and is the cleanest input we have. It is also exactly what Trigger B and the survival model consume. **Our two strongest triggers are the two least contaminated by allocation** — and that is worth saying in the room.

### 5.3 `NULL` is not zero, and this is a pipeline job

`DC-014`. A shut-in well and a well producing nothing are different facts, and most source systems conflate them by writing `0`.

```
source says            pipeline must write
────────────────────   ──────────────────────────────────────────
0.0, well shut in   →  oil_rate = NULL, is_producing = FALSE
0.0, well on but dry→  oil_rate = 0.0,  is_producing = TRUE
row absent          →  row absent — do NOT interpolate
```

**Get this wrong and every decline fit is poisoned by fake zeros**, pulling `arps_di` steeper and firing Trigger A across the field.

---

## 6. Field-level provenance

| Contract table | Track A — demo | Track B — ONGC source | Confidence |
|---|---|---|---|
| `well_master` | `SD-011`…`SD-016` | **EPINET** — well completion records ✅ *verified data class*. **Coordinates from survey/GIS, never synthesised** (`TC-016.1`) | 🟢 High |
| `daily_production` | `SD-017`…`SD-023` | Asset daily production reporting / SCADA via GGS. **Mostly allocated — §5** | 🟡 Medium |
| ↳ `spm`, `stroke`, `plunger`, `runtime`, `chp` | `SD-015b` gated to SRP | **`RISK-002` — UNKNOWN whether available.** Tier 1 in the data ladder | 🔴 **Open** |
| `well_tests` | `SD-020` | **EPINET** — well test results ✅ *verified data class* | 🟢 High |
| `well_status_history` | `SD-024`+ | **⚠ Probably does not exist. Reconstruct — §4** | 🔴 **Ask #1** |
| `workover_history` | `SD-025`+ | Scanned workover completion reports → §8. Possibly SAP-ICE work orders | 🟠 **Ask #2** |
| `well_offsets` | Derived from coordinates | Derived — same code | 🟢 High |
| `job_catalogue` | Config, 28 rows | **Ours, not ONGC's.** Norms to be confirmed by the Asset — §9 | 🟡 Config |
| `mro_inventory` | Config | SAP-ICE *(Project ICE is ONGC's SAP ERP backbone)* | 🟡 Medium |
| `well_run` | **Computed nightly by us** | Identical | 🟢 Ours |
| `draft_plan`, `decision_log` | **Created by the system** | Identical — and the feedback asset | 🟢 Ours |

### 6.1 Name the real system — EPINET

> **EPINET — Exploration & Production Information Network** is ONGC's corporate E&P data repository. Initiated **1999**, built on the **Schlumberger Finder / ProSource** databank, deployed across **18 centres**, with asset-level distributed custodianship.
> **Source: SPE-99336-MS**, Mittal (ONGC) & Chatterjee (Schlumberger), SPE Intelligent Energy, Amsterdam, 2006.

**Verified data classes:** well completion records, drilling operations, **well test results**, wireline logs, seismic, geological data, laboratory/fluid data, production and reservoir performance.

> [!WARNING]
> **Ask, do not assert.** It is **NOT VERIFIED** that EPINET holds static reservoir pressures, PVT, or **workover history** — and workover history is ask #2. Do not say *"we'll pull it from EPINET"*; say *"which EPINET data class holds workover history, and who is the custodian for Assam Asset?"*
>
> Two further cautions: **do not call EPINET "OSDU-style"** — it predates OSDU by two decades and no source supports the claim. And **its current operational status is unconfirmed**; it may have been superseded. Ask.
>
> **Fallback route:** the **National Data Repository (NDR)** run by DGH (`ndrdgh.gov.in`) is the *national* repository, distinct from EPINET. If ONGC deflects internally, NDR is the other door.

---

## 7. Latency and as-of correctness

**A demo that says "as of today" over data that is two days old is lying on screen, and it is the easiest lie for an Asset engineer to catch.**

```sql
-- well_run must carry BOTH
run_as_of       DATE   -- when we computed
data_as_of      DATE   -- the latest production date actually present
data_lag_days   INT64  -- run_as_of − data_as_of
```

| Rule | Statement |
|---|---|
| **DP-006** | **Every report and every agent answer states `data_as_of`, not `run_as_of`**, whenever they differ |
| **DP-007** | `data_lag_days > 3` → the run is `LOW_CONFIDENCE` and the agent says so |
| **DP-008** | **All dates are IST-local.** `DATE(ts, 'Asia/Kolkata')`, never a bare UTC cast. A midnight-boundary error shifts every daily rate by a day and is invisible until someone reconciles against the GGS |

---

## 8. The scanned-document pipeline — separate, and load-bearing

Workover history detail lives in **scanned reports, not a database**. This is a second pipeline and it is the proof of *"access data from anywhere."*

```
scanned PDFs  →  gs://…/docs/  →  Vertex AI Search  →  TC-012 search_well_history()
                                                            │
                                                            └─► citation: document name + date,
                                                                openable link, on screen
```

| Rule | Statement |
|---|---|
| **DP-009** | **A retrieved fact without a resolvable citation is not used.** `TC-012` returns the document name and date or it returns nothing |
| **DP-010** | If OCR quality is marginal, generate the demo corpus **with a real text layer** plus a scan-effect overlay, rather than true rasterised scans. **Disclose that this is a demo corpus** |

---

## 9. What is ours, not ONGC's — label it

Three things in the pipeline are **configuration we authored**, and presenting them as ONGC data would be the same class of error as an unsourced number:

| Item | Status |
|---|---|
| `job_catalogue` — 28 rows, rig/rigless, durations | **Ours.** Built from the corrected `TC-008.6` invariant. **Durations and the rig/rigless split need Asset confirmation** |
| Job cost norms, `realisation_per_bbl` | **Ours, derived.** The $45/bbl is derived, not disclosed — see `research_appendix` §2 |
| `mro_inventory`, base locations | **Illustrative** until SAP-ICE is connected |
| Lift mix 70 SRP / 20 gas lift / 10 natural | **Assumed, and must be labelled so on every screen** (`SD-015c`) |

> [!NOTE]
> **New evidence, and it cuts against our own assumption.** SPE-194798-MS (Maut et al., **Oil India Ltd**, 2019) reports that **~48% of OIL's producing wells in Upper Assam are on gas lift**. OIL is not ONGC and Hapjan is not Geleki — but it is the best regional anchor that exists, and **it suggests our assumed 20% gas lift is probably low.** Do not change the number on this evidence; **do** state that the assumption is conservative and that the real split is a named deliverable.

---

## 10. Quality gates — and what the agent says when one fails

The `DC-nnn` invariants in `spec/02` §11 are **pipeline gates, not a report**. They run on every load and they fail the build.

| Gate | Checks | On failure |
|---|---|---|
| **Schema** | Columns, types, nullability | **Hard fail.** Batch rejected |
| **Referential** | Every `well_id` in `well_master` | **Hard fail** |
| **Physical** | Water cut 0–100 · runtime 0–24 · `liquid = oil + water` · monotonic water on a 90-day mean except across a WSO | **Hard fail** |
| **NULL-vs-zero** | `DC-014` — no fake zeros | **Hard fail** — §5.3 |
| **Coverage** | Wells with no data in N days | **Warn**, exclude from ranking, report the exclusion |
| **Allocation** | Share of `TESTED` days per well | **Warn** — feeds `DP-002` confidence capping |
| **Freshness** | `data_lag_days` | `> 3` → `LOW_CONFIDENCE` (`DP-007`) |
| **Consistency** | Availability arithmetic, taxonomy shares ±3pp | **Hard fail** — closed 2026-09-23 (`D-15`, `AT-092` two-population assertion) |

> **The agent must be able to say a gate failed.** *"Eleven wells are excluded from tonight's ranking: no production data since the 19th."* That is a better demo moment than silent completeness, and it is the behaviour that survives contact with real data.

---

## 11. The ask to ONGC — one page, in priority order

| # | Ask | Likely source | If missing |
|---|---|---|---|
| **1** | **Well status history with reason codes**, 24+ months | Probably nowhere clean — **we reconstruct (§4)** | No survival label. **The system does not exist** |
| **2** | **Workover history with dated outcomes** | Scanned reports; ask EPINET custodian | No run-life, no baseline, no `P(success)` |
| **3** | Daily production, 24+ months, **with the allocated/tested flag** | Asset daily reporting / GGS | Triggers degrade to monthly |
| **4** | Well test records | **EPINET** ✅ verified class | Decline fits lose their anchor (`DP-001`) |
| **5** | Well master + **surveyed coordinates** | **EPINET** ✅ + GIS | No map |
| **6** | SRP geometry — plunger, stroke, SPM, runtime, CHP | `RISK-002` | Fillage proxy lost — the top mechanical feature |
| **7** | **The actual artificial-lift split** | Asset | The 70/20/10 stays an assumption |
| **8** | Job cost and duration norms | Asset / SAP-ICE | Ranking becomes barrels-only |
| **9** | MRO inventory | SAP-ICE | Plans lose the logistics block |
| **10** | Acoustic fluid levels | Asset, if acquired | *Nice to have, disproportionate value* |

**Two questions to ask rather than answer:** *which EPINET data class holds workover history, and who is the Assam Asset custodian?*

---

## 12. What goes on screen

> [!IMPORTANT]
> **Say this out loud in Act 0, before anything is shown.**
>
> *"Every number you are about to see is synthetic. It was generated from a model calibrated against three independent public sources, it is reproducible from a seed, and the generator is inspectable. What is **not** synthetic is the pipeline: this data entered through exactly the pipe your data would, and every value on screen traces back to a named column."*

| Rule | Statement |
|---|---|
| **DP-011** | Synthetic-data disclosure appears **on screen**, not only in the narration |
| **DP-012** | Every tooltip carries the `well_run` column it came from (`TC-016.6`) |
| **DP-013** | The agent never claims a data source it did not read |
| **DP-014** | Where a value is configuration rather than data (§9), the agent says so |

---

## 13. Open items

| # | Item | Status | Blocks |
|---|---|---|---|
| 1 | **`RISK-002`** — are SPM, stroke, plunger, runtime, CHP available? | 🔴 **Open — only ONGC can answer** | Tier 1 · the fillage proxy · `MS-011` |
| 2 | **Is EPINET still the live system?** Which class holds workover history? | 🔴 **Open — ask, do not assume** | Asks #2 and #4 |
| 3 | **What is the real allocation practice at Geleki?** How often is each well tested? | 🔴 **Open** | `DP-001`…`DP-005` calibration |
| 4 | **What is the true daily-reporting lag?** | 🔴 **Open** | `DP-006`, `DP-007` |
| 5 | **`D-15`** — the availability arithmetic did not close | ✅ **CLOSED 2026-09-23** — re-derived two-population: `E[down]` **37.3 d**, `FRACTION_DOWN_ACTIVE` **16.3%**, `FRACTION_DOWN_TOTAL` **20.0%**. The *"three sources agree to 0.2pp"* claim is **withdrawn**. [`spec/00`](./spec/00_overview.md) §5.2 · [`spec_audit.md`](./spec_audit.md) §6 | Was: the consistency gate · a spoken demo beat |
| 6 | **`D-17`** — no depth-generation rule, yet four `NOT NULL` depth fields | ✅ **CLOSED** — `SD-013b`…`SD-013d`, `spec/03` §2.2 | Gate C |
| 7 | **`D-18`** — allocation was unhandled anywhere in the spec set | ✅ **CLOSED** — see §14 | Gate C, Gate D |

> **Items 1–4 are questions only ONGC can answer, and asking them is a strength.** Items 5–7 were ours; all three are now closed. **Nothing in this document blocks the build.**

---

## 14. Propagation index — where these rules are actually enforced

> **A rule that lives only in this document is a wish. Every `DP-nnn` below is now bound to an enforceable clause somewhere else.**

| Rule | Subject | Enforced by |
|---|---|---|
| **DP-001** | Weight the decline fit toward `TESTED` | `TC-001` Method block — `TESTED` w=3.0, `ALLOCATED` w=1.0, `ESTIMATED` w=0.5 |
| **DP-002** | Cap confidence on allocation-only residuals | **`DC-070`** · `TC-001` condition table · test **`AT-001f`** |
| **DP-003** | Exclude allocation basis changes | **`DC-071`** · `TC-001.7` · `well_run.allocation_basis_id` · test **`AT-001e`** |
| **DP-004** | Runtime is observed, never allocated | `DC-070` note — Triggers B and D are explicitly unaffected |
| **DP-005** | The agent states the basis | `TC-001.8` `allocation_note` · **`AS-018`** |
| **DP-006** | Report `data_as_of`, not `run_as_of` | **`DC-067`** · `well_run.data_as_of` · **`AS-017`** |
| **DP-007** | `data_lag_days > 3` ⇒ `LOW_CONFIDENCE` | **`DC-069`** · `well_run.run_confidence` · **`AS-020`** |
| **DP-008** | All dates IST | **`DC-068`** · `build.md` C.4 transform table |
| **DP-009** | No citation, no fact | `TC-012` |
| **DP-010** | Disclose the demo document corpus | `build.md` Phase 1.5 |
| **DP-011** | On-screen synthetic disclosure | **`AS-024`** |
| **DP-012** | Tooltips carry their `well_run` column | **`AS-025`**, `TC-016.6` |
| **DP-013** | Never claim an unread source | **`AS-022`** |
| **DP-014** | Label configuration as ours | **`AS-019`**, `SD-015c` |

**Also propagated, from the same pass:**

| Finding | Landed in |
|---|---|
| The **swap point** — generator → landing → `geleki_raw` → transforms → `geleki` | **`build.md` Stage C.3/C.4**, and Gate C now fails if a generator writes a contract table directly |
| **EPINET**, verified half and false half separated | `spec/02` §12.1, `research_appendix.md` §3.1 |
| **Compressor trip is a field event** | `SD-031`, `SD-033d`, **`AS-021`**, Gate C |

