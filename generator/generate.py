"""
generator/generate.py

Master data generator for Geleki Field (Assam Asset).
Generates all 13 contract tables, enforces the 7 demo fixtures,
validates invariants, and exports Parquet/CSV files into data/landing/.
"""

import os
import shutil
import pandas as pd
from datetime import date

from generator.wells import generate_well_master
from generator.production import simulate_production_history
from generator.job_catalogue import generate_job_catalogue
from generator.supporting import (
    generate_well_offsets,
    generate_mro_inventory,
    generate_rig_calendar,
    generate_document_index,
    generate_well_run,
    generate_draft_plan_table,
    generate_decision_log,
    materialize_raw_documents,
)

LANDING_DIR = "data/landing"

def main():
    print("=" * 60)
    print("Geleki Well Intervention Dataset Generator (13 Contract Tables)")
    print("=" * 60)
    
    os.makedirs(LANDING_DIR, exist_ok=True)
    
    # 1. well_master (142 wells)
    print("Generating well_master (142 wells)...")
    df_wells = generate_well_master(142)
    
    # 2. job_catalogue (28 jobs)
    print("Generating job_catalogue (28 rows)...")
    df_jobs = generate_job_catalogue()
    
    # 3. daily_production, well_tests, well_status_history, workover_history
    print("Simulating 36 months production, status episodes & workover history...")
    df_daily, df_tests, df_status, df_workover = simulate_production_history(
        df_wells,
        start_date=date(2023, 10, 1),
        end_date=date(2026, 9, 30)
    )
    
    # 4. supporting tables
    print("Generating well_offsets...")
    df_offsets = generate_well_offsets(df_wells)
    
    print("Generating mro_inventory...")
    df_mro = generate_mro_inventory()
    
    print("Generating rig_calendar...")
    df_rigs = generate_rig_calendar()
    
    print("Generating document_index & materializing unstructured reports...")
    df_docs = generate_document_index(df_wells)
    n_raw_docs = materialize_raw_documents(df_docs, out_dir="data/raw/docs")
    print(f"  -> Materialized {n_raw_docs} report files in data/raw/docs/")

    # 5. Derived spine & feedback tables (well_run, draft_plan, decision_log)
    print("Generating well_run (142 rows), draft_plan, and decision_log...")
    df_well_run = generate_well_run(df_wells, df_daily, run_date=date(2026, 9, 23))
    df_draft_plan = generate_draft_plan_table(df_well_run)
    df_decision_log = generate_decision_log()
    
    # 6. Export all 13 tables with the 4 lineage columns (build.md §C.3)
    tables = {
        'well_master': df_wells,
        'daily_production': df_daily,
        'well_tests': df_tests,
        'well_status_history': df_status,
        'workover_history': df_workover,
        'job_catalogue': df_jobs,
        'well_offsets': df_offsets,
        'mro_inventory': df_mro,
        'rig_calendar': df_rigs,
        'document_index': df_docs,
        'well_run': df_well_run,
        'draft_plan': df_draft_plan,
        'decision_log': df_decision_log,
    }
    
    print(f"\nExporting {len(tables)} tables to {LANDING_DIR} (with lineage metadata)...")
    for t_name, df in tables.items():
        df_out = df.copy()
        df_out['_ingested_at'] = "2026-09-23T16:00:00Z"
        df_out['_source_system'] = "GENERATOR"
        df_out['_source_file'] = f"gs://well-workover-intervention-data/landing/generator/2026/09/23/{t_name}.parquet"
        df_out['_batch_id'] = "BATCH-GELEKI-20260923-V1"
        parquet_path = os.path.join(LANDING_DIR, f"{t_name}.parquet")
        csv_path = os.path.join(LANDING_DIR, f"{t_name}.csv")
        df_out.to_parquet(parquet_path, index=False)
        df_out.to_csv(csv_path, index=False)
        print(f"  -> {t_name:20s}: {len(df_out):7d} rows saved.")
        
    print("\nGeneration completed successfully.")

if __name__ == '__main__':
    main()

