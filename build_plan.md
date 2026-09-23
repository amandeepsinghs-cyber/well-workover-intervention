# Build Plan
## From specification to a rehearsable demo

**Version:** 1.0 · **Date:** 2026-09-23
**Companions:** [demo_flow.md](./demo_flow.md) v2.0 *(the script)* · [decision_architecture.md](./decision_architecture.md) v1.1 *(the product spec)* · [model_data_foundation.md](./model_data_foundation.md) *(what to measure)*
**Status:** Ready to execute. Phase 0 starts immediately and gates everything else.

---

## 0. The answer, first

> **Build in risk order, not narrative order. The two things that can kill this demo — the map renderer and the synthetic data's internal consistency — are both unknowns today, and neither is in the critical path of anything else. Spike both in parallel on day one, before writing a single tool.**

**The demo is four acts. The build is six phases. They do not correspond, and trying to build act-by-act is the main way this goes wrong** — Act 1 (the map) looks easy and is the highest technical risk; Act 4 (the reports) looks impressive and is three SQL queries.

| Phase | What | Gates | Can start |
|---|---|---|---|
| **0** | Spikes — map renderer, PDF retrieval, GE tool-call trace | Everything | **Now** |
| **1** | Synthetic data generator | Phases 2–5 | **Now**, parallel to 0 |
| **2** | Deterministic tool library | Phase 4 | After 1 |
| **3** | Survival model | Act 3 only | After 1 |
| **4** | Agent wiring + prompts | Rehearsal | After 0, 2 |
| **5** | Reports | Act 4 | After 2 |
| **6** | Rehearsal + fallbacks | The room | After 4, 5 |

---

## 1. Phase 0 — Spikes. Do these before anything else.

Three unknowns. Each is a half-day. **If any fails, the design changes, so failing fast is the whole point.**

### 0.1 The map renderer ⚠ HIGHEST RISK

**Question:** does the Gemini Enterprise A2UI renderer support Vega-Lite `geoshape` marks with a `projection`?

```
Acceptance: a Geleki field outline + 142 well points, colour-coded by status,
            rendered natively in a GE card, tooltips working, < 8s
```

**Fallback ladder — decide which tier you are on before Phase 4:**

| Tier | Approach | Cost if forced here |
|---|---|---|
| **1** | Native Vega-Lite `geoshape` + inline GeoJSON | — |
| **2** | Vega-Lite `point` mark on x=lon, y=lat with a background image layer | Loses field outline; still looks like a map |
| **3** | Pre-rendered basemap PNG with plotted points, served as an image | Loses interactivity. Acceptable — Act 1 is not where the demo is won |

> [!WARNING]
> **Also confirm whether inline GeoJSON is permitted or whether external URLs are required.** If external URLs are blocked by the tenant's egress policy, tier 1 dies even if `geoshape` works.

### 0.2 Scanned-PDF retrieval with citation

**Question:** can Vertex AI Search return a **citation with document name and date** from a scanned-appearance PDF, reliably enough to put on screen?

```
Acceptance: query "water shutoff history GK-129" returns the 2019 workover
            report with an openable link and a visible date
```

This is the single most load-bearing proof of *"access data from anywhere."* If OCR quality is marginal, generate the PDFs with a **text layer** (render-to-PDF with a scan-effect overlay) rather than true rasterised scans.

### 0.3 The tool-call trace

**Question:** can the visible tool-call trace be shown in the GE UI, and can it be made to animate?

It is doing double duty — proving determinism *and* covering an 18-second wait in Act 3. If it cannot be shown, Act 3's latency budget must drop to < 10s, which changes the pre-computation strategy.

---

## 2. Phase 1 — The synthetic data generator

**This is the longest pole and the one an ONGC engineer will attack.** Full parameter set in [demo_flow.md §5.3](./demo_flow.md) — those numbers are non-negotiable and were validated against three independent sources.

### 2.1 Project setup

```
workover_demo/
├── pyproject.toml            # uv-managed. numpy pandas scipy lifelines
│                             # scikit-survival pyarrow google-cloud-bigquery
├── generator/
│   ├── wells.py              # well_master: 142 Geleki wells
│   ├── geology.py            # zones, contacts, perf intervals
│   ├── production.py         # daily oil/water/gas/THP/CHP/SPM/runtime
│   ├── damage.py             # cumulative-damage accumulation → failure
│   ├── failures.py           # 9-code taxonomy, signatures, downtime
│   ├── history.py            # well_status_history + workover records
│   └── validate.py           # the 11-point checklist, runs on every build
├── tools/                    # Phase 2
├── model/                    # Phase 3
├── reports/                  # Phase 5
└── docs/pdfs/                # Phase 1.5 — scanned-appearance reports
```

> [!IMPORTANT]
> **Use `uv` with a project virtualenv. Do not `pip install` globally.** Pin versions in `pyproject.toml` so the generator is reproducible — "we can regenerate this exactly" is part of the integrity story.

### 2.2 The generation order matters

Generate in this sequence. Each step depends on the last, and getting the order wrong produces data that violates mass balance.

```
1. well_master        geometry, completion date, lift config, position
2. geology            zone, perf interval, initial contacts per well
3. reservoir drive    per-well Arps parameters, aquifer strength
4. base production    clean decline + water encroachment, no failures
5. damage integration W(t) = ∫(c₁·TotalFluid + c₂·WaterCut²)dt
6. failure events     fire when W ≥ W_crit; assign code from taxonomy
7. signature overlay  apply the pre-failure signature to the 14–45 d window
8. downtime + repair  Weibull/LogNormal, 8-day rig-mobilisation floor
9. post-job reset     partial or full damage reset by job type
10. observation layer well tests every 14–30 d; daily values allocated
```

> [!CAUTION]
> **Step 5 is the one that makes or breaks the model.** Failures must be **caused by** the simulated covariates via cumulative damage — never drawn as independent events. If they are independent, the survival model will *correctly* find no signal and Act 3 collapses silently, and you will not discover it until rehearsal.
>
> The mirror risk is equally real: if the damage function uses covariates the model also sees, with no noise, the model recovers the generator exactly and you get an AUC of 0.99. **Inject unobserved heterogeneity** — a per-well frailty term the model never sees — to keep achievable performance in the honest 0.70–0.85 band.

### 2.3 Availability identity — bake it into the validator

Uptime, downtime and the shut-in fraction close under a two-population derivation (`D-15`, corrected 2026-09-23). This is tested by `AT-092` on every regeneration.

```
Uptime    Weibull(β=2.0, η=216.7)                E[uptime]            = 192.0 d
Downtime  LogNormal(μ=3.219, σ=1.142), floor 8 d
          E[downtime | rig-requiring]            = 48.5 d
          E[downtime | rigless (24%)]            = 2.0 d
          E[downtime blended]                    = 37.3 d

  FRACTION_DOWN_ACTIVE = 37.3 / (192.0 + 37.3)   = 16.3%
  FRACTION_DOWN_TOTAL  = 0.955 × 16.3% + 4.5%    = 20.0%
  p96.7 downtime       = 204.1 d (CAG observed max: 205 d)
```

**Key properties:**
1. **The 8-day floor on downtime is mandatory.** Without it the lognormal p05 lands at 3.8 days, implying rigs mobilising in under four days.
2. **Downtime is blended across the taxonomy.** 24% of SRP failures are rigless at 1–3 days (mean 2.0 d), yielding a blended mean of 37.3 days.
3. **Two populations reconcile to the 20% census.** 95.5% of connected wells cycle actively (16.3% down at any snapshot), and 4.5% are permanently idle, landing at 20.0% total.

> [!CAUTION]
> **Honesty note:** The old claim that *"three independent sources reconcile to 0.2 percentage points"* was circular and has been withdrawn. The upper tail (`p96.7 = 204.1 d` vs CAG 205 d) is genuinely corroborated. The 20.0% total down fraction is **fitted** via the 4.5% idle carve-out. `AT-092` tests both `FRACTION_DOWN_ACTIVE = 16.3% ± 1.0pp` and `FRACTION_DOWN_TOTAL = 20.0% ± 1.0pp`. Figures come from `generator/validate.py`. See [`spec/00`](./spec/00_overview.md) §5.2 and [`spec/03`](./spec/03_synthetic_data_spec.md) §3.

### 2.4 Failure taxonomy — shares must hold ±3pp

Canonical source: [spec/00_overview.md §5.3](./spec/00_overview.md). **Classification is by the component that failed, not by the root cause** — rod-on-tubing wear parts a rod (`ROD_PART`) or holes the tubing (`TUBING_LEAK`), and those are two different jobs.

| Code | Share | Rigless? |
|---|---|---|
| **Tubing leak / rod-on-tubing wear** | **22%** | No |
| Rod parting | 18% | No |
| **Paraffin / wax** | **15%** | **Partly** — ~2/3 annulus-circulated, ~1/3 needs the rods out |
| Pump wear | 13% | No |
| Surface / power | **12%** | **Yes** |
| Other / unknown | 8% | Mixed |
| Sudden mechanical | 5% | No |
| **Sand / solids influx** | **5%** | No — cleanout and bailing both need the rods out |
| **Scale** | **2%** | **Yes** *(bullheaded acid)* |

**Predictable = 75%** → caps achievable AUC at 0.80–0.85. **Rigless = 24%** (`SURFACE 12 + SCALE 2 + ~2/3 of WAX 15 ≈ 10`) → the capacity argument. **The old 27% was asserted, not derived, and is wrong.**

### 2.5 The six signatures must be discriminable

If they are not distinct, the model learns one trivial pattern and the Act 3 table becomes six rows of the same diagnosis.

| Mode | Liquid | CHP | THP | GOR | Onset |
|---|---|---|---|---|---|
| Pump wear | gradual ↓ | **↑** | flat | flat | weeks |
| Tubing leak | sharp ↓ | flat | flat | flat | 3–5 d |
| Wax | ↓ | flat | **↑** | flat | seasonal |
| Scale | flat then bind | flat | flat | flat | latent |
| Rod part | → 0 | flat | ↓ | flat | instant |
| Gas interference | erratic | ↑ | flat | **↑** | gradual |

**Validator check:** train a 6-class classifier on the 30 days preceding each failure. If macro-F1 < 0.6 the signatures are not separable; if > 0.95 they are cartoonishly separable. Target 0.70–0.85.

### 2.6 Phase 1.5 — the PDF corpus

40–50 documents, 1998–2024, **scanned appearance**. Minimum set to make Act 3 work:

- **GK-129 Completion Report, 1998-03** — must contain "poor cement bond, 1,845–1,865 m"
- **GK-129 Workover Report, 2019-11** — water shutoff attempt, must let the agent infer a 14-month run
- ~20 other workover reports across the field, varied job types
- ~15 completion reports
- A handful of irrelevant documents, so retrieval is demonstrably *selecting*, not returning everything

---

## 3. Phase 2 — The deterministic tool library

One module per tool, each independently testable. Full signatures in [demo_flow.md §5.2](./demo_flow.md).

| Order | Tool | Why this order |
|---|---|---|
| 1 | `fit_decline_curve()` | Everything downstream depends on the residual |
| 2 | `chan_diagnostic()` | Highest-signal diagnostic; also the riskiest to get wrong |
| 3 | `fillage_proxy()` | Pure arithmetic, trivial once schema fields exist |
| 4 | `check_offsets()` | Produces the NO JOB JUSTIFIED row |
| 5 | `trigger_scan()` | Composes 1, 2, 3, 4 |
| 6 | `route_intervention()` | Lookup against the 28-row catalogue |
| 7 | `estimate_uplift()`, `rank_candidates()`, `check_mro()` | Value layer |
| 8 | `schedule_rigs()` | Only needed for optional Act 5 |

> [!WARNING]
> **`chan_diagnostic()` — the sign convention is the single most dangerous line of code in this build.**
>
> ```
> WOR′ slope NEGATIVE → CONING      → choke back, rigless
> WOR′ slope POSITIVE → CHANNELLING → cement squeeze, 7 rig-days
> ```
>
> Inverted, the system sends a rig and a cementing unit to a well that needed a thirty-minute choke adjustment. A research pass on this project got this backwards on 2026-09-23 and it was caught only by independent verification. **Write the unit test first**, with a known-coning and known-channelling fixture.

**Testing standard:** every tool gets a unit test with a hand-computed fixture. The claim is *"no number originates from a language model"* — that claim is only as good as the tools' test coverage.

---

## 4. Phase 3 — The survival model

| Step | Detail |
|---|---|
| Model | `RandomSurvivalForest` (scikit-survival) primary; `CoxPHFitter` (lifelines) as the interpretable baseline |
| Label | Time-to-event with **right censoring** — not binary "fails in 90 days" |
| Output | Expected time-to-failure **+ confidence interval** — the interval is on screen in Act 3, so it must be real |
| Features | Per [model_data_foundation.md §1.2](./model_data_foundation.md) Tiers A–C. **Fillage proxy and WOR′ are the top two. DLS is demoted, THP is wax-only** |
| Metric | **C-index, not AUC.** Expect **0.65–0.72** — the defensible band for a survival model on daily production data alone with no dynacard telemetry. **Set deliberately below vendor claims, because vendor performance numbers are rejected outright under this project's evidence standard** |
| Baseline to beat | **Trigger B** — "days since last intervention, throughput-weighted." If the model cannot beat that, do not ship the model |

> [!CAUTION]
> **An AUC above 0.95 means a data leak, not a good model.** 25% of failures are unpredictable by construction. If the model is near-perfect, the damage function is feeding the covariates too cleanly — go back to §2.2 and add frailty.

---

## 5. Phase 4 — Agent wiring

| Step | Detail |
|---|---|
| 4.1 | Register tools with the agent. Verify the tool-call trace renders |
| 4.2 | System prompt: **the LLM narrates and retrieves; it never computes a number.** Every figure in output must be traceable to a tool return or a cited document |
| 4.3 | Tune each act's prompt against the verbatim prompts in demo_flow §3 |
| 4.4 | **The Act 2 push-back** — decide model-driven vs hard-coded. Recommendation: **hard-code it.** It is the most-remembered beat and too important to leave to sampling |
| 4.5 | The Act 3 circularity answer — rehearse it, do not improvise it |

---

## 6. Phase 5 — Reports

**The cheapest phase and the one that sells it.** Three queries and three templates over the nightly run table. Specification in [decision_architecture.md §6](./decision_architecture.md).

| Report | Audience | Source |
|---|---|---|
| Daily | Asset Manager | Delta of tonight's run vs last night's |
| Weekly | AM + rig coordinator | 14-day rig calendar + rigless queue + slippage |
| **Monthly** | **Basin Manager / ED** | Aggregation + post-job actuals + **rejection log** |

> [!IMPORTANT]
> **`generate_report()` must not recompute anything.** If the monthly total disagrees with the sum of the dailies, that is a bug, not a reconciliation. Reports read the same table the drafts came from.
>
> **The monthly must include "Where the system was wrong."** It is the section that makes the rest believable — and it means the generator must also produce false positives and missed failures, deliberately.

---

## 7. Phase 6 — Rehearsal

| # | Check |
|---|---|
| 1 | Full run-through at 10 minutes with Act 5 in |
| 2 | Second run-through with **Act 5 cut** — the compressed path |
| 3 | Act 2 push-back fires **every time** |
| 4 | Act 3 PDF citation resolves to a real, openable document |
| 5 | Every act inside its latency budget on the **conference wifi**, not the office LAN |
| 6 | Offline fallback: screen-recorded video of every act, ready to play |
| 7 | Synthetic-data banner visible and the methodology answer rehearsed |
| 8 | Chan sign convention verified on screen — coning negative, channelling positive |

---

## 8. What is still blocking

| # | Item | Owner | Blocks |
|---|---|---|---|
| 1 | **Demo date** | You | The entire schedule, and whether CalGEM validation is feasible |
| 2 | **Vega `geoshape` + projection support in GE** | Eng | Act 1 — spike 0.1 |
| 3 | **Confirm SPM / stroke / plunger dia / runtime / CHP are generatable** | Eng | The fillage proxy, and therefore the top mechanical feature |
| 4 | **SPE-212848-PA full text** | You | The only ONGC-specific failure-mechanism source. §1 of the feature spec rests on an inference from its abstract that was formally retracted |
| 5 | Assam-literate reviewer for a data sanity check | You | Credibility of Phase 1 output |
| 6 | Decide: build the CalGEM validation? | You | The difference between *"tested on ~50,000 real onshore wells"* and *"we generated data"*. ~1 week |
| 7 | Does Assam already run acoustic fluid-level shots? | You | If yes, the diagnosis layer gets materially stronger for free |

> [!NOTE]
> **Items 2 and 3 are the only ones that stop work starting.** Everything else can proceed in parallel. Phase 0 and Phase 1 can both begin today.
