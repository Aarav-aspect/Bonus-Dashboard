import os
import json
import psycopg2
import toml
from psycopg2.extras import RealDictCursor, Json
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Prioritize .env, then secrets.toml
# Strip whitespace from env var names to handle Cloud Run env vars with trailing spaces
_env = {k.strip(): v for k, v in os.environ.items()}
DATABASE_URL = _env.get("DATABASE_URL")

if not DATABASE_URL:
    secrets_path = Path("secrets.toml")
    if secrets_path.exists():
        try:
            secrets = toml.load(secrets_path)
            DATABASE_URL = secrets.get("database", {}).get("url")
        except Exception as e:
            print(f"Warning: Could not load secrets.toml: {e}")

def get_db_connection():
    if not DATABASE_URL:
        # Fallback for dev if needed, though production requires DATABASE_URL
        raise ValueError("DATABASE_URL not found in .env or secrets.toml. Please add it to one of them.")
    
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def initialize_db():
    """Create the app_configs and app_users tables if they don't exist."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_configs (
                    config_key VARCHAR(100) PRIMARY KEY,
                    config_data JSONB NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255),
                    role VARCHAR(50) NOT NULL DEFAULT 'user',
                    assigned_group VARCHAR(255),
                    assigned_trade VARCHAR(255),
                    assigned_region VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
        conn.commit()
    finally:
        conn.close()

def get_config(key: str):
    """Fetch a configuration by key."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT config_data FROM app_configs WHERE config_key = %s", (key,))
            row = cur.fetchone()
            return row['config_data'] if row else None
    finally:
        conn.close()

def save_config(key: str, data: dict):
    """Save or update a configuration."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO app_configs (config_key, config_data, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (config_key) DO UPDATE
                SET config_data = EXCLUDED.config_data,
                    updated_at = CURRENT_TIMESTAMP;
            """, (key, Json(data)))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

def get_all_users() -> list:
    """Return all managed users."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id::text, email, name, role,
                       assigned_group, assigned_trade, assigned_region,
                       created_at, updated_at
                FROM app_users
                ORDER BY created_at ASC;
            """)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_user_by_email(email: str) -> dict | None:
    """Return a single user by email, or None."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id::text, email, name, role,
                       assigned_group, assigned_trade, assigned_region
                FROM app_users
                WHERE LOWER(email) = LOWER(%s);
            """, (email,))
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def create_user(data: dict) -> dict:
    """Insert a new user and return the created row."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO app_users (email, name, role, assigned_group, assigned_trade, assigned_region)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id::text, email, name, role,
                          assigned_group, assigned_trade, assigned_region,
                          created_at, updated_at;
            """, (
                data["email"],
                data.get("name"),
                data.get("role", "user"),
                data.get("assigned_group"),
                data.get("assigned_trade"),
                data.get("assigned_region"),
            ))
            conn.commit()
            return dict(cur.fetchone())
    finally:
        conn.close()


def update_user(user_id: str, data: dict) -> dict | None:
    """Update a user by UUID. Returns updated row or None if not found."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE app_users
                SET name            = COALESCE(%s, name),
                    role            = COALESCE(%s, role),
                    assigned_group  = %s,
                    assigned_trade  = %s,
                    assigned_region = %s,
                    updated_at      = CURRENT_TIMESTAMP
                WHERE id = %s::uuid
                RETURNING id::text, email, name, role,
                          assigned_group, assigned_trade, assigned_region,
                          created_at, updated_at;
            """, (
                data.get("name"),
                data.get("role"),
                data.get("assigned_group"),
                data.get("assigned_trade"),
                data.get("assigned_region"),
                user_id,
            ))
            conn.commit()
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def delete_user(user_id: str) -> bool:
    """Delete a user by UUID. Returns True if a row was deleted."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM app_users WHERE id = %s::uuid;", (user_id,))
            conn.commit()
            return cur.rowcount > 0
    finally:
        conn.close()
