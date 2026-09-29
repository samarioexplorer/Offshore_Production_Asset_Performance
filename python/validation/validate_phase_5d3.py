from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "offshore_production_asset_performance.db"
)

EXPECTED_VIEWS = [
    "vw_Production_Daily",
    "vw_Production_Monthly",
    "vw_Production_Annual",
    "vw_Well_Production_Summary",
    "vw_Field_Production_Summary",
    "vw_Downtime_Summary",
    "vw_Failure_Cause_Analysis",
    "vw_Well_Reliability_Summary",
    "vw_Economics_Daily",
    "vw_Economics_Well_Summary",
    "vw_Economics_Field_Summary",
    "vw_Economics_Scenario_Summary",
    "vw_Economics_Annual_Summary",
    "vw_Intervention_Economics",
    "vw_Intervention_Well_Summary",
    "vw_Intervention_Type_Summary",
    "vw_Intervention_Annual_Summary",
]


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as connection:

        actual_views = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'view'
                """
            )
        }

    results = []

    for view_name in EXPECTED_VIEWS:
        results.append(
            (
                view_name,
                view_name in actual_views,
            )
        )

    passed = sum(status for _, status in results)
    failed = len(results) - passed

    print("=" * 72)
    print("PHASE 5D.3 — SQL VIEW INVENTORY VALIDATION")
    print("=" * 72)
    print()

    for view_name, status in results:
        print(
            f"{view_name:<48} | "
            f"{'PASS' if status else 'FAIL'}"
        )

    print()
    print("-" * 72)
    print(f"EXPECTED VIEWS : {len(EXPECTED_VIEWS)}")
    print(f"FOUND VIEWS    : {passed}")
    print(f"MISSING VIEWS  : {failed}")
    print("-" * 72)

    if failed == 0:
        print("PHASE 5D.3 SQL VIEW INVENTORY STATUS: PASS")
    else:
        print("PHASE 5D.3 SQL VIEW INVENTORY STATUS: FAIL")
        raise SystemExit(1)


if __name__ == "__main__":
    main()