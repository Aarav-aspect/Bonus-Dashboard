# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from fastapi.middleware.cors import CORSMiddleware

import json
from pathlib import Path

from backend import (
    compute_kpis,
    TRADE_GROUPS,
    TRADE_SUBGROUPS,
    list_available_months,
    get_month_range,
    resolve_trades_for_filters,
    build_last3_completed_months_context,
    get_previous_month_range,
)

BONUS_POT_FILE = Path("bonuspot.json")
THRESHOLD_FILE = Path("thresholds.json")

from targets import reload_kpi_config
from insights.engine import build_insights_payload


app = FastAPI(title="Performance Dashboard API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DashboardRequest(BaseModel):
    month: str
    trade_group: str
    trade_filter: Optional[str] = "All"
    pool: Optional[str] = "All"  # "All" / "Conversion" / "Satisfaction" / ...


class DashboardResponse(BaseModel):
    overall_score: float
    bonus: Dict[str, Any]
    categories: Dict[str, Dict[str, Any]]
    kpi_scores: Dict[str, Any]
    category_scores: Dict[str, Any]
    insights: Optional[Dict[str, Any]] = None


@app.get("/meta/trade-groups")
def get_trade_groups():
    return TRADE_GROUPS


@app.get("/meta/trade-subgroups")
def get_trade_subgroups():
    return TRADE_SUBGROUPS


@app.get("/meta/months")
def get_months():
    return list_available_months()


@app.get("/config/bonus-pots")
def get_bonus_pots():
    if BONUS_POT_FILE.exists():
        with open(BONUS_POT_FILE, "r") as f:
            return json.load(f)
    return {}


@app.post("/config/bonus-pots")
def save_bonus_pots(pots: Dict[str, Any]):
    with open(BONUS_POT_FILE, "w") as f:
        json.dump(pots, f, indent=2)
    return {"status": "success"}


@app.get("/config/kpi-config")
def get_kpi_config():
    if THRESHOLD_FILE.exists():
        with open(THRESHOLD_FILE, "r") as f:
            data = json.load(f)
            return data.get("kpis", {})
    return {}


@app.post("/config/kpi-config")
def save_kpi_config(data: Dict[str, Any]):
    with open(THRESHOLD_FILE, "w") as f:
        json.dump({"kpis": data}, f, indent=2)
    reload_kpi_config()
    return {"status": "success"}


@app.put("/config/thresholds/dynamic/{kpi_name}")
def update_dynamic_threshold(kpi_name: str, trade_group: str, thresholds: List[float]):
    if not THRESHOLD_FILE.exists():
        raise HTTPException(status_code=404, detail="Thresholds file not found")

    with open(THRESHOLD_FILE, "r") as f:
        data = json.load(f)

    kpis = data.get("kpis", {})
    if kpi_name not in kpis:
        raise HTTPException(status_code=404, detail=f"KPI '{kpi_name}' not found")

    kpi_config = kpis[kpi_name]
    if "dynamic" not in kpi_config:
        raise HTTPException(status_code=400, detail=f"KPI '{kpi_name}' is not a dynamic KPI")

    dynamic_config = kpi_config["dynamic"]
    if dynamic_config.get("type") != "trade_based":
        raise HTTPException(status_code=400, detail=f"KPI '{kpi_name}' is not trade-based")

    scores = dynamic_config.get("scores", [])
    if len(thresholds) != len(scores):
        raise HTTPException(
            status_code=400,
            detail=f"Threshold count ({len(thresholds)}) must match scores count ({len(scores)})"
        )

    thresholds_by_trade = dynamic_config.get("thresholds_by_trade", {})
    thresholds_by_trade[trade_group] = thresholds

    with open(THRESHOLD_FILE, "w") as f:
        json.dump(data, f, indent=2)

    reload_kpi_config()
    return {"status": "success", "kpi": kpi_name, "trade_group": trade_group}


@app.post("/dashboard", response_model=DashboardResponse)
def get_dashboard(data: DashboardRequest):
    """
    Returns:
    - Monthly KPI result for selected month (dashboard)
    - Insights payload (monthly + quarterly/3-month window)
    - Supports pool filter: "All" / "Conversion" / "Satisfaction" / ...
      (filters only the insights returned; KPI calculation stays the same)
    """
    try:
        trade_filter = (data.trade_filter or "All").strip()
        pool = (data.pool or "All").strip()

        start_iso, end_iso = get_month_range(data.month)
        trades = resolve_trades_for_filters(data.trade_group, trade_filter)

        current_month_result = compute_kpis(
            trade_group_selected=data.trade_group,
            trades=trades,
            start_iso=start_iso,
            end_iso=end_iso,
            trade_filter=trade_filter,
            period="month",
        )

        prev_start_iso, prev_end_iso = get_previous_month_range(start_iso)
        previous_month_result = compute_kpis(
            trade_group_selected=data.trade_group,
            trades=trades,
            start_iso=prev_start_iso,
            end_iso=prev_end_iso,
            trade_filter=trade_filter,
            period="month",
        )

        quarterly_context = build_last3_completed_months_context(
            selected_month_display=data.month,
            trade_group=data.trade_group,
            trade_filter=trade_filter,
        )

        insights = build_insights_payload(
            current_result=current_month_result,
            previous_result=previous_month_result,
            trade_group=data.trade_group,
            trade_filter=trade_filter,
            month=data.month,
            quarterly_context=quarterly_context,
        )

        # Apply page-level pool filter
        if pool != "All":
            filtered_pools = {}
            if isinstance(insights.get("pools"), dict) and pool in insights["pools"]:
                filtered_pools[pool] = insights["pools"][pool]

            filtered_quarterly_pools = {}
            q = (insights.get("quarterly") or {})
            qp = (q.get("pools") or {})
            if isinstance(qp, dict) and pool in qp:
                filtered_quarterly_pools[pool] = qp[pool]

            insights = {
                "meta": insights.get("meta", {}),
                "pools": filtered_pools,
                "overall": insights.get("overall", {}),
                "quarterly": {
                    "meta": (insights.get("quarterly") or {}).get("meta", {}),
                    "pools": filtered_quarterly_pools,
                    "source": (insights.get("quarterly") or {}).get("source", {}),
                },
                "filter": {"pool": pool},
            }
        else:
            insights["filter"] = {"pool": "All"}

        return {
            "overall_score": current_month_result["overall_score"],
            "bonus": current_month_result["bonus"],
            "categories": current_month_result["categories"],
            "kpi_scores": current_month_result["kpi_scores"],
            "category_scores": current_month_result["category_scores"],
            "insights": insights,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))