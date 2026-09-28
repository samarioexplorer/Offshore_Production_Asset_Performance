from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "offshore_production_asset_performance.db"
)

SCHEMA_PATH = (
    PROJECT_ROOT
    / "sql"
    / "01_staging"
    / "01_initialize_database.sql"
)


def initialize_database() -> None:
    """Initialize the SQLite database from the authoritative SQL schema."""

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")

        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

        connection.executescript(schema_sql)

        foreign_keys = connection.execute(
            "PRAGMA foreign_keys;"
        ).fetchone()[0]

    print("=" * 72)
    print("PHASE 5A — SQLITE DATABASE INITIALIZATION")
    print("=" * 72)
    print()
    print(f"Database: {DATABASE_PATH}")
    print(f"Schema:   {SCHEMA_PATH}")
    print()
    print("Schema initialized successfully.")
    print(f"Foreign-key enforcement: {'ON' if foreign_keys else 'OFF'}")


if __name__ == "__main__":
    initialize_database()