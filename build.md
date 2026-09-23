# `build.md` — Step-by-Step Build and Deployment

**Agentic WRFM Execution Layer · ONGC Assam Asset, Geleki Field**
**Target:** ADK agent on Vertex AI **Agent Runtime**, published to **Gemini Enterprise**
**Version:** 1.0 · **Date:** 2026-09-23

---

## 0. Read this first

> **This is the executable companion to [`build_plan.md`](./build_plan.md). That document says *what* to build and in what risk order. This one gives the commands, in order, with a gate at the end of every stage.**

| Document | Answers |
|---|---|
| [`spec/`](./spec/) (10 docs) | **What the system must do** — the normative contract |
| [`build_plan.md`](./build_plan.md) | **Why in this order** — risk sequencing, the six phases |
| **`build.md`** ← you are here | **Exactly what to type** — commands, gates, definition of done |
| [`demo_flow.md`](./demo_flow.md) | **What to say** — the 10-minute script |
| [`blueprint_assessment.md`](./blueprint_assessment.md) | What we took from the external blueprint, and what we refused |

### Three rules that override convenience

> [!CAUTION]
> 1. **Never `pip install` globally.** Everything runs through `uv` with a pinned project virtualenv. *"We can regenerate this exactly"* is part of the integrity story we are selling.
> 2. **Never `agents-cli deploy` or publish without explicit human approval.** Not a style preference — a hard stop.
> 3. **Never fabricate a number to fill a field.** Every tool returns `UNAVAILABLE` / `LOW_CONFIDENCE` rather than guessing (`spec/04` §1.2). The demo's entire claim is that it refuses when it should.

### Stage map

```
 A  Preflight            auth, project, toolchain              30 min   ← gates everything
 B  Spikes               map · PDF citation · tool trace        1 day   ← gates D and G
 C  Data                 generator → validator → BigQuery       4 days
 D  Tools                18 deterministic tool contracts        4 days
 E  Model                survival model, C-index gate           3 days
 F  Scaffold             agents-cli project                     1 hour
 G  Wire                 tools → ADK, prompt, guardrails        3 days
 H  Evaluate             agents-cli eval, 5-10 iterations       2 days
 I  Deploy               Agent Runtime                          0.5 day
 J  Publish              Gemini Enterprise                      0.5 day
 K  Reports              daily / weekly / monthly cadence       2 days
 L  Rehearse             fallbacks, latency, dry runs           2 days
```

**A → B run first and in parallel. C runs in parallel with B. Nothing else may start early.**

---

## Stage A · Preflight

### A.1 Verify authentication — mandatory Step 0

```bash
gcloud auth list
gcloud auth application-default print-access-token >/dev/null && echo "ADC OK"
gcloud config get-value project
```

If ADC is missing:

```bash
gcloud auth application-default login
```

### A.2 Set project and region

```bash
export PROJECT_ID="<your-project>"
export REGION="us-central1"          # Agent Runtime region
export BQ_LOCATION="US"              # BigQuery dataset location

CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }datacloud.antigravity" \
  gcloud config set project "$PROJECT_ID"
```

> [!NOTE]
> **Every `gcloud` command in this document carries the `CLOUDSDK_METRICS_ENVIRONMENT` prefix, and every `bq query` / `bq load` / `bq mk` carries `--label datacloud:antigravity`.** Read-only `bq ls` / `bq show` must **not** carry `--label` — those subcommands reject it.

### A.3 Enable APIs

```bash
CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }datacloud.antigravity" \
gcloud services enable \
  aiplatform.googleapis.com \
  discoveryengine.googleapis.com \
  bigquery.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com
```

### A.4 Toolchain

```bash
uv tool install "google-agents-cli~=1.5.0"     # or: uv tool upgrade google-agents-cli
agents-cli info
```

> [!WARNING]
> **`agents-cli info` currently reports CLI v1.4.2 against v1.5.0 skills.** Run `agents-cli update` to sync before scaffolding, or the generated project will not match this guide.

### A.5 Create the Gemini Enterprise app — do this now, not at Stage J

Gemini Enterprise apps are created in the Console, not by the CLI, and **Stage J cannot start without one**.

```
Google Cloud Console → Gemini Enterprise → Apps → Create
```

Then confirm the CLI can see it:

```bash
agents-cli publish gemini-enterprise --list
```

Record the full resource name:

```bash
export GEMINI_ENTERPRISE_APP_ID="projects/<number>/locations/global/collections/default_collection/engines/<app>"
```

### ✅ Gate A

- [ ] ADC token prints
- [ ] All seven APIs enabled
- [ ] `agents-cli info` clean, CLI and skills on the same version
- [ ] `publish gemini-enterprise --list` returns at least one app

---

## Stage B · Spikes — three unknowns, one day, run in parallel

**Every one of these changes the design if it fails. That is the point of doing them first.**

### B.1 The map renderer ⚠ `RISK-001`, highest risk, first thing the ED sees

**Question:** does the Gemini Enterprise A2UI renderer support a Vega-Lite `geoshape` mark with a `projection`?

**Acceptance:** Geleki outline + 142 points, colour-coded, tooltips live, **< 8 s**.

Spike against the formal contract in [`spec/04` `TC-016`](./spec/04_tool_contracts.md), which already defines the tier ladder as part of the contract:

| Tier | Implementation | What the agent must say |
|---|---|---|
| **1** | Vega-Lite `geoshape` + `projection` + real basemap | Nothing — it is a live map |
| **2** | Vega-Lite points on raw lat/lon axes | *"Plotted on coordinates; the basemap layer is not available in this runtime"* |
| **3** | Pre-rendered basemap PNG + **live data table** | *"This basemap is pre-rendered; the well data beside it is live"* |

> [!IMPORTANT]
> **Tier 3 is the floor. There is no fallback outside Gemini Enterprise, and that is deliberate.**
>
> **The agent is deployed in Gemini Enterprise, so the demo happens in Gemini Enterprise.** Alt-tabbing to a second window mid-demo visibly breaks the claim that the agent did this — which is the whole point of the ten minutes. A pre-rendered basemap narrated honestly, with live data beside it, keeps the story intact. A second application does not.

> [!WARNING]
> **Also test whether inline GeoJSON is permitted, or whether external URLs are required.** If the tenant's egress policy blocks external URLs, Tier 1 dies even when `geoshape` works. Decide your tier **before Stage G**, and record it — `TC-016.2` requires `render_tier` to be surfaced so the agent can never narrate a live map it did not draw.

### B.2 Scanned-PDF retrieval with citation

**Question:** can Vertex AI Search return a citation with **document name and date** from a scanned-appearance PDF, reliably enough to put on screen?

**Acceptance:** `"water shutoff history GK-129"` returns the 2019 workover report with an openable link and a visible date.

If OCR is marginal, generate the corpus PDFs **with a real text layer** (render-to-PDF plus a scan-effect overlay) rather than true rasterised scans. This is the load-bearing proof of *"access data from anywhere."*

### B.3 The tool-call trace

**Question:** can the tool-call trace be displayed in the Gemini Enterprise UI, and animated?

It does double duty — proving determinism **and** covering the ~18 s wait in Act 3. If it cannot be shown, Act 3's latency budget drops below 10 s and the pre-computation strategy in Stage D changes.

### ✅ Gate B

- [ ] Map tier decided and written into `TC-016`
- [ ] PDF citation renders with name + date, or the text-layer workaround is adopted
- [ ] Trace visibility confirmed, or Act 3 latency budget revised

---

## Stage C · Data

### C.1 Project setup

```bash
mkdir -p workover_demo && cd workover_demo
uv init --python 3.12
uv add numpy pandas scipy pyarrow lifelines scikit-survival google-cloud-bigquery
uv add --dev pytest ruff
```

```
workover_demo/
├── pyproject.toml            # pinned. reproducibility is part of the pitch
├── generator/
│   ├── wells.py              # well_master: 142 Geleki wells, real coordinates
│   ├── geology.py            # zones, contacts, perforation intervals
│   ├── production.py         # daily oil/water/gas/THP/CHP/SPM/runtime
│   ├── damage.py             # Gamma-frailty cumulative damage → failure time
│   ├── failures.py           # taxonomy, signatures, downtime
│   ├── history.py            # well_status_history + workover records
│   └── validate.py           # the checklist. runs on EVERY build
├── tools/                    # Stage D
├── model/                    # Stage E
└── reports/                  # Stage K
```

### C.2 Generate in this order — the order is load-bearing

Getting it wrong produces data that violates mass balance.

```
1  well_master        →  2  geology      →  3  base decline (Arps, SD-017)
4  water cut trend    →  5  damage accumulation (Gamma frailty)
6  failure times      →  7  pre-failure signature overlays
8  downtime + workover records                →  9  status history
10 validator — and the validator FAILS THE BUILD, it does not warn
```

> [!CAUTION]
> **The three things that must be true, and that the external blueprint got wrong — see [`blueprint_assessment.md`](./blueprint_assessment.md) §2:**
> 1. **Production must decline.** Arps hyperbolic, `b ∈ [0.5, 1.0]`, `D_i ∈ [0.05, 0.15]/yr`. Without decline, *mechanical fault versus depletion* — the hardest and most valuable question in candidate selection — **cannot be posed at all**, and the `GK-141` refusal is unrepresentable.
> 2. **Failure times must come from a cumulative-damage process with unobserved frailty**, never from a fixed day index. A deterministic ramp starting on day 45 is a leak, and a C-index near 1.0 is the tell.
> 3. **Water-cut trajectories must differ per well.** Identical slopes make the Chan diagnostic impossible because coning, channelling and multilayer response are not in the data.

### C.3 ⚠ Load through the swap point — not straight into the contract tables

> [!CAUTION]
> **The tempting shortcut is to have the generator write directly into the 13 contract tables. Do not.** The whole integration story rests on the claim *"your data enters through exactly the pipe this data entered through, and we swap only the loader."* **If the generator writes the contract tables directly, that claim is false, and the transform layer runs for the first time in front of ONGC.**
>
> Full rationale in [`data_pipeline.md`](./data_pipeline.md) §1–§2. **Cost: about half a day. It buys the entire answer to the first question an Executive Director asks.**

```
generator/  emits SOURCE-SHAPED extracts     ← the ONLY layer that changes for ONGC
            mirroring ONGC export formats
                     │
                     ▼
     gs://<bucket>/landing/<source>/<yyyy>/<mm>/<dd>/     immutable, append-only
                     │
                     ▼
     BigQuery  geleki_raw     source-shaped, deliberately UGLY, untransformed
                     │
                     ▼
     transforms + DC-nnn gates                IDENTICAL CODE on both tracks
                     │
                     ▼
     BigQuery  geleki         the 13 contract tables
```

```bash
CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }datacloud.antigravity" \
  bq --location="$BQ_LOCATION" mk --label datacloud:antigravity -d "${PROJECT_ID}:geleki_raw"
```

```bash
CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }datacloud.antigravity" \
  bq --location="$BQ_LOCATION" mk --label datacloud:antigravity -d "${PROJECT_ID}:geleki"
```

Load the generator's source-shaped output into `geleki_raw`:

```bash
bq load --label datacloud:antigravity --source_format=PARQUET \
  "${PROJECT_ID}:geleki_raw.daily_prod_export" "gs://<bucket>/landing/generator/*/*/*/daily_prod_*.parquet"
```

**Every `geleki_raw` row carries four lineage columns**, and they are what make the provenance claim checkable:

```sql
_ingested_at    TIMESTAMP   -- when we received it
_source_system  STRING      -- 'GENERATOR' | 'SCADA' | 'EPINET' | 'WORKOVER_PDF' | 'SAP_ICE'
_source_file    STRING      -- the exact landing object
_batch_id       STRING      -- idempotency key
```

> [!TIP]
> **Minimum viable version: `geleki_raw → geleki` can be BigQuery *views*, not materialised tables.** The point is that the transform **exists as code and is the only path in.** Materialise later if performance demands it.

### C.4 The transform layer — where numbers silently go wrong

Create the 13 contract tables from the DDL in [`spec/02_data_contract.md`](./spec/02_data_contract.md) as the **output** of the transform, never as a load target.

| Transform | Why it is a risk |
|---|---|
| `tonnes → bbl`, `m³ → bbl` | A unit error here is invisible and changes every downstream number |
| **IST date normalisation** (`DP-008`) | `DATE(ts, 'Asia/Kolkata')`, **never a bare UTC cast.** A midnight-boundary error shifts every daily rate by one day |
| **`0 → NULL` correction** (`DC-014`, `DP-005.3`) | **A shut-in well and a well producing nothing are different facts**, and most source systems write `0` for both. Get this wrong and fake zeros poison every decline fit, steepening `arps_di` and firing Trigger A field-wide |
| `data_as_of` / `data_lag_days` (`DC-067`, `DC-068`) | Computed per well, **never a field-wide maximum** |
| `allocation_basis_id` (`DC-071`) | GGS + well-test vintage. **A change is a basis change, not a rate change** |

**Every one of these is tested.** They are the five places a correct-looking number becomes wrong.

### C.5 The validator is a build gate, not a report

```bash
uv run python -m generator.validate --fail-on-violation
```

It asserts the `DC-nnn` invariants in `spec/02` and the consistency checks in `spec/03`. **A violation exits non-zero and the pipeline stops.**

### ✅ Gate C

- [ ] 142 wells × 36 months, all 13 tables populated
- [ ] **`geleki_raw` exists and is the only source of `geleki`.** No generator process writes a contract table directly
- [ ] **Lineage columns present on every `geleki_raw` row**; a value on screen can be traced to a landing object
- [ ] Validator exits 0 with zero violations
- [ ] Failure-code shares hold within ±3pp of `spec/00` §5.3
- [ ] **Non-SRP wells carry NO `ROD_PART` or `PUMP_WEAR` rows** (`SD-028`) — assert, do not eyeball
- [ ] **Depths honour `SD-013b`…`SD-013d`**; no pump set below its perforations; TVD ≤ MD on every well
- [ ] Availability arithmetic reproduces `spec/00` §5.2 (`D-15` closed: `FRACTION_DOWN_ACTIVE = 16.3% ± 1.0pp`, `FRACTION_DOWN_TOTAL = 20.0% ± 1.0pp`)
- [ ] Spot-check: at least one well each exhibiting coning, channelling, multilayer and **injector breakthrough** (`SD-034`)
- [ ] **At least one compressor event exists** (`SD-033d`) and **writes no failure rows** — this is the trap set for our own ranking engine

---

## Stage D · The deterministic tool library

**Build these as plain, testable Python first. They are not ADK tools yet.** That separation is deliberate: it lets every tool be unit-tested without an LLM in the loop, and the tests are where the physics is defended.

| Priority | Tools | Why |
|---|---|---|
| **P0** | `TC-016` map · `TC-017` plot · `TC-018` query_wells | Acts 1–2. Nothing renders without them |
| **P0** | `TC-001` decline · `TC-002` Chan · `TC-007` triggers | The detection core |
| **P0** | `TC-004` offsets · `TC-008` route · `TC-009` uplift · `TC-010` rank | The decision core, including the refusal |
| **P1** | `TC-003` fillage · `TC-005` signature · `TC-006` predict | The prediction layer |
| **P1** | `TC-011` MRO · `TC-012` history · `TC-013` draft plan | The plan |
| **P2** | `TC-014` report · `TC-015` rig schedule | Act 4, Act 5 |

### D.1 Write the Chan test before the Chan code

> [!CAUTION]
> **`TC-002` is the highest-risk tool in the system and the sign convention has already been inverted once on this project.**
>
> ```
> WOR′ slope NEGATIVE → CONING       → choke back          → RIGLESS, < 1 day
> WOR′ slope POSITIVE → CHANNELLING  → cement squeeze      → RIG, 5–10 days
> WOR′ plateau        → MULTILAYER   → selective isolation → RIG, 3–7 days
> ```
>
> **Inverted, this books a seven-day rig job on a well that needed a thirty-minute choke adjustment.** Write the known-coning and known-channelling fixtures **first**, per `spec/00` §6.

### D.2 The rig/rigless invariant

`TC-008.6`: **on a well with `lift_type = 'SRP'`, any job requiring access below the pump seating nipple is `requires_rig = TRUE`, without exception.** Nothing enters the wellbore of a rod-pumped well without first pulling the rods.

This project has made the same error three times. `AT-041c` sweeps all 28 catalogue rows so it cannot recur.

### D.3 The seven rules every tool obeys

From [`spec/04`](./spec/04_tool_contracts.md) §1.2 — most importantly: **a tool returns `UNAVAILABLE` or `LOW_CONFIDENCE`; it never invents a value to fill a field.**

```bash
uv run pytest tools/ -v          # every TC has L1 unit tests in spec/08
```

### ✅ Gate D

- [ ] All 18 tools implemented with L1 tests green
- [ ] `AT-030d` Chan sign sweep passes
- [ ] `AT-041c` rigless invariant passes across all 28 catalogue rows
- [ ] `AT-013` a 5 BOPD well at expected decline does **not** outrank a 60 BOPD well 40% below its own curve

---

## Stage E · The survival model

```bash
uv run python -m model.train --config model/config.yaml
uv run python -m model.evaluate --report model/metrics.json
```

| Gate | Value | If it fails |
|---|---|---|
| `C_INDEX_MIN` | **≥ 0.65** | Do not ship the model |
| `C_INDEX_EXPECTED` | **0.65–0.72** ⚠ re-baselined under refinement #8 | — |
| `AUC_LEAK_THRESHOLD` | **> 0.95 = hard build failure** | You have a leak, not a good model |
| `BASELINE_TO_BEAT` | Trigger B alone | If the model cannot beat it, the model is not needed |

**Also report Brier score and calibration.** C-index alone is weak under heavy censoring, and workover data is heavily censored (~40%).

> [!NOTE]
> **No published C-index exists for rod-pump time-to-failure on daily production data.** That is a finding, not a gap — say so, and say we are setting the baseline. The nearest comparable is SPE-165374 (2013, ~2,000 rod pumps, five assets): precision and recall just above 65%, **on richer data than we will have**.

### ✅ Gate E

- [ ] C-index in band, on a held-out split
- [ ] AUC < 0.95
- [ ] Beats the Trigger-B baseline
- [ ] Brier score and a calibration plot exist

---

## Stage F · Scaffold the agent

> [!IMPORTANT]
> **`agents-cli` Phase 0 requires an approved `.agents-cli-spec.md` before scaffolding.** We already have ten spec documents, so write a thin pointer rather than duplicating them — but **write it**, because the CLI and every future session read it as the source of truth.

`.agents-cli-spec.md`:

```markdown
# Agent Spec — Workover Agent, Geleki

**Purpose:** an agentic WRFM execution layer for ONGC Assam Asset that converts
each rig-day into decline-arrest barrels — detecting which wells will fail and
when, selecting the intervention, and refusing when the evidence says the well
does not need one.

**Normative spec:** ../spec/ (10 documents). This file is a pointer, not a copy.
- Tools .......... spec/04_tool_contracts.md  (TC-001 … TC-018)
- Behaviour ...... spec/07_agent_spec.md      (AS-001 … AS-016)
- Tests .......... spec/08_test_plan.md

**Data source:** BigQuery dataset `geleki` (13 tables, spec/02).
**Safety:** never fabricate a value; return UNAVAILABLE. Never claim a live map
when rendering Tier 2 or 3. Never issue a draft plan that fails the barrier gate.
**Deployment:** Agent Runtime → published to Gemini Enterprise.
```

### F.1 Pick the model — list, do not guess

```bash
uv run --with google-genai python -c "
from google import genai
client = genai.Client(vertexai=True, location='global')
for m in client.models.list(): print(m.name)
"
```

Take the newest stable Gemini. **Do not hardcode a model name from memory** — it will be stale.

### F.2 Create the project

> [!WARNING]
> **Do not `mkdir` the directory first.** The CLI creates it; pre-creating it silently switches `create` into enhance mode.

```bash
agents-cli scaffold create workover-agent-geleki \
  --agent adk \
  --prototype \
  --region "$REGION" \
  --agent-guidance-filename GEMINI.md
```

`workover-agent-geleki` is 21 characters — inside the 26-character limit.

**Prototype first.** Deployment scaffolding is added at Stage I, once the agent actually works.

### ✅ Gate F

- [ ] `agents-cli info` reports the project
- [ ] `agents-cli run "hello"` returns a response

---

## Stage G · Wire the tools into ADK

### G.1 Before writing a line, study the recipes

Three shipped recipes cover capabilities we need. **Adapting one beats reinventing it worse.**

| Need | Recipe |
|---|---|
| Guardrails across a coordinator **and** every sub-agent, in one place | `safety-plugins` |
| Approval gate / workflow pause before a risky action | `ambient-expense-agent`, `deep-search` |
| Scheduled, headless, queue-driven runs — **our daily/weekly/monthly cadence** | `ambient-expense-agent` |
| A2A interop, including Gemini Enterprise client quirks | `long-horizon-harness` |

The topic index lives in `/google-agents-cli-adk-code` → `references/samples.md`.

### G.2 Register the tools

Each `TC-nnn` becomes an ADK `FunctionTool` wrapping the Stage-D function unchanged. **The wrapper adds no logic** — if it does, the L1 tests no longer test what ships.

### G.3 The system prompt and guardrails

Lift the system prompt verbatim from [`spec/07`](./spec/07_agent_spec.md). The non-negotiables:

| ID | Guardrail |
|---|---|
| `AS-001`…`AS-009`, `AS-016` | Never fabricate; always cite the tool; state confidence |
| `AS-007` | **Never narrate a Tier-2 or Tier-3 map as a live map** |
| `AS-012` | The push-back: absolute rate is never the ranking key |
| — | **`NO_JOB_JUSTIFIED` is a first-class outcome, not an error** |

### G.4 Smoke-test as you go

```bash
agents-cli run "Show me the wells in Geleki"
agents-cli run "Which wells need intervention this month?" -v
agents-cli playground                      # interactive
```

> [!WARNING]
> **Do not write pytest that asserts on LLM output.** Behaviour is validated in Stage H. Pytest covers the Stage-D tools only.

### ✅ Gate G

- [ ] All five demo acts run end to end locally
- [ ] Act 3 shows **≥ 8 named tool calls** (`AT-084`)
- [ ] `GK-141` produces a reasoned refusal, not an error
- [ ] The agent states the map tier out loud

---

## Stage H · Evaluate

```bash
agents-cli eval run                        # generate + grade
agents-cli eval generate && agents-cli eval grade    # two-step, for debugging
```

**Start with 1–2 cases, not a suite.** Expect **5–10 iterations**. `eval run` exits 0 whatever the scores are — read them.

Seed the dataset from the seven `spec/03` §12 fixtures, because each was designed to exercise a distinct decision path:

| Fixture | What it proves |
|---|---|
| `GK-129` | Channelling → cement squeeze + re-perforation, over the straddle packer that already failed here |
| **`GK-141`** | **The refusal.** Trigger A fires, offsets are proportionally down, no job justified |
| `GK-103` | Coning → choke adjustment. Rigless, < 1 day. The Chan sign convention made visible |
| `GK-112` | Scale → bullheaded acid. Genuinely rigless |
| `GK-087` | Trigger B only — no rate signal at all |
| `GK-055` | Pump wear → changeout. **Pulling unit, because the insert pump comes out on the rod string** |
| `GK-147` | Wax → hot oil + solvent soak, annulus-circulated |

### ✅ Gate H

- [ ] Every core case at the agreed bar
- [ ] `GK-141` refuses, with a stated reason
- [ ] No case invents a number for a missing field

---

## Stage I · Deploy to Agent Runtime

### I.1 Add deployment scaffolding

```bash
agents-cli scaffold enhance . --deployment-target agent_runtime
```

> Agent Runtime manages sessions internally. **If your code sets `session_type`, remove it** — Agent Runtime overrides it.

### I.2 Stop. Get approval.

> [!CAUTION]
> **Paste the Stage-H eval scores to the human and ask "Ready to deploy?". Wait for an explicit yes.** Never deploy without it.

### I.3 Deploy

```bash
agents-cli deploy --project "$PROJECT_ID" --region "$REGION"
```

Deploys take **5–10 minutes** and may exceed a command timeout. **The deployment continues server-side.** Poll rather than re-running:

```bash
agents-cli deploy --status        # every ~60 s until complete or failed
```

Success writes `deployment_metadata.json`, which Stage J reads automatically.

### ✅ Gate I

- [ ] `deployment_metadata.json` exists with `remote_agent_runtime_id`
- [ ] A test query against the deployed agent returns
- [ ] `google-cloud-aiplatform > 1.128.0` in `uv.lock` — **older versions cause "Session not found" after registration**

---

## Stage J · Publish to Gemini Enterprise

**ADK registration is the default and the right choice here**: Gemini Enterprise invokes the agent natively via `:streamQuery` on its reasoning-engine resource, authenticating end to end. No agent card URL needed.

```bash
agents-cli publish gemini-enterprise \
  --gemini-enterprise-app-id "$GEMINI_ENTERPRISE_APP_ID" \
  --display-name "Workover Agent — Geleki, Assam Asset" \
  --description "Predicts well failures, selects the intervention, and plans against the rig constraint" \
  --tool-description "Answers questions about Geleki well health, failure risk, and workover priority"
```

Everything else — runtime ID, registration type, deployment target — is auto-detected from `deployment_metadata.json`.

**Registration is idempotent.** Re-running updates in place rather than duplicating.

| Symptom | Fix |
|---|---|
| `HTTP 403` | Your account needs **Discovery Engine Editor** on the Gemini Enterprise project |
| `"Session not found"` | SDK too old — upgrade `google-cloud-aiplatform`, redeploy, re-register |
| ADK invocation fails silently | Grep the runtime's `reasoning_engine_stderr` logs for **`streaming_agent_run_with_events`** — that is the method `:streamQuery` dispatches to |

### ✅ Gate J

- [ ] The agent appears in the Gemini Enterprise app
- [ ] **All five acts run inside Gemini Enterprise, not just locally** — this is the first honest end-to-end test
- [ ] The map renders at the tier decided in Stage B
- [ ] Tool-call trace is visible

---

## Stage K · Reports and cadence

Three reports, field-by-field in [`spec/06_report_spec.md`](./spec/06_report_spec.md):

| Report | Audience | Delivery |
|---|---|---|
| **Daily** | Production engineer | 08:00 IST — what changed, what needs a decision today |
| **Weekly** | Asset Manager | The rig plan for the coming week, rigless queue separated |
| **Monthly** | **Basin Manager = the Executive Director** | Decline arrest, failures per well per year, run-life, job mix vs failure mix |

Built on `TC-014 generate_report()` over BigQuery. Use ADK `trigger_sources` for the schedule — on Agent Runtime the routes are reachable through the Agent Engine `/api` passthrough.

> [!IMPORTANT]
> **KPI order matters, and it changed under refinement #4.** Lead with **failures per well per year** and **mean run-life** — their language, their baseline. Then **incremental oil per job and payout days** — their approval language. Deferred-barrels-avoided per rig-day is the **stated internal objective function**, not the headline. Presented that way it reads as sophistication rather than an unfamiliar ask.

Use `DATE_TRUNC(DATE(decided_at, 'Asia/Kolkata'), MONTH)` — IST-local, and `DATE_TRUNC` on a bare `TIMESTAMP` is a parse error.

### ✅ Gate K

- [ ] All three render from live BigQuery
- [ ] Monthly separates **job mix** from **failure mix** — they are different populations; water shutoff is a job, not a failure mode
- [ ] Every number traces to a query

---

## Stage L · Rehearsal

| Check | Bar |
|---|---|
| Latency, Act 3 | < 18 s **with** a visible trace; < 10 s without |
| Map | Renders at the decided tier, every time, from cold |
| Fallbacks | Tier 3 / 3b rehearsed, and the spoken line for it rehearsed too |
| Refusal | `GK-141` rehearsed as a **highlight**, not an apology |
| Integrity | The synthetic-data disclosure said **out loud** and shown on screen |
| Assumptions | `N_RIGS = 15` stated as **Assam-Asset-wide**, not Geleki's allocation (`D-13`) |
| Q&A | [`demo_flow.md`](./demo_flow.md) §7 — including *"how is this different from WellEx?"* |

---

## Definition of done

- [ ] Every `spec/08` acceptance test passes
- [ ] Every number on screen traces to a tool call or a query
- [ ] The agent refuses at least once, on purpose, and explains why
- [ ] Nothing unsourced appears anywhere — see [`research_appendix.md`](./research_appendix.md) §3
- [ ] Deployed to Agent Runtime, published to Gemini Enterprise, rehearsed end to end **inside Gemini Enterprise**

---

## Open items that gate this plan

| # | Item | Owner | Blocks |
|---|---|---|---|
| 1 | **The demo date** | Assumed: 2026-10-14 | Governs schedule; 3-week build window assumed |
| 2 | **`D-15`** — availability arithmetic derivation | ✅ **CLOSED 2026-09-23** | Was: Gate C. Re-derived two-population in `spec/00` §5.2 |
| 3 | **`D-16`** — taxonomy is SRP-only | ✅ **CLOSED 2026-09-23** | Was: Gate C. Scoped in `spec/00` §5.3, gas-lift taxonomy in `spec/03` §6.2 |
| 4 | **`RISK-002`** — can the data include SPM, stroke length, plunger diameter, runtime, CHP? | ONGC | The `MS-011` fillage proxy, Stage E |
| 5 | **Does NETRA cover onshore Assam? Is WellEx scheduled for Assam Asset?** | ONGC | Positioning — complement or duplicate |
| 6 | **Who approves a workover in an onshore Asset today, on what cadence, with what inputs?** | ONGC | **One 20-minute call beats everything three research passes found** |
| 7 | Eleven refinements + `R-12`…`R-18` | ✅ **CLOSED** | Fully incorporated across spec set |
