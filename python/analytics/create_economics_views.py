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
    / "04_economics"
    / "01_economics_summary.sql"
)


EXPECTED_VIEWS = {
    "vw_Economics_Annual_Summary",
    "vw_Economics_Daily",
    "vw_Economics_Field_Summary",
    "vw_Economics_Scenario_Summary",
    "vw_Economics_Well_Summary",
}


def create_economics_views() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    if not SQL_PATH.exists():
        raise FileNotFoundError(
            f"Economics SQL file not found: {SQL_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")

        sql = SQL_PATH.read_text(encoding="utf-8")
        connection.executescript(sql)

        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'view'
              AND name LIKE 'vw_Economics_%'
            ORDER BY name;
            """
        ).fetchall()

    actual_views = {row[0] for row in rows}

    if actual_views != EXPECTED_VIEWS:
        raise RuntimeError(
            "Unexpected economics views.\n"
            f"Expected: {sorted(EXPECTED_VIEWS)}\n"
            f"Actual:   {sorted(actual_views)}"
        )

    print("=" * 72)
    print("PHASE 5C.3 — ECONOMICS ANALYTICS SQL")
    print("=" * 72)
    print()
    print("Economics views created successfully.")
    print()

    for view in sorted(actual_views):
        print(f"  {view}")

    print()
    print("PHASE 5C.3 SQL STATUS: PASS")


if __name__ == "__main__":
    create_economics_views()