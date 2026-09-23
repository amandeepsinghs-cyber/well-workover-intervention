# Specification — Agentic Workover Intervention Planning

**ONGC Assam Asset (Geleki)** · Version 1.0 · 2026-09-23
**Status:** 🟡 Draft complete, **not signed off.** Fourteen open defects in [§5](#5-open-defects). Two blocking engineering questions in [§4](#4-what-blocks-implementation).

---

## 0. The answer, first

> **This folder is the complete specification for a system that decides, every night, which wells in Geleki need attention, why, when they will fail, and what job fixes them — and puts a draft plan in front of the Asset Manager for signature.**
>
> Nine documents. Read `00` and `01` and you know what is being built. Read `04` and `08` and you know how to build it and when it is done.

---

## 1. Read in this order

| # | Document | Lines | Read it when you need to know… |
|---|---|---|---|
| **00** | [Overview](./00_overview.md) | 275 | The architecture, the ID scheme, **the fixed constants**, **the Chan sign convention**, the glossary, the evidence standard |
| **01** | [Functional requirements](./01_functional_requirements.md) | 324 | What the system must do — 38 `FR`, 7 `NFR`, 11 `RISK`, each with a checkable acceptance criterion |
| **02** | [Data contract](./02_data_contract.md) | 488 | The 13 BigQuery tables, units, nullability, and 97 `DC` invariants. §12 is the ask to ONGC |
| **03** | [Synthetic data spec](./03_synthetic_data_spec.md) | 228 | How the dataset is generated, the damage-and-frailty model, the validator, the 7 demo fixtures |
| **04** | [Tool contracts](./04_tool_contracts.md) | 699 | Every tool signature, return type, error semantics and worked example. **The implementation brief** |
| **05** | [Model spec](./05_model_spec.md) | 192 | The survival formulation, the feature tiers, the training protocol, the gates that stop a bad model shipping |
| **06** | [Report spec](./06_report_spec.md) | 349 | Daily / weekly / monthly, field by field, with the SQL |
| **07** | [Agent spec](./07_agent_spec.md) | 218 | The copy-pasteable system prompt, per-act behaviour, guardrails, the scripted answers to hard questions |
| **08** | [Test plan](./08_test_plan.md) | 304 | Six test levels, the seven honesty tests, the traceability matrix |

**Companion documents one level up** — these are the *why*; the spec is the *what*:

| Document | Role |
|---|---|
| [decision_architecture.md](../decision_architecture.md) v1.1 | The product. 4 triggers, the 28-job intervention catalogue, the reporting rhythm |
| [demo_flow.md](../demo_flow.md) v2.0 | The 10-minute demo, act by act, with the script |
| [build_plan.md](../build_plan.md) | Six phases ordered by technical risk, not narrative order |
| [research_appendix.md](../research_appendix.md) | Every sourced figure — **and the rejected-claims register** |
| [model_data_foundation.md](../model_data_foundation.md) | Feature tiers A/B/C/D and the public-data landscape |
| [thesis_risk_audit.md](../thesis_risk_audit.md) | Where this argument is weakest |
| **[data_pipeline.md](../data_pipeline.md) v1.1** | **Where the data comes from.** The swap point, the allocation problem (`DP-001`…`DP-014`), and the one-page ask to ONGC |
| **[build.md](../build.md)** | **12 gated stages, A–L.** The step-by-step build on the ADK and the deployment to Gemini Enterprise |
| **[spec_audit.md](../spec_audit.md)** | The defect register, `D-01`…`D-18`. **`D-15` is the one still open** |
| **[blueprint_assessment.md](../blueprint_assessment.md)** | What was extracted from two external documents before they were deleted, and what was rejected |

---

## 2. The five things that matter most

If you read nothing else in this folder, read these five.

| # | Thing | Where |
|---|---|---|
| 1 | **The Chan sign convention.** Negative WOR′ slope = coning = choke back, rigless. Positive = channelling = cement squeeze, rig. **Inverted, this sends a rig to a well that needed a 30-minute choke adjustment.** It was produced inverted once on this project | [00 §6](./00_overview.md) |
| 2 | **Three of the four triggers need no trained model.** A, B and C are arithmetic. Only D is ML. This is what makes the circularity answer honest rather than a dodge | [01 §3](./01_functional_requirements.md), [07 §6](./07_agent_spec.md) |
| 3 | **The LLM never computes a number.** It narrates, retrieves and assembles. Every figure traces to a tool return or a cited document | [00 §2.1](./00_overview.md) |
| 4 | **`NULL` is not zero.** A shut-in day written as `0` makes a healthy well read as catastrophically below its decline curve and floods the queue | [00 §8](./00_overview.md), `DC-014` |
| 5 | **The availability identity holds with two populations.** Uptime, downtime and fraction-down are closed: `E[down]` 37.3 d, active 16.3%, total 20.0% via a 4.5% idle carve-out. Corroborated upper tail (204.1 d vs CAG 205 d) is distinguished from fitted total down. `AT-092` re-checks both on every regeneration | [00 §5.2](./00_overview.md), [03 §3](./03_synthetic_data_spec.md) |

---

## 3. The seven honesty tests

Every one of them tests that the system **refuses to do something convenient.** Write these before the code they test.

| Test | It refuses to… | Spec |
|---|---|---|
| `AT-030d` ⭐ | invert the Chan sign convention, under any slope value | [08 §2.2](./08_test_plan.md) |
| `AT-003b` ⭐ | assume a plunger diameter when the field is missing | [08 §2.3](./08_test_plan.md) |
| `AT-032b` ⭐ | recommend a job when the offsets are declining too | [08 §2.4](./08_test_plan.md) |
| `AT-014` ⭐ | write a zero rate for a non-producing day | [08 §3](./08_test_plan.md) |
| `AT-073` ⭐ | let a monthly total differ from the sum of its dailies | [08 §5.4](./08_test_plan.md) |
| `AT-083` ⭐ | state a number without provenance | [08 §5.5](./08_test_plan.md) |
| `AT-072b` ⭐ | omit "where the system was wrong" from the ED scorecard | [08 §5.4](./08_test_plan.md) |

And one more that is not in the seven but should be:

| `AT-061` | runs Act 3 **with the model switched off** and asserts ≥4 of 7 rows still flag. If it fails, the scripted circularity answer in [07 §6](./07_agent_spec.md) is **literally false** and must be rewritten before anyone says it in a room |

---

## 4. What blocks implementation

> [!IMPORTANT]
> Two questions must be **answered**, not acknowledged. Both change the design.

| ID | Question | Why it blocks | Owner |
|---|---|---|---|
| `RISK-001` | Does the Gemini Enterprise A2UI renderer support Vega-Lite `geoshape` + `projection`? | Act 1 is the first thing on screen. If the answer is no, the fallback ladder in [build_plan.md](../build_plan.md) Phase 0 decides the tier | Eng |
| `RISK-002` | Can the data include SPM, stroke length, plunger diameter, runtime hours and CHP? | Without them the fillage proxy cannot be computed **at all** and the top mechanical feature disappears from `TC-003` and `MS-011` | Eng + ONGC |

**Also outstanding, not blocking:**

| Item | Owner | Why it matters |
|---|---|---|
| **The demo date** (`RISK-010`) | Assumed: 2026-10-14 | 3-week build window assumed; CalGEM deferred beyond target date (`01` §5) |
| SPE-212848-PA full text (`RISK-011`) | User | The only ONGC-specific failure-mechanism source in the evidence base |
| Build the CalGEM validation? | Decision | ~1 week. The difference between *"tested on ~50,000 real onshore wells"* and *"we generated data"* |
| Does Assam already run acoustic fluid-level shots? | Ask ONGC | The cheapest missing measurement in the whole system — separates *the reservoir won't give it* from *the pump won't lift it* |

---

## 5. Defects and refinements

### 5.1 Cross-document audit — **CLOSED 2026-09-23**

Fourteen defects were found by the audit in [spec_audit.md](../spec_audit.md) and **all fourteen are fixed.**

| Severity | Count | Resolution |
|---|---|---|
| 🔴 Blocking | 1 | **Acts 1 and 2 now have tool contracts** — `TC-016 render_well_map()`, `TC-017 plot_production()`, `TC-018 query_wells()` added to [04](./04_tool_contracts.md) |
| 🟠 Important | 5 | Two physically impossible fixtures corrected and generalised into the `TC-008.6` rig/rigless invariant; scope contradiction removed; `AS-012` now resolves; report mockup and BigQuery type error fixed |
| 🟡 Minor | 8 | Stale notes, wrong ranges, incomplete tool sequences, markdown defect |

### 5.2 Research findings — **OPEN, and larger than the audit**

Three research passes on 2026-09-23 asked whether this is the right problem. **It is the right problem, but the framing collides with software ONGC has already built,** and several domain assumptions are wrong.

> [!IMPORTANT]
> **Reconciliation status as of 2026-09-23. The research findings in [research_findings_2026-09-23.md](../research_findings_2026-09-23.md) and all 18 defects (`D-01`…`D-18`) have now been resolved across the spec set. Zero blocking defects remain.**

| Area | Status |
|---|---|
| **`D-15` — availability arithmetic derivation** | ✅ **CLOSED 2026-09-23.** Re-derived with two populations: `E[down]` **37.3 d**, `FRACTION_DOWN_ACTIVE` **16.3%**, `FRACTION_DOWN_TOTAL` **20.0%** (via 4.5% idle carve-out). Circular 0.2pp claim withdrawn. [`spec/00`](./00_overview.md) §5.2, [`spec/03`](./03_synthetic_data_spec.md) §3, [`spec_audit.md`](../spec_audit.md) §6 |
| CalGEM validation | 🟠 **Open — CalGEM is monthly, the model is daily.** Evaluate WOGCC as the replication set |
| Problem framing vs ONGC's WellEx, Udbhav and NETRA | ✅ Repositioned as the **WRFM execution layer**; the three are now named approvingly. `07` §7, `demo_flow` §1/§7 |
| 100% SRP assumption (`SD-015`) | ✅ Dropped → 70 SRP / 20 gas lift / 10 natural, **labelled as assumed**. `SD-015e` records that SPE-194798 suggests gas lift is understated |
| **`D-16` — taxonomy was SRP-only across a mixed-lift field** | ✅ Scoped. Gas-lift taxonomy at `03` §6.2 (`SD-028`…`SD-031`), natural flow at `SD-032` |
| Geleki water injection → Chan interpretation | ✅ **Injector-breakthrough branch added.** `00` §6.1, `TC-002.5`…`TC-002.7`, `SD-034`…`SD-037` |
| Failure taxonomy: tubing leak 7%, scale/sand 3% | ✅ Corrected to **22%**, and split into `SAND` 5% / `SCALE` 2%. `RIGLESS_SHARE` now **24%**, derived |
| KPI: deferred barrels per rig-day | ✅ Demoted to a **stated internal objective**. Failures/well/year and run-life lead |
| C-index band 0.65–0.80 | ✅ Re-baselined to **0.65–0.72**; AUC expectations aligned (`MS-101b`) |
| *"On production since 1968"* | ✅ Corrected to **discovered 1968, on production c.1974** |
| **`D-17` — no depth-generation rule** | ✅ Closed. `SD-013b`…`SD-013d`, grounded at `03` §2.2 |
| **`D-18` — production allocation was unhandled** | ✅ Closed. [`data_pipeline.md`](../data_pipeline.md) §5, `TC-001.7`/`.8`, `DC-067`…`DC-072`, `AS-017`…`AS-022` |

---

## 6. Conventions used throughout

| Area | Rule |
|---|---|
| **IDs** | `FR` `NFR` `DC` `SD` `TC` `MS` `RS` `AS` `AT` `RISK`. **Never reused, never renumbered.** Deprecated items are marked and retained |
| **Constants** | Defined **once** in [00 §5](./00_overview.md) and referenced. A value restated with a different number is a defect |
| **Units** | BOPD / BWPD / MSCFD · kg/cm² · metres MD · bbl · ISO 8601 dates |
| **Evidence** | Uncited numbers are unusable. Vendor claims rejected. *"Not published"* beats a plausible guess. Register in [research_appendix.md §3](../research_appendix.md) |
| **Language** | British English. `snake_case` everywhere |

---

## 7. Sign-off

| # | Document | Reviewed | Signed off |
|---|---|---|---|
| 00 | Overview | ☐ | ☐ |
| 01 | Functional requirements | ☐ | ☐ |
| 02 | Data contract | ☐ | ☐ |
| 03 | Synthetic data spec | ☐ | ☐ |
| 04 | Tool contracts | ☐ | ☐ |
| 05 | Model spec | ☐ | ☐ |
| 06 | Report spec | ☐ | ☐ |
| 07 | Agent spec | ☐ | ☐ |
| 08 | Test plan | ☐ | ☐ |

> [!CAUTION]
> **No implementation begins until the blocking defect in §5 is closed and `RISK-001` and `RISK-002` are answered.** Writing `chan_diagnostic()` before `AT-030d` exists is the single most likely way this build fails — once an implementation exists, the test gets written to match it, and if the implementation is inverted, so is the test.
