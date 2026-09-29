from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "offshore_production_asset_performance.db"
)
SQL_PATH = (
    PROJECT_ROOT
    / "sql"
    / "02_production"
    / "02_production_summary.sql"
)


def create_production_views() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    if not SQL_PATH.exists():
        raise FileNotFoundError(
            f"SQL file not found: {SQL_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")

        sql = SQL_PATH.read_text(encoding="utf-8")
        connection.executescript(sql)

    print("=" * 72)
    print("PHASE 5D.1 — PRODUCTION SQL VIEW RECREATION")
    print("=" * 72)
    print()
    print("Production analytical views recreated successfully.")
    print()
    print("PHASE 5D.1 SQL RECREATION STATUS: PASS")


if __name__ == "__main__":
    create_production_views()