# Project Execution Checklist: Well Workover & Intervention AI Agent (Geleki Field, Assam)

This checklist tracks completed milestones, current gates, and remaining cloud deployment steps for the Well Workover & Intervention Agent on Gemini Enterprise.

---

## 🏁 Overview of Progress

```
[█████████████████████████░░░] ~90% Complete
- Stage A (Scaffolding & Spec):           100% COMPLETE
- Stage C (Data Generation & Invariants): 100% COMPLETE (Gate C Passed: 0 violations)
- Stage B (Map Renderer & Spikes):        100% COMPLETE (TC-016 + GeoJSON verified < 8s)
- Stage D (Analytical Tool Contracts):    100% COMPLETE (All 18 tools TC-001..TC-018 passing)
- Stage E (Survival Model Training):      100% COMPLETE (Gate E Passed: C-index 0.7128 vs 0.7061 Trigger B)
- Stage F (ADK Agent & Prompts):          100% COMPLETE (Agent, System Prompt, 10/10 pytest passing)
- Stage G (Cloud & Gemini Enterprise):      0% COMPLETE (Ready for human-approved cloud upload/publish)
```

---

## ✅ Completed Tasks

### 1. Requirements & System Architecture
- [x] Researched ONGC Geleki Field operational parameters, Assam geology, and workover economics.
- [x] Defined 4-turn Executive Director demo flow:
  1. Interactive Well Map (142 wells tagged by status/urgency via Vega-Lite).
  2. Single Well Diagnostic Deep-Dive (Arps decline & Chan WOR diagnostic on GK-214 / GK-129).
  3. Predictive Candidate Selection (Survival curve, job codes, refusal logic on GK-141).
  4. Basin Manager Weekly/Monthly Allocation Report (15 rigs + rigless capacity).
- [x] Authored 9 formal specification documents in `spec/` (`spec/00` to `spec/08`).
- [x] Authored architectural blueprints: `decision_architecture.md`, `model_data_foundation.md`, `thesis_risk_audit.md`, and `build.md`.

### 2. Environment & Project Foundation (Stage A)
- [x] Verified GCP project `og-agentic-ecosystem` and active account (`admin@amandeepsinghs.altostrat.com`).
- [x] Verified active Google Cloud Storage bucket: `gs://well-workover-intervention-data` (in `ASIA`).
- [x] Initialized Python 3.11 virtual environment using `uv`.
- [x] Installed core dependencies (`numpy`, `pandas`, `scipy`, `scikit-learn`, `lifelines`, `google-cloud-bigquery`, `google-cloud-storage`, `pyarrow`, `pytest`, `ruff`).
- [x] Created project directory layout: `generator/`, `data/landing/`, `data/geodata/`, `data/raw/`, `tools/`, `model/`, `agent/`, `tests/`.

### 3. Synthetic Data Engine & Gate C Closure (Stage C)
- [x] `generator/wells.py`: Generates 142 wells across 3 fault blocks, depth zones, lift types (70% SRP / 20% GL / 10% Natural), pump geometry (`DC-001`..`DC-007b`), and named demo fixtures (`GK-129`, `GK-141`, `GK-103`, `GK-112`, `GK-087`, `GK-055`, `GK-147`, `GK-214`).
- [x] `generator/job_catalogue.py`: 28 intervention jobs with rigless vs. rig classification conforming to `spec/02` §7 and `TC-008.6`.
- [x] `generator/supporting.py`: Well offsets (852 pairs), MRO inventory (15 items across Nazira/Sivasagar with stock-out fixture `DC-081`), rig calendar (15 rigs, 915 rig-days), document index (41 scan records).
- [x] `generator/production.py`: 36-month daily production simulation calibrated to `FRACTION_DOWN_ACTIVE = 16.02%` (target `16.3% ± 1.0pp`) and `FRACTION_DOWN_TOTAL = 19.57%` (target `20.0% ± 1.0pp`).
- [x] `generator/validate.py`: Gate C passes with 0 violations (`uv run python -m generator.validate`).

### 4. Visual & System Spikes (Stage B)
- [x] Created `data/geodata/geleki_boundary.geojson` with Geleki perimeter and 3 fault blocks (`Tipam Main High`, `Central Fault Block`, `South-West Flank`).
- [x] Implemented `tools/render_well_map.py` (`TC-016`) with 3-tier A2UI Vega-Lite fallback ladder (`TIER_1_VEGA_GEOSHAPE`, `TIER_2_VEGA_XY`, `TIER_3_STATIC_IMAGE`) and `< 8s` render latency.

### 5. Deterministic Analytical Tool Contracts (Stage D)
- [x] Implemented `tools/arps_decline.py` (`TC-001`): Weighted hyperbolic decline curve fitting (`TESTED` 3x vs `ALLOCATED` 1x) with transient and shut-in exclusions.
- [x] Implemented `tools/chan_diagnostic.py` (`TC-002`): Normative SPE-30775 log-log WOR & WOR′ derivative diagnostic with paired-injector branch (`TC-002.5`).
- [x] Implemented `tools/candidate_ranking.py` (`TC-003`..`TC-015`, `TC-017`, `TC-018`): Pump fillage proxy, offset refusal check (`GK-141` -> `NO_JOB_JUSTIFIED`), mechanical signatures, candidate ranking (`RIG` vs `RIGLESS` queues), MRO check (`DC-081` Nazira->Sivasagar), PDF history citation (`1998 CBL` & `2019 failed WSO`), draft plan (`AWAITING REVIEW`), reporting (`DAILY`/`WEEKLY`/`MONTHLY`), rig scheduler, and rate-ranking push-back caveat (`TC-018.2`).

### 6. Survival Model Baseline (Stage E)
- [x] Implemented `model/train.py` using `lifelines.CoxPHFitter` on right-censored SRP run-life episodes.
- [x] Cleared Gate E: Holdout C-index is **0.7128** (inside target honest band `0.65–0.72`) and beats Trigger B baseline (**0.7061**).
- [x] Exported model artifacts to `model/coxph_srp_v1.pkl` and `model/survival_model_metrics.json`.

### 7. ADK Agent Orchestrator & Acceptance Tests (Stage F)
- [x] Installed `google-adk==2.9.2` and wired `root_agent` as a `google.adk.agents.Agent` (`WorkoverPlannerAgent`) with all 18 JSON-safe tool wrappers in `agent/adk_tools.py` and `agent/agent.py`.
- [x] Created `tests/test_contracts.py` — `10/10` pytest acceptance tests pass (`uv run pytest -v`).

### 8. Cloud Ingestion to Argolis GCP (`og-agentic-ecosystem`)
- [x] Uploaded all 13 landing Parquet tables (`data/landing/*.parquet`), 42 unstructured well documents (`data/raw/docs/*.txt`), and Geleki GeoJSON (`data/geodata/geleki_boundary.geojson`) to `gs://well-workover-intervention-data` (`ASIA`).
- [x] Created BigQuery datasets `og-agentic-ecosystem:geleki_raw` and `og-agentic-ecosystem:geleki` (`asia-south1`) and loaded all 13 contract tables (167,894 total rows verified).

---

### 9. Stage G: Vertex AI Agent Runtime & Gemini Enterprise Deployment (`asia-south1`)
- [x] Provisioned dedicated service account `workover-agent@og-agentic-ecosystem.iam.gserviceaccount.com` and deployed `workover-optimizer` to Vertex AI Agent Runtime (`projects/349946979746/locations/asia-south1/reasoningEngines/8982649359116009472`).
- [x] Published `Workover & Well Intervention Candidate Ranking Agent` (`adk` registration mode) to Gemini Enterprise (`projects/349946979746/locations/global/collections/default_collection/engines/oil-and-gas-agentic-transf_1788683272432/assistants/default_assistant/agents/9133818840672638712`).


