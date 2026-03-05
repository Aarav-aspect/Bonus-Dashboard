"""
Debug Script: Ops Not Found on Webfleet / Optidrive
=====================================================
Fetches all active ops from Salesforce (same filters as Ops Count KPI),
then finds which ones cannot be matched to Webfleet/Optidrive data.
Results are saved to ops_not_on_webfleet.txt
"""

import os
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from backend import (
    fetch_service_resources,
    fetch_webfleet_drivers,
    fetch_optidrive_scores_bulk,
    WEBFLEET_EMAIL_MAP,
    map_trade_to_group,
)


def debug_ops_not_on_webfleet():
    print("Fetching Service Resources (Ops) from Salesforce...")
    df_engineers = fetch_service_resources()
    
    print("Fetching Webfleet drivers...")
    df_drivers = fetch_webfleet_drivers()
    
    print("Fetching Optidrive scores...")
    df_optidrive = fetch_optidrive_scores_bulk()

    if df_engineers.empty:
        print("No engineers found in Salesforce.")
        return

    # Reproduce the same email matching logic from get_merged_vehicular_data()
    # 1. Merge Optidrive + Webfleet drivers to get emails
    if not df_optidrive.empty and not df_drivers.empty:
        df_optidrive["driverno_clean"] = df_optidrive["driverno"].astype(str).str.strip().str.lower()
        df_drivers["driverno_clean"] = df_drivers["Driver No"].astype(str).str.strip().str.lower()

        df_merged = df_optidrive.merge(
            df_drivers[["driverno_clean", "Email"]],
            on="driverno_clean",
            how="left",
        )
        df_merged["Email_Lower"] = df_merged["Email"].fillna("").astype(str).str.lower().str.strip()
        # Apply email overrides
        df_merged["Email_Lower"] = df_merged["Email_Lower"].map(
            lambda e: WEBFLEET_EMAIL_MAP.get(e, e)
        )
        webfleet_emails = set(df_merged["Email_Lower"].dropna().unique())
    else:
        webfleet_emails = set()

    # 2. Build matched emails from engineers
    df_engineers["Email_Lower"] = df_engineers["Email"].astype(str).str.lower().str.strip()
    
    # 3. Find ops NOT in webfleet
    df_not_matched = df_engineers[~df_engineers["Email_Lower"].isin(webfleet_emails)].copy()
    df_not_matched = df_not_matched.sort_values("Trade_Lookup__c")

    total_ops = len(df_engineers)
    not_matched_count = len(df_not_matched)

    print(f"\nTotal Ops in Salesforce: {total_ops}")
    print(f"Ops NOT found on Webfleet/Optidrive: {not_matched_count}")

    # 4. Write to file
    output_path = "ops_not_on_webfleet.txt"
    with open(output_path, "w") as f:
        f.write(f"Ops NOT Found on Webfleet/Optidrive\n")
        f.write(f"=" * 60 + "\n")
        f.write(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Ops in Salesforce: {total_ops}\n")
        f.write(f"Ops NOT matched to Webfleet/Optidrive: {not_matched_count}\n")
        f.write(f"=" * 60 + "\n\n")

        for _, row in df_not_matched.iterrows():
            name = row.get("Engineer Name", "N/A")
            email = row.get("Email", "N/A")
            trade = row.get("Trade_Lookup__c", "N/A")
            trade_group = row.get("Trade Group", "N/A")
            f.write(f"Name:        {name}\n")
            f.write(f"Email:       {email}\n")
            f.write(f"Trade:       {trade}\n")
            f.write(f"Trade Group: {trade_group}\n")
            f.write("-" * 40 + "\n")

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    debug_ops_not_on_webfleet()
