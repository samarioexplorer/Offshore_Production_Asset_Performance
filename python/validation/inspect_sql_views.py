from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "offshore_production_asset_performance.db"
)


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            """
            SELECT name, sql
            FROM sqlite_master
            WHERE type = 'view'
            ORDER BY name;
            """
        ).fetchall()

        print("=" * 72)
        print("PHASE 5D.1 — SQL VIEW DEFINITIONS")
        print("=" * 72)

        for name, sql in rows:
            print()
            print(name)
            print("-" * 72)
            print(sql)


if __name__ == "__main__":
    main()