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
    resolve_trades_for_filters,
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
def signin_microsoft():
    """Redirect user to Microsoft login page."""
    auth_url = (
        f"https://login.microsoftonline.com/{auth.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize"
        f"?client_id={auth.MICROSOFT_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={auth.REDIRECT_URI}"
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
    # 1. Exchange code for tokens
    token_data = await auth.exchange_code_for_token(code)

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
    redirect = RedirectResponse(url=f"{auth.FRONTEND_URL}/dashboard")
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


class DashboardResponse(BaseModel):
    overall_score: float
    bonus: Dict[str, Any]
    categories: Dict[str, Dict[str, Any]]
    kpi_scores: Dict[str, Any]
    category_scores: Dict[str, Any]


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

@app.put("/config/thresholds/dynamic/{kpi_name}")
def update_dynamic_threshold(kpi_name: str, trade_group: str, thresholds: List[float], request: Request):
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
def update_dynamic_threshold_all_groups(kpi_name: str, thresholds: List[float], request: Request):
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

        result = compute_kpis(req_group, trades, start_iso, end_iso, scoring_key=threshold_key)

        return {
            "overall_score": result["overall_score"],
            "bonus": result["bonus"],
            "categories": result["categories"],
            "kpi_scores": result["kpi_scores"],
            "category_scores": result["category_scores"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
