"""
generator/job_catalogue.py

Constructs the 28-row intervention job catalogue conforming to
spec/02_data_contract.md §7 and decision_architecture.md §3.1.
Enforces TC-008.6: exactly 8 genuinely rigless jobs on SRP wells.
"""

import pandas as pd

def generate_job_catalogue() -> pd.DataFrame:
    jobs = [
        # WAX
        ("WAX_SCRAPE", "Mechanical scraping", "WAX", "WAX",
         "THP rise, gradual liquid drop, prior wax history", True, "PULLING_UNIT", 1.5, 12.0),
        ("WAX_HOTOIL", "Hot oil / hot water wash", "WAX", "WAX",
         "THP rise, gradual liquid drop, seasonal correlation", False, "HOT_OILER", 0.5, 3.5),
        ("WAX_SOLVENT", "Solvent soak (xylene/toluene)", "WAX", "WAX",
         "Wax recurrence despite hot oil", False, "PUMP_TRUCK", 1.5, 6.0),
        ("WAX_INHIBITOR", "Wax inhibitor squeeze", "WAX", "WAX",
         ">=3 wax events in 12 months", False, "PUMP_TRUCK", 1.5, 8.0),
        ("WAX_HEATER", "Downhole heater install", "WAX", "WAX",
         "Continuous deep wax, severe recurrence", True, "WORKOVER_RIG", 2.5, 25.0),

        # MECHANICAL
        ("ROD_REPLACE", "Rod string replacement / part repair", "MECHANICAL", "ROD_PART",
         "Rate -> 0 instantaneously, CHP unchanged", True, "PULLING_UNIT", 1.5, 14.0),
        ("PUMP_OVERHAUL", "Pump changeout / overhaul", "MECHANICAL", "PUMP_WEAR",
         "Gradual liquid decline + CHP rise, fillage divergence", True, "PULLING_UNIT", 2.0, 18.0),
        ("TUBING_REPLACE", "Tubing leak repair / replacement", "MECHANICAL", "TUBING_LEAK",
         "Sharp drop over 3-5d, CHP flat, displacement gap", True, "WORKOVER_RIG", 3.5, 30.0),
        ("SURFACE_REPAIR", "Surface equipment repair", "MECHANICAL", "SURFACE",
         "Runtime hours collapse with no downhole signature", False, "SURFACE_CREW", 0.5, 2.0),
        ("LIFT_OPTIM", "Lift optimisation - SPM / stroke change", "MECHANICAL", "SURFACE",
         "Fillage proxy divergence without mechanical damage", False, "SURFACE_CREW", 0.5, 1.5),
        ("GAS_SEP_INSTALL", "Gas separator install / reset PSD", "MECHANICAL", "SURFACE",
         "Fillage loss with GOR rise", True, "PULLING_UNIT", 3.0, 20.0),
        ("LIFT_CONVERSION", "Lift conversion (resize/PCP/gas lift)", "MECHANICAL", "OTHER",
         "Repeated pump-off or over-capacity across >=2 cycles", True, "WORKOVER_RIG", 3.5, 45.0),

        # DEPOSITION & FILL
        ("SCALE_ACID_BULLHEAD", "Scale removal - acid bullhead", "DEPOSITION", "SCALE",
         "Flat production then sudden bind, high scaling index", False, "PUMP_TRUCK", 1.5, 8.5),
        ("SCALE_INHIBITOR", "Scale inhibitor squeeze", "DEPOSITION", "SCALE",
         "Recurrence, scaling index persistently > 0", False, "PUMP_TRUCK", 1.5, 7.0),
        ("SAND_CLEANOUT", "Sand cleanout / bailing", "DEPOSITION", "SAND",
         "Gradual decline, solids in fluid, wireline tags fill", True, "PULLING_UNIT", 2.5, 16.0),
        ("SAND_CONTROL", "Sand control screens / gravel pack", "DEPOSITION", "SAND",
         "Repeated cleanouts + accelerated pump wear", True, "WORKOVER_RIG", 7.0, 65.0),

        # INFLOW RESTORATION
        ("RE_PERFORATION", "Re-perforation", "INFLOW", "OTHER",
         "PI decline with static reservoir pressure intact", True, "WORKOVER_RIG", 3.0, 28.0),
        ("ADD_PERFORATION", "Add-perforation (extend interval)", "INFLOW", "OTHER",
         "Log-derived bypassed pay in current zone", True, "WORKOVER_RIG", 3.0, 32.0),
        ("MATRIX_ACID", "Matrix acidising / stimulation", "INFLOW", "OTHER",
         "PI decline, clean perfs, no fill", True, "WORKOVER_RIG", 2.0, 22.0),
        ("HYDRAULIC_FRAC", "Hydraulic fracturing / re-frac", "INFLOW", "OTHER",
         "Very low PI in tight zone despite clean perfs", True, "WORKOVER_RIG", 5.5, 95.0),
        ("ZONE_TRANSFER", "Zone transfer / behind-casing pay", "INFLOW", "OTHER",
         "Low fluid level + offsets depleted + pay on logs", True, "WORKOVER_RIG", 7.5, 70.0),

        # WATER CONTROL
        ("CHOKE_BACK", "Choke back / reduce drawdown (coning)", "WATER_CONTROL", "OTHER",
         "WOR prime negative slope", False, "SURFACE_CREW", 0.5, 1.0),
        ("CEMENT_SQUEEZE", "Cement squeeze + reperforation", "WATER_CONTROL", "OTHER",
         "WOR prime positive slope + step change in water cut", True, "WORKOVER_RIG", 6.5, 55.0),
        ("STRADDLE_PACKER", "Selective isolation / straddle packer", "WATER_CONTROL", "OTHER",
         "WOR prime plateau signature", True, "WORKOVER_RIG", 4.5, 40.0),
        ("POLYMER_GEL", "Polymer / gel treatment", "WATER_CONTROL", "OTHER",
         "WOR prime positive and prior squeeze failed", True, "WORKOVER_RIG", 4.0, 60.0),
        ("CASING_REPAIR", "Casing repair / patch / squeeze", "WATER_CONTROL", "OTHER",
         "Sudden water influx, abnormal annulus pressure", True, "WORKOVER_RIG", 7.0, 65.0),

        # TERMINAL
        ("NO_JOB_JUSTIFIED", "NO JOB JUSTIFIED (Reservoir decline)", "TERMINAL", "OTHER",
         "Decline fit clean, no mechanical signature, offsets declining identically", False, "SURFACE_CREW", 0.0, 0.0),
        ("PLUG_ABANDON", "Plug and abandon", "TERMINAL", "OTHER",
         "Rate < opex, offsets depleted, no behind-casing opportunity", True, "WORKOVER_RIG", 6.0, 45.0),
    ]

    columns = [
        "job_code", "job_name", "category", "mechanism_code",
        "selection_evidence", "requires_rig", "equipment", "est_days", "est_cost_lakh_inr"
    ]
    df = pd.DataFrame(jobs, columns=columns)
    return df

if __name__ == "__main__":
    df = generate_job_catalogue()
    print(f"Total jobs: {len(df)}")
    print(f"Rig jobs: {(df['requires_rig'] == True).sum()}, Rigless jobs: {(df['requires_rig'] == False).sum()}")
    print("Rigless jobs:\n", df[df['requires_rig'] == False][['job_code', 'job_name', 'equipment']])
