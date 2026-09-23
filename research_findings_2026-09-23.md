# Are We Solving the Right Problem?

**Three independent research passes · 2026-09-23 · ONGC Assam Asset (Geleki)**
Sources and confidence grades below. This project's evidence standard applies: **vendor performance claims are rejected outright**, an abstract is not the paper, and *"not published"* beats a plausible guess.

---

## 0. The answer, first

> **Yes, it is the right problem — but the pitch as currently framed walks into a room where ONGC has already built two of the three things we are selling, and says so publicly.**

ONGC holds a **copyright registration** for **WellEx**, an in-house AI/ML candidate-well-selection system built under its own **Project Udbhav 1.0**, which flags wells, diagnoses them on physics, picks the treatment, and explicitly claims to *"optimise use of rigs and resources."* It opened **NETRA**, a Production Operation Control Centre, on **18 April 2026**, whose advertised scope includes real-time monitoring, predictive analytics, well and network modelling, optimisation workflows and digital twins.

**Steps 1, 2 and 4 of our seven-step pitch are, in ONGC's own telling, already claimed.**

**So what:** presenting *"we flag, diagnose and pick the job"* as novel will read as not having done the homework on ONGC's own award-winning internal programme. The defensible ground is narrower, better, and nobody appears to occupy it:

> ### *"WellEx tells you which wells. We tell you which rig, which week, and what it costs you to wait."*

Two further findings are severe enough to change the build, not just the pitch:

| | |
|---|---|
| 🔴 **The 100% sucker-rod-pump assumption is contradicted.** Gas lift is documented in Upper Assam. **Pump fillage — our top mechanical feature — is physically undefined on a gas-lifted or flowing well** | [§2.1](#21-artificial-lift-the-assumption-that-breaks-the-top-feature) |
| 🔴 **Geleki is under active water injection**, with documented skewed injection patterns, radioactive tracer tests and water shut-off jobs in producers. Our Chan diagnostic assumes aquifer coning versus channelling and **has no injector-breakthrough branch** | [§2.2](#22-geleki-is-waterflooded--and-that-changes-the-chan-diagnostic) |

---

## 1. Are we aimed at the right problem?

### 1.1 The evidence that we are

| Claim | Source | Confidence |
|---|---|---|
| **ONGC Assam, Apr'25–Jan'26: 875.83 kt actual against a 980.33 kt target — a 10.66% miss, and *below* the prior year's 877.69 kt** | Govt Monthly Review Report on Infrastructure Performance, Jan 2026, via Sentinel Assam | **High** |
| ONGC states, **in its own words**, that manual candidate-well selection was *"time-consuming, subjective, bias-prone, not scalable"*, causing *"suboptimal resource allocation"* | ONGC-authored WellEx paper | **High** |
| **Natural decline of mature fields, with rising water cut, is ONGC's own #1 stated cause** of production shortfall | PIB, investor commentary, Ministry replies to Parliament | **High** |
| Upper Assam mature fields report water cuts **up to 98%** | Academic paper, Upper Assam Basin | Low–Med |
| **CAG precedent:** rig idle time 19–23%, ₹5,117 cr production deferment, and *"no Rig Requirement Plan was prepared for onland assets"* | CAG Performance Audit, *Utilisation of Rigs in ONGC* | High on existence |

> [!CAUTION]
> **Do not quote the CAG rig numbers as current state.** They cover 2010-11 to 2013-14 and concern **drilling** rigs, not workover rigs. Use them as precedent that *the regulator audits rig utilisation* — which is itself a strong argument — not as a live figure.

### 1.2 The evidence that the framing is wrong

**ONGC's tier-1 vocabulary is not ours.** Their stated strategic priorities, in order of prominence: arresting mature-field decline via **EOR/IOR**; **Technical Service Partnerships**; monetising new discoveries; record **drilling**; the **pivot to gas**.

Workover prioritisation sits inside a framework they call **WRFM — Well, Reservoir and Facility Management**, which they list as an FY26 lever. It is a **tier-2, asset-level operational problem, not a board narrative.**

> **"Workover prioritisation" is asset-floor language. An Executive Director hears a maintenance scheduler.**

### 1.3 What ONGC already has — read this before writing another slide

| Programme | What it claims | Status |
|---|---|---|
| **WellEx** ⚠️ | Indigenous AI/ML decision support for **candidate-well selection**. Computes remaining reserves, **skin**, modified heterogeneity index. Prioritises by oil-gain potential, **recommends the treatment** (acidisation, hydro-frac), shortlists flowing *and* non-flowing wells, and claims to *"optimise use of rigs and resources"* | **Copyright-registered**, Registrar of Copyrights, DPIIT. Built under **Udbhav 1.0**. Validated at **Ahmedabad Asset**; under consideration for **B&S and Mumbai High**. **Assam is not named** |
| **NETRA** ⚠️ | Production Operation Control Centre: real-time monitoring, **predictive analytics**, well and network modelling, **optimisation workflows**, **digital twin** | Inaugurated **18 Apr 2026**, IPEOT Panvel, by Director (Production). Under the *"Bytes to Barrel"* vision. **Whether it covers onshore Assam is unresolved** |
| **ONGC × Microsoft** | Unified data foundation on Azure / Fabric / Power BI; explicitly about moving *"from isolated AI experiments to production-ready AI agents"* | Ongoing |
| **Gas-lift AI tender** | ONGC is **tendering for autonomous gas-lift control with AI/ML written into the specification**, including a predictive-maintenance module for early warning on valve response and pressure trends | Live procurement |
| **Project Udbhav** | Internal bottom-up AI/ML programme; engineers submit problems, winners funded to field-ready | Ongoing |

> [!WARNING]
> **Three names currently in our materials should be deleted immediately.**
>
> | Name | Reality |
> |---|---|
> | *"Project Dhruv"* | No evidence found in a production-operations context |
> | *"ICE Cube"* | **Project ICE exists but is the SAP ERP backbone.** Searching "ICE Cube" returns ice machines and a neutrino observatory |
> | *"Project Lakshya"* | Appears to be a **manpower-contracting vendor** for Ahmedabad/Ankleshwar assets, not an ONGC strategy |
>
> The correct names: **Udbhav · WellEx · NETRA · Bytes to Barrel · WRFM · RTOC · Project ICE (ERP) · GATI · DOT**.

### 1.4 Where the white space actually is

| Capability | WellEx | NETRA | Vendors | Us |
|---|---|---|---|---|
| Flag underperforming wells | ✅ claimed | ✅ claimed | ✅ | — |
| Diagnose on physics | ✅ claimed (skin, heterogeneity) | — | ✅ | — |
| Recommend the treatment | ✅ claimed (stimulation only) | — | 🟡 Baker Hughes claims ranking | — |
| **Predict *when* it will fail** | ❌ ranks by oil-gain potential — a static question | 🟡 "predictive analytics", unspecified | ✅ but on dynacard telemetry | ✅ |
| **Schedule under a hard rig-day constraint** | ❌ claims rig optimisation as an *outcome*, not a function | ❌ | ❌ | ✅ |
| **Refuse to recommend a job** | ❌ | ❌ | ❌ | ✅ |
| **Work on daily production data with no telemetry** | — | — | ❌ all assume streaming dynacards | ✅ |

**No published ONGC or India-upstream work on survival / time-to-failure modelling for wells was found.** That appears to be genuine white space, and it is the piece that converts a ranked list into a **calendar**.

---

## 2. Domain assumptions that are wrong

> [!NOTE]
> **Evidence caveat, stated honestly.** The domain researcher had search-summary access only and could not open a single primary SPE PDF, ONGC annual report or tender document. Findings below are graded accordingly. **The "stop claiming X" findings are safe to act on immediately; the "claim Y instead" findings need a primary source before they go on a slide.**

### 2.1 Artificial lift — the assumption that breaks the top feature

**`SD-015` sets 100% SRP. That is contradicted.**

- **SPE-194798-MS** (*Gas Lift Optimization of a Mature Field of Upper Assam Basin*, Maut et al., **Oil India Ltd**, 2019) documents a **23-well intermittent gas-lift campaign** in Upper Assam with acoustic and downhole P/T surveys.
- Geleki is served by **Gas Gathering Stations and gas compressor plants**.
- ONGC tenders for Assam Asset are titled *"Surface Installations **and Artificial Lift** Upkeep Services"* — plural lift types.
- **No public source gives a Geleki SRP / gas-lift / flowing split. None.**

**Why this is severe:** `MS-011`, the pump fillage proxy, is the dominant mechanical feature in the model. It is **physically undefined** on a gas-lifted or naturally flowing well. We are silently claiming a feature applies to 100% of a stock where it may apply to a fraction.

**Recommended change:** replace "100% SRP" with an explicit, **labelled-as-assumed** lift mix; **gate the fillage proxy to the SRP subset**; report model performance on that subset, not on all 142. Ask ONGC for the real split as a named input. Do not invent a percentage.

### 2.2 Geleki is waterflooded — and that changes the Chan diagnostic

**Confirmed:** water injection for pressure maintenance, explicitly in **TS-2**. Pressure maintenance described as *"challenging"*, with **skewed injection patterns**. ONGC ran **radioactive inter-well tracer tests** at Geleki and responded with **injection profile modification** and **water shut-off jobs in producers**. Injected-water/clay interaction (smectite, kaolinite, illite) is a documented complication.

**Why this matters:** our Chan implementation distinguishes **aquifer coning** from **channelling**. In a waterflood, the dominant channelling mechanism is **injector breakthrough** — which is a *different problem with a different fix*. Profile modification at the injector may beat a cement squeeze at the producer, and it is cheaper.

**This is an opportunity, not just a defect.** Injector–producer pairing is a feature we can add, it uses data ONGC already has, and *"which producer is drowning, and which injector is drowning it"* is a question an Assam engineer will immediately recognise.

### 2.3 The failure taxonomy has two shares that are badly wrong

| Code | Ours | Published bands | Verdict |
|---|---|---|---|
| Rod parting | 30% | Rods 30–40% | ✅ Defensible, at the low end |
| Pump wear | 20% | Pump 20–30% | ✅ Defensible, at the low end |
| **Tubing leak** | **7%** | **Tubing 30–45%** — often the largest single bucket | 🔴 **Off by 4–5×** |
| **Scale / sand** | **3%** | Tipam sands at **Geleki and Lakwa specifically** are poorly-consolidated to unconsolidated braided-channel sandstones; sand production causes tubular abrasion, pump failure, valve obstruction and **increased workover frequency** — and is **exacerbated by water breakthrough**, which §2.2 confirms is happening | 🔴 **Too low, and sand control is missing entirely as a job category** |

> [!IMPORTANT]
> **The tubing-leak gap may be partly a taxonomy question we have not declared.** Rod-on-tubing attrition is the dominant tubing failure mechanism. If we classify that under "rod parting", we double-count the cause and starve the tubing bucket. **We must state whether we classify by primary *cause* or by final failure *event*** — that choice alone moves the Pareto, and it is exactly the first question a production engineer will ask.

**Also:** Upper Assam crude is reported at **wax 11–25 wt%** with a **pour point around 30 °C**, against winter ambient below 10 °C — the crude is routinely below its pour point at surface. **15% for wax is more likely a floor than a ceiling.**

### 2.4 Smaller corrections

| Item | Correction |
|---|---|
| *"On production since 1968"* | **Discovered 1968; commercial production ~1974.** Exactly the date an Asset veteran corrects out loud |
| Geleki well count, production rate, water cut | **Do not put any of these on a slide.** The "74 wells / 1,600 t/d" figure traces to a SlideShare deck; "200+ wells" traces to contractor marketing. Both fail our evidence standard |
| Acoustic fluid level, dynamometer cards | ONGC **has** institutional dynamometer capability (IOGPT, Western onshore) and acoustic surveys are used in Upper Assam — **but there is no evidence either is routinely acquired per-well at Geleki.** Frame as *required inputs* or *recommended instrumentation*, not as assumed-existing data. **A gap we help close is a stronger story than data we assumed** |
| `N_WELLS = 142` | Present explicitly as an **illustrative synthetic subset**, not as the Geleki well count |

---

## 3. The KPI is wrong for the audience

**No published use of *"deferred barrels avoided per rig-day"* as a managed KPI was found anywhere** — not in SPE literature, not in operator reporting. It is a constructed composite.

**It is a good objective function and a bad headline.** It fuses three things an ED will unpack separately: a counterfactual that requires a baseline nobody agrees on, an efficiency normaliser, and an implied constraint.

**What the industry actually manages to:**

| KPI | Status |
|---|---|
| **Failures per well per year** | The classic rod-lift asset-management metric. ALEOC in the Permian formed specifically to share failure/run-life data |
| **Mean run-life / MTBF** | Same |
| **Incremental oil per job**, **payout in days** | Approval-committee language |
| **Production Efficiency** — actual ÷ maximum economic potential | **Formally standardised**, computed via a 4-stage production choke model, collected through the UKCS Stewardship Survey; methodology developed **with SPE** |

### Recommended scorecard

```
1.  Failures per well per year          ↓     their language, their baseline
2.  Mean run-life / MTBF                ↑     their language
3.  Incremental oil per job, payout days      their approval language

    "…and because rig-days are the binding constraint, we optimise
     deferred-barrels-avoided per rig-day underneath."
```

The metric then reads as **evidence of sophistication rather than an unfamiliar ask.**

---

## 4. Our four claimed differentiators, graded

| Claimed | Verdict | Why |
|---|---|---|
| **(a) Selects the specific job, not just a risk score** | ❌ **Not novel** | **SPE-181072-MS** (2016, Zangl et al., **OMV Petrom Romania**) already builds a Bayesian Belief Network that detects integrity and deliverability problems, estimates risk and cost, selects the intervention and computes NPV per candidate. **Ten-year-old published prior art.** Do not lead with this |
| **(b) Drafts an approvable plan with materials and logistics** | 🟡 **Narrow, genuine, degrading** | **SPE-229606-MS** (ADIPEC, Nov 2025) covers LLM multi-agent whole-lifecycle downhole maintenance planning. Baker Hughes ships a GenAI assistant. **The materials-and-logistics specificity is still unclaimed by anyone** — narrow the claim to exactly that |
| **(c) Separates the rigless queue** | ❌ **TABLE STAKES** | Rig-versus-rigless triage is routine intervention planning. **Presenting it as an innovation to an ED who has run a workover programme will cost credibility.** Drop it from the pitch; keep it in the product |
| **(d) Refuses to recommend a job when offsets show reservoir decline** | ✅ **GENUINE — the headline** | The literature and every vendor optimise for **detection**; none claim principled **abstention**. Distinguishing mechanical failure from reservoir decline is precisely the failure mode that burns workover budgets. **But it must be *demonstrated* with a worked refusal, or it is an assertion** — which is why `GK-141` and `AT-127` exist |

### The differentiator we are not claiming, and should be

> **Every commercial product in this space — Weatherford ForeSite, Ambyint, SLB Lift IQ, Baker Hughes Leucipa — assumes high-frequency telemetry: POCs, VSDs, streaming dynamometer cards.**
>
> **Mature ONGC onshore rod pumps on daily production data is a regime most of them are not instrumented for.** Working from daily production alone, with no dynacard, is a harder problem and a real gap versus both the literature and the vendor stack. **We currently do not say this.**

---

## 5. Two problems with the validation plan

### 5.1 CalGEM is monthly. The model is daily.

**This is the largest methodological gap found, and it is bigger than the synthetic-data question.**

A C-index computed on monthly aggregates validates a different model at roughly 30× coarser event resolution. It will not transfer to a daily-resolution ONGC deployment.

**Two honest options:** reframe the validation explicitly as monthly-resolution and say so plainly, or find a daily source — which, on public data, probably does not exist.

**Also worth evaluating before locking CalGEM:**

| Source | Why |
|---|---|
| **Wyoming WOGCC** ⭐ | **Per-well monthly Form 2 *plus* an accessible sundry-notice trail** — the intervention-event source most explicitly available anywhere, over a heavily stripper-well population. **Strongest dark horse** |
| **Alberta Petrinex** | Well-level monthly volumetrics, **free self-service bulk CSV** — easier to obtain than CalGEM, weaker on intervention events |
| Kansas KCC | ❌ **Rule out** — lease-level, same defect as Texas |

**Texas RRC remains correctly ruled out.** Any "well-level" Texas figure from a commercial vendor is modelled and allocated, not measured.

### 5.2 There is no clean public rod-pump failure label

Every option yields, at best, a **downtime-onset or sundry-notice proxy**. **Say "proxy-labelled" in the pitch.** If an ED discovers the label was inferred and we did not say so, everything else goes with it.

### 5.3 Re-baseline the C-index

`00_overview` §5.5 states **0.65–0.80**. **Recommend 0.65–0.72.**

**No published C-index for rod-pump time-to-failure on daily production data was found.** The nearest comparable is **SPE-165374** (2013, ~2,000 rod pumps, 5 assets): **precision and recall just above 65%, using richer data than we will have**. Claiming the top of a 0.80 band on daily-only data invites exactly the challenge we do not want.

**Better: quote 0.65–0.72, state that no published baseline exists for this data regime, and say we are setting one.** That reads as rigour. Commit to reporting **Brier score and calibration** alongside, because C-index alone is weak under heavy censoring — and workover data is heavily censored.

### 5.4 Cite the prior art ourselves

**SPE-181072-MS** and **SPE-229606-MS** should appear in our own deck. Positioning as building on named prior art is far stronger than being told about it in Q&A.

---

## 6. What I recommend, in order

| # | Change | Type | Effort |
|---|---|---|---|
| **1** | **Reposition as the rig-day allocator.** *"WellEx tells you which wells. We tell you which rig, which week, and what it costs you to wait."* Name Udbhav, WellEx and NETRA approvingly on slide 2 | Pitch | 1 day |
| **2** | **Promote failure timing to the headline**, alongside principled refusal. No published ONGC survival-analysis work exists. This is the genuine white space | Pitch | 0 |
| **3** | **Re-label in ONGC's vocabulary: WRFM execution, decline arrest.** *"An agentic WRFM execution layer for Assam Asset that converts each rig-day into decline-arrest barrels"* | Pitch | 0 |
| **4** | **Re-order the KPI stack** — failures/well/year and run-life first, deferred-barrels-per-rig-day as the stated internal objective | Pitch + `06` | 0.5 day |
| **5** | **Drop the 100% SRP assumption.** Labelled assumed mix; gate the fillage proxy to the SRP subset | `03`, `05`, `02` | 1 day |
| **6** | **Fix the taxonomy** — tubing leak up, sand split out and raised, **add sand control as a job category**, declare cause-vs-event classification | `00`, `03`, `decision_architecture` | 1 day |
| **7** | **Add the injector-breakthrough branch to the Chan diagnostic** and an injector–producer pairing feature | `04 TC-002`, `05`, `03` | 1.5 days |
| **8** | **Re-baseline C-index to 0.65–0.72**; fix the CalGEM monthly/daily mismatch; evaluate WOGCC | `00`, `05` | 0.5 day + 1 day eval |
| **9** | **Drop differentiator (c)** from the pitch; **re-frame (a)** as *"from daily production data alone, with no dynacard telemetry"*; cite SPE-181072 and SPE-229606 | Pitch | 0 |
| **10** | **Delete "Project Dhruv", "ICE Cube", "Project Lakshya"** from every artefact | All | 10 min |
| **11** | Correct *"on production since 1968"* → discovered 1968, produced ~1974. Remove all unsourced Geleki figures | `00`, `demo_flow` | 10 min |

---

## 7. The two questions to resolve before the room

> [!IMPORTANT]
> **These cannot be answered from open sources and both change the positioning.**

| Question | Why it decides things |
|---|---|
| **Does NETRA cover onshore Assam, and is WellEx scheduled for Assam Asset?** | The difference between being a **complement** and a **duplicate**. If either is already landing in Assam, recommendations 1 and 2 are mandatory, not optional. **Ask this directly in the meeting if it cannot be answered beforehand** |
| **Who actually approves a workover in an onshore Asset today, on what cadence, with what inputs?** | Our claim to be improving something real currently rests on **one self-critical line** in an ONGC paper. **One 20-minute call with anyone in Assam Asset production beats everything three research passes found in open sources** |

---

## 8. What could not be verified

Recorded because an unverified item is not a small item. **None of these may appear on a slide.**

**Does not appear to exist:**
- Any **C-index for rod-pump time-to-failure on daily production data**. This is a finding, not a search failure — and it is why we can claim the white space.
- Any published use of **"deferred barrels avoided per rig-day"** as a managed KPI.
- Any **academic rod-pump failure benchmark dataset**. Petrobras 3W is the nearest analogue and is offshore, naturally-flowing — wrong lift physics.
- Any **ONGC survival-analysis or time-to-failure publication**.

**Not published anywhere findable:**
- Any **Geleki-specific artificial-lift mix**, well count, production rate, water cut or decline rate.
- Any **Assam or ONGC-specific failure-mode distribution**. Our entire taxonomy is benchmarked against non-Indian generic industry bands.
- Any **rig-versus-rigless activity split** for a mature onshore rod-pumped asset, anywhere. **The 27% figure is currently unsupported** and must be derived bottom-up from our own catalogue under `TC-008.6`, with the arithmetic shown — or labelled an explicit modelling assumption.
- Any **count of ONGC idle or shut-in wells**, or any **workover backlog** figure.
- **ONGC's own formal definitions** of work-over rig versus pulling unit versus rig-less.
- Any **CAG audit specifically on workovers** — the rig audit is about drilling.

**Unresolved and material:**
- Whether **NETRA covers onshore**. It sits at IPEOT Panvel under Director (Production), which *suggests* offshore-first — **that is a guess, labelled as one**.
- Whether **WellEx does rig-versus-rigless classification or scheduling**. Descriptions cite rig optimisation as an *outcome*. **This is our likely wedge, but it is absence of evidence, not evidence of absence.**
- Whether **CalGEM WellSTAR exposes intervention events in structured bulk form** rather than per-API lookup. **This determines whether the dataset is usable at all** and needs hands-on checking.

**Rejected as evidence:**
- Every vendor performance claim encountered — Ambyint's 38% failure reduction, and all Weatherford, SLB and Baker Hughes capability claims. Marketing, not proof.
- The "74 wells / 1,600 t/d" Geleki figure (SlideShare) and the "200+ wells" figure (contractor marketing).
- An MDPI 2024 paper reporting **98.61% accuracy** on 1,354 wells. That number is a leakage or class-imbalance red flag and must not be cited as a benchmark.

**Tooling limitation, stated plainly:** none of the three researchers could open a primary PDF. All SPE material is abstract- or summary-level. **Per our own standard, SPE-194798-MS, SPE-181072-MS, SPE-165374 and SPE-229606-MS are not yet verified** — paper identity and headline numbers were corroborated across independent secondary sources, but the papers were not read.
