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
    / "01_load_core_tables.sql"
)


def load_core() -> None:
    """Promote validated staging data into the relational core model."""

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    if not SQL_PATH.exists():
        raise FileNotFoundError(
            f"Core-load SQL file not found: {SQL_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")

        foreign_keys = connection.execute(
            "PRAGMA foreign_keys;"
        ).fetchone()[0]

        if foreign_keys != 1:
            raise RuntimeError(
                "SQLite foreign-key enforcement is not enabled."
            )

        sql = SQL_PATH.read_text(encoding="utf-8")

        try:
            connection.executescript(sql)
        except Exception:
            connection.rollback()
            raise

    print("=" * 72)
    print("PHASE 5B.2 — CORE RELATIONAL LOAD")
    print("=" * 72)
    print()
    print(f"Database: {DATABASE_PATH}")
    print(f"SQL:      {SQL_PATH}")
    print()
    print("Core relational load completed successfully.")
    print("Foreign-key enforcement: ON")
    print("PHASE 5B.2 LOAD STATUS: PASS")


if __name__ == "__main__":
    load_core()