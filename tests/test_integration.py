
import sys
import os
import pandas as pd

# Add current directory to sys.path
sys.path.append(os.getcwd())

from targets import calculate_kpi_score, reload_kpi_config, KPI_CONFIG
# We need to import the function from backend.py, but backend.py imports targets. 
# This circular dependency might be tricky if not handled, but usually fine in script.
from backend import calculate_dynamic_kpi_per_trade

def test():
    print("Reloading config...")
    reload_kpi_config()
    
    kpi = "Average Converted Estimate Value (£)"
    trade_group_selected = "HVac & Electrical"
    trade_filter = "All"
    
    # Mock Data
    # 3 jobs for HVAC, average 521.721
    # We need a DataFrame with "Trade" and "Charge Net" and "Job Status"
    # HVAC Trade names: "HVAC", "Air Con..."
    
    data = [
        {"Trade": "HVAC", "Charge Net": 521.721, "Job Status": "Closed"},
        {"Trade": "HVAC", "Charge Net": 521.721, "Job Status": "Converted"},
        {"Trade": "Electrical", "Charge Net": 100.0, "Job Status": "Closed"}, # Electrical low value
    ]
    df_data = pd.DataFrame(data)
    
    print(f"Testing Integration for: '{kpi}'")
    
    result = calculate_dynamic_kpi_per_trade(
        kpi,
        df_data,
        trade_group_selected,
        trade_filter
    )
    
    print(f"Integration Result: {result}")

if __name__ == "__main__":
    test()
