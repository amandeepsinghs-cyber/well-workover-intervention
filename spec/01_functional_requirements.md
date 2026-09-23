# 01 · Functional and Non-Functional Requirements

**Version:** 1.0 · **Date:** 2026-09-23
**Parent:** [00_overview.md](./00_overview.md) · **Tested by:** [08_test_plan.md](./08_test_plan.md)

---

## 0. How to read this

Each requirement has an **ID**, a **statement**, an **acceptance criterion** that is objectively checkable, and a **priority**.

| Priority | Meaning |
|---|---|
| **P0** | The demo fails without it. Build first |
| **P1** | The demo is materially weaker without it |
| **P2** | Valuable, cuttable under time pressure |

Requirements are grouped by the act they serve, then by cross-cutting concern. Act numbering follows [demo_flow.md](../demo_flow.md) v2.0.

---

## 1. Act 1 — The Map

### FR-001 · Render wells on real geography · **P0**
The system shall render all `N_WELLS` wells of the Geleki field on a map using **real geographic coordinates**, within a Gemini Enterprise response card.

**Acceptance:** a map appears in-card showing 142 distinct well points at their `well_master.latitude` / `.longitude`, with the Geleki field outline, inside `NFR-001` latency.

> [!NOTE]
> If `RISK-001` resolves negative, this degrades per the tier ladder in [build_plan.md](../build_plan.md) §0.1. **Tier 3 (static basemap image + plotted points) still satisfies FR-001**; it fails `FR-004` only.

### FR-002 · Colour-code by intervention status · **P0**
Well points shall be coloured by a four-state status derived from the nightly run, **not** from a static field.

| Colour | State | Derivation |
|---|---|---|
| 🟢 Green | Healthy | No trigger fired |
| 🟡 Amber | Below its own decline | Trigger A at watch level only |
| 🔴 Red | Flagged for intervention | Any trigger at flag level or above |
| ⚫ Grey | Shut-in / idle | `well_status_history` open shut-in record |

**Acceptance:** counts by colour equal the counts computed directly from `well_run`. Changing a well's trigger state and re-running changes its colour.

### FR-003 · Size by current oil rate · **P1**
Point radius shall encode current oil rate on a perceptually reasonable scale (`sqrt` area encoding).

**Acceptance:** the highest-rate well renders visibly larger than the median; a 2 BOPD well remains visible and clickable.

### FR-004 · Hover tooltips · **P1**
Hovering a well shall show: well ID, current oil rate, water cut, status, days since last intervention.

**Acceptance:** tooltip appears within 200 ms and values match `well_run` for that well.

### FR-005 · Natural-language scoping · **P1**
The map request shall be expressible in natural language with a field name, and the system shall scope correctly.

**Acceptance:** *"Show me all producing wells in the Geleki field on a map"* returns only Geleki wells. A request for a different field returns that field or an explicit "no data" message — **never silently returns Geleki**.

---

## 2. Act 2 — Ask the Data

### FR-010 · Ad-hoc production plotting · **P0**
The system shall plot oil, water and liquid rate plus water cut for any named well over any requested period, generating the chart specification on the fly.

**Acceptance:** *"Plot the oil, water and liquid production for GK-129 over the last three years, and show its water cut"* returns a dual-axis time-series chart. Plotted values equal `daily_production` for that well. No pre-built dashboard exists for this.

### FR-011 · Fit and expose per-well decline curves · **P0**
The system shall fit an Arps hyperbolic decline to **each well's own history** and expose both the fitted curve and the residual.

**Acceptance:** `TC-001` returns `qi`, `b`, `Di`, `r_squared` and a residual series for all 142 wells. `b` lies in `[0.0, 2.0]`; fits with `r_squared < 0.5` are flagged `LOW_CONFIDENCE`, not silently used.

### FR-012 · Push back on rate-ranked queries · **P0** ⭐
When asked for "lowest producing wells" or any absolute-rate ranking, the system shall answer literally **and then volunteer** that absolute rate is the wrong ranking, presenting instead wells ranked by **decline residual**.

**Acceptance:** the response contains (a) the literal rate-ranked list, (b) an explicit statement that rate ranking is misleading for mature wells, (c) a residual-ranked alternative table with actual, expected, gap and gap %. **All three parts present on every one of 20 consecutive runs.**

> [!IMPORTANT]
> **This is the most-remembered beat in the demo.** `AS-012` permits a deterministic implementation. If LLM sampling cannot deliver 20/20, hard-code it — reliability outranks elegance here.

### FR-013 · Never rank by absolute rate for candidate selection · **P0**
No intervention candidate ranking anywhere in the system shall use absolute production rate as its primary key.

**Acceptance:** code review plus `AT-013`: a synthetic 5 BOPD well at its expected decline must not outrank a 60 BOPD well 40% below its own curve.

---

## 3. Act 3 — Which wells need intervention

### 3.1 Triggers

### FR-020 · Trigger A — underperformance vs the well's own decline · **P0**
Flag when the residual against the well's **own** fitted decline falls below `TRIGGER_A_FLAG` for `TRIGGER_A_PERSISTENCE` consecutive **producing** days, with no choke change in the window.

**Acceptance:** tiering at watch / flag / urgent per `00_overview` §5.4. A well with a recorded choke change in the window is **not** flagged. Days with `NULL` production do not count toward or break persistence — see `DC-014`.

### FR-021 · Trigger B — due on its own run-life history · **P0**
Flag when `days_since_last_intervention` exceeds the **p50 of that well's own prior run-lives**, weighted by cumulative fluid throughput rather than calendar days.

**Acceptance:** a well with prior run-lives `[180, 210, 195]` flags past its throughput-weighted p50. A well with fewer than two prior intervention records returns `INSUFFICIENT_HISTORY`, **not** a flag and not an error.

> [!NOTE]
> **Trigger B is the baseline the survival model must beat** (`MS-030`). If `predict_failure()` cannot outperform this rule, the model does not ship.

### FR-022 · Trigger C — diagnostic signature · **P0**
Flag when any physics signature fires: Chan WOR′ classification, fillage divergence, CHP drift, THP rise with seasonality, or volume-vs-displacement gap.

**Acceptance:** each of the six signatures in `00_overview` §5.3 / [04](./04_tool_contracts.md) can be independently triggered by a crafted fixture, and each produces a distinct mechanism label.

### FR-023 · Trigger D — predicted failure · **P0**
Flag when the survival model's hazard crosses threshold, returning **expected time-to-failure with a confidence interval**.

**Acceptance:** `TC-006` returns `ettf_days`, `ci_low`, `ci_high`, `hazard`, `confidence_band` for every well. Intervals are derived from the model, not fabricated constants.

### 3.2 Diagnosis

### FR-030 · Chan water-mechanism diagnosis · **P0**
Compute WOR and WOR′ on log-log axes and classify the water mechanism per the normative convention in `00_overview` §6.

**Acceptance:** `AT-030` — known-coning fixture returns `CONING`; known-channelling fixture returns `CHANNELLING`. **This test is written before the implementation.**

### FR-031 · Pump fillage proxy · **P0**
Compute `fillage_proxy = 0.1166 × Ap × S × N × runtime_fraction − actual_liquid_rate`.

**Acceptance:** matches a hand-computed value for a fixture well to 3 significant figures. If any required geometry field is missing, return `UNAVAILABLE` with the missing field named — **never substitute a default**.

> [!WARNING]
> **Blocked by `RISK-002`.** Without SPM, stroke length, plunger diameter and runtime hours this cannot be computed at all, and the top mechanical feature disappears from the model.

### FR-032 · Offset-well check · **P0** ⭐
For any well flagged by Trigger A, compare its decline residual against its `k` nearest geometric neighbours. If neighbours show a comparable residual, classify as **reservoir**, not wellbore.

**Acceptance:** a fixture where six offsets decline identically yields `RESERVOIR_DECLINE` and downstream `NO_JOB_JUSTIFIED`. A fixture with stable offsets yields `WELL_SPECIFIC`.

### FR-033 · Ranked mechanisms with evidence, never a bare answer · **P1**
Diagnosis output shall present a primary mechanism with confidence and supporting evidence, **plus rejected alternatives with the reason for rejection**.

**Acceptance:** output for GK-129 names channelling as primary with ≥3 evidence items, and rejects coning and multilayer with stated reasons.

### 3.3 Job selection

### FR-040 · Mechanism → job routing · **P0**
Map each diagnosed mechanism to a specific job from the **28-row catalogue** in [decision_architecture.md §3.1](../decision_architecture.md), returning job name, rig requirement, duration and the evidence that selected it.

**Acceptance:** all 28 rows reachable by at least one fixture. The lookup is **data, not code** — an ONGC engineer can edit a table and change behaviour without a deployment.

### FR-041 · Rig vs rigless classification · **P0**
Every recommended job shall be classified rig-requiring or rigless, and rigless jobs shall be queued separately.

**Acceptance:** rigless share across a full synthetic year falls within `RIGLESS_SHARE ± 3pp`. **Re-perforation is classified rig-requiring** — on an SRP well the rod string blocks a perforating gun.

### FR-042 · NO JOB JUSTIFIED · **P0** ⭐
The system shall be capable of concluding that a flagged well needs **no intervention**, with a stated reason.

**Acceptance:** at least one well in the demo dataset produces `NO_JOB_JUSTIFIED` with `RESERVOIR_DECLINE` as the reason and offset evidence attached.

> [!IMPORTANT]
> **This is the credibility requirement.** A system that always recommends a job is a system nobody believes. It is also the direct defence against wrong-job loss (Problem Statement §4, loss #3).

### 3.4 Value and the draft plan

### FR-050 · Economic ranking by value per rig-day · **P0**
Rank candidates by `PRIORITY = net_value ÷ rig_days_consumed`, where `net_value = deferred_bbl_avoided × realisation × P(success) − job_cost`.

**Acceptance:** a ₹2 cr job consuming 10 rig-days ranks below two ₹1.2 cr jobs consuming 3 each. Rigless jobs are ranked in a **separate queue** and do not compete for rig-days.

### FR-051 · P(success) from this asset's own history · **P1**
`P(success)` shall be derived per job type from this asset's historical outcomes, never from vendor literature.

**Acceptance:** output states the sample, e.g. *"0.61 — 11 of 18 comparable jobs, Geleki 2019–25."* Job types with fewer than 5 historical instances return `INSUFFICIENT_HISTORY` and are excluded from the multiplier.

### FR-052 · Draft intervention plan · **P0** ⭐
For each flagged well the system shall generate a draft plan containing, at minimum: why now (triggers fired), diagnosis with confidence and evidence, rejected alternatives, recommended job, rig requirement and duration, P(success) with sample, value estimate, logistics with blockers, preconditions, and approval controls.

**Acceptance:** the GK-129 plan renders every section. **Every numeric value in it is traceable to a tool return or a cited document** — verified by `AT-052`, which asserts provenance for each figure.

### FR-053 · Unstructured document retrieval with citation · **P0** ⭐
The plan shall cite at least one scanned historical document, with document name and date, resolving to an openable artefact.

**Acceptance:** the GK-129 plan cites the 1998 completion report and the 2019 workover report; both links open; both dates display.

### FR-054 · Cite evidence against the system's own recommendation · **P1**
Where historical evidence contradicts the cheaper option, the system shall surface it.

**Acceptance:** GK-129's plan recommends the more expensive cement squeeze and explains that the cheaper straddle packer was attempted in 2019 and failed at 14 months.

### 3.5 Honesty

### FR-060 · Declare synthetic data provenance · **P0**
Any interface presenting generated data shall carry a visible, persistent indication that the data is synthetic.

**Acceptance:** a banner is present in every screenshot of every act.

### FR-061 · Answer the training-data question · **P0**
The system's documentation and the presenter's script shall contain a prepared, honest answer to *"what was the model trained on?"*

**Acceptance:** [07](./07_agent_spec.md) §6 contains the scripted answer. **Verifiable claim:** at least 4 of the 7 wells in the Act 3 table are flagged by triggers A/B/C alone, independently of the model — asserted by `AT-061`.

---

## 4. Act 4 — Reports

### FR-070 · Daily report · **P0**
Generate a daily brief: triggers newly fired overnight, drafts awaiting review, ranking movements, cleared blockers.

**Acceptance:** running two consecutive nights produces a daily report whose "new overnight" set equals the set difference between the runs.

### FR-071 · Weekly report · **P0**
Generate a 14-day rig plan with a **separate parallel rigless queue**, plus slipping jobs with reasons and review activity counts.

**Acceptance:** committed rig-days never exceed available rig-days. Rigless jobs appear in their own block and consume zero rig-days.

### FR-072 · Monthly ED scorecard · **P0** ⭐
Generate a monthly review for the Basin Manager containing throughput, outcomes, job mix, **and a mandatory "Where the system was wrong" section** covering false positives, missed failures and engineer overrides.

**Acceptance:** the section is present and non-empty. If there were genuinely no errors, it states so explicitly rather than being omitted.

### FR-073 · Reports aggregate, never recompute · **P0**
`generate_report()` shall read the same `well_run` records the drafts were generated from.

**Acceptance:** monthly totals equal the sum of the constituent dailies, exactly. `AT-073` asserts equality, not tolerance.

### FR-074 · Scheduled unattended operation · **P1**
The nightly run and daily report shall execute on a schedule without human initiation.

**Acceptance:** a scheduled trigger produces a dated report artefact with no interactive session.

---

## 5. Cross-cutting

### FR-080 · Human approval gate · **P0**
No output shall be actioned automatically. Every plan terminates at `APPROVE / MODIFY / REJECT / DEFER`.

**Acceptance:** no code path writes to any system of record. `REJECT` requires a reason — it is not optional.

### FR-081 · Capture rejection reasons · **P0**
Every rejection and modification shall be persisted with its reason, well, recommended job and timestamp.

**Acceptance:** `decision_log` accumulates structured records. **These are the most valuable data the system collects** — each is a labelled correction encoding tacit engineering knowledge.

### FR-082 · Feedback loop · **P2**
Post-job actuals shall be compared against predicted uplift and feed back into `P(success)` and model retraining.

**Acceptance:** recalibration is demonstrable on synthetic data. **Not required for the demo** — specified so the architecture does not preclude it.

### FR-083 · No LLM arithmetic · **P0** ⭐
Every number in every output traces to a deterministic tool return or a cited document.

**Acceptance:** `AT-083` — for each of the 20 numeric values in the GK-129 plan, a provenance record identifies the producing tool call or source document.

### FR-084 · Visible tool-call trace · **P1**
The system shall display the sequence of deterministic tool calls with timings.

**Acceptance:** Act 3 shows ≥8 named tool calls with per-call durations. It serves double duty — proving determinism and making an 18-second wait feel like work.

---

## 6. Non-functional requirements

### NFR-001 · Latency
| Interaction | Target |
|---|---|
| Act 1 map | < 8s |
| Act 2 chart / decline fit | < 12s |
| **Act 3 intervention list** | **< 18s** |
| Act 3 well drill-down | < 12s |
| Act 4 report | < 10s |
| Act 5 plan / replan | < 15s |

**Acceptance:** measured on **conference wifi**, not the office LAN. Any turn over ~15s without a visible trace loses the room.

### NFR-002 · Determinism
Given identical inputs, every deterministic tool returns identical outputs. Random seeds are fixed and recorded.

### NFR-003 · Reproducibility
The synthetic dataset regenerates byte-identically from a recorded seed and a pinned `pyproject.toml`. *"We can regenerate this exactly"* is part of the integrity story.

### NFR-004 · Auditability
Every draft plan persists with the tool calls, inputs and outputs that produced it.

### NFR-005 · Offline fallback
Every act has a screen-recorded fallback, playable without network.

### NFR-006 · Editability by the customer
The mechanism→job catalogue and trigger thresholds are configuration, not code. **Their edits are the adoption.**

### NFR-007 · Scale headroom
The nightly batch completes for 142 wells in under 5 minutes and shall not exhibit worse than `O(n log n)` scaling to 5,000 wells.

---

## 7. Risks

| ID | Risk | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|
| **RISK-001** | GE A2UI renderer may not support Vega `geoshape` + `projection` | **Act 1 is the first thing on screen** | Three-tier fallback ladder, [build_plan.md](../build_plan.md) §0.1. Spike before any other work | Eng | **OPEN — blocking** |
| **RISK-002** | SPM, stroke, plunger diameter, runtime, CHP may not be generatable | Fillage proxy impossible; top mechanical feature lost | Confirm before Phase 1. If unavailable, demote to rate-trend features and **say so** | Eng | **OPEN — blocking** |
| **RISK-003** | Circularity — model trained on data generated from the same covariates | A technical reviewer discredits Act 3 | 4 of 7 rows model-free; scripted honest answer (`FR-061`); unobserved frailty term (`SD-021`) | Spec | Mitigated |
| **RISK-004** | Model too good — AUC > 0.95 indicates leakage | Instantly non-credible | Hard build gate `MS-031`; frailty injection | Spec | Mitigated |
| **RISK-005** | Signatures not discriminable; model learns one pattern | Act 3 table shows six identical diagnoses | Validator trains a 6-class classifier; target macro-F1 0.70–0.85 (`SD-040`) | Spec | Mitigated |
| **RISK-006** | Chan sign convention inverted | Recommends a 7-day rig job instead of a choke adjustment | Normative statement `00_overview` §6; test-first `AT-030` | Spec | Mitigated |
| **RISK-007** | `NULL` vs `0` confusion in downtime | Shut-in wells flood the queue as false positives | `DC-014` enforced invariant | Spec | Mitigated |
| **RISK-008** | Push-back beat fails to fire under sampling | Loses the most-remembered moment | `AS-012` permits deterministic implementation | Eng | Accepted |
| **RISK-009** | Scanned-PDF OCR quality insufficient for citation | `FR-053` fails; the strongest "data from anywhere" proof is lost | Generate PDFs with a text layer plus scan-effect overlay | Eng | Mitigated |
| **RISK-010** | Demo date unknown | Cannot sequence CalGEM validation or set scope | ⚠ **ASSUMED: 2026-10-14** — three working weeks from 2026-09-23. See the note below. **Correct this in one line and the schedule re-plans around it** | You | **ASSUMED** |
| **RISK-011** | SPE-212848-PA read only as abstract | The sole ONGC-specific mechanism source is unverified; a DLS inference was retracted | Obtain full text, or continue to label §1 of the feature spec "well-reasoned but not yet sourced" | You | **OPEN** |

### Working assumption on the demo date

> [!IMPORTANT]
> **Assumed demo date: Wednesday 2026-10-14 — three working weeks out.** Nothing in this spec set depends on the date being *right*; several things depend on there being *a* date. **This is a planning assumption, not a commitment, and correcting it costs one line.**

**Why three weeks:** it is the shortest window in which Stages A–L in [`build.md`](../build.md) complete without cutting the survival model, and the longest that is plausible for something already being socialised with Executive Directors.

**What the assumption actually decides:**

| Scope item | At 2026-10-14 | If the date pulls in to ~2 weeks | If it slips to 6+ weeks |
|---|---|---|---|
| Stages A–D *(data, tools)* | ✅ In | ✅ In | ✅ In |
| Stage E *(survival model)* | ✅ In | ⚠ **Ships on Trigger B heuristic alone**, model becomes a follow-up | ✅ In |
| Stages F–J *(agent, deploy, publish)* | ✅ In | ✅ In | ✅ In |
| **CalGEM external validation** | ❌ **Out.** Monthly-vs-daily mismatch makes it a research task, not a build task | ❌ Out | ✅ **In — and it is the single highest-value addition.** External validation on real operator data is the one thing that would make the model's numbers more than internally consistent |
| Scanned-PDF corpus *(40–50 documents)* | ⚠ **Reduced to ~15**, enough for the citation beat | ❌ Cut to 5 hero documents | ✅ Full corpus |
| Act 5 rig-scheduling plan | ⚠ Optional, cut first if Stage L rehearsal runs short | ❌ Out | ✅ In |

> **The one thing to tell me if you correct the date:** whether it moves *in* or *out*. Moving in cuts the survival model, which is the part that answers *"can you tell me which wells will fail?"* — so if the date is closer than three weeks, **that is a conversation to have before Stage A, not at Stage E.**

---

## 8. Requirement count

| Group | P0 | P1 | P2 | Total |
|---|---|---|---|---|
| Act 1 — Map | 2 | 3 | 0 | 5 |
| Act 2 — Ask the data | 4 | 0 | 0 | 4 |
| Act 3 — Intervention | 14 | 4 | 0 | 18 |
| Act 4 — Reports | 4 | 1 | 0 | 5 |
| Cross-cutting | 4 | 1 | 1 | 6 |
| **Total FR** | **28** | **9** | **1** | **38** |
| NFR | — | — | — | 7 |
| Risks | — | — | — | 11 |

**⭐ marks the eight requirements that carry the demo.** If time runs out, these are the last to be cut: `FR-012`, `FR-032`, `FR-042`, `FR-052`, `FR-053`, `FR-072`, `FR-083`.
