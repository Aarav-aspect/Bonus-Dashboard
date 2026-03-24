import re

import json
from pathlib import Path
import builtins
from database import get_config


# Bonus pot values
BONUS_POT_FILE = Path("bonuspot.json")

def load_bonus_pots():
    # Prefer database
    try:
        config = get_config("bonuspot")
        if config:
            return config
    except Exception as e:
        print(f"Warning: Could not fetch bonus pots from DB: {e}")

    # Fallback to local file
    if BONUS_POT_FILE.exists():
        with open(BONUS_POT_FILE, "r") as f:
            return json.load(f)
    return {}


# Utilities

def normalise_kpi_name(name: str):
    if type(name) is not builtins.str:
        return name

    # Replace ANY unicode whitespace with a normal space
    name = re.sub(r"\s+", " ", name, flags=re.UNICODE)

    # Replace invisible Unicode characters
    for bad in ["\u00A0", "\u2009", "\u202F", "\u2060", "\uFEFF"]:
        name = name.replace(bad, " ")

    return name.strip()

# Month Mapping

MONTH_MAP = {
    "January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr",
    "May": "May", "June": "Jun", "July": "Jul", "August": "Aug",
    "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec",
    "01": "Jan", "1": "Jan", "02": "Feb", "2": "Feb", "03": "Mar", "3": "Mar",
    "04": "Apr", "4": "Apr", "05": "May", "5": "May", "06": "Jun", "6": "Jun",
    "07": "Jul", "7": "Jul", "08": "Aug", "8": "Aug", "09": "Sep", "9": "Sep",
    "10": "Oct", "11": "Nov", "12": "Dec",
}

# KPI Config

THRESHOLD_FILE = Path("thresholds.json")
KPI_CONFIG = {}

def reload_kpi_config():
    global KPI_CONFIG
    
    # Prefer database
    try:
        config = get_config("thresholds")
        if config:
            KPI_CONFIG = config.get("kpis", {})
            return
    except Exception as e:
        print(f"Warning: Could not fetch thresholds from DB: {e}")

    # Fallback to local file
    if THRESHOLD_FILE.exists():
        with open(THRESHOLD_FILE, "r") as f:
            KPI_CONFIG = json.load(f)["kpis"]
    else:
        KPI_CONFIG = {}

# Initial load
reload_kpi_config()

# OPS Count Targets — sub-trade + region level; trade group totals are derived by summing sub-trades.

# Maps each trade group to its sub-trade keys in OPS_COUNT_SUBTRADE_TARGETS
OPS_COUNT_GROUP_SUBTRADES = {
    "HVac & Electrical":       ["Gas & HVAC", "Electrical"],
    "Building Fabric":         ["Decoration", "Roofing", "Multi"],
    "Environmental Services":  ["Gardening", "Pest Control", "Specialist Cleaning", "Waste and Grease"],
    "Fire Safety":             ["Fire Safety"],
    "Leak, Damp & Restoration":["Leak Detection", "Damp"],
    "Plumbing & Drainage":     ["Plumbing", "Drainage"],
}

# Sub-trade + Region Ops Count Targets
# Phase 2 (North/South): +1 per region every 2 months from March
# Phase 3 (NW/SW/East):  +2 per region every 2 months from March
OPS_COUNT_SUBTRADE_TARGETS = {
    # --- Phase 2: HVac & Electrical ---
    "Gas & HVAC": {
        2026: {
            "Mar": {"North":  4, "South":  4},
            "Apr": {"North":  4, "South":  4},
            "May": {"North":  5, "South":  5},
            "Jun": {"North":  5, "South":  5},
            "Jul": {"North":  6, "South":  6},
            "Aug": {"North":  6, "South":  6},
            "Sep": {"North":  7, "South":  7},
            "Oct": {"North":  7, "South":  7},
            "Nov": {"North":  8, "South":  8},
            "Dec": {"North":  8, "South":  8},
        },
    },
    "Electrical": {
        2026: {
            "Mar": {"North": 10, "South":  6},
            "Apr": {"North": 10, "South":  6},
            "May": {"North": 11, "South":  7},
            "Jun": {"North": 11, "South":  7},
            "Jul": {"North": 12, "South":  8},
            "Aug": {"North": 12, "South":  8},
            "Sep": {"North": 13, "South":  9},
            "Oct": {"North": 13, "South":  9},
            "Nov": {"North": 14, "South": 10},
            "Dec": {"North": 14, "South": 10},
        },
    },
    # --- Phase 2: Building Fabric ---
    "Decoration": {
        2026: {
            "Mar": {"North":  2},
            "Apr": {"North":  2},
            "May": {"North":  3},
            "Jun": {"North":  3},
            "Jul": {"North":  4},
            "Aug": {"North":  4},
            "Sep": {"North":  5},
            "Oct": {"North":  5},
            "Nov": {"North":  6},
            "Dec": {"North":  6},
        },
    },
    "Roofing": {
        2026: {
            "Mar": {"North":  7},
            "Apr": {"North":  7},
            "May": {"North":  8},
            "Jun": {"North":  8},
            "Jul": {"North":  9},
            "Aug": {"North":  9},
            "Sep": {"North": 10},
            "Oct": {"North": 10},
            "Nov": {"North": 11},
            "Dec": {"North": 11},
        },
    },
    "Multi": {
        2026: {
            "Mar": {"North": 10, "South":  2},
            "Apr": {"North": 10, "South":  2},
            "May": {"North": 11, "South":  3},
            "Jun": {"North": 11, "South":  3},
            "Jul": {"North": 12, "South":  4},
            "Aug": {"North": 12, "South":  4},
            "Sep": {"North": 13, "South":  5},
            "Oct": {"North": 13, "South":  5},
            "Nov": {"North": 14, "South":  6},
            "Dec": {"North": 14, "South":  6},
        },
    },
    # --- Phase 2: Fire Safety ---
    "Fire Safety": {
        2026: {
            "Mar": {"North":  6, "South":  2},
            "Apr": {"North":  6, "South":  2},
            "May": {"North":  7, "South":  3},
            "Jun": {"North":  7, "South":  3},
            "Jul": {"North":  8, "South":  4},
            "Aug": {"North":  8, "South":  4},
            "Sep": {"North":  9, "South":  5},
            "Oct": {"North":  9, "South":  5},
            "Nov": {"North": 10, "South":  6},
            "Dec": {"North": 10, "South":  6},
        },
    },
    # --- Phase 1: Environmental Services (no regional split) ---
    "Gardening": {
        2026: {
            "Mar": {"All": 1},
        },
    },
    "Pest Control": {
        2026: {
            "Mar": {"All": 4},
        },
    },
    "Specialist Cleaning": {
        2026: {
            "Mar": {"All": 1},
        },
    },
    "Waste and Grease": {
        2026: {
            "Mar": {"All": 4},
        },
    },
    # --- Phase 3: Leak, Damp & Restoration ---
    "Leak Detection": {
        2026: {
            "Mar": {"North West": 18, "South West": 10, "East": 28},
            "Apr": {"North West": 18, "South West": 10, "East": 28},
            "May": {"North West": 20, "South West": 12, "East": 30},
            "Jun": {"North West": 20, "South West": 12, "East": 30},
            "Jul": {"North West": 22, "South West": 14, "East": 32},
            "Aug": {"North West": 22, "South West": 14, "East": 32},
            "Sep": {"North West": 24, "South West": 16, "East": 34},
            "Oct": {"North West": 24, "South West": 16, "East": 34},
            "Nov": {"North West": 26, "South West": 18, "East": 36},
            "Dec": {"North West": 26, "South West": 18, "East": 36},
        },
    },
    "Damp": {
        2026: {
            "Mar": {"South West":  4, "East":  2},
            "Apr": {"South West":  4, "East":  2},
            "May": {"South West":  6, "East":  4},
            "Jun": {"South West":  6, "East":  4},
            "Jul": {"South West":  8, "East":  6},
            "Aug": {"South West":  8, "East":  6},
            "Sep": {"South West": 10, "East":  8},
            "Oct": {"South West": 10, "East":  8},
            "Nov": {"South West": 12, "East": 10},
            "Dec": {"South West": 12, "East": 10},
        },
    },
    # --- Phase 3: Plumbing & Drainage ---
    "Plumbing": {
        2026: {
            "Mar": {"North West":  2, "South West":  2, "East":  4},
            "Apr": {"North West":  2, "South West":  2, "East":  4},
            "May": {"North West":  4, "South West":  4, "East":  6},
            "Jun": {"North West":  4, "South West":  4, "East":  6},
            "Jul": {"North West":  6, "South West":  6, "East":  8},
            "Aug": {"North West":  6, "South West":  6, "East":  8},
            "Sep": {"North West":  8, "South West":  8, "East": 10},
            "Oct": {"North West":  8, "South West":  8, "East": 10},
            "Nov": {"North West": 10, "South West": 10, "East": 12},
            "Dec": {"North West": 10, "South West": 10, "East": 12},
        },
    },
    "Drainage": {
        2026: {
            "Mar": {"North West": 12, "East": 23},
            "Apr": {"North West": 12, "East": 23},
            "May": {"North West": 14, "East": 25},
            "Jun": {"North West": 14, "East": 25},
            "Jul": {"North West": 16, "East": 27},
            "Aug": {"North West": 16, "East": 27},
            "Sep": {"North West": 18, "East": 29},
            "Oct": {"North West": 18, "East": 29},
            "Nov": {"North West": 20, "East": 31},
            "Dec": {"North West": 20, "East": 31},
        },
    },
}

def get_ops_count_subtrade_target(subtrade: str, month: str, year: int, region: str = "All"):
    month_key = MONTH_MAP.get(month, month)
    data = OPS_COUNT_SUBTRADE_TARGETS.get(subtrade, {}).get(year, {}).get(month_key)
    if data is None:
        return None
    if isinstance(data, dict):
        if region != "All":
            return data.get(region)
        return sum(data.values())
    return data

def get_ops_count_target(trade_group: str, month: str, year: int, region: str = "All", trade: str = None):
    """Returns ops count target for a trade group (or specific sub-trade) by summing sub-trade targets."""
    month_key = MONTH_MAP.get(month, month)
    if trade and trade != "All":
        # Look up just this sub-trade directly
        data = OPS_COUNT_SUBTRADE_TARGETS.get(trade, {}).get(year, {}).get(month_key)
        if data is None:
            return None
        if isinstance(data, dict):
            return data.get(region, 0) if region != "All" else sum(data.values())
        return data
    subtrades = OPS_COUNT_GROUP_SUBTRADES.get(trade_group, [])
    total = 0
    found_any = False
    for subtrade in subtrades:
        data = OPS_COUNT_SUBTRADE_TARGETS.get(subtrade, {}).get(year, {}).get(month_key)
        if data is None:
            continue
        found_any = True
        if isinstance(data, dict):
            total += data.get(region, 0) if region != "All" else sum(data.values())
        else:
            total += data
    return total if found_any else None

# Sales Targets

SALES_TARGETS = {
    "Waste and Grease": {
        2026: {
            "Mar": 6638.90, "Apr": 6594.89, "May": 6489.65, "Jun": 4236.04,
            "Jul": 3555.19, "Aug": 2690.96, "Sep": 5216.27, "Oct": 5680.32,
            "Nov": 5795.75, "Dec": 5291.29,
        },
    },
    "Pest Control": {
        2026: {
            "Mar": 11929.00, "Apr": 11849.92, "May": 11660.82, "Jun": 4361.81,
            "Jul": 3366.00, "Aug": 2351.77, "Sep": 7749.13, "Oct": 8438.52,
            "Nov": 8610.00, "Dec": 15251.09,
        },
    },
    "Gardening": {
        2026: {
            "Mar": 10730.01, "Apr": 10658.88, "May": 10488.79, "Jun": 17870.77,
            "Jul": 19683.01, "Aug": 19655.39, "Sep": 15948.90, "Oct": 17367.77,
            "Nov": 17720.70, "Dec": 4878.10,
        },
    },
    "Fire Safety": {
        2025: {"Nov": 7000, "Dec": 7200},
        2026: {
            "Jan": 7400,
            "Feb": 7600,
            "Mar": {"North": 265227.456, "South": 23639.616},
            "Apr": {"North": 274956.744, "South": 24506.784},
            "May": {"North": 277801.8, "South": 24760.368},
            "Jun": {"North": 271155.912, "South": 24168.024},
            "Jul": {"North": 288757.128, "South": 25736.808},
            "Aug": {"North": 296856.432, "South": 26458.704},
            "Sep": {"North": 298927.076, "South": 26625.432},
            "Oct": {"North": 295010.928, "South": 26294.208},
            "Nov": {"North": 294001.404, "South": 26204.232},
            "Dec": {"North": 309594.408, "South": 27594.036},
        },
    },
    "Leak, Damp & Restoration": {
        2025: {"Nov": 15000, "Dec": 15500},
        2026: {
            "Jan": 15700,
            "Feb": 16000,
            "Mar": {"East": 331704.336, "North West": 347615.412, "South West": 314064.00},
            "Apr": {"East": 319387.236, "North West": 334707.492, "South West": 302401.932},
            "May": {"East": 301015.296, "North West": 315454.284, "South West": 285007.032},
            "Jun": {"East": 302956.836, "North West": 317488.956, "South West": 286845.312},
            "Jul": {"East": 323267.628, "North West": 338774.004, "South West": 306075.96},
            "Aug": {"East": 300313.296, "North West": 314718.612, "South West": 284342.364},
            "Sep": {"East": 324103.392, "North West": 339649.86, "South West": 306867.264},
            "Oct": {"East": 349347.132, "North West": 366104.496, "South West": 330768.54},
            "Nov": {"East": 364085.784, "North West": 381550.116, "South West": 344723.364},
            "Dec": {"East": 300937.32, "North West": 315372.564, "South West": 284931.996},
        },
    },
    "Drainage": {
        2026: {
            "Mar": {"East": 280452.996, "North West": 291787.332, "South West": 252255.312},
            "Apr": {"East": 273345.348, "North West": 284392.428, "South West": 245862.288},
            "May": {"East": 257754.012, "North West": 268170.972, "South West": 231838.56},
            "Jun": {"East": 252772.848, "North West": 245939.88, "South West": 210442.476},
            "Jul": {"East": 265960.716, "North West": 253257.96, "South West": 213801.972},
            "Aug": {"East": 240430.14, "North West": 222066.792, "South West": 184861.992},
            "Sep": {"East": 271875.492, "North West": 270771.36, "South West": 231537.396},
            "Oct": {"East": 294762.852, "North West": 293565.768, "South West": 251028.972},
            "Nov": {"East": 303413.424, "North West": 302181.204, "South West": 258396.048},
            "Dec": {"East": 241697.772, "North West": 264344.34, "South West": 214293.192},
        },
    },
    "Plumbing": {
        2026: {
            "Mar": {"East": 106353.192, "North West": 56465.328, "South West": 65356.764},
            "Apr": {"East": 103657.824, "North West": 55034.304, "South West": 63700.392},
            "May": {"East": 97745.292, "North West": 51895.2, "South West": 60066.996},
            "Jun": {"East": 104427.156, "North West": 75657.48, "South West": 82859.532},
            "Jul": {"East": 114388.56, "North West": 89181.348, "South West": 98508.252},
            "Aug": {"East": 107812.488, "North West": 91465.992, "South West": 101085.0},
            "Sep": {"East": 109931.172, "North West": 72980.088, "South West": 81969.648},
            "Oct": {"East": 119185.536, "North West": 79123.788, "South West": 88869.948},
            "Nov": {"East": 122683.332, "North West": 81445.872, "South West": 91478.076},
            "Dec": {"East": 104407.848, "North West": 47264.436, "South West": 69899.064},
        },
    },
    "Decoration": {
        2026: {
            "Mar": {"North": 39813.984, "South": 37096.608},
            "Apr": {"North": 38347.98, "South": 35730.672},
            "May": {"North": 36674.544, "South": 34171.452},
            "Jun": {"North": 26324.868, "South": 35176.092},
            "Jul": {"North": 24561.396, "South": 37727.424},
            "Aug": {"North": 19793.496, "South": 35001.192},
            "Sep": {"North": 32226.348, "South": 37396.548},
            "Oct": {"North": 34618.98, "South": 40173.048},
            "Nov": {"North": 35888.16, "South": 41645.844},
            "Dec": {"North": 27076.86, "South": 33545.844},
        },
    },
    "Multi": {
        2026: {
            "Mar": {"North": 280039.884, "South": 75413.136},
            "Apr": {"North": 269728.464, "South": 72636.324},
            "May": {"North": 257958.0, "South": 69466.608},
            "Jun": {"North": 310400.1, "South": 82364.88},
            "Jul": {"North": 344473.272, "South": 95077.356},
            "Aug": {"North": 331932.12, "South": 95311.5},
            "Sep": {"North": 312506.196, "South": 85384.128},
            "Oct": {"North": 335708.16, "South": 91723.464},
            "Nov": {"North": 348015.72, "South": 95086.176},
            "Dec": {"North": 268416.156, "South": 85968.0},
        },
    },
    "Roofing": {
        2026: {
            "Mar": {"North": 225269.88, "South": 152005.872},
            "Apr": {"North": 216975.168, "South": 146408.82},
            "May": {"North": 207506.76, "South": 140019.804},
            "Jun": {"North": 205154.868, "South": 125278.188},
            "Jul": {"North": 214315.548, "South": 128083.008},
            "Aug": {"North": 193171.62, "South": 113016.096},
            "Sep": {"North": 219622.272, "South": 139952.652},
            "Oct": {"North": 235928.088, "South": 150343.416},
            "Nov": {"North": 244577.556, "South": 155855.232},
            "Dec": {"North": 179631.336, "South": 119435.136},
        },
    },
    "Electrical": {
        2026: {
            "Mar": {"North": 168961.524, "South": 123966.804},
            "Apr": {"North": 164496.972, "South": 120691.164},
            "May": {"North": 155075.16, "South": 113778.396},
            "Jun": {"North": 171349.488, "South": 134102.34},
            "Jul": {"North": 186856.092, "South": 150948.768},
            "Aug": {"North": 180313.968, "South": 150068.556},
            "Sep": {"North": 178154.4, "South": 137789.28},
            "Oct": {"North": 192566.076, "South": 148935.648},
            "Nov": {"North": 197747.1, "South": 152942.796},
            "Dec": {"North": 162209.364, "South": 126698.532},
        },
    },
    "Gas & HVAC": {
        2026: {
            "Mar": {"North": 173996.868, "South": 194270.364},
            "Apr": {"North": 169399.26, "South": 189137.064},
            "May": {"North": 159696.66, "South": 178303.956},
            "Jun": {"North": 141776.892, "South": 156453.18},
            "Jul": {"North": 144286.92, "South": 156324.708},
            "Aug": {"North": 129280.476, "South": 137209.62},
            "Sep": {"North": 158844.972, "South": 174918.408},
            "Oct": {"North": 171694.62, "South": 189068.304},
            "Nov": {"North": 176314.092, "South": 194155.224},
            "Dec": {"North": 154653.588, "South": 167324.232},
        },
    },
}

# Sub-trade groupings — when a parent trade group is queried with trade="All",
# targets are summed across all sub-trades.
TRADE_GROUP_SUBTRADES = {
    "Plumbing & Drainage": ["Drainage", "Plumbing"],
    "Building Fabric": ["Decoration", "Multi", "Roofing"],
    "HVac & Electrical": ["Electrical", "Gas & HVAC"],
    "Environmental Services": ["Waste and Grease", "Pest Control", "Gardening"],
}

def _get_direct_sales_target(trade_group: str, month_key: str, year: int, region: str) -> float:
    matched_group = next((k for k in SALES_TARGETS if k.lower() == trade_group.strip().lower()), None)
    if matched_group is None:
        return 0.0
    target_data = SALES_TARGETS.get(matched_group, {}).get(year, {}).get(month_key, 0.0)
    if isinstance(target_data, dict):
        if region != "All":
            return target_data.get(region, 0.0)
        else:
            return sum(target_data.values())
    return float(target_data)

def get_sales_target(trade_group: str, month: str, year: int = 2025, region: str = "All", trade: str = "All") -> float:
    month_key = MONTH_MAP.get(month, month)
    trade_group_clean = trade_group.strip().lower()

    # Check if this trade group has sub-trades
    matched_parent = next((k for k in TRADE_GROUP_SUBTRADES if k.lower() == trade_group_clean), None)
    if matched_parent:
        sub_trades = TRADE_GROUP_SUBTRADES[matched_parent]
        if trade != "All":
            sub_trades = [t for t in sub_trades if t.lower() == trade.strip().lower()]
        return sum(_get_direct_sales_target(t, month_key, year, region) for t in sub_trades)

    return _get_direct_sales_target(trade_group, month_key, year, region)

def calculate_target_achievement(actual: float, trade_group: str, month: str, year: int = 2025, region: str = "All", trade: str = "All") -> float:
    normalised_month = MONTH_MAP.get(month, month)
    target = get_sales_target(trade_group, normalised_month, year, region, trade)
    if target == 0:
        return 0.0
    return (actual / target) * 100

def calculate_ops_count_achievement(actual: int, trade_group: str, month: str, year: int) -> float:
    target = get_ops_count_target(trade_group, month, year)
    if not target:
        return 0.0
    return (actual / target) * 100

# KPI Scoring

def calculate_kpi_score(kpi_name: str, value: float, scoring_key: str = None) -> dict:
    kpi_name = normalise_kpi_name(kpi_name)

    if value is None or kpi_name not in KPI_CONFIG:
        return {"score": None, "target_met": None, "value": value, "threshold": None}

    cfg = KPI_CONFIG[kpi_name]

    # Dynamic trade-based KPIs
    if "dynamic" in cfg:
        dyn = cfg["dynamic"]
        if dyn.get("type") == "trade_based":
            # Use scoring_key (e.g. "Electrical" or "HVac & Electrical") to find thresholds
            trade_thresholds = dyn["thresholds_by_trade"].get(scoring_key, [])
            scores = dyn.get("scores", [])
            for t, s in zip(trade_thresholds, scores):
                # Handle None in dynamic thresholds
                t_val = t if t is not None else float("-inf")
                if value >= t_val:
                    return {"score": s, "target_met": s == 100, "value": value, "threshold": {"min": t, "score": s}}
            return {"score": 0, "target_met": False, "value": value, "threshold": {"min": None, "score": 0}}

    # Static KPI thresholds
    direction = cfg.get("direction", "higher_is_better")
    thresholds = cfg.get("thresholds", [])

    matched = None
    score = 0

    if direction == "higher_is_better":
        # Handle None in min: treat as -infinity for sorting and comparison
        sorted_thresholds = sorted(
            thresholds, 
            key=lambda x: (x.get("min") if x.get("min") is not None else float("-inf")), 
            reverse=True
        )
        for t in sorted_thresholds:
            t_min = t.get("min") if t.get("min") is not None else float("-inf")
            if value >= t_min:
                matched = t
                score = t["score"]
                break
    elif direction == "lower_is_better":
        # Handle None in max: treat as infinity for sorting and comparison
        sorted_thresholds = sorted(
            thresholds, 
            key=lambda x: (x.get("max") if x.get("max") is not None else float("inf"))
        )
        for t in sorted_thresholds:
            t_max = t.get("max") if t.get("max") is not None else float("inf")
            if value <= t_max:
                matched = t
                score = t["score"]
                break

    return {"score": score, "target_met": score == 100, "value": value, "threshold": matched}

def calculate_all_kpi_scores(kpis: dict) -> dict:
    scores = {}
    for kpi_name, value in kpis.items():
        if kpi_name in KPI_CONFIG:
            scores[kpi_name] = calculate_kpi_score(kpi_name, value)
    return scores

# Category Scoring

CATEGORY_KPIS = {
    "Conversion": [
        "Estimate Conversion %",
        "FOC Conversion Rate %",
        "Estimate Production / Reactive Leads %",
        "Average Converted Estimate Value (£)",
    ],
    "Procedural": [
        "TQR Ratio %",
        "TQR (Not Satisfied) Ratio %",
        "Unclosed SA %",
        "Reactive 6+ hours %",
        "Late to Site %",
    ],
    "Satisfaction": [
        "Average Review Rating",
        "Review Ratio %",
        "Engineer Satisfaction %",
        "Cases %",
        "Engineer Retention %",
    ],
    "Vehicular": [
        "Average Driving Score",
        "Drivers with <7",
        "VCR Update %",
    ],
    "Productivity": [
        "Sales Target Achievement %",
        "Callback Jobs %",
        "Average Site Value (£)",
        "SA Attended",
        "Ops Count %",
    ],
}

def get_category_score(category_name: str, kpis: dict, scoring_key: str) -> dict:
    if category_name not in CATEGORY_KPIS:
        return {"category_score": None}

    relevant_kpis = CATEGORY_KPIS[category_name]
    scored_kpis = []
    breakdown = {}

    for kpi_name in relevant_kpis:
        if kpi_name in kpis and kpis[kpi_name] is not None:
            # Pass scoring_key (e.g., "Electrical" or "HVac & Electrical")
            result = calculate_kpi_score(kpi_name, kpis[kpi_name], scoring_key)
            if result["score"] is not None:
                scored_kpis.append(result["score"])
                breakdown[kpi_name] = result

    if not scored_kpis:
        return {"category_score": None, "kpi_count": 0}

    kpi_count = len(scored_kpis)
    points_per_kpi = 100 / kpi_count
    category_score = sum((score / 100) * points_per_kpi for score in scored_kpis)

    return {
        "category_score": round(category_score, 2),
        "kpi_count": kpi_count,
        "points_per_kpi": points_per_kpi,
        "kpi_scores": breakdown,
        "target_met": category_score >= 100,
    }

# Bonus Calculation

# We are removing the hardcoded bonut pot functionality and will be moving it to the threshold page.




BONUS_SCORE_BANDS = [
    {"min": 90, "max": 101, "multiplier": 0.30},
    {"min": 80, "max": 90,  "multiplier": 0.20},
    {"min": 70, "max": 80,  "multiplier": 0.10},
    {"min": 60, "max": 70,  "multiplier": -0.10},
    {"min": 50, "max": 60,  "multiplier": -0.20},
    {"min": 40, "max": 50,  "multiplier": -0.30},
    {"min": 30, "max": 40,  "multiplier": -0.40},
    {"min": 20, "max": 30,  "multiplier": -0.50},
    {"min": 10, "max": 20,  "multiplier": -0.60},
]

def get_bonus_multiplier(overall_score: float) -> float:
    if overall_score is None:
        return 0.0
    for band in BONUS_SCORE_BANDS:
        if band["min"] <= overall_score < band["max"]:
            return band["multiplier"]
    return 0.0

def calculate_bonus(overall_score: float, bonus_group: str, bonus_trade: str = None) -> dict:
    multiplier = get_bonus_multiplier(overall_score)
    pots = load_bonus_pots()

    # Try trade-specific key first (e.g. "HVac & Electrical::Gas & Heating")
    pot = None
    if bonus_trade and bonus_trade != "All":
        trade_key = f"{bonus_group}::{bonus_trade}"
        canonical_trade_key = next((k for k in pots if k.lower() == trade_key.lower()), None)
        if canonical_trade_key:
            pot = pots.get(canonical_trade_key)

    # Fall back to group key
    if pot is None:
        canonical_key = next((k for k in pots if k.lower() == bonus_group.lower()), bonus_group)
        pot = pots.get(canonical_key, 969.25)

    bonus_value = pot * (1 + multiplier)
    return {"pot": pot, "multiplier": multiplier, "bonus_value": bonus_value}

def get_overall_score(kpis: dict, scoring_key: str, bonus_group: str, weights: dict = None, bonus_trade: str = None):
    """Calculate the overall performance score."""
    categories = ["Conversion", "Procedural", "Satisfaction", "Vehicular", "Productivity"]
    if weights is None:
        weights = {c: 1 for c in categories}
    total_weight = sum(weights.values())
    if total_weight == 0:
        return {"overall_score": 0.0}

    weighted_sum = 0.0
    for category in categories:
        # Use scoring_key for KPI/Category scoring
        cat_result = get_category_score(category, kpis, scoring_key)
        cat_score = cat_result.get("category_score", 0.0) or 0.0
        weighted_sum += cat_score * weights.get(category, 1)

    overall_score = float(weighted_sum / total_weight)
    
    # Use bonus_group (and optional bonus_trade) for Bonus Pot lookup
    bonus = calculate_bonus(overall_score, bonus_group, bonus_trade=bonus_trade)

    return {"overall_score": overall_score, "bonus": bonus}

# Helpers

def get_kpi_target_info(kpi_name: str) -> dict:
    return KPI_CONFIG.get(kpi_name)

def get_all_kpi_targets() -> dict:
    return KPI_CONFIG
