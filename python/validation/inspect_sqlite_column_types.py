import sqlite3
from pathlib import Path

DB_PATH = Path("database/offshore_production_asset_performance.db")

connection = sqlite3.connect(DB_PATH)

tables = connection.execute(
    """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
      AND name NOT LIKE 'sqlite_%'
    ORDER BY name
    """
).fetchall()

print("=" * 110)
print("PHASE 6B.3 — SQLITE COLUMN TYPE INVENTORY")
print("=" * 110)

for (table_name,) in tables:
    print()
    print(f"TABLE: {table_name}")
    print("-" * 110)

    columns = connection.execute(
        f'PRAGMA table_info("{table_name}")'
    ).fetchall()

    print(
        f"{'CID':<5}"
        f"{'COLUMN':<38}"
        f"{'SQLITE TYPE':<18}"
        f"{'NOT NULL':<12}"
        f"{'PK':<5}"
    )

    print("-" * 110)

    for column in columns:
        cid = column[0]
        name = column[1]
        data_type = column[2]
        not_null = column[3]
        primary_key = column[5]

        print(
            f"{cid:<5}"
            f"{name:<38}"
            f"{data_type:<18}"
            f"{'YES' if not_null else 'NO':<12}"
            f"{'YES' if primary_key else 'NO':<5}"
        )

print()
print("=" * 110)
print(f"TOTAL TABLES: {len(tables)}")
print("=" * 110)

connection.close()