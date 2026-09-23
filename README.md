# Workover & Well Intervention Candidate Ranking Agent (`P08-WORKOVER-OPTIMIZER`)

**Target Asset:** ONGC Assam Asset — Geleki Field (142 wells: Tipam, Barail, Girujan, Lakwa sands)  
**Framework:** Google Agent Development Kit (`google-adk==2.9.2`) · **Model:** `gemini-2.5-pro`  
**Cloud Runtime (`asia-south1`):** `projects/349946979746/locations/asia-south1/reasoningEngines/8982649359116009472`  
**Gemini Enterprise Agent ID:** `9133818840672638712` (`oil-and-gas-agentic-transformation`)  
**BigQuery Datasets (`asia-south1`):** `og-agentic-ecosystem:geleki_raw` (Bronze) & `og-agentic-ecosystem:geleki` (Curated Gold — 13 tables, 167,894 rows)  
**GCS Data Lake (`ASIA`):** `gs://well-workover-intervention-data`

---

## 1. How to Test the Agent (3 Options)

### Option A — Test Live in Gemini Enterprise (Recommended for Executive Demo)
1. Open the [**Gemini Enterprise Dashboard (`oil-and-gas-agentic-transformation`)**](https://console.cloud.google.com/gemini-enterprise/locations/global/engines/oil-and-gas-agentic-transf_1788683272432/overview/dashboard?project=og-agentic-ecosystem).
2. Open the **Preview / Web App** and select **`Workover & Well Intervention Candidate Ranking Agent`**.
3. Copy-paste any of the **8 Golden Test Q&As** below.

### Option B — Test Live in Vertex AI Agent Engine Playground
1. Open the [**Vertex AI Reasoning Engine Console (`8982649359116009472`)**](https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/asia-south1/agent-engines/8982649359116009472?project=og-agentic-ecosystem).
2. Click the **Playground** tab and enter any prompt from Section 2 below.

### Option C — Test Locally (ADK Web UI, CLI, or Automated Pytest Suite)
```bash
# 1. Run all 10 deterministic & ADK contract tests
uv run pytest tests/test_contracts.py -v

# 2. Launch the interactive local ADK Web UI (http://localhost:8080)
uv run adk web . --port 8080

# 3. Or chat in the terminal via ADK CLI
uv run adk run agent
```

---

## 2. Complete Golden Q&A Test Script (Copy-Paste Prompts & Expected Answers)

### Q1 · Act 1 — Spatial Field Map (`AS-010` / `TC-016`)
**Copy-Paste Prompt:**
> `Show me all producing wells in the Geleki field on a map, sized by current oil rate and coloured by well status.`

* **Expected Tool Call:** `adk_render_map(field="Geleki", size_by="oil_rate_bopd", colour_by="trigger_state")`
* **Expected Answer Highlights:**
  * Renders all **142 Geleki wells** inside `geleki_boundary.geojson` (zero fabricated coordinates).
  * Reports exact trigger state breakdown: **119 `GREEN`** (normal), **16 `AMBER`** (watch), and **7 `RED`** (critical intervention candidates: `GK-129`, `GK-141`, `GK-103`, `GK-112`, `GK-087`, `GK-055`, `GK-147`).
  * Declares the active render tier (`TIER_1_VEGA_GEOSHAPE`).

---

### Q2 · Act 2a — 3-Year Production & Historical Workover Overlay (`AS-011` / `TC-017`)
**Copy-Paste Prompt:**
> `Plot the oil, water and liquid production for GK-129 over the last three years, and show its water cut.`

* **Expected Tool Call:** `adk_plot_production(well_id="GK-129", months=36)`
* **Expected Answer Highlights:**
  * Summarizes 36 months of daily production (`>900` producing days) with shut-in intervals preserved as gaps (never plotted as zero rate).
  * Explicitly marks the **2019-06-14 Water Shut-Off Squeeze (`WSO_SQUEEZE`)** and highlights that its outcome was **`FAILED`** (water cut rebounded from 88% to 79% within 45 days due to packer bypass across the 2,890–2,898 m MD unbonded cement interval).

---

### Q3 · Act 2b — The Mature-Field Rate-Ranking Push-Back (`AS-012` / `TC-018`)
**Copy-Paste Prompt:**
> `Which are my lowest producing wells in Geleki?`

* **Expected Tool Calls:** `adk_query_wells(order_by="oil_rate_bopd", direction="ASC", limit=5)` **AND** `adk_query_wells(order_by="decline_residual_pct", direction="ASC", limit=5)`
* **Expected Answer Highlights (3-Part Normative Response):**
  1. **Literal Answer:** Lists the 5 lowest absolute oil rate wells (`oil_rate_bopd`).
  2. **Mandatory Engineering Caveat:** Explicitly states that *ranking mature wells by lowest absolute oil rate is misleading because a low-rate Barail/Girujan well may be performing at 100% of its natural Arps decline curve, whereas a higher-rate Tipam well with a -60% residual represents recoverable deferred barrels.*
  3. **Residual-Ranked Table:** Presents the top 5 wells ranked by **Arps decline residual (`decline_residual_pct`)** showing Actual BOPD, Expected Arps BOPD, Gap BOPD, and Residual % (`GK-129` at `-60.5%`, `GK-087` at `-58.1%`, `GK-112` at `-52.4%`, `GK-103` at `-46.2%`, `GK-055` at `-41.0%`).

---

### Q4 · Act 3 — Full 10-Tool Diagnostic & Candidate Ranking (`AS-013` / `TC-001`..`TC-010`)
**Copy-Paste Prompt:**
> `Which Geleki wells need intervention, when is each one likely to fail, and what job does each need?`

* **Expected Tool Call Sequence:** `adk_fit_decline`, `adk_chan_diagnostic`, `adk_fillage_proxy`, `adk_check_offsets`, `adk_detect_mechanical`, `adk_predict_failure`, `adk_route_intervention`, `adk_estimate_uplift`, `adk_rank_candidates`
* **Expected Answer Highlights:**
  * Separates candidates into **Rig Workover Queue** (`RIG`) vs **Rigless Campaign Queue** (`RIGLESS`) ranked by **Expected Net Value per Rig Day (`INR Lakhs / Rig-Day`)**:
    * **Rig Queue (`RIG`):**
      1. **`GK-129`** (`CHANNELLING`, positive log-log WOR′ slope `+0.78`, `ISOLATED_WELL` offset verdict) → **`WSO_SQUEEZE` (`RIG`, 7 days)**, +45.0 BOPD uplift.
      2. **`GK-087`** (`TUBING_LEAK`, `ISOLATED_WELL`) → **`TUBING_REPLACEMENT` (`RIG`, 5 days)**, +38.0 BOPD uplift.
      3. **`GK-055`** (`PUMP_WEAR`, SRP volumetric fillage efficiency dropped to `65.2%`, gap `27.3 BLPD`, CoxPH 30-day survival `42%`) → **`SRP_PUMP_CHANGE` (`RIG`, 4 days)**, +28.0 BOPD uplift.
    * **Rigless Queue (`RIGLESS` — 0 Rig Days):**
      1. **`GK-103`** (`CONING`, negative log-log WOR′ slope `-0.62`) → **`CHOKE_BACK_OPT` (`RIGLESS`, 1 day)**, +18.0 BOPD uplift.
      2. **`GK-112`** (`WAX_RESTRICTION`) → **`HOT_OIL_CIRC` (`RIGLESS`, 1 day)**, +26.0 BOPD uplift.
      3. **`GK-147`** (`SCALE_RESTRICTION`) → **`ORGANIC_SOLVENT_SOAK` (`RIGLESS`, 2 days)**, +19.0 BOPD uplift.
  * **Mandatory Engineering Refusal (`GK-141`):** Explicitly lists **`GK-141` as `NO_JOB_JUSTIFIED`** because offset check (`adk_check_offsets("GK-141")`) returns **`RESERVOIR_DECLINE`** (simultaneous pressure and rate decline across surrounding Tipam T-2 injectors/offsets — a wellbore workover cannot fix regional reservoir depletion).

---

### Q5 · Act 3 Drill-Down — `GK-129` Workover Plan, Unstructured Citations & MRO Stockout (`TC-011`..`TC-013`)
**Copy-Paste Prompt:**
> `Build me the plan for GK-129. Why channelling rather than coning? Check materials availability as well.`

* **Expected Tool Calls:** `adk_chan_diagnostic("GK-129")`, `adk_search_well_history("GK-129")`, `adk_check_mro("WSO_SQUEEZE")`, `adk_generate_draft_plan("GK-129")`
* **Expected Answer Highlights:**
  * **Physics Justification (Chan SPE-30775):** WOR′ derivative log-log slope is **`+0.78` (positive)**, which is the normative signature of rapid channel breakthrough behind pipe (`CHANNELLING`), whereas water coning exhibits a **negative** WOR′ derivative slope (`-0.5` to `-1.0`).
  * **Cited Unstructured Reports (`gs://well-workover-intervention-data/docs/`):**
    * Cites **`DOC-CBL-GK-129-1998.txt`** (*1998-11-04 Cement Bond Log Report*) confirming poor cement bond index (`< 0.25`) across **2,890–2,898 m MD** above the Tipam T-3 shale barrier.
    * Cites **`DOC-SCAN-GK-129-2019.txt`** (*2019-06-14 Workover Completion Report*) explaining why the 2019 shallow cement squeeze failed (single-retainer set at 2,897 m MD bypassed through the unbonded 2,890–2,896 m MD channel) and recommends a **dual-retainer balanced micro-fine cement squeeze across the full 2,890–2,898 m MD interval**.
  * **MRO Logistics (`DC-081`):** Flags that `RET-7IN-10K` (7-inch High-Temp Cement Retainer) is **out of stock (`0` units) at `NAZIRA`**, but **`2` units are available at `SIVASAGAR`** warehouse (`+2 days` inter-warehouse transfer lead time).
  * **Governance Status:** Marks the draft plan as **`AWAITING REVIEW`** (never writes directly to SAP PM).

---

### Q6 · Pump Fillage & CoxPH Survival Deep-Dive (`GK-055` / `TC-003` & `TC-006`)
**Copy-Paste Prompt:**
> `Check the SRP pump fillage efficiency and failure survival forecast for GK-055.`

* **Expected Tool Calls:** `adk_fillage_proxy("GK-055")`, `adk_predict_failure("GK-055")`
* **Expected Answer Highlights:**
  * Theoretical SRP displacement: **`78.5 BLPD`** vs Actual liquid rate: **`51.2 BLPD`** → Gap of **`27.3 BLPD`** (**`65.2%` volumetric efficiency**, down from `83.4%` baseline `-18.2 pp`).
  * CoxPH (`coxph_srp_v1.pkl`, holdout C-index `0.7128`) forecasts median remaining run life of **`18 days`** (`90% CI: [9, 31] days`, 30-day survival probability `42%`).

---

### Q7 · Act 4 — Daily, Weekly & Monthly Executive Scorecard (`AS-014` / `TC-014`)
**Copy-Paste Prompt:**
> `Generate today's intervention report, and show me what the weekly and monthly versions look like.`

* **Expected Tool Calls:** `adk_generate_report(period="DAILY")`, `adk_generate_report(period="WEEKLY")`, `adk_generate_report(period="MONTHLY")`
* **Expected Answer Highlights:**
  * **Daily Brief:** Active status breakdown (`119 GREEN`, `16 AMBER`, `7 RED`), `11` excluded stale/untested wells named explicitly (`AS-020`), and `data_as_of = 2026-09-21` (`data_lag_days = 2`, `AS-017`).
  * **Weekly Campaign Plan:** 3-rig allocation (`ONG-RIG-01` -> `GK-129`, `ONG-RIG-02` -> `GK-087`, `ONG-RIG-03` -> `GK-055`) plus parallel rigless schedule (`GK-112`, `GK-103`, `GK-147`).
  * **Monthly Executive Scorecard:** Includes the mandatory **"Where the system was wrong"** calibration section (`TC-014.2`) auditing historical false positives (`GK-117` polymer squeeze overridden after fresh CBL) and uplift estimation residuals.

---

### Q8 · Act 5 — Constrained Rig Schedule & Force-Include Trade-Off (`AS-015` / `TC-015`)
**Copy-Paste Prompt:**
> `Build next month's workover plan for Geleki using the available rigs. What falls off if we force-include GK-114?`

* **Expected Tool Call:** `adk_schedule_rigs(horizon_days=30, force_include_csv="GK-114")`
* **Expected Answer Highlights:**
  * Explicitly states the rig fleet assumption (**`3` workover rigs allocated to Geleki** out of the 15-rig Assam Asset fleet: `ONG-RIG-01`, `ONG-RIG-02`, `ONG-RIG-03`).
  * Shows that force-including `GK-114` (`+11 BOPD`) displaces **`GK-055` (`+28 BOPD`)** from `ONG-RIG-03`, resulting in a **net loss of `-17 BOPD` (`-510 bbl` over 30 days)**, and advises against displacing `GK-055` or attempting to swap with a rigless job (since rigless jobs consume zero rig days).
