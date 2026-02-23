# backend.py
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from simple_salesforce import Salesforce
from simple_salesforce.login import SalesforceLogin
import logging
import toml
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Make sure we can import targets.py from same folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from targets import (  # noqa: E402
    get_sales_target,
    calculate_kpi_score,
    get_category_score,
    get_overall_score,
    calculate_ops_count_achievement,
)

import queries  # noqa: E402

import re


def normalise_kpi_name(name: str):
    if not isinstance(name, str):
        return name

    # Replace ANY unicode whitespace with a normal space
    name = re.sub(r"\s+", " ", name, flags=re.UNICODE)

    # Replace invisible Unicode characters
    for bad in ["\u00A0", "\u2009", "\u202F", "\u2060", "\uFEFF"]:
        name = name.replace(bad, " ")

    return name.strip()


def get_previous_month_range(start_iso: str) -> tuple[str, str]:
    """
    Given start_iso of selected month,
    return (start_iso, end_iso) for the PREVIOUS month.
    """
    dt = datetime.fromisoformat(start_iso.replace("Z", ""))
    first_of_current = dt.replace(day=1)
    last_of_previous = first_of_current - timedelta(seconds=1)
    first_of_previous = last_of_previous.replace(day=1)

    return (
        first_of_previous.strftime("%Y-%m-%dT00:00:00Z"),
        last_of_previous.strftime("%Y-%m-%dT23:59:59Z"),
    )


# ============================================================
# ✅ Quarter Helpers (ADDED)
# ============================================================

MONTH_KEYS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def _shift_months(year: int, month: int, delta: int) -> tuple[int, int]:
    m = month + delta
    y = year
    while m <= 0:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    return y, m


def _quarter_month_key_years_from_iso(start_iso: str) -> List[Tuple[str, int]]:
    """
    For a given month start_iso, return the rolling quarter months (including that month):
      [(MonKey, Year), (MonKey, Year), (MonKey, Year)]
    """
    try:
        dt = datetime.fromisoformat(start_iso.replace("Z", ""))
    except Exception:
        try:
            dt = datetime.strptime(start_iso[:10], "%Y-%m-%d")
        except Exception:
            dt = datetime.now()

    y, m = dt.year, dt.month
    y1, m1 = _shift_months(y, m, -2)
    y2, m2 = _shift_months(y, m, -1)

    return [
        (MONTH_KEYS[m1 - 1], y1),
        (MONTH_KEYS[m2 - 1], y2),
        (MONTH_KEYS[m - 1], y),
    ]


def _quarter_range_from_month_range(start_iso: str, end_iso: str) -> Tuple[str, str]:
    """
    Convert selected month start/end into rolling quarter start/end.
    Quarter end remains end_iso (end of selected month / now if current month).
    Quarter start becomes first day of month-2 at 00:00:00Z.
    """
    try:
        dt = datetime.fromisoformat(start_iso.replace("Z", ""))
    except Exception:
        try:
            dt = datetime.strptime(start_iso[:10], "%Y-%m-%d")
        except Exception:
            dt = datetime.now()

    y, m = dt.year, dt.month
    y_start, m_start = _shift_months(y, m, -2)
    q_start_iso = f"{y_start}-{m_start:02d}-01T00:00:00Z"
    q_end_iso = end_iso
    return q_start_iso, q_end_iso


def _quarter_sales_target(trade_group: str, start_iso: str) -> float:
    """
    Sum of monthly sales targets for the rolling quarter.
    Uses get_sales_target (already imported).
    """
    total = 0.0
    for mon, yr in _quarter_month_key_years_from_iso(start_iso):
        try:
            total += float(get_sales_target(trade_group, mon, yr) or 0.0)
        except Exception:
            total += 0.0
    return float(total)


def _quarter_ops_target_avg(trade_group: str, start_iso: str) -> float:
    """
    Ops Count is headcount-style (snapshot), so quarter target should be the average of month targets.
    Uses existing calculate_ops_count_achievement for monthly elsewhere, but here we compute target average directly.
    """
    # calculate_ops_count_achievement expects actual + month/year and looks up monthly target.
    # We don't have direct access to targets dict here, so we compute achievement per month target
    # by reconstructing target through that function is not possible.
    # Instead: we try importing get_ops_count_target from targets if it exists; otherwise fallback to 0.
    try:
        from targets import get_ops_count_target  # type: ignore
    except Exception:
        get_ops_count_target = None

    if not get_ops_count_target:
        return 0.0

    vals = []
    for mon, yr in _quarter_month_key_years_from_iso(start_iso):
        try:
            t = get_ops_count_target(trade_group, mon, yr)
            if t is not None:
                vals.append(float(t))
        except Exception:
            pass
    return float(sum(vals) / len(vals)) if vals else 0.0


def _months_in_window_adjusted_qtd(end_iso: str) -> float:
    """
    Quarter-to-date months weight:
      months_in_window_adjusted = 1 + 1 + (days_elapsed_in_selected_month / total_days_in_selected_month)

    We infer the selected month from end_iso.
    """
    from calendar import monthrange

    dt = datetime.fromisoformat(end_iso.replace("Z", ""))
    total_days = monthrange(dt.year, dt.month)[1]
    days_elapsed = dt.day
    return 2.0 + (days_elapsed / total_days)


def _fmt_month_display(year: int, month: int) -> str:
    return f"{MONTH_KEYS[month-1]} {year}"


def build_last3_completed_months_context(
    *,
    selected_month_display: str,
    trade_group: str,
    trade_filter: str,
) -> Dict[str, Any]:
    """Build the quarterly_context expected by insights.engine.build_insights_payload().

    Fix logic (rolling 3 completed months):
      - If selected month is the CURRENT month, exclude it and anchor on previous month.
      - If selected month is a PAST month, anchor on selected month.
      - The returned window is [anchor-2, anchor-1, anchor] in chronological order.

    Examples:
      - Selected Feb 2026 (current month) -> Nov 2025, Dec 2025, Jan 2026
      - Selected Jan 2026 -> Nov 2025, Dec 2025, Jan 2026
      - Selected Dec 2025 -> Oct 2025, Nov 2025, Dec 2025
    """
    # Resolve trades from filter
    trades = resolve_trades_for_filters(trade_group, trade_filter)

    # parse selected month
    sel_start_iso, sel_end_iso = get_month_range(selected_month_display)

    now = datetime.now()

    try:
        sel_dt = datetime.fromisoformat(sel_start_iso.replace("Z", ""))
    except Exception:
        sel_dt = now

    # Determine month anchor
    anchor_year, anchor_month = sel_dt.year, sel_dt.month
    if sel_dt.year == now.year and sel_dt.month == now.month:
        anchor_year, anchor_month = _shift_months(anchor_year, anchor_month, -1)

    # build 3-months window ending at anchor
    y1, m1 = _shift_months(anchor_year, anchor_month, -2)
    y2, m2 = _shift_months(anchor_year, anchor_month, -1)
    y3, m3 = anchor_year, anchor_month

    quarter_months = [
        _fmt_month_display(y1, m1),
        _fmt_month_display(y2, m2),
        _fmt_month_display(y3, m3),
    ]

    # Fetch monthly payloads for each month
    month_payloads: List[Dict[str, Any]] = []
    for md in quarter_months:
        m_start_iso, m_end_iso = get_month_range(md)
        month_payloads.append(
            compute_kpis(
                trade_group_selected=trade_group,
                trades=trades,
                start_iso=m_start_iso,
                end_iso=m_end_iso,
                trade_filter=trade_filter,
                period="month",
            )
        )

    # fetch quarter result
    anchor_display = quarter_months[-1]
    anchor_start_iso, anchor_end_iso = get_month_range(anchor_display)

    quarter_result = compute_kpis(
        trade_group_selected=trade_group,
        trades=trades,
        start_iso=anchor_start_iso,
        end_iso=anchor_end_iso,
        trade_filter=trade_filter,
        period="quarter",
    )

    return {
        "quarter_months": quarter_months,
        "month_payloads": month_payloads,
        "quarter_result": quarter_result,
    }


# ============================================================
# Trade Groups / Mappings
# ============================================================

TRADE_GROUPS: Dict[str, List[str]] = {
    "HVac & Electrical": [
        "Electrical",
        "Heating & Hot Water (Domestic)",
        "Air Con, Ventilation & Refrigeration",
        "Heating & Hot Water (Commercial)",
        "Electrical Renewable",
        "Gas",
        "HVAC",
        "Utilities",
    ],
    "Building Fabric": [
        "Decorating",
        "Roofing/LeakDetection",
        "Windows & Doors",
        "Roofing",
        "Roof Window & Gutter Cleaning",
        "Handyman",
        "Carpentry",
        "Flooring Trade",
        "Plastering",
        "Project Management Refurbishment",
        "Tiling",
        "Fencing",
        "Brickwork & Paving",
        "Locksmithing",
        "Partition Walls & Ceilings",
        "Access",
        "Glazing",
        "Project Management Decoration",
        "General Refurbishment",
        "Wallpapering",
        "Bathroom Refurbishment",
        "Key",
        "PM",
        "Multi",
    ],
    "Environmental Services": [
        "Gardening",
        "Pest Control",
        "Rubbish Removal",
        "Pest Proofing",
        "Sanitisation & specialist cleaning",
    ],
    "Fire Safety": ["Fire Safety", "Fire Safety Consultation", "Vent Hygiene and Safety"],
    "Leak, Damp & Restoration": [
        "Leak Detection",
        "Leak Detection Restoration",
        "Leak Detection Restoration Drainage",
        "Leak Detection Restoration Plumbing",
        "Leak Detection Restoration Central Heating",
        "Damp & Mould",
        "Damp Proofing",
        "LD Commercial Mains Water Leak",
        "LD commercial Gas",
        "LD Damp Restoration",
        "Leak Detection Building Fabric",
        "Leak Detection Domestic Plumbing",
        "Leak Detection Industrial Plumbing",
        "Leak Detection Domestic Gas & Heating",
        "Damp Survey",
        "Mould Survey",
        "Damp Survey Roofing",
        "Leak Detection Commercial Gas & Heating",
        "Leak Detection Industrial Gas & Heating",
        "Leak Detection Diving",
    ],
    "Plumbing & Drainage": [
        "Drainage (Soil Water)",
        "Plumbing & Cold Water",
        "Drainage (Wastewater)",
        "Drainage Restoration",
        "Drainage (Tanker)",
        "Commercial Pumps",
        "Drainage (Septic Tanks)",
        "Drainage Leak Detection",
        "Plumbing",
        "Drainage",
    ],
}

TRADE_SUBGROUPS = {
    "HVac & Electrical": {
        "Air Conditioning": [
            "Air Con, Ventilation & Refrigeration",
        ],
        "Gas & Heating": [
            "Heating & Hot Water (Domestic)",
            "Heating & Hot Water (Commercial)",
            "Gas",
            "HVAC",
        ],
        "Electrical": [
            "Electrical",
            "Electrical Renewable",
        ],
    },
    "Building Fabric": {
        "Decoration": [
            "Decorating",
            "Plastering",
            "Tiling",
            "Wallpapering",
            "Multi",
        ],
        "Roofing": [
            "Roofing/LeakDetection",
            "Roofing",
            "Roof Window & Gutter Cleaning",
        ],
        "Multi Trades": [
            "Windows & Doors",
            "Handyman",
            "Carpentry",
            "Flooring Trade",
            "Fencing",
            "Brickwork & Paving",
            "Locksmithing",
            "Partition Walls & Ceilings",
            "Access",
            "Glazing",
        ],
        "Project Management": [
            "Project Management Refurbishment",
            "General Refurbishment",
            "Bathroom Refurbishment",
            "Project Management Decoration",
        ],
    },
    "Environmental Services": {
        "Gardening": [
            "Gardening",
        ],
        "Pest Control": [
            "Pest Control",
            "Pest Proofing",
        ],
        "Specialist Cleaning": [
            "Sanitisation & specialist cleaning",
        ],
        "Waste and Grease Management": [
            "Rubbish Removal",
        ],
    },
    "Fire Safety": {
        "Fire Safety": [
            "Fire Safety",
            "Fire Safety Consultation",
            "Vent Hygiene and Safety",
        ],
    },
    "Leak, Damp & Restoration": {
        "Leak Detection": [
            "Leak Detection",
            "Leak Detection Restoration",
            "Leak Detection Restoration Drainage",
            "Leak Detection Restoration Plumbing",
            "Leak Detection Restoration Central Heating",
            "LD Commercial Mains Water Leak",
            "LD commercial Gas",
            "LD Damp Restoration",
            "Leak Detection Building Fabric",
            "Leak Detection Domestic Plumbing",
            "Leak Detection Industrial Plumbing",
            "Leak Detection Domestic Gas & Heating",
            "Leak Detection Commercial Gas & Heating",
            "Leak Detection Industrial Gas & Heating",
            "Leak Detection Diving",
        ],
        "Damp": [
            "Damp & Mould",
            "Damp Proofing",
            "Damp Survey",
            "Mould Survey",
            "Damp Survey Roofing",
        ],
    },
    "Plumbing & Drainage": {
        "Plumbing": [
            "Plumbing",
            "Plumbing & Cold Water",
        ],
        "Drainage": [
            "Drainage (Soil Water)",
            "Drainage (Wastewater)",
            "Drainage Restoration",
            "Drainage (Tanker)",
            "Commercial Pumps",
            "Drainage (Septic Tanks)",
            "Drainage",
            "Drainage Leak Detection",
        ],
    },
}


TRADE_TO_GROUP: Dict[str, str] = {}
for group, trades in TRADE_GROUPS.items():
    for t in trades:
        TRADE_TO_GROUP[t.lower()] = group

# Mapping from trade group names to simplified names used in dynamic KPI thresholds
# This is used for per-trade scoring of dynamic KPIs
TRADE_GROUP_TO_SIMPLE_NAMES: Dict[str, List[str]] = {
    "HVac & Electrical": ["HVAC", "Electrical"],
    "Plumbing & Drainage": ["Plumbing"],
    "Building Fabric": ["Plumbing"],
    "Environmental Services": ["Plumbing"],
    "Fire Safety": ["Plumbing"],
    "Leak, Damp & Restoration": ["Plumbing"],
}

TRADE_ALIASES = {
    "plumbing": "Plumbing & Drainage",
    "drainage": "Plumbing & Drainage",
    "electrical": "HVac & Electrical",
    "hvac": "HVac & Electrical",
    "heating": "HVac & Electrical",
    "air con": "HVac & Electrical",
    "air conditioning": "HVac & Electrical",
    "building": "Building Fabric",
    "decorating": "Building Fabric",
    "roofing": "Building Fabric",
    "gardening": "Environmental Services",
    "pest": "Environmental Services",
    "fire": "Fire Safety",
    "leak": "Leak, Damp & Restoration",
    "damp": "Leak, Damp & Restoration",
}


def get_trade_list(group_name: str) -> List[str]:
    """
    Frontend uses this to get list of trades for selected group.
    If 'All Groups', return every trade in TRADE_GROUPS.
    """
    if group_name == "All Groups":
        return [t for sub in TRADE_GROUPS.values() for t in sub]
    return TRADE_GROUPS.get(group_name, [])


# ============================================================
# Month Filters (Used by Frontend to Pick Month)
# ============================================================

# Helper for dynamic month ranges
def get_last_day_of_month(year: int, month: int) -> int:
    import calendar

    return calendar.monthrange(year, month)[1]


def list_available_months() -> List[str]:
    """
    Generates a list of the last 24 months (e.g., 'Feb 2026', 'Jan 2026')
    starting from the current month.
    """
    now = datetime.now()
    months = []
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    curr_month = now.month
    curr_year = now.year

    for _ in range(24):
        months.append(f"{month_names[curr_month-1]} {curr_year}")
        curr_month -= 1
        if curr_month == 0:
            curr_month = 12
            curr_year -= 1

    return months


def get_month_range(month_display: str) -> Tuple[str, str]:
    """
    Converts 'Feb 2026' into ISO start/end.
    If it's the current month, end is 'now'.
    """
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    now = datetime.now()
    month_idx = now.month
    year = now.year

    try:
        parts = month_display.split()
        if len(parts) == 2:
            m_name, year_str = parts
            if m_name in month_names:
                month_idx = month_names.index(m_name) + 1
                year = int(year_str)
    except Exception:
        pass  # Fallback to current month set above

    start_iso = f"{year}-{month_idx:02d}-01T00:00:00Z"

    if year == now.year and month_idx == now.month:
        # Current month: end at current time
        end_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        # Past month: end at last day
        last_day = get_last_day_of_month(year, month_idx)
        end_iso = f"{year}-{month_idx:02d}-{last_day:02d}T23:59:59Z"

    return start_iso, end_iso


def infer_month_key_and_year_from_iso(start_iso: str):
    try:
        # Try parsing ISO with timezone
        dt = datetime.fromisoformat(start_iso.replace("Z", ""))
    except Exception:
        # Fallback: try parsing just YYYY-MM-DD
        try:
            dt = datetime.strptime(start_iso[:10], "%Y-%m-%d")
        except Exception:
            # Final fallback to today to avoid crashing
            dt = datetime.now()

    month_keys = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    return month_keys[dt.month - 1], dt.year


# ============================================================
# Secrets Loader
# ============================================================
def get_secrets():
    try:
        with open("secrets.toml", "r") as f:
            return toml.load(f)
    except FileNotFoundError:
        logger.warning("secrets.toml not found")
        return {}


# ============================================================
# Salesforce Client
# ============================================================

@lru_cache(maxsize=1)
def sf_client() -> Salesforce:
    s = get_secrets()["salesforce"]
    session_id, instance = SalesforceLogin(
        username=s["username"],
        password=s["password"],
        security_token=s["security_token"],
        domain=s["domain"],
    )
    return Salesforce(session_id=session_id, instance=instance)


# ============================================================
# Utility Helpers
# ============================================================

def _strip_attrs(records: List[dict]) -> List[dict]:
    for r in records:
        r.pop("attributes", None)
    return records


def _chunk(lst: List[str], n: int = 200) -> List[List[str]]:
    return [lst[i : i + n] for i in range(0, len(lst), n)]


@lru_cache(maxsize=128)
def sf_query_df(soql: str) -> pd.DataFrame:
    res = sf_client().query_all(soql)
    return pd.DataFrame(_strip_attrs(res.get("records", [])))


def map_trade_to_group(t: str) -> str:
    if not t:
        return "Unmapped"
    t = t.lower().strip()

    if t in TRADE_TO_GROUP:
        return TRADE_TO_GROUP[t]

    for alias, grp in TRADE_ALIASES.items():
        if alias in t:
            return grp

    return "Unmapped"


def resolve_trades_for_filters(trade_group: str, trade_filter: str) -> List[str]:
    """
    Returns the list of trades to use for KPI calculation
    based on Trade Group + Trade filter.
    """
    if trade_filter == "All":
        return get_trade_list(trade_group)

    subgroup = TRADE_SUBGROUPS.get(trade_group, {})
    return subgroup.get(trade_filter, get_trade_list(trade_group))


# ============================================================
# Webfleet API
# ============================================================

def get_webfleet_config() -> Optional[Dict]:
    try:
        wf = get_secrets()["webfleet"]
        apikey = wf.get("apikey") or wf.get("api_key")
        if not apikey:
            return None
        return {
            "account": wf["account"],
            "username": wf["username"],
            "password": wf["password"],
            "apikey": apikey,
            "base_url": wf.get("base_url", "https://csv.webfleet.com/extern"),
        }
    except Exception:
        return None


@lru_cache(maxsize=1)
def fetch_webfleet_drivers() -> pd.DataFrame:
    config = get_webfleet_config()
    if not config:
        return pd.DataFrame()

    params = {
        "action": "showDriverReportExtern",
        "account": config["account"],
        "apikey": config["apikey"],
        "lang": "en",
        "outputformat": "json",
        "useUTF8": "true",
        "useISO8601": "true",
    }

    try:
        r = requests.get(
            config["base_url"],
            params=params,
            auth=HTTPBasicAuth(config["username"], config["password"]),
            timeout=20,
        )
        if r.status_code != 200:
            return pd.DataFrame()

        data = r.json()
        if not isinstance(data, list):
            return pd.DataFrame()

        rows = [
            {
                "Driver No": (d.get("driverno") or "").strip(),
                "Driver Name": (d.get("name1") or "").strip(),
                "Email": (d.get("email") or "").strip().lower(),
            }
            for d in data
        ]

        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


@lru_cache(maxsize=1)
def fetch_optidrive_scores_bulk() -> pd.DataFrame:
    config = get_webfleet_config()
    if not config:
        return pd.DataFrame()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    params = {
        "action": "showOptiDriveIndicator",
        "account": config["account"],
        "username": config["username"],
        "password": config["password"],
        "apikey": config["apikey"],
        "lang": "en",
        "outputformat": "json",
        "useUTF8": "true",
        "useISO8601": "true",
        "rangefrom_string": start_date.strftime("%Y%m%d"),
        "rangeto_string": end_date.strftime("%Y%m%d"),
    }

    try:
        r = requests.get(config["base_url"], params=params, timeout=60)
        if r.status_code != 200:
            return pd.DataFrame()

        data = r.json()
        return pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


# ============================================================
# Salesforce Fetchers
# ============================================================

@lru_cache(maxsize=1)
def fetch_service_resources() -> pd.DataFrame:
    q = queries.get_service_resources_query()
    df = sf_query_df(q)
    if df.empty:
        return df

    df.rename(columns={"Id": "ServiceResourceId"}, inplace=True)

    # Use .get() so missing columns do not throw KeyError
    related_email = df.get("RelatedRecord.Email")

    if related_email is not None:
        df["Email"] = df["Email__c"].fillna(related_email)
    else:
        df["Email"] = df["Email__c"]

    df["Email"] = df["Email"].astype(str).str.lower()

    df["Trade Group"] = df["Trade_Lookup__c"].apply(map_trade_to_group)
    df.rename(columns={"Name": "Engineer Name"}, inplace=True)
    return df


@lru_cache(maxsize=128)
def fetch_ops_count(trades: Tuple[str]) -> int:
    # Changed list to tuple for lru_cache compatibility
    if not trades:
        return 0
    excluded = {"Key", "Utilities", "PM", "Test Ops"}
    filtered_trades = [t for t in trades if t not in excluded]
    if not filtered_trades:
        return 0

    trades_str = ",".join([f"'{t}'" for t in filtered_trades])
    q = queries.get_ops_count_query(trades_str)
    try:
        res = sf_client().query(q)
        records = res.get("records", [])
        if records:
            return records[0].get("cnt", 0)
        return 0
    except Exception:
        return 0


@lru_cache(maxsize=1)
def fetch_total_ops_count() -> int:
    q = queries.get_total_ops_count_query()
    try:
        res = sf_client().query(q)
        records = res.get("records", [])
        if records:
            return records[0].get("cnt", 0)
        return 0
    except Exception:
        return 0


@lru_cache(maxsize=128)
def fetch_cases_count(trades: Tuple[str], start_iso: str, end_iso: str) -> int:
    """Count Cases by Service_Resource__r.Trade_Lookup__c and date."""
    if not trades:
        return 0
    trades_str = ",".join([f"'{t}'" for t in trades])
    q = queries.get_cases_count_query(trades_str, start_iso, end_iso)
    try:
        res = sf_client().query(q)
        records = res.get("records", [])
        if records:
            return records[0].get("cnt", 0)
        return 0
    except Exception as e:
        logger.warning(f"⚠️ Case query error: {e}")
        return 0


@lru_cache(maxsize=128)
def fetch_engineer_satisfaction(trades: Tuple[str], start_iso: str, end_iso: str) -> Tuple[Optional[float], int]:
    """Average engineer satisfaction score for given trades."""
    if not trades:
        return None, 0
    trades_str = ",".join([f"'{t}'" for t in trades])
    q = queries.get_engineer_satisfaction_query(trades_str, start_iso, end_iso)
    try:
        res = sf_client().query_all(q)
        records = res.get("records", [])
        if not records:
            return None, 0
        scores = [r.get("Total_Score__c") for r in records if r.get("Total_Score__c") is not None]
        if not scores:
            return None, 0
        avg_score = sum(scores) / len(scores)
        return avg_score, len(scores)
    except Exception as e:
        logger.warning(f"⚠️ Survey query error: {e}")
        return None, 0


@lru_cache(maxsize=128)
def fetch_customer_invoice_sales(trades: Tuple[str], start_iso: str, end_iso: str) -> Tuple[float, float]:
    """Return (filtered_sales_for_trades, total_sales_all_non_key_accounts)."""
    start_date = start_iso[:10]
    end_date = end_iso[:10]
    trade_list = ", ".join([f"'{t}'" for t in trades])

    q_total = queries.get_total_invoice_sales_query(start_date, end_date)
    q_filtered = queries.get_filtered_invoice_sales_query(trade_list, start_date, end_date)

    total = 0.0
    filtered = 0.0

    try:
        res_total = sf_client().query(q_total)
        total_val = res_total["records"][0].get("total_sales")
        total = float(total_val) if total_val else 0.0

        res_filtered = sf_client().query(q_filtered)
        filtered_val = res_filtered["records"][0].get("total_sales")
        filtered = float(filtered_val) if filtered_val else 0.0

        return filtered, total

    except Exception as e:
        logger.error(f"Invoice query error: {e}")
        return 0.0, 0.0


@lru_cache(maxsize=128)
def fetch_job_history_closed(start_iso: str, end_iso: str) -> pd.DataFrame:
    q = queries.get_job_history_closed_query(start_iso, end_iso)
    df = sf_query_df(q)
    if df.empty:
        return df
    return df[df["NewValue"] == "Closed"].copy()


@lru_cache(maxsize=128)
def fetch_jobs_by_ids(job_ids: Tuple[str]) -> pd.DataFrame:
    """Fetch jobs by IDs, excluding Key Accounts."""
    if not job_ids:
        return pd.DataFrame()
    frames = []
    for batch in _chunk(job_ids, 200):
        id_str = ",".join([f"'{x}'" for x in batch])
        q = queries.get_jobs_by_ids_query(id_str)
        frames.append(sf_query_df(q))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


@lru_cache(maxsize=128)
def fetch_jobs_created_between(trades: Tuple[str], start_iso: str, end_iso: str) -> pd.DataFrame:
    """Jobs created in date range, excluding Key Accounts."""
    if not trades:
        return pd.DataFrame()
    trades_str = ",".join([f"'{t}'" for t in trades])
    q = queries.get_jobs_created_between_query(trades_str, start_iso, end_iso)
    return sf_query_df(q)


@lru_cache(maxsize=128)
def fetch_service_appointments_by_job_ids(job_ids: Tuple[str]) -> pd.DataFrame:
    """Service appointments by job IDs, excluding Key Accounts."""
    # Convert tuple back to list for internal usage if needed, or _chunk handles it (it expects list-like)
    job_ids = list(job_ids)
    if not job_ids:
        return pd.DataFrame()

    frames = []
    for batch in _chunk(job_ids, 200):
        id_str = ",".join([f"'{x}'" for x in batch])
        q = queries.get_service_appointments_query(id_str)
        frames.append(sf_query_df(q))

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


@lru_cache(maxsize=128)
def fetch_service_appointments_month(trades: Tuple[str], start_iso: str, end_iso: str) -> pd.DataFrame:
    """Service appointments in month, excluding Key Accounts."""
    if not trades:
        return pd.DataFrame()
    trades_str = ",".join([f"'{t}'" for t in trades])
    q = queries.get_service_appointments_month_query(trades_str, start_iso, end_iso)
    return sf_query_df(q)


@lru_cache(maxsize=128)
def fetch_workorders_month(trades: Tuple[str], start_iso: str, end_iso: str) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame()
    trades_str = ",".join([f"'{t}'" for t in trades])
    q = queries.get_workorders_month_query(trades_str, start_iso, end_iso)
    return sf_query_df(q)


@lru_cache(maxsize=128)
def fetch_vcr_forms(start_iso: str, end_iso: str) -> pd.DataFrame:
    q = queries.get_vcr_forms_query(start_iso, end_iso)
    return sf_query_df(q)


@lru_cache(maxsize=128)
def fetch_jobs_created_and_closed_count(
    trades: Tuple[str],
    start_iso: str,
    end_iso: str,
) -> int:
    if not trades:
        return 0

    trades_str = ",".join([f"'{t}'" for t in trades])
    q = queries.get_jobs_created_and_closed_count_query(trades_str, start_iso, end_iso)
    try:
        res = sf_client().query(q)
        return res["records"][0].get("expr0", 0)
    except Exception:
        return 0


# ============================================================
# Vehicular Merge + KPI
# ============================================================

def get_merged_vehicular_data() -> pd.DataFrame:
    df_drivers = fetch_webfleet_drivers()
    df_optidrive = fetch_optidrive_scores_bulk()
    df_engineers = fetch_service_resources()

    if df_optidrive.empty:
        return pd.DataFrame()

    df_optidrive["driverno_clean"] = df_optidrive["driverno"].astype(str).str.strip().str.lower()
    df_drivers["driverno_clean"] = df_drivers["Driver No"].astype(str).str.strip().str.lower()

    df_merged = df_optidrive.merge(
        df_drivers[["driverno_clean", "Email"]],
        on="driverno_clean",
        how="left",
    )

    df_merged["Email_Lower"] = df_merged["Email"].fillna("").astype(str).str.lower().str.strip()

    if not df_engineers.empty:
        df_engineers["Email_Lower"] = df_engineers["Email"].astype(str).str.lower().str.strip()
        df_merged = df_merged.merge(
            df_engineers[["Email_Lower", "Trade Group", "Engineer Name"]],
            on="Email_Lower",
            how="left",
        )
    else:
        df_merged["Trade Group"] = "Unknown"
        df_merged["Engineer Name"] = ""

    df_merged["Trade Group"] = df_merged["Trade Group"].fillna("Unknown")
    df_merged = df_merged.drop(columns=["driverno_clean", "Email_Lower"], errors="ignore")

    return df_merged


def calculate_vehicular_kpi(df_veh: pd.DataFrame, trade_group: str) -> dict:
    if df_veh.empty:
        return {
            "avg_driving_score": None,
            "driver_count": 0,
            "drivers_below_7_pct": None,
        }

    df_trade = df_veh[df_veh["Trade Group"] == trade_group]
    if df_trade.empty:
        return {
            "avg_driving_score": None,
            "driver_count": 0,
            "drivers_below_7_pct": None,
        }

    score_col = (
        "optidrive_indicator"
        if "optidrive_indicator" in df_trade.columns
        else "OptiDrive Score"
        if "OptiDrive Score" in df_trade.columns
        else None
    )
    if not score_col:
        return {
            "avg_driving_score": None,
            "driver_count": 0,
            "drivers_below_7_pct": None,
        }

    scores = pd.to_numeric(df_trade[score_col], errors="coerce").dropna()
    if scores.empty:
        return {
            "avg_driving_score": None,
            "driver_count": 0,
            "drivers_below_7_pct": None,
        }

    scores_scaled = scores * 10
    drivers_below_7 = int((scores_scaled < 7).sum())
    drivers_below_7_pct = (drivers_below_7 / len(scores) * 100) if len(scores) > 0 else None

    return {
        "avg_driving_score": float(scores.mean() * 10),
        "driver_count": int(len(scores)),
        "drivers_below_7_pct": float(drivers_below_7_pct) if drivers_below_7_pct is not None else None,
    }


def rename_job_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Helper to rename Salesforce job columns to internal names."""
    if df.empty:
        return df
    mapping = {
        "Id": "Job ID",
        "Name": "Job Name",
        "Job_Type_Trade__c": "Trade",
        "Type__c": "Job Type",
        "Status__c": "Job Status",
        "Charge_Policy__c": "Charge Policy",
        "Customer_Facing_Description__c": "Customer Comment",
        "Raised_from_Job__c": "Raised From Job",
        "Charge_Net__c": "Charge Net",
        "Job_Duration__c": "Job Duration",
    }
    # Only rename columns that exist
    to_rename = {k: v for k, v in mapping.items() if k in df.columns}
    return df.rename(columns=to_rename)


def calculate_conversion_metrics(df_history: pd.DataFrame, df_jobs_month: pd.DataFrame) -> Tuple[float, float]:
    """
    Calculates Estimated Conversion % and FOC Conversion Rate %.
    """
    if df_jobs_month.empty:
        return 0.0, 0.0

    # Updated mapping: "For Client Approval" is the key indicator for a sent estimate
    sent_statuses = ["For Client Approval", "Approved by Client", "Quote Sent"]
    sent = len(df_jobs_month[df_jobs_month["Job Status"].isin(sent_statuses)]) if "Job Status" in df_jobs_month.columns else 0
    converted = len(df_history[df_history["NewValue"] == "Closed"]) if "NewValue" in df_history.columns else 0

    conv_pct = (converted / sent * 100) if sent > 0 else 0.0

    foc_rate = 0.0
    if "Charge Policy" in df_jobs_month.columns:
        # Data investigation showed "FOC Estimate" as the predominant FOC policy
        foc_jobs = len(df_jobs_month[df_jobs_month["Charge Policy"].isin(["Free of Charge", "FOC Estimate"])])
        foc_rate = (foc_jobs / len(df_jobs_month) * 100)

    return float(conv_pct), float(foc_rate)


# ============================================================
# HIGH-LEVEL KPI ENGINE
# ============================================================

def calculate_dynamic_kpi_per_trade(
    kpi_name: str,
    df_data: pd.DataFrame,
    trade_group: str,
    trade_filter: str = "All",
    score_divisor: Optional[float] = None,  # ✅ ADDED (non-breaking)
) -> dict:
    """
    Calculate a dynamic KPI value and score per individual trade, then aggregate.

    Args:
        kpi_name: Name of the dynamic KPI (e.g., "SA Attended", "Average Site Value (£)")
        df_data: DataFrame containing the data with a 'Trade' column
        trade_group: The trade group name (e.g., "HVac & Electrical")
        trade_filter: Specific trade filter or "All"
        score_divisor: If provided, the value used for scoring is (value / score_divisor),
                       while the returned 'value' remains the raw aggregated value.

    Returns:
        dict with 'value' (aggregated) and 'score' (aggregated)
    """
    from targets import calculate_kpi_score

    # Get the simplified trade names for this trade group
    simple_trades = TRADE_GROUP_TO_SIMPLE_NAMES.get(trade_group, ["Plumbing"])

    # If a specific trade is selected, only use that one
    if trade_filter and trade_filter != "All":
        # Map the filter to a simple trade name if needed
        simple_trades = [t for t in simple_trades if t.lower() in trade_filter.lower()]
        if not simple_trades:
            simple_trades = TRADE_GROUP_TO_SIMPLE_NAMES.get(trade_group, ["Plumbing"])[:1]

    if df_data.empty or "Trade" not in df_data.columns:
        return {"value": 0.0, "score": 0}

    trade_scores = []
    trade_values = []
    trade_counts = []

    for simple_trade in simple_trades:
        # Filter data for this specific trade
        # Match trades that contain the simple trade name
        trade_data = df_data[df_data["Trade"].str.contains(simple_trade, case=False, na=False)]

        if trade_data.empty:
            continue

        # Calculate KPI value for this trade (raw)
        if kpi_name == "SA Attended":
            value = float(len(trade_data))
        elif kpi_name == "Average Site Value (£)":
            if "Charge Net" in trade_data.columns:
                value = float(trade_data["Charge Net"].mean())
            else:
                value = 0.0
        elif kpi_name == "Average Converted Estimate Value (£)":
            if "Charge Net" in trade_data.columns:
                converted = trade_data[trade_data["Job Status"].isin(["Converted", "Closed"])]
                value = float(converted["Charge Net"].mean()) if not converted.empty else 0.0
            else:
                value = 0.0
        else:
            value = 0.0

        # ✅ Score using adjusted value (if score_divisor provided)
        value_for_scoring = value
        if score_divisor is not None:
            try:
                d = float(score_divisor)
                if d > 0:
                    value_for_scoring = value / d
            except Exception:
                pass

        # Score this trade's value using its specific thresholds
        score_result = calculate_kpi_score(kpi_name, value_for_scoring, simple_trade)
        score = score_result.get("score", 0) if score_result.get("score") is not None else 0

        trade_values.append(value)
        trade_scores.append(score)
        trade_counts.append(len(trade_data))

    # Aggregate: weighted average by count
    if not trade_scores:
        return {"value": 0.0, "score": 0}

    total_count = sum(trade_counts)
    if total_count == 0:
        aggregated_score = sum(trade_scores) / len(trade_scores)
        aggregated_value = sum(trade_values) / len(trade_values)
    else:
        aggregated_score = sum(s * c for s, c in zip(trade_scores, trade_counts)) / total_count
        aggregated_value = sum(v * c for v, c in zip(trade_values, trade_counts)) / total_count

    return {"value": float(aggregated_value), "score": int(round(aggregated_score))}


def compute_kpis(
    trade_group_selected: str,
    trades: List[str],
    start_iso: str,
    end_iso: str,
    trade_filter: str = "All",
    period: str = "month",  # ✅ ADDED (default keeps existing behavior)
) -> dict:
    """
    High-level KPI computation:
    - Fetches all required data (Salesforce + Webfleet)
    - Re-implements your old monolithic logic
    - Returns:
        {
            "kpis": {flat KPIs, numeric},
            "categories": {Conversion/Procedural/...},
            "category_scores": {0-100 per category},
            "overall_score": float,
        }
    """

    try:
        # ✅ If quarterly, widen the date range FIRST, then fetch ONCE for the quarter
        if period == "quarter":
            start_iso, end_iso = _quarter_range_from_month_range(start_iso, end_iso)

        # Convert trades list to tuple for lru_cache compatibility
        trades_tuple = tuple(trades)

        # --------------------------------------------------------
        # 1. Parallel data fetch
        # --------------------------------------------------------
        def _run_futures(fmap: dict, timeout: int = 180) -> dict:
            results = {}
            with ThreadPoolExecutor(max_workers=8) as ex:
                fut_to_key = {ex.submit(fn): key for key, fn in fmap.items()}
                for fut in as_completed(fut_to_key, timeout=timeout):
                    key = fut_to_key[fut]
                    try:
                        results[key] = fut.result()
                    except Exception as e:
                        logger.warning(f"⚠️ Fetch failed for {key}: {e}")
                        results[key] = (
                            pd.DataFrame()
                            if key
                            not in {
                                "ops_count",
                                "total_ops_count",
                                "engineer_satisfaction",
                                "cases_count",
                                "invoice_sales",
                                "total_invoice_sales",
                            }
                            else 0
                        )
            return results

        stage1 = _run_futures(
            {
                "history": lambda: fetch_job_history_closed(start_iso, end_iso),
                "jobs_month": lambda: fetch_jobs_created_between(trades_tuple, start_iso, end_iso),
                "workorders": lambda: fetch_workorders_month(trades_tuple, start_iso, end_iso),
                "sa_month": lambda: fetch_service_appointments_month(trades_tuple, start_iso, end_iso),
                "vehicular": lambda: get_merged_vehicular_data(),
                "vcr_forms": lambda: fetch_vcr_forms(start_iso, end_iso),
            },
            timeout=180,
        )

        ops_count = fetch_ops_count(trades_tuple)
        total_ops_count = fetch_total_ops_count()
        engineer_satisfaction, engineer_survey_count = fetch_engineer_satisfaction(trades_tuple, start_iso, end_iso)

        cases_start_iso, cases_end_iso = get_previous_month_range(start_iso)
        cases_count = fetch_cases_count(trades_tuple, cases_start_iso, cases_end_iso)
        invoice_sales, total_invoice_sales = fetch_customer_invoice_sales(trades_tuple, start_iso, end_iso)

        df_history = stage1["history"]
        df_jobs_month = rename_job_columns(stage1["jobs_month"])
        df_wo_month = stage1["workorders"]
        df_sa_month_all = stage1["sa_month"]
        df_vehicular = stage1["vehicular"]
        df_vcr = stage1["vcr_forms"]
        df_engineers = fetch_service_resources()

        if df_history.empty:
            return {
                "overall_score": 0.0,
                "bonus": {
                    "current_band": "below",
                    "bonus_value": 0.0,
                    "note": "No data available (SF connection failed or no jobs closed).",
                },
                "categories": {},
                "kpi_scores": {},
                "category_scores": {},
                "kpis": {},
            }

        # --------------------------------------------------------
        # 2. Process Data
        # --------------------------------------------------------
        df_history["CreatedDate"] = pd.to_datetime(df_history["CreatedDate"], errors="coerce")
        df_history = df_history.rename(columns={"ParentId": "Job ID"})
        job_ids_closed = tuple(df_history["Job ID"].dropna().astype(str).unique().tolist())

        df_jobs_closed = rename_job_columns(fetch_jobs_by_ids(job_ids_closed))
        df_sa = fetch_service_appointments_by_job_ids(job_ids_closed)

        df_jobs_closed["Job Duration"] = pd.to_numeric(df_jobs_closed.get("Job Duration"), errors="coerce")
        df_closed = df_history.merge(df_jobs_closed, on="Job ID", how="left")

        # --------------------------------------------------------
        # 3. Compute Metrics
        # --------------------------------------------------------
        # Conversion
        estimated_conversion_pct, foc_conversion_rate = calculate_conversion_metrics(df_history, df_jobs_month)

        total_jobs = len(job_ids_closed)
        reactive_leads_count = len(df_closed[df_closed["Job Type"] == "Reactive"])

        estimate_production_count = 0
        if not df_jobs_month.empty:
            estimate_production_count = df_jobs_month[
                (df_jobs_month["Job Type"] == "Reactive") & (df_jobs_month["Job Status"] != "Cancelled")
            ].shape[0]

        estimate_production_pct = (
            (estimate_production_count / reactive_leads_count * 100) if reactive_leads_count > 0 else None
        )

        # Dynamic KPIs - calculate per trade and aggregate
        avg_converted_estimate_result = calculate_dynamic_kpi_per_trade(
            "Average Converted Estimate Value (£)",
            df_jobs_month,
            trade_group_selected,
            trade_filter,
        )
        avg_converted_estimate_value = avg_converted_estimate_result["value"]

        # Prepare workorder data with Trade column for per-trade calculation
        df_wo_with_trade = df_wo_month.copy()
        if not df_wo_with_trade.empty and "CCT_Charge_NET__c" in df_wo_with_trade.columns:
            df_wo_with_trade["Charge Net"] = df_wo_with_trade["CCT_Charge_NET__c"]
            if "CCT_Trade__c" in df_wo_with_trade.columns:
                df_wo_with_trade["Trade"] = df_wo_with_trade["CCT_Trade__c"]
            elif "Trade__c" in df_wo_with_trade.columns:
                df_wo_with_trade["Trade"] = df_wo_with_trade["Trade__c"]
            elif "Job__r.Job_Type_Trade__c" in df_wo_with_trade.columns:
                df_wo_with_trade["Trade"] = df_wo_with_trade["Job__r.Job_Type_Trade__c"]

        avg_site_value_result = calculate_dynamic_kpi_per_trade(
            "Average Site Value (£)",
            df_wo_with_trade,
            trade_group_selected,
            trade_filter,
        )
        avg_site_value = avg_site_value_result["value"]

        # Callbacks
        def detect_callback(row):
            cp = str(row.get("Charge Policy") or "").lower()
            comment = str(row.get("Customer Comment") or "").lower()
            return ("callback" in comment) or ("call back" in comment) or (cp == "call back")

        callback_jobs_count = int(df_closed.apply(detect_callback, axis=1).sum())
        callback_jobs_pct = (callback_jobs_count / total_jobs * 100) if total_jobs > 0 else None

        # 6+ Hours
        jobs_6_plus_df = df_closed[(df_closed["Job Type"] == "Reactive") & (df_closed["Job Duration"] >= 6)]
        jobs_6_plus_total = len(jobs_6_plus_df)
        jobs_6_plus_pct = (jobs_6_plus_total / reactive_leads_count * 100) if reactive_leads_count > 0 else 0.0

        jobs_6_plus_by_status = {}
        if not jobs_6_plus_df.empty:
            status_counts = jobs_6_plus_df.groupby("Job Status").size().sort_values(ascending=False)
            jobs_6_plus_by_status = status_counts.to_dict()

        # Service Appointments - calculate per trade
        df_sa_with_trade = df_sa_month_all.copy()
        if not df_sa_with_trade.empty:
            # Add Trade column if not present
            if "CCT_Trade__c" in df_sa_with_trade.columns:
                df_sa_with_trade["Trade"] = df_sa_with_trade["CCT_Trade__c"]
            elif "ServiceAppointment.CCT_Trade__c" in df_sa_with_trade.columns:
                df_sa_with_trade["Trade"] = df_sa_with_trade["ServiceAppointment.CCT_Trade__c"]
            elif "Job__r" in df_sa_with_trade.columns:

                def extract_trade(val):
                    if isinstance(val, dict):
                        return val.get("Job_Type_Trade__c")
                    return None

                df_sa_with_trade["Trade"] = df_sa_with_trade["Job__r"].apply(extract_trade)

        # ✅ QTD pro-rating divisor for SA Attended scoring (thresholds.json stays monthly)
        sa_score_divisor = None
        if period == "quarter":
            sa_score_divisor = _months_in_window_adjusted_qtd(end_iso)

        sa_attended_result = calculate_dynamic_kpi_per_trade(
            "SA Attended",
            df_sa_with_trade,
            trade_group_selected,
            trade_filter,
            score_divisor=sa_score_divisor,  # ✅ ADDED (only affects scoring, not returned value)
        )
        service_appts_count = int(sa_attended_result["value"])
        unclosed_sa_count = (
            df_sa_month_all[~df_sa_month_all["Status"].isin(["Visit Complete", "Cancelled"])].shape[0]
            if not df_sa_month_all.empty
            else 0
        )
        unclosed_sa_pct = (unclosed_sa_count / service_appts_count * 100) if service_appts_count > 0 else None

        late_count = df_sa_month_all[df_sa_month_all["Status"] == "Late"].shape[0] if not df_sa_month_all.empty else 0
        late_pct = (late_count / service_appts_count * 100) if service_appts_count > 0 else 0.0

        # Satisfaction
        count_reviews = engineer_survey_count
        avg_rating_val = engineer_satisfaction

        # TQR Ratio
        tqr_total_count = 0
        tqr_not_satisfied_count = 0
        tqr_ratio_pct = None
        tqr_not_satisfied_ratio_pct = None

        service_appts_count = 0
        sa_attended_count = 0
        count_reviews = 0
        avg_review_rating = None
        review_ratio_pct = None
        late_count = 0
        late_pct = 0.0

        if not df_sa.empty:
            df_sa_month = df_sa[df_sa["Job__c"].astype(str).isin(job_ids_closed)].copy()
            service_appts_count = len(df_sa_month)

            attended = df_sa_month[df_sa_month["Status"] == "Visit Complete"]
            sa_attended_count = len(attended)

            with_review = attended[attended["Review_Star_Rating__c"].notna()].copy()
            with_review["Review_Star_Rating__c"] = pd.to_numeric(with_review["Review_Star_Rating__c"], errors="coerce")
            with_review = with_review.dropna(subset=["Review_Star_Rating__c"])
            count_reviews = len(with_review)
            avg_review_rating = round(with_review["Review_Star_Rating__c"].mean(), 1) if count_reviews else None
            review_ratio_pct = (count_reviews / sa_attended_count * 100) if sa_attended_count > 0 else None

            if "ActualStartTime" in df_sa_month.columns and "ArrivalWindowStartTime" in df_sa_month.columns:
                df_sa_month["ActualStartTime"] = pd.to_datetime(df_sa_month["ActualStartTime"], errors="coerce")
                df_sa_month["ArrivalWindowStartTime"] = pd.to_datetime(
                    df_sa_month["ArrivalWindowStartTime"], errors="coerce"
                )
                df_sa_month["Late"] = (
                    (df_sa_month["ActualStartTime"] - df_sa_month["ArrivalWindowStartTime"]).dt.total_seconds() / 60 > 30
                )
                late_count = int(df_sa_month["Late"].sum())
                late_pct = (late_count / service_appts_count * 100) if service_appts_count > 0 else 0.0

            df_tqr = df_sa_month[df_sa_month["Post_Visit_Report_Check__c"] == "TQR"].drop_duplicates(subset=["Job__c"])
            tqr_total_count = len(df_tqr)
            tqr_ratio_pct = (tqr_total_count / len(job_ids_closed) * 100) if len(job_ids_closed) > 0 else None

            if "Job__r" in df_tqr.columns:

                def extract_satisfied(val):
                    if isinstance(val, dict):
                        return val.get("Final_WO_Is_the_Customer_Satisfied__c")
                    return None

                df_tqr["Satisfied_Val"] = df_tqr["Job__r"].apply(extract_satisfied)
                tqr_not_satisfied_count = len(df_tqr[df_tqr["Satisfied_Val"] == "No"])
            elif "Job__r.Final_WO_Is_the_Customer_Satisfied__c" in df_tqr.columns:
                tqr_not_satisfied_count = len(df_tqr[df_tqr["Job__r.Final_WO_Is_the_Customer_Satisfied__c"] == "No"])
            elif "Final_WO_Is_the_Customer_Satisfied__c" in df_tqr.columns:
                tqr_not_satisfied_count = len(df_tqr[df_tqr["Final_WO_Is_the_Customer_Satisfied__c"] == "No"])

            tqr_not_satisfied_ratio_pct = (
                (tqr_not_satisfied_count / tqr_total_count * 100) if tqr_total_count > 0 else None
            )

        # Cases % (Previous Month)
        total_jobs_prev = fetch_jobs_created_and_closed_count(trades_tuple, cases_start_iso, cases_end_iso)
        cases_pct = (cases_count / total_jobs_prev * 100) if total_jobs_prev > 0 else None

        # Hardcoded Placeholders (as per original snippet)
        engineer_retention_pct = 80.0
        monthly_working_time = 200.0
        absence_pct = 10.0

        # VCR
        vcr_count = 0
        if not df_vcr.empty and not df_engineers.empty:
            df_vcr_merged = df_vcr.merge(
                df_engineers[["ServiceResourceId", "Trade Group"]],
                left_on="Current_Engineer_Assigned_to_Vehicle__c",
                right_on="ServiceResourceId",
                how="left",
            )
            vcr_count = df_vcr_merged[df_vcr_merged["Trade Group"] == trade_group_selected].shape[0]
        vcr_update_pct = (vcr_count / (ops_count * 4) * 100) if ops_count > 0 else None

        # Vehicular
        vehicular_data = calculate_vehicular_kpi(df_vehicular, trade_group_selected)
        driving_score = vehicular_data.get("avg_driving_score", 0.0) or 0.0
        drivers_below_7_pct = vehicular_data.get("drivers_below_7_pct", 0.0) or 0.0

        # Sales Target Achievement %
        month_key, year = infer_month_key_and_year_from_iso(start_iso)

        # ✅ If quarterly, compute quarter target (sum of 3 months) and achievement vs quarter Invoice Sales
        if period == "quarter":
            sales_target = _quarter_sales_target(trade_group_selected, start_iso)
            sales_target_achievement = (invoice_sales / sales_target * 100) if sales_target > 0 else 0.0
        else:
            sales_target = get_sales_target(trade_group_selected, month_key, year)
            sales_target_achievement = (invoice_sales / sales_target * 100) if sales_target > 0 else 0.0

        # Ops Count
        if period == "quarter":
            ops_target_avg = _quarter_ops_target_avg(trade_group_selected, start_iso)
            ops_achievement = (ops_count / ops_target_avg * 100) if ops_target_avg > 0 else 0.0
        else:
            ops_achievement = calculate_ops_count_achievement(ops_count, trade_group_selected, month_key, year)

        # --------------------------------------------------------
        # 4. Flat KPI dict (Standardized names for targets.py)
        # --------------------------------------------------------
        kpis = {
            "Estimate Conversion %": float(estimated_conversion_pct),
            "FOC Conversion Rate %": float(foc_conversion_rate),
            "Reactive Leads": int(reactive_leads_count),
            "Estimate Production": int(estimate_production_count),
            "Estimate Production / Reactive Leads %": float(estimate_production_pct)
            if estimate_production_pct is not None
            else None,
            "Average Converted Estimate Value (£)": float(avg_converted_estimate_value),
            "Average Site Value (£)": float(avg_site_value),
            "Callback Jobs %": float(callback_jobs_pct) if callback_jobs_pct is not None else None,
            "Callback Jobs Count": int(callback_jobs_count),
            "Jobs with 6+ Hours": int(jobs_6_plus_total),
            "Reactive 6+ hours %": float(jobs_6_plus_pct),
            "Service Appointments": int(service_appts_count),
            "SA Attended": int(sa_attended_result["value"]),
            "Unclosed SA %": float(unclosed_sa_pct) if unclosed_sa_pct is not None else None,
            "Late to Site": int(late_count),
            "Late to Site %": float(late_pct),
            "VCR Update %": float(vcr_update_pct) if vcr_update_pct is not None else None,
            "VCR Count": int(vcr_count),
            "Engineer Satisfaction %": float(engineer_satisfaction) if engineer_satisfaction is not None else None,
            "Average Driving Score": float(driving_score),
            "Drivers with <7 %": float(drivers_below_7_pct),
            "Ops Count %": float(ops_achievement),
            "Ops Count": int(ops_count),
            "Total Ops Count": int(total_ops_count),
            "TQR Ratio %": float(tqr_ratio_pct) if tqr_ratio_pct is not None else None,
            "TQR Count": int(tqr_total_count),
            "TQR (Not Satisfied) Ratio %": float(tqr_not_satisfied_ratio_pct)
            if tqr_not_satisfied_ratio_pct is not None
            else None,
            "TQR (Not Satisfied) Count": int(tqr_not_satisfied_count),
            "Average Review Rating": float(avg_review_rating) if avg_review_rating is not None else None,
            "Review Ratio %": float(review_ratio_pct) if review_ratio_pct is not None else None,
            "Reviews Count": int(count_reviews),
            "Cases %": float(cases_pct) if cases_pct is not None else None,
            "Cases Count": int(cases_count),
            "Engineer Retention %": float(engineer_retention_pct),
            "Sales Target Achievement %": float(sales_target_achievement),
            "Sales Target": float(sales_target),
            "Invoice Sales": float(invoice_sales),
            "Total Invoice Sales": float(total_invoice_sales),
            "Monthly Working Time (hrs)": float(monthly_working_time),
            "Absence %": float(absence_pct),
            "Top Performers %": 20.0,
            "Red Flags %": 20.0,
            "Engineer Survey Count": int(engineer_survey_count),
            "Drivers in Trade Group": int(vehicular_data.get("driver_count", 0)),
        }

        # --------------------------------------------------------
        # 5. Grouped categories (Aligned with backend_original.py)
        # --------------------------------------------------------
        categories = {
            "Conversion": {
                "Estimate Production / Reactive Leads %": kpis["Estimate Production / Reactive Leads %"],
                "Estimate Conversion %": kpis["Estimate Conversion %"],
                "FOC Conversion Rate %": kpis["FOC Conversion Rate %"],
                "Average Converted Estimate Value (£)": kpis["Average Converted Estimate Value (£)"],
            },
            "Procedural": {
                "TQR Ratio %": kpis["TQR Ratio %"],
                "TQR (Not Satisfied) Ratio %": kpis["TQR (Not Satisfied) Ratio %"],
                "Unclosed SA %": kpis["Unclosed SA %"],
                "Reactive 6+ hours %": kpis["Reactive 6+ hours %"],
            },
            "Satisfaction": {
                "Average Review Rating": kpis["Average Review Rating"],
                "Review Ratio %": kpis["Review Ratio %"],
                "Engineer Satisfaction %": kpis["Engineer Satisfaction %"],
                "Cases %": kpis["Cases %"],
                "Engineer Retention %": kpis["Engineer Retention %"],
            },
            "Vehicular": {
                "Average Driving Score": kpis["Average Driving Score"],
                "Drivers with <7 %": kpis["Drivers with <7 %"],
                "VCR Update %": kpis["VCR Update %"],
            },
            "Productivity": {
                "Ops Count %": kpis["Ops Count %"],
                "Sales Target Achievement %": kpis["Sales Target Achievement %"],
                "Monthly Working Time (hrs)": kpis["Monthly Working Time (hrs)"],
                "Callback Jobs %": kpis["Callback Jobs %"],
                "SA Attended": kpis["SA Attended"],
                "Average Site Value (£)": kpis["Average Site Value (£)"],
                "Late to Site %": kpis["Late to Site %"],
                "Absence %": kpis["Absence %"],
            },
        }

        # --------------------------------------------------------
        # 6. Scores & Bonus
        # --------------------------------------------------------

        # Collect pre-calculated scores for dynamic KPIs
        precalc_scores = {
            "Average Converted Estimate Value (£)": avg_converted_estimate_result.get("score"),
            "Average Site Value (£)": avg_site_value_result.get("score"),
            "SA Attended": sa_attended_result.get("score"),  # ✅ now QTD-pro-rated for scoring if period=="quarter"
        }

        kpi_scores = {}
        for kpi_name, kpi_value in kpis.items():
            if kpi_name in precalc_scores and precalc_scores[kpi_name] is not None:
                kpi_scores[kpi_name] = precalc_scores[kpi_name]
                continue

            clean_name = normalise_kpi_name(kpi_name)
            score_result = calculate_kpi_score(clean_name, kpi_value, trade_group_selected)
            if score_result and score_result.get("score") is not None:
                kpi_scores[kpi_name] = score_result["score"]

        category_scores = {}
        for cat in categories:
            cat_res = get_category_score(cat, kpis, trade_group_selected)
            category_scores[cat] = cat_res.get("category_score", 0.0) or 0.0

        overall_result = get_overall_score(kpis, trade_group_selected)
        bonus = overall_result.get("bonus", {})

        multiplier = bonus.get("multiplier", 0)
        current_band = "below"
        if multiplier > 0:
            current_band = "gold"
        elif multiplier == 0:
            current_band = "silver"
        else:
            current_band = "bronze"
        bonus["current_band"] = current_band

        return {
            "kpis": kpis,
            "kpi_scores": kpi_scores,
            "categories": categories,
            "category_scores": category_scores,
            "overall_score": float(overall_result.get("overall_score", 0.0)),
            "bonus": bonus,
            "jobs_6_plus_by_status": jobs_6_plus_by_status,
        }
    except Exception as e:
        logger.error(f"Global error in compute_kpis: {e}", exc_info=True)
        return {
            "overall_score": 0.0,
            "bonus": {"current_band": "below", "bonus_value": 0.0, "note": f"System error during calculation: {e}"},
            "categories": {},
            "kpi_scores": {},
            "category_scores": {},
            "kpis": {},
        }


# ============================================================
# ✅ Quarterly Trend History Helpers (ADDED ONLY)
# ============================================================

def _parse_iso_dt(iso_str: str) -> datetime:
    try:
        return datetime.fromisoformat(iso_str.replace("Z", ""))
    except Exception:
        try:
            return datetime.strptime(iso_str[:19], "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return datetime.strptime(iso_str[:10], "%Y-%m-%d")


def _month_start_iso_from_dt(dt: datetime) -> str:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT00:00:00Z")


def _month_end_iso_from_dt(dt: datetime) -> str:
    # end of month 23:59:59Z
    year, month = dt.year, dt.month
    last_day = get_last_day_of_month(year, month)
    return f"{year}-{month:02d}-{last_day:02d}T23:59:59Z"


def _add_months(dt: datetime, months: int) -> datetime:
    y = dt.year
    m = dt.month + months
    while m > 12:
        m -= 12
        y += 1
    while m <= 0:
        m += 12
        y -= 1
    # clamp day safely (we always use day=1 for anchors)
    return dt.replace(year=y, month=m, day=1)


def _quarter_label_from_anchor(dt: datetime) -> str:
    # Rolling quarter ending at anchor month.
    # Label as "QTD ending Mon YYYY" to avoid implying calendar-quarter alignment.
    return f"Rolling QTD ending {MONTH_KEYS[dt.month - 1]} {dt.year}"


# NOTE: renamed to avoid overwriting the other function
def build_quarterly_history_quarter_step(
    *,
    trade_group_selected: str,
    trades: List[str],
    trade_filter: str,
    trend_start_iso: str,
    trend_end_iso: str,
) -> Dict[str, Any]:
    """
    Build quarterly history over an arbitrary trend window.

    - Uses rolling quarters (same definition as compute_kpis(period="quarter")).
    - Uses anchor months stepped by 3 months.
    - Each element in history is the compute_kpis() output for that quarter.

    Returns:
      {
        "trend_start_iso": ...,
        "trend_end_iso": ...,
        "quarters": [
           {"label": "...", "anchor_month_start_iso": "...", "anchor_month_end_iso": "...", "result": {...}},
           ...
        ]
      }

    IMPORTANT: this does NOT change compute_kpis; it only provides the data needed for insights over time.
    """
    start_dt = _parse_iso_dt(trend_start_iso)
    end_dt = _parse_iso_dt(trend_end_iso)

    # Normalize to month starts
    cur = start_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_anchor = end_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Step by 3 months to represent quarter anchors
    quarters: List[Dict[str, Any]] = []
    guard = 0
    while cur <= end_anchor and guard < 400:  # guard against infinite loops
        guard += 1
        anchor_start_iso = _month_start_iso_from_dt(cur)

        # For the very last anchor month, if trend_end_iso is inside that month, cap end to trend_end_iso
        if cur.year == end_dt.year and cur.month == end_dt.month:
            anchor_end_iso = trend_end_iso
        else:
            anchor_end_iso = _month_end_iso_from_dt(cur)

        result = compute_kpis(
            trade_group_selected=trade_group_selected,
            trades=trades,
            start_iso=anchor_start_iso,
            end_iso=anchor_end_iso,
            trade_filter=trade_filter,
            period="quarter",
        )

        quarters.append(
            {
                "label": _quarter_label_from_anchor(cur),
                "anchor_month_start_iso": anchor_start_iso,
                "anchor_month_end_iso": anchor_end_iso,
                "result": result,
            }
        )

        cur = _add_months(cur, 3)

    return {
        "trend_start_iso": trend_start_iso,
        "trend_end_iso": trend_end_iso,
        "quarters": quarters,
    }


# NOTE: renamed to avoid overwriting the other function
def build_quarterly_history_month_step(
    *,
    trade_group_selected: str,
    trades: List[str],
    start_month_iso: str,
    end_month_iso: str,
    trade_filter: str = "All",
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Build a time series of rolling-quarter KPI results.

    Inputs are MONTH start ISOs (YYYY-MM-01T00:00:00Z), inclusive.
    The function steps month-by-month from start_month_iso to end_month_iso
    and for each month computes the rolling quarter ending in that month.

    Returns a list of dicts:
      [{ "month_end": "Feb 2026", "start_iso": ..., "end_iso": ..., "result": <compute_kpis output> }, ...]
    """

    def _parse_month_start(iso: str) -> datetime:
        return datetime.fromisoformat(iso.replace("Z", "")).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def _fmt_month(dt: datetime) -> str:
        return f"{MONTH_KEYS[dt.month-1]} {dt.year}"

    start_dt = _parse_month_start(start_month_iso)
    end_dt = _parse_month_start(end_month_iso)

    out: List[Dict[str, Any]] = []
    cur = start_dt

    while cur <= end_dt:
        # month range for THIS month
        month_display = _fmt_month(cur)
        month_start_iso = f"{cur.year}-{cur.month:02d}-01T00:00:00Z"

        # end iso: last day of that month at 23:59:59Z (historical months)
        last_day = get_last_day_of_month(cur.year, cur.month)
        month_end_iso = f"{cur.year}-{cur.month:02d}-{last_day:02d}T23:59:59Z"

        # compute rolling quarter for that end-month
        res = compute_kpis(
            trade_group_selected=trade_group_selected,
            trades=trades,
            start_iso=month_start_iso,
            end_iso=month_end_iso,
            trade_filter=trade_filter,
            period="quarter",
        )

        out.append(
            {
                "month": month_display,  # quarter-ending month label
                "month_start_iso": month_start_iso,
                "month_end_iso": month_end_iso,
                "result": res,
            }
        )

        if limit is not None and len(out) >= limit:
            break

        # step to next month
        y, m = _shift_months(cur.year, cur.month, 1)
        cur = cur.replace(year=y, month=m, day=1)

    return out