# Research Appendix
## Supporting material for `Problem Statement.md` v3.0

**Purpose:** Everything cut from the problem statement to keep it clean — derivations, corrections to the public record, explicitly rejected claims, known data gaps, and outstanding research items.

> [!IMPORTANT]
> **Read §2 and §3 before quoting any well-count or utilisation figure to a customer.** Several widely-circulated ONGC figures are wrong by an order of magnitude and appear in third-party decks.

---

## 1. Derivation of the well population

ONGC does not publish a consolidated producing-well count anywhere. Segment reporting goes only to Onshore vs Offshore. The estimates in §3.1 of the problem statement are derived as follows.

### 1.1 The one hard ONGC well census in the public domain

**Tamil Nadu, March 2018** — ONGC-supplied figures, disclosed under pressure during the Cauvery Delta land protests:

| Category | Count | Share |
|---|---|---|
| **Total wells drilled in Tamil Nadu** | **712** | 100% |
| Dry and abandoned | 380 | 53.4% |
| Oil/gas bearing, connected to production installations | 304 | 42.7% |
| — of which **presently flowing / operational** | **181** | 25.4% of total |
| — of which **connected but NOT flowing** | **123** | 17.3% of total |
| Utility wells | 28 | 3.9% |

*The arithmetic closes exactly: 380 + 304 + 28 = 712. Garbled or fabricated figures rarely reconcile. This reads as a genuine ONGC dataset.*

> **Key ratio: 181 / 304 = 59.5% of completed, hooked-up wells were flowing. 40.5% were connected but NOT flowing.**

**Caveat:** Cauvery is atypical — a 53.4% dry-hole rate reflects a geologically difficult basin, and Gujarat and Assam perform materially better. **Treat 40.5% non-flowing-of-connected as an upper bound, not a point estimate.**

### 1.2 The arithmetic

```
(A) Onshore flowing oil producers        = 4,000 – 5,500
    [from ONGC onshore crude ≈110–120 kbopd ÷ 20–30 bopd/well,
     using Mehsana and Ahmedabad per-well rates]

(B) Flowing ÷ connected ratio            = 59.5%   [Tamil Nadu 2018]
(C) Flowing ÷ ever-drilled ratio         = 25.4%   [Tamil Nadu 2018]

Step 1  Connected onshore wells   = 4,000/0.595 to 5,500/0.595  →  ~6,700 – 9,200
Step 2  NON-FLOWING onshore       = 6,700−4,000 to 9,200−5,500  →  ~2,700 – 3,700
Step 3  Onshore drilled all-time  = 4,000/0.254 to 5,500/0.254  →  ~15,700 – 21,700
Step 4  + offshore drilled (~2,000–3,000)                       →  ~18,000 – 25,000

Cross-check: DGH NDR holds ~24,000 wells, all India, all operators, since 1889.
             ONGC ≈ 70–75% of India's drilling history → 0.72 × 24,000 ≈ 17,300.
             Two independent routes converge. Centre on ~20,000.
```

| Quantity | Estimate | Confidence |
|---|---|---|
| ONGC **cumulative wells drilled**, all-time | **~18,000–25,000** (centre ~20,000) | **Strongest** — two independent routes converge |
| ONGC **producing** oil + gas wells | ~5,000–7,500 | Moderate |
| ONGC **non-flowing connected** wells, onshore | ~2,700–3,700 (treat 3,700 as a soft ceiling; true figure likely 2,000–3,000) | **Most fragile** — generalises one atypical asset |

### 1.3 Sanity check on the workover job count

ONGC operates ~230 drilling + workover rigs combined. If the Assam ratio (16 drilling : 15 workover) holds company-wide, that implies **~110 workover rigs**.

```
2,200 jobs ÷ 110 rigs ≈ 20 jobs per rig per year
                      ≈ 18 days per job including moves
```

A plausible onshore figure. **The 2,200 number survives the check.**

### 1.4 Value of recovered production *(derived; assumptions stated)*

| Incremental production | Annual avoided import value (@ $70/bbl, ₹88/USD) |
|---|---|
| **1,000 bopd** | **~$25.6 mn ≈ ₹225 crore** |
| 10,000 bopd | ~$256 mn ≈ ₹2,250 crore |
| 1 MMT/yr (~20,000 bopd) | ~$513 mn ≈ ₹4,500 crore |

On an **incremental** barrel from *existing* infrastructure — the correct case for workovers, where facilities and overhead are sunk — marginal contribution to ONGC is estimated at **~$45/bbl**, i.e. **~₹145 crore/yr per 1,000 bopd**, plus ~₹75 crore/yr to the exchequer via royalty and cess.

> [!WARNING]
> The $45/bbl is **derived, not disclosed**: realisation $78.67/bbl (FY25) less ~10% effective royalty, less 20% OID cess, less ~$10/bbl marginal lifting cost. ONGC does not publish opex/bbl or levies/bbl. The $10/bbl lifting cost is a sector rule of thumb. OID cess exemptions apply to parts of the portfolio.

---

## 2. Corrections to the public record

### 2.1 "53,967 producing wells" is false

> [!CAUTION]
> **This figure circulates in online summaries and slide decks. It is wrong by roughly an order of magnitude. Do not use it.**

Three independent refutations:

1. **Per-well productivity.** ONGC standalone crude FY2024-25 was 18.558 MMT ≈ **373,000 bopd**. Across 53,967 wells that is **~6.9 bopd/well** — incoherent for a company taking ~70% of its oil from offshore platforms producing 150–250 bopd per well.
2. **National denominator.** DGH's National Data Repository holds data for approximately **24,000 wells for all of India, all operators, since 1889**. One operator cannot hold twice every well the country has ever logged.
3. **ONGC's own drilling history.** ONGC has plausibly drilled **~18,000–25,000 wells in total since 1956** (§1.2). 53,967 exceeds ONGC's entire 70-year drilling history by 2–3×.

### 2.2 "19–23% idle" is RIG time, not well idleness

> [!WARNING]
> The widely-quoted **19–23% figure from the CAG rig audit is rig non-productive time** — the share of *rig-days* spent not drilling. It is frequently paraphrased in a way that invites reading it as "19–23% of ONGC's wells are idle." **Those are entirely different denominators.**
>
> The audit also does **not disaggregate workover-rig utilisation from drilling-rig utilisation**, so the figure must not be attributed to workover rigs specifically.

### 2.3 The rig audit is CAG Report No. 42 of 2015 — not No. 39

Much secondary coverage mis-cites this. **No. 42 of 2015** is correct.

### 2.4 Production series before FY2016 is not comparable

CAG's crude over-reporting audit (FY2011-12 to FY2014-15) found **~12% over-reporting** via condensate, off-gas and BS&W treatment, carrying a >₹18,000 crore subsidy burden. **Do not build a trend line across the FY2016 boundary.**

Similarly, the FY21–FY23 ONGC production series is contaminated by inconsistent reporting basis (standalone vs standalone+JV vs Group). **Only the FY24/FY25 pair is safely comparable:**

| | FY2023-24 | FY2024-25 |
|---|---|---|
| Crude (standalone) | 18.401 MMT | **18.558 MMT** (+0.9%) |
| Gas (standalone) | 19.978 BCM | **19.654 BCM** (−1.6%) |

### 2.5 Import dependency — do not re-derive it

PPAC computes import dependency on a **net consumption basis**. Re-deriving it from production and import volumes yields ~89.8% and will cost credibility. **Quote PPAC's published figure.**

---

## 3. Explicitly rejected claims — do not use

| Claim | Why rejected |
|---|---|
| **"ONGC has 53,967 producing wells"** | Refuted three ways (§2.1). Wrong by an order of magnitude |
| **"19–23% of ONGC's wells are idle"** | Misreading. It is **rig** non-productive time from CAG 42/2015 — a different denominator, and not disaggregated to workover rigs |
| **"ONGC performs 63 workover jobs/year"** | Mis-read sub-category from a third-party document. **Actual: ~2,110–2,320/year.** Formally retracted |
| **"CAG Report No. 39 of 2015"** for the rig audit | Wrong report number. It is **No. 42 of 2015** |
| **"ONGC total wells: 7,839 (5,987 onshore / 1,852 offshore)"** | Untraceable; components attributable to unrelated filings. Plausible magnitude makes it *more* dangerous, not less |
| **Mumbai High "665 oil / 90 gas / 1,300 injectors"** as a current figure | Undatable, probably pre-2014. See §4 |
| **Artificial lift split "gas lift 50.8% / SRP 47.0% / PCP 1.2% / ESP 0.7%"** | Single undated SlideShare source, no corroboration in any SPE paper or filing, implausible for an onshore-weighted population. **Drop entirely** |
| **ESP MTBF bands (<90 days / 365–550 / >1,000)** | Vendor marketing, not operator or peer-reviewed data |
| **"ML reduces unplanned downtime by 30%"** and similar | Vendor-sourced. **No credible published figure exists** for deferred-production reduction from ML well-failure prediction |
| **"24% of UKCS production is lost to well problems"** | **73% of UKCS losses are plant and facilities, not wells.** Dangerous — a technically literate client will catch it |

### 3.1 From `workover_problem.md` and `workover_demo_blueprint.md` — added 2026-09-23

Full analysis in [blueprint_assessment.md](./blueprint_assessment.md). These are recorded here because both documents are in the project folder and the numbers are quotable-looking.

| Claim | Why rejected |
|---|---|
| **"60–75% unplanned downtime reduction"**, **"15–25% deferred oil recovery"**, **"30–40% artificial lift run-life extension"**, **"20–30% rig NPT reduction"**, **"near-zero high-risk incidents"** | `workover_problem.md` carries **25 citation markers, `[1]`–`[55]`, and no bibliography. Not one resolves.** Vendor-brochure performance class, already rejected above. **The highest-risk content in the folder** |
| **"CNN dynacard classification with >95% accuracy"** | Unsourced, and there is no open labelled dynacard data on which any such figure could be independently checked — see below |
| **"SPE Sucker Rod Pump Dynacard Datasets — open benchmark datasets, 30+ labelled diagnostic states"** | **No such dataset exists.** SPE operates no public dynacard repository. The "30 working conditions" taxonomy comes from papers trained on **proprietary** operator data |
| **"Equinor Volve — 24 wells, 10 years"** as a validation set | Volve is real and genuinely open, but it is **7 wellbores**, offshore North Sea, 2008–2016, **gas lift / natural flow with no sucker rod pumps**, and carries no verified structured intervention log. **Wrong physics for rod-pump failure** |
| **"Utah FORGE & Kansas KGS IIoT feeds"** | Utah FORGE is a **DOE geothermal** EGS laboratory — no hydrocarbons, no artificial lift. **KGS publishes regulatory records only**, with production reported **per lease, not per well** |
| **The blueprint's synthetic generator output** | Eight measured defects on execution. The fatal one: **it contains no production decline at all** (7 of 15 healthy wells trend *upward*), so mechanical fault versus depletion cannot be posed. Also `corr(EVI, ΔQ) = 0.9997`, 18 of 20 wells ranked in a queue that says DEFER, an ESP well diagnosed with gas-lift valve erosion, BHP understated ~3.9× and uncorrelated with rate, and identical water-cut slope on every well |
| **"Level 4 Autonomous Agent"** | Invites *"who signs off?"* Our human-in-the-loop draft-plan model is both accurate and the stronger answer |
| **⛔ "Upper Assam crude is sour — H₂S / CO₂ drive tubular corrosion"** | **REFUTED.** Five searches found **no H₂S figure and no CO₂ figure for Upper Assam crude or associated gas, from any source.** What *is* supported is the opposite: Upper Assam crude is **sweet and low-sulphur (<0.5%)**, and its defining problem is **wax — 11–25 wt% with a pour point of 25–33 °C**. **This one mattered.** A sour-service premise would have put corrosion-inhibition and CRA tubing in the job catalogue and demoted wax, which is the actual dominant flow-assurance risk in the basin. *(No primary ONGC/DGH/PPAC/IOCL assay was located; the sulphur figure is qualitative.)* |
| **⛔ "Geleki producers are completed at 3,000–4,200 m"** | **REFUTED.** Verified: **Geleki TS-5A sand 2,700–3,100 m** (apgindia.org); **field-wide drilling range 2,400–4,000 m** (pcbassam.org). Tipam producers therefore sit at **≈ 2,400–3,100 m** — the claim was **300–1,100 m too deep.** It would have pushed every synthetic pump setting below any real Geleki pump and forced `SD-014` onto the small-plunger branch field-wide. Corrected by `SD-013b`…`SD-013d` |
| **🟡 "EPINET is an OSDU-style Oracle repository holding workover history and PVT"** | **PARTLY REFUTED — and the true part is valuable.** EPINET is **real and verified**: ONGC's E&P repository, initiated 1999, Schlumberger **Finder / ProSource**, 18 centres (**SPE-99336-MS**, abstract only). But **"Oracle" has no source**, **"OSDU-style" is refuted** — EPINET predates OSDU by two decades — and it is **NOT VERIFIED** that it holds workover history, static reservoir pressures or PVT. **Its 2026 operational status is unconfirmed.** Name EPINET; **ask** what it contains |
| **⛔ Any published share-of-failures distribution for gas-lifted wells** | **Does not appear to exist in the public literature.** Every gas-lift share in `SD-028` §6.2 is therefore **assigned by us and labelled as assigned.** Recorded so that no one later mistakes our own table for a citation |

### 3.2 A rejection that is evidence *for* us

> [!IMPORTANT]
> **No open, labelled sucker-rod-pump failure or dynamometer dataset exists anywhere. This was verified, and it is a finding rather than a search failure.**
>
> | Corpus | Size | Status |
> |---|---|---|
> | Mossoró, RN, Brazil — *Sensors* 21(13):4546 (2021) | >50,000 cards, 38 SRP wells, 8 operating modes + 2 sensor faults | **"Available on request from the corresponding author." Not open** |
> | Bahrain beam-pump field data | ~5.38 M cards, 297 pumps, **35,292 expert-labelled into 12 classes** | Described in the literature, **never released** |
> | Petrobras **3W** — github.com/petrobras/3W, **CC BY 4.0** | Expert-labelled multivariate well-event time series | ✅ **Genuinely open** — but offshore and flowing, so **precedent, not a substitute** |
>
> **Every labelled rod-pump corpus of meaningful size is held privately by the operator that generated it. That is precisely why the white space exists** — and it is a far better answer to *"has this been done before?"* than silence.

---

## 4. Mumbai High — why the circulating well figures are stale

The widely-repeated **665 oil wells / 90 gas wells / >1,300 water injectors** figure set traces only to Scribd and SlideShare, and could not be dated against ONGC, bp or DGH material. Datable redevelopment activity shows why it cannot be current:

| Phase | Wells | Status |
|---|---|---|
| Mumbai High **North** Phase III (approved Jun 2014) | **52 new + 24 sidetracks = 76**; 5 new wellhead platforms; mods at 13 platforms | Completed 2017 |
| Mumbai High **North** Phase IV | **43 wells** | Completed Dec 2022; new platform Feb 2023 |
| Mumbai High **South** Phase III (approved 2014) | **70 new wells** (57 done by Sep 2018); 3 new WHPs, 2 clamp-ons, mods at 18 platforms | Largely complete |
| Mumbai High **South** Phase IV | Water injection facility upgrade; new NWIS-R platform | — |
| **Phase V** (field-wide, current) | **71 wells = 16 new + 55 sidetracks**; new platform RS23. Target: **4.36 MMT incremental oil + 1.83 BCM gas by 2039-40** | Underway |

**260 wells drilled or sidetracked at Mumbai High since 2014 alone.**

- If 665 was the **pre-2014** count, the current figure should be far higher.
- If 665 is **current**, then ~260 additions were offset by a comparable number of shut-ins or conversions.

**Either reading makes it unusable as a current producing-well number — and the second reading would itself be strong evidence for this problem statement.**

---

## 5. What we do not know

| Unknown | Status |
|---|---|
| ONGC's producing well count, onshore/offshore | **Not published anywhere.** Confirmed absent from CAG, COPU, Parliament, DGH, PPAC and the Annual Report. Best available is the ~5,000–7,500 inference in §1.2 |
| Number of idle / shut-in / non-flowing wells | **Not published.** No CAG report contains well-count tables — the audits are about rigs |
| ONGC's artificial lift population by type | **Not published. Full stop.** The circulating split traces to one undated SlideShare deck |
| Average days a well waits for a workover rig | **No published figure exists globally**, at ONGC or any operator. Nearest public proxy: 33 of 142 Assam wells with 8–205 day rig mobilisation delays (CAG 42/2015) — but that is inter-well rig-move lag, not time-to-intervention |
| Workover-rig utilisation *as distinct from* drilling-rig utilisation | **Not disclosed separately** |
| Per-job workover cost / onshore workover rig day rate in India | **Not published.** Sourcing route in §6, item 2 |
| NSTA's wells-vs-plant mmboe loss split | **Not in public reports.** Available via NSTA's benchmarking packs on request |
| ONGC opex/bbl and levies/bbl | **Not disclosed.** Must be derived from segment reporting |
| Indian equivalent of the NSTA production-efficiency benchmark | **Does not exist.** No regulator-published production efficiency measure for India |
| Mumbai High current producing well count | See §4 |

> [!NOTE]
> **The absence of published data is itself part of the problem statement.** India's most important upstream asset base has no public production-efficiency metric, no public idle-well register, and no public intervention-cost benchmark. **The gap has persisted precisely because it has never been measured.**

---

## 6. Outstanding research items

| # | Item | Route | Value |
|---|---|---|---|
| 1 | **NSTA wells-vs-plant mmboe loss split** | Request the NSTA Production Efficiency benchmarking pack / dashboard access — free and legitimate | **Highest.** Directly sizes the addressable slice and closes the §7 Objection 4 caveat in the problem statement |
| 2 | **ONGC onshore workover rig day rates** | Manual extraction from `etenders.gov.in` (GePNIC, organisation = ONGC) and `vendor.ongc.co.in`. Keywords: "Charter Hiring" + "Workover Rig" + "Onshore". Ref **XU1AC25003** is a live empanelment tender | High. Only route to an India cost basis. ~2–3 hours of human portal work — **search will not surface it** |
| 3 | **SPE-212848-PA full text** | OnePetro / SPE Journal | **BLOCKING — escalated 2026-09-23.** Three reasons now, not one: (a) the abstract confirms the 4–5 month baseline but **not the achieved post-intervention uplift**, and the uplift is the number that makes the case; (b) it is the **only ONGC-specific failure-mechanism source** in the entire evidence base, and the model feature specification rests on it; (c) a **claim that the paper identifies dogleg severity as a predictive feature has been retracted** — the abstract states "lateral loads in deviated wells" and "tubing and rod buckling" but does **not** name DLS or the neutral point. See `model_data_foundation.md` §7.2 |
| 4 | **ONGC "work-over efficiency index" definition** | ONGC investor filings; direct ask | High. Improving a metric the customer already reports is a far easier sale than introducing one |
| 5 | **CAG Report No. 42 of 2015 full PDF** and the **March 2018 *New Indian Express*** piece | `cag.gov.in`; `newindianexpress.com` | Medium. Both primary; may contain adjacent tables lost in search summarisation |
| 6 | **PEC awardee investor material** | The 7 bidders holding 49 ex-ONGC fields across 13 contract areas | Medium. An unexploited back-door into field-level ONGC asset data |
| 7 | **Reference asset selection** | Internal decision | **Blocking all data generation.** Assam is recommended: documented 10.66% shortfall, known rig count (15), single coherent geography |

---

## 7. Additional context not carried into the problem statement

### 7.1 Diagnostic technique the solution should use

- **Chan diagnostic plots (K.S. Chan, 1995, SPE 30775).** WOR and WOR′ plotted log-log distinguishes **water coning** from **channelling** — a distinction that determines whether the correct job is a squeeze, a recompletion or nothing at all. Naive water-cut thresholds cannot make this call.
- **Skin factor and nodal analysis** for uplift estimation, rather than an assumed percentage recovery.
- **Wellbore integrity and geometry pre-check** before any candidate is put on a plan — a well the tooling cannot physically reach is not a candidate.

### 7.2 ONGC's existing digital programmes

| Programme | What it is | Why it does not close this gap |
|---|---|---|
| **NETRA** (IPEOT, "Bytes to Barrel") | Real-time analytics, well and network modelling | Monitoring, not forward planning |
| **DARPAN** | Corporate visualisation centre | Presentation layer |
| **RTOC** (Dehradun) | Real-Time Operations Centre | Drilling-focused |
| **Lakhmoni pilot** (with SLB) | Digital oilfield pilot | **~10% production uplift on artificial-lift wells** — ONGC's own internal precedent, and the strongest "it works here" evidence available |

### 7.3 The Indonesia analogue

A comparable NOC facing the same problem, with published numbers:

- **~16,000–17,000 idle wells** nationally; **~4,495 assessed as having reactivation potential**
- **Pertamina holds 4,886**, of which ~4,200 are reactivatable
- **SKK Migas is targeting 1,000–1,500 reactivations per year to 2028** under Permen ESDM 14/2025

Useful as a "another national oil company has quantified this and is acting on it" reference. **Do not present Indonesian figures as proxies for Indian ones.**

### 7.4 Field ages and asset anchors

| Anchor | Value |
|---|---|
| ONGC rigs, drilling + workover | ~230 |
| ONGC share of India's crude / gas | ~65–70% / ~84% |
| Mature-field recovery factor | 25–33% |
| Assam Asset | 43 production installations, 16 drilling rigs, 15 workover rigs |
| Assam production Apr'25–Jan'26 | 875.83 kT, **10.66% below target** |
