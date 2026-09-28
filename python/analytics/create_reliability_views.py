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
    / "03_reliability"
    / "01_reliability_summary.sql"
)


def create_reliability_views() -> None:
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
    print("PHASE 5C.2 — RELIABILITY ANALYTICS SQL")
    print("=" * 72)
    print()
    print("Reliability views created successfully.")
    print("PHASE 5C.2 SQL STATUS: PASS")


if __name__ == "__main__":
    create_reliability_views()