"""
Stateless Azure AD Authentication Module
=========================================
Zero database dependency. JWT sessions validated against Azure AD JWKS.
Roles are read from Azure AD App Roles claims.

Role format in Azure AD:
  - "admin"
  - "manager"
  - "trade_group_manager:HVAC"
  - "trade_manager:HVAC:Heating"
  - "user"
"""

import os
import time
import httpx
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, Request, Response

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "a7682cd1-5ec8-4228-a2fa-26e000133b18")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "hAO8Q~yrza0jXMBoCBxESJjkpLphTzFh6uKLkby7")
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "93ce9c27-3bb2-4ef2-b686-1829de4f2584")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/api/auth/callback/microsoft")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Secret key for signing our own session JWT (NOT the Azure AD token)
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-to-a-real-secret-in-production")
JWT_ALGORITHM = "HS256"
SESSION_EXPIRY_DAYS = 7

SESSION_COOKIE_NAME = "session_token"

# Azure AD JWKS cache
_jwks_cache = {"keys": None, "fetched_at": 0}
JWKS_CACHE_TTL = 3600  # 1 hour

# ---------------------------------------------------------------------------
# Azure AD JWKS (for validating ID tokens from Microsoft)
# ---------------------------------------------------------------------------

async def _fetch_jwks():
    """Fetch Azure AD public signing keys (JWKS)."""
    now = time.time()
    if _jwks_cache["keys"] and (now - _jwks_cache["fetched_at"]) < JWKS_CACHE_TTL:
        return _jwks_cache["keys"]

    jwks_url = f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/discovery/v2.0/keys"
    async with httpx.AsyncClient() as client:
        resp = await client.get(jwks_url)
        resp.raise_for_status()
        keys = resp.json()["keys"]
        _jwks_cache["keys"] = keys
        _jwks_cache["fetched_at"] = now
        return keys


async def verify_azure_id_token(id_token: str) -> dict:
    """
    Validate an Azure AD ID token against the JWKS endpoint.
    Returns the decoded claims dict.
    """
    keys = await _fetch_jwks()

    # Build the JWKS key set for python-jose
    try:
        unverified_header = jwt.get_unverified_header(id_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid ID token header")

    # Find the matching key
    rsa_key = None
    for key in keys:
        if key.get("kid") == unverified_header.get("kid"):
            rsa_key = key
            break

    if not rsa_key:
        raise HTTPException(status_code=401, detail="Unable to find matching signing key")

    try:
        payload = jwt.decode(
            id_token,
            rsa_key,
            algorithms=["RS256"],
            audience=MICROSOFT_CLIENT_ID,
            issuer=f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/v2.0",
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")


# ---------------------------------------------------------------------------
# OAuth Code Exchange
# ---------------------------------------------------------------------------

async def exchange_code_for_token(code: str) -> dict:
    """Exchange authorization code for tokens (access_token + id_token)."""
    token_url = f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
    data = {
        "client_id": MICROSOFT_CLIENT_ID,
        "scope": "User.Read openid profile email",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
        "client_secret": MICROSOFT_CLIENT_SECRET,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to fetch token: {response.text}")
        return response.json()


# ---------------------------------------------------------------------------
# Role Parsing (from Azure AD App Roles)
# ---------------------------------------------------------------------------

# Azure AD doesn't allow special chars (&, commas, spaces) in role values.
# We use simplified slugs in Azure and map them to real trade group names here.
ROLE_ALIAS_MAP = {
    # Trade groups
    "hvac_electrical": "HVac & Electrical",
    "building_fabric": "Building Fabric",
    "environmental_services": "Environmental Services",
    "fire_safety": "Fire Safety",
    "leak_damp_restoration": "Leak, Damp & Restoration",
    "plumbing_drainage": "Plumbing & Drainage",
    # Sub-trades (add more as needed)
    "air_conditioning": "Air Conditioning",
    "gas_heating": "Gas & Heating",
    "electrical": "Electrical",
    "decoration": "Decoration",
    "roofing": "Roofing",
    "multi_trades": "Multi Trades",
    "project_management": "Project Management",
    "gardening": "Gardening",
    "pest_control": "Pest Control",
    "specialist_cleaning": "Specialist Cleaning",
    "waste_grease": "Waste and Grease Management",
    "fire_safety_sub": "Fire Safety",
    "leak_detection": "Leak Detection",
    "damp": "Damp",
    "plumbing": "Plumbing",
    "drainage": "Drainage",
}


def _resolve_alias(slug: str) -> str:
    """Resolve an Azure-safe slug to the real trade group/sub-trade name."""
    return ROLE_ALIAS_MAP.get(slug, slug)


def parse_role_claims(roles: list) -> dict:
    """
    Parse Azure AD App Roles into role + scoping info.

    Roles are encoded as (using Azure-safe slugs):
      "admin"                                      → role=admin
      "manager"                                    → role=manager
      "user"                                       → role=user
      "trade_group_manager:hvac_electrical"         → role=trade_group_manager, assigned_group=HVac & Electrical
      "trade_manager:hvac_electrical:gas_heating"   → role=trade_manager, assigned_group=HVac & Electrical, assigned_trade=Gas & Heating

    If a user has multiple roles, the highest-privilege one wins.
    Priority: admin > manager > trade_group_manager > trade_manager > user
    """
    ROLE_PRIORITY = {
        "admin": 5,
        "manager": 4,
        "trade_group_manager": 3,
        "trade_manager": 2,
        "user": 1,
    }

    best = {"role": "user", "assigned_group": None, "assigned_trade": None, "_priority": 0}

    for role_str in (roles or []):
        parts = role_str.split(":")
        base_role = parts[0]

        if base_role not in ROLE_PRIORITY:
            continue

        priority = ROLE_PRIORITY[base_role]
        if priority <= best["_priority"]:
            continue

        assigned_group = _resolve_alias(parts[1]) if len(parts) > 1 else None
        assigned_trade = _resolve_alias(parts[2]) if len(parts) > 2 else None

        best = {
            "role": base_role,
            "assigned_group": assigned_group,
            "assigned_trade": assigned_trade,
            "_priority": priority,
        }

    del best["_priority"]
    return best


# ---------------------------------------------------------------------------
# Session JWT (our own cookie-based session)
# ---------------------------------------------------------------------------

def create_session_token(user_data: dict) -> str:
    """
    Create a signed JWT containing user info for our session cookie.
    This is NOT the Azure AD token — it's our own compact session.
    """
    payload = {
        "sub": user_data["id"],
        "name": user_data["name"],
        "email": user_data["email"],
        "role": user_data["role"],
        "assigned_group": user_data.get("assigned_group"),
        "assigned_trade": user_data.get("assigned_trade"),
        "exp": datetime.utcnow() + timedelta(days=SESSION_EXPIRY_DAYS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_dev_token(role: str, group: str = None, trade: str = None) -> str:
    """
    Create a session token for a developer/test user.
    """
    user_data = {
        "id": "dev-user-id",
        "name": "Developer User",
        "email": "dev@example.com",
        "role": role,
        "assigned_group": group,
        "assigned_trade": trade,
    }
    return create_session_token(user_data)


def decode_session_token(token: str) -> dict:
    """Decode and validate our session JWT."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "id": payload["sub"],
            "name": payload.get("name"),
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
            "assigned_group": payload.get("assigned_group"),
            "assigned_trade": payload.get("assigned_trade"),
        }
    except JWTError:
        return None


def set_session_cookie(response: Response, token: str):
    """Set the session JWT as an HTTP-only cookie."""
    expires = datetime.utcnow() + timedelta(days=SESSION_EXPIRY_DAYS)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,  # Set to True in production (HTTPS)
        samesite="lax",
        path="/",
        expires=int(expires.timestamp()),
    )


# ---------------------------------------------------------------------------
# Request Helpers
# ---------------------------------------------------------------------------

def get_current_user(request: Request) -> Optional[dict]:
    """
    Extract the current user from the session cookie JWT.
    Returns user dict or None if not authenticated.
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    return decode_session_token(token)


def require_user(request: Request) -> dict:
    """Get current user or raise 401."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


def require_role(request: Request, allowed_roles: list) -> dict:
    """Get current user and verify they have one of the allowed roles."""
    user = require_user(request)
    if user["role"] not in allowed_roles:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user
