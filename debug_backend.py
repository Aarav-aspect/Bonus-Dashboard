
import sys
import os
import toml
from backend import compute_kpis, resolve_trades_for_filters, get_month_range, get_secrets

print("1. Testing Secrets Loading...")
try:
    secrets = get_secrets()
    print(f"   Secrets found keys: {list(secrets.keys())}")
    if "salesforce" not in secrets:
        print("   ❌ 'salesforce' key missing!")
    else:
        print("   ✅ 'salesforce' key found")
except Exception as e:
    print(f"   ❌ Secrets loading failed: {e}")

print("\n2. Testing KPI Computation...")
try:
    month = "Jan"
    trade_group = "HVac & Electrical"
    start_iso, end_iso = get_month_range(month)
    trades = resolve_trades_for_filters(trade_group, "All")
    
    print(f"   Month: {month}")
    print(f"   Trade Group: {trade_group}")
    print(f"   Trades: {trades}")
    print(f"   Range: {start_iso} - {end_iso}")

    result = compute_kpis(trade_group, trades, start_iso, end_iso)
    print("   ✅ Compute KPIs success!")
    print(f"   Overall Score: {result.get('overall_score')}")
except Exception as e:
    print(f"   ❌ Compute KPIs failed: {e}")
    import traceback
    traceback.print_exc()
