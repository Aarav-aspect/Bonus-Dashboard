import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import toml
from functools import lru_cache
import re

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from simple_salesforce import Salesforce
from simple_salesforce.login import SalesforceLogin

import queries
import kpi_details
from mapping import get_region_for_trade, TRADE_GROUP_PHASE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Make sure we can import targets.py from same folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from targets import (
    get_sales_target,
    get_ops_count_target,
    calculate_kpi_score,
    get_category_score,
    get_overall_score,
    calculate_ops_count_achievement,
)

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

# Trade Groups / Mappings

TRADE_GROUPS: Dict[str, List[str]] = {
    "HVac & Electrical": [
        "Electrical", "Heating & Hot Water (Domestic)", "Air Con, Ventilation & Refrigeration",
        "Heating & Hot Water (Commercial)", "Electrical Renewable", "Gas", "HVAC",
    ],
    "Building Fabric": [
        "Decorating", "Roofing/LeakDetection", "Windows & Doors", "Roofing",
        "Roof Window & Gutter Cleaning", "Handyman", "Carpentry", "Flooring Trade",
        "Plastering", "Project Management Refurbishment", "Tiling", "Fencing",
        "Brickwork & Paving", "Locksmithing", "Partition Walls & Ceilings", "Access",
        "Glazing", "Project Management Decoration", "General Refurbishment",
        "Wallpapering", "Bathroom Refurbishment", "Key", "PM", "Multi", "General Builders", "Decoration"
    ],
    "Environmental Services": [
        "Gardening", "Pest Control", "Rubbish Removal", "Pest Proofing",
        "Sanitisation & specialist cleaning", "Waste Clearance",
    ],
    "Fire Safety": ["Fire Safety", "Fire Safety Consultation", "Vent Hygiene and Safety", "Vent Hygiene"],
    "Leak, Damp & Restoration": [
        "Leak Detection", "Leak Detection Restoration", "Leak Detection Restoration Drainage",
        "Leak Detection Restoration Plumbing", "Leak Detection Restoration Central Heating",
        "Damp & Mould", "Damp Proofing", "LD Commercial Mains Water Leak",
        "LD commercial Gas", "LD Damp Restoration", "Leak Detection Building Fabric",
        "Leak Detection Domestic Plumbing", "Leak Detection Industrial Plumbing",
        "Leak Detection Domestic Gas & Heating",
        "Damp Survey", "Mould Survey", "Damp Survey Roofing",
        "Leak Detection Commercial Gas & Heating",
        "Leak Detection Industrial Gas & Heating", "Leak Detection Diving",
    ],
    "Plumbing & Drainage": [
        "Drainage (Soil Water)", "Plumbing & Cold Water", "Drainage (Wastewater)",
        "Drainage Restoration", "Drainage (Tanker)", "Commercial Pumps",
        "Drainage (Septic Tanks)", "Drainage Leak Detection",
        "Plumbing", "Drainage",
    ],
}

TRADE_SUBGROUPS = {
    "HVac & Electrical": {
        "Gas & HVAC": ["Air Con, Ventilation & Refrigeration", "Heating & Hot Water (Domestic)", "Heating & Hot Water (Commercial)", "Gas", "HVAC"],
        "Electrical": ["Electrical", "Electrical Renewable"],
    },
    "Building Fabric": {
        "Decoration": ["Decorating", "Plastering", "Tiling", "Wallpapering", "Decoration"],
        "Roofing": ["Roofing/LeakDetection", "Roofing", "Roof Window & Gutter Cleaning"],
        "Multi Trades": ["Windows & Doors", "Handyman", "Carpentry", "Flooring Trade", "Fencing", "Brickwork & Paving", "Locksmithing", "Partition Walls & Ceilings", "Access", "Glazing", "Multi", "General Builders"],
        "Project Management": ["Project Management Refurbishment", "General Refurbishment", "Bathroom Refurbishment", "Project Management Decoration"],
    },
    "Environmental Services": {
        "Gardening": ["Gardening"],
        "Pest Control": ["Pest Control", "Pest Proofing"],
        "Specialist Cleaning": ["Sanitisation & specialist cleaning"],
        "Waste and Grease Management": ["Rubbish Removal", "Waste Clearance"],
    },
    "Fire Safety": {
        "Fire Safety": ["Fire Safety", "Fire Safety Consultation", "Vent Hygiene and Safety"],
    },
    "Leak, Damp & Restoration": {
        "Leak Detection": [
            "Leak Detection", "Leak Detection Restoration", "Leak Detection Restoration Drainage",
            "Leak Detection Restoration Plumbing", "Leak Detection Restoration Central Heating",
            "LD Commercial Mains Water Leak", "LD commercial Gas", "LD Damp Restoration",
            "Leak Detection Building Fabric", "Leak Detection Domestic Plumbing",
            "Leak Detection Industrial Plumbing", "Leak Detection Domestic Gas & Heating",
            "Leak Detection Commercial Gas & Heating", "Leak Detection Industrial Gas & Heating",
            "Leak Detection Diving"
        ],
        "Damp": ["Damp & Mould", "Damp Proofing", "Damp Survey", "Mould Survey", "Damp Survey Roofing"],
    },
    "Plumbing & Drainage": {
        "Plumbing": ["Plumbing", "Plumbing & Cold Water"],
        "Drainage": ["Drainage (Soil Water)", "Drainage (Wastewater)", "Drainage Restoration", "Drainage (Tanker)", "Commercial Pumps", "Drainage (Septic Tanks)", "Drainage", "Drainage Leak Detection"],
    },
}

TRADE_TO_GROUP: Dict[str, str] = {}
for group, trades in TRADE_GROUPS.items():
    for t in trades:
        TRADE_TO_GROUP[t.lower()] = group

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

KEY_ACCOUNTS_FILTER_JOB = "AND Sector_Type__c != 'Key accounts' AND Account_Type__c != 'Key accounts'"
KEY_ACCOUNTS_FILTER_SA = "AND Job__r.Sector_Type__c != 'Key accounts' AND Job__r.Account_Type__c != 'Key accounts'"

def get_trade_list(group_name: str) -> List[str]:
    if group_name == "All Groups":
        return [t for sub in TRADE_GROUPS.values() for t in sub]
    return TRADE_GROUPS.get(group_name, [])


# Month Filters

def get_last_day_of_month(year: int, month: int) -> int:
    import calendar
    return calendar.monthrange(year, month)[1]

def list_available_months() -> List[str]:
    now = datetime.now()
    months = []
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
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
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
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
        pass 

    start_iso = f"{year}-{month_idx:02d}-01T00:00:00Z"
    
    if year == now.year and month_idx == now.month:
        end_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        last_day = get_last_day_of_month(year, month_idx)
        end_iso = f"{year}-{month_idx:02d}-{last_day:02d}T23:59:59Z"
        
    return start_iso, end_iso

def infer_month_key_and_year_from_iso(start_iso: str):
    try:
        dt = datetime.fromisoformat(start_iso.replace("Z", ""))
    except Exception:
        try:
            dt = datetime.strptime(start_iso[:10], "%Y-%m-%d")
        except Exception:
            dt = datetime.now()

    month_keys = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    return month_keys[dt.month - 1], dt.year


# Secrets & Salesforce Client
# ============================================================

def get_secrets():
    """Read secrets from secrets.toml or environment variables."""
    secrets = {}
    try:
        if os.path.exists("secrets.toml"):
            with open("secrets.toml", "r") as f:
                secrets = toml.load(f)
    except Exception as e:
        logger.warning(f"Error reading secrets.toml: {e}")

    # --- Salesforce ---
    if "salesforce" not in secrets:
        secrets["salesforce"] = {}
    
    sf = secrets["salesforce"]
    sf["username"] = os.getenv("SF_USERNAME", sf.get("username"))
    sf["password"] = os.getenv("SF_PASSWORD", sf.get("password"))
    sf["security_token"] = os.getenv("SF_SECURITY_TOKEN", sf.get("security_token"))
    sf["domain"] = os.getenv("SF_DOMAIN", sf.get("domain", "login"))

    # --- Webfleet ---
    if "webfleet" not in secrets:
        secrets["webfleet"] = {}
    
    wf = secrets["webfleet"]
    wf["account"] = os.getenv("WF_ACCOUNT", wf.get("account"))
    wf["username"] = os.getenv("WF_USERNAME", wf.get("username"))
    wf["password"] = os.getenv("WF_PASSWORD", wf.get("password"))
    wf["apikey"] = os.getenv("WF_APIKEY", wf.get("apikey"))
    # Support both key names for flexibility
    if not wf.get("apikey") and os.getenv("WF_API_KEY"):
         wf["apikey"] = os.getenv("WF_API_KEY")
    
    return secrets

@lru_cache(maxsize=1)
def sf_client() -> Salesforce:
    secrets = get_secrets()
    s = secrets.get("salesforce", {})
    
    # Validation
    required = ["username", "password", "security_token"]
    missing = [field for field in required if not s.get(field)]
    if missing:
        raise ValueError(f"Missing required Salesforce credentials: {', '.join(missing)}")

    session_id, instance = SalesforceLogin(
        username=s["username"],
        password=s["password"],
        security_token=s["security_token"],
        domain=s["domain"],
    )
    return Salesforce(session_id=session_id, instance=instance)


# Utility Helpers

def _strip_attrs(records: List[dict]) -> List[dict]:
    for r in records:
        r.pop("attributes", None)
    return records


def _chunk(lst: List[str], n: int = 200) -> List[List[str]]:
    return [lst[i:i + n] for i in range(0, len(lst), n)]


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
    if not trade_filter or trade_filter == "All":
        return get_trade_list(trade_group)
    
    subgroups = TRADE_SUBGROUPS.get(trade_group, {})
    if trade_filter in subgroups:
        return subgroups[trade_filter]
    
    return [trade_filter]

def get_ops_baseline_count(trade_group: str, trades: List[str], region_filter: str) -> int:
    """Returns the baseline headcount from ops_report.json for the given filters.
    
    ops_report.json is keyed by subgroup name (e.g. 'Multi Trades', 'Decoration'),
    so we first map the given list of raw trade names to their subgroups, then sum.
    If no subgroup is found (for trade groups without subgroups), we match directly.
    """
    try:
        import json
        path = os.path.join(os.path.dirname(__file__), "ops_report.json")
        if not os.path.exists(path):
            return 0
        with open(path, "r") as f:
            data = json.load(f)

        # Build reverse map: (trade_group, trade_name) -> subgroup_name
        subgroup_names_to_match = set()
        subgroups = TRADE_SUBGROUPS.get(trade_group, {})
        if subgroups:
            for subgroup_name, subgroup_trades in subgroups.items():
                if any(t in trades for t in subgroup_trades):
                    subgroup_names_to_match.add(subgroup_name)
        else:
            # No subgroups defined — match directly on trade names
            subgroup_names_to_match = set(trades)

        filtered = [
            item for item in data
            if item.get("Trade Group") == trade_group
            and item.get("Trade") in subgroup_names_to_match
        ]

        # Filter by region
        if region_filter != "All":
            filtered = [item for item in filtered if item.get("Region") == region_filter]

        return sum(item.get("Count", 0) for item in filtered)
    except Exception as e:
        logger.warning(f"Error reading ops_baseline: {e}")
        return 0


# Webfleet API

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
        logger.warning("⚠️ Webfleet config missing or incomplete")
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
            logger.error(f"❌ Webfleet drivers fetch failed: {r.status_code} - {r.text}")
            return pd.DataFrame()

        data = r.json()
        if not isinstance(data, list):
            logger.warning(f"⚠️ Webfleet drivers returned non-list data: {type(data)}")
            return pd.DataFrame()

        rows = [{
            "Driver No": (d.get("driverno") or "").strip(),
            "Driver Name": (d.get("name1") or "").strip(),
            "Email": (d.get("email") or "").strip().lower(),
        } for d in data]

        logger.info(f"✅ Fetched {len(rows)} drivers from Webfleet")
        return pd.DataFrame(rows)
    except Exception as e:
        logger.error(f"❌ Webfleet drivers exception: {e}")
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
            logger.error(f"❌ Webfleet optidrive fetch failed: {r.status_code} - {r.text}")
            return pd.DataFrame()

        data = r.json()
        if not isinstance(data, list):
            logger.warning(f"⚠️ Webfleet optidrive returned non-list data: {type(data)}")
            return pd.DataFrame()
            
        logger.info(f"✅ Fetched {len(data)} optidrive scores from Webfleet")
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"❌ Webfleet optidrive exception: {e}")
        return pd.DataFrame()


# ============================================================
# Salesforce Fetchers (Using queries.py)
# ============================================================

@lru_cache(maxsize=1)
def fetch_service_resources() -> pd.DataFrame:
    q = queries.get_service_resources_query()
    df = sf_query_df(q)
    if df.empty:
        return df

    df.rename(columns={"Id": "ServiceResourceId"}, inplace=True)
    related_email = df.get("RelatedRecord.Email")

    if related_email is not None:
        df["Email"] = df["Email__c"].fillna(related_email)
    else:
        df["Email"] = df["Email__c"]
        
    df["Email"] = df["Email"].astype(str).str.lower()
    df["Trade Group"] = df["Trade_Lookup__c"].apply(map_trade_to_group)
    df.rename(columns={"Name": "Engineer Name"}, inplace=True)
    
    # Postcode Fallback
    df["Effective_PostalCode__c"] = df["Residential_PostalCode__c"].fillna(df.get("Postcode_for_schedule_STM__c"))
    
    # Exclude specific names requested by user
    excluded_names = {"Project Management", "Electrical FOC Cover"}
    df = df[~df["Engineer Name"].isin(excluded_names)].copy()
    
    return df


@lru_cache(maxsize=128)
def fetch_ops_count(trades: Tuple[str], region_filter: str = "All", trade_group_selected: str = None) -> int:
    """Count active engineers matching the given trades/region using the same
    data source as the ops-list drilldown, so the two always agree."""
    if not trades:
        return 0
    excluded = {"Key", "Utilities", "PM", "Test Ops"}
    filtered_trades = [t for t in trades if t not in excluded]
    if not filtered_trades:
        return 0

    try:
        df = fetch_service_resources()
        if df.empty:
            return 0

        # Filter by trade
        df = df[df["Trade_Lookup__c"].isin(filtered_trades)]

        # Filter by region using the same Effective_PostalCode__c logic
        if region_filter != "All" and trade_group_selected:
            df = df[
                df["Effective_PostalCode__c"].apply(
                    lambda pc: get_region_for_trade(str(pc) if pc else "", trade_group_selected) == region_filter
                )
            ]

        return len(df)
    except Exception as e:
        logger.warning(f"⚠️ Ops count fallback: {e}")
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
def fetch_cases_data(trades: Tuple[str], start_iso: str, end_iso: str) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame()
    trades_str = ",".join([f"'{t}'" for t in trades])
    q = queries.get_cases_data_query(trades_str, start_iso, end_iso)
    try:
        res = sf_client().query_all(q)
        records = res.get("records", [])
        if records:
            df = pd.DataFrame(records)
            if "attributes" in df.columns:
                df = df.drop(columns=["attributes"])
            return df
        return pd.DataFrame()
    except Exception as e:
        logger.warning(f"⚠️ Case query error: {e}")
        return pd.DataFrame()


@lru_cache(maxsize=128)
def fetch_engineer_satisfaction(
    trades: Tuple[str], start_iso: str, end_iso: str, region_filter: str = "All", trade_group_selected: str = None
) -> Tuple[Optional[float], int]:
    if not trades:
        return None, 0
    trades_str = ",".join([f"'{t}'" for t in trades])
    q = queries.get_engineer_satisfaction_query(trades_str, start_iso, end_iso)
    try:
        res = sf_client().query_all(q)
        records = res.get("records", [])
        if not records:
            return None, 0
        
        df_surveys = pd.DataFrame(records)
        if "attributes" in df_surveys.columns:
            df_surveys = df_surveys.drop(columns=["attributes"])
            
        # If we need regional filtering, join with ServiceResource to get postcodes
        if region_filter != "All" and trade_group_selected:
            df_engineers = fetch_service_resources()
            if not df_engineers.empty:
                df_surveys = df_surveys.merge(
                    df_engineers[["ServiceResourceId", "Effective_PostalCode__c"]],
                    left_on="Service_Resource__c",
                    right_on="ServiceResourceId",
                    how="left"
                )
                # Filter by region based on engineer's effective postcode
                df_surveys = df_surveys[
                    df_surveys["Effective_PostalCode__c"].apply(
                        lambda pc: get_region_for_trade(str(pc) if pc else "", trade_group_selected) == region_filter
                    )
                ]

        if df_surveys.empty:
            return None, 0

        scores = df_surveys["Total_Score__c"].dropna().tolist()
        if not scores:
            return None, 0
        avg_score = sum(scores) / len(scores)
        return avg_score, len(scores)
    except Exception as e:
        logger.warning(f"⚠️ Survey query error: {e}")
        return None, 0


@lru_cache(maxsize=128)
def fetch_customer_invoice_sales(
    trades: Tuple[str], start_iso: str, end_iso: str, trade_group: str = "All Groups", region_filter: str = "All"
) -> Tuple[float, float]:
    start_date = start_iso[:10]
    end_date = end_iso[:10]
    trade_list = ", ".join([f"'{t}'" for t in trades])

    # If asking for "All" or it's a phase 1 group, use the fast SOQL SUM aggregate.
    phase = TRADE_GROUP_PHASE.get(trade_group, 1) if trade_group else 1
    if region_filter == "All" or phase == 1:
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
            logger.error(f"Invoice aggregate query error: {e}")
            return 0.0, 0.0

    # Otherwise (we need a specific region), fetch individual records and sum in Python.
    # Note: 'total' here usually means total for the trade, but since we are filtering by region,
    # the frontend expects 'filtered' to be the region total for the trades, and 'total' is usually
    # the entire business total. However, the exact KPI calculation divides 'filtered' by the target.
    # We will compute both filtered (the region total) and total (the full business total).
    
    q_all_trades_total = queries.get_total_invoice_sales_query(start_date, end_date)
    q_records = queries.get_invoice_records_query(trade_list, start_date, end_date)
    
    filtered_sum = 0.0
    total_business_sum = 0.0
    
    try:
        # Get overall business total (unfiltered by region for the KPI denominator context if needed)
        res_total = sf_client().query(q_all_trades_total)
        total_val = res_total["records"][0].get("total_sales")
        total_business_sum = float(total_val) if total_val else 0.0
        
        # Now fetch individual records for the selected trades to filter by region
        res_records = sf_client().query_all(q_records)
        records = res_records.get("records", [])
        
        for rec in records:
            postcode = rec.get("Site_Postal_Code__c") or ""
            charge = rec.get("Charge_Net__c")
            if not charge or pd.isna(charge):
                continue
                
            charge_val = float(charge)
            
            # Map postcode to region
            rec_region = get_region_for_trade(postcode, trade_group)
            
            # If the record matches the requested region filter, add to sum
            if rec_region == region_filter:
                filtered_sum += charge_val
                
        return filtered_sum, total_business_sum
        
    except Exception as e:
        logger.error(f"Invoice records query error: {e}")
        return 0.0, 0.0


@lru_cache(maxsize=128)
def fetch_live_collections(trades: Tuple[str], start_iso: str, end_iso: str) -> Dict[str, float]:
    start_date = start_iso[:10]
    end_date = end_iso[:10]
    
    if not trades:
        return {"collections": 0.0, "labour": 0.0, "materials": 0.0}
        
    group_list = ", ".join([f"'{t}'" for t in trades])
    q = queries.get_live_collections_query(group_list, start_date, end_date)

    try:
        res = sf_client().query(q)
        records = res.get("records", [])
        if records:
            total_coll = records[0].get("total_collected")
            total_lab = records[0].get("total_labour")
            total_mat = records[0].get("total_materials")
            return {
                "collections": float(total_coll) if total_coll else 0.0,
                "labour": float(total_lab) if total_lab else 0.0,
                "materials": float(total_mat) if total_mat else 0.0
            }
        return {"collections": 0.0, "labour": 0.0, "materials": 0.0}
    except Exception as e:
        logger.error(f"Live collections query error: {e}")
        return {"collections": 0.0, "labour": 0.0, "materials": 0.0}


@lru_cache(maxsize=128)
def fetch_job_history_closed(start_iso: str, end_iso: str) -> pd.DataFrame:
    q = queries.get_job_history_closed_query(start_iso, end_iso)
    df = sf_query_df(q)
    if df.empty:
        return df
    return df[df["NewValue"] == "Closed"].copy()


@lru_cache(maxsize=128)
def fetch_jobs_by_ids(job_ids: Tuple[str]) -> pd.DataFrame:
    if not job_ids:
        return pd.DataFrame()
    frames = []
    for batch in _chunk(list(job_ids), 200):
        id_str = ",".join([f"'{x}'" for x in batch])
        q = queries.get_jobs_by_ids_query(id_str)
        frames.append(sf_query_df(q))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


@lru_cache(maxsize=128)
def fetch_jobs_created_between(
    trades: Tuple[str], start_iso: str, end_iso: str
) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame()
    trades_str = ",".join([f"'{t}'" for t in trades])
    q = queries.get_jobs_created_between_query(trades_str, start_iso, end_iso)
    return sf_query_df(q)


@lru_cache(maxsize=128)
def fetch_service_appointments_by_job_ids(job_ids: Tuple[str]) -> pd.DataFrame:
    # Convert tuple back to list for _chunk
    job_ids_list = list(job_ids)
    if not job_ids_list:
        return pd.DataFrame()

    frames = []
    for batch in _chunk(job_ids_list, 200):
        id_str = ",".join([f"'{x}'" for x in batch])
        q = queries.get_service_appointments_query(id_str)
        frames.append(sf_query_df(q))

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


@lru_cache(maxsize=128)
def fetch_service_appointments_month(
    trades: Tuple[str], start_iso: str, end_iso: str
) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame()
    trades_str = ",".join([f"'{t}'" for t in trades])
    q = queries.get_service_appointments_month_query(trades_str, start_iso, end_iso)
    return sf_query_df(q)


@lru_cache(maxsize=128)
def fetch_reactive_sas(
    trades: Tuple[str], start_iso: str, end_iso: str
) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame()
    trades_str = ",".join([f"'{t}'" for t in trades])
    q = queries.get_reactive_sas_query(trades_str, start_iso, end_iso)
    return sf_query_df(q)


@lru_cache(maxsize=128)
def fetch_service_appointments_activity(
    trades: Tuple[str], start_iso: str, end_iso: str
) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame()
    trades_str = ",".join([f"'{t}'" for t in trades])
    q = queries.get_service_appointments_by_actual_start_query(trades_str, start_iso, end_iso)
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

# Email overrides: maps Webfleet email (lowercase) → correct Salesforce email (lowercase)
# Add new mismatches here whenever Webfleet and Salesforce emails don't align.
WEBFLEET_EMAIL_MAP = {
    "rionmanandvan@outlook.com":        "rion.peters@aspect.co.uk",
    "michael.hall@aspect.co.uk":        "ziaaspect@gmail.com",
    "iwanengineering@outlook.com":      "igor.bochentin@aspect.co.uk",
    "busterdoyle1@gmail.com":           "phillip.doyle@aspect.co.uk",
    "frankiemclintock14@gmail.com":     "frankie.mclintock@aspect.co.uk",
    "jimbohiggo2911@gmail.com":         "james.higgins@aspect.co.uk",
    "abuafzalmiah@hotmail.com":         "abu.miah@aspect.co.uk",
    "kofikonnect@gmail.com":            "kofi.boakye@aspect.co.uk",
    "reece.tullett@outlook.com":        "reece.tullett@aspect.co.uk",
    "joshieplayer@hotmail.co.uk":       "joshua.player@aspect.co.uk",
    "srboom@me.com":                    "steven.boom@aspect.co.uk",
    "darrenpodmore2025@outlook.com":    "darren.podmore@aspect.co.uk",
    "s.uelectricss@gmail.com":          "serhat.uysal@aspect.co.uk",
    "l.beeson@hotmail.com":             "lewis.beeson@aspect.co.uk",
    "owenct07@gmail.com":               "owen.taunton@aspect.co.uk",
    "artinpacolli@gmail.com":           "artin.pacoli@aspect.co.uk",
    "tdgallagher8777@yahoo.com":        "thomas.gallagher@aspect.co.uk",
    "jaywebster041@gmail.com":          "jay.webster@aspect.co.uk",
    "soloarribaa@gmail.com":            "nathan.sango@aspect.co.uk",
    "bowdensean6@gmail.com":            "sean.bowden@aspect.co.uk",
    "aarongale1998@icloud.com":         "aaron.gale@aspect.co.uk",
    "dwaynewilson420@gmail.com":        "dwayne.wilson@aspect.co.uk",
    "stingray2303@yahoo.com":           "matthew.boyes@aspect.co.uk",
    "tjay751@icloud.com":               "robbie.wray@aspect.co.uk",
    "emanuelshehi16@gmail.com":         "emanuel.shehi@aspect.co.uk",
 
    "montel.o@hotmail.com":             "montel.brown@aspect.co.uk",
 
    "relliot0722@gmail.com":            "robert.elliott@aspect.co.uk",
   
    "charlie.mitchel@aspect.co.uk":     "charlie.mitchell@aspect.co.uk",  # typo fix
 
    "ali.totali@aspect.co.uk":          "ali.tolali@aspect.co.uk",    # typo fix
 
     "office@bugthugsuk.com":          "mike.houareau@aspect.co.uk", 
    "ahmed.belafkih@aspet.co.uk":       "ahmed.belafkih@aspect.co.uk",  # typo fix
  
    "lukejcashin@gmail.com":            "luke.cashin@aspect.co.uk",
    "lukasz.zarebaasp@aspect.co.uk":    "amandeep.singh@aspect.co.uk",
    "aspect70@aspect.co.uk":            "patrick.read@aspect.co.uk",

    # --- Added from ops_not_on_webfleet audit (2026-03-05) ---
    # Igor Bochentin uses Mohamed Khalifa's Webfleet account
    "mohamed.khalifa@aspect.co.uk":     "igor.bochentin@aspect.co.uk",
    # Damp & Mould
    "danielnics@hotmail.co.uk":         "daniel.nichols@aspect.co.uk",
    "popedward116@gmail.com":           "simon.farthing@aspect.co.uk",

    # Drainage
    "tristanupton@hotmail.co.uk":       "tristan.upton@aspect.co.uk",
    "blake.benson84@gmail.com":         "blake.benson@aspect.co.uk",
    "bradleywells1983.bw@gmail.com":    "bradley.wells@aspect.co.uk",
    "aarongj.love@hotmail.com":         "aaron.love@aspect.co.uk",
    "wbrac.1745@gmail.com":             "warren.bracewell@aspect.co.uk",
    "maxxfurnell@gmail.com":            "max.furnell@aspect.co.uk",
    "harrybracewell012@googlemail.com": "harry.bracewell@aspect.co.uk",
    "alexguvenler@gmail.com":           "alex.guvenler@aspect.co.uk",
    "tomdavies461@gmail.com":           "tom.davies@aspect.co.uk",
    "harveygoldring96@icloud.com":      "harvey.goldring@aspect.co.uk",
    "shane_brady87@hotmail.com":        "shane.bradey@aspect.co.uk",

    # Electrical
    "redqos121@gmail.com":              "redi.qosja@aspect.co.uk",
    "astevey17@hotmail.co.uk":          "steve.freitas@aspect.co.uk",
    "elushmillion@icloud.com":          "emiljan.lushja@aspect.co.uk",
    "jordanleemcfeeters@yahoo.com":     "jordan.mcfeeters@aspect.co.uk",
    "angelos67duro@gmail.com":          "angelos.ntouro@aspect.co.uk",

    # Fire Safety
    "damienf.kfc@contractor.net":       "damien.fraser@aspect.co.uk",
    "touchoftimber@yahoo.com":          "james.teka@aspect.co.uk",

    # Gas
    "deepac.naidu@gmail.com":           "deepac.naidu@aspect.co.uk",
    "onuraraz@icloud.com":              "onur.araz@aspect.co.uk",
    "tannerhillyard@hotmail.com":       "tanner.hillyard@aspect.co.uk",
    "ashleyflash@hotmail.co.uk":        "ashley.flash@aspect.co.uk",
    "mundayconnah@gmail.com":           "connah.munday@aspect.co.uk",
    "mohamed_munye@hotmail.co.uk":      "igor.bochentin@aspect.co.uk",

    # HVAC
    "jackbalchin57@gmail.com":          "jack.ball@aspect.co.uk",

    # Leak Detection
    "denizinator@live.co.uk":           "deniz.okcay@aspect.co.uk",
    "joe.stedman@aspect.co.uk":         "joe.stedman@aspect.co.uk",   # case-fix
    "lukelazar89@gmail.com":            "luke.lazar@aspect.co.uk",
    "mclean_86@icloud.com":             "james.mclean@aspect.co.uk",
    "idsystems@live.co.uk":             "michael.hall@aspect.co.uk",
    "scottsmith9696@hotmail.co.uk":     "scott.smith@aspect.co.uk",
    "ollydealey@gmail.com":             "oliver.dealey@aspect.co.uk",
    

    # Multi / Building Fabric
    "arroncox64@yahoo.co.uk":           "aaron.cox@aspect.co.uk",

    # Pest Control (already mapped via office@bugthugsuk.com above)

    # Plumbing
    "willoughby172@hotmail.co.uk":      "william.hosford@aspect.co.uk",
    "camara0081@gmail.com":             "pedro.camara@aspect.co.uk",
    "steve_j135@hotmail.com":           "steven.hayden@aspect.co.uk",
    "dsestanovich@hotmail.com":         "daniel.sestanovich@aspect.co.uk",

    # Roofing
    "bradfilby@hotmail.com":            "bradley.filby@aspect.co.uk",
    "linksondaniel@gmail.com":          "daniel.linkson@aspect.co.uk",

    # Waste Clearance
    "swedigere@gmail.com":              "samuel.gebregziabiher@aspect.co.uk",
}

def get_merged_vehicular_data() -> pd.DataFrame:
    df_drivers = fetch_webfleet_drivers()
    df_optidrive = fetch_optidrive_scores_bulk()
    df_engineers = fetch_service_resources()

    if df_optidrive.empty:
        return pd.DataFrame()

    df_optidrive["driverno_clean"] = (
        df_optidrive["driverno"].astype(str).str.strip().str.lower()
    )
    df_drivers["driverno_clean"] = (
        df_drivers["Driver No"].astype(str).str.strip().str.lower()
    )

    df_merged = df_optidrive.merge(
        df_drivers[["driverno_clean", "Email"]],
        on="driverno_clean",
        how="left",
    )

    df_merged["Email_Lower"] = (
        df_merged["Email"].fillna("").astype(str).str.lower().str.strip()
    )

    # Apply email overrides: replace known Webfleet-only emails with the correct Salesforce email.
    df_merged["Email_Lower"] = df_merged["Email_Lower"].map(
        lambda e: WEBFLEET_EMAIL_MAP.get(e, e)
    )

    if df_engineers.empty:
        return pd.DataFrame()

    df_engineers["Email_Lower"] = (
        df_engineers["Email"].astype(str).str.lower().str.strip()
    )
    df_merged = df_merged.merge(
        df_engineers[["Email_Lower", "Trade Group", "Trade_Lookup__c", "Engineer Name", "Effective_PostalCode__c", "ServiceResourceId"]],
        on="Email_Lower",
        how="inner",
    )

    df_merged["Trade Group"] = df_merged["Trade Group"].fillna("Unknown")
    df_merged = df_merged.drop(columns=["driverno_clean", "Email_Lower"], errors="ignore")

    return df_merged


def calculate_vehicular_kpi(df_veh: pd.DataFrame, trade_group: str, trades: List[str] = None, region_filter: str = "All") -> dict:
    if df_veh.empty:
        return {
            "avg_driving_score": None,
            "driver_count": 0,
            "drivers_below_7_pct": None,
        }

    df_filtered = df_veh.copy()
    
    # Apply Trade Filter
    if trades:
        df_filtered = df_filtered[df_filtered["Trade_Lookup__c"].isin(trades)]
        # Fallback if no specific trades found
        if df_filtered.empty:
            df_filtered = df_veh[df_veh["Trade Group"] == trade_group]
    else:
        df_filtered = df_filtered[df_filtered["Trade Group"] == trade_group]

    # Apply Region Filter
    if region_filter != "All":
        df_filtered = df_filtered[
            df_filtered["Effective_PostalCode__c"].apply(
                lambda pc: get_region_for_trade(pc, trade_group) == region_filter
            )
        ]
        
    if df_filtered.empty:
        return {
            "avg_driving_score": None,
            "driver_count": 0,
            "drivers_below_7_pct": None,
        }

    df_trade = df_filtered # for compatibility with existing code below

    score_col = (
        "optidrive_indicator"
        if "optidrive_indicator" in df_trade.columns
        else "OptiDrive Score" if "OptiDrive Score" in df_trade.columns else None
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


# ============================================================
# HIGH-LEVEL KPI ENGINE (Restored to Original Logic)
# ============================================================

def compute_kpis(
    trade_group_selected: str,
    trades: List[str],
    start_iso: str,
    end_iso: str,
    scoring_key: str = None,
    bonus_trade: str = None,
    region_filter: str = "All",
) -> dict:
    """
    High-level KPI computation:
    - Fetches all required data (Salesforce + Webfleet)
    - Returns standard KPI dict
    """
   
    # --------------------------------------------------------
    # 1. Parallel data fetch
    # --------------------------------------------------------
    trades_tuple = tuple(trades) # For lru_cache
    
    # Calculate previous month range early for SA Activity Prev fetch
    cases_start_iso, cases_end_iso = get_previous_month_range(start_iso)

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
                    results[key] = pd.DataFrame() if key not in {
                        "ops_count",
                        "total_ops_count",
                        "engineer_satisfaction",
                        "cases_count",
                        "invoice_sales",
                        "total_invoice_sales",
                    } else 0
        return results

    stage1 = _run_futures(
        {
            "history": lambda: fetch_job_history_closed(start_iso, end_iso),
            "jobs_month": lambda: fetch_jobs_created_between(trades_tuple, start_iso, end_iso),
            "workorders": lambda: fetch_workorders_month(trades_tuple, start_iso, end_iso),
            "sa_month": lambda: fetch_service_appointments_month(trades_tuple, start_iso, end_iso),
            "sa_activity": lambda: fetch_service_appointments_activity(trades_tuple, start_iso, end_iso),
            "sa_activity_prev": lambda: fetch_service_appointments_activity(trades_tuple, cases_start_iso, cases_end_iso),
            "vehicular": lambda: get_merged_vehicular_data(),
            "vcr_forms": lambda: fetch_vcr_forms(start_iso, end_iso),
        },
        timeout=180,
    )

    # Non-DF extra calls
    ops_count = fetch_ops_count(trades_tuple, region_filter, trade_group_selected)
    total_ops_count = fetch_total_ops_count()
    engineer_satisfaction, engineer_survey_count = fetch_engineer_satisfaction(
        trades_tuple, start_iso, end_iso, region_filter=region_filter, trade_group_selected=trade_group_selected
    )

    # Cases from PREVIOUS month (dates already calculated above)
    df_cases_all = fetch_cases_data(
        trades_tuple,
        cases_start_iso,
        cases_end_iso,
    )

    invoice_sales, total_invoice_sales = fetch_customer_invoice_sales(
        trades_tuple, start_iso, end_iso, trade_group=trade_group_selected, region_filter=region_filter
    )

    df_history = stage1["history"]
    df_jobs_month = stage1["jobs_month"]
    df_wo_month = stage1["workorders"]
    df_sa_month_all = stage1["sa_month"]
    df_vehicular = stage1["vehicular"]
    df_vcr = stage1["vcr_forms"]
    df_engineers = fetch_service_resources()

    if df_history.empty:
        return {
            "kpis": {},
            "categories": {},
            "category_scores": {},
            "overall_score": 0.0,
            "bonus": {"current_band": "below", "bonus_value": 0.0, "note": "No history data available."},
        }

    # --------------------------------------------------------
    # 2. Normalize & secondary fetches
    # --------------------------------------------------------
    df_history["CreatedDate"] = pd.to_datetime(df_history["CreatedDate"], errors="coerce")
    df_history = df_history.rename(columns={"ParentId": "Job ID"})
    job_ids_closed = (
        df_history["Job ID"].dropna().astype(str).unique().tolist()
    )

    if not df_jobs_month.empty:
        df_jobs_month["CreatedDate"] = pd.to_datetime(
            df_jobs_month["CreatedDate"], errors="coerce"
        )
        df_jobs_month["Charge_Net__c"] = pd.to_numeric(
            df_jobs_month.get("Charge_Net__c"), errors="coerce"
        )

    if not df_wo_month.empty:
        df_wo_month["CreatedDate"] = pd.to_datetime(
            df_wo_month["CreatedDate"], errors="coerce"
        )
        df_wo_month["CCT_Charge_NET__c"] = pd.to_numeric(
            df_wo_month["CCT_Charge_NET__c"], errors="coerce"
        )

    if not df_sa_month_all.empty:
        df_sa_month_all["CreatedDate"] = pd.to_datetime(
            df_sa_month_all["CreatedDate"], errors="coerce"
        )
        # Flatten Job__r.Site_Id__c from nested dict
        if "Job__r" in df_sa_month_all.columns:
            df_sa_month_all["Site_Id__c"] = (
                df_sa_month_all["Job__r"]
                .apply(lambda x: x.get("Site_Id__c") if isinstance(x, dict) else None)
            )

    unclosed_sa_count = 0
    unclosed_sa_total = 0  # denominator: all SAs excluding today
    if not df_sa_month_all.empty:
        today_date = pd.Timestamp.now(tz="UTC").normalize()
        df_sa_month_all["ActualStartTime"] = pd.to_datetime(
            df_sa_month_all.get("ActualStartTime"), errors="coerce", utc=True
        )
        # Exclude appointments where the actual visit was today
        df_sa_excl_today = df_sa_month_all[
            df_sa_month_all["ActualStartTime"].dt.normalize() < today_date
        ]
        
        # Region Filtering for SA month (affects Site Value and Unclosed SA %)
        if region_filter != "All" and "PostalCode" in df_sa_month_all.columns:
            df_sa_month_all = df_sa_month_all[
                df_sa_month_all["PostalCode"].apply(
                    lambda pc: get_region_for_trade(pc, trade_group_selected) == region_filter
                )
            ]
            df_sa_excl_today = df_sa_excl_today[
                df_sa_excl_today["PostalCode"].apply(
                    lambda pc: get_region_for_trade(pc, trade_group_selected) == region_filter
                )
            ]
        unclosed_sa_total = len(df_sa_excl_today)
        unclosed_sa_count = df_sa_excl_today[
            ~df_sa_excl_today["Status"].isin(["Visit Complete", "Cancelled"])
        ].shape[0]

    # --- KPI ALIGNMENT: Baseline for Callbacks, TQR, and 6+ Hours ---
    # We identify unique Job IDs that had a "Visit Complete" appointment this month.
    df_sa_activity = stage1.get("sa_activity", pd.DataFrame())
    attended_job_ids_month = set()
    attended_reactive_job_ids = set()
    
    if not df_sa_activity.empty:
        if "Job__r" in df_sa_activity.columns:
            # Flatten Job Type if possible
            df_sa_activity["Job__r.Type__c"] = df_sa_activity["Job__r"].apply(
                lambda x: x.get("Type__c") if isinstance(x, dict) else None
            )
        
        # Region Filtering for all attended activities
        if region_filter != "All" and "PostalCode" in df_sa_activity.columns:
            df_sa_activity = df_sa_activity[
                df_sa_activity["PostalCode"].apply(
                    lambda pc: get_region_for_trade(pc, trade_group_selected) == region_filter
                )
            ]

        # All attended jobs (denominator for Callbacks and TQR)
        attended_job_ids_month = set(
            df_sa_activity[df_sa_activity["Status"] == "Visit Complete"]["Job__c"].astype(str).unique()
        )
        
        # Region Filtering for Reactive Leads Baseline
        df_reactive_attended = df_sa_activity[
            (df_sa_activity["Status"] == "Visit Complete") &
            (df_sa_activity["Job__r.Type__c"] == "Reactive")
        ]

        # Reactive attended jobs (denominator for 6+ Hours and Estimate Production)
        attended_reactive_job_ids = set(
            df_reactive_attended["Job__c"].astype(str).unique()
        )

    # Filter Previous Month SA Activity (for Satisfaction) by Region
    df_sa_activity_prev = stage1.get("sa_activity_prev", pd.DataFrame())
    if not df_sa_activity_prev.empty and region_filter != "All" and "PostalCode" in df_sa_activity_prev.columns:
        df_sa_activity_prev = df_sa_activity_prev[
            df_sa_activity_prev["PostalCode"].apply(
                lambda pc: get_region_for_trade(pc, trade_group_selected) == region_filter
            )
        ]

    # Combine closed job IDs and attended job IDs for detail fetch
    job_ids_to_fetch = set(job_ids_closed).union(attended_job_ids_month)
    
    df_jobs_detailed = fetch_jobs_by_ids(tuple(job_ids_to_fetch))
    df_sa = fetch_service_appointments_by_job_ids(tuple(job_ids_to_fetch))

    # Flatten Job__r.Final_WO_Is_the_Customer_Satisfied__c safely
    if "Job__r" in df_sa.columns:
        df_sa["Final_WO_Is_the_Customer_Satisfied__c"] = (
            df_sa["Job__r"]
            .apply(lambda x: x.get("Final_WO_Is_the_Customer_Satisfied__c") if isinstance(x, dict) else None)
        )

    # --------------------------------------------------------
    # 3. KPI Computation
    # --------------------------------------------------------
    df_jobs_detailed = df_jobs_detailed.rename(
        columns={
            "Id": "Job ID",
            "Name": "Job Name",
            "Job_Type_Trade__c": "Trade",
            "Type__c": "Job Type",
            "Status__c": "Job Status",
            "Charge_Policy__c": "Charge Policy",
            "Customer_Facing_Description__c": "Customer Comment",
            "Raised_from_Job__c": "Raised From Job",
        }
    )
    df_jobs_detailed["Job_Duration__c"] = pd.to_numeric(
        df_jobs_detailed.get("Job_Duration__c"), errors="coerce"
    )

    # Universe for Jobs Closed Metrics
    df_closed = df_history.merge(df_jobs_detailed, on="Job ID", how="left")
    df_closed = df_closed[df_closed["Trade"].isin(trades)]

    if not df_sa.empty:
        df_sa["Review_Star_Rating__c"] = pd.to_numeric(
            df_sa["Review_Star_Rating__c"], errors="coerce"
        )
        df_sa["CreatedDate"] = pd.to_datetime(df_sa["CreatedDate"], errors="coerce")
        df_sa["ActualStartTime"] = pd.to_datetime(
            df_sa["ActualStartTime"], errors="coerce"
        )
        df_sa["ArrivalWindowStartTime"] = pd.to_datetime(
            df_sa["ArrivalWindowStartTime"], errors="coerce"
        )
        df_sa["ArrivalWindowEndTime"] = pd.to_datetime(
            df_sa["ArrivalWindowEndTime"], errors="coerce"
        )

    # Reactive Leads baseline: use unique reactive jobs that had an attended visit this month
    reactive_leads_count = len(attended_reactive_job_ids) if attended_reactive_job_ids else 0

    # Numerator: Converted jobs created this month that were raised from those specific attended FOC jobs
    # THAT belong to the filtered Reactive Leads baseline.
    estimate_production_count = 0
    df_fp_wo_all = pd.DataFrame()
    if not df_wo_month.empty:
        # Filter 1: Fixed Price and Engineer Partner Community
        df_fp_wo_all = df_wo_month[
            (df_wo_month["Record_Type_Name__c"].astype(str).str.contains("Fixed Price", case=False, na=False)) &
            (df_wo_month["Created_by_Profile_Name__c"] == "Engineer Partner Community")
        ]
        
        # Filter 2: Region filtering (independent of reactive leads denominator)
        if region_filter != "All" and "PostalCode" in df_fp_wo_all.columns:
            df_fp_wo_all = df_fp_wo_all[
                df_fp_wo_all["PostalCode"].apply(
                    lambda pc: get_region_for_trade(pc, trade_group_selected) == region_filter
                )
            ]

        estimate_production_count = len(df_fp_wo_all)

    estimate_production_pct = (
        estimate_production_count / reactive_leads_count * 100
        if reactive_leads_count > 0
        else None
    )

    # Average Site Value = Invoice Sales / Unique Sites from attended SAs
    if not df_sa_month_all.empty and "Site_Id__c" in df_sa_month_all.columns:
        sa_sites = df_sa_month_all[df_sa_month_all["Site_Id__c"].notna()]
        site_count = sa_sites["Site_Id__c"].nunique()
    else:
        site_count = 0
    avg_site_value = (invoice_sales / site_count) if site_count else 0.0

    # FOC Conversion Rate (Attended Baseline)
    # Denominator: Unique Jobs that had a "Visit Complete" SA this month AND have FOC/£60 policy
    # Note: df_jobs_detailed was renamed: Id -> Job ID, Charge_Policy__c -> Charge Policy
    attended_ids_list = list(attended_job_ids_month)
    df_attended_foc = df_jobs_detailed[
        (df_jobs_detailed["Job ID"].isin(attended_ids_list)) &
        (df_jobs_detailed["Charge Policy"].isin(["FOC Estimate", "£60 Estimate"]))
    ]
    foc_attended_ids = set(df_attended_foc["Job ID"].astype(str))
    
    # Numerator: Converted jobs created this month that were raised from those specific attended FOC jobs
    # We only count jobs with status "Approved by Client" or "Closed"
    raised_from_attended_foc = pd.DataFrame()
    if not df_jobs_month.empty and "Raised_from_Job__c" in df_jobs_month.columns:
        raised_from_attended_foc = df_jobs_month[
            (df_jobs_month["Raised_from_Job__c"].astype(str).isin(foc_attended_ids)) &
            (df_jobs_month["Status__c"].isin(["Approved by Client", "Closed", "Ongoing"]))
        ]
    
    # User asked to count ALL converted follow-on jobs (can exceed 100% if one visit raises multiple approved jobs)
    foc_conversion_rate = (
        len(raised_from_attended_foc) / len(df_attended_foc) * 100 
        if not df_attended_foc.empty else 0.0
    )

    month_key, year = infer_month_key_and_year_from_iso(start_iso)

    ops_target = get_ops_count_target(trade_group_selected, month_key, year)
    ops_count_achievement = (ops_count / ops_target * 100) if ops_target and ops_target > 0 else 0.0

    # Fetch target safely
    sales_target = get_sales_target(trade_group_selected, month_key, year)

    if sales_target > 0:
        sales_target_achievement = (invoice_sales / sales_target) * 100
    else:
        sales_target_achievement = 0.0

    # Estimated Conversion % (from WorkOrders)
    estimated_conversion_pct = 0.0
    converted_fp_wo = 0
    total_fp_wo = 0
    total_cct = 0.0
    avg_converted_estimate_value = 0.0
    
    if not df_wo_month.empty and not df_fp_wo_all.empty:
        # Use the common df_fp_wo_all defined above for Estimate Production
        total_fp_wo = len(df_fp_wo_all)
        
        # 2. Filter for those that were converted (Accepted/Live or Complete)
        # Using WO_Status__c to be consistent with user preference
        df_fp_wo_converted = df_fp_wo_all[
            df_fp_wo_all["WO_Status__c"].isin(["Complete", "Accepted/Live"])
        ]
        converted_fp_wo = len(df_fp_wo_converted)
        
        # 3. Calculate %
        estimated_conversion_pct = (
            converted_fp_wo / total_fp_wo * 100 if total_fp_wo else 0.0
        )
        
        # 4. Calculate Average Value
        total_cct = df_fp_wo_converted["CCT_Charge_NET__c"].sum()
        avg_converted_estimate_value = (
            total_cct / converted_fp_wo if converted_fp_wo else 0.0
        )
        
        # For raw_metrics mapping later
        wo_count = converted_fp_wo 
    else:
        wo_count = 0

    # Baseline for Callbacks and TQR: Unique jobs with Attended SAs (Visit Complete)
    job_ids_month = list(attended_job_ids_month)

    if not df_sa_activity.empty:
        df_sa_activity["ActualStartTime"] = pd.to_datetime(df_sa_activity["ActualStartTime"], errors="coerce")
        df_sa_activity["ArrivalWindowStartTime"] = pd.to_datetime(df_sa_activity["ArrivalWindowStartTime"], errors="coerce")
        df_sa_activity["ArrivalWindowEndTime"] = pd.to_datetime(df_sa_activity["ArrivalWindowEndTime"], errors="coerce")
        df_sa_activity["Review_Star_Rating__c"] = pd.to_numeric(df_sa_activity["Review_Star_Rating__c"], errors="coerce")

    # ------------------------------------------------------------------
    # Review Ratio (Previous Month Based)
    # ------------------------------------------------------------------
    # User requested Review Ratio to be based on LAST month's SA activity 
    # (specifically ActualStartTime in previous month).
    
    count_attended_prev = 0
    count_reviews_prev = 0
    review_ratio = None
    avg_rating = None          # ← ARR now also based on previous month
    
    if not df_sa_activity_prev.empty:
        # We rely on the fetch function to have filtered by date range already
        attended_prev = df_sa_activity_prev[df_sa_activity_prev["Status"] == "Visit Complete"].copy()
        # Convert to numeric to be safe
        attended_prev["Review_Star_Rating__c"] = pd.to_numeric(
            attended_prev["Review_Star_Rating__c"], errors="coerce"
        )
        
        # Extract Job__r.Name from nested dictionary if it exists
        if "Job__r" in attended_prev.columns:
            attended_prev["Job__r.Name"] = attended_prev["Job__r"].apply(
                lambda x: x.get("Name") if isinstance(x, dict) else None
            )

        # Deduplicate by Job__r.Name (Job Number) to get per-job review stats rather than per-SA
        # The Salesforce API sometimes returns Job__r.Name directly, or nested. We can safely deduplicate
        # using Job__c instead if Job__r.Name is missing as a column since it's a 1:1 mapping to Job Number.
        attended_prev = attended_prev.sort_values(by="Review_Star_Rating__c", ascending=False)
        dedup_col = "Job__r.Name" if "Job__r.Name" in attended_prev.columns else "Job__c"
        attended_prev_unique_jobs = attended_prev.drop_duplicates(subset=[dedup_col], keep="first")
        
        count_attended_prev = len(attended_prev_unique_jobs)
        with_review_prev = attended_prev_unique_jobs[attended_prev_unique_jobs["Review_Star_Rating__c"].notna()]
        count_reviews_prev = len(with_review_prev)
        
        review_ratio = (
            count_reviews_prev / count_attended_prev * 100 if count_attended_prev else None
        )

        # Average Review Rating — also previous month (using the unique jobs data)
        avg_rating = (
            round(with_review_prev["Review_Star_Rating__c"].mean(), 1) if count_reviews_prev else None
        )

    # ------------------------------------------------------------------
    # Current Month SA Metrics (for Late Stats, SA Attended)
    # ------------------------------------------------------------------
    if not df_sa_activity.empty:
        service_appts = len(df_sa_activity)
        attended = df_sa_activity[df_sa_activity["Status"] == "Visit Complete"]
        with_review = attended[attended["Review_Star_Rating__c"].notna()]
        count_attended = len(attended)
        count_reviews = len(with_review)
        total_star_rating = with_review["Review_Star_Rating__c"].sum()
        # Note: avg_rating and review_ratio are now calculated above using prev data
        
        # Late Calculation
        # We need to ensure we don't have NaTs before comparison to avoid errors
        # (Though query filters on ActualStartTime, ArrivalWindow might be missing)
        valid_times = df_sa_activity.dropna(subset=["ActualStartTime", "ArrivalWindowEndTime"]).copy()
        
        valid_times["Late"] = (
            (valid_times["ActualStartTime"] - valid_times["ArrivalWindowEndTime"])
            .dt.total_seconds()
            / 60
            > 0
        )
        late_count = int(valid_times["Late"].sum())
        late_pct = (late_count / service_appts * 100) if service_appts else 0.0
    else:
        service_appts = 0
        count_attended = 0
        count_reviews = 0
        total_star_rating = 0 # Ensure this is reset if empty
        # avg_rating and review_ratio are handled above
        # review_ratio is handled above
        late_count = 0
        late_pct = 0.0

    # Unclosed SA % — use today-excluded total as denominator
    unclosed_sa_pct = (
        unclosed_sa_count / unclosed_sa_total * 100 if unclosed_sa_total > 0 else None
    )

    # --------------------------------------------------------
    # VCR Updates KPI
    # --------------------------------------------------------

    vcr_count = 0

    if not df_vcr.empty and not df_engineers.empty:
        df_vcr = df_vcr.merge(
            df_engineers[["ServiceResourceId", "Trade Group", "Trade_Lookup__c", "Residential_PostalCode__c"]],
            left_on="Current_Engineer_Assigned_to_Vehicle__c",
            right_on="ServiceResourceId",
            how="left",
        )

        if trades:

            df_trade_vcr = df_vcr[df_vcr["Trade_Lookup__c"].isin(trades)]
            # Fallback if no specific trades found
            if df_trade_vcr.empty:
                df_trade_vcr = df_vcr[df_vcr["Trade Group"] == trade_group_selected]
        else:
            df_trade_vcr = df_vcr[df_vcr["Trade Group"] == trade_group_selected]

        # Apply Region Filter for VCR
        if region_filter != "All":
            df_trade_vcr = df_trade_vcr[
                df_trade_vcr["Residential_PostalCode__c"].apply(
                    lambda pc: get_region_for_trade(pc, trade_group_selected) == region_filter
                )
            ]

        vcr_count = df_trade_vcr.shape[0]

    vcr_update_pct = None  # calculated after vehicular_kpi is available (uses driver_count)

    # --------------------------------------------------------
    # TQR Ratios
    # --------------------------------------------------------

    total_jobs = len(job_ids_month) if job_ids_month else 0
    tqr_total_count = 0
    tqr_not_satisfied_count = 0
    tqr_ratio_pct = 0.0 if total_jobs > 0 else None
    tqr_not_satisfied_ratio_pct = None

    if not df_sa.empty and job_ids_month:
        df_sa_tqr = df_sa[
            (df_sa["Job__c"].astype(str).isin(job_ids_month))
            & (df_sa["Post_Visit_Report_Check__c"] == "TQR")
        ]

        if not df_sa_tqr.empty:
            df_tqr_jobs = df_sa_tqr.drop_duplicates(subset=["Job__c"])
            tqr_total_count = len(df_tqr_jobs)

            tqr_not_satisfied_count = len(
                df_tqr_jobs[
                    df_tqr_jobs["Final_WO_Is_the_Customer_Satisfied__c"] == "No"
                ]
            )

            tqr_ratio_pct = (tqr_total_count / total_jobs * 100) if total_jobs > 0 else None
            tqr_not_satisfied_ratio_pct = (
                tqr_not_satisfied_count / tqr_total_count * 100
                if tqr_total_count > 0
                else None
            )
        else:
            tqr_total_count = 0
            tqr_not_satisfied_count = 0
    else:
        tqr_total_count = 0
        tqr_not_satisfied_count = 0


    # Callbacks & 6+ Hours
    def detect_callback(row):
        cp = str(row.get("Charge Policy") or "").lower()
        comment = str(row.get("Customer Comment") or "").lower()
        return ("callback" in comment) or ("call back" in comment) or (cp == "call back")
    
    # Baseline for Callbacks (Current Month)
    df_attended_month = df_jobs_detailed[df_jobs_detailed["Job ID"].isin(job_ids_month)]
    callback_jobs_count = int(df_attended_month.apply(detect_callback, axis=1).sum())

    # Case KPI Baseline: Unique Jobs from Service Appointments completed in previous month
    attended_job_ids_prev = set()
    if not df_sa_activity_prev.empty:
        attended_job_ids_prev = set(
            df_sa_activity_prev[df_sa_activity_prev["Status"] == "Visit Complete"]["Job__c"].astype(str).unique()
        )
    
    total_jobs_prev = len(attended_job_ids_prev)
    
    # Numerator: Cases linked to those specific jobs
    cases_count = 0
    if not df_cases_all.empty and attended_job_ids_prev:
        # Filter cases where Job__c is in the baseline set
        df_cases_filtered = df_cases_all[
            df_cases_all["Job__c"].astype(str).isin(attended_job_ids_prev)
        ]
        cases_count = len(df_cases_filtered)

    cases_pct = (
        (cases_count / total_jobs_prev) * 100
        if total_jobs_prev > 0
        else None
    )

    callback_jobs_pct = (
        (callback_jobs_count / total_jobs) * 100
        if total_jobs > 0
        else None
    )

    # Jobs 6+ Hours: Baseline is now Reactive Jobs Attended this Month (Visit Complete)
    df_attended_reactive = df_jobs_detailed[
        (df_jobs_detailed["Job ID"].isin(attended_reactive_job_ids)) &
        (df_jobs_detailed["Job Type"] == "Reactive") &
        (df_jobs_detailed["Trade"].isin(trades))
    ]
    
    jobs_6_plus_df = df_attended_reactive[df_attended_reactive["Job_Duration__c"] >= 6]
    jobs_6_plus_total = len(jobs_6_plus_df)
    
    jobs_6_plus_by_status = {}
    if not jobs_6_plus_df.empty:
        status_counts = (
            jobs_6_plus_df.groupby("Job Status").size().sort_values(ascending=False)
        )
        jobs_6_plus_by_status = status_counts.to_dict()

    reactive_jobs_count = len(df_attended_reactive)
    jobs_6_plus_pct = (
        jobs_6_plus_total / reactive_jobs_count * 100 if reactive_jobs_count > 0 else 0.0
    )

    # Vehicular KPI
    vehicular_kpi = calculate_vehicular_kpi(
        df_vehicular, trade_group_selected, trades, region_filter=region_filter
    )

    # VCR % uses driver_count (Webfleet) as denominator so it aligns with Drivers with <7
    driver_count = vehicular_kpi.get("driver_count", 0)
    if driver_count > 0:
        vcr_update_pct = (vcr_count / (driver_count * 2)) * 100

    # --------------------------------------------------------
    # 4. Flat KPI dict (numeric values, no strings)
    # --------------------------------------------------------
    kpis = {
        "Estimate Conversion %": float(estimated_conversion_pct),
        "FOC Conversion Rate %": float(foc_conversion_rate),
        "Reactive Leads": int(reactive_leads_count),
        "Estimate Production": int(estimate_production_count),
        "Estimate Production / Reactive Leads %": (
            float(estimate_production_pct) if estimate_production_pct is not None else None
        ),
        "Average Converted Estimate Value (£)": float(avg_converted_estimate_value),
        "Average Site Value (£)": float(avg_site_value),
        "Callback Jobs %": (float(callback_jobs_pct) if callback_jobs_pct is not None else None),
        "Callback Jobs Count": int(callback_jobs_count),
        "Jobs with 6+ Hours": int(jobs_6_plus_total),
        "Reactive 6+ hours %": float(jobs_6_plus_pct),
        "Service Appointments": int(service_appts),
        "SA Attended": int(count_attended),
        "Unclosed SA %": (float(unclosed_sa_pct) if unclosed_sa_pct is not None else None),
        "Late to Site": int(late_count),
        "Late to Site %": float(late_pct),
        "TQR Ratio %": float(tqr_ratio_pct) if tqr_ratio_pct is not None else None,
        "TQR Count": int(tqr_total_count),
        "TQR (Not Satisfied) Ratio %": float(tqr_not_satisfied_ratio_pct) if tqr_not_satisfied_ratio_pct is not None else None,
        "TQR (Not Satisfied) Count": int(tqr_not_satisfied_count),
        "Reviews Count": int(count_reviews),
        "Average Review Rating": float(avg_rating) if avg_rating is not None else None,
        "Review Ratio %": float(review_ratio) if review_ratio is not None else None,
        "Top Performers %": 20.0,
        "Red Flags %": 20.0,
        "Engineer Retention %": float(
            (ops_count / get_ops_baseline_count(trade_group_selected, trades, region_filter) * 100)
            if get_ops_baseline_count(trade_group_selected, trades, region_filter) > 0
            else 0.0
        ),
        "Ops Count %": float(ops_count_achievement),
        "Ops Count": int(ops_count),
        "Total Ops Count": int(total_ops_count),
        "Cases %": (float(cases_pct) if cases_pct is not None else None),
        "Cases Count": int(cases_count),
        "Engineer Satisfaction %": (
            float(engineer_satisfaction) if engineer_satisfaction is not None else None
        ),
        "Engineer Survey Count": int(engineer_survey_count),
        "Sales Target": float(sales_target),
        "Sales Target Achievement %": (
            float(sales_target_achievement) if sales_target_achievement is not None else None
        ),
        "Invoice Sales": float(invoice_sales),
        "Total Invoice Sales": float(total_invoice_sales),
        "Average Driving Score": (
            round(float(vehicular_kpi["avg_driving_score"]), 1)
            if vehicular_kpi["avg_driving_score"] is not None
            else None
        ),
        "Drivers with <7": (
            float(vehicular_kpi["drivers_below_7_pct"])
            if vehicular_kpi["drivers_below_7_pct"] is not None
            else None
        ),
        "VCR Update %": float(vcr_update_pct) if vcr_update_pct is not None else None,
        "VCR Count": int(vcr_count),
        "Drivers in Trade Group": int(vehicular_kpi["driver_count"]),
    }

    # --------------------------------------------------------
    # 5. Category KPIs
    # --------------------------------------------------------
    categories = {
        "Conversion": {
            "Estimate Production / Reactive Leads %": kpis.get(normalise_kpi_name("Estimate Production / Reactive Leads %")),
            "Estimate Conversion %": kpis.get(normalise_kpi_name("Estimate Conversion %")),
            "FOC Conversion Rate %": kpis.get(normalise_kpi_name("FOC Conversion Rate %")),
            "Average Converted Estimate Value (£)": kpis.get(normalise_kpi_name("Average Converted Estimate Value (£)")),
        },
        "Procedural": {
            "TQR Ratio %": kpis.get(normalise_kpi_name("TQR Ratio %")),
            "TQR (Not Satisfied) Ratio %": kpis.get(normalise_kpi_name("TQR (Not Satisfied) Ratio %")),
            "Unclosed SA %": kpis.get("Unclosed SA %"),
            "Reactive 6+ hours %": kpis.get(normalise_kpi_name("Reactive 6+ hours %")),
        },
        "Satisfaction": {
            "Average Review Rating": kpis.get(normalise_kpi_name("Average Review Rating")),
            "Review Ratio %": kpis.get(normalise_kpi_name("Review Ratio %")),
            "Engineer Satisfaction %": kpis.get(normalise_kpi_name("Engineer Satisfaction %")),
            "Cases %": kpis.get(normalise_kpi_name("Cases %")),
            "Engineer Retention %": kpis.get(normalise_kpi_name("Engineer Retention %")),
        },
        "Vehicular": {
            "Average Driving Score": kpis.get(normalise_kpi_name("Average Driving Score")),
            "Drivers with <7": kpis.get(normalise_kpi_name("Drivers with <7")),
            "VCR Update %": kpis.get(normalise_kpi_name("VCR Update %")),
        },
        "Productivity": {
            "Ops Count %": kpis.get(normalise_kpi_name("Ops Count %")),
            "Sales Target Achievement %": kpis.get(normalise_kpi_name("Sales Target Achievement %")),
            "Callback Jobs %": kpis.get(normalise_kpi_name("Callback Jobs %")),
            "SA Attended": kpis.get(normalise_kpi_name("SA Attended")),
            "Average Site Value (£)": kpis.get(normalise_kpi_name("Average Site Value (£)")),
            "Late to Site %": kpis.get(normalise_kpi_name("Late to Site %")),
        },
    }

    # --------------------------------------------------------
    # 6. KPI Scores (0–100), Category Scores, Overall Score
    # --------------------------------------------------------
    if not scoring_key:
        scoring_key = trade_group_selected

    kpi_scores = {}
    for kpi_name, kpi_value in kpis.items():
        clean_name = normalise_kpi_name(kpi_name)
        score_result = calculate_kpi_score(clean_name, kpi_value, scoring_key)
        if score_result and score_result.get("score") is not None:
            kpi_scores[kpi_name] = score_result["score"]

    category_scores = {}
    for cat in categories:
        cat_res = get_category_score(cat, kpis, scoring_key)
        category_scores[cat] = cat_res.get("category_score", 0.0) or 0.0

    # overall_result scored against the same scoring_key
    overall_result = get_overall_score(kpis, scoring_key, trade_group_selected, bonus_trade=bonus_trade)
    bonus = overall_result.get("bonus", {})
    
    multiplier = bonus.get("multiplier", 0)
    current_band = "below"
    if multiplier > 0: current_band = "gold"
    elif multiplier == 0: current_band = "silver"
    else: current_band = "bronze"
    bonus["current_band"] = current_band

    # --------------------------------------------------------
    # 7. Post-Scoring: Enrich KPIs for Drilldown
    # --------------------------------------------------------
    # Now that scoring is done (which requires floats), we can replace specific KPIs 
    # with rich objects {value, numerator, denominator} for the frontend using kpi_details module.
    
    raw_metrics = {
        "estimate_production_count": estimate_production_count,
        "reactive_leads_count": reactive_leads_count,
        "converted_fp_wo_count": converted_fp_wo,
        "total_fp_wo_count": total_fp_wo,
        "raised_from_foc_count": len(raised_from_attended_foc),
        "foc_jobs_count": len(df_attended_foc),
        "total_converted_estimate_value": total_cct,
        "converted_estimate_count": wo_count,
        
        # Satisfaction Metrics
        "count_reviews": count_reviews,
        "count_attended": count_attended,
        "total_star_rating": total_star_rating if 'total_star_rating' in locals() else 0,
        "engineer_survey_count": engineer_survey_count,
        "engineer_satisfaction_avg": engineer_satisfaction,
        "cases_count": cases_count,
        "total_jobs_prev": total_jobs_prev,

        # Productivity Metrics
        "ops_count": ops_count,
        "ops_target": ops_target if 'ops_target' in locals() else 0,
        "invoice_sales": invoice_sales,
        "sales_target": sales_target,
        "callback_jobs_count": callback_jobs_count,
        "total_jobs": total_jobs,
        "total_charge": invoice_sales,
        "site_count": site_count,
        "late_count": late_count,
        "service_appts": service_appts,
        "count_attended": count_attended,
        "count_reviews_prev": count_reviews_prev,
        "count_attended_prev": count_attended_prev,

        # Vehicular Metrics
        "avg_driving_score": vehicular_kpi.get("avg_driving_score"),
        "driver_count": vehicular_kpi.get("driver_count", 0),
        "drivers_below_7_count": int((vehicular_kpi.get("drivers_below_7_pct") or 0) / 100 * vehicular_kpi.get("driver_count", 0)) if vehicular_kpi.get("driver_count") else 0,
        "vcr_count": vcr_count,
        "vcr_target": driver_count * 2 if driver_count else 0,

        # Procedural Metrics
        "tqr_total_count": tqr_total_count,
        "tqr_not_satisfied_count": tqr_not_satisfied_count,
        "total_jobs": total_jobs,
        "unclosed_sa_count": unclosed_sa_count,
        "unclosed_sa_total": unclosed_sa_total,
        "jobs_6_plus_total": jobs_6_plus_total,
        "reactive_jobs_count": reactive_jobs_count,
        "ops_baseline": get_ops_baseline_count(trade_group_selected, trades, region_filter),
    }

    kpis = kpi_details.enrich_kpis(kpis, raw_metrics)

    # Also update the nested category dict to pick up the enriched objects
    for cat_name, cat_kpis in categories.items():
        for kpi_name in cat_kpis:
            if kpi_name in kpis:
                cat_kpis[kpi_name] = kpis[kpi_name]

    # --------------------------------------------------------
    # Fetch Live Collections
    # --------------------------------------------------------
    live_data = fetch_live_collections(tuple(trades), start_iso, end_iso)

    return {
        "kpis": kpis,
        "kpi_scores": kpi_scores,
        "categories": categories,
        "category_scores": category_scores,
        "overall_score": float(overall_result.get("overall_score", 0.0)),
        "bonus": bonus,
        "jobs_6_plus_by_status": jobs_6_plus_by_status,
        "live_collections": live_data["collections"],
        "live_labour": live_data["labour"],
        "live_materials": live_data["materials"],
    }


# ============================================================
# Google Sheets Integration
# ============================================================
import time as _time

_GSHEET_CACHE: dict = {}
_GSHEET_CACHE_TS: float = 0.0
_GSHEET_CACHE_TTL: float = 300  # 5 minutes

GSHEET_ID = "1ehYMcI0Plwup7I11WEnyaP674CSB6_lc8zrrdwa7Kjs"
GSHEET_CREDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bonus-dashboard-9e3fb8d8d57d.json")
GSHEET_WORKSHEET = "Dummy data"

# Maps trade filter (subgroup) name → sheet column prefix
TRADE_TO_SHEET_PREFIX = {
    "Decoration": "Decoration",
    "Gas & HVAC": "Gas and HVAC",
    "Electrical": "Electrical",
    "Roofing": "Roofing",
    "Multi Trades": "Multi",
    "Fire Safety": "Fire Safety",
    "Vent Hygiene and Safety": "Vent Hygiene",
}

# Maps trade GROUP name → sheet column prefix (trade filter is ignored for these)
TRADE_GROUP_TO_SHEET_PREFIX = {
    "Plumbing & Drainage": "Drainage and Plumbing",
    "Leak, Damp & Restoration": "Leak Detection",
}


def fetch_gsheet_all_data() -> dict:
    """Fetch all columns from the Dummy data sheet. Cached for 5 minutes."""
    global _GSHEET_CACHE, _GSHEET_CACHE_TS
    now = _time.time()
    if _GSHEET_CACHE and (now - _GSHEET_CACHE_TS) < _GSHEET_CACHE_TTL:
        return _GSHEET_CACHE
    try:
        import gspread
        from google.oauth2.service_account import Credentials as GCreds
        creds = GCreds.from_service_account_file(
            GSHEET_CREDS_FILE,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(GSHEET_ID)
        ws = sh.worksheet(GSHEET_WORKSHEET)
        rows = ws.get_all_values()
        if not rows:
            return {}
        headers = rows[0]
        result = {}
        for col_idx, col_name in enumerate(headers):
            if col_idx == 0:
                continue
            col_data = {}
            for row in rows[1:]:
                row_name = row[0]
                val_str = row[col_idx] if col_idx < len(row) else ""
                try:
                    col_data[row_name] = float(val_str.replace(",", ""))
                except (ValueError, AttributeError):
                    col_data[row_name] = val_str
            result[col_name] = col_data
        _GSHEET_CACHE = result
        _GSHEET_CACHE_TS = now
        logger.info(f"✅ Google Sheet fetched: {list(result.keys())}")
        return result
    except Exception as e:
        logger.error(f"❌ Google Sheet fetch error: {e}")
        return _GSHEET_CACHE


def get_gsheet_column_data(trade_filter: str, region: str, trade_group: str = "") -> dict:
    """Return row data for a specific trade+region column.
    Trade groups in TRADE_GROUP_TO_SHEET_PREFIX are looked up by group+region (trade_filter ignored).
    All others use trade_filter+region. Sums matching columns if region='All'.
    """
    all_data = fetch_gsheet_all_data()
    # Trade group takes priority if it has a direct sheet mapping.
    # If the UI passes a group with "All" trade selected (e.g. Fire Safety),
    # allow the group name itself to resolve through the trade-prefix map too.
    if trade_group and trade_group in TRADE_GROUP_TO_SHEET_PREFIX:
        prefix = TRADE_GROUP_TO_SHEET_PREFIX[trade_group]
    elif trade_filter and trade_filter != "All":
        prefix = TRADE_TO_SHEET_PREFIX.get(trade_filter, trade_filter)
    elif trade_group and trade_group in TRADE_TO_SHEET_PREFIX:
        prefix = TRADE_TO_SHEET_PREFIX[trade_group]
    else:
        prefix = TRADE_TO_SHEET_PREFIX.get(trade_filter, trade_filter or trade_group)
    if region and region != "All":
        col_name = f"{prefix} {region}"
        return all_data.get(col_name, {})
    # Sum across all regions for this trade prefix
    result: dict = {}
    for col_name, col_data in all_data.items():
        if col_name.startswith(prefix + " "):
            for row_name, val in col_data.items():
                if isinstance(val, (int, float)):
                    result[row_name] = result.get(row_name, 0) + val
    return result
