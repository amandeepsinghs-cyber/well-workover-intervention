# Thesis Risk Audit
## Which cards is this actually standing on?

**Date:** 2026-09-23 · **Method:** hostile audit of `Problem Statement.md` v3.0 — assume a technically literate ONGC reader who wants it to be wrong.

---

## The verdict

> **The foundation is solid. The causal mechanism is one unsourced sentence, repeated five times. Everything monetary rests on assumptions the document itself flags.**

The thesis is not built on a deck of cards uniformly — it is a concrete slab with a card table on top of it, and the valuable conclusions are all on the card table.

**The single card that matters:**

> *"Those rig-days are allocated by **arrival order and escalation pressure**, because no forward, ranked, value-quantified queue exists to allocate them any other way."*
> — Problem Statement §1, and repeated in §5 (P2), §4 diagram, §10 twice

**There is no source for this anywhere in either document.** It is a claim about ONGC's internal operating practice, which we have no visibility into, asserted as fact in the most confident sentence of the whole thesis.

Worse, `research_appendix.md` §5 separately concedes:

> *"Average days a well waits for a workover rig — **No published figure exists globally**, at ONGC or any operator."*

**So the document asserts as its central mechanism something its own appendix states has never been measured, anywhere, by anyone.**

---

## Tier 1 — Solid. Survives hostile audit.

These are primary, attributable, and mostly from institutions hostile to ONGC's interests.

| # | Claim | Source | Why it holds |
|---|---|---|---|
| 1 | ~2,200 workovers + ~13,000 stimulations/yr | ONGC filings | Their own numbers |
| 2 | Capex +31% while production −16%; MoPNG's explanation found "interim" and inadequate | COPU 36th Report | **Parliament.** Cannot be waved away |
| 3 | ₹7,995 cr rig losses, **₹6,418 cr controllable**; ≥₹5,117 cr production deferment | CAG 42/2015 | National auditor |
| 4 | **"In-built inefficiency" in Rig Requirement Plans** | CAG 42/2015 | The planning instrument itself was found defective |
| 5 | No offshore rig acquisition policy 2002–2015 | CAG 42/2015 | 13-year governance gap |
| 6 | Fields 43–68 years old; 64 self-classified marginal, 49 awarded | ONGC PEC records | ONGC self-certifying maturity |
| 7 | Import dependency ~88.7%, record | PPAC | Official |
| 8 | NSTA cut intervention cost £11.00 → £7.60/boe by **re-prioritising what it intervened on** | NSTA 2026 | **Regulator, not vendor.** The proof the mechanism works |
| 9 | ONGC/bp conceded **+44% oil upside** from existing infrastructure | ONGC/bp | Contractual |
| 10 | Assam **10.66% below target** | ONGC operational | Specific and current |
| 11 | WRSP is NP-complete; objective = rig cost **+ production loss from delay** | Aloise et al. 2006 | Peer-reviewed |

> [!NOTE]
> **Item 4 is under-used and is the strongest card in the deck.** The national auditor found ONGC's *rig planning instrument* defective — not its execution. That is close to the thesis, sourced, and unarguable. It currently sits in §6.2 as a footnote.

---

## Tier 2 — Asserted. No source. These are the cards.

| # | Claim | Appears | Evidence |
|---|---|---|---|
| **12** | **"Rig-days allocated by arrival order and escalation pressure"** | **5×, as fact** | **None** |
| **13** | **"T5 queue wait is typically the longest interval"** | §4 diagram + §4 body | **None.** Appendix says no such figure exists globally |
| 14 | "No forward, ranked, value-quantified queue exists" | §1 | None — a claim about ONGC internal systems |
| 15 | "Diagnosis assembled manually from fragmented systems, some on paper" | §4 | None. Plausible, unverified |

### Why #12 is the load-bearing card

It is the causal claim. Remove it and the thesis has a problem with no mechanism:

```
ONGC underperforms          ← SOLID (CAG, COPU)
  because rig-days are misallocated   ← ASSERTED, NO SOURCE
    because allocation is by arrival order   ← ASSERTED, NO SOURCE
      therefore prediction + ranking fixes it   ← follows only if the above hold
```

**The failure mode is not academic.** An Assam asset manager says, reasonably:

> *"We do not work by arrival order. We hold a monthly well services meeting. I know which of my wells matter."*

At that moment the framing is not merely unsupported — it is **insulting and factually contradicted by the person you are selling to**, and every Tier 1 fact you cited becomes suspect by association.

And he is **probably partly right.** Experienced asset managers do prioritise. What they plausibly lack is not judgement but *systematisation, forward visibility, and a defensible audit trail.* That is a different — and far safer — claim.

---

## Tier 3 — Assumption-driven. Flagged in-document, to its credit.

Everything monetary lives here.

| # | Figure | Depends on | Status |
|---|---|---|---|
| 16 | 5,000–7,500 producing wells | One atypical Tamil Nadu census | Marked weak |
| 17 | **₹65–130 cr/yr (Frame A)** | **"20–40% of shortfall attributable to well availability" — explicit assumption** | Marked as assumption |
| 18 | **110 job-equivalents freed (Frame B)** | **A 5% sequencing gain — unsourced** | Not flagged |
| 19 | ~$45/bbl marginal contribution | Derived from undisclosed opex | Marked derived |
| 20 | MTBF 4–5 months | One paper, *problem wells* subpopulation | Marked as upper bound |

> [!WARNING]
> **Frame B is presented as the safer number and it is not.** §8 recommends it because it "requires no assumption about deferred-barrel share." True — but it substitutes an unstated assumption that **5% sequencing improvement is achievable**, which has no source either. Swapping a flagged assumption for an unflagged one is not de-risking.

---

## Tier 4 — Newly fragile as of today's research

| # | Claim | What changed |
|---|---|---|
| 21 | Failures are predictable at ONGC Assam | Evidence transferred from **deviated/horizontal, telemetry-rich, non-Indian** wells. Assam is vertical, manually-tested, waxy |
| 22 | Dogleg severity is the key failure driver | **Inference retracted** — not stated in the SPE-212848-PA abstract |
| 23 | Value can be demonstrated | Requires precondition **C2** (downtime history with reason codes), which is unverified and may not exist |

---

## The repair — three changes, roughly a day of editing

### Repair 1 — Downgrade the mechanism claim *(critical)*

Remove every instance of "arrival order and escalation pressure" as a factual assertion. Replace with a claim that is almost certainly true and cannot be contradicted in the room:

| Remove | Replace with |
|---|---|
| *"allocated by arrival order and escalation pressure"* | *"allocated on experienced judgement that is **not systematised, not forward-looking, and not auditable** — there is no ranked, quantified 90-day queue an Asset Manager can defend in a production review"* |

**Why this survives:** it concedes competence, claims only the absence of a *system*, and is confirmed by CAG's finding of "in-built inefficiency in Rig Requirement Plans" — which is **sourced**. It converts the weakest card into the strongest one.

### Repair 2 — Lead with measurement, not prediction

§8 already contains the right posture, buried at the end:

> *"The first deliverable of any engagement should be to measure the gap, not to assume it."*

**Promote that to the thesis.** Every unknown then stops being a weakness and becomes the product:

- *"No one has measured what well unavailability costs this asset"* → **that is the engagement**
- *"India has no production-efficiency benchmark"* → **that is the offer**
- *"C2 may not exist"* → **then phase 1 is production-loss accounting**

**A measurement pitch cannot be falsified by an asset manager's local knowledge. A prediction pitch can.**

### Repair 3 — Cut Frame A, caveat Frame B

Delete the ₹65–130 cr/yr figure. It is assumption × assumption and it is the number a hostile CFO will attack first. Keep Frame B, but label the 5% explicitly as illustrative, not estimated.

---

## Rewritten core thesis — survives contradiction

> **ONGC executes ~2,200 workovers and ~13,000 stimulations a year against a fixed rig fleet, on a well stock 43–68 years old. The national auditor has found ₹6,418 crore of *controllable* rig-management loss and has specifically found "in-built inefficiency" in the Rig Requirement Plans themselves. Parliament has rejected the explanation for capex rising 31% while production fell 16%.**
>
> **What does not exist — at ONGC or at any operator worldwide — is a measurement of what well unavailability actually costs an asset, and a forward, ranked, quantified queue an Asset Manager can defend in a monthly production review.**
>
> **The UK regulator cut intervention cost 31% in two years purely by re-prioritising what it intervened on. That is the benchmark. The first deliverable is to measure the gap at one asset — not to assume it.**

Every sentence is sourced. It makes no claim about ONGC's internal practice. It cannot be contradicted by someone who knows their own wells.

---

## Honest bottom line

| Question | Answer |
|---|---|
| Is the problem real? | **Yes.** Tier 1 is strong, and CAG/COPU are hostile witnesses |
| Is the stated *mechanism* evidenced? | **No.** One unsourced assertion, five times |
| Is the *sizing* defensible? | **No.** Assumption × assumption. Cut it |
| Is prediction feasible at this asset? | **Unknown.** Evidence is transferred from materially different wells |
| Is the thesis salvageable? | **Yes — and cheaply.** The repair is a reframe, not a rebuild |
| What is the actual product? | **Measurement first.** Prediction is phase 2, and phase 1 is what makes phase 2 provable |

> [!IMPORTANT]
> **The strongest version of this thesis is not "we can predict your well failures."** It is: *"nobody — not ONGC, not any operator on earth — has measured what this costs. The UK regulator measured it and cut intervention cost 31%. Let us measure yours."*
>
> That version needs no synthetic data, no unverified claim about ONGC's internal practice, and no prediction accuracy the demo cannot honestly show.
