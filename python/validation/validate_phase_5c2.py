from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "offshore_production_asset_performance.db"
)


EXPECTED_VIEWS = {
    "vw_Downtime_Summary",
    "vw_Failure_Cause_Analysis",
    "vw_Well_Reliability_Summary",
}


def validate_phase_5c2() -> None:

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as connection:

        # ---------------------------------------------------------------
        # View existence
        # ---------------------------------------------------------------

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

        # ---------------------------------------------------------------
        # Authoritative downtime fact
        # ---------------------------------------------------------------

        source = connection.execute(
            """
            SELECT
                COUNT(*),
                COUNT(DISTINCT Downtime_ID),
                COUNT(DISTINCT Well_ID),
                SUM(Duration_hr),
                SUM(
                    CASE
                        WHEN Production_Affected = 'Yes' THEN 1
                        ELSE 0
                    END
                )
            FROM Fact_Downtime_Event;
            """
        ).fetchone()

        (
            source_rows,
            source_events,
            source_wells,
            source_hours,
            source_affected_events,
        ) = source

        # ---------------------------------------------------------------
        # Downtime summary reconciliation
        # ---------------------------------------------------------------

        summary = connection.execute(
            """
            SELECT
                COUNT(*),
                COUNT(DISTINCT Downtime_ID),
                COUNT(DISTINCT Well_ID),
                SUM(Duration_hr),
                SUM(
                    CASE
                        WHEN Production_Affected = 'Yes' THEN 1
                        ELSE 0
                    END
                )
            FROM vw_Downtime_Summary;
            """
        ).fetchone()

        (
            summary_rows,
            summary_events,
            summary_wells,
            summary_hours,
            summary_affected_events,
        ) = summary

        # ---------------------------------------------------------------
        # Failure-cause reconciliation
        # ---------------------------------------------------------------

        cause = connection.execute(
            """
            SELECT
                COUNT(*),
                SUM(Downtime_Event_Count),
                SUM(Downtime_Hours),
                SUM(Production_Affected_Events),
                SUM(Planned_Events),
                SUM(Unplanned_Events)
            FROM vw_Failure_Cause_Analysis;
            """
        ).fetchone()

        (
            cause_rows,
            cause_events,
            cause_hours,
            cause_affected_events,
            cause_planned,
            cause_unplanned,
        ) = cause

        # ---------------------------------------------------------------
        # Well reliability reconciliation
        # ---------------------------------------------------------------

        well = connection.execute(
            """
            SELECT
                COUNT(*),
                COUNT(DISTINCT Well_ID),
                SUM(Downtime_Event_Count),
                SUM(Downtime_Hours),
                SUM(Production_Affected_Events),
                SUM(Planned_Events),
                SUM(Unplanned_Events)
            FROM vw_Well_Reliability_Summary;
            """
        ).fetchone()

        (
            well_rows,
            well_count,
            well_events,
            well_hours,
            well_affected_events,
            well_planned,
            well_unplanned,
        ) = well

        # ---------------------------------------------------------------
        # Logical checks
        # ---------------------------------------------------------------

        checks = [
            (
                "Expected reliability views",
                not missing_views,
            ),
            (
                "Downtime event count reconciliation",
                summary_events == source_events,
            ),
            (
                "Downtime hours reconciliation",
                abs(summary_hours - source_hours) <= 0.01,
            ),
            (
                "Production-affected event reconciliation",
                summary_affected_events == source_affected_events,
            ),
            (
                "Failure-cause event reconciliation",
                cause_events == source_events,
            ),
            (
                "Failure-cause hours reconciliation",
                abs(cause_hours - source_hours) <= 0.01,
            ),
            (
                "Failure-cause affected-event reconciliation",
                cause_affected_events == source_affected_events,
            ),
            (
                "Planned/unplanned reconciliation",
                cause_planned + cause_unplanned == source_events,
            ),
            (
                "Well summary row count",
                well_rows == source_wells,
            ),
            (
                "Well event reconciliation",
                well_events == source_events,
            ),
            (
                "Well hours reconciliation",
                abs(well_hours - source_hours) <= 0.01,
            ),
            (
                "Well affected-event reconciliation",
                well_affected_events == source_affected_events,
            ),
            (
                "Well planned/unplanned reconciliation",
                well_planned + well_unplanned == source_events,
            ),
        ]

        failed = [
            name
            for name, passed in checks
            if not passed
        ]

        print("=" * 72)
        print("PHASE 5C.2 — RELIABILITY ANALYTICS SQL QA")
        print("=" * 72)
        print()

        for name, passed in checks:
            print(
                f"{name:<48} | "
                f"{'PASS' if passed else 'FAIL'}"
            )

        print()
        print("-" * 72)

        print(f"Source downtime rows       : {source_rows}")
        print(f"Source downtime events     : {source_events}")
        print(f"Source wells               : {source_wells}")
        print(f"Source downtime hours      : {source_hours:.2f}")
        print(
            "Source affected events     : "
            f"{source_affected_events}"
        )

        print()
        print(f"Failure-cause rows         : {cause_rows}")
        print(f"Well reliability rows      : {well_rows}")

        print()
        print("-" * 72)

        if failed:
            print("PHASE 5C.2 QA STATUS: FAIL")
            print(f"Failed checks: {failed}")
            raise SystemExit(1)

        print("PHASE 5C.2 QA STATUS: PASS")


if __name__ == "__main__":
    validate_phase_5c2()