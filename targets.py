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

# OPS Count Targets

OPS_COUNT_TARGETS = {
    "HVac & Electrical": {
        2025: {"Nov": 20, "Dec": 20},
        2026: {"Jan": 22, "Feb": 22, "Mar": 22, "Apr": 23, "May": 23, "Jun": 23,
               "Jul": 24, "Aug": 24, "Sep": 24},
    },
    "Building Fabric": {
        2025: {"Nov": 18, "Dec": 18},
        2026: {"Jan": 20, "Feb": 20, "Mar": 20, "Apr": 20, "May": 20,
               "Jun": 22, "Jul": 22, "Aug": 22, "Sep": 22},
    },
    "Environmental Services": {
        2025: {"Nov": 5, "Dec": 5},
        2026: {"Jan": 6, "Feb": 6, "Mar": 7, "Apr": 7, "May": 8,
               "Jun": 8, "Jul": 9, "Aug": 9, "Sep": 10},
    },
    "Fire Safety": {
        2025: {"Nov": 5, "Dec": 5},
        2026: {"Jan": 5, "Feb": 6, "Mar": 6, "Apr": 7, "May": 7,
               "Jun": 8, "Jul": 8, "Aug": 9, "Sep": 9},
    },
    "Leak, Damp & Restoration": {
        2025: {"Nov": 54, "Dec": 54},
        2026: {"Jan": 56, "Feb": 56, "Mar": 58, "Apr": 58, "May": 60,
               "Jun": 60, "Jul": 62, "Aug": 62, "Sep": 64},
    },
    "Plumbing & Drainage": {
        2025: {"Nov": 36, "Dec": 36},
        2026: {"Jan": 37, "Feb": 37, "Mar": 37, "Apr": 40, "May": 40,
               "Jun": 40, "Jul": 44, "Aug": 44, "Sep": 44},
    },
}

def get_ops_count_target(trade_group: str, month: str, year: int):
    month_key = MONTH_MAP.get(month, month)
    return OPS_COUNT_TARGETS.get(trade_group, {}).get(year, {}).get(month_key)

# Sales Targets

SALES_TARGETS = {
    "HVac & Electrical": {
        2025: {"Nov": 10000, "Dec": 10500},
        2026: {"Jan": 11000, "Feb": 564162, "Mar": 11500, "Apr": 11750, "May": 12000,
               "Jun": 12250, "Jul": 12500, "Aug": 12750, "Sep": 13000},
    },
    "Building Fabric": {
        2025: {"Nov": 8000, "Dec": 8500},
        2026: {"Jan": 8700, "Feb": 8800, "Mar": 9000, "Apr": 9200, "May": 9400,
               "Jun": 9600, "Jul": 9800, "Aug": 10000, "Sep": 10200},
    },
    "Environmental Services": {
        2025: {"Nov": 5000, "Dec": 5200},
        2026: {"Jan": 5400, "Feb": 5500, "Mar": 5600, "Apr": 5700, "May": 5800,
               "Jun": 5900, "Jul": 6000, "Aug": 6100, "Sep": 6200},
    },
    "Fire Safety": {
        2025: {"Nov": 7000, "Dec": 7200},
        2026: {"Jan": 7400, "Feb": 7600, "Mar": 7800, "Apr": 8000, "May": 8200,
               "Jun": 8400, "Jul": 8600, "Aug": 8800, "Sep": 9000},
    },
    "Leak, Damp & Restoration": {
        2025: {"Nov": 15000, "Dec": 15500},
        2026: {"Jan": 15700, "Feb": 16000, "Mar": 16250, "Apr": 16500, "May": 16750,
               "Jun": 17000, "Jul": 17250, "Aug": 17500, "Sep": 17750},
    },
    "Plumbing & Drainage": {
        2025: {"Nov": 12000, "Dec": 12500},
        2026: {"Jan": 12750, "Feb": 890000, "Mar": 13250, "Apr": 13500, "May": 13750,
               "Jun": 14000, "Jul": 14250, "Aug": 14500, "Sep": 14750},
    },
}

def get_sales_target(trade_group: str, month: str, year: int = 2025) -> float:
    month_key = MONTH_MAP.get(month, month)
    trade_group_clean = trade_group.strip().lower()
    matched_group = next((k for k in SALES_TARGETS if k.lower() == trade_group_clean), None)
    if matched_group is None:
        return 0.0
    return SALES_TARGETS.get(matched_group, {}).get(year, {}).get(month_key, 0.0)

def calculate_target_achievement(actual: float, trade_group: str, month: str, year: int = 2025) -> float:
    normalised_month = MONTH_MAP.get(month, month)
    target = get_sales_target(trade_group, normalised_month, year)
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
