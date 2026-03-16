import json
from pathlib import Path
from database import initialize_db, save_config

def migrate():
    print("🚀 Initializing database...")
    initialize_db()
    
    configs = {
        "bonuspot": "bonuspot.json",
        "thresholds": "thresholds.json"
    }
    
    for key, filename in configs.items():
        path = Path(filename)
        if path.exists():
            print(f"✅ Migrating {filename} to database...")
            with open(path, "r") as f:
                data = json.load(f)
                save_config(key, data)
            print(f"✨ Successfully migrated {key}")
        else:
            print(f"⚠️ Warning: {filename} not found, skipping.")

if __name__ == "__main__":
    try:
        migrate()
        print("\n🎉 Migration complete!")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
