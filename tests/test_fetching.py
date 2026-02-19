
import sys
import os
import pandas as pd
from datetime import datetime
import asyncio

# Add current directory to sys.path
sys.path.append(os.getcwd())

from backend import fetch_service_appointments_month, fetch_workorders_month, sf_client

async def test():
    print("Testing Data Fetching...")
    
    # Define period: Feb 2026
    start_iso = "2026-02-01T00:00:00Z"
    end_iso = "2026-03-01T00:00:00Z"
    
    # Simulating what happens for "HVac & Electrical"
    # Although backend logic might use broader list found in TRADE_GROUPS
    trades_tuple = ("HVAC", "Electrical", "Air Conditioning", "Refrigeration") 
    
    print(f"Period: {start_iso} to {end_iso}")
    print(f"Trades: {trades_tuple}")
    
    try:
        # Test Service Appointments
        print("\n--- Fetching Service Appointments ---")
        df_sa = fetch_service_appointments_month(trades_tuple, start_iso, end_iso)
        print(f"Rows returned: {len(df_sa)}")
        if not df_sa.empty:
            print("Columns:", df_sa.columns.tolist())
            # Check for columns used in backend logic
            if "Job__r.Job_Type_Trade__c" in df_sa.columns:
                 print("Unique Job__r.Job_Type_Trade__c:", df_sa["Job__r.Job_Type_Trade__c"].unique())
            elif "ServiceAppointment.CCT_Trade__c" in df_sa.columns:
                 print("Unique ServiceAppointment.CCT_Trade__c:", df_sa["ServiceAppointment.CCT_Trade__c"].unique())
            elif "CCT_Trade__c" in df_sa.columns:
                 print("Unique CCT_Trade__c:", df_sa["CCT_Trade__c"].unique())
            else:
                 print("WARNING: No Trade column found!")
        else:
            print("WARNING: Empty DataFrame returned for Service Appointments")

        # Test Work Orders
        print("\n--- Fetching Work Orders ---")
        df_wo = fetch_workorders_month(trades_tuple, start_iso, end_iso)
        print(f"Rows returned: {len(df_wo)}")
        if not df_wo.empty:
            print("Columns:", df_wo.columns.tolist())
            if "Trade__c" in df_wo.columns:
                print("Unique Trade__c:", df_wo["Trade__c"].unique())
            elif "CCT_Trade__c" in df_wo.columns:
                print("Unique CCT_Trade__c:", df_wo["CCT_Trade__c"].unique())
            else:
                print("WARNING: No Trade column found!")
        else:
            print("WARNING: Empty DataFrame returned for Work Orders")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
