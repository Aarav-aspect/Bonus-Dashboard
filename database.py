import os
import json
import psycopg2
import toml
from psycopg2.extras import RealDictCursor, Json
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Prioritize .env, then secrets.toml
DATABASE_URL = os.getenv("DATABASE_URL")

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
    """Create the app_configs table if it doesn't exist."""
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

