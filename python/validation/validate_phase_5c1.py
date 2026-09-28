from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "offshore_production_asset_performance.db"
)


EXPECTED_VIEWS = {
    "vw_Production_Daily",
    "vw_Production_Monthly",
    "vw_Production_Annual",
    "vw_Well_Production_Summary",
    "vw_Field_Production_Summary",
}


def validate_phase_5c1() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as connection:

        views = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'view';
                """
            )
        }

        missing_views = EXPECTED_VIEWS - views

        if missing_views:
            raise AssertionError(
                f"Missing expected views: {sorted(missing_views)}"
            )

        daily = connection.execute(
            """
            SELECT
                COUNT(*),
                COUNT(DISTINCT Well_ID),
                SUM(Potential_Oil_bbl),
                SUM(Actual_Oil_bbl),
                SUM(Deferred_Oil_bbl),
                SUM(Potential_Oil_bbl)
                    - SUM(Actual_Oil_bbl)
                    - SUM(Deferred_Oil_bbl)
            FROM vw_Production_Daily;
            """
        ).fetchone()

        (
            daily_rows,
            daily_wells,
            potential_oil,
            actual_oil,
            deferred_oil,
            reconciliation,
        ) = daily

        well_summary = connection.execute(
            """
            SELECT
                COUNT(*),
                COUNT(DISTINCT Well_ID),
                SUM(Potential_Oil_bbl),
                SUM(Actual_Oil_bbl),
                SUM(Deferred_Oil_bbl)
            FROM vw_Well_Production_Summary;
            """
        ).fetchone()

        (
            well_rows,
            well_count,
            well_potential,
            well_actual,
            well_deferred,
        ) = well_summary

        annual = connection.execute(
            """
            SELECT
                MIN(Production_Year),
                MAX(Production_Year),
                COUNT(*)
            FROM vw_Production_Annual;
            """
        ).fetchone()

        min_year, max_year, annual_rows = annual

        tolerance = 0.01

        checks = [
            ("Expected views", not missing_views),
            ("Daily rows", daily_rows == 32250),
            ("Daily producer wells", daily_wells == 24),
            (
                "Daily production reconciliation",
                abs(reconciliation) <= tolerance,
            ),
            ("Well summary rows", well_rows == 24),
            ("Well summary wells", well_count == 24),
            ("Annual first year", min_year == "2023"),
            ("Annual last year", max_year == "2026"),
            ("Annual row count", annual_rows == 4),
        ]

        print("=" * 72)
        print("PHASE 5C.1 — PRODUCTION ANALYTICS SQL QA")
        print("=" * 72)
        print()

        for name, passed in checks:
            print(
                f"{name:<40} | "
                f"{'PASS' if passed else 'FAIL'}"
            )

        print()
        print("-" * 72)

        print(f"Daily rows              : {daily_rows}")
        print(f"Daily producer wells    : {daily_wells}")
        print(f"Potential Oil           : {potential_oil:.2f}")
        print(f"Actual Oil              : {actual_oil:.2f}")
        print(f"Deferred Oil            : {deferred_oil:.2f}")
        print(f"Reconciliation         : {reconciliation:.10f}")
        print()
        print(f"Well summary rows       : {well_rows}")
        print(f"Well summary wells     : {well_count}")
        print()
        print(f"Annual periods          : {min_year}–{max_year}")
        print(f"Annual rows             : {annual_rows}")

        failed = [name for name, passed in checks if not passed]

        print()
        print("-" * 72)

        if failed:
            print("PHASE 5C.1 QA STATUS: FAIL")
            print(f"Failed checks: {failed}")
            raise SystemExit(1)

        print("PHASE 5C.1 QA STATUS: PASS")


if __name__ == "__main__":
    validate_phase_5c1()