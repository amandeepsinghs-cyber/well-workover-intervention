# 08 · Test Plan and Traceability

**Version:** 1.0 · **Date:** 2026-09-23
**Parent:** [00_overview.md](./00_overview.md) · **Verifies:** [01](./01_functional_requirements.md), [02](./02_data_contract.md), [03](./03_synthetic_data_spec.md), [04](./04_tool_contracts.md), [05](./05_model_spec.md), [06](./06_report_spec.md), [07](./07_agent_spec.md)

---

## 0. The answer, first

> **Seven tests decide whether this system is honest. The rest decide whether it works. Write the seven first — every one of them is a test that the system refuses to do something convenient: refuses to invert a sign, refuses to default a missing input, refuses to recommend a job, refuses to hide an error, refuses to compute a number in the narration.**

The seven are `AT-030d`, `AT-003b`, `AT-032b`, `AT-014`, `AT-073`, `AT-083`, `AT-072b`. They are marked ⭐ throughout.

---

## 1. Test levels

| Level | Scope | Runs | Gate |
|---|---|---|---|
| **L1 · Unit** | One tool, one fixture | Every commit | All pass |
| **L2 · Data** | Generated dataset against the contract | Every regeneration | All `DC-` invariants hold |
| **L3 · Model** | Trained model against its gates | Every training run | `MS-` gates pass |
| **L4 · Integration** | Full nightly run, 142 wells | Nightly | `well_run` complete and consistent |
| **L5 · Acceptance** | Agent behaviour per act | Before every rehearsal | All P0 `FR` demonstrated |
| **L6 · Rehearsal** | End-to-end, timed, on demo network | Twice before the room | Inside `NFR-001` |

> [!IMPORTANT]
> **L2 runs on every regeneration, not once.** The availability identity (`DC-092`) underpins a spoken beat in the demo. If a parameter tweak silently breaks it, the claim becomes false and nobody notices until someone in the room does the arithmetic.

> [!CAUTION]
> **Corrected 2026-09-23 (`D-15`). The old "three independent sources reconcile to within 0.2 percentage points" claim was circular and is withdrawn — it must not be reinstated here or spoken.** What `AT-092` now protects is narrower: `FRACTION_DOWN_ACTIVE` **16.3%** and `FRACTION_DOWN_TOTAL` **20.0%**, of which only the downtime **upper tail** (`p96.7 = 204.1 d` against the CAG-audited maximum of 205 d) is genuinely corroborated. The 20.0% is **fitted** via a 4.5% permanently-idle carve-out. See [00 §5.2](./00_overview.md) and [03 §3](./03_synthetic_data_spec.md).

---

## 2. L1 — Unit tests by tool

### 2.1 TC-001 · `fit_decline_curve()`

| ID | Test | Expected |
|---|---|---|
| AT-001a | Fit a synthetically-generated Arps curve with known `qi`, `b`, `Di` | Parameters recovered within 1% |
| AT-001b | Well with all-`NULL` production | `INSUFFICIENT_HISTORY`, no exception |
| AT-001c | Well with a workover mid-window | The 30 days following `end_date` are excluded from the fit |
| AT-001d | Call twice with identical inputs | Byte-identical output (`NFR-002`) |
| AT-001e | Noisy data giving `r² = 0.3` | `LOW_CONFIDENCE`, and Trigger A does not fire on it |
| AT-001f | Data producing `b = 2.4` | Clamped to 2.0 **and the clamp reported in `message`** |

### 2.2 TC-002 · `chan_diagnostic()` ⚠ write these before the implementation

| ID | Test | Expected |
|---|---|---|
| AT-030a | Analytic coning fixture — `WOR(t) = WOR_max − A·t^(−k)` | `CONING`, `wor_prime_slope < −0.10` |
| AT-030b | Analytic channelling fixture — `WOR(t) = A·t^n`, `n ≈ 1.1` | `CHANNELLING`, `wor_prime_slope > +0.30` |
| AT-030c | Multilayer fixture, stepped breakthroughs | `MULTILAYER` |
| **AT-030d** ⭐ | **Sign-inversion canary.** Sweep `wor_prime_slope` from −2.0 to +2.0 | **No negative slope ever returns `CHANNELLING`. No positive slope ever returns `CONING`.** Hard failure |
| AT-030e | Dry well, water cut 4% | `INSUFFICIENT_HISTORY` |
| AT-030f | Window containing a water-shutoff job | `LOW_CONFIDENCE`, discontinuity reported |

> [!WARNING]
> **`AT-030d` is the most important single test in the suite.** The inverted mapping was produced by a research pass on this project on 2026-09-23 and caught only by independent verification. A parameterised sweep is the only way to guarantee it cannot creep back in during a refactor.

### 2.3 TC-003 · `fillage_proxy()`

| ID | Test | Expected |
|---|---|---|
| AT-003a | Hand-computed fixture: `Ap=1.767, S=74, N=6.2, rt=0.83` | `78.5 blpd` to 3 s.f. |
| **AT-003b** ⭐ | `plunger_diameter_in` is `NULL` | **`UNAVAILABLE` with `missing_fields = ['plunger_diameter_in']`. Never a default** |
| AT-003c | Gas-lift well | `UNAVAILABLE`, *"not a rod-pumped well"* |
| AT-003d | Actual exceeds theoretical | `LOW_CONFIDENCE`, **not clamped** |
| AT-003e | Widening gap over 30 days | `is_diverging = True`, positive trend slope |

### 2.4 TC-004 · `check_offsets()`

| ID | Test | Expected |
|---|---|---|
| AT-032a | Subject −31%, six offsets near 0% | `WELL_SPECIFIC` |
| **AT-032b** ⭐ | Subject −22%, six offsets −19% to −21% | **`RESERVOIR_DECLINE`** |
| AT-032c | Only two eligible offsets | `INSUFFICIENT` |
| AT-032d | Neighbours in a different zone | Excluded; same-zone preferred |
| AT-032e | Shut-in neighbour | Excluded from the median |

### 2.5 TC-005 · `detect_mechanical_signature()`

| ID | Test | Expected |
|---|---|---|
| AT-022a–f | One crafted fixture per signature: pump wear, tubing leak, wax, scale, rod part, gas interference | Each returns **its own label and no other** |
| AT-022g | `casing_vented = TRUE` | `DISCRIMINATOR_UNAVAILABLE`, fallback with `confidence = LOW` |
| AT-022h | Healthy well | `NONE` |

### 2.6 TC-007, TC-008, TC-009, TC-010, TC-011, TC-012, TC-013

| ID | Test | Expected |
|---|---|---|
| AT-020a | Residual at exactly −25% for 7 producing days | `FLAG`. Boundary is inclusive as specified |
| AT-020b | Residual −30% but a choke change occurred in the window | **Trigger A does not fire** |
| AT-020c | Producing days interrupted by `NULL` days | `NULL` days neither count toward nor break persistence |
| AT-021a | Run-lives `[180, 210, 195]` with differing throughput | Throughput-weighted p50 ≠ calendar p50 |
| AT-021b | Well with one prior intervention | `INSUFFICIENT_HISTORY` — **not a flag, not an error** |
| AT-040a | Iterate every mechanism code | All 28 catalogue rows reachable |
| AT-040b | `offset_verdict = RESERVOIR_DECLINE` with a strong mechanical signature | **`NO_JOB_JUSTIFIED` wins unconditionally** |
| AT-040c | Edit `job_catalogue` duration, re-run | Behaviour changes with **no code change** (`NFR-006`) |
| AT-041a | Full synthetic year | Rigless share = `24% ± 3pp` (`00_overview` §5.3 — derived, not asserted; the old 27% is wrong) |
| AT-041b | Re-perforation and add-perforation | `requires_rig = TRUE` in every case |
| **AT-041c** ⭐ | **Rig/rigless canary.** Iterate all 28 `job_catalogue` rows against `lift_type = 'SRP'` | **No job requiring access below the pump seating nipple is marked rigless** (`TC-008.6`). Hard failure |
| AT-050a | Hand-computed deferred barrels | Matches to 3 s.f. |
| AT-050b | Job type with 3 historical instances | `INSUFFICIENT_HISTORY`; `P(success)` multiplier not applied |
| AT-050c | ₹2 cr / 10 rig-days vs two ₹1.2 cr / 3 rig-days | The pair ranks higher |
| AT-011a | Item out of stock at Nazira | Resolves to Sivasagar, `+2` transit days |
| AT-011b | Two short items with different transit | Earliest start reflects the **worst**, not the first |
| AT-053a | GK-129 history query | Returns the 1998 completion and 2019 workover reports with dates |
| AT-053b | Every returned `gcs_uri` | Resolves to an openable document |
| AT-053c | Well with no documents | Returns empty — **no fabricated citation** |
| AT-052 | Every numeric in the GK-129 draft plan | Each has a `provenance` entry naming its tool call or document |

### 2.7 TC-016, TC-017, TC-018 · Acts 1 and 2

| ID | Test | Expected |
|---|---|---|
| AT-106 | A well whose `lat`/`lon` are `NULL` in `well_master` | Appears in `excluded_wells` with a reason. **Never rendered at a substituted coordinate** (`AS-009`) |
| AT-107 | Force each of the three render tiers | `render_tier` matches the tier actually used; the narration names it when not `TIER_1` |
| AT-108 | Request a field other than Geleki | `UNAVAILABLE` naming the field. **Never a silent Geleki result** |
| AT-110b | A well with a 40-day shut-in inside the window | Renders as a **gap**. Zero points and interpolated points both fail |
| AT-110c | GK-129 over 36 months | The 2019 water shutoff appears as a marker with `outcome = FAILED` |
| AT-110d | A metric absent from `daily_production` | Omitted **and named in `message`**; the remaining metrics still return |
| **AT-112b** | `query_wells(order_by='oil_rate_bopd')`, 20 calls | **`caveat` is non-empty on all 20.** This is the deterministic half of `AT-112` |
| AT-112c | Same call with a shut-in well in the field | The shut-in well is excluded and counted in `excluded_reasons`, not ranked as the lowest producer |
| AT-112d | Both orderings on the same `as_of` | Every row carries `oil_rate_bopd`, `expected_bopd`, `gap_bopd` and `residual_pct`, so the two tables are directly comparable (`TC-018.5`) |

### 2.8 TC-014 · `generate_report()`

| ID | Test | Expected |
|---|---|---|
| AT-145a | A month of synthetic `well_run` partitions | Monthly aggregate equals the summed dailies **exactly**. Feeds `AT-073` |
| AT-145b | A month with zero detected errors | "Where the system was wrong" is present and states zero explicitly (`TC-014.2`) |
| AT-145c | Most recent nightly run marked failed | Report declares itself stale and names the last good run (`TC-014.3`) |
| AT-145d | Late-arriving production for a past date | A previously generated report is **unchanged** (`RS-102`) |

> [!NOTE]
> **`TC-015 schedule_rigs()` has no L1 tests, deliberately.** It is P2 and Act 5 is optional. This is recorded here so the gap is a decision rather than an oversight — **if Act 5 is promoted to the core demo, this note is the blocker to clear first.**

---

## 3. L2 — Data contract tests

Every `DC-nnn` invariant in [02](./02_data_contract.md) is an assertion in `generator/validate.py`, run on every regeneration.

| ID | Invariant | Assertion |
|---|---|---|
| **AT-014** ⭐ | `DC-014` | `COUNT(*) WHERE is_producing = FALSE AND oil_rate_bopd IS NOT NULL` = **0** |
| AT-090 | `DC-090` | Mass balance within 2% |
| AT-091 | `DC-091` | Water cut non-decreasing on 90-day rolling mean, except across a water-shutoff job |
| **AT-092** | `DC-092` | **Two assertions, both must pass.** `FRACTION_DOWN_ACTIVE` = **16.3% ± 1.0pp** *and* `FRACTION_DOWN_TOTAL` = **20.0% ± 1.0pp**. Corrected 2026-09-23 (`D-15`); tolerance widened from ±0.5pp because `FRACTION_DOWN_TOTAL` rests on a **fitted** 4.5% idle carve-out and a tolerance tighter than the uncertainty in a fitted parameter is false precision |
| AT-093 | `DC-093` | Failure-code distribution within ±3pp of `00_overview` §5.3 |
| AT-094 | `DC-094` | Every well has ≥2 prior interventions or is marked `INSUFFICIENT_HISTORY` |
| AT-096 | `DC-096` | Every `well_run` row has a non-empty `tool_trace` |
| AT-097 | `DC-097` | Referential integrity across all foreign keys |
| AT-013D | `DC-013` | Exactly 36 months of continuous daily rows per well — no gaps |
| AT-046 | `DC-046` | ~40% of recent episodes censored. **Zero censoring fails** |
| AT-042D | `DC-042` | Job success rate 60–70%. **100% fails** |

### 3.1 Signature discriminability

| ID | Test | Pass band |
|---|---|---|
| AT-SD040 | Train a 6-class classifier on the 30 days preceding each failure | macro-F1 **0.70–0.85** |

Below 0.60 the signatures are not separable and the Act 3 table becomes six identical diagnoses. Above 0.95 they are cartoonishly separable and any reviewer will say so.

---

## 4. L3 — Model gates

| ID | Gate | Threshold | On failure |
|---|---|---|---|
| AT-023a | Confidence interval is model-derived | Not a fixed ± multiple of `ettf` | Fix derivation |
| AT-023b | C-index on time-based holdout | **≥ 0.65**; expected band **0.65–0.72** — the defensible range on daily production data alone with no dynacard telemetry, set deliberately below vendor claims because vendor performance numbers are rejected under this project's evidence standard | Do not ship the model |
| AT-023c | Beats the Trigger B baseline | Strictly greater on the same holdout | **Do not ship the model.** Say so |
| **AT-023d** | AUC | **> 0.95 = hard build failure** | Data leak. Return to `03` §5 and increase frailty variance |
| AT-023e | Calibration of predicted intervals | Observed coverage within ±10pp of nominal | Recalibrate |
| AT-023f | Split integrity | No well appears in both train and test | Fix the split — this is fatal leakage |

> [!CAUTION]
> **`AT-023c` is the test most likely to be quietly skipped, and it is the one that protects intellectual honesty.** If "days since last intervention, throughput-weighted" performs as well as a random survival forest, we do not need the model — and the right response is to say that out loud, not to tune until the model wins.

---

## 5. L5 — Acceptance tests by requirement

### 5.1 Act 1

| ID | Requirement | Test |
|---|---|---|
| AT-101 | FR-001 | 142 points render at their true coordinates, in-card, under 8s |
| AT-102 | FR-002 | Colour counts equal `well_run`; changing a trigger state changes the colour |
| AT-103 | FR-003 | A 2 BOPD well remains visible and clickable |
| AT-104 | FR-004 | Tooltip values match `well_run` |
| AT-105 | FR-005 | A request for another field returns that field **or an explicit "no data"** — never silently Geleki |

### 5.2 Act 2

| ID | Requirement | Test |
|---|---|---|
| AT-110 | FR-010 | Plotted values equal `daily_production` for GK-129 |
| AT-111 | FR-011 | All 142 fits produced; low-`r²` fits flagged, not silently used |
| **AT-112** ⭐ | FR-012 | **20 consecutive runs. All three parts present every time** — literal answer, explicit statement that rate ranking misleads, residual-ranked alternative |
| AT-013 | FR-013 | A 5 BOPD well at expected decline does **not** outrank a 60 BOPD well 40% below its own curve |

### 5.3 Act 3

| ID | Requirement | Test |
|---|---|---|
| AT-120 | FR-020–023 | All four triggers demonstrably fire on their designated fixtures |
| AT-121 | FR-030 | GK-129 → `CHANNELLING`; GK-103 → `CONING` |
| AT-122 | FR-031 | GK-055 fillage gap matches the hand computation |
| AT-123 | FR-032 | GK-141 → `RESERVOIR_DECLINE` |
| AT-124 | FR-033 | GK-129 diagnosis names ≥3 evidence items and ≥2 rejected alternatives with reasons |
| AT-125 | FR-040 | Every flagged well receives a specific job from the catalogue |
| AT-126 | FR-041 | Rigless jobs appear in a separate queue consuming zero rig-days |
| **AT-127** ⭐ | FR-042 | **At least one well returns `NO JOB JUSTIFIED` with offset evidence attached** |
| AT-128 | FR-050 | Ranking is by value per rig-day; verified against a hand-worked ordering |
| AT-129 | FR-051 | `P(success)` states its sample, e.g. *"11 of 18"* |
| AT-130 | FR-052 | The GK-129 plan renders every mandatory section |
| AT-131 | FR-053 | Both citations resolve and display their dates |
| AT-132 | FR-054 | The plan recommends the dearer squeeze and explains the 2019 straddle-packer failure |
| **AT-061** ⭐ | FR-061 | **≥4 of the 7 Act 3 rows are flagged by triggers A/B/C with the model disabled** |

> [!IMPORTANT]
> **`AT-061` is run with the model switched off.** It is the executable form of the circularity answer. If fewer than four rows survive, the scripted response in [07](./07_agent_spec.md) §6 is **false** and must be rewritten before anyone says it in a room.

### 5.4 Act 4

| ID | Requirement | Test |
|---|---|---|
| AT-140 | FR-070 | Two consecutive nights: "new overnight" equals the set difference |
| AT-141 | FR-071 | Committed rig-days never exceed available rig-days |
| **AT-072b** ⭐ | FR-072 | **"Where the system was wrong" is present and non-empty.** With zero errors it states so explicitly rather than being omitted |
| **AT-073** ⭐ | FR-073 | **Monthly totals equal the sum of constituent dailies exactly. Equality, not tolerance** |
| AT-143 | FR-074 | A scheduled trigger produces a dated artefact with no interactive session |
| AT-144 | RS stale rule | With the nightly run failed, the report declares itself stale |

### 5.5 Cross-cutting

| ID | Requirement | Test |
|---|---|---|
| AT-080 | FR-080 | Static analysis: **no code path writes to any system of record** |
| AT-081 | FR-081 | `REJECT` without a reason is refused |
| **AT-083** ⭐ | FR-083 | **For all 20 numerics in the GK-129 plan, a provenance record names the producing tool call or source document** |
| AT-084 | FR-084 | Act 3 displays ≥8 named tool calls with durations |
| AT-060 | FR-060 | The synthetic-data banner is present in a screenshot of every act |

---

## 6. L6 — Rehearsal checklist

| # | Check | Pass condition |
|---|---|---|
| 1 | Full run-through with Act 5 | ≤ 11:15 |
| 2 | Compressed run-through, Act 5 cut | ≤ 9:30 |
| 3 | Latency on **conference wifi** | Every act inside `NFR-001` |
| 4 | Push-back fires | 20/20 |
| 5 | PDF citation opens | Live, in front of the room |
| 6 | Offline fallback video | Every act recorded and playable |
| 7 | Chan convention on screen | Coning negative, channelling positive |
| 8 | Circularity answer | Delivered from memory, not read |
| 9 | Synthetic banner | Visible throughout |
| 10 | `NO JOB JUSTIFIED` row | Pointed at deliberately |

---

## 7. Traceability matrix

**Generated, not hand-maintained.** An `FR` with no `AT` is a build failure.

| Requirement | Priority | Tests |
|---|---|---|
| FR-001 | P0 | AT-101 |
| FR-002 | P0 | AT-102 |
| FR-003 | P1 | AT-103 |
| FR-004 | P1 | AT-104 |
| FR-005 | P1 | AT-105 |
| FR-010 | P0 | AT-110 |
| FR-011 | P0 | AT-111, AT-001a–f |
| **FR-012** ⭐ | P0 | **AT-112** |
| FR-013 | P0 | AT-013, AT-050c |
| FR-020 | P0 | AT-020a, AT-020b, AT-020c, AT-120 |
| FR-021 | P0 | AT-021a, AT-021b, AT-120 |
| FR-022 | P0 | AT-022a–h, AT-120 |
| FR-023 | P0 | AT-023a–f, AT-120 |
| FR-030 | P0 | AT-030a–f, AT-121 |
| FR-031 | P0 | AT-003a–e, AT-122 |
| **FR-032** ⭐ | P0 | AT-032a–e, AT-123 |
| FR-033 | P1 | AT-124 |
| FR-040 | P0 | AT-040a–c, AT-125 |
| FR-041 | P0 | AT-041a, AT-041b, AT-126 |
| **FR-042** ⭐ | P0 | AT-040b, **AT-127** |
| FR-050 | P0 | AT-050a–c, AT-128 |
| FR-051 | P1 | AT-050b, AT-129 |
| **FR-052** ⭐ | P0 | AT-052, AT-130 |
| **FR-053** ⭐ | P0 | AT-053a–c, AT-131 |
| FR-054 | P1 | AT-132 |
| FR-060 | P0 | AT-060 |
| FR-061 | P0 | **AT-061** |
| FR-070 | P0 | AT-140 |
| FR-071 | P0 | AT-141 |
| **FR-072** ⭐ | P0 | **AT-072b** |
| FR-073 | P0 | **AT-073** |
| FR-074 | P1 | AT-143, AT-144 |
| FR-080 | P0 | AT-080 |
| FR-081 | P0 | AT-081 |
| FR-082 | P2 | *deferred — not required for the demo* |
| **FR-083** ⭐ | P0 | **AT-083**, AT-052 |
| FR-084 | P1 | AT-084 |

**Coverage: 37 of 38 requirements have at least one test.** `FR-082` (feedback retraining) is explicitly deferred and marked as such — it is specified so the architecture does not preclude it, not built for the demo.

---

## 8. Definition of done

A phase is done when **all** of these hold. Not "mostly."

| Phase | Done when |
|---|---|
| **0 · Spikes** | `RISK-001` and `RISK-002` are **answered**, and the chosen map tier is recorded |
| **1 · Data** | Every L2 test passes, including `AT-092` availability identity (**both** `FRACTION_DOWN_ACTIVE` and `FRACTION_DOWN_TOTAL`) and `AT-SD040` discriminability |
| **2 · Tools** | Every L1 test passes. **`AT-030d` was written before `chan_diagnostic()`** |
| **3 · Model** | Every L3 gate passes, including `AT-023c` beating the Trigger B baseline |
| **4 · Agent** | Every P0 L5 test passes, including `AT-112` at 20/20 and `AT-061` with the model disabled |
| **5 · Reports** | `AT-073` exact equality and `AT-072b` non-empty error section |
| **6 · Rehearsal** | All ten L6 checks, twice, on the demo network |

> [!CAUTION]
> **The single most likely way this build fails is `AT-030d` being written after `chan_diagnostic()` rather than before.** Once an implementation exists, the test gets written to match it — and if the implementation is inverted, so is the test. The sign convention must be fixed by a test authored from [00_overview.md §6](./00_overview.md), before anybody opens the implementation file.
