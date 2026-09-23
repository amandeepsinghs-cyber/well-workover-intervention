"""
generator/wells.py

Generates well_master table (142 wells) for Geleki Field, Assam.
Adheres strictly to spec/02_data_contract.md (DC-001..DC-007b)
and spec/03_synthetic_data_spec.md (SD-011..SD-016).
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta

RANDOM_SEED = 42

def generate_well_master(n_wells: int = 142, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    
    well_ids = [f"GK-{i+1:03d}" for i in range(n_wells)]
    if n_wells >= 140:
        well_ids[138] = "GK-147"
        well_ids[139] = "GK-214"
    
    # Geleki field coordinates
    block_centers = [
        (26.980, 94.830, 0.45),  # Tipam Main High (North-East)
        (26.955, 94.805, 0.35),  # Central Fault Block
        (26.935, 94.780, 0.20),  # South-West Flank
    ]
    
    lats = []
    lons = []
    for _ in range(n_wells):
        c_idx = rng.choice(len(block_centers), p=[b[2] for b in block_centers])
        c_lat, c_lon, _ = block_centers[c_idx]
        d_lat = rng.normal(0, 0.012)
        d_lon = d_lat * 0.8 + rng.normal(0, 0.008)
        lats.append(round(c_lat + d_lat, 6))
        lons.append(round(c_lon + d_lon, 6))
        
    start_date = date(1968, 1, 1)
    end_date = date(2015, 12, 31)
    total_days = (end_date - start_date).days
    
    beta_draws = rng.beta(2.0, 5.0, size=n_wells)
    completion_dates = [start_date + timedelta(days=int(b * total_days)) for b in beta_draws]
    spud_dates = [comp - timedelta(days=int(rng.integers(60, 180))) for comp in completion_dates]
    
    zones = rng.choice(['Tipam', 'Barail', 'Lakadong'], size=n_wells, p=[0.45, 0.35, 0.20])
    
    perf_top_m = []
    perf_bottom_m = []
    total_depth_md_m = []
    total_depth_tvd_m = []
    
    for z in zones:
        if z == 'Tipam':
            raw_top = rng.normal(2750, 180)
            top = float(np.clip(raw_top, 2400.0, 3100.0))
        elif z == 'Barail':
            raw_top = rng.normal(3300, 250)
            top = float(np.clip(raw_top, 2900.0, 3700.0))
        else:
            raw_top = rng.normal(3900, 280)
            top = float(np.clip(raw_top, 3500.0, 4377.0))
            
        top = round(top, 1)
        bot = round(top + rng.uniform(12.0, 60.0), 1)
        td_md = round(bot + rng.uniform(15.0, 90.0), 1)
        td_tvd = round(td_md * (1.0 - rng.uniform(0.005, 0.030)), 1)
        
        perf_top_m.append(top)
        perf_bottom_m.append(bot)
        total_depth_md_m.append(td_md)
        total_depth_tvd_m.append(td_tvd)
        
    fixture_srp_ids = {
        "GK-129", "GK-141", "GK-103", "GK-112",
        "GK-087", "GK-055", "GK-147", "GK-214", "GK-117"
    }
    lift_types = list(rng.choice(['SRP', 'GAS_LIFT', 'NATURAL'], size=n_wells, p=[0.70, 0.20, 0.10]))
    for idx, wid in enumerate(well_ids):
        if wid in fixture_srp_ids:
            lift_types[idx] = 'SRP'
            if wid in {"GK-129", "GK-141", "GK-214"}:
                zones[idx] = 'Tipam'
    
    pump_setting_depth_m = []
    plunger_diameter_in = []
    stroke_length_in = []
    rod_string_grade = []
    pump_type = []
    casing_vented = []
    
    for i, lt in enumerate(lift_types):
        if lt == 'SRP':
            psd = round(perf_top_m[i] - rng.uniform(30.0, 150.0), 1)
            if psd > 2000.0:
                p_diam = float(rng.choice([1.25, 1.50]))
            else:
                p_diam = float(rng.choice([1.25, 1.50, 1.75, 2.00]))
                
            s_len = float(rng.choice([54.0, 64.0, 74.0, 86.0, 100.0]))
            if well_ids[i] == "GK-055":
                p_diam = 1.50
                s_len = 74.0
            r_grade = str(rng.choice(['C', 'D', 'K'], p=[0.20, 0.50, 0.30]))
            p_typ = str(rng.choice(['INSERT', 'TUBING'], p=[0.75, 0.25]))
            is_vented = False if well_ids[i] in fixture_srp_ids else bool(rng.choice([False, True], p=[0.88, 0.12]))
            
            pump_setting_depth_m.append(psd)
            plunger_diameter_in.append(p_diam)
            stroke_length_in.append(s_len)
            rod_string_grade.append(r_grade)
            pump_type.append(p_typ)
            casing_vented.append(is_vented)
        else:
            pump_setting_depth_m.append(None)
            plunger_diameter_in.append(None)
            stroke_length_in.append(None)
            rod_string_grade.append(None)
            pump_type.append(None)
            casing_vented.append(False)
            
    tubing_sizes = [2.875 if rng.random() > 0.3 else 3.5 for _ in range(n_wells)]
    casing_sizes = [5.5 if rng.random() > 0.25 else 7.0 for _ in range(n_wells)]
    
    n_idle = int(round(0.045 * n_wells))
    non_fixture_indices = [i for i, wid in enumerate(well_ids) if wid not in fixture_srp_ids]
    idle_indices = set(rng.choice(non_fixture_indices, size=n_idle, replace=False))
    statuses = ['IDLE' if i in idle_indices else 'ACTIVE' for i in range(n_wells)]
    
    # MS-022: DLS is NULL throughout synthetic dataset (1968-vintage vertical wells)
    max_dls = [None for _ in range(n_wells)]
    
    df_wells = pd.DataFrame({
        'well_id': well_ids,
        'field': 'Geleki',
        'asset': 'Assam',
        'latitude': lats,
        'longitude': lons,
        'spud_date': spud_dates,
        'completion_date': completion_dates,
        'current_zone': zones,
        'perf_top_m': perf_top_m,
        'perf_bottom_m': perf_bottom_m,
        'total_depth_md_m': total_depth_md_m,
        'total_depth_tvd_m': total_depth_tvd_m,
        'max_dls_deg_30m': max_dls,
        'lift_type': lift_types,
        'plunger_diameter_in': plunger_diameter_in,
        'stroke_length_in': stroke_length_in,
        'pump_setting_depth_m': pump_setting_depth_m,
        'rod_string_grade': rod_string_grade,
        'pump_type': pump_type,
        'casing_vented': casing_vented,
        'tubing_size_in': tubing_sizes,
        'casing_size_in': casing_sizes,
        'status': statuses
    })
    
    return df_wells

if __name__ == '__main__':
    df = generate_well_master()
    print(f"Generated {len(df)} wells.")
    print("Lift types:\n", df['lift_type'].value_counts(normalize=True))
    print("Zones:\n", df['current_zone'].value_counts(normalize=True))
    print("Status:\n", df['status'].value_counts(normalize=True))
