import sqlite3
from pathlib import Path


DB_PATH = Path(
    r"C:\Users\aniba\Documents\Offshore_Production_Asset_Performance"
) / "database" / "offshore_production_asset_performance.db"


conn = sqlite3.connect(DB_PATH)

print("=" * 78)
print("vw_Economics_Daily — COLUMN INVENTORY")
print("=" * 78)

columns = conn.execute(
    'PRAGMA table_info("vw_Economics_Daily")'
).fetchall()

for cid, name, data_type, notnull, default_value, pk in columns:
    print(
        f"{cid:>3} | "
        f"{name:<40} | "
        f"{data_type:<12} | "
        f"NOT NULL={notnull} | "
        f"PK={pk}"
    )

print("=" * 78)

conn.close()