import os
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

from backend import (
    get_month_range,
    resolve_trades_for_filters,
    fetch_jobs_created_between,
    fetch_service_appointments_activity,
    fetch_jobs_by_ids,
)

def debug_foc():
    trade_group = "Fire Safety"
    month_name = "Mar"
    year = 2026
    
    month_display = f"{month_name} {year}"
    start_iso, end_iso = get_month_range(month_display)
    trades = resolve_trades_for_filters(trade_group, None)
    
    print(f"--- FOC Discrepancy Debug: {trade_group} ({month_display}) ---")
    
    # 1. Fetch SAs (to find attended jobs)
    df_sa_activity = fetch_service_appointments_activity(tuple(trades), start_iso, end_iso)
    if df_sa_activity.empty:
        print("No SA activity found.")
        return

    attended_job_ids = set(
        df_sa_activity[df_sa_activity["Status"] == "Visit Complete"]["Job__c"].astype(str).unique()
    )

    # 2. Fetch detailed jobs to check Charge Policy and get Names
    df_jobs_detailed = fetch_jobs_by_ids(tuple(attended_job_ids))
    
    df_attended_foc = df_jobs_detailed[
        (df_jobs_detailed["Id"].isin(attended_job_ids)) &
        (df_jobs_detailed["Charge_Policy__c"].isin(["FOC Estimate", "£60 Estimate"]))
    ]
    foc_attended_ids = set(df_attended_foc["Id"].astype(str))
    
    # Map IDs to Job Names (J-XXXXX)
    id_to_name = dict(zip(df_jobs_detailed["Id"], df_jobs_detailed["Name"]))
    
    # 3. Fetch all jobs created this month
    df_jobs_month = fetch_jobs_created_between(tuple(trades), start_iso, end_iso)
    
    raised_from_attended_foc = df_jobs_month[
        df_jobs_month["Raised_from_Job__c"].astype(str).isin(foc_attended_ids)
    ]

    print(f"\nDenominator: {len(foc_attended_ids)} attended FOC visits.")
    print(f"Numerator: {len(raised_from_attended_foc)} total jobs raised.")

    if not raised_from_attended_foc.empty:
        print("\n--- Detailed Linkage (Job Numbers) ---")
        for _, row in raised_from_attended_foc.iterrows():
            child_name = row["Name"]
            parent_id = row["Raised_from_Job__c"]
            parent_name = id_to_name.get(parent_id, "Unknown")
            print(f"Job {child_name} was raised from Parent FOC Visit {parent_name}")

if __name__ == "__main__":
    debug_foc()
