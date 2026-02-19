
import sys
import os

# Add current directory to sys.path
sys.path.append(os.getcwd())

from targets import calculate_kpi_score, reload_kpi_config, KPI_CONFIG

def test():
    print("Reloading config...")
    reload_kpi_config()
    
    kpi = "Average Converted Estimate Value (£)"
    val = 521.721
    trade = "HVAC"
    
    print(f"Testing KPI: '{kpi}'")
    print(f"Value: {val}")
    print(f"Trade: '{trade}'")
    
    # Check config presence
    if kpi in KPI_CONFIG:
        print("KPI found in config.")
        cfg = KPI_CONFIG[kpi]
        if "dynamic" in cfg:
            print("KPI is dynamic.")
            thresholds = cfg["dynamic"]["thresholds_by_trade"].get(trade)
            print(f"Thresholds for {trade}: {thresholds}")
        else:
            print("KPI is NOT dynamic.")
    else:
        print("KPI NOT found in config.")
        keys = list(KPI_CONFIG.keys())
        print(f"Available keys (first 5): {keys[:5]}")
        # Check for near matches
        for k in keys:
            if "Average Converted" in k:
                print(f"Potential match: '{k}'")

    result = calculate_kpi_score(kpi, val, trade)
    print(f"Result: {result}")

if __name__ == "__main__":
    test()
