# Model & Data Foundation
## What to measure, where to get it, and how to generate it if we can't

**Version:** 1.0 · **Date:** 2026-09-23
**Companions:** `Problem Statement.md` v3.0 · `research_appendix.md` · `demo_flow.md`
**Status:** Research complete. Three changes to `demo_flow.md` required — see §6.

---

## 0. The answer, first

> **No public dataset exists with both well-level production time series and labelled failure events for low-rate onshore rod-pumped wells. We must generate the data — but we can validate the method against real wells using California CalGEM, which is a near-exact physical analogue to mature Assam.**

That is a materially stronger position than pure synthesis. It lets us say to ONGC: *"the method was tested on 50,000 real onshore stripper wells; only the Assam-specific instance is synthetic."*

**Three findings change the current build spec:**

| # | Finding | Impact | Severity |
|---|---|---|---|
| **1** | The literature says this is a **survival / time-to-event** problem, not binary classification | `predict_stoppage_risk()` must output time-to-failure, not a 90-day flag | **Blocking** — changes the model and the ranking logic |
| **2** | **Dogleg severity is the wrong headline feature** for this asset — Geleki-era wells are near-vertical. Replace with a **pump fillage proxy** | Feature list in `demo_flow.md` §5.2 is wrong | **Blocking** — the stated features would underperform |
| **3** | ⚠ **Corrected 2026-09-23 (`D-15`).** The former claim that three independently-sourced parameters reconcile *"to within 0.2 percentage points"* was **circular and is withdrawn — it was never true.** What survives is narrower and defensible: the downtime upper tail (`p96.7 = 204.1 d`) **independently reproduces** the CAG-audited maximum of 205 d, while the 20.0% total down fraction is **fitted**, not corroborated | Still a credibility asset, but a smaller and honest one. The concession is now explicit. See §4 | Important, not blocking |

---

## 1. What data to analyse — the feature specification

This replaces the uncited feature list currently in [demo_flow.md §5.2](file:///usr/local/google/home/amandeepsinghs/O&G_slidedeck_agentic_transformation/Oil%20&%20Gas%20Agent%20Portfolio/agent_ideas/Workover_well_intervention/demo_flow.md#L314).

### 1.1 The correction that matters most

> [!WARNING]
> **Do not build the model on dogleg severity / deviation.**
>
> SPE-212848-PA identifies *lateral loads in deviated wells* as the dominant rod-failure driver, and it is tempting to promote dogleg severity (DLS) to the top feature. **It does not transfer to this asset.** Geleki was discovered in 1968 and came on production c.1974; that vintage of ONGC onshore well is near-vertical. If DLS ≈ 0 across the population it carries **zero discriminating information** — the feature would be inert and the model would quietly underperform.
>
> Two further cautions: (a) the SPE-212848-PA abstract does **not** actually name DLS as a predictive feature — that was an inference, now retracted (§7.2); (b) the paper's field is ONGC **Western** onshore, not Assam.

**Replace it with the Pump Fillage Proxy** — the dominant mechanism for *vertical*, low-rate, high-water-cut rod-pumped wells:

```
fillage_proxy(t) = theoretical_pump_displacement(t) − actual_liquid_rate(t)

  theoretical_pump_displacement = 0.1166 × Ap(in²) × S(in) × N(spm) × runtime_fraction
                                  [bbl/d, standard SRP displacement constant]
```

**The physics:** at low reservoir inflow the pump displaces more than the well delivers. The plunger falls through gas or void on the downstroke and slams into fluid — *fluid pound*. That sends a compressive shock up the rod string, buckling it against the tubing **even in a perfectly vertical well**. A well running high SPM and long runtime while producing little liquid is destroying its own rod string, and it is visible in daily data.

**The second driver is chemical:** at 60–92% water cut the wellbore is a conductive electrolyte. Corrosion thins rods and tubing; combined with fluid-pound fatigue, rods part and tubing holes develop quickly.

### 1.2 Tiered feature specification

Tiers reflect **data availability at ONGC onshore**, where most wells are on manual well testing at daily-to-monthly cadence, not continuous telemetry.

#### Tier A — from daily production data alone ✅ *assume available*

| Feature | Rationale | Source |
|---|---|---|
| **WOR and WOR′** (`d(WOR)/d(ln t)`) | **Highest-signal Tier A feature.** Log-log slope separates coning from channelling from multilayer — determines whether the right job is a squeeze, a recompletion, or nothing | Chan, SPE-30775 (1995) |
| **Pump fillage proxy** (above) | Fluid-pound detection; the dominant vertical-well mechanical driver | Derived; see §1.1 |
| **Liquid rate trend / decline residual** | Departure from the fitted Arps decline, not raw rate | Arps (1945); Fetkovich (1980) |
| **Runtime fraction & SPM** | Falling runtime or rising SPM at flat production ⇒ fillage loss | SPE-232484-MS |
| **Casing head pressure (CHP) drift** | Rising CHP ⇒ annular fluid backing up as volumetric efficiency drops | Engineering judgement |
| **Intermittency / cycling frequency** | Pre-failure operational instability | SPE-232484-MS |
| **Water rate (absolute)** | Drives both corrosion and scale accumulation | §1.1 |

> [!CAUTION]
> **Tubing head pressure (THP) drift was in the draft spec and is being dropped as a pump-failure signal.** On a rod-pumped well producing into a flowline, THP is set substantially by flowline and separator backpressure, so it is largely insensitive to declining downhole pump performance. THP is retained **only** as a *wax* indicator, where it rises on near-surface restriction.

#### Tier B — periodic well tests and static attributes ✅ *assume available*

| Feature | Rationale |
|---|---|
| **Pump setting depth, plunger diameter, stroke length** | Required to compute the fillage proxy at all |
| **Rod string design and grade** | Sets baseline fatigue life |
| **Completion date / well age** | Geleki discovered 1968, on production from c.1974 — corrosion and casing condition scale with age |
| **Perforation interval vs. current fluid contacts** | Water-encroachment exposure |
| Deviation / DLS | **Retain but demote.** Keep for the minority of deviated wells; expect near-zero variance |

#### Tier C — event history ⚠️ *this is the make-or-break table*

| Feature | Rationale |
|---|---|
| **Days since last intervention** | The baseline covariate for any survival model |
| **Prior run-life (previous inter-failure intervals)** | Wells exhibit *failure memory* |
| **Prior failure type and count** | A well that failed on scale will likely fail on scale again |
| **Prior job outcome / what was replaced** | A full tubing-string replacement resets the survival clock differently from a pump change |

> [!IMPORTANT]
> Tier C maps exactly onto **precondition C2/C3** in the Problem Statement, and onto `well_status_history` in the demo spec. The research confirms the existing judgement: **without event history there is no survival model at all.** This strengthens the "the one thing we need from you is this table" ask.

#### Tier D — telemetry ❌ *do not assume; subset only*

Scaled load ratio (min/max surface rod loads) achieved **F1 = 0.857 with ~14-day lead time** on surface data alone (SPE-233386-PA) — worth naming as the upgrade path once instrumentation exists. Dynamometer cards, ESP amps/intake pressure/motor temperature belong here too. **Out of scope for the base model.**

### 1.3 Label definition — change this

| Approach | Verdict |
|---|---|
| Binary "fails in next 90 days" | **Current spec. Inferior.** High false-alarm rate on low-frequency data; discards censoring information |
| **Survival / time-to-event with right-censoring** | **RECOMMENDED.** Handles wells still running natively, and outputs a continuous hazard that ranks the whole stock |
| Unsupervised anomaly detection | Too noisy to drive rig scheduling |

**Why this matters operationally:** a binary flag says *"these 14 wells are at risk."* A survival model says *"rank all 142 by expected time-to-failure and expected deferred barrels."* **Only the second can feed `rank_candidates()` and `schedule_rigs()`.** The internal optimisation objective — deferred barrels avoided per rig-day — requires a ranking, not an alarm. The headline KPIs we report against are **failures per well per year** and **mean run-life between interventions**; both are also ranking-derived.

### 1.4 Model class and evaluation

**Model:** Random Survival Forest or Cox proportional hazards as primary; gradient boosting retained for the binary sub-task and for non-linear handling of static features. LSTM/autoencoder approaches win only in Tier D and are **not** recommended here.

**Evaluation — two levels, and the second is the one that counts:**

| Level | Metric | Note |
|---|---|---|
| **Operational — primary** | **Failures per well per year** | The headline KPI. ONGC's own WRFM reporting already uses it, so it needs no explanation and invites no argument |
| **Operational — primary** | **Mean run-life between interventions** | The second headline KPI, and the direct survival-model analogue |
| **Operational** | **Rigless share of interventions** | **24% of failures need no rig at all** — see §3.2 |
| **Operational** | **Decline-arrest barrels** | Barrels held on the curve that would otherwise have been lost |
| *Internal* | *Deferred barrels avoided per rig-day* | **A stated internal optimisation objective, not a headline KPI.** It is what `rank_candidates()` maximises. ONGC does not report on it, and presenting it as the top-line metric invites an argument we do not need |
| **Operational** | Intervention cost avoided | SPE-219563-MS ties a **$700 proactive treatment to a $50,000 workover avoided** — the cleanest published economic framing found |
| Model | **Concordance index (C-index)** | Correct metric for a ranking model. Report this, not AUC. **Target band 0.65–0.72** — the defensible range on daily production data alone with no dynacard telemetry, set deliberately below vendor claims because vendor performance numbers are rejected under this project's evidence standard |
| Model | Precision@k, lead-time distribution | A false positive sends a rig to a healthy well |

---

## 2. Public data — the verdict

### 2.1 Nothing has both production *and* labels

| Dataset | Fitness | Why |
|---|---|---|
| **Petrobras 3W** | Low | Offshore flow assurance (slugging, hydrates), not rod-pump mechanics. Apache 2.0 |
| **Equinor Volve** | Low | Offshore; failures buried in unstructured PDFs |
| **Norway FactPages / UK NSTA** | None | Monthly volumes, no failure labels, offshore |
| **DGH NDR (India)** | **None** | Seismic and logs for block bidding. No production series, no intervention history, registration-walled |
| **NASA C-MAPSS** | Medium *(method only)* | Run-to-failure benchmark — a methodological analogue for RUL, not oilfield data |

### 2.2 But a weak *real* label is constructible — use it

US state regulators publish **days-produced per well per month**. A well reporting 31 → 6 → 0 days is an unlabelled shut-in event. Join that to **dated idle-well registers** and **dated recompletion records** on the API number and you get real `(well, date)` shut-in and intervention events on real onshore wells.

**Primary source: California CalGEM.** Kern County — Midway-Sunset, Kern River, South Belridge — is the closest analogue on earth to mature Assam: century-old fields, stripper rates, very high water cut, overwhelmingly rod-pumped, with a statutory idle-well register.

| Requirement | CalGEM | Colorado ECMC |
|---|---|---|
| Archetype match to Assam | ✅ Century-old stripper, rod pump, high water cut | ❌ DJ Basin horizontal unconventional |
| Days-producing | ✅ | ✅ |
| **Well-level water volumes** (`WaterBBL`) | ✅ **Per API number** | ✅ |
| Dated idle-well register | ✅ Statutory | ✅ Status date |
| Lift type filterable | ✅ "Method of Operation" in well header | Partial |

- **Primary:** [CalGEM WellSTAR Data Dashboard](https://www.conservation.ca.gov/calgem/Online_Data/Pages/WellSTAR-Data-Dashboard.aspx)
- **Secondary:** [Colorado ECMC downloadable data](https://ecmc.colorado.gov/data-maps/downloadable-data)
- **Texas RRC is not usable** for this — it reports at **lease** level, so per-well days cannot be recovered.

> [!NOTE]
> **Well-level water is the make-or-break field, and CalGEM has it.** Without water there is no WOR, and WOR is the highest-signal Tier A feature.

### 2.3 Limitation statement — customer-facing, use verbatim

> The California CalGEM dataset provides a strong physical analogue for mature, heavy-oil, rod-pumped wells at high water cut, but its use in validating a failure-prediction model carries explicit limits. The data is **monthly**, so sub-month degradation cannot be reconstructed; only month-over-month shut-in occurrence, derived from drops in days-producing and from the dated idle-well register, can be validated. The dataset carries **no root-cause reason codes**, so component-level diagnosis — distinguishing a tubing leak from a parted rod — cannot be validated against it. And while Kern County wells share fundamental lift mechanics with the target asset, differences in operating practice, crude rheology and the regulatory definition of "idle" mean this data validates **macro-level well survival and downtime-event detection on a US analogue**, not mechanical failure modes on Indian wells.

---

## 3. Synthetic generation — the build specification

### 3.1 The one methodological rule

> [!IMPORTANT]
> **Failures must be a consequence of the simulated covariates, not an independent draw.**
>
> If failure times are drawn independently from a Weibull, any model trained on the data will *correctly* find no signal, and Act 4 collapses. This is the most common way synthetic ML demos fail, and it is silent until rehearsal.

**Use a cumulative-damage / first-passage model:**

```
W(t) = ∫₀ᵗ ( c₁·TotalFluid(s) + c₂·WaterCut(s)² ) ds      # hidden wear state
failure  when  W(t) ≥ W_crit ,   W_crit ~ Normal(μ_w, σ_w)
observable degradation begins when W(t) > 0.85 · W_crit
```

### 3.2 Failure taxonomy — and the rigless finding

**Rebalanced to 75% predictable / 25% unpredictable (Decision 2, resolved). Canonical source: [spec/00_overview.md §5.3](./spec/00_overview.md). Classification is by the component that failed, not by the root cause** — rod-on-tubing wear parts a rod (`ROD_PART`) or holes the tubing (`TUBING_LEAK`), and those are two different failures needing two different jobs.

| Code | Share | Predictable? | Rig? | Repair |
|---|---|---|---|---|
| **Tubing leak / rod-on-tubing wear** | **22%** | ✅ | Rig | LogN(μ=3.219, σ=1.142), floor 8 d |
| Rod parting / fatigue | 18% | ✅ | Rig | LogN(μ=3.219, σ=1.142), floor 8 d |
| **Paraffin / wax deposition** | **15%** | ✅ | **Partly RIGLESS** — ~2/3 annulus-circulated, ~1/3 needs the rods out | 1–3 d rigless; LogN, floor 8 d when rods must come out |
| Pump wear / attrition | 13% | ✅ | Rig | LogN, floor 8 d |
| **Surface unit / power** | **12%** | ❌ | **RIGLESS** | 1–2 d |
| Other / unknown | 8% | ❌ | Mixed | LogN, floor 8 d |
| Sudden mechanical / casing | 5% | ❌ | Rig | 200 d |
| **Sand / solids influx** | **5%** | ✅ | Rig — cleanout and bailing both need the rods out | LogN, floor 8 d |
| **Scale** | **2%** | ✅ | **RIGLESS** *(bullheaded acid)* | 1–3 d |

- **Predictable = 75%** → caps achievable AUC at roughly **0.68–0.78**, the same neighbourhood as the re-baselined C-index band of 0.65–0.72 (`MS-100` / `MS-101b`, `spec/00` §5.5). **An AUC of 0.85 alongside a C-index of 0.68 is a contradiction, not a result** — this model sees daily production data only: no dynacards, no downhole gauges. An AUC above 0.95 means a leak.
- **Rigless = 24%** of failures — `SURFACE 12 + SCALE 2 + ~2/3 of WAX 15 (≈10)`. It is an **arithmetic consequence of this table, not an industry benchmark**; the previously asserted 27% was unsupported.
- The 8% *other/unknown* bucket is deliberate: real reason-code data always has one, and its absence is itself a tell.
- **`SAND` and `SCALE` are split, not combined.** They need different jobs — sand needs a cleanout or a screen/gravel pack, scale needs acid or an inhibitor squeeze. A combined bucket hid sand control as a job category entirely, and Tipam sands at Geleki are poorly consolidated.

> [!TIP]
> **24% of failures require no rig at all.** This is a business-case finding, not a data-modelling detail. Rigless substitution is one of the four capacity mechanisms answering the "the fleet is already saturated" objection in Problem Statement §7 — and this taxonomy **quantifies it for the first time**. It should be promoted into that objection-handling table.

Assam crude is waxy / high pour point, which is why paraffin carries a 15% share — and that 15% should be treated as a **probable floor**, not a ceiling.

### 3.3 Distinct pre-failure signatures — deliberately non-identical

If every failure is preceded by the same efficiency decay, the model learns one trivial pattern and the demo is hollow. Four *discriminable* signatures:

| Mode | Liquid rate | CHP | THP | Shape |
|---|---|---|---|---|
| **Pump wear** | Gradual decline | **Rises** | Flat | 14–30 d ramp |
| **Tubing leak** | Sharp accelerating drop | **Flat** | Flat | 3–5 d |
| **Wax** | Drops | Flat | **Rises** | Seasonal, temperature-driven |
| **Scale** | **Flat and healthy** | Flat | Flat | **Sudden death** — no warning in rate |

Scale is the important one: it fails *without* rate decline, driven only by cumulative produced water. It forces the model to use a cumulative covariate rather than a trend.

### 3.4 Other parameters

- **Decline:** Arps hyperbolic, `b = 0.5–1.0`, `Di = 5–15%/yr` (Fetkovich 1980 for mature waterfloods)
- **Chan-distinguishable WOR** — these functional forms produce the required log-log slopes exactly:
  - Coning: `WOR(t) = WOR_max − A·t^(−k)` ⇒ WOR′ slope `= −k`, use `k = 0.3–0.7`
  - Channelling: `WOR(t) = A·t^n` ⇒ WOR′ slope `= n`, use `n = 1.0–1.2`
  - Fracture/rapid: as channelling with `n ≥ 2.0`
- **Monsoon (Jun–Sep):** multiply rig mobilisation delay ×1.5–3.0; inject 1–2 day power-outage shut-ins
- **Realism:** 3–5% missingness; well tests only every 14–30 days with daily values allocated, never daily truth
- **Tooling:** hand-roll with `numpy`/`pandas`/`scipy.stats`; `lifelines` (MIT) to validate Kaplan-Meier curves. **Avoid SDV / ydata-synthetic** — they learn covariance but violate mass balance and petroleum physics

---

## 4. The availability derivation — corrected 2026-09-23 (`D-15`)

> [!CAUTION]
> **This section previously ran under the title *"The consistency triangle — verified, with two corrections"*, and it claimed that three independently-sourced parameters reconciled *"to within 0.2 percentage points."* That claim was an artefact of a derivation that does not close. It is withdrawn, and it must not reappear in any wording.**
>
> Canonical constants now live in [`spec/00_overview.md` §5.2](./spec/00_overview.md); the worked derivation is in [`spec/03_synthetic_data_spec.md` §3](./spec/03_synthetic_data_spec.md). This section is downstream of both.

### 4.1 What was wrong

| # | Error | Effect |
|---|---|---|
| 1 | Downtime lognormal had **p05 = 3.8 days**, and expected sample-minimum of 2.9 days over 33 wells, against CAG's observed minimum of **8 days** | Implies workover rigs mobilising in under 4 days. A domain expert would reject this instantly |
| 2 | The headline 20.0% used a **uniform 48-day downtime**, ignoring that the taxonomy makes a substantial share of jobs rigless at 1–3 days | The claimed "exact" match was an artefact of not applying the taxonomy |
| 3 | Taxonomy implied **85% predictable**; the spec elsewhere stated **75%** | **Resolved** — rebalanced to 75/25, see §3.2 and §8.1 |
| **4** | 🔴 **`D-15` — found on the second pass, and it is the serious one. `E[downtime \| rig-requiring] = 56.2 d` was unreachable, and the blend was never actually applied.** `LogNormal(μ = 3.219, σ = 1.142)` floored at 8 d has a mean of **48.5 d** — and that is the mean of the *whole* distribution, so **no sub-population of it can average 56.2 d.** The published blended **48.7 d** is simply the unblended floored mean, with a blending narrative retrofitted onto it | **Everything downstream moved:** `E[down]` 48.7 → **37.3 d**, active down fraction 20.2% → **16.3%**, and the "0.2 percentage points" reconciliation **disappears entirely, because it was circular** |

> [!IMPORTANT]
> **Error 4 invalidated a *conclusion*, not just an arithmetic line.** The §4.3 finding that the well stock *"cannot be split"* rested directly on the wrong 48.7 d. **Decision 1 is reversed — see §4.3.**

### 4.2 The corrected parameter set

Applying the **8-day rig-mobilisation floor** (physically necessary), the rebalanced §3.2 taxonomy, **and the rigless blend actually applied this time:**

```
Uptime    Weibull(β = 2.0, η = 216.7)     E[uptime] = 216.7 × Γ(1.5)   = 192.0 d  (6.3 months)
Downtime  LogNormal(μ = 3.219, σ = 1.142), floored at 8 d
          E[downtime | rig-requiring]                                  =  48.5 d   ← the floored mean, computed
          E[downtime | rigless]                                        =   2.0 d
          RIGLESS_SHARE                                                =    24%    ← derived, spec/00 §5.3

  E[down] blended      = 0.76 × 48.5 + 0.24 × 2.0                      =  37.3 d
  FRACTION_DOWN_ACTIVE = 37.3 / (192.0 + 37.3)                         =  16.3%
  PERMANENTLY_IDLE                                                     =   4.5%    ⚠ FITTED, not observed
  FRACTION_DOWN_TOTAL  = 0.955 × 16.3% + 4.5%                          =  20.0%
```

#### What corroborates, and what is merely fitted — the distinction *is* the finding

| Constraint | Independent source | Model | Status |
|---|---|---|---|
| Rig wait 8–205 days | CAG Report No. 42 of 2015 | floor **8 d**, **p96.7 = 204.1 d** | 🟢 **Genuine independent corroboration.** `μ` and `σ` were fixed on other grounds; the tail landing on the CAG-audited maximum of 205 d was not arranged. **This one is worth saying out loud** |
| ~20% of connected wells shut-in | Tamil Nadu 2018 census, discounted | **20.0%** total | 🟠 **FITTED.** The 4.5% permanently-idle carve-out is a free parameter, chosen so the total lands on the census. Legitimate calibration — **but it is not independent agreement and must never be presented as such** |
| Rod pump MTBF 5–9 months | SPE-212848-PA, widened | **6.3 months** | 🟢 Inside the band |

> [!CAUTION]
> **Say this:** *"Our downtime distribution's upper tail independently reproduces the CAG-audited maximum of 205 days. The idle fraction is calibrated to the one published census we have."*
>
> **Do not say:** *"three independent sources reconcile to within 0.2 percentage points."* **It was never true.** The 20.2% was the *unblended* lognormal mean divided by the Weibull mean, with a reconciliation story written around it afterwards — and the 20% it "agreed" with is the figure the model is now openly tuned to.
>
> **The replacement is a weaker claim, and it is the right trade.** An ED who says *"reconcile that for me"* gets an answer that survives a calculator. The old one did not.

**Sensitivity** — recomputed at `E[down] = 37.3 d`, β = 2.0 (how hard the 20% is pinned):

| Weibull η | E[uptime] | Down, active | Down, total *(incl. 4.5% idle)* |
|---|---|---|---|
| 188.0 | 166.6 d (5.5 mo) | 18.3% | 22.0% |
| 200.0 | 177.2 d (5.8 mo) | 17.4% | 21.1% |
| **216.7** | **192.0 d (6.3 mo)** | **16.3%** | **20.0%** |
| 240.0 | 212.7 d (7.0 mo) | 14.9% | 18.7% |
| 270.0 | 239.3 d (7.9 mo) | 13.5% | 17.4% |

> [!WARNING]
> **`FRACTION_DOWN_TOTAL = 20.0%` is a target for the generator, not a guarantee from it.** The `SCALE_SAND` → `SAND` + `SCALE` split moved sand to a rig job and scale to a bullheaded rigless job, so **the per-code downtime weights changed too.** The figure must come back out of `generator/validate.py` — **it must not be adjusted by hand.** `DC-092` / `AT-092` now assert **20.0% ± 1.0pp**, widened from ±0.5pp because a tolerance tighter than the uncertainty in a fitted parameter is false precision.

### 4.3 Does a permanently-idle population fit? ⚠ **REVERSED — yes, it does**

> [!CAUTION]
> **This section previously concluded "No", and on that basis closed Decision 1 as *one population*. That conclusion is withdrawn. It was wrong, and it was wrong *because of* the `D-15` error in §4.1 — not because of anything about the physics.**

**The original reasoning, kept for the record.** The Tamil Nadu ~20% is *"connected but not flowing"*, which plausibly includes **permanently idle** wells that will never see a rig. Splitting the stock was ruled out on this table:

| Assumed permanently-idle share | Active stock must be down | Required E[uptime] | Inside 5–9 month MTBF band? |
|---|---|---|---|
| 5% | 15.8% | 260 d (8.5 mo) | ✅ *marginal* |
| 10% | 11.1% | 389 d (12.8 mo) | ❌ |
| 15% | 5.9% | 779 d (25.6 mo) | ❌ |

> ⛔ **SUPERSEDED — retained so the reversal is auditable, not to be quoted.**
> *"**Resolution: the ~20% must refer to the ACTIVELY CYCLING stock alone.** Carving a permanently-idle population out of the same 20% forces the active-well MTBF to 13–26 months, which directly contradicts SPE-212848-PA. The two constraints are only simultaneously satisfiable if idle wells sit **outside** the 20%, as additional stock."*

**Why that reasoning failed.** Every `Required E[uptime]` in the table above was computed with **`E[down] = 48.7 d` — the number that does not exist.** A larger `E[down]` mechanically inflates the uptime an active population needs in order to leave room for an idle carve-out, which is exactly how a 5% carve-out came out at an implausible 260 d. At the correct **`E[down] = 37.3 d`**, a **4.5%** idle carve-out needs **`E[uptime] = 192.5 d`** — and the Weibull already gives us **192.0 d**. **The split closes at the observed MTBF.** It was the arithmetic that was broken, not the two-population model.

> [!IMPORTANT]
> **Resolution, reversed: the stock is TWO populations.**
>
> | Population | Share of connected stock | Down at any snapshot |
> |---|---|---|
> | **Actively cycling** — fails, waits for a rig, returns | **95.5%** | **16.3%** of it (`FRACTION_DOWN_ACTIVE`) |
> | **Permanently idle** — will not see a rig in the modelled window | **4.5%** ⚠ fitted | 100% by definition |
> | **Total** | 100% | **20.0%** (`FRACTION_DOWN_TOTAL`) |
>
> **Build consequence:** idle wells are now *inside* the availability arithmetic, not excluded from it. They must be explicitly labelled so `generator/validate.py` can report `FRACTION_DOWN_ACTIVE` and `FRACTION_DOWN_TOTAL` separately — `DC-092` asserts both. They remain a reactivation opportunity in their own right, mirroring the NSTA *"56 reinstatements → 16 mmboe"* evidence in Problem Statement §4.
>
> **And state the concession when you present the 20%:** the 4.5% was chosen to make the total land on the census. It is the one parameter in this derivation we tuned, and we say so.

---

## 5. Validation checklist before rehearsal

| # | Check | Pass criterion |
|---|---|---|
| 1 | Median well rate | ≈ 20 BOPD |
| 2 | Field total (Geleki) | 2,500–3,500 BOPD |
| 3 | Water cut range | 60–92%, rising |
| 4 | Chan plot | Coning (negative slope) and channelling (positive) both visibly present and correctly classified |
| 5 | Kaplan-Meier MTBF | Recovers 5–9 months from the generated event log |
| 6 | Shut-in share at any snapshot | **`FRACTION_DOWN_TOTAL` 20.0% ± 1.0pp** *and* **`FRACTION_DOWN_ACTIVE` 16.3% ± 1.0pp** — both, separately (`DC-092`) |
| 7 | Downtime distribution | min ≥ 8 d, **p96.7 ≈ 204.1 d** against the CAG-audited max of 205 d |
| 8 | **Baseline model AUC** | **0.68–0.78**, the same neighbourhood as the C-index (`MS-101b`). **If it scores > 0.95 there is a leak** |
| 9 | C-index | 0.65–0.72 |
| 10 | Failure-mode mix | Matches §3.2 shares within ±3pp |
| 11 | Leakage audit | Status code must not flip before production actually drops |

---

## 6. Required changes to `demo_flow.md`

| § | Change | Why |
|---|---|---|
| **5.1** | `daily_production` schema must add **SPM, stroke length, runtime hours, casing head pressure**; `well_master` must add **plunger diameter, pump setting depth, rod string grade** | Without these the pump fillage proxy — now the top mechanical feature — **cannot be computed at all** |
| **5.1** | `well_status_history` reason codes must use the §3.2 taxonomy, with a **rigless flag** | Enables the rigless-substitution metric |
| **5.2** | `predict_stoppage_risk()` → **survival model** returning expected time-to-failure + hazard, not a 90-day binary | Required for `rank_candidates()` to rank the full stock |
| **5.2** | Replace the feature list with §1.2. **Drop DLS from the headline**, add fillage proxy, WOR′, CHP drift, runtime fraction | Current list is uncited and partly wrong for vertical wells |
| **5.3** | Add the §4.2 corrected parameter set and the §3.2 taxonomy | Makes the synthetic data reproducible and defensible |
| **6** | Add the §2.3 limitation statement and the §4.2 **corroborated-vs-fitted distinction** to the on-screen integrity slide. **Not the old "0.2 percentage points" line — that is withdrawn** | Turns a weakness into a credibility beat, and the openly-conceded fitted parameter is what makes it survive Q&A |

---

## 7. Citation register

### 7.1 Verified and corrected

| Citation | Status | Note |
|---|---|---|
| Chan, K.S. (1995), **SPE-30775** | ✅ Verified | WOR / WOR′ diagnostic plots |
| Chan, T. et al. (2024), **SPE-219563-MS** | ✅ Verified | Ambyint. **Unrelated to K.S. Chan** — do not conflate |
| Hyder, Z., Yermekova, M., Kemp, C. et al. (2026), **SPE-232484-MS** | ✅ Verified | Oman Petroleum & Energy Show, May 2026 |
| Jung, Y., Kim, Y., Oh, B., Jeong, H., Jun, J., Sun, W. (2026), **SPE-233386-PA** | ⚠️ Corrected | Was cited as `-MS` with no authors. It is a peer-reviewed article. F1 = 0.857 |
| Pastre, L.F. & Fastovets, A. (2017), **SPE-187735-MS** | ⚠️ Corrected | Original citation was malformed |
| Bailey, W. et al. (2005), **SPE-96722** | ✅ Verified | Foundational ESP survival-analysis paper |
| Abdelkerim, Alseedi & Al-Radhi (**2025**), **SPE-224462-MS** | ⚠️ Corrected | Mis-dated 2023. **Project records were right** |
| Aloise et al. (2006), DOI 10.1016/j.dam.2004.09.021 | ✅ Verified | Workover Rig Scheduling Problem, NP-complete |
| Fetkovich (1980), JPT | ✅ | Mature waterflood decline `b` behaviour |

### 7.2 Retracted inference — read this

> [!CAUTION]
> **The claim "dogleg severity is the dominant predictive feature, per SPE-212848-PA" is withdrawn.**
>
> The full text was **not** accessed — consistent with `research_appendix.md` §6 item 3, which still lists it as outstanding. The abstract **does** state *"lateral loads acting along the rod string in deviated wells"*, *"tubing and rod buckling"*, and *"rubbing and bending"*. It does **not** name DLS as a data feature, and does **not** mention the neutral point. Those were inferred and are now retracted.
>
> **Consequence:** obtaining SPE-212848-PA full text moves from *"high value"* to **blocking** for the feature spec.

### 7.3 Could not verify

| Claim | Issue |
|---|---|
| Castillo et al. (2025), SPE-227253-MS — "median survival 232 days" | Figure is in the abstract but **no population size or field is stated**. A median with no denominator. **Do not quote** |

### 7.4 Rejected — do not cite

Generic vendor claims of the form *"AI reduces downtime by 30%"*: no baseline, no data-frequency requirement, no methodology. Consistent with the existing rejection in `research_appendix.md` §3.

---

## 8. Decisions — resolved and outstanding

### 8.1 Resolved

| # | Decision | Resolution | Basis |
|---|---|---|---|
| **1** | Is the ~20% shut-in stock one population or two? | ⚠ **REVERSED 2026-09-23 — TWO.** **95.5% actively cycling, 16.3% of it down at any snapshot, plus a 4.5% permanently-idle carve-out — 20.0% in total.** *Superseded answer, kept for the record: "One — the actively cycling stock; long-term-idle wells sit outside the 20%."* | **The original reasoning was an artefact of `D-15`.** It rejected the split because a 5% carve-out appeared to demand `E[uptime] ≈ 260 d` — but that was computed with the erroneous `E[down] = 48.7 d`. At the correct **37.3 d**, a 4.5% carve-out needs **192.5 d**, and the Weibull gives **192.0 d**. **The split closes at the observed MTBF.** See §4.3 |
| **2** | 75% or 85% predictable? | **75%** — wax to 15%, surface/power to 12%, new 8% *other/unknown* bucket | Caps achievable AUC at **0.68–0.78**, consistent with the re-baselined C-index band of 0.65–0.72 (`MS-100` / `MS-101b`, `spec/00` §5.5) — **an AUC of 0.85 next to a C-index of 0.68 is a contradiction, not a result.** The availability derivation closes at **16.3% active / 20.0% total**, see §4.2 |
| **5** | Where does this document live? | `Workover_well_intervention/model_data_foundation.md`, referenced from the Problem Statement alongside `research_appendix.md` | Consistent with existing structure |

### 8.2 Outstanding — these need you

| # | Item | Recommendation | Why it is not mine to close |
|---|---|---|---|
| **3** | **Build the CalGEM validation, or just cite it?** | **Build it if a week is available.** *"Tested on ~50,000 real onshore wells"* is a materially different sentence from *"we generated data."* If time is short, cite availability and make it the phase-2 ask | Depends on the demo timeline, which I do not control |
| **4** | **Obtain SPE-212848-PA full text** | **Now blocking**, upgraded from "high value" in `research_appendix.md` §6 item 3 | Requires OnePetro/SPE access or purchase |

> [!IMPORTANT]
> **Item 4 is the one genuine blocker.** SPE-212848-PA is the only ONGC-specific failure-mechanism source in the entire evidence base. The feature specification in §1 currently rests on inference from its abstract plus transfer from non-Indian literature. Until the full text is read, §1.1 should be treated as **well-reasoned but not yet sourced**.
