# 05 · Model Specification

**System:** Agentic Workover Intervention Planning — ONGC Assam Asset (Geleki)
**Version:** 1.0 · **Date:** 2026-09-23
**Parent:** [00_overview.md](./00_overview.md) · **Consumed by:** [07_agent_spec.md](./07_agent_spec.md), [08_test_plan.md](./08_test_plan.md)

---

## 0. The answer, first

> **This is a SURVIVAL / time-to-event problem with right censoring, NOT binary classification. The model must beat Trigger B (days since last intervention, throughput-weighted) on the same holdout, or it does not ship.**

---

## 1. Problem formulation

| ID | Requirement |
|---|---|
| **MS-001** | **The model must frame failure prediction as a time-to-event survival analysis, not a binary "fails in 90 days" classification.** |
| **MS-002** | **The prediction target is a continuous hazard curve yielding an expected time-to-failure for every active well.** |

**Why survival, not classification:** A binary flag says *"these 14 wells are at risk."* A survival model says *"rank all 142 by expected time-to-failure and expected deferred barrels."* **Only the second can feed `rank_candidates()` and `schedule_rigs()`.** The declared success metric — deferred barrels avoided per rig-day — requires a ranking, not an alarm.

**Right censoring:** Roughly ~40% of recent episodes in the `workover_history` table are wells still running at the end of the observation window. Their exact failure time is unknown, but it is bounded strictly below by their current run-life. **Discarding censored wells discards the healthiest wells in the population, silently biasing the model.** Survival models natively handle right censoring as partial information.

**Event definition:** An event occurs when `workover_history.is_censored = FALSE`. Planned maintenance is not treated as a failure event; only unplanned interventions mapping to the 8-code taxonomy are modelled as failure events.

---

## 2. Feature specification

The features below map exactly to the Tier A/B/C/D structure defined in `model_data_foundation.md`. 

> [!WARNING]
> **Two critical corrections are applied here that must not be regressed:**
> 1. **DOGLEG SEVERITY IS DEMOTED.** Geleki wells are 1968-vintage near-vertical. DLS has near-zero variance and carries no discriminating information. The correct vertical-well mechanism is FLUID POUND, captured by the fillage proxy. The inference that SPE-212848-PA named DLS as the dominant feature is formally retracted.
> 2. **THP DRIFT IS DROPPED as a pump-wear signal.** On a rod-pumped well producing into a flowline, Tubing Head Pressure (THP) is set largely by flowline/separator backpressure. RISING CASING HEAD PRESSURE (CHP) is the correct pump-wear signal. THP is retained **only** as a wax indicator.

### Tier A — from daily production data alone

| ID | Feature | Exact Computation | Source | Window | Units | Expected Range | Rationale & Citation |
|---|---|---|---|---|---|---|---|
| **MS-010** | **WOR and WOR′** | `d(WOR)/d(ln t)` | `daily_production.water_rate_bwpd`, `oil_rate_bopd` | 30d, 90d | Ratio/day | -2.0 to +3.0 | Top Tier A feature. Log-log slope separates coning from channelling from multilayer. *(Chan, SPE-30775)* |
| **MS-011** | **Pump Fillage Proxy** ⚠ **SRP ONLY** | `(0.1166 * Ap * S * N * runtime_fraction) - liquid_rate_blpd` | `daily_production`, `well_master` | 7d rolling | bbl/d | 0 to 100 | Fluid-pound detection; the dominant **rod-pump** mechanical driver. **Physically undefined on `GAS_LIFT` and `NATURAL` wells** — there is no plunger. Returns `UNAVAILABLE` there (`TC-003`, `SD-015b`), never a default |
| **MS-012** | **Casing Head Pressure (CHP) drift** | `d(chp_kgcm2)/dt` | `daily_production.chp_kgcm2` | 14d | kg/cm²/d | 0 to 0.5 | Rising CHP ⇒ annular fluid backing up as volumetric efficiency drops. |
| **MS-013** | **Liquid rate residual** | `(actual - expected) / expected` | `daily_production`, Arps fit | 7d | % | -1.0 to 1.0 | Departure from the fitted Arps decline. |
| **MS-014** | **Runtime fraction & SPM** | Raw mean and rolling variance | `daily_production.runtime_fraction`, `spm` | 7d | %, SPM | 0 to 1.0; 4 to 12 | Falling runtime or rising SPM at flat production ⇒ fillage loss. |
| **MS-015** | **Water rate (absolute)** | 7d rolling mean | `daily_production.water_rate_bwpd` | 7d | bwpd | 50 to 500 | Drives both corrosion and scale accumulation. |
| **MS-016** | **THP drift** | `d(thp_kgcm2)/dt` | `daily_production.thp_kgcm2` | 14d | kg/cm²/d | 0 to 0.5 | THP rises on near-surface restriction (wax indicator only). |

### Tier B — periodic well tests and static attributes

| ID | Feature | Exact Computation | Source | Window | Units | Expected Range | Rationale & Citation |
|---|---|---|---|---|---|---|---|
| **MS-020** | **Pump Geometry** | `plunger_diameter`, `stroke_length` | `well_master` | Static | in | 1.25-2.0, 54-100 | Required to compute the fillage proxy. |
| **MS-021** | **Well age** | `run_date - completion_date` | `well_master` | Static | days | 4,000–21,500 | Completion dates span 1968–2015 (`SD-012`), so the range runs from ~11 to ~58 years. Corrosion and casing condition scale with age. |
| **MS-022** | **DLS — INERT in v1** | `max_dls_deg_30m` | `well_master` | Static | deg/30m | — | **`NULL` throughout the synthetic dataset.** Geleki wells are 1968-vintage and near-vertical, so there is no deviation to generate and no variance to learn from. The feature is retained in the schema for real ONGC data, where deviated wells exist, but **it contributes nothing in v1 and must not be reported as if it did.** Generating a plausible-looking DLS column would be fabricating a covariate to make a demoted feature look alive. |

### Tier C — event history

| ID | Feature | Exact Computation | Source | Window | Units | Expected Range | Rationale & Citation |
|---|---|---|---|---|---|---|---|
| **MS-030** | **Days since intervention** | `run_date - last_intervention_date` | `workover_history` | Dynamic | days | 0 to 1,500 | The baseline covariate for any survival model. |
| **MS-031** | **Prior run-life** | Previous `run_life_days` | `workover_history` | Historical | days | 0 to 1,500 | Wells exhibit failure memory. |

### Tier D — telemetry (OUT OF SCOPE for v1)

| ID | Feature | Exact Computation | Source | Window | Units | Expected Range | Rationale & Citation |
|---|---|---|---|---|---|---|---|
| **MS-040** | **Scaled load ratio** | Min/max surface rod loads | Dynamometer | Real-time | Ratio | N/A | *Jung et al. SPE-233386-PA (F1=0.857, ~14-day lead)*. Excluded for now. |

---

## 3. Feature engineering rules

| ID | Requirement |
|---|---|
| **MS-050** | **NULL production days:** Per `DC-014`, missing production is `NULL`, never `0`. Imputing zeros for shut-in days will fatally poison the decline residual and trigger false positives. |
| **MS-051** | **Lagged features:** Rolling statistics (mean, variance, slopes) must be computed in strictly backward-looking windows (e.g., `[t-7, t]`). |
| **MS-052** | **Leakage prevention:** The model must NOT see anything computed after the failure date, nor the synthetic data's hidden frailty term, nor the synthetic cumulative damage state variable `W(t)`. |

---

## 4. Label construction

| ID | Requirement |
|---|---|
| **MS-060** | **Target Variables:** The primary targets for the survival model are `duration = run_life_days` and `event = NOT is_censored`, derived directly from `workover_history`. |
| **MS-061** | **All-cause primary model:** The primary model predicts all-cause mechanical and wellbore failure to derive the universal ranking metric (time-to-failure). |
| **MS-062** | **Per-mechanism secondary multiclass:** A secondary, dependent model estimates cause-specific hazards across the 8 failure codes (e.g., `PUMP_WEAR`, `WAX`, `ROD_PART`) to feed the diagnostic layer. |

**Justification:** A well cannot die twice. Treating this as a competing risks problem ensures the overall survival curve accurately reflects the aggregate probability of staying online, while the mechanism-specific layer helps route the draft plan (e.g., rig vs. rigless). 

---

## 5. Model class

| ID | Requirement |
|---|---|
| **MS-070** | **Primary Model:** Random Survival Forest (via `scikit-survival`). |
| **MS-071** | **Interpretable Baseline:** Cox Proportional Hazards (via `lifelines`). |
| **MS-072** | **Hyperparameter Space (RSF):** `n_estimators` ∈ [100, 500], `min_samples_split` ∈ [10, 50], `min_samples_leaf` ∈ [5, 20]. |

> [!NOTE]
> **Why LSTM and autoencoders are excluded:** Deep learning sequence models excel on high-frequency Tier D telemetry (e.g., 100 Hz dynamometer cards). On daily and monthly production data, they chronically overfit and lose to tree-based survival models, while destroying the interpretability required by the LLM drafting process.

---

## 6. Training protocol

> [!CAUTION]
> **The split must be by WELL and by TIME, never a random row split.** If the data is shuffled and split by row, the model learns the future of a well from the test set and uses it to predict the past of the same well in the training set. This is a fatal data leak.

| ID | Requirement |
|---|---|
| **MS-080** | **Holdout definition:** The test set must be a strict time-based holdout (e.g., the last 6 months of observed history) across all wells. |
| **MS-081** | **Cross-validation:** The training set must use grouped cross-validation, where groups are defined by `well_id`. A single well's entire history must remain in the same fold. |

---

## 7. Evaluation

| ID | Requirement |
|---|---|
| **MS-090** | **Primary Metric: C-INDEX.** Because the model ranks 142 wells, concordance (C-index) is the correct metric to measure ranking quality. **Do not optimize for AUC on a binary threshold.** |
| **MS-091** | **Secondary Metrics:** Time-dependent AUC, and Integrated Brier Score for overall probabilistic accuracy. |
| **MS-092** | **Calibration:** The model must emit calibrated confidence intervals for the predicted time-to-failure. The CI is explicitly rendered in the Act 3 draft plan, so it must be mathematically honest (e.g., derived from the variance of the RSF terminal nodes), not fabricated. |

---

## 8. Acceptance gates

| ID | Condition | Status if Failed |
|---|---|---|
| **MS-100** | **`C_INDEX_MIN` ≥ 0.65.** The expected honest band is **0.65–0.72** — see `00_overview.md` §5.5. **This model sees daily production data only: no dynacard telemetry, no downhole gauges.** | Do not ship the model. |
| **MS-101** | **AUC > 0.95 is a HARD BUILD FAILURE.** The synthetic taxonomy has 25% unpredictable failures (5% sudden mechanical, 8% other, 12% surface). A model scoring > 0.95 has found a data leak. | Build blocked. |
| **MS-101b** | **C-index > 0.78 ⇒ investigate before celebrating.** On this feature set it is far more likely to be a leaked failure date in a covariate than a genuinely better model. **Time-dependent AUC is expected in the same neighbourhood as the C-index — roughly 0.68–0.78 — and an AUC of 0.85 alongside a C-index of 0.68 is a contradiction, not a result.** | Investigate; do not report until resolved. |
| **MS-102** | **Must beat Trigger B.** Evaluated on the same holdout, the ML model must produce a higher C-index and lower Brier score than the heuristic baseline. | Do not ship the model. |
| **MS-103** | **Calibration tolerance.** The 90% confidence intervals must contain the true failure time for at least 85% of uncensored holdout events. | Recalibrate before shipping. |

---

## 9. The Trigger B baseline

**This is the most important section for intellectual honesty.** If a simple heuristic ranks wells as effectively as a Random Survival Forest, the ML model is operational dead-weight and we must say so.

| ID | Requirement |
|---|---|
| **MS-110** | **Definition:** `days_since_last_intervention` divided by `p50(this well's own prior run-lives)`, weighted by cumulative fluid throughput. |
| **MS-111** | **Evaluation:** Trigger B must be evaluated as a survival hazard predictor on the exact same time-based holdout as the ML model, using C-index. |

---

## 10. Explainability

| ID | Requirement |
|---|---|
| **MS-120** | **Attribution:** The model must produce per-well feature attribution (via Permutation Importance or SHAP for tree ensembles) to justify its hazard output. |
| **MS-121** | **LLM constraint:** The LLM narrates; it never computes. The attribution values passed to the LLM must originate strictly from the model. |

---

## 11. The circularity problem

> [!WARNING]
> **RISK-003: If failures are generated from covariates, and then a model is trained to predict failures from those exact covariates, the model simply recovers the generator.** This proves nothing about the real-world predictability of the asset.

**Mitigations:**
1. **Unobserved frailty:** The synthetic data generator (`03_synthetic_data_spec.md` §5) injects a hidden wear state and unobserved frailty parameters that the model is strictly blind to.
2. **Deterministic flagging:** 4 of the 7 wells flagged in the demo are flagged by Triggers A, B, and C — without the ML model at all.
3. **The honest script:** The demo must explicitly state what synthetic validation does and does not prove. It proves the pipeline, the ranking logic, and the user experience; it does not prove the physics of Assam Asset.

---

## 12. Path to real data

When ONGC asks *"has this been run on real data?"*, the answer relies on the **California CalGEM validation option**.

*   **The Data:** California CalGEM WellSTAR provides per-well oil, gas, and WATER by API number, plus days-producing, plus a statutory dated idle-well register, plus 'Method of Operation' for lift-type filtering.
*   **The Analogue:** Roughly 50,000+ Kern County wells (Midway-Sunset, Kern River, South Belridge, Elk Hills) are century-old rod-pumped high-water-cut stripper wells — a near-exact physical analogue to mature Assam.
*   **The Label:** A weak-but-real failure label IS constructible by joining drops in days-produced with the dated idle register and recompletion records.
*   **Why not Texas?** Texas RRC is unusable because it reports at the LEASE level; per-well days cannot be recovered.

---

## 13. Model versioning, retraining cadence, and drift monitoring

| ID | Requirement |
|---|---|
| **MS-130** | **Retraining Cadence:** The survival model is retrained monthly. The baseline deterministic triggers (A, B, C) operate continuously without retraining. |
| **MS-131** | **Drift Monitoring:** The system must monitor the distribution of `workover_history.failure_code` against the expected taxonomy. If the share of any failure code drifts by > ±3 percentage points, an alert is triggered. |
| **MS-132** | **Versioning:** Every `well_run` row records `model_version`. Predictions cannot be overwritten; a new model version produces a new daily partition. |

