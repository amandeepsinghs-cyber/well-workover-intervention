# Decision Architecture
## How a well gets from a signal to a draft intervention plan on the Asset Manager's desk

**Version:** 1.1 · **Date:** 2026-09-23
**Companions:** `Problem Statement.md` · `model_data_foundation.md` · `demo_flow.md` · `build_plan.md`
**Status:** This is the product specification. Everything else describes the problem.

**v1.1 changes:** §3 expanded from a 12-row mechanism table to a **28-job intervention catalogue** grouped by category, with wax split into four distinct jobs and re-perforation made a standalone job · §3.2 adds the Chan WOR′ slope directions and a six-mode surface-signature discrimination table · §6 **new** — the daily / weekly / monthly reporting rhythm, including the ED-facing monthly scorecard · re-perforation confirmed rig-requiring on SRP wells.

---

## 0. The answer

> **Three of the four triggers need no trained model at all. The system flags wells, diagnoses mechanism, selects the job, prices it, and drafts the plan — on day one, from daily production data and workover history. The ML model improves trigger #4 and adds lead time. It is not the thing standing between here and a working product.**

That resolves the tension in the last two conversations. Measurement-first is not a retreat from the product — **it is the first running version of the product**, because measuring deferred barrels requires exactly the same tables, the same decline fits and the same event history that prediction does. You do not build one and then start over.

| | Needs a trained model? | Works day one? |
|---|---|---|
| **Trigger A** — rate below this well's own expected decline | ❌ No | ✅ **Yes** |
| **Trigger B** — well is *due* on its own run-life history | ❌ No | ✅ **Yes** |
| **Trigger C** — diagnostic signature fires (Chan, fillage) | ❌ No | ✅ **Yes** |
| **Trigger D** — survival model hazard crosses threshold | ✅ Yes | ⏳ After training |

---

## 1. The trigger layer — runs nightly, every well

### 1.1 Trigger A · Underperformance *(the one that catches silent loss)*

This is **P3** in the Problem Statement — wells that keep producing, so never generate a work request, and never enter the queue.

> [!WARNING]
> **Do not use an absolute rate threshold.** "Flag anything below 10 BOPD" is wrong: a 5 BOPD well is healthy and a 60 BOPD well that has fallen to 25 is in trouble. An absolute threshold flags the wrong wells in both directions and destroys trust in week one.

**Use the residual against the well's own fitted decline:**

```
expected(t)  = Arps fit on this well's trailing 12–24 months
residual(t)  = (actual(t) − expected(t)) / expected(t)

FLAG when  residual < −15%  sustained over 7+ consecutive producing days
           AND no choke/operational change recorded in that window
```

**Why it is defensible:** every well is judged against itself. The Asset Manager cannot object that you don't understand his field, because you are not comparing his wells to anyone else's.

**Severity tiers:** −15% watch · −25% flag · −40% urgent.

### 1.2 Trigger B · Due on its own history *(the strongest signal, and it is not ML)*

A well that parted rods at 5.2, 6.1 and 5.8 months, now at 5.9 months, is **due**. No model required — this is renewal theory.

```
FLAG when  days_since_intervention > p50 of this well's own prior run-lives
  ESCALATE when > p75
  and weight by cumulative fluid throughput since last intervention,
      not calendar days alone — a well that has been down half that period
      has not accumulated the same wear
```

> [!IMPORTANT]
> **This is also the baseline the ML model must beat.** If the survival model cannot outperform "days since last workover, normalised by throughput," then **we do not need the model** — and saying that out loud is worth more than any demo. Build the baseline first, deliberately, as the control.

### 1.3 Trigger C · Diagnostic signature

Deterministic physics, no training required:

| Signature | Fires on | Means |
|---|---|---|
| WOR′ log-log slope shift | Well tests | Water mechanism change — breakthrough, channelling |
| Fillage proxy divergence | SPM, stroke, runtime vs liquid | Pump degrading, or fluid pound |
| THP rise + rate fall | Daily production | Near-surface restriction — wax |
| Volume vs pump displacement gap, CHP flat | Daily production | Tubing leak |
| Rising CHP at falling rate | Daily production | Pump not evacuating annulus |

### 1.4 Trigger D · Predicted failure *(the ML one)*

Survival model returns hazard and expected time-to-failure. **Flag at P(fail ≤ 30d) > threshold**, tuned so flag volume matches what the asset can actually action — roughly 6 workovers/day company-wide.

> [!CAUTION]
> **Tune on precision, not recall.** A false positive sends a rig to a healthy well and costs ~₹ lakhs plus the credibility of every future flag. Missing a failure costs deferred barrels you were already losing. **The asymmetry runs strongly against false alarms**, especially in year one.

---

## 2. Diagnosis — *why* is this happening?

Once flagged, the agent assembles evidence. **It does not guess.** It calls deterministic tools and retrieves the well's own history.

```
▸ fit_decline_curve()     is this reservoir decline, or something mechanical?
▸ chan_diagnostic()       WOR/WOR′ → coning | channelling | multilayer
▸ fillage_proxy()         theoretical displacement vs actual liquid
▸ pressure_signature()    CHP/THP pattern → pump | tubing | wax
▸ search_well_history()   prior workovers, completion schematic, last 3 job outcomes
▸ check_offsets()         are neighbouring wells doing the same thing?
```

**`check_offsets()` matters more than it looks.** If six surrounding wells show the same water rise, it is a **reservoir or injection issue, not a well problem** — and no workover will fix it. A system that cannot reach that conclusion will send rigs to wells that do not need them.

**Output is ranked candidate mechanisms with evidence, never a single unexplained answer:**

```
GK-129  ·  primary: water channelling behind casing   confidence HIGH
          WOR′ log-log slope +1.08 over 90 d  → channelling, not coning
          step change 62% → 78% water cut in 11 days
          offsets GK-127, GK-131 stable      → well-specific, not reservoir
          1998 completion report: poor cement bond log, 1,847–1,862 m
        alternative: multilayer breakthrough  confidence LOW
          rejected — WOR′ lacks the characteristic plateau
```

---

## 3. Mechanism → job. The intervention catalogue.

This is the *"what type of job"* the Asset Manager asked for. It is a **deterministic lookup, not an LLM judgement** — auditable, reviewable, and editable by ONGC's own engineers.

> [!IMPORTANT]
> **The rig / rigless column is the most commercially important column in this document — and it is the one this project has got wrong three times.** Separating the two queues is the single largest source of effective capacity in the asset, and it costs nothing. But the claim only holds if the column is right.
>
> **The governing constraint (`TC-008.6`):** on a sucker-rod-pumped well, **nothing enters the wellbore below the pump seating nipple without first pulling the rod string.** Slickline, coiled tubing and wireline tools cannot pass the rods. Genuinely rigless work on an SRP well is therefore confined to: **annulus circulation, bullheading, squeezes, and surface work.**
>
> **Five rows below were corrected on 2026-09-23** against this constraint — they are marked ⚠**CORRECTED**. See [§3.2a](#32a-the-five-rows-that-were-wrong).

> [!CAUTION]
> **`RIGLESS_SHARE = 24%` is derived, not asserted, and it must never be presented as an industry benchmark.** No published rig-versus-rigless split for a mature onshore rod-pumped asset exists anywhere. The figure is computed bottom-up from this catalogue under `TC-008.6` — `SURFACE 12 + SCALE 2 + ~2/3 of WAX 15 (≈10) = 24%` — and is recorded canonically in [spec/00_overview.md §5.3](./spec/00_overview.md). **The previously quoted 27% was asserted and is now wrong.** If the lift mix turns out to contain more gas-lifted or flowing wells, this number rises sharply: the rod string is what blocks wireline and coiled tubing, and those wells do not have one.

### 3.1 The catalogue

| # | Job | Mechanism addressed | Evidence that selects it | Rig? | Days | Cost |
|---|---|---|---|---|---|---|
| **Wax / paraffin** |||||||
| 1 | **Mechanical scraping** ⚠**CORRECTED** | Paraffin in tubing | THP rise, gradual liquid drop, prior wax history | **Rig** *(pulling unit)* — a wireline scraper cannot pass the rod string. Rod scrapers are fitted **while the rods are out** | 1–2 | Low |
| 2 | **Hot oil / hot water wash** | Paraffin in tubing + flowline | As above, plus seasonal/ambient correlation | **Rigless** — hot oiler, circulated down the annulus | <1 | Low |
| 3 | **Solvent soak** (xylene/toluene) | Heavy paraffin, asphaltene | Recurrence despite 1 and 2 | **Rigless** — pump truck, annulus | 1–2 | Low |
| 4 | **Wax inhibitor squeeze** | Prevention, not cure | ≥3 wax events in 12 months | **Rigless** — pump truck, annulus | 1–2 | Low |
| 5 | Downhole heater install | Continuous deep wax | Severe recurrence, low fluid temperature | Rig | 2–3 | Med |
| **Mechanical — the rod-pump failure set** |||||||
| 6 | **Rod string replacement / part repair** | Rod fatigue, fluid pound | Rate → 0 **instantaneously**, CHP unchanged | Rig *(pulling unit)* | 1–2 | Low–Med |
| 7 | **Pump changeout / overhaul** ⚠**CORRECTED** | Worn barrel, plunger, valve | **Gradual** liquid decline **+ CHP rise**, fillage divergence | **Rig** *(pulling unit)* — **an insert pump is retrieved with the rod string.** There is no slickline path to it | 1–3 | Low–Med |
| 8 | **Tubing leak repair / replacement** | Rod-on-tubing wear, corrosion | **Sharp** drop over 3–5 d, **CHP flat**, volume/displacement gap | Rig | 2–5 | Med |
| 9 | **Surface equipment repair** | Prime mover, gearbox, belts, stuffing box, polished rod, flowline | Runtime hours collapse with no downhole signature | **Rigless** | <1 | Low |
| 10 | **Lift optimisation — SPM / stroke change** | Pump-off, over-pumping | Fillage proxy divergence **without** mechanical damage signature | **Rigless** — surface crew | <1 | Low |
| 11 | **Gas separator install / reset pump setting depth** | **Gas interference / gas lock** | Fillage loss **with GOR rise** — distinguishes it from pump wear, where GOR is flat | Rig | 2–4 | Low–Med |
| 12 | Lift conversion — plunger resize, SRP→PCP, SRP→gas lift | Sustained inflow/lift mismatch | Repeated pump-off or repeated over-capacity across ≥2 cycles | Rig | 2–5 | Med |
| **Deposition and fill** |||||||
| 13 | **Scale removal — acid treatment** ⚠**CORRECTED** | Carbonate (HCl) or sandstone (mud acid) | **Flat production then sudden bind**, high produced-water scaling index | **Rigless *only* if bullheaded or annulus-circulated** by acid truck. **The CT-conveyed variant needs the rods out → Rig** | 1–3 | Low–Med |
| 14 | **Scale inhibitor squeeze** | Prevention | Recurrence, saturation index persistently >0 | **Rigless** — squeezed down the annulus | 1–2 | Low |
| 15 | **Sand cleanout / bailing** ⚠**CORRECTED** | Fill over perforations | Gradual decline, solids in produced fluid, wireline tags fill | **Rig** *(pulling unit)* — CT and bailers both require the rods out on an SRP well | 1–4 | Med |
| 16 | Sand control — screens, gravel pack | Chronic sand influx | Repeated cleanouts + accelerated pump wear | Rig | 5–10 | High |
| **Inflow restoration** |||||||
| 17 | **Re-perforation** | Plugged / damaged perforations | PI decline with static reservoir pressure intact; offsets healthy | Rig ⚠ *see 3.3* | 2–4 | Med |
| 18 | **Add-perforation** (extend interval) | Under-perforated pay | Log-derived bypassed pay in the current zone | Rig ⚠ *see 3.3* | 2–4 | Med |
| 19 | **Matrix acidising / stimulation** ⚠**CORRECTED** | Near-wellbore formation damage | PI decline, clean perfs, no fill | **Rigless *only* if bullheaded.** **CT-conveyed placement needs the rods out → Rig.** Bullheading gives no placement control, so the two are not interchangeable | 1–3 | Low–Med |
| 20 | Hydraulic fracturing / re-frac | Low-permeability zone (Tipam, Barail, Kalol) | Very low PI in a tight zone despite clean perfs | Rig + frac spread | 4–7 | High |
| 21 | **Zone transfer / behind-casing opportunity** | Current zone depleted, pay bypassed | Low fluid level + offsets depleted + logs show bypassed pay | Rig | 5–10 | High |
| **Water control** |||||||
| 22 | **Choke back / reduce drawdown** | Water **coning** | **WOR′ negative slope** | **Rigless** — surface | <1 | Low |
| 23 | **Cement squeeze + reperforation** | Water **channelling** behind pipe | **WOR′ positive slope** + step change in water cut | Rig + cementing unit | 5–10 | High |
| 24 | **Selective isolation / straddle packer / bridge plug** | Multilayer breakthrough | WOR′ plateau signature | Rig | 3–7 | Med–High |
| 25 | Polymer / gel treatment | Channelling where squeeze has failed | WOR′ positive **and** prior squeeze failed on this well | Rig | 3–5 | High |
| 26 | Casing repair / patch / squeeze | Casing leak | Sudden water influx, abnormal annulus pressure | Rig | 5–10 | High |
| **Terminal** |||||||
| 27 | **NO JOB JUSTIFIED** | **Reservoir pressure decline** | **Decline fit clean, no mechanical signature, offsets declining identically** | — | — | — |
| 28 | Plug and abandon | Below economic limit | Rate < opex, offsets depleted, no behind-casing opportunity | Rig | 5–10 | High |

### 3.2a The five rows that were wrong

All five failed for the same reason, and it is worth stating once: **on a rod-pumped well the rod string occupies the tubing, so slickline, wireline and coiled tubing cannot reach anything downhole.**

| # | Job | Was | Why it was wrong |
|---|---|---|---|
| 1 | Mechanical scraping | *Rigless — slickline* | A wireline scraper cannot pass the rods. Rod scrapers are fitted when the rods are already out |
| 7 | Pump changeout | *Rig (slickline if insert pump)* | An insert pump is **retrieved with the rod string**. The parenthetical inverted the physics |
| 13 | Scale acid wash | *Rigless — CT / acid truck* | The acid truck is rigless; **the CT is not.** They were conflated |
| 15 | Sand cleanout | *Rigless (CT) or Rig* | Both CT and a bailer need the rods out |
| 19 | Matrix acidising | *Rigless — CT* | Same. Bullheading is rigless but gives no placement control, so it is a different job, not a cheaper version of the same one |

> [!WARNING]
> **Genuinely rigless rows after correction: 2, 3, 4, 9, 10, 13 (bullhead variant only), 14, 22 — eight of twenty-eight.** The remaining rigless work is annulus circulation, squeezes and surface work. **This is still a real and valuable queue — and the figure has now been recomputed from the corrected column: `SURFACE 12 + SCALE 2 + ~2/3 of WAX 15 (≈10) = RIGLESS_SHARE 24%`, per [spec/00_overview.md §5.3](./spec/00_overview.md).** Wax and surface failures together are 27% of the taxonomy, but only about two-thirds of the wax work is annulus-circulated — the rest needs the tubing scraped, which means pulling rods. **Say 24%, not 27%.**
>
> **This constraint disappears if the well is not rod-pumped.** On a naturally flowing or gas-lifted well, slickline and CT reach the wellbore freely and most of these rows revert to rigless — which is one more reason the 100% SRP assumption in `spec/03` §2 needs resolving before this number is quoted.

> [!IMPORTANT]
> **Row 27 is the credibility row.** A system that always recommends a job is a system nobody believes. Being able to say *"this well does not need a workover, and here is why"* is what makes the other twenty-seven rows trustworthy — and it directly protects against **loss #3, the wrong-job loss**, in Problem Statement §4.

> [!CAUTION]
> **Cost bands are relative only.** No public per-job cost figures or Indian onshore workover rig day rates exist — see `research_appendix.md` §6 item 2. Absolute rupee figures must come from ONGC's own norms or from tender data, never from this table.

### 3.2 Discriminating between jobs on production data alone

Two diagnostic layers do nearly all the work. Both are published methods, not judgement.

**Water: the Chan (SPE-30775) WOR′ log-log diagnostic.** This decides whether water is a *well* problem or a *reservoir* problem, and therefore whether a rig is warranted at all.

| WOR′ behaviour | Mechanism | Physics | Job |
|---|---|---|---|
| **Negative slope** | **Coning** | The cone is self-limiting — it approaches pseudo-steady state, so the rate of WOR increase decays | Choke back (rigless). **A squeeze will not fix coning** |
| **Positive slope** | **Channelling** — behind pipe or high-perm streak | Progressive and non-self-limiting; the channel grows | Cement squeeze + reperf, or gel |
| Plateau | Multilayer breakthrough | Sequential layer breakthroughs | Selective isolation |
| Negative → positive late | Coning with late channelling | Both, in sequence | Stage: choke first, squeeze later |

> [!WARNING]
> **The coning/channelling slope directions are inverted in some secondary sources — including a research pass run for this project on 2026-09-23, which was corrected.** Getting it backwards sends a rig and a cementing unit to a well that needed a choke adjustment. The directions above are the verified Chan convention: **coning negative, channelling positive.**

**Mechanical: six surface signatures that must be distinguishable.** On a rod-pumped well with no downhole telemetry, these variables separate the major failure modes:

| Mode | Liquid rate | CHP | THP | GOR | Onset |
|---|---|---|---|---|---|
| **Pump wear** | gradual decline | **rises** | flat | flat | weeks |
| **Tubing leak** | sharp drop | **flat** | flat | flat | 3–5 days |
| **Wax** | drops | flat | **rises** | flat | gradual / seasonal |
| **Scale** | **flat, then sudden bind** | flat | flat | flat | instant after latency |
| **Rod part** | **→ zero** | flat | falls | flat | instantaneous |
| **Gas interference** | erratic / declines | rises | flat | **rises** | gradual |

*Why CHP rises on pump wear and not on a tubing leak:* as plunger-barrel clearance opens up, lifted fluid falls back and the **annular fluid level rises**, compressing casing gas. On a tubing leak the fluid recirculates tubing-to-annulus rather than accumulating, so annular gas volume stays roughly constant.

> [!NOTE]
> That mechanism assumes the casing valve is closed. **If the casing is vented to a flowline, CHP tracks flowline pressure and this discriminator is lost** — confirm casing configuration per well before relying on it.

### 3.3 Open items in this catalogue

| # | Item | Why it matters |
|---|---|---|
| 1 | ~~Is through-tubing re-perforation feasible, or must rods and pump be pulled first?~~ **RESOLVED 2026-09-23 — rig/pulling unit required.** On an SRP well the rod string and pump occupy the tubing, so a perforating gun **cannot be run past them**. Rods must come out first. A light pulling unit may suffice instead of a full workover rig, but it is **categorically not a rigless wireline job** | Rows 17–18 correctly stay in the rig-requiring queue. Any spec that put re-perforation in the rigless queue would have under-booked rig-days |
| 2 | **Is re-perforation defensible without a pressure-transient test?** Skin is the textbook justification, and a stripper well will not have a build-up test | Fallback evidence is PI decline + acoustic fluid level + healthy offsets. Weaker, and must be labelled as such in the draft plan |
| 3 | **Acoustic fluid-level shots are the cheapest missing measurement in the whole system** | They separate *"the reservoir won't give it"* from *"the pump won't lift it"* — the single most valuable disambiguation, and a one-hour rigless job |

---

## 4. Economics — what earns the rig-day

```
deferred_bbl_avoided =
    current_rate
  × ( expected_downtime_if_unplanned − expected_downtime_if_planned )
  + uplift_rate × remaining_months

net_value = deferred_bbl_avoided × realisation × P(job succeeds) − job_cost

PRIORITY  =  net_value ÷ rig_days_consumed
```

Three deliberate design choices:

1. **Divide by rig-days.** The scarce resource is rig-days, not money. A ₹2 cr job consuming 10 rig-days loses to two ₹1.2 cr jobs consuming 3 each.
2. **`P(job succeeds)` comes from this asset's own history**, by job type — not from a vendor brochure. If cement squeezes succeed 60% of the time here, that is the number.
3. **Rigless jobs are ranked separately.** They do not compete for rig-days at all. **24% of jobs exit the queue here** — and that is the single largest source of effective capacity.

---

## 5. The draft plan — what actually lands on the desk

This is the deliverable. Generated nightly, one per flagged well.

```
╔══════════════════════════════════════════════════════════════════════╗
║  DRAFT INTERVENTION PLAN — GK-129 · Geleki                           ║
║  Generated 2026-09-23 · Status: AWAITING ASSET MANAGER REVIEW        ║
╚══════════════════════════════════════════════════════════════════════╝

WHY THIS WELL, NOW
  Trigger A  production 31% below its own fitted decline, 12 consecutive days
  Trigger C  WOR′ slope +1.08 → channelling signature
  Not Trigger B — only 3.1 months since last intervention (p50 = 6.4)

DIAGNOSIS                                                  confidence HIGH
  Water channelling behind casing, 1,847–1,862 m
  · water cut 62% → 78% in 11 days — too fast for coning
  · WOR′ log-log slope +1.08 sustained over 90 days
  · offsets GK-127, GK-131 stable → well-specific, not reservoir
  · [cite] Completion Report GK-129, 1998-03: poor cement bond, 1,845–1,865 m
  · [cite] Workover Report GK-129, 2019-11: water shutoff attempted, 14 mo success

  Rejected: multilayer breakthrough — WOR′ lacks characteristic plateau
  Rejected: coning — rate of change inconsistent with vertical movement

RECOMMENDED JOB
  Cement squeeze + reperforation, 1,840–1,870 m
  Rig required        YES — workover rig, Class II
  Duration            7 days ± 2
  Estimated cost      ₹ [from asset norms]
  P(success)          0.61  — 11 of 18 comparable jobs, Geleki, 2019–2025

  Alternative considered: mechanical straddle packer
    Cheaper, 3 days, no rig — but 2019 attempt on this well failed at 14 months.
    Not recommended without a cement bond log first.

VALUE
  Current rate            18 BOPD (was 26)
  Post-job estimate       24 BOPD  (nodal, skin reduction)
  Deferred bbl avoided    ~2,900 over 12 months
  Value per rig-day       [ranked #3 of 14 candidates this cycle]

LOGISTICS                                            ⚠ ONE BLOCKER
  Cement, Class G         ✅ Nazira, 40 t
  Retainer, 5½"           ⚠ NOT IN STOCK at Nazira
                             Available Sivasagar — +2 days transit
  Rig availability        WO-7 free from 2026-10-04
  Earliest feasible       2026-10-06 (retainer transit governs)
  Displaces               nothing — WO-7 idle 10-04 to 10-09

PRECONDITIONS
  ☐ Cement bond log before squeeze — 2019 failure is unexplained without it
  ☐ Confirm 5½" retainer transit from Sivasagar

──────────────────────────────────────────────────────────────────────
  [ APPROVE ]   [ MODIFY ]   [ REJECT — reason required ]   [ DEFER ]
──────────────────────────────────────────────────────────────────────
```

**Everything in that plan is either computed by a deterministic tool or cited to a document.** No number in it originates from a language model.

---

## 6. The reporting rhythm — daily, weekly, monthly

The draft plan in §5 is **one well**. The operating value of the system is the **rhythm** it establishes around the asset. Same nightly engine, three aggregation levels, three audiences, three different questions.

| Cadence | Goes to | Question it answers | Content |
|---|---|---|---|
| **Daily** | Asset Manager | *"What changed overnight and what needs my signature today?"* | New triggers fired · draft plans awaiting review · wells that moved up or down the ranking · plans whose logistics blocker cleared |
| **Weekly** | Asset Manager + Surface Manager + rig coordinator | *"What is the rig doing for the next 14 days, and what is slipping?"* | Committed rig schedule · rigless queue (runs in parallel, no rig contention) · jobs slipping and why · approve/modify/reject counts |
| **Monthly** | **Basin Manager / ED** | *"Is this asset being worked in the right order, and is the system earning its place?"* | **Failures per well per year** · **mean run-life between interventions** · rigless share of interventions · decline-arrest barrels vs counterfactual · rig-day utilisation · job-type mix · **prediction accuracy against actuals** · **where the system was wrong**. *(Deferred barrels per rig-day is the internal ranking objective and is not reported here.)* |

> [!IMPORTANT]
> **Three rules that keep the rhythm honest.**
> 1. **Nothing is recomputed for a report.** Weekly and monthly are aggregations of the same nightly run. If the monthly number disagrees with the sum of the dailies, that is a bug, not a reconciliation.
> 2. **Daily is a queue, weekly is a plan, monthly is a scorecard.** Do not let the monthly become a longer weekly — it is the only artefact that looks *backwards* and grades the system.
> 3. **The monthly must show where the system was wrong.** A scorecard that only reports wins gets read once. See §7 on why rejections are the most valuable data in the system.

### 6.1 Weekly — the rig plan

```
WEEKLY INTERVENTION PLAN — Geleki · week of 2026-10-05
────────────────────────────────────────────────────────────────────
RIG-REQUIRING                              WO-7        WO-3
  Mon 05   GK-129  cement squeeze + reperf  ████████
  Thu 08   GK-204  pump changeout                      ████
  Fri 09   GK-118  rod string repair                   ██████
  committed rig-days 14 of 14 available     ⚠ no slack

RIGLESS — parallel, no rig contention                    9 jobs
  hot oil / scraper        GK-133, GK-147, GK-151, GK-162
  scale squeeze (CT)       GK-109, GK-188
  choke adjustment         GK-171, GK-193
  surface / prime mover    GK-206

SLIPPING                                                 2 jobs
  GK-141   deferred — offsets confirm reservoir decline, no job justified
  GK-177   blocked  — 5½" retainer, Sivasagar transit, ETA 10-11

REVIEW ACTIVITY (last 7 d)   approved 11 · modified 3 · rejected 2
  rejection reasons: "workover due on GK-155 anyway, combine" ×1
                     "water source is injector breakthrough" ×1
```

> **The rigless block is the point of this report.** Nine jobs cleared with no rig-day spent. **24%** of the failure taxonomy exits the rig queue this way — `SURFACE 12 + SCALE 2 + ~2/3 of WAX 15`, derived in [spec/00_overview.md §5.3](./spec/00_overview.md) and mirrored in `demo_flow.md` §5.3 — the single largest source of effective capacity in the asset, and today it is invisible because rigless work is not scheduled as intervention work at all.

### 6.2 Monthly — the ED scorecard

This is the ED-facing artefact. It has to survive the question *"how do I know any of this is real?"*

```
MONTHLY INTERVENTION REVIEW — Geleki · September 2026        [ILLUSTRATIVE]
═══════════════════════════════════════════════════════════════════════

THROUGHPUT                    this month     3-mo avg     trend
  Jobs completed                     23           19         ▲
    rig-requiring                    16           15         ─
    rigless                           7            4         ▲
  Rig-days consumed                  61           68         ▼
  Mean days flagged → executed     11.4         18.2         ▼

OUTCOME
  Deferred bbl avoided            ~4,800                     [method §4]
  Post-job uplift vs predicted      +7%  (18 of 23 within ±20%)
  Jobs that failed to deliver          3  → P(success) recalibrated

WHERE THE SYSTEM WAS WRONG                        ⚠ read this section
  False positives                      4   flagged, engineer rejected, well fine
      3 × choke change not in the data feed  → FIX: ingest choke log
      1 × genuine model error
  Missed failures                      2   failed with no prior flag
      GK-162  rod part, no precursor in daily data  → expected, 5% class
      GK-118  precursor present 9 d prior, threshold too loose → retuned

ENGINEER OVERRIDES                   rejected 6 · modified 9
  most common reason: "combine with adjacent well, save a rig move"
  → NOT currently in the value function. Candidate change to §4.

JOB MIX                     rod 26% · pump 22% · wax 17% · water shutoff 13%
                            surface 13% · scale 4% · other 5%
  deviation from expected taxonomy within ±3pp — no drift
```

> [!WARNING]
> **⚠ The illustrative JOB MIX line above still predates the corrected taxonomy and must be regenerated before use.** It carries no tubing-repair category, yet `TUBING_LEAK` is now the largest failure bucket at 22%. It also cannot be recomputed by hand: job mix is a **different population** from failure mix — one failure code can map to several jobs and several codes to one job — so it must come from the mechanism→job catalogue in §3.1 applied to a generated year, not from the share table. **The ±3pp drift check does not apply to job mix at all** and that line should be dropped when the block is regenerated.

> [!NOTE]
> **"Where the system was wrong" is the section that sells it.** Four false positives with three traced to a missing choke feed is not an embarrassment — it is a system that knows its own error modes and names the fix. An ED who sees that believes the other numbers.

> [!CAUTION]
> All figures above are **illustrative placeholders** for layout purposes and must not be quoted. Real values come from the asset's own history once §10 requirements 2 and 3 are supplied.

### 6.3 What this costs to build

Nothing beyond stage 1. The nightly run already produces per-well records with trigger, mechanism, job, rig-days and value. Daily, weekly and monthly are **three queries and three templates** over that table. The reporting rhythm is close to free once the engine exists — which is why it belongs in stage 1, not a later phase.

---

## 7. Routing and the feedback loop

```
nightly run
  → flagged wells ranked by value per rig-day
  → drafts generated
  → Asset Manager queue, ordered
  → APPROVE / MODIFY / REJECT(reason) / DEFER
  → approved jobs enter the rig schedule
  → post-job actuals captured
  → compared against predicted uplift
  → feeds P(success) by job type, and model retraining
```

> [!IMPORTANT]
> **The rejection reason is the most valuable data the system will ever collect.** Every *"no, because…"* from the Asset Manager is a labelled correction encoding tacit knowledge nobody has ever written down. After 200 of them you have something ONGC cannot buy: **a machine-readable record of how this asset's best engineers actually reason.**
>
> This is also why the output is a **draft, not an instruction**. The Asset Manager stays the decision-maker; the system does the assembly he does not have time for.

---

## 8. Trust architecture — who is allowed to compute what

| Layer | Implementation | Why |
|---|---|---|
| Triggers | Deterministic thresholds on fitted curves | Reproducible; an engineer can re-derive by hand |
| Diagnosis | Physics tools — Arps, Chan, nodal, fillage | Published methods, not opinion |
| Mechanism → job | **Lookup table, owned and editable by ONGC** | Their engineering standards, not ours |
| Prediction | Survival model | The only ML in the system |
| Economics | Explicit arithmetic, stated inputs | Auditable line by line |
| **Narrative, retrieval, assembly** | **LLM** | **Only here** |
| **Decision** | **Asset Manager** | Always |

> **The language model writes the plan. It never computes a number in it.** Every figure is a tool output or a cited document. That is what makes the tool-call trace worth showing.

---

## 9. Build sequence — what ships when

| Stage | Contains | Needs | Ships without a model? |
|---|---|---|---|
| **1** | Triggers A + B + C · diagnosis · job table · draft generation | `daily_production`, `well_master`, workover history | ✅ **Yes** |
| **2** | Economics, ranking, MRO check, rig calendar | Job costs, inventory, rig availability | ✅ Yes |
| **3** | Trigger D — survival model + lead time | 24+ months history, ≥200 labelled failures | ❌ No |
| **4** | Feedback loop, retraining, per-asset calibration | 6+ months of live decisions | ❌ No |

**Stage 1 alone answers the Asset Manager's question.** It flags the well, says why, names the job, and drafts the plan. It does it reactively-plus-early rather than predictively — and it is fully buildable on data ONGC already has.

**Stage 3 is what converts *early* into *ahead*.** It is the upgrade, not the foundation.

---

## 10. What has to be true

| # | Requirement | If missing |
|---|---|---|
| 1 | Daily or near-daily production per well, 24 months | Triggers A and C degrade to monthly resolution |
| 2 | **Workover history with dates, type and outcome** | **Trigger B dies; `P(success)` dies; no baseline** |
| 3 | Well status history with reason codes | Cannot compute deferred barrels — no value case |
| 4 | Pump geometry — plunger, stroke, SPM, runtime | Fillage proxy unavailable; pump diagnosis weakens |
| 5 | Job cost and duration norms | Ranking becomes barrels-only, ignoring rig-days |
| 6 | MRO inventory | Drop the logistics block; plans become less actionable |

**#2 and #3 are the ones to ask for first.** Everything structural depends on them.

---

## 11. Decisions needed to start

| # | Question | Recommendation |
|---|---|---|
| 1 | Build stage 1 before any model? | **Yes.** It is the product, it needs no synthetic data, and it makes the demo honest |
| 2 | Does the demo show stage 1 or stage 3? | **Stage 1 as the spine, stage 3 as the closing upgrade.** Currently it shows only stage 3 — the part we can least defend |
| 3 | Who owns the mechanism→job table? | **ONGC.** Ship a draft, have them edit it. Their edits are the adoption |
| 4 | Draft auto-sent, or queued for review? | **Queued.** Auto-send creates alert fatigue and one bad flag poisons the well |
| 5 | Nightly, or on-trigger? | **Nightly batch.** Matches the production-report rhythm the asset already runs on |
