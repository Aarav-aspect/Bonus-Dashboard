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
    fetch_webfleet_drivers,
    fetch_vcr_forms,
)

import json
from pathlib import Path
from database import (
    get_config, save_config, get_db_connection,
    get_all_users, get_user_by_email, create_user, update_user, delete_user,
    initialize_db,
)

BONUS_POT_FILE = Path("bonuspot.json")
THRESHOLD_FILE = Path("thresholds.json")

from targets import (
    get_overall_score,
    reload_kpi_config,
)

import auth

from kpi_drilldown_config import KPI_DRILLDOWNS
from mapping import TRADE_GROUP_PHASE, REGION_OPTIONS_BY_PHASE, get_region_for_trade

# App startup
initialize_db()

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

# Serve Frontend (Production)


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

# Fallback Routing

@app.get("/dashboard")
async def dashboard_fallback(request: Request):
    """Serve index or redirect based on environment."""
    dist_path = Path("web-app/dist")
    index_file = dist_path / "index.html"
    
    # If the built frontend exists (production), serve it directly
    if index_file.exists():
        from fastapi.responses import FileResponse
        return FileResponse(index_file)
        
    # Otherwise fallback to the configured frontend URL (development)
    return RedirectResponse(url=f"{auth.FRONTEND_URL}/dashboard")

# Auth Endpoints

@app.get("/api/auth/signin/microsoft")
def signin_microsoft(request: Request):
    """Redirect user to Microsoft login page."""
    
    # Dynamically determine the redirect URI based on the request host
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.hostname)
    port = request.url.port
    
    # If running locally on port 8000, keep it. Otherwise, assume standard HTTPS/HTTP port.
    # Force localhost for local environment to match Azure AD configuration
    if host == "127.0.0.1":
        host = "localhost"

    if port and host == "localhost":
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
        f"&prompt=select_account"
    )
    return RedirectResponse(url=auth_url)


@app.get("/api/auth/callback/microsoft")
async def callback_microsoft(request: Request, code: str):
    """Handle OAuth callback from Microsoft."""
    # Determine dynamic URLs from the request headers
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.hostname)
    port = request.url.port
    
    # Force localhost for local environment to match Azure AD configuration
    if host == "127.0.0.1":
        host = "localhost"

    # Construct exact redirect_uri to match what we sent in signin
    if port and host == "localhost":
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

    # 4. Parse roles from App Roles claim (Azure AD)
    roles = claims.get("roles", [])
    role_info = auth.parse_role_claims(roles)

    # 4b. Check if this user has a DB-managed role (overrides Azure AD role)
    try:
        db_user = get_user_by_email(email)
        if db_user:
            role_info = {
                "role": db_user["role"],
                "assigned_group": db_user.get("assigned_group"),
                "assigned_trade": db_user.get("assigned_trade"),
                "assigned_region": db_user.get("assigned_region"),
            }
            # Sync name from Azure if not set in DB
            if not db_user.get("name") and name:
                update_user(db_user["id"], {"name": name})
    except Exception:
        pass  # Fall back to Azure AD role on any DB error

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
def signout(request: Request, response: Response):
    """Clear session cookie and return Microsoft logout URL."""
    response.delete_cookie(auth.SESSION_COOKIE_NAME, path="/")
    
    # Dynamically determine the frontend URL for post-logout redirect
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.hostname)
    port = request.url.port
    
    if port and host in ["localhost", "127.0.0.1"]:
        frontend_url = f"{scheme}://{host}:5173"
    else:
        frontend_url = f"{scheme}://{host}"

    # Microsoft logout endpoint
    ms_logout_url = (
        f"https://login.microsoftonline.com/{auth.MICROSOFT_TENANT_ID}/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri={frontend_url}"
    )

    return {"status": "success", "logout_url": ms_logout_url}


class DevLoginRequest(BaseModel):
    role: str
    assigned_group: Optional[str] = None
    assigned_trade: Optional[str] = None
    assigned_region: Optional[str] = None


@app.post("/api/auth/dev/login")
def dev_login(request: Request, data: DevLoginRequest, response: Response):
    """Developer login for testing."""
    # In a real production app, checking a flag like 'DEBUG_MODE' here is good practice.
    # For this internal dashboard, we expose it for ease of testing.
    
    token = auth.create_dev_token(
        role=data.role,
        group=data.assigned_group,
        trade=data.assigned_trade,
        region=data.assigned_region
    )
    
    auth.set_session_cookie(request, response, token)
    return {"status": "success", "message": f"Logged in as {data.role}"}


# ---------------------------------------------------------------------------
# Account management — admin-only CRUD for app users
# ---------------------------------------------------------------------------

# Cache the Graph API token so we don't request a new one every search
_graph_token_cache: dict = {"token": None, "expires_at": 0}

async def _get_graph_token() -> str:
    """Obtain (or return cached) an app-only Microsoft Graph access token."""
    import time
    now = time.time()
    if _graph_token_cache["token"] and now < _graph_token_cache["expires_at"] - 60:
        return _graph_token_cache["token"]
    import httpx as _httpx
    url = f"https://login.microsoftonline.com/{auth.MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
    async with _httpx.AsyncClient() as client:
        resp = await client.post(url, data={
            "client_id":     auth.MICROSOFT_CLIENT_ID,
            "client_secret": auth.MICROSOFT_CLIENT_SECRET,
            "scope":         "https://graph.microsoft.com/.default",
            "grant_type":    "client_credentials",
        })
        resp.raise_for_status()
        data = resp.json()
        _graph_token_cache["token"] = data["access_token"]
        _graph_token_cache["expires_at"] = now + data.get("expires_in", 3600)
        return _graph_token_cache["token"]


@app.get("/admin/users/search")
async def search_org_users(request: Request, q: str = ""):
    """Search Azure AD directory for users matching a query. Admin only."""
    auth.require_role(request, ["admin"])
    if not q or len(q) < 2:
        return {"users": []}
    try:
        token = await _get_graph_token()
        import httpx as _httpx
        q_safe = q.replace("'", "''")  # escape single quotes for OData filter
        async with _httpx.AsyncClient() as client:
            resp = await client.get(
                "https://graph.microsoft.com/v1.0/users",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "$filter": f"startsWith(displayName,'{q_safe}') or startsWith(userPrincipalName,'{q_safe}')",
                    "$select": "id,displayName,mail,userPrincipalName",
                    "$top": 15,
                },
            )
            if not resp.is_success:
                return {"users": [], "error": f"Graph {resp.status_code}: {resp.text[:300]}"}
            results = resp.json().get("value", [])
        users = [
            {
                "id":    u.get("id"),
                "name":  u.get("displayName") or "",
                "email": u.get("mail") or u.get("userPrincipalName") or "",
            }
            for u in results
            if u.get("mail") or u.get("userPrincipalName")
        ]
        return {"users": users}
    except Exception as e:
        return {"users": [], "error": str(e)}


class UserCreateRequest(BaseModel):
    email: str
    name: Optional[str] = None
    role: str = "user"
    assigned_group: Optional[str] = None
    assigned_trade: Optional[str] = None
    assigned_region: Optional[str] = None


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    assigned_group: Optional[str] = None
    assigned_trade: Optional[str] = None
    assigned_region: Optional[str] = None


@app.get("/admin/users")
def list_users(request: Request):
    """List all managed users. Admin only."""
    auth.require_role(request, ["admin"])
    users = get_all_users()
    # Convert datetime objects to ISO strings for JSON serialisation
    for u in users:
        for field in ("created_at", "updated_at"):
            if u.get(field) and hasattr(u[field], "isoformat"):
                u[field] = u[field].isoformat()
    return {"users": users}


@app.post("/admin/users")
def add_user(request: Request, data: UserCreateRequest):
    """Create a managed user. Admin only."""
    auth.require_role(request, ["admin"])
    try:
        user = create_user(data.dict())
        for field in ("created_at", "updated_at"):
            if user.get(field) and hasattr(user[field], "isoformat"):
                user[field] = user[field].isoformat()
        return {"user": user}
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=409, detail="A user with this email already exists.")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/admin/users/{user_id}")
def edit_user(request: Request, user_id: str, data: UserUpdateRequest):
    """Update a managed user's role/permissions. Admin only."""
    auth.require_role(request, ["admin"])
    user = update_user(user_id, data.dict(exclude_none=False))
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    for field in ("created_at", "updated_at"):
        if user.get(field) and hasattr(user[field], "isoformat"):
            user[field] = user[field].isoformat()
    return {"user": user}


@app.delete("/admin/users/{user_id}")
def remove_user(request: Request, user_id: str):
    """Delete a managed user. Admin only."""
    auth.require_role(request, ["admin"])
    deleted = delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"status": "deleted"}


# Schemas

class DashboardRequest(BaseModel):
    month: str
    trade_group: str
    trade_filter: Optional[str] = "All"
    region_filter: Optional[str] = "All"

class GsheetShareholderRequest(BaseModel):
    trade_filter: Optional[str] = "All"
    region: Optional[str] = "All"
    trade_group: Optional[str] = ""

class DrilldownDriversRequest(BaseModel):
    trade_group: str
    trade_filter: Optional[str] = "All"
    region_filter: Optional[str] = "All"

class DrilldownReviewsRequest(BaseModel):
    trade_group: str
    month: str
    trade_filter: Optional[str] = "All"
    region_filter: Optional[str] = "All"


class DashboardResponse(BaseModel):
    overall_score: float
    bonus: Dict[str, Any]
    categories: Dict[str, Dict[str, Any]]
    kpi_scores: Dict[str, Any]
    category_scores: Dict[str, Any]
    live_collections: float = 0.0
    live_labour: float = 0.0
    live_materials: float = 0.0


# Meta Endpoints

@app.get("/meta/trade-groups")
def get_trade_groups():
    return TRADE_GROUPS


@app.get("/meta/trade-subgroups")
def get_trade_subgroups():
    return TRADE_SUBGROUPS


@app.get("/meta/months")
def get_months():
    return list_available_months()


@app.get("/meta/regions")
def get_regions():
    """Returns the mapping of trade groups to phase and available region options."""
    return {
        "phases": TRADE_GROUP_PHASE,
        "options": REGION_OPTIONS_BY_PHASE
    }


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
    
    # Try database first
    try:
        config = get_config("bonuspot")
        if config:
            return config
    except Exception as e:
        print(f"Error fetching bonus pots from DB: {e}")

    # Fallback to file
    if BONUS_POT_FILE.exists():
        with open(BONUS_POT_FILE, "r") as f:
            return json.load(f)
    return {}

@app.post("/config/bonus-pots")
def save_bonus_pots(pots: Dict[str, Any], request: Request):
    auth.require_role(request, ["admin", "manager"])

    # Update database
    try:
        save_config("bonuspot", pots)
    except Exception as e:
        print(f"Error saving bonus pots to DB: {e}")

    # Still update file for now (dual-write phase)
    with open(BONUS_POT_FILE, "w") as f:
        json.dump(pots, f, indent=2)
    return {"status": "success"}

@app.get("/config/kpi-config")
def get_kpi_config(request: Request):
    auth.require_user(request)

    # Load file as baseline (always includes newly added KPIs)
    file_kpis = {}
    if THRESHOLD_FILE.exists():
        try:
            with open(THRESHOLD_FILE, "r") as f:
                file_kpis = json.load(f).get("kpis", {})
        except Exception:
            pass

    # Merge DB on top: DB values win for existing KPIs, file fills in any gaps
    try:
        config = get_config("thresholds")
        if config:
            db_kpis = config.get("kpis", {})
            merged = {**file_kpis, **db_kpis}
            return merged
    except Exception as e:
        print(f"Error fetching thresholds from DB: {e}")

    return file_kpis

@app.post("/config/kpi-config")
def save_kpi_config(data: Dict[str, Any], request: Request):
    auth.require_role(request, ["admin", "manager"])

    # Update database
    try:
        save_config("thresholds", {"kpis": data})
    except Exception as e:
        print(f"Error saving thresholds to DB: {e}")

    # Still update file for now
    with open(THRESHOLD_FILE, "w") as f:
        json.dump({"kpis": data}, f, indent=2)
    
    reload_kpi_config()
    return {"status": "success"}

from fastapi import Body, Request, HTTPException

class DynamicUpdate(BaseModel):
    thresholds: List[float]
    scores: Optional[List[float]] = None

@app.put("/config/thresholds/dynamic/{kpi_name}")
def update_dynamic_threshold(kpi_name: str, trade_group: str, request: Request, payload: DynamicUpdate):
    auth.require_role(request, ["admin", "manager"])

    # Load existing data (prefer DB)
    data = None
    try:
        data = get_config("thresholds")
    except Exception as e:
        print(f"Error fetching thresholds from DB for dynamic update: {e}")
    
    if not data and THRESHOLD_FILE.exists():
        with open(THRESHOLD_FILE, "r") as f:
            data = json.load(f)
    
    if not data:
        raise HTTPException(status_code=404, detail="Thresholds configuration not found")

    kpis = data.get("kpis", {})
    if kpi_name not in kpis:
        raise HTTPException(status_code=404, detail=f"KPI '{kpi_name}' not found")

    kpi_config = kpis[kpi_name]
    if "dynamic" not in kpi_config:
        raise HTTPException(status_code=400, detail=f"KPI '{kpi_name}' is not a dynamic KPI")

    dynamic_config = kpi_config["dynamic"]
    if dynamic_config.get("type") != "trade_based":
        raise HTTPException(status_code=400, detail=f"KPI '{kpi_name}' is not trade-based")

    scores = payload.scores if payload.scores is not None else dynamic_config.get("scores", [])
    thresholds = payload.thresholds

    # Persist the (possibly trimmed) scores array so deleted rows are removed everywhere
    dynamic_config["scores"] = scores

    thresholds_by_trade = dynamic_config.setdefault("thresholds_by_trade", {})
    thresholds_by_trade[trade_group] = thresholds

    # Save to both
    try:
        save_config("thresholds", data)
    except Exception as e:
        print(f"Error saving updated thresholds to DB: {e}")

    with open(THRESHOLD_FILE, "w") as f:
        json.dump(data, f, indent=2)

    reload_kpi_config()
    return {"status": "success", "kpi": kpi_name, "trade_group": trade_group}


@app.put("/config/thresholds/dynamic/{kpi_name}/all")
def update_dynamic_threshold_all_groups(kpi_name: str, request: Request, payload: DynamicUpdate):
    auth.require_role(request, ["admin", "manager"])

    # Load existing data (prefer DB)
    data = None
    try:
        data = get_config("thresholds")
    except Exception as e:
        print(f"Error fetching thresholds from DB for dynamic update all: {e}")
    
    if not data and THRESHOLD_FILE.exists():
        with open(THRESHOLD_FILE, "r") as f:
            data = json.load(f)
    
    if not data:
        raise HTTPException(status_code=404, detail="Thresholds configuration not found")

    kpis = data.get("kpis", {})
    if kpi_name not in kpis:
        raise HTTPException(status_code=404, detail=f"KPI '{kpi_name}' not found")

    kpi_config = kpis[kpi_name]
    if "dynamic" not in kpi_config:
        raise HTTPException(status_code=400, detail=f"KPI '{kpi_name}' is not a dynamic KPI")

    dynamic_config = kpi_config["dynamic"]
    if dynamic_config.get("type") != "trade_based":
        raise HTTPException(status_code=400, detail=f"KPI '{kpi_name}' is not trade-based")

    scores = payload.scores if payload.scores is not None else dynamic_config.get("scores", [])
    thresholds = payload.thresholds

    if payload.scores is not None:
        dynamic_config["scores"] = scores

    # Build the full set of keys: all trade groups + all sub-trade keys (with name mapping)
    _SA_KEY_MAP = {"Gas & HVAC": "HVAC"}
    all_keys = set()
    for group_name, subtrades in TRADE_SUBGROUPS.items():
        all_keys.add(group_name)
        for subtrade_label in subtrades:
            all_keys.add(_SA_KEY_MAP.get(subtrade_label, subtrade_label))

    # Write thresholds to all known keys (creating missing ones too)
    thresholds_by_trade = dynamic_config.setdefault("thresholds_by_trade", {})
    for trade_key in all_keys:
        thresholds_by_trade[trade_key] = thresholds
        
    # Save to both
    try:
        save_config("thresholds", data)
    except Exception as e:
        print(f"Error saving updated thresholds to DB: {e}")

    with open(THRESHOLD_FILE, "w") as f:
        json.dump(data, f, indent=2)

    reload_kpi_config()
    return {"status": "success", "kpi": kpi_name, "applied_to": list(thresholds_by_trade.keys())}


# ------------------------------------------------------------
# DRILLDOWN ENDPOINTS
# ------------------------------------------------------------

@app.post("/api/gsheet/shareholder-breakdown")
def get_gsheet_shareholder_breakdown(data: GsheetShareholderRequest, request: Request):
    user = auth.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    from backend import get_gsheet_column_data
    col_data = get_gsheet_column_data(data.trade_filter, data.region, data.trade_group or "")
    return {
        "data": col_data,
        "trade_filter": data.trade_filter,
        "region": data.region,
        "found": bool(col_data),
    }


# Reverse lookup: raw Trade_Lookup__c value -> subgroup display name (e.g. "Gas" -> "Gas & HVAC")
_TRADE_TO_SUBGROUP: Dict[str, str] = {}
for _grp, _subs in TRADE_SUBGROUPS.items():
    for _subname, _trades in _subs.items():
        for _t in _trades:
            _TRADE_TO_SUBGROUP[_t.lower()] = _subname


def _trade_display_name(raw_trade: str) -> str:
    """Return the human-readable sub-group name for a raw Trade_Lookup__c value."""
    return _TRADE_TO_SUBGROUP.get((raw_trade or "").lower(), raw_trade)


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

    # NEW: Apply Region Filter for Drivers
    if data.region_filter != "All":
        df_trade = df_trade[
            df_trade["Effective_PostalCode__c"].apply(
                lambda pc: get_region_for_trade(pc, data.trade_group) == data.region_filter
            )
        ]

    if df_trade.empty:
        return {"drivers": [], "trade_group": data.trade_group}

    df_trade["score_numeric"] = pd.to_numeric(df_trade[score_col], errors="coerce")
    df_scored = df_trade.dropna(subset=["score_numeric"]).copy()

    # Scale to 0–10
    df_scored["score_scaled"] = df_scored["score_numeric"] * 10

    # Build results for engineers with Optidrive scores
    drivers = []
    matched_ids = set()
    for _, row in df_scored.iterrows():
        name = row.get("Engineer Name", "Unknown")
        score_raw = float(row[score_col])
        score_scaled = score_raw * 10  # Webfleet raw is 0-1, displayed as 0-10
        pc = str(row.get("Effective_PostalCode__c", ""))
        region = get_region_for_trade(pc, data.trade_group) if pc else "Unknown"
        rid = str(row.get("ServiceResourceId", ""))
        if rid:
            matched_ids.add(rid)
        drivers.append({
            "name": name if name else "Unknown",
            "score": score_scaled,          # send 0-10 value to frontend
            "below_threshold": score_scaled < 7.0,  # consistent with KPI: < 7 on 0-10 scale
            "trade": _trade_display_name(str(row.get("Trade_Lookup__c", "Unknown"))),
            "region": region,
            "missing_data": False,
        })

    # Sort scored drivers: worst scores first
    drivers.sort(key=lambda d: d["score"])

    # Find engineers in SF for this trade/region who have no Optidrive data
    df_engineers_all = fetch_service_resources()
    if not df_engineers_all.empty:
        if trades:
            df_eng_filtered = df_engineers_all[df_engineers_all["Trade_Lookup__c"].isin(trades)].copy()
        else:
            df_eng_filtered = df_engineers_all[df_engineers_all["Trade Group"] == data.trade_group].copy()

        if data.region_filter != "All" and not df_eng_filtered.empty:
            df_eng_filtered = df_eng_filtered[
                df_eng_filtered["Effective_PostalCode__c"].apply(
                    lambda pc: get_region_for_trade(str(pc) if pc else "", data.trade_group) == data.region_filter
                )
            ]

        for _, row in df_eng_filtered.iterrows():
            rid = str(row.get("ServiceResourceId", ""))
            if rid in matched_ids:
                continue
            name = row.get("Engineer Name", "Unknown")
            pc = str(row.get("Effective_PostalCode__c", ""))
            region = get_region_for_trade(pc, data.trade_group) if pc else "Unknown"
            drivers.append({
                "name": name if name else "Unknown",
                "score": None,
                "below_threshold": False,
                "trade": _trade_display_name(str(row.get("Trade_Lookup__c", "Unknown"))),
                "region": region,
                "missing_data": True,
            })

    missing_count = sum(1 for d in drivers if d["missing_data"])
    return {
        "drivers": drivers,
        "trade_group": data.trade_group,
        "total_count": len(drivers),
        "scored_count": len(drivers) - missing_count,
        "missing_count": missing_count,
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

        # NEW: Apply Region Filter
        if data.region_filter != "All":
            df_filtered = df_filtered[
                df_filtered["Effective_PostalCode__c"].apply(
                    lambda pc: get_region_for_trade(pc, data.trade_group) == data.region_filter
                )
            ]

        ops = []
        for _, row in df_filtered.iterrows():
            name = row.get("Engineer Name", "") or "Unknown"
            trade = str(row.get("Trade_Lookup__c", "Unknown"))
            pc = str(row.get("Effective_PostalCode__c", ""))
            region = get_region_for_trade(pc, data.trade_group) if pc else "Unknown"
            ops.append({"name": name, "trade": trade, "region": region})

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

        # NEW: Apply Region Filter for SAs
        if data.region_filter != "All":
            df_sa = df_sa[
                df_sa["PostalCode"].apply(
                    lambda pc: get_region_for_trade(pc, data.trade_group) == data.region_filter
                )
            ]

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


@app.post("/api/drilldown/vcr-update")
def get_vcr_update(data: DrilldownReviewsRequest, request: Request):
    """
    Returns the VCR forms submitted per driver for a given trade group.
    """
    user = auth.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    import pandas as pd
    import traceback

    try:
        # Use get_merged_vehicular_data() to only show people who actually drive (the "drivers")
        df_all_drivers = get_merged_vehicular_data()
        if df_all_drivers.empty:
            return {"drivers": [], "trade_group": data.trade_group, "total_count": 0}

        # Filter to specific trades via trade_filter
        trades = resolve_trades_for_filters(data.trade_group, data.trade_filter)
        if trades:
            df_filtered = df_all_drivers[df_all_drivers["Trade_Lookup__c"].isin(trades)].copy()
        else:
            df_filtered = df_all_drivers[df_all_drivers["Trade Group"] == data.trade_group].copy()

        # Apply Region Filter
        if data.region_filter != "All":
            df_filtered = df_filtered[
                df_filtered["Effective_PostalCode__c"].apply(
                    lambda pc: get_region_for_trade(pc, data.trade_group) == data.region_filter
                )
            ]


        # Fetch VCR forms for the selected month
        # Use get_month_range(data.month) here to accurately reflect the dashboard's selected month
        start_iso, end_iso = get_month_range(data.month)
        df_vcr = fetch_vcr_forms(start_iso, end_iso)

        driver_stats = []
        for _, row in df_filtered.iterrows():
            name = row.get("Engineer Name", "") or "Unknown"
            trade = str(row.get("Trade_Lookup__c", "Unknown"))
            pc = str(row.get("Effective_PostalCode__c", ""))
            region = get_region_for_trade(pc, data.trade_group) if pc else "Unknown"
            resource_id = str(row.get("ServiceResourceId", "")) # Using ServiceResourceId from fetch_service_resources
            
            submissions = 0
            if not df_vcr.empty and resource_id:
                # Count VCR records for this specific Service Resource ID
                # The user confirmed: Current_Engineer_Assigned_to_Vehicle__c = ServiceResourceId
                submissions = len(df_vcr[df_vcr["Current_Engineer_Assigned_to_Vehicle__c"].astype(str) == resource_id])

            driver_stats.append({
                "name": name,
                "trade": trade,
                "region": region,
                "submissions": submissions,
                "target": 2, # Fixed target per driver per user specification
            })

        # Sort alphabetically by name
        driver_stats.sort(key=lambda o: o["name"])

        return {
            "drivers": driver_stats,
            "trade_group": data.trade_group,
            "total_count": len(driver_stats),
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/drilldown/satisfaction-form-update")
def get_satisfaction_form_update(data: DrilldownReviewsRequest, request: Request):
    """
    Returns per-engineer satisfaction form submission status (0/1 or 1/1) for a given trade group and month.
    """
    user = auth.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    import traceback

    try:
        df_engineers = fetch_service_resources()
        if df_engineers.empty:
            return {"engineers": [], "trade_group": data.trade_group, "total_count": 0, "submitted_count": 0}

        trades = resolve_trades_for_filters(data.trade_group, data.trade_filter)
        if trades:
            df_filtered = df_engineers[df_engineers["Trade_Lookup__c"].isin(trades)].copy()
        else:
            df_filtered = df_engineers[df_engineers["Trade Group"] == data.trade_group].copy()

        if data.region_filter != "All":
            df_filtered = df_filtered[
                df_filtered["Effective_PostalCode__c"].apply(
                    lambda pc: get_region_for_trade(str(pc) if pc else "", data.trade_group) == data.region_filter
                )
            ]

        # Fetch satisfaction forms for the selected month
        trades_tuple = tuple(trades) if trades else ()
        trades_str = ",".join([f"'{t}'" for t in trades_tuple]) if trades_tuple else "''"
        start_iso, end_iso = get_month_range(data.month)
        from backend import sf_client, queries
        q = queries.get_engineer_satisfaction_query(trades_str, start_iso, end_iso)
        try:
            res = sf_client().query_all(q)
            records = res.get("records", [])
        except Exception:
            records = []

        # Build a set of resource IDs that submitted a form
        submitted_ids = set()
        for rec in records:
            rid = str(rec.get("Service_Resource__c") or "")
            if rid:
                submitted_ids.add(rid)

        engineer_stats = []
        for _, row in df_filtered.iterrows():
            name = row.get("Engineer Name", "") or "Unknown"
            trade = _trade_display_name(str(row.get("Trade_Lookup__c", "Unknown")))
            pc = str(row.get("Effective_PostalCode__c", ""))
            region = get_region_for_trade(pc, data.trade_group) if pc else "Unknown"
            resource_id = str(row.get("ServiceResourceId", ""))
            submitted = 1 if resource_id and resource_id in submitted_ids else 0
            engineer_stats.append({
                "name": name,
                "trade": trade,
                "region": region,
                "submitted": submitted,
                "target": 1,
            })

        # Sort: not submitted first, then alphabetically
        engineer_stats.sort(key=lambda o: (o["submitted"], o["name"]))

        return {
            "engineers": engineer_stats,
            "trade_group": data.trade_group,
            "total_count": len(engineer_stats),
            "submitted_count": sum(1 for e in engineer_stats if e["submitted"] == 1),
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

        # NEW: Apply Region Filter
        if data.region_filter != "All" and "PostalCode" in df_attended.columns:
            df_attended = df_attended[
                df_attended["PostalCode"].apply(
                    lambda pc: get_region_for_trade(pc, data.trade_group) == data.region_filter
                )
            ]
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
        df_sa["ArrivalWindowEndTime"] = pd.to_datetime(df_sa.get("ArrivalWindowEndTime"), errors="coerce")

        # NEW: Apply Region Filter
        if data.region_filter != "All" and "PostalCode" in df_sa.columns:
            df_sa = df_sa[
                df_sa["PostalCode"].apply(
                    lambda pc: get_region_for_trade(pc, data.trade_group) == data.region_filter
                )
            ]
            if df_sa.empty:
                return {"engineers": [], "trade_group": data.trade_group, "total_late": 0, "total_sas": 0}

        # Flatten Allocated_Engineer__r.Name
        if "Allocated_Engineer__r" in df_sa.columns:
            df_sa["EngineerName"] = (
                df_sa["Allocated_Engineer__r"]
                .apply(lambda x: x.get("Name") if isinstance(x, dict) else None)
            )
        else:
            df_sa["EngineerName"] = None

        # Calculate late flag (same logic as compute_kpis: ArrivalWindowEndTime + 0 min)
        valid = df_sa.dropna(subset=["ActualStartTime", "ArrivalWindowEndTime"]).copy()
        valid["Late"] = (
            (valid["ActualStartTime"] - valid["ArrivalWindowEndTime"]).dt.total_seconds() / 60 > 0
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

        # NEW: Apply Region Filter using service resource postcode crosswalk
        if data.region_filter != "All" and not df.empty:
            from backend import fetch_service_resources
            df_engineers = fetch_service_resources()
            if not df_engineers.empty:
                # Build name -> region mapping
                name_to_region = {}
                for _, er in df_engineers.iterrows():
                    ename = er.get("Engineer Name", "")
                    pc = str(er.get("Effective_PostalCode__c", "") or "")
                    region = get_region_for_trade(pc, data.trade_group) if pc else "Unknown"
                    name_to_region[ename] = region
                cases = [c for c in cases if name_to_region.get(c["engineer_name"], "Unknown") == data.region_filter]

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

        # NEW: Apply Region Filter
        if data.region_filter != "All" and "PostalCode" in df_tqr_not_sat.columns:
            df_tqr_not_sat = df_tqr_not_sat[
                df_tqr_not_sat["PostalCode"].apply(
                    lambda pc: get_region_for_trade(pc, data.trade_group) == data.region_filter
                )
            ]

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

    # NEW: Apply Region Filter
    if data.region_filter != "All" and "PostalCode" in with_review.columns:
        with_review = with_review[
            with_review["PostalCode"].apply(
                lambda pc: get_region_for_trade(pc, data.trade_group) == data.region_filter
            )
        ]

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
        # Maps dashboard trade names to the keys used in thresholds_by_trade config
        TRADE_TO_THRESHOLD_KEY = {
            "Gas & HVAC": "HVAC",
        }

        # Determine threshold key
        # If specific trade selected (and not "All"), use that trade name for thresholds.
        # If "All" selected, use the Group Name for thresholds.
        threshold_key = req_group
        if req_trade and req_trade != "All":
            threshold_key = TRADE_TO_THRESHOLD_KEY.get(req_trade, req_trade)
            
        req_region = data.region_filter or "All"

        result = compute_kpis(
            req_group, trades, start_iso, end_iso,
            scoring_key=threshold_key, bonus_trade=req_trade, region_filter=req_region,
            trade_filter=req_trade or "All"
        )

        # Fetch Base Bonus Pot from Google Sheet (Excel) for the blue card
        bonus = dict(result["bonus"])
        try:
            from backend import get_gsheet_column_data, TRADE_TO_SHEET_PREFIX
            if req_trade and req_trade != "All":
                if req_trade in TRADE_TO_SHEET_PREFIX:
                    # Sub-trade has its own sheet column — look it up directly
                    sub_trade_data = get_gsheet_column_data(req_trade, req_region, trade_group="")
                    gsheet_pot = sub_trade_data.get("Base Bonus Pot")
                    if gsheet_pot is not None:
                        bonus["gsheet_pot"] = float(gsheet_pot)
                    else:
                        bonus["bonus_pot_unavailable"] = req_trade
                else:
                    # No individual pot for this sub-trade
                    bonus["bonus_pot_unavailable"] = req_trade
            else:
                gsheet_data = get_gsheet_column_data(req_trade, req_region, req_group)
                gsheet_pot = gsheet_data.get("Base Bonus Pot")
                if gsheet_pot is not None:
                    bonus["gsheet_pot"] = float(gsheet_pot)
        except Exception:
            pass

        return {
            "overall_score": result["overall_score"],
            "bonus": bonus,
            "categories": result["categories"],
            "kpi_scores": result["kpi_scores"],
            "category_scores": result["category_scores"],
            "live_collections": result.get("live_collections", 0.0),
            "live_labour": result.get("live_labour", 0.0),
            "live_materials": result.get("live_materials", 0.0)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
