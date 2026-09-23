"""
generator/supporting.py

Generates:
  - well_offsets (DC-080: k=6 nearest neighbours, spatial distance, same_zone)
  - mro_inventory (DC-081: Nazira & Sivasagar bases, planned stock-out fixture)
  - rig_calendar (DC-082, DC-083: 15 Assam rigs, capabilities)
  - document_index (DC-084: historical scan records)
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta
from scipy.spatial.distance import cdist

RANDOM_SEED = 42

def generate_well_offsets(df_wells: pd.DataFrame) -> pd.DataFrame:
    coords = df_wells[['latitude', 'longitude']].to_numpy()
    # Approx distance in metres (1 deg lat ~ 111,000m, 1 deg lon ~ 100,000m at 27N)
    scale = np.array([111000.0, 100000.0])
    scaled_coords = coords * scale
    dist_mat = cdist(scaled_coords, scaled_coords)
    
    records = []
    n = len(df_wells)
    well_ids = df_wells['well_id'].tolist()
    zones = df_wells['current_zone'].tolist()
    k_neighbors = min(6, n - 1)
    
    for i in range(n):
        w_id = well_ids[i]
        z = zones[i]
        dists = dist_mat[i]
        
        nearest = np.argsort(dists)
        nearest = [idx for idx in nearest if idx != i][:k_neighbors]
        
        for rank, j in enumerate(nearest, start=1):
            records.append({
                'well_id': w_id,
                'offset_well_id': well_ids[j],
                'distance_m': round(float(dists[j]), 1),
                'same_zone': bool(z == zones[j]),
                'rank': rank
            })
            
    return pd.DataFrame(records)

def generate_mro_inventory() -> pd.DataFrame:
    items = [
        ("SRP_PLUNGER_150", "Insert Pump Plunger 1.50 in", 15, 0, "NAZIRA"),
        ("SRP_PLUNGER_125", "Insert Pump Plunger 1.25 in", 8, 0, "NAZIRA"),
        ("SRP_VALVE_ROD", "Valve Rod Assembly", 12, 0, "NAZIRA"),
        ("ROD_GRADE_D_78", "Sucker Rod Grade D 7/8 in (box of 50)", 25, 0, "NAZIRA"),
        ("ROD_GRADE_K_78", "Sucker Rod Grade K 7/8 in (box of 50)", 10, 0, "NAZIRA"),
        ("TUBING_J55_278", "Tubing 2-7/8 in J-55 (joints)", 120, 0, "NAZIRA"),
        ("TUBING_L80_278", "Tubing 2-7/8 in L-80 (joints)", 80, 0, "NAZIRA"),
        ("PARAFFIN_SOLVENT_BBL", "Paraffin Solvent Blend (Barrels)", 40, 0, "NAZIRA"),
        ("SCALE_INHIBITOR_DRUM", "Scale Inhibitor Chemical (Drums)", 20, 0, "NAZIRA"),
        ("CEMENT_RETAINER_55", "Mechanical Cement Retainer 5.5 in", 0, 0, "NAZIRA"),
        ("CEMENT_RETAINER_55", "Mechanical Cement Retainer 5.5 in", 4, 2, "SIVASAGAR"),
        ("BRIDGE_PLUG_55", "Cast Iron Bridge Plug 5.5 in", 6, 0, "NAZIRA"),
        ("POLISHED_ROD_125", "Polished Rod 1-1/4 in x 26 ft", 5, 0, "NAZIRA"),
        ("GAS_LIFT_VALVE_1IN", "Operating Gas Lift Valve 1 in", 18, 0, "NAZIRA"),
        ("GAS_LIFT_ORIFICE_1IN", "Gas Lift Orifice Valve 1 in", 12, 0, "NAZIRA"),
    ]
    
    records = []
    for code, name, qty, transit, base in items:
        records.append({
            'item_code': code,
            'item_name': name,
            'base': base,
            'qty_on_hand': qty,
            'transit_days': transit
        })
    return pd.DataFrame(records)

def generate_rig_calendar(start_date: date = date(2026, 9, 1), end_date: date = date(2026, 10, 31)) -> pd.DataFrame:
    rig_configs = [
        (f"RIG-ASSAM-{i:02d}", "PULLING_UNIT") for i in range(1, 6)
    ] + [
        (f"RIG-ASSAM-{i:02d}", "CLASS_I") for i in range(6, 12)
    ] + [
        (f"RIG-ASSAM-{i:02d}", "CLASS_II") for i in range(12, 16)
    ]
    
    n_days = (end_date - start_date).days + 1
    dates = [start_date + timedelta(days=d) for d in range(n_days)]
    
    rng = np.random.default_rng(RANDOM_SEED)
    records = []
    for rig_id, r_class in rig_configs:
        status_pool = ['COMMITTED'] * 65 + ['AVAILABLE'] * 20 + ['MOVING'] * 10 + ['MAINTENANCE'] * 5
        for d in dates:
            st = rng.choice(status_pool)
            well = f"GK-{rng.integers(1, 143):03d}" if st == 'COMMITTED' else None
            records.append({
                'rig_id': rig_id,
                'date': d,
                'status': st,
                'well_id': well,
                'rig_class': r_class
            })
    return pd.DataFrame(records)

def generate_document_index(df_wells: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    records = []
    
    n_sample = min(35, len(df_wells))
    for _, row in df_wells.sample(n_sample, random_state=RANDOM_SEED).iterrows():
        records.append({
            'doc_id': f"DOC-COMP-{row['well_id']}",
            'well_id': row['well_id'],
            'doc_type': 'COMPLETION_REPORT',
            'doc_date': row['completion_date'],
            'gcs_uri': f"gs://well-workover-intervention-data/documents/completion/{row['well_id']}_completion.pdf",
            'title': f"Well Completion & CBL Report {row['well_id']}",
            'has_text_layer': bool(row['completion_date'].year > 2005)
        })
        
    records.append({
        'doc_id': "DOC-CBL-GK129-1998",
        'well_id': "GK-129",
        'doc_type': 'WORKOVER_REPORT',
        'doc_date': date(1998, 4, 15),
        'gcs_uri': "gs://well-workover-intervention-data/documents/workover/GK129_1998_CBL_scan.pdf",
        'title': "Cement Bond Log & Micro-Annulus Report GK-129 (1998)",
        'has_text_layer': False
    })
    
    field_docs = [
        ("DOC-FIELD-TIPAM-GEOL-2012", "Tipam Sand Reservoir Geological Study Geleki", "COMPLETION_REPORT", date(2012, 6, 1)),
        ("DOC-FIELD-WATERFLOOD-HIST", "History of Water Injection in Geleki Asset", "OTHER", date(2018, 3, 15)),
        ("DOC-FIELD-ASSET-RIG-SCHEDULE", "Assam Asset Rig Deployment Matrix 2025-2026", "OTHER", date(2025, 12, 10)),
        ("DOC-FIELD-WAX-FLOWLINE-MAP", "Geleki Surface Flowline Wax Scraping Protocol", "OTHER", date(2021, 9, 20)),
        ("DOC-FIELD-CHAN-STUDY-2016", "Upper Assam Water Production Diagnostic Review", "OTHER", date(2016, 11, 5)),
    ]
    for doc_id, title, d_type, d_date in field_docs:
        records.append({
            'doc_id': doc_id,
            'well_id': None,
            'doc_type': d_type,
            'doc_date': d_date,
            'gcs_uri': f"gs://well-workover-intervention-data/documents/field/{doc_id}.pdf",
            'title': title,
            'has_text_layer': True
        })
        
    records.append({
        'doc_id': "DOC-SCAN-GK-129-2019",
        'well_id': "GK-129",
        'doc_type': 'WORKOVER_REPORT',
        'doc_date': date(2019, 5, 14),
        'gcs_uri': "gs://well-workover-intervention-data/docs/GK-129_2019_wso_report.pdf",
        'title': "GK-129 Workover Completion Report — Straddle Packer WSO (May 2019)",
        'has_text_layer': True
    })
        
    return pd.DataFrame(records)


def generate_well_run(df_wells: pd.DataFrame, df_daily: pd.DataFrame, run_date: date = date(2026, 9, 23)) -> pd.DataFrame:
    """Generates the 142-row nightly spine table well_run (spec/02 §7, DC-060..DC-072)."""
    import json

    df_day = df_daily[df_daily['production_date'] == run_date].set_index('well_id')
    df_90 = df_daily[(df_daily['production_date'] >= run_date - timedelta(days=90)) & (df_daily['production_date'] <= run_date)]

    demo_overrides = {
        "GK-129": ("FLAG", "CHANNELLING", "HIGH", "CHANNELLING", 1.08, 12.0, "WELL_SPECIFIC", 24.0, 14.0, 39.0, 0.042, "WSO_SQUEEZE", True, 7.0, 0.68, 24, 5840.0, 249.6, 35.7, 1, 1, "RIG", "CEMENT_RETAINER_55 out of stock at NAZIRA (+2d SIVASAGAR)", date(2026, 9, 25)),
        "GK-055": ("WATCH", "PUMP_WEAR", "HIGH", "NORMAL", 0.05, 27.3, "WELL_SPECIFIC", 31.0, 19.0, 48.0, 0.032, "SRP_PUMP_CHANGE", True, 3.0, 0.72, 45, 4690.0, 141.4, 47.1, 2, 2, "RIG", None, date(2026, 9, 24)),
        "GK-087": (None, "ROD_PART", "HIGH", "NORMAL", 0.04, 18.5, "WELL_SPECIFIC", 38.0, 22.0, 58.0, 0.026, "SRP_ROD_REPLACE", True, 2.5, 0.70, 38, 3410.0, 94.0, 37.6, 3, 3, "RIG", None, date(2026, 9, 24)),
        "GK-112": ("FLAG", "SCALE", "HIGH", "NORMAL", 0.02, 8.0, "WELL_SPECIFIC", 18.0, 10.0, 29.0, 0.055, "CHEM_SCALE_BULLHEAD", False, 1.5, 0.74, 31, 7420.0, 318.4, 212.3, 4, 1, "RIGLESS", None, date(2026, 9, 24)),
        "GK-147": ("FLAG", "WAX", "HIGH", "NORMAL", 0.03, 9.5, "WELL_SPECIFIC", 29.0, 17.0, 45.0, 0.034, "CHEM_HOT_OIL_ANNULUS", False, 1.5, 0.76, 42, 4520.0, 195.0, 130.0, 5, 2, "RIGLESS", None, date(2026, 9, 24)),
        "GK-103": ("WATCH", "CONING", "HIGH", "CONING", -0.42, 6.0, "WELL_SPECIFIC", 44.0, 26.0, 68.0, 0.022, "SURF_CHOKE_ADJ", False, 0.5, 0.78, 19, 2680.0, 121.6, 121.6, 6, 3, "RIGLESS", None, date(2026, 9, 24)),
        "GK-141": ("WATCH", "CHANNELLING_OR_INJECTOR_BREAKTHROUGH", "MEDIUM", "CHANNELLING", 0.61, 5.0, "RESERVOIR_DECLINE", 110.0, 70.0, 165.0, 0.009, "NO_JOB_JUSTIFIED", False, 0.0, 0.0, 0, 0.0, 0.0, 0.0, None, None, "NONE", None, None),
    }

    rows = []
    for _, w_row in df_wells.iterrows():
        wid = str(w_row['well_id'])
        w_90 = df_90[(df_90['well_id'] == wid) & (df_90['is_producing'] == True)]
        tested_90 = int((w_90['data_source'] == 'TESTED').sum()) if len(w_90) > 0 else 0
        data_as_of = w_90['production_date'].max() if len(w_90) > 0 else run_date
        lag_days = int((run_date - data_as_of).days)

        if wid in demo_overrides:
            (ta, mech, m_conf, c_cls, c_slp, f_gap, off_v, ettf, ci_l, ci_h, haz, j_code, req_r, dur_d, p_s, p_n, def_b, net_v, prio, r_ov, r_q, q_name, blk, e_start) = demo_overrides[wid]
            tb = (wid == "GK-087")
            tc = mech
            td = True
        else:
            ta, tb, tc, td = None, False, None, False
            mech, m_conf, c_cls, c_slp, f_gap, off_v = None, "HIGH", "NORMAL", 0.02, 4.5, "WELL_SPECIFIC"
            ettf, ci_l, ci_h, haz = 155.0, 95.0, 225.0, 0.006
            j_code, req_r, dur_d, p_s, p_n, def_b, net_v, prio = None, False, 0.0, 0.68, 25, 0.0, 0.0, 0.0
            r_ov, r_q, q_name, blk, e_start = None, None, "NONE", None, None

        trace_json = json.dumps([
            {"tool": "TC-001:fit_decline_curve", "well_id": wid, "status": "OK"},
            {"tool": "TC-007:trigger_scan", "well_id": wid, "status": "OK"},
        ])

        rows.append({
            'run_date': run_date,
            'well_id': wid,
            'trigger_a': ta,
            'trigger_a_days': 21 if ta else 0,
            'trigger_a_residual_pct': -31.0 if wid == "GK-129" else (-22.0 if wid == "GK-141" else -2.5),
            'trigger_b': tb,
            'trigger_b_days_since': 195.0 if wid == "GK-087" else 95.0,
            'trigger_b_p50_days': 179.0 if wid == "GK-087" else 185.0,
            'trigger_c': tc,
            'trigger_d': td,
            'mechanism': mech,
            'mechanism_confidence': m_conf,
            'chan_class': c_cls,
            'chan_wor_slope': c_slp,
            'fillage_gap_blpd': f_gap,
            'offset_verdict': off_v,
            'rejected_mechanisms': json.dumps(["CONING"] if wid == "GK-129" else []),
            'ettf_days': ettf,
            'ettf_ci_low': ci_l,
            'ettf_ci_high': ci_h,
            'hazard': haz,
            'recommended_job_code': j_code,
            'requires_rig': req_r,
            'est_duration_days': dur_d,
            'p_success': p_s,
            'p_success_n': p_n,
            'deferred_bbl_avoided': def_b,
            'net_value': net_v,
            'priority': prio,
            'rank_overall': r_ov,
            'rank_within_queue': r_q,
            'queue': q_name,
            'logistics_blocker': blk,
            'earliest_start_date': e_start,
            'tool_trace': trace_json,
            'model_version': "coxph-v1.0-geleki",
            'config_version': "1.0.0-geleki",
            'data_as_of': data_as_of,
            'data_lag_days': lag_days,
            'run_confidence': "LOW_CONFIDENCE" if lag_days > 3 else "NORMAL",
            'confidence_reason': "Data lag > 3 days" if lag_days > 3 else None,
            'tested_days_90d': tested_90,
            'allocation_basis_id': f"GGS-BASIS-2026Q3-{wid}",
        })
    return pd.DataFrame(rows)


def generate_draft_plan_table(df_well_run: pd.DataFrame) -> pd.DataFrame:
    """Generates draft_plan table (spec/02 §8) for flagged wells."""
    flagged = df_well_run[df_well_run['recommended_job_code'].notna()].copy()
    records = []
    for idx, r in flagged.iterrows():
        wid = str(r['well_id'])
        records.append({
            'draft_plan_id': f"PLAN-{wid}-20260923",
            'run_date': r['run_date'],
            'well_id': wid,
            'recommended_job_code': r['recommended_job_code'],
            'queue': r['queue'],
            'requires_rig': bool(r['requires_rig']),
            'approval_status': 'AWAITING REVIEW',
            'why_this_well_now': f"Residual {r['trigger_a_residual_pct']}% with diagnosed mechanism {r['mechanism']}.",
            'selection_evidence': f"Offset verdict={r['offset_verdict']}, Chan WOR' slope={r['chan_wor_slope']}.",
            'rejected_alternative_code': 'WSO_STRADDLE' if wid == 'GK-129' else 'NONE',
            'rejected_alternative_reason': 'May 2019 straddle packer failed at 14 months due to poor primary cement sheath.' if wid == 'GK-129' else 'N/A',
            'deferred_bbl_avoided_12mo': float(r['deferred_bbl_avoided']),
            'logistics_blocker': r['logistics_blocker'],
            'earliest_start_date': r['earliest_start_date'],
        })
    return pd.DataFrame(records)


def generate_decision_log() -> pd.DataFrame:
    """Generates historical decision_log table (spec/02 §9, DC-070..DC-072)."""
    rows = [
        ("DEC-2026-001", "PLAN-GK-129-20260923", "GK-129", date(2026, 9, 23), "2026-09-23T09:15:00Z", "asset_mgr_nazira", "APPROVE", "Confirmed 1998 CBL and 2019 straddle failure; approve rig cement squeeze.", "HISTORICAL_FAILURE_EVIDENCE", None),
        ("DEC-2026-002", "PLAN-GK-141-20260923", "GK-141", date(2026, 9, 23), "2026-09-23T09:22:00Z", "asset_mgr_nazira", "REJECT", "Agreed with NO_JOB_JUSTIFIED; all 6 Tipam offsets declining together.", "RESERVOIR_DEPLETION", None),
        ("DEC-2026-003", "PLAN-GK-055-20260923", "GK-055", date(2026, 9, 23), "2026-09-23T09:30:00Z", "prod_eng_geleki", "APPROVE", "Fluid pound confirmed by fillage proxy (65.2% eff) and rising CHP.", "MECHANICAL_WEAR", None),
        ("DEC-2026-004", "PLAN-GK-103-20260923", "GK-103", date(2026, 9, 23), "2026-09-23T09:40:00Z", "prod_eng_geleki", "MODIFY", "Bean down surface choke to 12/64th prior to chemical job.", "SURFACE_OPTIMISATION", "SURF_CHOKE_ADJ"),
    ]
    return pd.DataFrame(rows, columns=[
        'decision_id', 'draft_plan_id', 'well_id', 'run_date', 'decided_at',
        'decided_by', 'decision', 'reason_text', 'reason_category', 'modified_job_code'
    ])


def materialize_raw_documents(df_docs: pd.DataFrame, out_dir: str = "data/raw/docs") -> int:
    """Materializes text/markdown report artifacts in data/raw/docs/ for GCS upload and citation resolution."""
    import os
    os.makedirs(out_dir, exist_ok=True)
    for _, row in df_docs.iterrows():
        doc_id = str(row['doc_id'])
        wid = str(row['well_id']) if pd.notna(row['well_id']) else "FIELD_WIDE"
        fname = os.path.join(out_dir, f"{doc_id}.txt")
        with open(fname, "w", encoding="utf-8") as f:
            f.write(f"DOCUMENT ID: {doc_id}\n")
            f.write(f"TITLE      : {row['title']}\n")
            f.write(f"WELL ID    : {wid}\n")
            f.write(f"DATE       : {row['doc_date']}\n")
            f.write(f"GCS URI    : {row['gcs_uri']}\n")
            f.write("-" * 60 + "\n")
            if wid == "GK-129" and "1998" in str(row['doc_date']):
                f.write("FINDING: CBL amplitude 42-55 mV across 2795-2840m MD (Tipam TS-5A shale barrier), indicating channelled primary cement sheath behind 5.5-in casing.\n")
            elif wid == "GK-129" and "2019" in str(row['doc_date']):
                f.write("FINDING: Straddle packer set at 2812-2828m MD across TS-5A upper perfs. Post-job WC dropped to 54% for 14 months before annular bypass resumed behind poorly cemented casing. OUTCOME: FAILED at 14 months.\n")
            else:
                f.write(f"Archival ONGC Assam Asset engineering report for {wid} ({row['doc_type']}).\n")
    return len(df_docs)


if __name__ == '__main__':
    from generator.wells import generate_well_master
    wells = generate_well_master(10)
    offsets = generate_well_offsets(wells)
    mro = generate_mro_inventory()
    rigs = generate_rig_calendar()
    docs = generate_document_index(wells)
    print(f"Generated {len(offsets)} offset rows, {len(mro)} MRO items, {len(rigs)} rig days, {len(docs)} docs.")

