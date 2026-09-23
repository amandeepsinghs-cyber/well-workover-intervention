# Assessment · `workover_problem.md` and `workover_demo_blueprint.md`

**Date:** 2026-09-23 · **Companions:** [spec/](./spec/) · [spec_audit.md](./spec_audit.md) · [research_findings_2026-09-23.md](./research_findings_2026-09-23.md) · [build.md](./build.md)

**Method:** full read of both documents; **the blueprint's code was extracted and executed** and its outputs measured; a verification pass was run on every public dataset either document names. Nothing below about the generator is a reading — it is a measurement.

---

## 0. The answer, first

> **Yes — we are still solving the right problem, and the blueprint is independent confirmation of it. Take four things from it. Reject three. Two sections of it must never be shown to an Executive Director.**

**The confirmation matters.** These documents were written independently of our spec set and land on the same core question: *which wells are going sick, when will they fail, and in what order should they be worked over.* Two independent derivations converging is the strongest evidence yet that the framing is right.

**But the blueprint omits the one thing our research identified as the actual white space — the rig-day constraint — and adds two dependencies that do not survive checking: dynamometer cards, and four public datasets that are not what it says they are.**

| Verdict | Count | Items |
|---|---|---|
| ✅ **Adopt** | 3 | Intervention-risk term *(gated)* · Barrier pre-condition *(reshaped)* · Data tiering |
| 🟡 **Adopt narrowed** | 1 | Production Efficiency as a KPI *(not the composite index)* |
| ⛔ **Reject** | 6 | The KPI/ROI table · The synthetic generator · The dynacard dependency · The H₂S/sour-service framing · Four false dataset claims · **The Streamlit dashboard** |
| ⚠️ **Resolve** | 1 | Mehsana vs Assam scope |

> [!NOTE]
> **§1 was re-graded on a second, sceptical pass.** The first pass recommended adopting four things. Under challenge, **two of the four changed** — the Well Health Index was downgraded and the barrier gate was reshaped. Both changes are recorded in place, with the argument that moved them. A recommendation that survives its own cross-examination is worth more than one that was never tested.

---

## 1. What to adopt — cross-examined

**Each recommendation below was challenged before being kept. The challenge is stated, because a recommendation that survives one is worth more than one that was never tested.**

### R-12 · Add the intervention-risk term to `TC-010 rank_candidates()` — ✅ **ADOPT, gated**

The blueprint's $EVI_j$ and our `rank_candidates()` are nearly the same expression. Ours is better in one place and worse in another.

```
blueprint:  EVI  = P_succ · (ΔQ · P_oil · Δt) − C_WO − P_fail · C_risk
ours:       net  = deferred_bbl · realisation · P(success) − job_cost
            PRIORITY = net ÷ rig_days                       ← we have this, they don't
                                                  ↑
                                   they have this, we don't
```

**We are missing `− P_fail · C_risk`: the probability the intervention itself goes wrong, times what that costs.** Stuck pipe, a fishing job, a lost well, a barrier breach on a forty-year-old corroded string. This is what a workover superintendent actually worries about, and it is entirely absent from our ranking.

**Challenge 1 — *isn't this already inside `P_success`?*** No, and the distinction must be stated in the spec or the two will be conflated in implementation:

| Term | Meaning | Outcome |
|---|---|---|
| `1 − P_success` | The job does not achieve its objective | You spent the rig-days and the well is where it was |
| `P_complication` | The job **actively makes things worse** | Fishing, a sidetrack, or a lost well. You spent the rig-days and destroyed value |

**Challenge 2 — *can we populate it, or is this a fabricated number in the objective function?*** This is the serious objection, and it is fatal if unanswered — a made-up coefficient inside the ranking is worse than no coefficient, because it is invisible.

> **Resolution: gate it exactly as `TC-009.2` already gates `p_success`.** Fewer than five historical instances of that job type on wells of that vintage → **`P_complication = 0`, the term drops out, and the tool returns `INSUFFICIENT_HISTORY`**. The agent then says so. We are not obliged to estimate it everywhere; we are obliged never to invent it.

> [!IMPORTANT]
> **It strengthens differentiator (d), which is the one research graded genuine.** Today the agent can refuse for exactly one reason: *the well does not need a job* (`GK-141`). With this term it can also refuse because *the job is too likely to make things worse* — and `GK-129` already carries a 1998 poor cement-bond report and a failed 2019 water shut-off, so **the evidence to demonstrate it is already in the fixture set.**

**Final form, keeping our rig-day denominator:**

```
EVI      = P_success · deferred_bbl_avoided · realisation
           − job_cost
           − P_complication · C_complication     ← NEW, zero unless n ≥ 5
PRIORITY = EVI ÷ rig_days_consumed               ← retained; rig-days are the binding constraint
```

### R-13 · The Well Health Index — 🟡 **DOWNGRADED. Do not build the composite**

$$WHI_j = w_1(1 - P_{\text{fail},j}) + w_2\left(\frac{RUL_j}{RUL_{\max}}\right) + w_3\left(\frac{Q_{\text{actual},j}}{Q_{\text{potential},j}}\right)$$

**My first pass recommended this as the map colour scale. On challenge it does not hold.**

| Challenge | Why it lands |
|---|---|
| **It is the thing we criticise vendors for** | A weighted composite with three chosen weights, collapsing three different signals into one opaque number. Our entire credibility position is *traceability* — every value on screen tied to a tool call. A composite index is the opposite of that |
| **`Q_potential` is undefendable** | Actual-over-potential is the hardest quantity in the whole problem. UKCS computes it with a **formal four-stage production choke model** through the Stewardship Survey. **We cannot compute a per-well potential rate from daily production alone**, and asserting one invites precisely the challenge we cannot answer |
| **`RUL_max` is arbitrary** | Normalising by a chosen ceiling makes the index's scale a modelling choice, not a measurement |
| **We do not need it** | `TC-016` already offers `colour_by ∈ {status, trigger_state, queue, days_to_failure}`. **`trigger_state` already answers the user's *"colour code of some sort"*** — and every colour maps to a stated rule, which is strictly more defensible |

> **Revised recommendation: keep the map on `trigger_state`. Take one narrow thing instead — report Production Efficiency as a KPI where, and only where, the denominator is defensible.** The right denominator for us is not a nodal "potential" but **the well's own fitted decline curve**, which we already compute in `TC-001`. *"Actual against its own expected decline"* is a quantity we can show the working for. Name the UKCS link in conversation; do not claim the UKCS methodology.

### R-14 · The Safety & Barrier gate — ✅ **ADOPT, but reshaped**

The blueprint's sixth sub-agent audits double-barrier integrity and casing-tubing annulus pressure before a work order is issued.

**Challenge — *we do not have the data to run this audit.*** `RISK-002` means we do not even know whether we get CHP. A- and B-annulus pressures are a further measurement again, and there is no evidence ONGC Assam surfaces them per well. **An automated barrier gate we cannot actually evaluate is theatre, and a green tick we did not earn is the worst possible thing to put on a work order.**

> **Resolution — and the reshaped version is better than the original.** Do not build an automated pass/fail. Make the barrier check a **declared pre-condition printed on the face of every draft plan** produced by `TC-013`:
>
> ```
> BARRIER STATUS ......... NOT VERIFIED
> REQUIRED BEFORE EXECUTION:
>   • A/B annulus pressure test
>   • Double-barrier confirmation per OISD
> This plan is not executable until the above are signed off.
> ```
>
> **This is more credible than a tick, not less.** It shows we know what has to happen before a rig moves, it names a real control an ED expects to see, and it reinforces the human-in-the-loop posture that answers *"who signs off?"* — without claiming a check we did not perform. If annulus pressure later becomes available, the field upgrades to a real evaluation.

### R-15 · Declare an explicit data tier ladder — ✅ **ADOPT**

**Challenge — *is this even from the blueprint?*** Not directly; it is the corrective to the blueprint's habit of assuming rich telemetry throughout. It stands on its own merits either way, and it is the cleanest win of the six.

Stating it converts our open `RISK-002` from a blocker into a costed upgrade path — and it is the honest answer to *"what do you need from us?"*

| Tier | Data | Status | What it buys |
|---|---|---|---|
| **0 — required** | Daily oil / water / gas, THP, well status, workover history, coordinates | **The demo runs on this alone** | Triggers A/B, Chan diagnostic, decline residuals, survival model |
| **1 — strong uplift** | CHP, SPM, stroke length, plunger diameter, runtime hours | `RISK-002`, **unanswered** | The pump-fillage proxy `MS-011`, the dominant mechanical feature |
| **2 — best case** | Dynamometer cards, acoustic fluid-level shots | **Assume absent** | Direct component-level diagnosis |

> [!NOTE]
> **This is a selling point, not an apology.** Every commercial product in this space — Weatherford ForeSite, Ambyint, SLB Lift IQ, Baker Hughes Leucipa — assumes Tier 2 telemetry. *"We work at Tier 0, and we get better if you have more"* is a genuine differentiator against the entire vendor stack, and it is exactly the re-framing research pass 3 recommended.

---

## 2. What to reject — and the evidence

### ⛔ R-16a · The KPI / ROI table must never reach a slide

`workover_problem.md` §"Expected KPIs" promises **60–75% downtime reduction, 15–25% deferred-oil recovery, 30–40% run-life extension, 20–30% rig NPT reduction, near-zero safety incidents.**

| Problem | Detail |
|---|---|
| **Unsourceable** | The document carries **25 distinct citation markers, `[1]` through `[55]`. It contains no bibliography. Not one marker resolves to anything.** |
| **Rejected class** | These are vendor-brochure performance claims, which [`research_appendix.md`](./research_appendix.md) §3 rejects outright regardless of source |
| **Self-refuting** | *"Near-Zero High-Risk Incidents"* from an analytics layer is not a claim any operator would accept, and offering it invites the room to discount everything beside it |

> [!CAUTION]
> **This is the highest-risk item in the folder.** If one of these numbers reaches an Executive Director and is challenged, the only honest answer is *"I cannot source it"* — and everything else, including the parts that are rigorous, goes with it.

### ⛔ R-16b · The synthetic generator cannot be used — eight measured defects

**The blueprint's `generate_synthetic_data.py` and `ml_engine.py` were extracted and run.** Measured results:

| # | Defect | Measured evidence |
|---|---|---|
| **1** | **There is no production decline at all.** `q_oil = np.random.normal(base_q, base_q*0.05)` is not a function of time | Annualised trend on the 15 non-sick wells: **+0.5 bopd/yr, with 7 of 15 trending *upward***. Real mature Assam wells decline 5–15%/yr |
| **2** | **`EVI` is `ΔQ` wearing a hat** | `corr(EVI, ΔQ) = 0.9997`. With `P_succ` hardcoded at 0.90, the ranking reduces to *"which well lost the most absolute barrels since day one"* — which ranks by well size and age |
| **3** | **The queue recommends against itself** | **18 of 20 wells** sit in a "priority candidate queue" whose own `recommendation` field reads `DEFER`. Ranks 3, 4 and 5 all carry negative EVI |
| **4** | **An ESP well is diagnosed with gas-lift valve erosion** | `MEH-W-113`, `lift_type = ESP`, `diagnostic_cause = 'Gas Lift Valve Erosion'`. The else-branch never checks lift type |
| **5** | **Bottomhole pressure is unphysical and inert** | Emits **450 psi** across wells of 1,260–2,455 m. The tubing fluid column alone at 2,000 m is ~1,640 psi even for gassy oil, so minimum physical BHP ≈ 1,760 psi — **understated ~3.9×**. And `corr(BHP, oil_rate) = −0.009`: it is noise that responds to nothing |
| **6** | **No Chan diagnostic is possible** | Water cut is `base + 0.001·day` for every well. Per-well slope **std = 9.1×10⁻⁶**. Every well has an identical water trend, so coning, channelling and multilayer response cannot be distinguished — they are not in the data |
| **7** | **Survival analysis is not viable** | **61 days of history, 20 wells, 5 events.** Cox and Weibull need years and hundreds of events. Our spec uses 36 months × 142 wells |
| **8** | **Labels are broken, and there is no model** | The hardcoded dynacard-sick list `['MEH-W-103','MEH-W-106','MEH-W-118']` — **two of those three are `GAS_LIFT` wells with no rod pump**, so only **one** fluid-pound card is ever produced. Separately, `p_failure_prob` and `rul_days` are `np.random.uniform()` inside an `if/else` on the same thresholds: **there is no model, only a rule engine emitting random numbers dressed as probabilities.** An ED asking *"how did you get 82.4%?"* gets no answer |

> [!WARNING]
> **Defect 1 is fatal, and it is structural rather than a bug.** Because the dataset contains no reservoir decline, **the hardest and most valuable problem in workover candidate selection — telling a mechanical fault apart from ordinary depletion — cannot even be posed in it.** Our `GK-141` refusal case is unrepresentable. A demo built on this data would recommend a workover on every old well, in front of the only people in the room qualified to notice.
>
> Our own generator exists precisely to prevent this: Arps decline (`SD-017`), Gamma-frailty cumulative damage (`03` §5), 36 months of history, and a validator that fails the build. **Keep ours.**

**Reproduction:** [`scratch/bp/`](file:///usr/local/google/home/amandeepsinghs/.gemini/jetski/brain/50a2b34f-c03e-490a-9018-f823d7f93836/scratch/bp) — `uv run --with numpy --with pandas python generate_synthetic_data.py`, then `ml_engine.py`.

### ⛔ R-16c · Do not build on dynamometer cards

Both documents lean on wave-equation inversion plus a CNN dynacard classifier at *">95% accuracy"*. Four reasons to refuse, the last of which is new and decisive:

1. **We have no evidence ONGC Assam acquires per-well dynacards.** `RISK-002` is open. Research found institutional capability at IOGPT and Oil India acoustic surveys in Upper Assam, but **no evidence of routine per-well acquisition at Geleki.**
2. **It contradicts our strongest unclaimed differentiator** — working from daily production alone, in a regime the vendor stack is not instrumented for.
3. **The ">95%" figure is unsourced**, and falls under the same rejected class as the KPI table.
4. **There is no open labelled dynacard data to train or validate on.** See §5 — this was verified, and the blueprint's claim that such benchmarks exist is false.

**Keep dynacards at Tier 2 in `R-15`: a stated upgrade, never a dependency.**

---

## 3. One thing to resolve, one thing now settled

| # | Conflict | Recommendation |
|---|---|---|
| **1** | **Scope: Mehsana vs Assam.** The blueprint generates `MEH-W-1xx` wells in "Mehsana Asset, Cambay Basin". Our entire spec set is Geleki, Assam. `workover_problem.md` straddles both | ⚠ **Open. Stay Geleki-only.** `spec/00` §1.2 already says so and `D-03` was raised for exactly this drift. Mehsana is a *second slide*, not a second dataset — and the Assam shortfall (**−10.66%**, Apr'25–Jan'26) is the one verified asset number we have |
| **2** | **UI: Streamlit vs Gemini Enterprise.** The blueprint ships a Streamlit + Plotly dashboard | ⛔ **SETTLED — Streamlit is rejected outright.** Not narrowed, not contingent. See below |

> [!IMPORTANT]
> **⛔ `R-17` — REJECTED, 2026-09-23. The Streamlit fallback is deleted from the plan entirely.**
>
> **The reasoning, in one line: the agent is deployed in Gemini Enterprise, so the demo is in Gemini Enterprise. There is nowhere for a second UI to sit.**
>
> **This went through three positions, and the final one is the simplest.** My first read called Streamlit a better fallback than a static PNG. The sceptical pass downgraded it to contingent, on the grounds that **alt-tabbing out of Gemini Enterprise mid-demo visibly breaks the claim that the agent did this** — which is the whole point of the ten minutes. The correct answer was one step further: **a contingency you would never actually exercise is not a contingency, it is an unbuilt branch cluttering the plan.**
>
> **Tier 3 is the floor** — a pre-rendered basemap inside Gemini Enterprise, narrated honestly, with live data beside it. If Stage B shows Tier 1 *and* Tier 2 both fail, the map is the least of the problems and a second window would not rescue it.

Also discard: the **16-month roadmap** (we need weeks, not months); **"Level 4 Autonomous Agent"** (an ED will ask who signs off — our human-in-the-loop draft-plan model is the right answer and the better story); and the **PIPESIM / PROSPER / ECLIPSE MCP servers** (no licences, undemonstrable, and they put a third-party dependency on the critical path).

---

## 4. Are we solving the right problem? — the scorecard

| Question | Verdict |
|---|---|
| Is the core question right? | ✅ **Yes.** Two independent derivations converge on *which wells, when, in what order* |
| Does the blueprint find something we missed? | ✅ **Two** — intervention risk (`R-12`) and the barrier gate (`R-14`) |
| Does it miss something we have? | ⛔ **The rig-day constraint, entirely.** No rig count, no rig-vs-rigless split, no scheduling. Research named this as our white space; the blueprint confirms by omission that it is not obvious |
| | ⛔ **Reservoir-decline discrimination** — defined out of existence by its own data |
| | ⛔ **Refusal.** There is no `NO_JOB_JUSTIFIED` path anywhere in it |
| Do we have the data we need? | ✅ **For the demo, yes** — see §5 |

---

## 5. Data availability — verified

> **Every one of the four public datasets the blueprint names is wrong, missing, or misdescribed. The demo must run on our own synthetic data. Public data is for external validation of the survival model only, and the best available option gives proxy labels at monthly resolution.**

### 5.1 The blueprint's four dataset claims, checked

| Claim | Reality | Verdict |
|---|---|---|
| *"Equinor Volve — 24 wells, 10 years, daily rates, pressures, chokes"* | Real and genuinely open, but it is **7 wellbores**, not 24; **2008–2016**; **offshore North Sea**; **gas lift / natural flow, no sucker rod pumps**; and **no verified structured intervention log** | ⛔ **Wrong physics.** A rod-pump survival model has nothing to validate against |
| *"SPE Sucker Rod Pump Dynacard Datasets — open benchmarks, 30+ labelled diagnostic states"* | **No such dataset was found to exist.** SPE operates no public dynacard repository. The "30 working conditions" taxonomy comes from *papers* trained on **proprietary** operator data | ⛔ **False claim** |
| *"Utah FORGE & Kansas KGS IIoT feeds — high-frequency temperature, pressure, acoustic/vibration"* | **Utah FORGE is geothermal** (DOE Enhanced Geothermal Systems, Milford, Utah) — no hydrocarbons, no artificial lift, no rod-pump failure modes. **KGS publishes regulatory records only; no IIoT feed was found** | ⛔ **Irrelevant and non-existent respectively** |
| *(implied) KGS usable for well-level analysis* | **KGS production is reported per LEASE, not per well.** A rod-pump failure on one of six wells on a lease shows only as a partial dip in a shared total | ⛔ **Structurally unusable** |

### 5.2 The one lead worth chasing — and it closed

The strongest candidate found anywhere for real labelled rod-pump data:

> **Mossoró, Rio Grande do Norte, Brazil — >50,000 dynamometer cards from 38 sucker-rod-pumped wells, expert-labelled into 8 operating modes plus 2 sensor-fault types.** Published in *Sensors* 21(13):4546 (2021), *"Diagnostic of Operation Conditions and Sensor Faults Using Machine Learning in Sucker-Rod Pumping Wells."*
>
> **Data Availability Statement: "available on request from the corresponding author." Not open.**

Same for the Bahrain corpus (~5.38 M cards from 297 beam pumps, 35,292 expert-labelled into 12 classes) — described in the literature, never released.

> [!IMPORTANT]
> **This is a finding, not a search failure, and it is worth stating in the room.** Every labelled rod-pump failure corpus of meaningful size is held privately by the operator that generated it. **That is precisely why the white space exists** — and it is a much better answer to *"has this been done before?"* than silence.

### 5.3 What we should actually use

| Purpose | Source | Status |
|---|---|---|
| **The demo itself** | **Our own synthetic generator** — `spec/03` | ✅ **The only dataset that can simultaneously contain Arps decline, a Gamma-frailty damage process, the three Chan signatures, a rig constraint and a defensible refusal case** |
| **External validation, primary** | **CalGEM (California)** — well-level **monthly** production, the statutory **idle-well register**, and published **approved rework Notices of Intention**. San Joaquin / LA basin mature heavy-oil, high water cut, heavily rod-pumped | 🟡 **Best available.** Event = producing→idle transition, corroborated by a rework NOI. **Proxy-labelled, monthly** |
| **External validation, replication** | **Wyoming WOGCC** — per-well monthly Form 2 plus a sundry-notice trail over a stripper population | 🟡 Same construction; the intervention records look document-based rather than tabular, so extraction is likely far more laborious |
| **Methodological precedent to cite** | **Petrobras 3W** — https://github.com/petrobras/3W, **CC BY 4.0**, expert-labelled multivariate well-event time series | ✅ Genuinely open and genuinely labelled. Offshore and flowing, so **not a substitute** — but strong precedent that labelled well-event data can be published, and worth naming |

> [!CAUTION]
> **Two honesty obligations carry forward unchanged.** The CalGEM/WOGCC labels are **regulatory proxies, not mechanical failure labels** — say *"proxy-labelled"* out loud. And they are **monthly**, against a daily-resolution model; `research_findings` §5.1 already flags this as the largest methodological gap in the plan, and it is not closed by anything found here.

### 5.4 Residual unknowns

| Item | Status |
|---|---|
| Volve per-well artificial-lift type; whether any structured intervention log exists in the 5 TB release | **NOT VERIFIED** |
| CalGEM bulk file formats — some historical production archives ship as SQL Server `.BAK`, an ingestion cost to budget | **NOT VERIFIED** |
| Whether WOGCC sundry notices are bulk-downloadable in structured form, or per-document only | **NOT VERIFIED** — the main practical risk versus CalGEM |
| Whether artificial-lift type is machine-readable anywhere in public CalGEM data | **NOT VERIFIED** |

---

## 6. Net change to the backlog

| ID | Change | Verdict | Files | Effort |
|---|---|---|---|---|
| **R-12** | Intervention-risk term in `EVI`, **gated to zero below n = 5**; keep the rig-day denominator; state the `P_success` vs `P_complication` distinction | ✅ Adopt | `04` `TC-009`/`TC-010`, `02`, `03`, `08` | 0.5 d |
| **R-13** | ~~`well_health_index` colour scale~~ → **keep the map on `trigger_state`.** Report Production Efficiency against the well's **own fitted decline curve** (`TC-001`), not a nodal potential | 🟡 **Downgraded** | `06` only | 0.25 d |
| **R-14** | ~~Automated barrier gate~~ → **`BARRIER STATUS: NOT VERIFIED` printed as a declared pre-condition** on every draft plan | ✅ Adopt, reshaped | `04` `TC-013`, `06`, `08` | 0.25 d |
| **R-15** | Tier 0/1/2 data ladder | ✅ Adopt | `02` §12, `05`, `demo_flow`, pitch | 0.5 d |
| **R-16** | Record the rejected KPI table, generator, dynacard dependency and four false dataset claims | ✅ **Done** | `research_appendix.md` §3.1 | — |
| **R-17** | ~~Streamlit Tier-3b fallback~~ | ⛔ **REJECTED — deleted from the plan.** The agent is deployed in Gemini Enterprise; there is nowhere for a second UI to sit. **Tier 3 is the floor** | `build.md` Stage B.1 | **0 — branch removed** |
| **R-18** | Record that **no open labelled rod-pump dataset exists** — as a *finding* supporting the white space | ✅ **Done** | `research_appendix.md` §3.2 | — |
| **R-19** | **The gas-lift failure taxonomy** — the single most valuable thing in either document, and it **closes `D-16`** | ✅ **Done** | `03` §6.2 `SD-028`…`SD-032`, `00` §5.3 scope block | 0.5 d |
| **R-20** | **EPINET named, and the false half stripped** | ✅ **Done** | `02` §12.1, `data_pipeline.md` §6.1, `research_appendix.md` §3.1 | — |
| **R-21** | **The depth claim, refuted and replaced** — closes `D-17` | ✅ **Done** | `03` §2.2 `SD-013b`…`SD-013d`, `02` `DC-007b` | — |
| **R-22** | **The sour-service premise, refuted** | ✅ **Done** | `research_appendix.md` §3.1 | — |

**Net effect of the sceptical pass: two recommendations weakened, one strengthened, and about a day of build effort removed.** These are additive to the eleven refinements and to `D-15`/`D-16`. **Nothing already agreed is invalidated.**

---

## 7. `R-19` — the gas-lift taxonomy, which is what the exercise was actually worth

> **BLUF: of everything in the two documents, one thing was genuinely load-bearing — the recognition that a gas-lifted well fails on completely different components from a rod-pumped one. It closed `D-16`, which we had raised but not solved.**

The document that prompted it was wrong about most things. **It was right about this, and it is the reason the exercise paid for itself.**

### 7.1 What survived, and the honesty constraint that shaped it

**There is no published share-of-failures distribution for gas-lifted wells.** Five independent searches found none. So the *modes* are grounded in physics and named in the literature; the *shares* are ours, and every one is labelled as assigned.

**The design decision that came out of it — `SD-029`:** four modes (valve erosion, bellows leak, multipointing, check-valve failure) are **mutually confusable on daily data.** Rather than pretend to discriminate them, they collapse into one superclass, `GL_INJ_ANOMALY`, and the agent says that separating them needs an acoustic or slickline survey.

> **Claiming daily-data discrimination between a bellows leak and valve erosion would not survive one question from a production engineer.** Collapsing them is the stronger answer, and it is the same principled-refusal move the rest of the system makes.

### 7.2 What is actually diagnosable from daily production data alone

| Verdict | Modes | Why |
|---|---|---|
| 🟢 **Reliably yes (4)** | Compressor/supply failure · casing heading · liquid loading · wax-or-scale *pattern* | Each has a distinct daily-resolution signature |
| 🟡 **Partly (4)** | Valve erosion · bellows leak · multipointing · tubing leak | All disturb CHP and gas rate; **mutually confusable** → `GL_INJ_ANOMALY` |
| 🔴 **No (2)** | **Valve chatter** — seconds-to-minutes, washed out by daily averaging · **sand fill** — indistinguishable from generic productivity loss | **Excluded from the generator.** Generating a label no model could learn is worse than omitting it |

### 7.3 The finding with the most operational value

> [!IMPORTANT]
> **Compressor and injection-supply failure is a FIELD event masquerading as many WELL events.**
>
> CHP collapses across every gas-lift well on the GGS **simultaneously**, oil declines together, everything recovers on restart. **It is trivially detectable and completely unambiguous — and a naive per-well trigger reports it as fourteen well failures.**
>
> **This is the first filter the agent applies** (`SD-031`, `AS-021`). It is now generated deliberately as `SD-033d` — **a trap laid for our own ranking engine**, with mandatory test coverage. Being the system that says *"this is your compressor, not your wells"* is worth more in the room than any ranking.

---

## 8. Disposition of the source documents

**Both `workover_problem.md` and `workover_demo_blueprint.md` were deleted on 2026-09-23, after extraction, at the user's instruction.**

| | |
|---|---|
| **Why** | Their citation-marker density made them **quotable-looking and unverifiable**. `workover_problem.md` carried **25 markers `[1]`–`[55]` and no bibliography — not one resolves.** Leaving them in a folder used to build an ED-facing demo was the risk |
| **Archived to** | `~/.gemini/jetski/brain/50a2b34f-c03e-490a-9018-f823d7f93836/scratch/deleted_source_docs/` (15,406 and 20,302 bytes) |
| **What was kept** | `R-12`, `R-14`, `R-15`, `R-19`…`R-22` above |
| **What was rejected, and recorded so it cannot return** | `research_appendix.md` §3.1 — the five vendor performance claims, the four false dataset claims, the eight measured generator defects, the sour-service premise, the depth claim, and "Level 4 Autonomous Agent" |

> **This document is now the standing record of what those two files contained.** Nothing of value was lost; everything unverifiable was.

