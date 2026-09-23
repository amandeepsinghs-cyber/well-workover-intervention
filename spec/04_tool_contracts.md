# 04 · Tool Contracts

**Version:** 1.0 · **Date:** 2026-09-23
**Parent:** [00_overview.md](./00_overview.md) · **Tested by:** [08_test_plan.md](./08_test_plan.md)

---

## 0. The answer, first

> **These eighteen functions are the system. The language model is a narrator wrapped around them. Every number that ever reaches the Asset Manager originates in exactly one of these returns, or in a cited document — and that property is what makes the tool-call trace worth putting on screen.**

If a behaviour is not specified here, the agent must not exhibit it.

---

## 1. Conventions

### 1.1 Common types

```python
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Literal

WellId    = str      # 'GK-129', matches ^GK-\d{3}$
JobCode   = str      # FK to job_catalogue
Bopd      = float    # barrels of oil per day
Blpd      = float    # barrels of liquid per day
KgCm2     = float    # pressure, ONGC onshore convention
Metres    = float
Days      = float

class Confidence(str, Enum):
    HIGH   = "HIGH"
    MEDIUM = "MEDIUM"
    LOW    = "LOW"

class ToolStatus(str, Enum):
    OK                       = "OK"
    UNAVAILABLE              = "UNAVAILABLE"              # required input missing
    INSUFFICIENT_HISTORY     = "INSUFFICIENT_HISTORY"     # not enough data
    LOW_CONFIDENCE           = "LOW_CONFIDENCE"           # computed but unreliable
    DISCRIMINATOR_UNAVAILABLE = "DISCRIMINATOR_UNAVAILABLE"  # physics precondition unmet

@dataclass(frozen=True)
class ToolResult:
    status: ToolStatus
    value: object | None            # None unless status == OK
    missing_fields: list[str]       # populated when UNAVAILABLE
    message: str                    # human-readable, appears in the draft plan
    provenance: dict                # input hash, config_version, duration_ms
```

### 1.2 The seven rules every tool obeys

| ID | Rule |
|---|---|
| **TC-000.1** | **Never substitute a default for a missing input.** Return `UNAVAILABLE` and name the missing field in `missing_fields` |
| **TC-000.2** | **Never raise for a data condition.** Exceptions are reserved for programming errors. A well with no history is `INSUFFICIENT_HISTORY`, not a stack trace |
| **TC-000.3** | **Deterministic.** Identical inputs → byte-identical outputs. Seeds fixed and recorded (`NFR-002`) |
| **TC-000.4** | **Pure.** No writes to source tables. The only writer is the nightly orchestrator, to `well_run` |
| **TC-000.5** | **Self-describing.** Every result carries `provenance` sufficient to reproduce it |
| **TC-000.6** | **Units in the field name or the type.** `_bopd`, `_kgcm2`, `_m`, `_days`, `_pct`. No bare numbers |
| **TC-000.7** | **`NULL` is not zero.** Non-producing days are excluded from fits and from persistence counts, never treated as zero rate (`DC-014`) |

> [!CAUTION]
> **TC-000.1 exists because of the fillage proxy.** If `plunger_diameter_in` is missing and the tool quietly assumes 1.5", the system produces a confident, wrong fluid-pound diagnosis and recommends a rod-string job on a healthy well. **A visible `UNAVAILABLE` is always better than an invisible default.**

---

## 2. TC-001 · `fit_decline_curve()`

**Purpose:** fit an Arps hyperbolic decline to a single well's own production history. Everything downstream depends on the residual this produces.
**Serves:** `FR-011`, `FR-020` · **Used in:** Act 2, Act 3

```python
def fit_decline_curve(
    well_id: WellId,
    as_of: date,
    lookback_months: int = 36,
    min_producing_days: int = 180,
) -> ToolResult:  # value: DeclineFit
```

```python
@dataclass(frozen=True)
class DeclineFit:
    well_id: WellId
    qi_bopd: float           # initial rate of the fitted curve
    b: float                 # hyperbolic exponent, [0.0, 2.0]
    di_per_day: float        # initial decline rate
    r_squared: float
    n_points: int            # producing days used
    n_tested_points: int     # of which data_source = 'TESTED'   (DP-001)
    expected_bopd: float     # fitted value at as_of
    actual_bopd: float       # 7-day mean of producing days ending as_of
    residual_pct: float      # (actual - expected) / expected * 100
    residual_series: list[tuple[date, float]]
    fit_quality: Confidence
    basis_changes: list[date]  # allocation basis changes excluded   (DP-003)
    allocation_note: str | None  # rendered verbatim by the agent     (DP-005)
```

**Method**
```
q(t) = qi / (1 + b · Di · t)^(1/b)

Weighted non-linear least squares on log(q) to stabilise variance.

WEIGHTS (DP-001):
  data_source = 'TESTED'      w = 3.0    measured
  data_source = 'ALLOCATED'   w = 1.0    apportioned from the GGS total
  data_source = 'ESTIMATED'   w = 0.5

Fit window excludes:
  - days where is_producing = FALSE                        (DC-014)
  - the 30 days following any workover_history.end_date    (transient)
  - well_tests rows with test_quality = 'REJECTED'         (DC-021)
  - ⚠ any step coincident with a change in
    allocation_basis_id — this is a BASIS change,
    NOT a rate change                                      (DC-071, DP-003)
```

| Condition | Status | Behaviour |
|---|---|---|
| Fewer than `min_producing_days` producing days | `INSUFFICIENT_HISTORY` | No fit. Well excluded from Trigger A |
| `r_squared < 0.5` | `LOW_CONFIDENCE` | Fit returned, `fit_quality = LOW`. **Trigger A must not fire on a LOW fit** |
| Optimiser fails to converge | `LOW_CONFIDENCE` | Fall back to exponential (`b = 0`) and say so in `message` |
| **`n_tested_points = 0` in the trailing 90 d** | **`OK`, capped** | **`fit_quality` capped at `MEDIUM`. Trigger A may reach `FLAG` but never `URGENT`** (`DP-002`, `DC-070`). `allocation_note` is populated |
| **A basis change falls inside the trailing 30 d** | **`LOW_CONFIDENCE`** | The most recent residual is not trustworthy yet. **Report, do not suppress** |
| Otherwise | `OK` | — |

> [!CAUTION]
> **`TC-001.7` — the allocation invariant.** Most ONGC onshore daily per-well production is **allocated, not measured**: the GGS total is apportioned across wells in the ratio of their last well tests. **A well's daily rate therefore moves when a *neighbour* is re-tested.** Fitted naively, that step is indistinguishable from a 30% mechanical rate loss — and it will fire Trigger A across every well on that GGS at once.
>
> **The tell is the cohort.** A genuine failure hits one well. A basis change hits every well on the GGS on the same day. `TC-001` must detect the cohort and exclude the step.

> [!NOTE]
> **`TC-001.8` — say the basis out loud.** Where `n_tested_points` is low, `allocation_note` is populated and the agent renders it verbatim: *"Trigger A fired on GK-129. The last well test was 9 days ago; the intervening rates are allocated, so this is flagged rather than escalated."* **That sentence is worth more than a cleaner-looking number.**

> [!NOTE]
> **`b ∈ [0.5, 1.0]` is expected for a mature waterflood.** A fitted `b` outside `[0.0, 2.0]` indicates the data is not decline-like — usually a well that has been worked over mid-window. Clamping silently would hide that, so the bound is enforced and the clamp is reported in `message`.

**Worked example — GK-129**
```
input:   well_id='GK-129', as_of=2026-09-23, lookback_months=36
output:  qi=41.2 bopd, b=0.68, di=0.00091/d, r²=0.87, n=982, n_tested=71
         expected=26.1 bopd, actual=18.0 bopd, residual=-31.0%
         fit_quality=HIGH, basis_changes=[2025-04-11], status=OK
```

**Tests:** `AT-001a` known-Arps synthetic recovers parameters to 1%; `AT-001b` all-NULL well returns `INSUFFICIENT_HISTORY`; `AT-001c` post-workover transient excluded; `AT-001d` deterministic across repeated calls; **`AT-001e` a synthetic allocation basis step injected across a whole GGS cohort must NOT produce a residual at any well in that cohort**; **`AT-001f` a well with zero tested points in 90 d cannot reach `URGENT`**.

---

## 3. TC-002 · `chan_diagnostic()` ⚠ HIGHEST RISK

**Purpose:** classify the excess-water mechanism from the WOR / WOR′ log-log diagnostic (Chan, **SPE-30775**, 1995).
**Serves:** `FR-022`, `FR-030` · **Used in:** Act 3

```python
def chan_diagnostic(
    well_id: WellId,
    as_of: date,
    window_days: int = 90,
    min_water_cut_pct: float = 20.0,
) -> ToolResult:  # value: ChanDiagnosis
```

```python
class WaterMechanism(str, Enum):
    CONING        = "CONING"
    CHANNELLING   = "CHANNELLING"
    MULTILAYER    = "MULTILAYER"
    NORMAL        = "NORMAL_DISPLACEMENT"
    INDETERMINATE = "INDETERMINATE"
    # positive WOR' slope attributable to a paired injector, not the formation
    INJECTOR_BREAKTHROUGH = "INJECTOR_BREAKTHROUGH"
    # positive WOR' slope, injector evidence absent or ambiguous.
    # THIS IS A VALID TERMINAL ANSWER, not a failure to decide.
    CHANNELLING_OR_INJECTOR = "CHANNELLING_OR_INJECTOR_BREAKTHROUGH"

@dataclass(frozen=True)
class ChanDiagnosis:
    well_id: WellId
    mechanism: WaterMechanism
    wor_slope: float          # d(log WOR)/d(log t)
    wor_prime_slope: float    # THE discriminator
    r_squared: float
    confidence: Confidence
    water_cut_start_pct: float
    water_cut_end_pct: float
    series: list[tuple[date, float, float]]   # date, WOR, WOR'
    # injector pairing (SD-034 … SD-037)
    paired_injectors: list[WellId]
    injector_rate_step: float | None   # lagged step at the paired injector
    injector_lag_days: int | None      # 20–70 d where detected
    discriminating_evidence: str | None  # what separated the two, or why it could not
```

### 3.1 The classification rule — normative

> [!WARNING]
> **This table is the single most dangerous piece of logic in the system. It is stated normatively in [00_overview.md §6](./00_overview.md) and reproduced here verbatim. Do not derive it from memory and do not trust a secondary source over it.**
>
> | `wor_prime_slope` | Mechanism | Job | Rig? |
> |---|---|---|---|
> | **< −0.10** | **CONING** | Choke back / reduce drawdown | **Rigless, < 1 day** |
> | **> +0.30** | **→ go to §3.2.** Either **CHANNELLING** or **INJECTOR_BREAKTHROUGH** | Cement squeeze **or** injection reallocation | **Rig 5–10 d, or rigless** |
> | −0.10 … +0.30, low variance | MULTILAYER | Selective isolation | Rig, 3–7 days |
> | Negative then positive | CONING → late CHANNELLING | Stage: choke first, squeeze later | Mixed |
> | `r² < 0.4` | INDETERMINATE | No water job recommended on this evidence | — |
>
> **Inverted, this recommends a seven-day rig job and a cementing unit on a well that needed a thirty-minute choke adjustment.**

**Why the signs go the way they do** — so it can be re-derived rather than memorised:

- **Coning is gravity-opposed and self-limiting.** As drawdown pulls the contact upward, the water column's hydrostatic head brakes further growth; the cone approaches pseudo-steady state, so the *rate of change* of WOR decays. **Derivative falls.**
- **Channelling has no stabilising force.** Water sweeps a conductive path, relative permeability to water rises while oil falls, and fractional flow accelerates toward unity. **Derivative holds or rises.**

### 3.2 `TC-002.5` — the injector branch, on a positive slope

> [!CAUTION]
> **Chan produces three classes. The field has four mechanisms. A positive WOR′ slope is produced by BOTH formation channelling AND injector breakthrough, and Chan cannot separate them — because the evidence that separates them is not in this well's data.**
>
> The two need **different jobs on different wells**: a cement squeeze on *this producer*, versus **reallocating injection at a neighbouring injector** — which is cheaper, rigless, and does not touch the producer at all.

```
IF wor_prime_slope > +0.30:

    look up paired_injectors from well_offsets            (SD-034)
    for each, test for a rate STEP in the window
    [as_of − 70 d, as_of − 20 d]

    ├─ step found, single dominant injector, r² ≥ 0.5
    │       → INJECTOR_BREAKTHROUGH
    │         job:  reallocate / curtail injection        RIGLESS
    │         discriminating_evidence populated
    │
    ├─ no step found at any paired injector, and the well
    │  HAS paired injectors with complete rate history
    │       → CHANNELLING
    │         job:  cement squeeze + reperforation        RIG, 5–10 d
    │         discriminating_evidence = "no injection step
    │                                    in the lag window"
    │
    └─ no paired injector, incomplete injector history,
       or two or more injectors stepped
            → CHANNELLING_OR_INJECTOR_BREAKTHROUGH
              job:  TRACER OR INJECTION SURVEY — not a squeeze
              confidence: MEDIUM
```

| Rule | Statement |
|---|---|
| **TC-002.5** | **A positive WOR′ slope alone must never return `CHANNELLING`.** It returns `CHANNELLING` only after the injector test has been run and come back negative |
| **TC-002.6** | **`CHANNELLING_OR_INJECTOR_BREAKTHROUGH` is a valid terminal answer and must be rendered as one.** Naming two candidate mechanisms and the survey that separates them is a better answer than confidently naming one. **This is the refusal behaviour the whole system exists to demonstrate, applied to a diagnosis rather than a ranking** |
| **TC-002.7** | `discriminating_evidence` is `NOT NULL` whenever the mechanism is `CHANNELLING` or `INJECTOR_BREAKTHROUGH`. **If we cannot say what separated them, we have not separated them** |

> **This costs one join and no vendor can do it.** Single-well analytics products are structurally incapable of the injector branch, because they look at one well at a time.

| Condition | Status |
|---|---|
| `water_cut < min_water_cut_pct` | `INSUFFICIENT_HISTORY` — no meaningful WOR |
| Fewer than 30 producing days in window | `INSUFFICIENT_HISTORY` |
| `r_squared < 0.4` | `LOW_CONFIDENCE`, mechanism `INDETERMINATE` |
| A water-shutoff job occurred in the window | `LOW_CONFIDENCE` — the series is discontinuous |
| **Positive slope, no paired-injector history available** | **`OK`**, mechanism `CHANNELLING_OR_INJECTOR_BREAKTHROUGH`, confidence `MEDIUM` |

**Worked examples**
```
GK-129  wor_prime_slope = +1.08, r²=0.91, wc 62% → 78% over 11 d
        paired injector GK-I07: no rate step in [−70, −20] d
        → CHANNELLING, confidence HIGH
          evidence: "no injection step in the lag window"

GK-117  wor_prime_slope = +0.94, r²=0.88
        paired injector GK-I03: +38% rate step at as_of − 44 d
        → INJECTOR_BREAKTHROUGH, confidence HIGH
          job: curtail GK-I03.  RIGLESS.  Saves a 7-day rig squeeze.

GK-141  wor_prime_slope = +0.61, r²=0.72
        two paired injectors, both stepped
        → CHANNELLING_OR_INJECTOR_BREAKTHROUGH, confidence MEDIUM
          job: tracer survey.  NOT a squeeze.

GK-103  wor_prime_slope = −0.42, r²=0.79
        → CONING, confidence HIGH
          job: choke back.  RIGLESS, < 1 day.
          (negative slope — the injector branch is never reached)
```

**Tests — written before the implementation (`RISK-006`):**
`AT-030a` analytically-generated coning fixture → `CONING`; `AT-030b` channelling fixture → `CHANNELLING`; `AT-030c` multilayer fixture → `MULTILAYER`; `AT-030d` **sign-inversion canary** — asserts a negative slope never returns `CHANNELLING`; `AT-030e` dry well → `INSUFFICIENT_HISTORY`.

---

## 4. TC-003 · `fillage_proxy()`

**Purpose:** detect fluid pound — the dominant mechanical failure driver in vertical, low-rate, high-water-cut rod-pumped wells.
**Serves:** `FR-022`, `FR-031` · **Used in:** Act 3 · **Blocked by:** `RISK-002`

```python
def fillage_proxy(well_id: WellId, as_of: date, window_days: int = 30) -> ToolResult
```

```python
@dataclass(frozen=True)
class FillageResult:
    well_id: WellId
    theoretical_displacement_blpd: float
    actual_liquid_blpd: float
    gap_blpd: float                 # theoretical − actual
    gap_pct: float
    volumetric_efficiency_pct: float
    trend_slope_blpd_per_day: float # widening gap ⇒ worsening
    is_diverging: bool
    confidence: Confidence
```

```
theoretical_displacement = 0.1166 × Ap(in²) × S(in) × N(spm) × runtime_fraction
  where Ap = π/4 × plunger_diameter_in²
        0.1166 = standard SRP displacement constant, bbl/d per in²·in·spm

gap = theoretical_displacement − actual_liquid_rate
volumetric_efficiency = actual / theoretical × 100
```

**The physics:** at low reservoir inflow the pump displaces more than the well delivers. The plunger falls through gas or void on the downstroke and slams into fluid. That compressive shock travels up the rod string and buckles it against the tubing **even in a perfectly vertical well**. A well running high SPM and long runtime while producing little liquid is destroying its own rod string, and it is visible in daily data.

| Condition | Status |
|---|---|
| Any of `plunger_diameter_in`, `stroke_length_in`, `spm`, `runtime_hours` is `NULL` | **`UNAVAILABLE`**, with the field named |
| `lift_type != 'SRP'` | `UNAVAILABLE`, message *"not a rod-pumped well"* |
| `volumetric_efficiency > 100%` | `LOW_CONFIDENCE` — physically impossible; indicates allocation error |

> [!CAUTION]
> **Volumetric efficiency above 100% means the data is wrong, not that the pump is exceptional.** Most likely cause is allocated rather than tested production (`DC-016`). Report it; do not clamp it.

**Worked example — GK-055**
```
Ap = π/4 × 1.5² = 1.767 in²   S = 74 in   N = 6.2 spm   runtime = 0.83
theoretical = 0.1166 × 1.767 × 74 × 6.2 × 0.83 = 78.5 blpd
actual = 51.2 blpd  →  gap = 27.3 blpd,  vol. eff. = 65.2%
trend = +0.31 blpd/day over 30 d  →  is_diverging = True
```

**Tests:** `AT-003a` hand-computed fixture to 3 s.f.; `AT-003b` missing plunger diameter → `UNAVAILABLE` naming it; `AT-003c` gas-lift well → `UNAVAILABLE`; `AT-003d` efficiency > 100% → `LOW_CONFIDENCE`.

---

## 5. TC-004 · `check_offsets()`

**Purpose:** decide whether an underperformance is a **well** problem or a **reservoir** problem. This is the tool that produces `NO JOB JUSTIFIED`.
**Serves:** `FR-032`, `FR-042` · **Used in:** Act 3

```python
def check_offsets(well_id: WellId, as_of: date, k: int = 6,
                  same_zone_only: bool = True) -> ToolResult
```

```python
class OffsetVerdict(str, Enum):
    WELL_SPECIFIC     = "WELL_SPECIFIC"
    RESERVOIR_DECLINE = "RESERVOIR_DECLINE"
    MIXED             = "MIXED"
    INSUFFICIENT      = "INSUFFICIENT"

@dataclass(frozen=True)
class OffsetResult:
    well_id: WellId
    verdict: OffsetVerdict
    subject_residual_pct: float
    offset_residuals: list[tuple[WellId, float, float]]  # id, residual%, distance_m
    offset_median_residual_pct: float
    excess_residual_pct: float      # subject − offset median
    n_offsets_used: int
    confidence: Confidence
```

**Decision rule**
```
excess = subject_residual − median(offset_residuals)

excess < −15pp                     → WELL_SPECIFIC      (this well is worse)
|excess| ≤ 5pp and offsets < −10%  → RESERVOIR_DECLINE  (everyone is down)
otherwise                          → MIXED
n_offsets_used < 3                 → INSUFFICIENT
```

| Rule | Statement |
|---|---|
| **TC-004.1** | Offsets must share `current_zone` where ≥3 same-zone neighbours exist. Comparing a Tipam well to a Barail well is meaningless |
| **TC-004.2** | Offsets currently shut-in are excluded — a shut-in well has no residual |
| **TC-004.3** | `RESERVOIR_DECLINE` **forces** `recommended_job_code = 'NO_JOB_JUSTIFIED'` downstream (`DC-065`) |

> [!IMPORTANT]
> **This tool matters more than it looks.** If six surrounding wells show the same decline, it is a reservoir or injection issue and **no workover will fix it**. A system that cannot reach that conclusion will send rigs to wells that do not need them — and will be discredited the first time an engineer notices.

**Worked examples**
```
GK-129  subject −31.0%, offsets median −3.2%, excess −27.8pp → WELL_SPECIFIC
GK-141  subject −22.0%, offsets median −19.4%, excess −2.6pp → RESERVOIR_DECLINE
```

**Tests:** `AT-032a` stable offsets → `WELL_SPECIFIC`; `AT-032b` all offsets down → `RESERVOIR_DECLINE`; `AT-032c` two offsets → `INSUFFICIENT`; `AT-032d` cross-zone neighbours excluded.

---

## 6. TC-005 · `detect_mechanical_signature()`

**Purpose:** discriminate the mechanical failure mode from surface variables alone.
**Serves:** `FR-022` · **Used in:** Act 3

```python
def detect_mechanical_signature(well_id: WellId, as_of: date,
                                window_days: int = 45) -> ToolResult
```

```python
class MechSignature(str, Enum):
    PUMP_WEAR        = "PUMP_WEAR"
    TUBING_LEAK      = "TUBING_LEAK"
    WAX              = "WAX"
    SCALE            = "SCALE"
    ROD_PART         = "ROD_PART"
    GAS_INTERFERENCE = "GAS_INTERFERENCE"
    NONE             = "NONE"
```

### 6.1 The signature table

| Mode | Liquid rate | CHP | THP | GOR | Onset |
|---|---|---|---|---|---|
| **Pump wear** | gradual decline | **rises** | flat | flat | weeks |
| **Tubing leak** | sharp drop | **flat** | flat | flat | 3–5 days |
| **Wax** | drops | flat | **rises** | flat | gradual / seasonal |
| **Scale** | **flat, then sudden bind** | flat | flat | flat | latent then instant |
| **Rod part** | **→ zero** | flat | falls | flat | instantaneous |
| **Gas interference** | erratic | rises | flat | **rises** | gradual |

**Why CHP rises on pump wear but not on a tubing leak:** as plunger-barrel clearance opens, lifted fluid falls back and the **annular fluid level rises**, compressing casing gas. On a tubing leak the fluid recirculates tubing-to-annulus rather than accumulating, so annular gas volume stays roughly constant.

> [!CAUTION]
> **That mechanism assumes the casing valve is closed.** If `well_master.casing_vented = TRUE`, CHP tracks flowline pressure and the discriminator is lost. The tool must return **`DISCRIMINATOR_UNAVAILABLE`** for vented wells and fall back to liquid-rate shape alone with `confidence = LOW`. **Producing a confident wrong answer here is worse than producing none.**

> [!NOTE]
> **THP is a wax indicator only.** It was in an earlier draft as a pump-wear signal and was dropped: on a rod-pumped well producing into a flowline, THP is set substantially by flowline and separator backpressure and is largely insensitive to declining downhole pump performance.

**Tests:** `AT-022a`–`AT-022f` one crafted fixture per signature, each returning its own label and nothing else; `AT-022g` vented-casing well → `DISCRIMINATOR_UNAVAILABLE`.

---

## 7. TC-006 · `predict_failure()`

**Purpose:** expected time-to-failure with an honest confidence interval.
**Serves:** `FR-023` · **Used in:** Act 3 · **Specified in detail by:** [05_model_spec.md](./05_model_spec.md)

```python
def predict_failure(well_id: WellId, as_of: date,
                    model_version: str | None = None) -> ToolResult
```

```python
@dataclass(frozen=True)
class FailurePrediction:
    well_id: WellId
    ettf_days: float
    ci_low_days: float
    ci_high_days: float
    predicted_date: date
    hazard: float                 # instantaneous hazard at as_of
    confidence: Confidence
    top_features: list[tuple[str, float]]   # name, attribution
    model_version: str
    baseline_ettf_days: float     # Trigger B alone, for comparison
```

| Rule | Statement |
|---|---|
| **TC-006.1** | The confidence interval is **derived from the model's survival distribution**, never a fixed ± percentage |
| **TC-006.2** | `baseline_ettf_days` is always returned so the model's marginal value is visible on every call |
| **TC-006.3** | Wells with `INSUFFICIENT_HISTORY` for Trigger B still receive a prediction, flagged `confidence = LOW` |
| **TC-006.4** | `top_features` come from the model's attribution, **not** from the LLM's reading of the output |

> [!IMPORTANT]
> **`baseline_ettf_days` is an honesty mechanism, not a diagnostic convenience.** If the model's prediction is consistently no better than "days since last intervention," that fact is visible on every single call rather than buried in an evaluation report nobody reads.

**Tests:** `AT-023a` returns a real interval, not a fixed multiple; `AT-023b` C-index on holdout ≥ 0.65; `AT-023c` beats the Trigger B baseline; `AT-023d` AUC > 0.95 fails the build.

---

## 8. TC-007 · `trigger_scan()`

**Purpose:** the nightly orchestration entry point. Composes TC-001 through TC-006 for every well.
**Serves:** `FR-020`, `FR-021`, `FR-022`, `FR-023` · **Used in:** Act 3

```python
def trigger_scan(field: str, as_of: date,
                 well_ids: list[WellId] | None = None) -> ToolResult
```

```python
@dataclass(frozen=True)
class TriggerResult:
    well_id: WellId
    trigger_a: Literal[None, "WATCH", "FLAG", "URGENT"]
    trigger_a_days: int
    trigger_a_residual_pct: float
    trigger_b: bool
    trigger_b_days_since: float
    trigger_b_p50_days: float
    trigger_c: MechSignature | WaterMechanism | None
    trigger_d: bool
    trigger_d_ettf_days: float | None
    any_fired: bool
    highest_severity: Literal[None, "WATCH", "FLAG", "URGENT"]
```

### 8.1 Trigger A

```
residual < -15%  → WATCH
residual < -25%  → FLAG
residual < -40%  → URGENT
sustained 7 consecutive PRODUCING days          (DC-014: NULL days neither count nor break)
AND no choke_size_64th change within the window
AND the decline fit is not LOW_CONFIDENCE
```

### 8.2 Trigger B

```
run_lives      = prior intervals from workover_history
weights        = cumulative fluid throughput over each interval
p50            = throughput-weighted median of run_lives
fires when days_since_last_intervention > p50
requires ≥ 2 prior interventions, else INSUFFICIENT_HISTORY  (DC-044)
```

> [!NOTE]
> **Throughput weighting, not calendar days.** A well that produced 400 blpd for 150 days has worked its pump far harder than one that produced 40 blpd for 150 days. Calendar age is a weak proxy for the thing that actually wears the equipment.

### 8.3 Triggers C and D
C fires on any non-`NONE` return from `TC-002` or `TC-005` at `confidence ≥ MEDIUM`.
D fires when `TC-006.hazard` exceeds the configured percentile of the field's hazard distribution.

**Tests:** `AT-020a` tiering boundaries exact; `AT-020b` choke change suppresses Trigger A; `AT-020c` NULL days neither count nor break persistence; `AT-021a` throughput weighting changes p50 vs calendar; `AT-021b` one prior intervention → `INSUFFICIENT_HISTORY`, not a flag and not an error.

---

## 9. TC-008 · `route_intervention()`

**Purpose:** map a diagnosed mechanism to a specific job from the 28-row catalogue.
**Serves:** `FR-040`, `FR-041`, `FR-042` · **Used in:** Act 3, Act 5

```python
def route_intervention(well_id: WellId, mechanism: str,
                       offset_verdict: OffsetVerdict,
                       evidence: dict) -> ToolResult
```

```python
@dataclass(frozen=True)
class InterventionRoute:
    well_id: WellId
    job_code: JobCode
    job_name: str
    requires_rig: bool
    equipment: str
    duration_days_min: float
    duration_days_max: float
    cost_band: Literal["LOW", "MED", "HIGH"]
    selection_evidence: str
    alternatives: list[tuple[JobCode, str, str]]  # code, name, why not chosen
    queue: Literal["RIG", "RIGLESS", "NONE"]
```

| Rule | Statement |
|---|---|
| **TC-008.1** | The mapping is **a lookup against `job_catalogue`, not code.** ONGC edits the table; no deployment (`NFR-006`) |
| **TC-008.2** | `offset_verdict == RESERVOIR_DECLINE` → `job_code = 'NO_JOB_JUSTIFIED'`, `queue = 'NONE'`, **unconditionally**, before any other rule |
| **TC-008.3** | At least one alternative with a stated rejection reason must be returned whenever one exists |
| **TC-008.4** | Prior failed attempts of the same job on the same well demote it and the demotion is stated |
| **TC-008.5** | **Re-perforation and add-perforation are always `requires_rig = TRUE`.** On an SRP well the rod string and pump occupy the tubing; a perforating gun cannot pass them. A pulling unit may suffice, but it is not a rigless wireline job |
| **TC-008.6** | **THE RIG/RIGLESS INVARIANT.** On a well with `lift_type = 'SRP'`, **any job requiring access below the pump seating nipple is `requires_rig = TRUE`, without exception.** Nothing enters the wellbore of a rod-pumped well without first pulling the rod string. Genuinely rigless work on an SRP well is confined to: hot oiling, chemical or solvent circulation down the annulus, inhibitor squeeze, choke and surface adjustment, prime-mover and surface-equipment repair, and annulus-accessible operations |

> [!CAUTION]
> **`TC-008.6` exists because this project has made the same error three times.** Re-perforation was queued as rigless wireline; a pump changeout was queued as rigless slickline; both were wrong for the same reason. The rigless share is not a technical detail — **it is a commercial claim in the pitch**: *"24% of these need no rig, so you already have capacity you did not know about."* If the catalogue over-counts rigless jobs, that number inflates and the claim is false in front of the only people in the room qualified to notice. `AT-041c` enforces the invariant across all 28 catalogue rows so it cannot recur.

**Worked example — GK-129**
```
mechanism='CHANNELLING', offset_verdict=WELL_SPECIFIC
→ job_code='WSO_SQUEEZE', 'Cement squeeze + reperforation'
  requires_rig=True, 5–10 d, cost_band=HIGH
  alternatives:
    ('WSO_STRADDLE', 'Straddle packer',
     'Cheaper and 3 days, but the 2019 attempt on this well failed at 14 months')
```

**Tests:** `AT-040a` all 28 rows reachable; `AT-040b` `RESERVOIR_DECLINE` always yields `NO_JOB_JUSTIFIED`; `AT-041a` rigless share within ±3pp over a synthetic year; `AT-041b` re-perforation never rigless; **`AT-041c`** no catalogue row requiring below-seating-nipple access on an SRP well is marked rigless; `AT-040c` editing the catalogue changes behaviour with no code change.

---

## 10. TC-009 · `estimate_uplift()`

**Purpose:** estimate post-intervention rate and deferred barrels avoided.
**Serves:** `FR-050` · **Used in:** Act 3, Act 5

```python
def estimate_uplift(well_id: WellId, job_code: JobCode, as_of: date) -> ToolResult
```

```python
@dataclass(frozen=True)
class UpliftEstimate:
    well_id: WellId
    current_bopd: float
    expected_post_job_bopd: float
    uplift_bopd: float
    deferred_bbl_avoided_12mo: float
    method: str                    # 'NODAL_SKIN' | 'ANALOGUE' | 'DECLINE_RESTORE'
    p_success: float
    p_success_n: int
    confidence: Confidence
```

```
deferred_bbl_avoided =
    current_rate × (expected_downtime_if_unplanned − expected_downtime_if_planned)
  + uplift_rate × remaining_months × 30.4
```

| Rule | Statement |
|---|---|
| **TC-009.1** | `p_success` comes from **this asset's own history by job type**, never vendor literature |
| **TC-009.2** | Fewer than 5 historical instances → `p_success_n < 5` and `INSUFFICIENT_HISTORY`; the multiplier is not applied |
| **TC-009.3** | `method` is always stated so the estimate can be challenged on its basis |

**Tests:** `AT-050a` hand-computed deferred barrels; `AT-050b` rare job type → `INSUFFICIENT_HISTORY`; `AT-051a` `p_success` states its sample.

---

## 11. TC-010 · `rank_candidates()`

**Purpose:** rank flagged wells by value per rig-day, in two separate queues.
**Serves:** `FR-050`, `FR-013` · **Used in:** Act 3, Act 5

```python
def rank_candidates(field: str, as_of: date,
                    realisation_per_bbl: float) -> ToolResult
```

```
net_value = deferred_bbl_avoided × realisation × P(success) − job_cost
PRIORITY  = net_value ÷ rig_days_consumed
```

| Rule | Statement |
|---|---|
| **TC-010.1** | **Divide by rig-days.** The scarce resource is rig-days, not money. A ₹2 cr job over 10 rig-days loses to two ₹1.2 cr jobs over 3 each |
| **TC-010.2** | **Rigless jobs rank in a separate queue** and never compete for rig-days |
| **TC-010.3** | Absolute production rate is **never** the primary sort key (`FR-013`) |
| **TC-010.4** | `NO_JOB_JUSTIFIED` wells are excluded from both queues |

**Tests:** `AT-013` a 5 BOPD well at expected decline must not outrank a 60 BOPD well 40% below its own curve; `AT-050c` rig-day division changes the order as specified.

---

## 12. TC-011 · `check_mro()`

```python
def check_mro(job_code: JobCode, required_date: date,
              primary_base: str = "NAZIRA") -> ToolResult
```

Returns per-item availability, the alternate base, transit days, the **governing blocker**, and the earliest feasible start. Must identify *which* item governs the date, not merely that something is short.

**Tests:** `AT-011a` out-of-stock item at Nazira resolves to Sivasagar with +2 days; `AT-011b` earliest feasible start reflects the worst item, not the first.

---

## 13. TC-012 · `search_well_history()`

**Purpose:** retrieve evidence from scanned workover and completion reports, with citation.
**Serves:** `FR-053`, `FR-054` · **Used in:** Act 3

```python
def search_well_history(well_id: WellId, query: str, top_k: int = 5) -> ToolResult
```

```python
@dataclass(frozen=True)
class DocumentHit:
    doc_id: str
    doc_type: str
    doc_date: date
    title: str
    gcs_uri: str
    excerpt: str
    relevance: float
```

| Rule | Statement |
|---|---|
| **TC-012.1** | Every hit carries `doc_date` and an openable `gcs_uri`. **A citation without a resolvable link is not a citation** |
| **TC-012.2** | Returns empty rather than fabricating. The agent must then say no document was found |
| **TC-012.3** | Excerpts are literal spans from the document, never paraphrased by a model |

> [!IMPORTANT]
> **This tool carries the whole "access data from anywhere" claim.** One scanned 2019 report, found and cited, is more persuasive than any architecture diagram — particularly when it argues *against* the system's own cheaper recommendation.

**Tests:** `AT-053a` GK-129 query returns the 1998 and 2019 documents with dates; `AT-053b` links resolve; `AT-053c` a well with no documents returns empty, not a hallucination.

---

## 14. TC-013 · `generate_draft_plan()`

**Purpose:** assemble the draft intervention plan. **The only tool the LLM materially contributes to — and it contributes prose, never numbers.**
**Serves:** `FR-052`, `FR-083` · **Used in:** Act 3

```python
def generate_draft_plan(well_id: WellId, run_date: date) -> ToolResult
```

Sections, all mandatory: why this well now · diagnosis with confidence and evidence · rejected alternatives with reasons · recommended job · alternative considered · value · logistics with blockers · preconditions · approval controls.

| Rule | Statement |
|---|---|
| **TC-013.1** | Every numeric value carries a `provenance` entry naming the producing tool call or source document |
| **TC-013.2** | The plan renders with `[UNAVAILABLE]` markers rather than omitting a section whose inputs are missing |
| **TC-013.3** | Status is always `AWAITING REVIEW`. There is no path to `APPROVED` inside this tool |

**Tests:** `AT-052` every numeric in the GK-129 plan has provenance; `AT-080` no code path writes to a system of record.

---

## 15. TC-014 · `generate_report()`

**Purpose:** daily / weekly / monthly aggregation. **Specified in detail by** [06_report_spec.md](./06_report_spec.md).
**Serves:** `FR-070`–`FR-074`

```python
def generate_report(field: str, period: Literal["DAILY","WEEKLY","MONTHLY"],
                    as_of: date) -> ToolResult
```

| Rule | Statement |
|---|---|
| **TC-014.1** | **Reads `well_run` and aggregates. Recomputes nothing.** If a monthly total disagrees with the sum of its dailies, that is a bug, not a reconciliation (`FR-073`) |
| **TC-014.2** | Monthly **must** include "Where the system was wrong." If there were genuinely no errors it says so explicitly rather than omitting the section |
| **TC-014.3** | If the most recent nightly run failed, the report declares itself stale rather than silently serving yesterday's |

---

## 16. TC-015 · `schedule_rigs()` · **P2, Act 5 only**

Workover Rig Scheduling Problem. Objective = rig cost **+ deferred production** (Aloise et al. 2006, DOI 10.1016/j.dam.2004.09.021 — NP-complete). Constraints: rig count, rig-class capability, geography and mobilisation, material availability.

| Rule | Statement |
|---|---|
| **TC-015.1** | Rigless jobs are **excluded from the optimisation entirely** — they do not consume the constrained resource |
| **TC-015.2** | Campaign batching by geography is explicit; saved rig-move days are reported separately |
| **TC-015.3** | Deferred candidates are listed **with the reason**, never silently dropped |
| **TC-015.4** | Replanning reports the trade-off in barrels, not just the changed schedule |

---

## 17. TC-016 · `render_well_map()` · **the first thing on screen**

**Purpose:** render the 142 Geleki wells at their true coordinates, sized by rate and coloured by state.
**Serves:** `FR-001`–`FR-005` · **Used in:** Act 1

> [!WARNING]
> **This tool carries `RISK-001` and it is the first thing the Executive Director sees.** If the A2UI renderer cannot draw a `geoshape` with a `projection`, the demo opens on a failure. The tier ladder below is therefore **part of the contract, not an operational fallback** — the tool declares which tier it rendered so the agent never claims a live map it did not draw.

```python
def render_well_map(
    field: str = "Geleki",
    as_of: date = ...,
    size_by: Literal["oil_rate_bopd", "liquid_rate_blpd", "deferred_bopd"] = "oil_rate_bopd",
    colour_by: Literal["status", "trigger_state", "queue", "days_to_failure"] = "trigger_state",
    include_shut_in: bool = True,
) -> ToolResult:  # value: WellMap
```

```python
@dataclass(frozen=True)
class MapPoint:
    well_id: WellId
    lat: float                   # WGS84, from well_master. NEVER synthesised at render time
    lon: float
    size_value: float | None     # None when the metric is NULL — rendered hollow, not zero
    colour_key: str              # 'URGENT' | 'FLAG' | 'WATCH' | 'HEALTHY' | 'SHUT_IN' | 'NO_JOB'
    tooltip: dict                # every value traced to well_run for this as_of

@dataclass(frozen=True)
class WellMap:
    field: str
    as_of: date
    points: list[MapPoint]
    n_rendered: int
    render_tier: Literal["TIER_1_VEGA_GEOSHAPE", "TIER_2_VEGA_XY", "TIER_3_STATIC_IMAGE"]
    basemap_attribution: str | None
    colour_legend: dict[str, str]
    size_legend: dict[str, float]
    excluded_wells: list[tuple[WellId, str]]   # well_id, reason
```

**The tier ladder**

| Tier | Implementation | Use when | What the agent must say |
|---|---|---|---|
| **1** | Vega-Lite `geoshape` + `projection`, real Assam basemap | `geoshape` renders in the target A2UI runtime | Nothing special — it is a live map |
| **2** | Vega-Lite point chart on raw lat/lon axes, no basemap | `geoshape` unsupported but Vega renders | *"Plotted on coordinates; the basemap layer is not available in this runtime"* |
| **3** | Pre-rendered static basemap PNG with plotted points, **plus a live data table** | Vega unavailable or too slow | *"This basemap is pre-rendered; the well data beside it is live"* |

| Rule | Statement |
|---|---|
| **TC-016.1** | **Coordinates come from `well_master` only.** A well with a `NULL` coordinate appears in `excluded_wells` with the reason. **It is never placed at a plausible-looking position** — a fabricated coordinate is the map equivalent of a fabricated number |
| **TC-016.2** | **`render_tier` is always returned and always surfaced.** Tier 3 must never be narrated as a live map (`AS-007`) |
| **TC-016.3** | A well with `size_value = None` renders as a hollow marker at minimum visible size. **`NULL` is not zero** (`DC-014`), and a shut-in well must remain clickable (`FR-003`) |
| **TC-016.4** | `colour_key` is read from `well_run` for `as_of`. The tool does not evaluate triggers; it reads the nightly result |
| **TC-016.5** | A request for a field other than Geleki returns `UNAVAILABLE` naming the field. **It never silently returns Geleki** (`FR-005`) |
| **TC-016.6** | Every `tooltip` value carries the `well_run` column it came from, so `AT-104` can diff the tooltip against the table |

| Condition | Status | Behaviour |
|---|---|---|
| Field not in the dataset | `UNAVAILABLE` | `missing_fields = ['field:<name>']` |
| No nightly `well_run` for `as_of` | `LOW_CONFIDENCE` | Renders the most recent run and states its date |
| Some wells lack coordinates | `OK` | Rendered set is complete-minus-excluded; `excluded_wells` populated and reported |
| Tier 1 unavailable | `OK` | Degrades one tier and records it in `render_tier` |

**Worked example**
```
render_well_map(field='Geleki', as_of=2026-09-23,
                size_by='oil_rate_bopd', colour_by='trigger_state')
→ OK
  n_rendered = 140,  render_tier = TIER_1_VEGA_GEOSHAPE
  colour_legend = {URGENT: 3, FLAG: 9, WATCH: 17, HEALTHY: 96, SHUT_IN: 12, NO_JOB: 3}
  excluded_wells = [('GK-160', 'lat/lon NULL in well_master'),
                    ('GK-171', 'lat/lon NULL in well_master')]
  message = "140 of 142 wells plotted. 2 excluded: no surveyed coordinates."
```

**Tests:** `AT-101` 142 points at true coordinates under 8 s; `AT-102` colour counts equal `well_run`; `AT-103` a 2 BOPD well stays visible and clickable; `AT-104` tooltips match `well_run`; `AT-105` another field returns an explicit no-data, never Geleki; **`AT-106`** a `NULL` coordinate is excluded and reported, **never placed**.

---

## 18. TC-017 · `plot_production()`

**Purpose:** return a production time series for one well, ready to chart. The visual half of Act 2.
**Serves:** `FR-010` · **Used in:** Act 2, and inside the Act 3 drill-down

```python
def plot_production(
    well_id: WellId,
    months: int = 36,
    metrics: list[Literal["oil","water","gas","liquid","water_cut","thp","chp","runtime"]] = ...,
    overlay_decline_fit: bool = False,
    overlay_interventions: bool = True,
) -> ToolResult:  # value: ProductionSeries
```

```python
@dataclass(frozen=True)
class SeriesPoint:
    d: date
    value: float | None          # None on non-producing days. NEVER 0.0
    source: Literal["ALLOCATED", "TESTED", "NULL"]

@dataclass(frozen=True)
class InterventionMarker:
    d: date
    job_code: JobCode
    label: str
    outcome: Literal["SUCCESS", "PARTIAL", "FAILED", "UNKNOWN"]

@dataclass(frozen=True)
class ProductionSeries:
    well_id: WellId
    series: dict[str, list[SeriesPoint]]
    units: dict[str, str]                      # 'oil' -> 'BOPD', 'water_cut' -> '%'
    axis_assignment: dict[str, Literal["LEFT","RIGHT"]]
    decline_fit: list[SeriesPoint] | None      # populated only if overlay_decline_fit
    interventions: list[InterventionMarker]
    n_producing_days: int
    n_null_days: int
```

| Rule | Statement |
|---|---|
| **TC-017.1** | **Non-producing days are `None`, and the chart shows a gap.** Interpolating across a shut-in period draws a smooth line through a well that was not running, which is a lie told in pixels (`DC-014`) |
| **TC-017.2** | `source` is returned per point. A `TESTED` point is a measurement; an `ALLOCATED` point is an estimate. **Where the renderer supports it, tested points are marked distinctly** |
| **TC-017.3** | The tool **returns data, it does not compute new data.** `water_cut` is read or derived by the single published definition `water / (oil + water) × 100`, and that definition is stated in `units` |
| **TC-017.4** | `overlay_decline_fit` calls `TC-001`; it never fits independently. One decline fit exists per well per night |
| **TC-017.5** | Intervention markers come from `workover_history`. **A failed job is marked as failed** — the 2019 GK-129 water shutoff must be visible as a failure on the chart |
| **TC-017.6** | Rate metrics and ratio metrics are assigned to opposite axes automatically, and the assignment is returned so the caption can state it |

| Condition | Status | Behaviour |
|---|---|---|
| Unknown `well_id` | `UNAVAILABLE` | `missing_fields = ['well_id']` |
| Requested metric not in `daily_production` | `OK` | That metric is omitted and **named in `message`**; the rest still return |
| Fewer than 90 days of any production | `INSUFFICIENT_HISTORY` | No series |
| `overlay_decline_fit` but the fit is `LOW_CONFIDENCE` | `LOW_CONFIDENCE` | Overlay drawn **and labelled low-confidence** |

**Tests:** `AT-110` plotted values equal `daily_production` for GK-129; **`AT-110b`** a shut-in stretch renders as a gap, not a zero line; **`AT-110c`** the 2019 failed water shutoff appears as a `FAILED` marker.

---

## 19. TC-018 · `query_wells()` · **powers the push-back**

**Purpose:** the general ranked-query tool behind Act 2's *"which are my lowest producing wells?"* — and behind the answer that follows it.
**Serves:** `FR-013` · **Used in:** Act 2

> [!IMPORTANT]
> **One tool, two orderings — that is the whole point.** The push-back beat is not the agent being clever; it is the agent calling the same tool twice with a different `order_by` and putting the two tables side by side. Specifying it as two tools would make the comparison look rhetorical rather than computed.

```python
def query_wells(
    field: str = "Geleki",
    as_of: date = ...,
    order_by: Literal[
        "oil_rate_bopd",           # absolute rate — the literal question
        "decline_residual_pct",    # below its OWN curve — the useful question
        "deferred_bopd",
        "days_to_failure",
        "water_cut_pct",
    ] = "decline_residual_pct",
    direction: Literal["ASC", "DESC"] = "ASC",
    limit: int = 10,
    filters: dict | None = None,   # e.g. {'status': 'PRODUCING', 'zone': 'Tipam'}
) -> ToolResult:  # value: WellRanking
```

```python
@dataclass(frozen=True)
class RankedWell:
    rank: int
    well_id: WellId
    oil_rate_bopd: float | None
    expected_bopd: float | None       # from the well's own Arps fit
    gap_bopd: float | None
    residual_pct: float | None
    water_cut_pct: float | None
    status: str
    fit_quality: Confidence | None

@dataclass(frozen=True)
class WellRanking:
    order_by: str
    direction: str
    rows: list[RankedWell]
    n_eligible: int
    n_excluded: int
    excluded_reasons: dict[str, int]
    caveat: str | None            # populated when order_by is misleading — see TC-018.2
```

| Rule | Statement |
|---|---|
| **TC-018.1** | **The literal question is always answered first and in full.** The tool never refuses an ordering because a better one exists |
| **TC-018.2** | **`order_by = 'oil_rate_bopd'` always returns a populated `caveat`**, stating that absolute rate ranking is misleading on mature wells because a low-rate well may be exactly on its own expected decline. **The caveat is a tool return, not LLM improvisation** — this is what makes `AT-112`'s 20/20 reliability achievable (`AS-012`) |
| **TC-018.3** | Wells with `is_producing = FALSE` at `as_of` are excluded from rate orderings and counted in `excluded_reasons`. A shut-in well is not the lowest producer; it is not a producer |
| **TC-018.4** | `residual_pct` is read from the nightly `TC-001` fit. Wells whose fit is `LOW_CONFIDENCE` are returned **with `fit_quality = LOW`** and are never silently dropped |
| **TC-018.5** | Every row returns `oil_rate_bopd`, `expected_bopd`, `gap_bopd` and `residual_pct` **regardless of `order_by`**, so the two tables are directly comparable and the audience can see the same wells reordered |

**Worked example — the push-back, as two calls**
```
query_wells(order_by='oil_rate_bopd', direction='ASC', limit=5)
→ OK   caveat = "Absolute rate ranking is misleading on mature wells: a 3 BOPD
                 well may be exactly on its own expected decline, while a 60 BOPD
                 well 40% below its own curve is losing far more."

query_wells(order_by='decline_residual_pct', direction='ASC', limit=5)
→ OK   caveat = None
```

**Tests:** **`AT-112`** ⭐ 20 consecutive runs, all three parts present; `AT-013` a 5 BOPD well at expected decline does not outrank a 60 BOPD well 40% below its own curve; **`AT-112b`** `order_by='oil_rate_bopd'` returns a non-empty `caveat` on every call.

---

## 20. Summary

| ID | Tool | Priority | Act | Risk |
|---|---|---|---|---|
| TC-001 | `fit_decline_curve()` | P0 | 2, 3 | Low |
| **TC-002** | **`chan_diagnostic()`** | **P0** | 3 | **⚠ Sign convention** |
| TC-003 | `fillage_proxy()` | P0 | 3 | ⚠ Blocked by RISK-002 |
| TC-004 | `check_offsets()` | P0 | 3 | Low |
| TC-005 | `detect_mechanical_signature()` | P0 | 3 | ⚠ Vented casing |
| TC-006 | `predict_failure()` | P0 | 3 | ⚠ Circularity |
| TC-007 | `trigger_scan()` | P0 | 3 | Low |
| TC-008 | `route_intervention()` | P0 | 3, 5 | ⚠ Rig/rigless boundary |
| TC-009 | `estimate_uplift()` | P1 | 3, 5 | Low |
| TC-010 | `rank_candidates()` | P0 | 3, 5 | Low |
| TC-011 | `check_mro()` | P1 | 3, 5 | Low |
| **TC-012** | **`search_well_history()`** | **P0** | 3 | ⚠ OCR quality |
| TC-013 | `generate_draft_plan()` | P0 | 3 | Low |
| TC-014 | `generate_report()` | P0 | 4 | Low |
| TC-015 | `schedule_rigs()` | P2 | 5 | Low |
| **TC-016** | **`render_well_map()`** | **P0** | **1** | **⚠ RISK-001 — first thing on screen** |
| TC-017 | `plot_production()` | P0 | 2, 3 | Low |
| **TC-018** | **`query_wells()`** | **P0** | 2 | ⚠ Carries the push-back caveat |

**Build order:** **TC-016 (spike first — it gates Phase 0)** → TC-001 → **TC-002 (test first)** → TC-017 → TC-018 → TC-003 → TC-004 → TC-005 → TC-007 → TC-008 → TC-006 → TC-009/010/011 → TC-012 → TC-013 → TC-014 → TC-015.

> [!NOTE]
> **TC-016 is built first despite being narratively simple.** It is the only P0 tool whose feasibility is genuinely unknown (`RISK-001`), and it is the opening shot of the demo. Discovering in rehearsal week that the runtime cannot draw a map is the worst available outcome.
