import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import requests
from backend import compute_kpis, get_month_range, resolve_trades_for_filters

def test_kpi_fix():
    month = "Feb 2026"
    trade_group = "Plumbing & Drainage"
    trade_filter = "All"
    
    start_iso, end_iso = get_month_range(month)
    trades = resolve_trades_for_filters(trade_group, trade_filter)
    
    print(f"Testing KPIs for {trade_group}...")
    result = compute_kpis(trade_group, trades, start_iso, end_iso, trade_filter)
    
    kpis = result.get("kpis", {})
    categories = result.get("categories", {})
    
    kpis_to_check = [
        "Drivers with <7 %",
        "TQR Ratio %",
        "Cases %",
        "Engineer Retention %",
        "Sales Target Achievement %",
        "Monthly Working Time (hrs)",
        "Absence %"
    ]
    
    for kpi_name in kpis_to_check:
        if kpi_name in kpis:
            print(f"SUCCESS: '{kpi_name}' found in kpis: {kpis[kpi_name]}")
        else:
            print(f"FAILURE: '{kpi_name}' NOT found in kpis")
            
    categories_to_check = {
        "Vehicular": ["Drivers with <7 %"],
        "Procedural": ["TQR Ratio %"],
        "Satisfaction": ["Cases %", "Engineer Retention %"],
        "Productivity": ["Sales Target Achievement %", "Monthly Working Time (hrs)", "Absence %"]
    }
    
    for cat_name, cat_kpis in categories_to_check.items():
        cat_data = categories.get(cat_name, {})
        for kpi_name in cat_kpis:
            if kpi_name in cat_data:
                print(f"SUCCESS: '{kpi_name}' found in {cat_name} category: {cat_data[kpi_name]}")
            else:
                print(f"FAILURE: '{kpi_name}' NOT found in {cat_name} category")

if __name__ == "__main__":
    test_kpi_fix()
