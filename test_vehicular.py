import asyncio
from backend import get_merged_vehicular_data, calculate_vehicular_kpi, resolve_trades_for_filters
import pandas as pd

import copy

def test():
    # Fetch data
    df_veh = get_merged_vehicular_data()
    print(f"Total rows fetched: {len(df_veh)}")
    
    # Resolving trades
    trades = resolve_trades_for_filters("HVac & Electrical", "Electrical")
    print(f"Resolved Trades (Electrical): {trades}")
    
    kpi_all = calculate_vehicular_kpi(df_veh, "HVac & Electrical", None)
    print("KPI ALL:", kpi_all)

    kpi_elec = calculate_vehicular_kpi(df_veh, "HVac & Electrical", trades)
    print("KPI ELECTRICAL:", kpi_elec)

if __name__ == "__main__":
    test()
