from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi import Request, Response
from fastapi.staticfiles import StaticFiles
import os

# Existing logic (UNCHANGED)
from backend import (
    compute_kpis,
    TRADE_GROUPS,
    TRADE_SUBGROUPS,
    list_available_months,
    get_month_range,
    get_previous_month_range,
    resolve_trades_for_filters,
    get_merged_vehicular_data,
    fetch_service_appointments_activity,
    fetch_service_resources,
    fetch_service_appointments_month,
    fetch_job_history_closed,
    fetch_jobs_by_ids,
    fetch_service_appointments_by_job_ids,
    fetch_reactive_sas,
)

import json
from pathlib import Path

BONUS_POT_FILE = Path("bonuspot.json")
THRESHOLD_FILE = Path("thresholds.json")

from targets import (
    get_overall_score,
    reload_kpi_config,
)

import auth

from kpi_drilldown_config import KPI_DRILLDOWNS

# ------------------------------------------------------------
# App
# ------------------------------------------------------------

app = FastAPI(
    title="Performance Dashboard API",
    version="2.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# SERVE FRONTEND (For production)
# ------------------------------------------------------------

# We assume the frontend is built into 'web-app/dist'
# This will be used in the Docker container
dist_path = Path("web-app/dist")
if dist_path.exists():
    app.mount("/dashboard", StaticFiles(directory=str(dist_path), html=True), name="dashboard_static")
    app.mount("/assets", StaticFiles(directory=str(dist_path / "assets")), name="assets")
    
    # Catch-all for React Router on the root or other paths if needed
    @app.get("/")
    async def serve_index():
        index_file = dist_path / "index.html"
        if index_file.exists():
            from fastapi.responses import FileResponse
            return FileResponse(index_file)
        return {"message": "Frontend not built yet. Run 'npm run build' in web-app/"}

# ------------------------------------------------------------
# FALLBACK ROUTING (For development)
# ------------------------------------------------------------

@app.get("/dashboard")
async def dashboard_fallback():
    """
    If someone hits /dashboard on the backend port directly:
    - In production: app.mount handles it (if dist exists).
    - In development: Redirect to the Vite port.
    """
    return RedirectResponse(url=f"{auth.FRONTEND_URL}/dashboard")

# ------------------------------------------------------------
# AUTH ENDPOINTS (Stateless Azure AD)
# ------------------------------------------------------------

@app.get("/api/auth/signin/microsoft")
def signin_microsoft(request: Request):
    """Redirect user to Microsoft login page."""
    
    # Dynamically determine the redirect URI based on the request host
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.hostname)
    port = request.url.port
    
    # If running locally on port 8000, keep it. Otherwise, assume standard HTTPS/HTTP port.
    if port and host in ["localhost", "127.0.0.1"]:
        redirect_uri = f"{scheme}://{host}:{port}/api/auth/callback/microsoft"
    else:
        redirect_uri = f"{scheme}://{host}/api/auth/callback/microsoft"
        
    auth_url = (
        f"https://login.microsoftonline.com/{auth.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize"
        f"?client_id={auth.MICROSOFT_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&response_mode=query"
        f"&scope=User.Read openid profile email"
    )
    return RedirectResponse(url=auth_url)


@app.get("/api/auth/callback/microsoft")
async def callback_microsoft(request: Request, code: str):
    """
    Handle OAuth callback from Microsoft.
    Exchange code → get ID token → create session JWT → redirect to frontend.
    """
    # Determine dynamic URLs from the request headers
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.hostname)
    port = request.url.port
    
    # Construct exact redirect_uri to match what we sent in signin
    if port and host in ["localhost", "127.0.0.1"]:
        redirect_uri = f"{scheme}://{host}:{port}/api/auth/callback/microsoft"
        frontend_url = f"{scheme}://{host}:5173" # Local dev frontend
    else:
        redirect_uri = f"{scheme}://{host}/api/auth/callback/microsoft"
        frontend_url = f"{scheme}://{host}" # Production serves frontend on same host
        
    # 1. Exchange code for tokens
    token_data = await auth.exchange_code_for_token(code, redirect_uri)

    id_token = token_data.get("id_token")
    if not id_token:
        raise HTTPException(status_code=400, detail="No ID token received from Microsoft")

    # 2. Validate the ID token against Azure AD JWKS
    claims = await auth.verify_azure_id_token(id_token)

    # 3. Extract user info from claims
    user_id = claims.get("oid") or claims.get("sub")
    name = claims.get("name", "")
    email = claims.get("preferred_username") or claims.get("email") or ""

    # 4. Parse roles from App Roles claim
    roles = claims.get("roles", [])
    role_info = auth.parse_role_claims(roles)



    # 5. Build user data
    user_data = {
        "id": user_id,
        "name": name,
        "email": email,
        **role_info,  # role, assigned_group, assigned_trade
    }

    # 6. Create our session JWT
    session_token = auth.create_session_token(user_data)

    # 7. Set cookie and redirect to frontend dashboard
    redirect = RedirectResponse(url=f"{frontend_url}/dashboard")
    auth.set_session_cookie(request, redirect, session_token)
    return redirect


@app.get("/api/auth/session")
def get_session(request: Request):
    """Return the current user from the session JWT cookie."""
    user = auth.get_current_user(request)
    return {"user": user}


@app.post("/api/auth/signout")
def signout(response: Response):
    """Clear session cookie and return Microsoft logout URL."""
    response.delete_cookie(auth.SESSION_COOKIE_NAME, path="/")

    # Microsoft logout endpoint
    ms_logout_url = (
        f"https://login.microsoftonline.com/{auth.MICROSOFT_TENANT_ID}/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri={auth.FRONTEND_URL}"
    )

    return {"status": "success", "logout_url": ms_logout_url}


class DevLoginRequest(BaseModel):
    role: str
    assigned_group: Optional[str] = None
    assigned_trade: Optional[str] = None


@app.post("/api/auth/dev/login")
def dev_login(request: Request, data: DevLoginRequest, response: Response):
    """
    Developer login endpoint.
    Creates a valid session cookie for the requested role without Azure AD.
    """
    # In a real production app, checking a flag like 'DEBUG_MODE' here is good practice.
    # For this internal dashboard, we expose it for ease of testing.
    
    token = auth.create_dev_token(
        role=data.role,
        group=data.assigned_group,
        trade=data.assigned_trade
    )
    
    auth.set_session_cookie(request, response, token)
    return {"status": "success", "message": f"Logged in as {data.role}"}


# ------------------------------------------------------------
# Schemas (API contracts)
# ------------------------------------------------------------

class DashboardRequest(BaseModel):
    month: str
    trade_group: str
    trade_filter: Optional[str] = "All"

class DrilldownDriversRequest(BaseModel):
    trade_group: str
    trade_filter: Optional[str] = "All"

class DrilldownReviewsRequest(BaseModel):
    trade_group: str
    month: str
    trade_filter: Optional[str] = "All"


class DashboardResponse(BaseModel):
    overall_score: float
    bonus: Dict[str, Any]
    categories: Dict[str, Dict[str, Any]]
    kpi_scores: Dict[str, Any]
    category_scores: Dict[str, Any]
    live_collections: float = 0.0
    live_labour: float = 0.0
    live_materials: float = 0.0


# ------------------------------------------------------------
# META ENDPOINTS
# ------------------------------------------------------------

@app.get("/meta/trade-groups")
def get_trade_groups():
    return TRADE_GROUPS


@app.get("/meta/trade-subgroups")
def get_trade_subgroups():
    return TRADE_SUBGROUPS


@app.get("/meta/months")
def get_months():
    return list_available_months()


# ------------------------------------------------------------
# CONFIG ENDPOINTS
# ------------------------------------------------------------

@app.get("/config/drilldown")
def get_drilldown_config():
    """Returns the KPI drilldown configuration for the frontend."""
    return KPI_DRILLDOWNS


@app.get("/config/bonus-pots")
def get_bonus_pots(request: Request):
    auth.require_user(request)

    if BONUS_POT_FILE.exists():
        with open(BONUS_POT_FILE, "r") as f:
            return json.load(f)
    return {}

@app.post("/config/bonus-pots")
def save_bonus_pots(pots: Dict[str, Any], request: Request):
    auth.require_role(request, ["admin", "manager"])

    with open(BONUS_POT_FILE, "w") as f:
        json.dump(pots, f, indent=2)
    return {"status": "success"}

@app.get("/config/kpi-config")
def get_kpi_config(request: Request):
    auth.require_user(request)

    if THRESHOLD_FILE.exists():
        with open(THRESHOLD_FILE, "r") as f:
            data = json.load(f)
            return data.get("kpis", {})
    return {}

@app.post("/config/kpi-config")
def save_kpi_config(data: Dict[str, Any], request: Request):
    auth.require_role(request, ["admin", "manager"])

    with open(THRESHOLD_FILE, "w") as f:
        json.dump({"kpis": data}, f, indent=2)
    reload_kpi_config()
    return {"status": "success"}

from fastapi import Body, Request, HTTPException

@app.put("/config/thresholds/dynamic/{kpi_name}")
def update_dynamic_threshold(kpi_name: str, trade_group: str, request: Request, thresholds: List[float] = Body(...)):
    auth.require_role(request, ["admin", "manager"])

    """
    Update thresholds for a specific trade group within a dynamic KPI.
    """
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


@app.put("/config/thresholds/dynamic/{kpi_name}/all")
def update_dynamic_threshold_all_groups(kpi_name: str, request: Request, thresholds: List[float] = Body(...)):
    auth.require_role(request, ["admin", "manager"])

    """
    Update thresholds for ALL trade groups within a dynamic KPI at once.
    """
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

    # Write the same thresholds to every existing trade group key
    thresholds_by_trade = dynamic_config.get("thresholds_by_trade", {})
    for trade_key in list(thresholds_by_trade.keys()):
        thresholds_by_trade[trade_key] = thresholds

    with open(THRESHOLD_FILE, "w") as f:
        json.dump(data, f, indent=2)

    reload_kpi_config()

    return {"status": "success", "kpi": kpi_name, "applied_to": list(thresholds_by_trade.keys())}


# ------------------------------------------------------------
# DRILLDOWN ENDPOINTS
# ------------------------------------------------------------

@app.post("/api/drilldown/drivers")
def get_driver_scores(data: DrilldownDriversRequest, request: Request):
    """
    Returns a list of drivers with their OptiDrive scores for a given trade group.
    Used by the KPI Details page for 'Drivers with <7' drilldown.
    """
    user = auth.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    import pandas as pd

    df = get_merged_vehicular_data()
    if df.empty:
        return {"drivers": [], "trade_group": data.trade_group}

    # Filter to specific trades via trade_filter
    trades = resolve_trades_for_filters(data.trade_group, data.trade_filter)
    if trades:
        df_trade = df[df["Trade_Lookup__c"].isin(trades)].copy()
    else:
        df_trade = df[df["Trade Group"] == data.trade_group].copy()

    # Find score column
    score_col = None
    for col in ["optidrive_indicator", "OptiDrive Score"]:
        if col in df_trade.columns:
            score_col = col
            break

    if not score_col or df_trade.empty:
        return {"drivers": [], "trade_group": data.trade_group}

    df_trade["score_numeric"] = pd.to_numeric(df_trade[score_col], errors="coerce")
    df_trade = df_trade.dropna(subset=["score_numeric"])

    # Scale to 0–10
    df_trade["score_scaled"] = df_trade["score_numeric"] * 10

    # Build results
    drivers = []
    for _, row in df_trade.iterrows():
        name = row.get("Engineer Name", "") or row.get("Email", "Unknown")
        score = round(float(row["score_scaled"]), 1)
        drivers.append({
            "name": name if name else "Unknown",
            "score": score,
            "below_threshold": score < 7.0,
            "trade": str(row.get("Trade_Lookup__c", "Unknown"))
        })

    # Sort: worst scores first
    drivers.sort(key=lambda d: d["score"])

    return {
        "drivers": drivers,
        "trade_group": data.trade_group,
        "total_count": len(drivers),
        "below_7_count": sum(1 for d in drivers if d["below_threshold"]),
    }


@app.post("/api/drilldown/ops-list")
def get_ops_list(data: DrilldownDriversRequest, request: Request):
    """
    Returns the list of active ops (engineers) for a given trade group.
    Shows their name and specific trade.
    """
    user = auth.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    import pandas as pd
    import traceback

    try:
        df_engineers = fetch_service_resources()
        if df_engineers.empty:
            return {"ops": [], "trade_group": data.trade_group, "total_count": 0}

        # Resolve trade group and filter -> list of individual trades
        trades = resolve_trades_for_filters(data.trade_group, data.trade_filter)
        
        if trades:
            df_filtered = df_engineers[df_engineers["Trade_Lookup__c"].isin(trades)]
        else:
            df_filtered = df_engineers[df_engineers["Trade Group"] == data.trade_group]

        ops = []
        for _, row in df_filtered.iterrows():
            name = row.get("Engineer Name", "") or "Unknown"
            trade = str(row.get("Trade_Lookup__c", "Unknown"))
            ops.append({"name": name, "trade": trade})

        # Sort alphabetically by name
        ops.sort(key=lambda o: o["name"])

        return {
            "ops": ops,
            "trade_group": data.trade_group,
            "total_count": len(ops),
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/drilldown/unclosed-sas")
def get_unclosed_sas(data: DrilldownReviewsRequest, request: Request):
    """
    Returns a list of unclosed Service Appointments for a given trade group and month.
    """
    user = auth.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    import pandas as pd
    import traceback

    try:
        trades = resolve_trades_for_filters(data.trade_group, data.trade_filter)
        trades_tuple = tuple(trades)
        start_iso, end_iso = get_month_range(data.month)

        df_sa = fetch_service_appointments_month(trades_tuple, start_iso, end_iso)
        if df_sa.empty:
            return {"unclosed_sas": [], "trade_group": data.trade_group, "total_count": 0}

        df_sa["ActualStartTime"] = pd.to_datetime(
            df_sa.get("ActualStartTime"), errors="coerce", utc=True
        )

        today_date = pd.Timestamp.now(tz="UTC").normalize()
        df_excl_today = df_sa[df_sa["ActualStartTime"].dt.normalize() < today_date]

        # Filter for unclosed: NOT "Visit Complete" or "Cancelled"
        df_unclosed = df_excl_today[
            ~df_excl_today["Status"].isin(["Visit Complete", "Cancelled"])
        ]

        sas = []
        for _, row in df_unclosed.iterrows():
            sa_no = row.get("AppointmentNumber", "") or row.get("Id", "Unknown")
            status = row.get("Status", "Unknown")
            actual_start = row.get("ActualStartTime", None)
            if pd.notna(actual_start):
                actual_start_str = pd.Timestamp(actual_start).strftime("%d %b %Y, %H:%M")
            else:
                actual_start_str = "N/A"
            sas.append({
                "appointment_number": str(sa_no),
                "status": str(status),
                "actual_start_time": actual_start_str,
            })

        sas.sort(key=lambda s: s["appointment_number"])

        return {
            "unclosed_sas": sas,
            "trade_group": data.trade_group,
            "total_count": len(sas),
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/drilldown/callback-jobs")
def get_callback_jobs(data: DrilldownReviewsRequest, request: Request):
    """
    Returns a list of callback jobs for a given trade group and month.
    """
    user = auth.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    import pandas as pd
    import traceback

    try:
        trades = resolve_trades_for_filters(data.trade_group, data.trade_filter)
        start_iso, end_iso = get_month_range(data.month)

        # Fetch closed job history and job details
        df_history = fetch_job_history_closed(start_iso, end_iso)
        if df_history.empty:
            return {"callback_jobs": [], "trade_group": data.trade_group, "total_count": 0}

        # Rename to match compute_kpis convention
        df_history = df_history.rename(columns={"ParentId": "Job ID"})

        job_ids_closed = df_history["Job ID"].astype(str).unique().tolist()
        df_jobs_closed = fetch_jobs_by_ids(tuple(job_ids_closed))
        if df_jobs_closed.empty:
            return {"callback_jobs": [], "trade_group": data.trade_group, "total_count": 0}

        # Rename columns to match compute_kpis convention
        df_jobs_closed = df_jobs_closed.rename(columns={
            "Id": "Job ID",
            "Name": "Job Name",
            "Job_Type_Trade__c": "Trade",
            "Type__c": "Job Type",
            "Charge_Policy__c": "Charge Policy",
            "Customer_Facing_Description__c": "Customer Comment",
        })

        df_closed = df_history.merge(df_jobs_closed, on="Job ID", how="left")
        df_closed = df_closed[df_closed["Trade"].isin(trades)]

        # Detect callbacks
        def detect_callback(row):
            cp = str(row.get("Charge Policy") or "").lower()
            comment = str(row.get("Customer Comment") or "").lower()
            return ("callback" in comment) or ("call back" in comment) or (cp == "call back")

        df_callbacks = df_closed[df_closed.apply(detect_callback, axis=1)]

        jobs = []
        for _, row in df_callbacks.iterrows():
            job_name = row.get("Job Name", "") or row.get("Job ID", "Unknown")
            jobs.append({
                "job_number": str(job_name),
            })

        jobs.sort(key=lambda j: j["job_number"])

        return {
            "callback_jobs": jobs,
            "trade_group": data.trade_group,
            "total_count": len(jobs),
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/drilldown/reactive-6plus")
def get_reactive_6plus(data: DrilldownReviewsRequest, request: Request):
    """
    Returns reactive SAs started this month where
    ActualEndTime - ActualStartTime > 6 hours.
    """
    user = auth.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    import pandas as pd
    import traceback

    try:
        trades = resolve_trades_for_filters(data.trade_group, data.trade_filter)
        trades_tuple = tuple(trades)
        start_iso, end_iso = get_month_range(data.month)

        df_sa = fetch_reactive_sas(trades_tuple, start_iso, end_iso)
        if df_sa.empty:
            return {"reactive_6plus": [], "trade_group": data.trade_group, "total_count": 0}

        # Only count SAs that were actually attended (Visit Complete)
        df_attended = df_sa[df_sa["Status"] == "Visit Complete"].copy()
        if df_attended.empty:
            return {"reactive_6plus": [], "trade_group": data.trade_group, "total_count": 0}

        # Get unique Job IDs for these attended SAs
        job_ids = tuple(df_attended["Job__c"].astype(str).unique())
        
        # Fetch detailed job info (specifically duration)
        df_jobs = fetch_jobs_by_ids(job_ids)
        if df_jobs.empty:
            return {"reactive_6plus": [], "trade_group": data.trade_group, "total_count": 0}

        # Ensure duration is numeric and filter for 6+ hours
        df_jobs["Job_Duration__c"] = pd.to_numeric(df_jobs["Job_Duration__c"], errors="coerce")
        df_6plus = df_jobs[df_jobs["Job_Duration__c"] >= 6].copy()

        results = []
        for _, row in df_6plus.iterrows():
            job_name = row.get("Name", "Unknown")
            duration = row.get("Job_Duration__c", 0.0)
            
            hours = int(duration)
            mins = int((duration - hours) * 60)
            duration_str = f"{hours}h {mins}m"
            
            results.append({
                "appointment_number": str(job_name), # Keep key name for frontend compatibility (Job Name here)
                "duration": duration_str,
            })

        results.sort(key=lambda r: r["appointment_number"])

        return {
            "reactive_6plus": results,
            "trade_group": data.trade_group,
            "total_count": len(results),
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/drilldown/late-to-site")
def get_late_to_site(data: DrilldownReviewsRequest, request: Request):
    """
    Returns engineers with their late SA count vs total SA count.
    """
    user = auth.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    import pandas as pd
    import traceback

    try:
        trades = resolve_trades_for_filters(data.trade_group, data.trade_filter)
        trades_tuple = tuple(trades)
        start_iso, end_iso = get_month_range(data.month)

        df_sa = fetch_service_appointments_activity(trades_tuple, start_iso, end_iso)
        if df_sa.empty:
            return {"engineers": [], "trade_group": data.trade_group, "total_late": 0, "total_sas": 0}

        df_sa["ActualStartTime"] = pd.to_datetime(df_sa.get("ActualStartTime"), errors="coerce")
        df_sa["ArrivalWindowStartTime"] = pd.to_datetime(df_sa.get("ArrivalWindowStartTime"), errors="coerce")

        # Flatten Allocated_Engineer__r.Name
        if "Allocated_Engineer__r" in df_sa.columns:
            df_sa["EngineerName"] = (
                df_sa["Allocated_Engineer__r"]
                .apply(lambda x: x.get("Name") if isinstance(x, dict) else None)
            )
        else:
            df_sa["EngineerName"] = None

        # Calculate late flag (same logic as compute_kpis: >30 min after arrival window)
        valid = df_sa.dropna(subset=["ActualStartTime", "ArrivalWindowStartTime"]).copy()
        valid["Late"] = (
            (valid["ActualStartTime"] - valid["ArrivalWindowStartTime"]).dt.total_seconds() / 60 > 30
        )

        # Group by engineer
        engineer_stats = {}
        for _, row in valid.iterrows():
            name = row.get("EngineerName") or "Unknown"
            if name not in engineer_stats:
                engineer_stats[name] = {"total": 0, "late": 0}
            engineer_stats[name]["total"] += 1
            if row["Late"]:
                engineer_stats[name]["late"] += 1

        engineers = []
        for name, stats in engineer_stats.items():
            engineers.append({
                "engineer_name": name,
                "late_count": stats["late"],
                "total_count": stats["total"],
                "summary": f"{stats['late']}/{stats['total']}",
            })

        engineers.sort(key=lambda e: e["late_count"], reverse=True)

        total_late = sum(e["late_count"] for e in engineers)
        total_sas = sum(e["total_count"] for e in engineers)

        return {
            "engineers": engineers,
            "trade_group": data.trade_group,
            "total_late": total_late,
            "total_sas": total_sas,
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/api/drilldown/cases")
def get_cases_detail(data: DrilldownReviewsRequest, request: Request):
    """
    Returns individual cases for the previous month (matching Cases % logic).
    """
    user = auth.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    import traceback

    try:
        trades = resolve_trades_for_filters(data.trade_group, data.trade_filter)
        trades_tuple = tuple(trades)
        start_iso, end_iso = get_month_range(data.month)
        # Cases uses previous month
        prev_start, prev_end = get_previous_month_range(start_iso)

        trades_str = ",".join([f"'{t}'" for t in trades])
        from backend import sf_query_df, queries
        q = queries.get_cases_detail_query(trades_str, prev_start, prev_end)
        df = sf_query_df(q)

        cases = []
        if not df.empty:
            for _, row in df.iterrows():
                sr = row.get("Service_Resource__r")
                eng_name = sr.get("Name") if isinstance(sr, dict) else str(sr or "Unknown")
                cases.append({
                    "case_number": str(row.get("CaseNumber", "Unknown")),
                    "case_type": str(row.get("Case_Type__c", "Unknown")),
                    "engineer_name": eng_name,
                })

        cases.sort(key=lambda c: c["case_number"])

        return {
            "cases": cases,
            "trade_group": data.trade_group,
            "total_count": len(cases),
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/drilldown/tqr-not-satisfied")
def get_tqr_not_satisfied(data: DrilldownReviewsRequest, request: Request):
    """
    Returns jobs with TQR where customer was Not Satisfied.
    """
    user = auth.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    import pandas as pd
    import traceback

    try:
        trades = resolve_trades_for_filters(data.trade_group, data.trade_filter)
        start_iso, end_iso = get_month_range(data.month)

        df_history = fetch_job_history_closed(start_iso, end_iso)
        if df_history.empty:
            return {"tqr_jobs": [], "trade_group": data.trade_group, "total_count": 0}

        df_history = df_history.rename(columns={"ParentId": "Job ID"})
        job_ids_closed = df_history["Job ID"].astype(str).unique().tolist()

        df_jobs = fetch_jobs_by_ids(tuple(job_ids_closed))
        if df_jobs.empty:
            return {"tqr_jobs": [], "trade_group": data.trade_group, "total_count": 0}

        df_jobs = df_jobs.rename(columns={
            "Id": "Job ID",
            "Name": "Job Name",
            "Job_Type_Trade__c": "Trade",
        })
        df_closed = df_history.merge(df_jobs, on="Job ID", how="left")
        df_closed = df_closed[df_closed["Trade"].isin(trades)]
        job_ids_month = df_closed["Job ID"].astype(str).unique().tolist()

        # Fetch SAs for those jobs
        df_sa = fetch_service_appointments_by_job_ids(tuple(job_ids_closed))
        if df_sa.empty:
            return {"tqr_jobs": [], "trade_group": data.trade_group, "total_count": 0}

        # Flatten Final_WO_Is_the_Customer_Satisfied__c from Job__r
        if "Job__r" in df_sa.columns:
            df_sa["Final_WO_Is_the_Customer_Satisfied__c"] = (
                df_sa["Job__r"]
                .apply(lambda x: x.get("Final_WO_Is_the_Customer_Satisfied__c") if isinstance(x, dict) else None)
            )

        # Filter: TQR + Not Satisfied, in month's jobs
        df_sa_tqr = df_sa[
            (df_sa["Job__c"].astype(str).isin(job_ids_month))
            & (df_sa["Post_Visit_Report_Check__c"] == "TQR")
        ]
        df_tqr_not_sat = df_sa_tqr[
            df_sa_tqr["Final_WO_Is_the_Customer_Satisfied__c"] == "No"
        ].drop_duplicates(subset=["Job__c"])

        # Build job name lookup
        job_name_map = df_jobs.drop_duplicates("Job ID").set_index("Job ID")["Job Name"].to_dict()

        jobs = []
        for _, row in df_tqr_not_sat.iterrows():
            job_id = str(row.get("Job__c", ""))
            job_name = job_name_map.get(job_id, job_id)
            jobs.append({"job_name": str(job_name)})

        jobs.sort(key=lambda j: j["job_name"])

        return {
            "tqr_jobs": jobs,
            "trade_group": data.trade_group,
            "total_count": len(jobs),
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/drilldown/reviews")
def get_review_details(data: DrilldownReviewsRequest, request: Request):
    """
    Returns a list of Service Appointments with their review ratings
    for a given trade group and month.
    """
    user = auth.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    import pandas as pd

    trades = resolve_trades_for_filters(data.trade_group, data.trade_filter)
    trades_tuple = tuple(trades)
    start_iso, end_iso = get_month_range(data.month)
    # ARR is based on previous month's data
    prev_start, prev_end = get_previous_month_range(start_iso)

    df = fetch_service_appointments_activity(trades_tuple, prev_start, prev_end)
    if df.empty:
        return {"reviews": [], "trade_group": data.trade_group, "total_count": 0, "avg_rating": None}

    # Only completed visits with a review
    attended = df[df["Status"] == "Visit Complete"].copy()
    attended["Review_Star_Rating__c"] = pd.to_numeric(attended["Review_Star_Rating__c"], errors="coerce")
    with_review = attended[attended["Review_Star_Rating__c"].notna()].copy()

    # Extract Job__r.Name from nested dictionary if it exists
    if "Job__r" in with_review.columns:
        with_review["Job__r.Name"] = with_review["Job__r"].apply(
            lambda x: x.get("Name") if isinstance(x, dict) else None
        )

    # Deduplicate by Job__r.Name to match the actual metric logic
    with_review = with_review.sort_values(by="Review_Star_Rating__c", ascending=False)
    dedup_col_api = "Job__r.Name" if "Job__r.Name" in with_review.columns else "Job__c"
    with_review = with_review.drop_duplicates(subset=[dedup_col_api], keep="first")

    reviews = []
    for _, row in with_review.iterrows():
        # User requested SA Number instead of Job Number, but deduplication remains by job
        sa_no = row.get("AppointmentNumber", "") or row.get("Id", "Unknown")
        
        rating = round(float(row["Review_Star_Rating__c"]), 1)
        reviews.append({
            "sa_number": str(sa_no), # Frontend still keys off 'sa_number' variable internally
            "rating": rating,
        })

    # Sort by rating (lowest first)
    reviews.sort(key=lambda r: r["rating"])

    avg = round(with_review["Review_Star_Rating__c"].mean(), 1) if len(with_review) > 0 else None

    return {
        "reviews": reviews,
        "trade_group": data.trade_group,
        "total_count": len(reviews),
        "avg_rating": avg,
    }


# ------------------------------------------------------------
# DASHBOARD ENDPOINT
# ------------------------------------------------------------

@app.post("/api/dashboard", response_model=DashboardResponse)
def get_dashboard(data: DashboardRequest, request: Request):
    """
    This is the MAIN endpoint React will call.
    """
    # 1. Check Authentication
    user = auth.require_user(request)

    # 2. Enforce Scoping
    req_group = data.trade_group
    req_trade = data.trade_filter or "All"

    user_role = user.get("role")
    user_group = user.get("assigned_group")
    user_trade = user.get("assigned_trade")

    if user_role == "trade_group_manager":
        if req_group != user_group:
            raise HTTPException(status_code=403, detail=f"Permission denied. You are restricted to {user_group}")

    elif user_role == "trade_manager":
        if req_group != user_group or req_trade != user_trade:
            raise HTTPException(status_code=403, detail=f"Permission denied. You are restricted to {user_group} > {user_trade}")

    try:
        start_iso, end_iso = get_month_range(data.month)
        trades = resolve_trades_for_filters(req_group, req_trade)
        # Determine threshold key
        # If specific trade selected (and not "All"), use that trade name for thresholds.
        # If "All" selected, use the Group Name for thresholds.
        threshold_key = req_group
        if req_trade and req_trade != "All":
            threshold_key = req_trade

        result = compute_kpis(req_group, trades, start_iso, end_iso, scoring_key=threshold_key, bonus_trade=req_trade)

        return {
            "overall_score": result["overall_score"],
            "bonus": result["bonus"],
            "categories": result["categories"],
            "kpi_scores": result["kpi_scores"],
            "category_scores": result["category_scores"],
            "live_collections": result.get("live_collections", 0.0),
            "live_labour": result.get("live_labour", 0.0),
            "live_materials": result.get("live_materials", 0.0)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
