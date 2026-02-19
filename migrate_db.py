import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Load env variables if .env exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DATABASE_URL = os.getenv("DATABASE_URL")

def migrate():
    if not DATABASE_URL:
        print("Error: DATABASE_URL not found.")
        return

    print("Connecting to Postgres...")
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()

    # User Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS "user" (
            id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE,
            "emailVerified" BOOLEAN DEFAULT FALSE,
            image TEXT,
            role TEXT DEFAULT 'user',
            "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            "updatedAt" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # Ensure active and scope columns exist if table was already created
    c.execute('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT FALSE;')
    c.execute('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS assigned_group TEXT;')
    c.execute('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS assigned_trade TEXT;')

    # Session Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS session (
            id TEXT PRIMARY KEY,
            "sessionToken" TEXT UNIQUE,
            "userId" TEXT NOT NULL,
            "expiresAt" TIMESTAMP WITH TIME ZONE NOT NULL,
            "ipAddress" TEXT,
            "userAgent" TEXT,
            "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY("userId") REFERENCES "user"(id) ON DELETE CASCADE
        );
    ''')

    # Account Table (OAuth)
    c.execute('''
        CREATE TABLE IF NOT EXISTS account (
            id TEXT PRIMARY KEY,
            "userId" TEXT NOT NULL,
            type TEXT NOT NULL,
            provider TEXT NOT NULL,
            "providerAccountId" TEXT NOT NULL,
            refresh_token TEXT,
            access_token TEXT,
            expires_at INTEGER,
            token_type TEXT,
            scope TEXT,
            id_token TEXT,
            session_state TEXT,
            "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            "updatedAt" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY("userId") REFERENCES "user"(id) ON DELETE CASCADE,
            UNIQUE(provider, "providerAccountId")
        );
    ''')

    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
