
import sys
import os
import pandas as pd
import asyncio

# Add current directory to sys.path
sys.path.append(os.getcwd())

from backend import (
    fetch_webfleet_drivers,
    fetch_optidrive_scores_bulk,
    get_merged_vehicular_data,
    fetch_job_history_closed,
    fetch_jobs_created_between,
    calculate_conversion_metrics,
    rename_job_columns,
    sf_client
)

async def test():
    print("Testing Extended Data Fetching...")
    
    start_iso = "2026-02-01T00:00:00Z"
    end_iso = "2026-03-01T00:00:00Z"
    trades_tuple = ("HVAC", "Electrical")

    print(f"Period: {start_iso} to {end_iso}")
    
    # 1. Vehicular
    print("\n--- Testing Vehicular Data ---")
    try:
        df_drivers = fetch_webfleet_drivers()
        print(f"Webfleet Drivers: {len(df_drivers)}")
        if not df_drivers.empty:
            print("Driver Columns:", df_drivers.columns.tolist())
            
        df_scores = fetch_optidrive_scores_bulk()
        print(f"Optidrive Scores: {len(df_scores)}")
        
        df_merged = get_merged_vehicular_data()
        print(f"Merged Vehicular Data: {len(df_merged)}")
        if not df_merged.empty:
            print("Merged Columns:", df_merged.columns.tolist())
            print("Trade Groups found:", df_merged["Trade Group"].unique())
            print("Sample Trade Group:", df_merged["Trade Group"].iloc[0])
    except Exception as e:
        print(f"Vehicular Error: {e}")

    # 2. Conversion
    print("\n--- Testing Conversion Metrics ---")
    try:
        df_history = fetch_job_history_closed(start_iso, end_iso)
        print(f"Job History (Closed events): {len(df_history)}")
        if not df_history.empty:
            print("History Columns:", df_history.columns.tolist())
        
        df_jobs_month = fetch_jobs_created_between(trades_tuple, start_iso, end_iso)
        df_jobs_month = rename_job_columns(df_jobs_month)
        print(f"Jobs Created Month: {len(df_jobs_month)}")
        
        if not df_jobs_month.empty:
             print("Job Types in Month:", df_jobs_month["Job Type"].unique())
             print("Job Statuses in Month:", df_jobs_month["Job Status"].unique())

        # Test the metric calc
        result = calculate_conversion_metrics(df_history, df_jobs_month)
        print(f"Conversion Metrics Result: {result}")
        
    except Exception as e:
        print(f"Conversion Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
