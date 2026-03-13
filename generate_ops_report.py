"""
Generate ops_report.json — a snapshot of active engineer headcount
by Trade Group, Subgroup (Trade Filter), and Region.

Run this script at the start of each month to lock in the baseline
for the Engineer Retention % KPI.
"""

import json
import os
from collections import defaultdict

from backend import fetch_service_resources, TRADE_GROUPS, TRADE_SUBGROUPS
from mapping import get_region_for_trade

EXCLUDED_NAMES = {"Project Management", "Electrical FOC Cover"}
EXCLUDED_TRADES = {"Key", "Utilities", "PM", "Test Ops"}


def build_trade_to_subgroup_map():
    """Returns a dict: trade_name -> subgroup_name for each trade group."""
    mapping = {}  # (trade_group, trade_name) -> subgroup_name
    for trade_group, subgroups in TRADE_SUBGROUPS.items():
        for subgroup_name, trades in subgroups.items():
            for trade in trades:
                mapping[(trade_group, trade)] = subgroup_name
    return mapping


def generate_ops_report():
    print("Fetching live service resources from Salesforce...")
    df = fetch_service_resources()

    if df.empty:
        print("ERROR: No service resources returned. Aborting.")
        return

    print(f"  → {len(df)} total active resources fetched.")

    # Remove excluded names and trades
    df = df[~df["Engineer Name"].isin(EXCLUDED_NAMES)]
    df = df[~df["Trade_Lookup__c"].isin(EXCLUDED_TRADES)]

    trade_to_subgroup = build_trade_to_subgroup_map()
    counts = defaultdict(int)

    for _, row in df.iterrows():
        trade_group = row.get("Trade Group", "")
        trade = str(row.get("Trade_Lookup__c", ""))

        if not trade_group or trade_group == "Unknown":
            continue

        # Map to subgroup name (what the user sees in the filter dropdown)
        subgroup = trade_to_subgroup.get((trade_group, trade))
        if not subgroup:
            # If no subgroup, use the raw trade name (for groups with no subgroups like Fire Safety)
            subgroup = trade

        # Use effective postcode (fallback already computed in fetch_service_resources)
        pc = str(row.get("Effective_PostalCode__c", "") or "")
        if not pc or pc.lower() in ("nan", "none", ""):
            pc = ""

        region = get_region_for_trade(pc, trade_group) if pc else "Unknown"

        counts[(trade_group, subgroup, region)] += 1

    report = [
        {
            "Trade Group": tg,
            "Trade": subgroup,
            "Region": rg,
            "Count": cnt
        }
        for (tg, subgroup, rg), cnt in sorted(counts.items())
    ]

    out_path = os.path.join(os.path.dirname(__file__), "ops_report.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=4)

    total = sum(r['Count'] for r in report)
    print(f"\n✅ ops_report.json updated with {total} engineers across {len(report)} subgroup/region combos.")
    print(f"   Saved to: {out_path}")

    # Print summary by trade group
    from collections import Counter
    tg_totals = Counter()
    for r in report:
        tg_totals[r["Trade Group"]] += r["Count"]
    print("\nSummary by Trade Group:")
    for tg, cnt in sorted(tg_totals.items()):
        print(f"  {tg}: {cnt}")


if __name__ == "__main__":
    generate_ops_report()
