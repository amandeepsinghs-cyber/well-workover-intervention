# Spec Cross-Document Audit

**Scope:** all nine documents in [`spec/`](./spec/) · **Date:** 2026-09-23 · **Auditor:** full line-by-line read of `03`, `05`, `06`, `07` (subagent-authored) plus automated cross-reference of all nine

---

## 0. The answer, first

> **One blocking defect: the first 195 seconds of the demo — the map and the plotting — have no tool contracts. `04` specifies 15 tools and not one of them draws a map or plots a production curve. `07` calls four tool names that exist in no other document.**
>
> Everything else is fixable in an hour. This one needs three new tool contracts written before Phase 0 starts, because the map is `RISK-001` and the map is the first thing the Executive Director sees.

**Verdict on the subagent-authored documents:** structurally sound, physically accurate on the points that matter most, and internally consistent with `00`'s constants. The Chan convention is correct in all four. The failure taxonomy reconciles. The one physics error found (`GK-055`) is the same *class* of error already caught on re-perforation, which suggests the rigless/rig boundary is where this project reliably goes wrong and should be audited every time the job catalogue is touched.

---

## 1. Defect register

| # | Sev | Document | Defect | Recommended fix |
|---|---|---|---|---|
| **D-01** | 🔴 | `04`, `07` | **Acts 1 and 2 have no tool contracts.** `04` defines `TC-001`…`TC-015`; none serve the map or the plot. `07` calls `render_map()`, `plot_production()`, `query_production_rates()`, `query_decline_residuals()` — all four appear **only** in `07`. `08` already writes acceptance tests against them (`AT-101`…`AT-105`, `AT-110`, `AT-112`) | Add **`TC-016 render_well_map()`**, **`TC-017 plot_production()`**, **`TC-018 query_wells()`** to `04` with the same rigour as TC-001…015, including the three-tier map fallback as an explicit return field. Update `07` Act 1/2 sequences. Collapse the two invented query tools into one `query_wells()` with an `order_by` enum covering both `oil_rate_bopd` and `decline_residual_pct` |
| **D-02** | 🟠 | `03` §12 | **`GK-055` fixture reads "Rigless slickline pump changeout."** Physically impossible on a sucker-rod pumped well: the insert pump is retrieved by pulling the **rod string**, which needs a pulling unit. Slickline cannot do it. This is the identical error class to the re-perforation one already fixed by `TC-008.5` | Change to **"Pump changeout — pulling unit, `requires_rig = TRUE`."** Then add `AT-041c`: *no job in `job_catalogue` that requires pulling the rod string may be marked rigless* — the general form of `TC-008.5`, so this class of error cannot recur |
| **D-03** | 🟠 | `07` Act 5 | **Prompt says "Geleki and Lakwa."** Contradicts `00` §1.2 (*"Geleki only. Multi-asset rollout is out of scope"*) and `07` Act 1's own rule (*"Must NOT appear: wells from other fields"*). An ED who notices will ask which it is | Drop Lakwa. Rewrite as *"Build next month's workover plan for Geleki…"* |
| **D-04** | 🟠 | `07` §2, §3 | **`AS-012` is referenced twice in `01`** (§ push-back, `RISK-008` mitigation) **but `07` defines only `AS-001`…`AS-008`** — all guardrails. The per-act behaviours and the push-back have no IDs at all, so nothing in `01` or `08` can point at them | Assign `AS-010`…`AS-015` to the six per-act behaviour blocks in §2, and **`AS-012` to the push-back** in §3 so the existing references in `01` resolve |
| **D-05** | 🟠 | `06` §4.3 | **The monthly mockup contradicts its own claim.** Job mix reads `rod 26%` against a taxonomy of 30% — a **−4pp deviation** directly above the line *"deviation from expected taxonomy within ±3pp — no drift."* `TUBING_LEAK` (7%) is absent entirely and `water shutoff 13%` is not a failure code | Two things are being conflated: **executed job categories** and **failure-code taxonomy**. They are not the same population — water shutoff is a job, not a failure mode. Split the mockup into two lines, and make the ±3pp check apply only to failure codes |
| **D-06** | 🟠 | `06` §4.2 | **BigQuery type error.** `DATE_TRUNC(decided_at, MONTH)` where `decided_at` is a `TIMESTAMP`. `DATE_TRUNC` takes a `DATE`; this raises at parse time | `TIMESTAMP_TRUNC(decided_at, MONTH)`, or `DATE_TRUNC(DATE(decided_at), MONTH)` if IST-local grouping is wanted — and it should be, given the 08:00 IST delivery |
| **D-07** | 🟡 | `06` §5.2 | Root cause 4 reads *"Sudden mechanical rod part without warning (statistically expected for 25% of failures)."* `SUDDEN_MECH` is **5%**. The 25% unpredictable share is `SUDDEN_MECH 5% + OTHER 8% + SURFACE 12%` | Restate as *"Expected-unpredictable: the 25% of failures with no recoverable precursor — sudden mechanical 5%, other 8%, surface/power 12%"* |
| **D-08** | 🟡 | `06` §10, `RS-004` | **Stale.** Both still say the schema addition is *required*; `well_run.logistics_blocker` and `earliest_start_date` were added to `02` on 2026-09-23 | Mark **APPLIED** with the date, and add `earliest_start_date` to the list |
| **D-09** | 🟡 | `05` `MS-021` | **Expected range for well age is `> 20,000 days`** — that is 54.8 years. `SD-012` draws completion dates to **2015-12-31**, so the minimum is ~4,000 days | Correct to **`4,000 – 21,500 days`** |
| **D-10** | 🟡 | `03`, `05` `MS-022` | `MS-022` consumes `max_dls_deg_30m` for *"minority deviated wells"*, but **`03` has no generation rule for it** and `SD-015` sets 100% SRP with no deviation model. The feature would be all-`NULL` or absent | Either add `SD-018b` generating near-zero DLS with a small tail, **or** state in `MS-022` that the field is `NULL` in the synthetic set and the feature is inert. **Recommend the latter** — it is honest, and a demoted feature that is literally absent is easier to defend than one that is fabricated |
| **D-11** | 🟡 | `07` §2 | **Act 3 tool sequence is incomplete.** It lists 8 calls but omits `rank_candidates()` (`TC-010`) although the output is described as *"a ranked markdown table"*, and omits `detect_mechanical_signature()` (`TC-005`) although Trigger C depends on it per `TC-007`. The drill-down omits `generate_draft_plan()` (`TC-013`) although it produces a draft plan | Insert `TC-005` after `fillage_proxy()`, `TC-010` before the table renders, and `TC-013` in the drill-down. **`AT-084` requires ≥8 named tool calls visible** — the corrected sequence gives 10 |
| **D-12** | 🟡 | `07` §3 | **Markdown defect.** The `> [!IMPORTANT]` block is immediately followed by `4. **Reliability requirement:**` with no `>` prefix, so the alert renders empty and the list item is orphaned | Prefix the line with `>`, or move it out of the alert |
| **D-13** | 🟡 | `07` Act 5 / `00` §5.1 | **`N_RIGS = 15` is defined as the whole Assam Asset fleet**, but Act 5 applies all 15 to Geleki alone. An ONGC reader knows the Geleki allocation is a fraction of that | State the assumption explicitly in Act 5 — *"the 15 Assam Asset rigs, of which N are typically allocated to Geleki"* — or scope the prompt to the Geleki allocation |
| **D-14** | 🟡 | `08` §2 | **No L1 unit tests for `TC-014 generate_report()` or `TC-015 schedule_rigs()`.** `TC-014` is covered at L5 only (`AT-140`…`AT-144`); `TC-015` has no test at any level | Add L1 tests for `TC-014` aggregation arithmetic. `TC-015` is P2/Act-5-optional — acceptable to leave untested, but **say so explicitly** rather than leaving a silent gap |

### Found 2026-09-23 (second pass), while propagating refinement #6

| # | Sev | Document | Defect | Recommended fix |
|---|---|---|---|---|
| **D-15** | 🔴 → ✅ **FIXED** | `00` §5.2, `03` §3, `model_data_foundation` §4.2, `build_plan`, `08` | **The consistency triangle did not close; the blend was never actually applied.** Re-derived 2026-09-23 with two populations: `E_DOWNTIME_RIG` **48.5 d**, `E_DOWNTIME_RIGLESS` **2.0 d**, `RIGLESS_SHARE` **24%** → `E_DOWNTIME_BLENDED` **37.3 d** → `FRACTION_DOWN_ACTIVE` **16.3%**, plus a **4.5% permanently-idle carve-out** to reconcile to the Tamil Nadu 20.0%. Circular 0.2pp claim withdrawn. Propagated to all affected files. Decision 1 in `model_data_foundation` reversed to **two populations** |
| **D-16** | 🟠 → ✅ **FIXED** | `00` §5.3, `03` §6, `05` | **The failure taxonomy is a sucker-rod taxonomy, but refinement #5 set the lift mix to 70% SRP / 20% gas lift / 10% natural.** `ROD_PART`, `PUMP_WEAR` and rod-on-tubing `TUBING_LEAK` — **53% of the taxonomy** — are physically undefined on the 43 non-SRP wells. A gas-lifted well fails on valves, on the injection-gas system and on tubing corrosion, not on a rod string. The taxonomy shares and `RIGLESS_SHARE = 24%` were both computed as if the field were still 100% SRP | **DONE.** `00` §5.3 now carries an explicit *"this table is SRP only"* scope block. `03` §6.2 adds the gas-lift taxonomy (`SD-028`…`SD-031`) and `SD-032` for natural flow. **`RIGLESS_SHARE = 24%` is retained and re-labelled as the SRP figure**, with the blended field figure stated as higher and unquantified — we will not invent it. **Bonus catch: `SD-031` splits compressor failure out as a *field* event, not a well event** |
| **D-17** | 🟠 → ✅ **FIXED** | `02` §2, `03` §2 | **`well_master` required `perf_top_m`, `perf_bottom_m`, `total_depth_md_m` and `total_depth_tvd_m` as `NOT NULL`, and no document anywhere specified how to generate any of them.** The only adjacent rule was `SD-013` (zone assignment). The implementer would have invented four depths, and the natural guess — the "3,000–4,200 m" figure then in circulation — is **refuted**: Geleki Tipam producers sit at ≈ **2,400–3,100 m** | **DONE.** `SD-013b`…`SD-013d` added with per-zone truncated normals, a TVD/MD ratio bound, and a pump-setting-depth rule that puts the pump **above** the perforations. `03` §2.2 records the grounding and flags the Barail band as interpolated |
| **D-18** | 🔴 | `02` §8, `04` `TC-001`, `07` §4 | **Nothing in the spec set handled production ALLOCATION.** `daily_production.data_source` existed, and no tool read it. On real ONGC data most daily per-well rates are back-allocated from the GGS total, so **a well's rate steps when a *neighbour* is re-tested** — and `TC-001` would have reported that as a 30% mechanical loss at every well on the GGS simultaneously. **The single most likely way this demo fails on contact with real data** | **DONE.** [`data_pipeline.md`](./data_pipeline.md) §5 (`DP-001`…`DP-005`); `TC-001` now weights `TESTED` 3× and excludes basis changes (`TC-001.7`/`.8`); `well_run` gains `data_as_of`, `data_lag_days`, `run_confidence`, `tested_days_90d`, `allocation_basis_id`; `DC-067`…`DC-072`; agent guardrails `AS-017`…`AS-022` |

---

## 2. What passed

Worth recording, because these were the things most likely to be wrong.

> [!WARNING]
> **Three rows below were wrong, and the way they were wrong is instructive.** The *"consistency triangle ✅"* check verified only that `03` §3 **reproduced** `00` §5.2 faithfully. It never re-ran the arithmetic. Two documents agreeing with each other is not the same as either being right — see `D-15`. Rows retracted on the second pass are marked ⛔.

| Check | Result |
|---|---|
| **Chan sign convention** across all nine documents | ✅ Correct everywhere. `03` §8 generates the matching mathematical forms; `07` restates it in the system prompt; `08` `AT-030d` sweeps it |
| **Failure taxonomy sums** | ⛔ **Superseded by refinement #6.** The audited set (30+20+15+12+8+7+5+3) summed to 100 but the shares themselves were wrong; the corrected set in `00` §5.3 is 22+18+15+13+12+8+5+5+2 = 100. `03` §6 has **not** yet been propagated |
| **Unpredictable share arithmetic** | ✅ `MS-101` states 5+8+12 = 25%, consistent with `PREDICTABLE_SHARE = 75%`. Survives the taxonomy correction unchanged |
| **Consistency triangle** | ⛔ **Retracted — see `D-15`.** The check confirmed `03` §3 reproduces `00` §5.2. It did not confirm the derivation closes. It does not |
| **Circularity claim consistency** | ✅ `05` §11 says 4 of 7; `07` §6 says 4 of 7; `08` `AT-061` asserts ≥4 of 7 |
| **Rigless share** | ⛔ **Superseded.** 27% was consistent across `00`, `03`, `07` §7, `08` `AT-041a` — and consistently unsourced. Now derived at **24%** in `00` §5.3 and **fully propagated**. Scoped to the SRP subset under `D-16`; the blended field figure is higher and deliberately left unquantified |
| **C-index gates** | ⛔ **Superseded by refinement #8.** The 0.65–0.80 band was consistent everywhere; it is being re-baselined to **0.65–0.72** |
| **AUC leak threshold** | ✅ >0.95 = hard build failure in `00`, `05` `MS-101`, `08` `AT-023d` |
| **THP demotion / CHP promotion** | ✅ Held in `03` `SD-021`/`SD-023`, `05` `MS-012`/`MS-016`, `00` glossary |
| **Dogleg demotion** | ✅ Held in `05` `MS-022` with the SPE-212848-PA retraction stated |
| **ID cross-references** | ✅ All `FR`, `NFR`, `DC`, `SD`, `TC`, `MS`, `RS`, `AT`, `RISK` references resolve to a definition. **`AS-012` is the sole exception** — see `D-04` |
| **Traceability coverage** | ✅ 37 of 38 `FR` have ≥1 `AT`; `FR-082` deferred and marked |
| **Censoring, job success rate, deliberate imperfections** | ✅ `03` §10 aligns with `05` §1 (~40% censored) and `08` `AT-046`, `AT-042D` |

---

## 3. The pattern worth naming

**Three of the errors caught on this project are the same error: calling a job rigless when it is not.**

| Occasion | The claim | The reality |
|---|---|---|
| Research pass | Re-perforation is rigless wireline | The rod string and pump occupy the tubing; a gun cannot pass them |
| `03` §12 (this audit) | Slickline pump changeout | The insert pump comes out with the rod string; that needs a pulling unit |
| *Latent risk* | Any CT or wireline job on an SRP well | **Nothing enters the wellbore of a rod-pumped well without first pulling the rods** |

The rigless share is a **commercial claim in the pitch** — *"24% of these need no rig, so you have capacity you didn't know about."* If the catalogue over-counts rigless jobs, that number inflates and the claim becomes false in front of the people who would know.

> [!IMPORTANT]
> **Recommendation: promote this to a general invariant, not a per-job correction.** Add to `04` as `TC-008.6` and to `08` as `AT-041c`: *on a well with `lift_type = 'SRP'`, any job requiring access below the pump seating nipple is `requires_rig = TRUE`, no exceptions.* Then re-audit all 28 rows of the catalogue in [decision_architecture.md](./decision_architecture.md) §3 against it.

---

## 4. Recommended order of fixes

| Order | Fix | Effort | Why first |
|---|---|---|---|
| 1 | **D-01** — write `TC-016`/`017`/`018` | ~1 h | Gates Phase 0. The map spike (`RISK-001`) cannot be specified without a contract to spike against |
| 2 | **D-02** + the `TC-008.6` / `AT-041c` invariant | ~30 min | Protects a commercial claim. Also re-audit the 28-job catalogue |
| 3 | **D-04** (`AS-012`), **D-03**, **D-05**, **D-06** | ~30 min | Broken reference, scope contradiction, self-contradicting mockup, SQL that will not parse |
| 4 | **D-07** … **D-14** | ~30 min | Batch as one editing pass |

**Total: roughly 2.5 hours to a clean, signed-off spec set.**

---

## 5. The ask

**Go-ahead to apply all fourteen fixes in one batch?**

Two of them need a decision from you rather than a correction from me:

1. **D-10 (dogleg):** generate a DLS column with near-zero variance, or declare the feature inert in the synthetic set? **I recommend declaring it inert** — an absent feature is easier to defend to an ED than a fabricated one. ✅ *Resolved: inert.*
2. **D-13 (rig count):** does Act 5 plan against all 15 Assam Asset rigs, or against Geleki's actual allocation? **If you know the Geleki number, it is a better demo** — a real constraint beats a round one. ⏳ *Open.*

---

## 6. `D-15` — the availability arithmetic, re-derived

### 6.1 What the documents currently say

```
Uptime    Weibull(β = 2.0, η = 216.7)        E[uptime]   = 192.0 d  (6.3 months)
Downtime  LogNormal(μ = 3.219, σ = 1.142), floored at 8 d
          E[downtime | rig-requiring]         = 56.2 d          ← unsourced
          Blended across all failure codes    = 48.7 d          ← does not follow

  fraction of ACTIVE stock down = 48.7 / (192.0 + 48.7) = 20.2%
```

### 6.2 Why it cannot be right

| Step | Check | Result |
|---|---|---|
| Mean of `LogNormal(3.219, 1.142)` floored at 8 d | $8 \cdot \Phi(z) + e^{\mu + \sigma^2/2}\,(1 - \Phi(z - \sigma))$, $z = (\ln 8 - \mu)/\sigma$ | **48.49 d** |
| Can any sub-population of it average 56.2 d? | 48.49 d is the mean of the **whole** distribution. Rig jobs are the *upper* part of it, so conditioning does raise the mean — but only if the rigless jobs are the *bottom* draws of the same distribution, and the spec assigns rigless jobs a **fixed 1–3 d**, outside the distribution entirely | **No. 56.2 is unreachable** |
| Blend, taking the spec at its word | $0.27 \times 2 + 0.73 \times 56.2$ | **41.6 d**, not 48.7 d |
| Where 48.7 actually comes from | It is **48.49 d** — the *unblended* floored mean — rounded | **The blend was never applied** |

> [!CAUTION]
> **The three-source reconciliation is therefore circular.** The 20.2% was not an independent confirmation of the Tamil Nadu census; it is the unblended lognormal mean divided by the Weibull mean, with a blending story written around it afterwards. **This is a spoken beat in the demo and it is the single most likely thing in the pack to be checked by a reservoir engineer with a calculator.**

### 6.3 The corrected derivation

```
Uptime    Weibull(β = 2.0, η = 216.7)              E[uptime]      = 192.0 d  (6.3 months)
Downtime  rig-requiring   LogNormal(3.219, 1.142), floored 8 d
                                                   E[down | rig]  =  48.5 d   ← computed
          rigless         1–3 d                    E[down | -rig] =   2.0 d
          RIGLESS_SHARE = 24%  (00 §5.3, derived)
                                                   E[down] blended =  37.3 d

  failure-driven downtime, ACTIVE stock  = 37.3 / (192.0 + 37.3) = 16.3%
  permanently-idle carve-out                                      =  4.5%
  ────────────────────────────────────────────────────────────────────────
  total connected-but-not-flowing = 0.045 + 0.955 × 0.163          = 20.0%
```

| Constraint | Independent source | Model | Match |
|---|---|---|---|
| Rod pump MTBF 5–9 months | SPE-212848-PA, widened | **6.3 months** | ✅ mid-band |
| Rig wait 8–205 days | CAG Report No. 42 of 2015 | floor **8 d**, p96.7 = **204.1 d** | ✅ |
| ~20% of connected wells shut-in | Tamil Nadu 2018 census, discounted | **20.0%** | ✅ |
| Permanently-idle share plausible? | `model_data_foundation` §4.3 concluded *"only 5% idle is marginally credible"* | **4.5%** | ✅ |

> [!NOTE]
> **The corrected version is a stronger claim than the broken one, not a weaker one.** It reconciles **four** quantities instead of three, it no longer requires an unsourced 56.2 d, and the 4.5% idle carve-out it forces out lands exactly where §4.3 independently said the only credible value was. The arithmetic now closes because the physics closes, which is the thing we were claiming all along.

### 6.4 Recomputed sensitivity

At `RIGLESS_SHARE = 24%`, `E[down] = 37.3 d`:

| Weibull η | E[uptime] | Active-stock down | Total at 4.5% idle |
|---|---|---|---|
| 188 | 5.5 mo | 18.3% | 22.0% |
| 200 | 5.8 mo | 17.4% | 21.1% |
| **216.7** | **6.3 mo** | **16.3%** | **20.0%** |
| 240 | 7.0 mo | 14.9% | 18.7% |
| 270 | 7.9 mo | 13.5% | 17.4% |

### 6.5 What this reverses

> [!IMPORTANT]
> **`model_data_foundation.md` §4.3 and Decision 1 in §8 must be rewritten.** They currently conclude *"the ~20% is ONE population — the actively cycling stock — and long-term-idle wells sit outside it."* Under the corrected blend the opposite holds: **a small permanently-idle carve-out of 4–5% is now required**, and a 10%+ carve-out remains ruled out exactly as before. The disproof logic in §4.3 is sound; only the input number was wrong, and the conclusion flips from *none* to *about one well in twenty-two*.

**Affected files:** `spec/00` §5.2, `spec/03` §3, `model_data_foundation.md` §4.2 / §4.3 / §8, `build_plan.md` §(triangle block), `demo_flow.md` §(triangle block), `spec/08` (`AT-040`-series tolerance).

### 6.6 Resolution of `D-15` — CLOSED 2026-09-23

**Resolution applied across all affected documents:**
1. Re-derived under §6.3 with two populations: `E[downtime | rig]` **48.5 d**, `E[downtime | rigless]` **2.0 d** (24% share) → `E[downtime blended]` **37.3 d**.
2. Active shut-in fraction: **16.3%** (`FRACTION_DOWN_ACTIVE`).
3. Total shut-in fraction: **20.0%** (`FRACTION_DOWN_TOTAL`), reconciling with the 20% Tamil Nadu census via an explicit **4.5% permanently-idle carve-out**.
4. Spoken claim corrected: the circular *"three independent sources reconcile to 0.2 percentage points"* claim is **withdrawn**. The upper tail (`p96.7 = 204.1 d` vs CAG 205 d) is corroborated; the 20.0% total is **fitted**.
5. Reversal enacted: `model_data_foundation.md` Decision 1 reversed from *one population* to *two populations*.
6. Contracts updated: `DC-092` and `AT-092` now test both `FRACTION_DOWN_ACTIVE = 16.3% ± 1.0pp` and `FRACTION_DOWN_TOTAL = 20.0% ± 1.0pp`.
7. Propagated to: `spec/00` §5.2, `spec/02` (`DC-092`), `spec/03` §3, `spec/08` (`AT-092`), `spec/README.md`, `model_data_foundation.md`, `demo_flow.md`, `data_pipeline.md`, `build_plan.md`, `build.md`.

