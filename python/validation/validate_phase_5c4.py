from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "offshore_production_asset_performance.db"
)

EXPECTED_VIEWS = {
    "vw_Intervention_Economics",
    "vw_Intervention_Well_Summary",
    "vw_Intervention_Type_Summary",
    "vw_Intervention_Annual_Summary",
}

EXPECTED_EVENT_COUNT = 39
EXPECTED_WELL_COUNT = 20
EXPECTED_TYPE_COUNT = 6
EXPECTED_YEAR_COUNT = 4

EXPECTED_COMPLETED = 36
EXPECTED_CANCELLED = 3

TOLERANCE_USD = 0.01
TOLERANCE_DAYS = 0.000001


def assert_close(actual, expected, tolerance, label):
    difference = abs(actual - expected)

    if difference > tolerance:
        raise AssertionError(
            f"{label} failed: "
            f"actual={actual}, expected={expected}, "
            f"difference={difference}"
        )


def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as connection:

        # ---------------------------------------------------------------
        # QA-01 — Expected intervention economics views
        # ---------------------------------------------------------------
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'view'
              AND name LIKE 'vw_Intervention_%'
            ORDER BY name;
            """
        ).fetchall()

        actual_views = {row[0] for row in rows}

        if actual_views != EXPECTED_VIEWS:
            raise AssertionError(
                "Unexpected intervention economics views.\n"
                f"Expected: {sorted(EXPECTED_VIEWS)}\n"
                f"Actual:   {sorted(actual_views)}"
            )

        print("QA-01 Expected intervention views             | PASS")

        # ---------------------------------------------------------------
        # QA-02 — Event count reconciliation
        # ---------------------------------------------------------------
        source_events = connection.execute(
            """
            SELECT COUNT(*)
            FROM Fact_Intervention_Event;
            """
        ).fetchone()[0]

        view_events = connection.execute(
            """
            SELECT COUNT(*)
            FROM vw_Intervention_Economics;
            """
        ).fetchone()[0]

        if source_events != EXPECTED_EVENT_COUNT:
            raise AssertionError(
                f"Expected {EXPECTED_EVENT_COUNT} source events, "
                f"got {source_events}"
            )

        if view_events != source_events:
            raise AssertionError(
                f"Event reconciliation failed: "
                f"source={source_events}, view={view_events}"
            )

        print("QA-02 Event count reconciliation              | PASS")

        # ---------------------------------------------------------------
        # QA-03 — Status reconciliation
        # ---------------------------------------------------------------
        source_status = dict(
            connection.execute(
                """
                SELECT Status, COUNT(*)
                FROM Fact_Intervention_Event
                GROUP BY Status;
                """
            ).fetchall()
        )

        view_status = dict(
            connection.execute(
                """
                SELECT Status, COUNT(*)
                FROM vw_Intervention_Economics
                GROUP BY Status;
                """
            ).fetchall()
        )

        if source_status != view_status:
            raise AssertionError(
                f"Status reconciliation failed: "
                f"source={source_status}, view={view_status}"
            )

        if source_status.get("Completed", 0) != EXPECTED_COMPLETED:
            raise AssertionError("Completed intervention count mismatch")

        if source_status.get("Cancelled", 0) != EXPECTED_CANCELLED:
            raise AssertionError("Cancelled intervention count mismatch")

        print("QA-03 Status reconciliation                   | PASS")

        # ---------------------------------------------------------------
        # QA-04 — Cost reconciliation
        # ---------------------------------------------------------------
        source_cost = connection.execute(
            """
            SELECT SUM(Intervention_Cost_USD)
            FROM Fact_Intervention_Event;
            """
        ).fetchone()[0]

        view_cost = connection.execute(
            """
            SELECT SUM(Intervention_Cost_USD)
            FROM vw_Intervention_Economics;
            """
        ).fetchone()[0]

        assert_close(
            view_cost,
            source_cost,
            TOLERANCE_USD,
            "Total intervention cost"
        )

        print("QA-04 Intervention cost reconciliation        | PASS")

        # ---------------------------------------------------------------
        # QA-05 — Duration reconciliation
        # ---------------------------------------------------------------
        source_days = connection.execute(
            """
            SELECT SUM(Duration_Days)
            FROM Fact_Intervention_Event;
            """
        ).fetchone()[0]

        view_days = connection.execute(
            """
            SELECT SUM(Duration_Days)
            FROM vw_Intervention_Economics;
            """
        ).fetchone()[0]

        assert_close(
            view_days,
            source_days,
            TOLERANCE_DAYS,
            "Total intervention duration"
        )

        print("QA-05 Duration reconciliation                 | PASS")

        # ---------------------------------------------------------------
        # QA-06 — Well summary reconciliation
        # ---------------------------------------------------------------
        source_wells = connection.execute(
            """
            SELECT COUNT(DISTINCT Well_ID)
            FROM Fact_Intervention_Event;
            """
        ).fetchone()[0]

        summary_wells = connection.execute(
            """
            SELECT COUNT(*)
            FROM vw_Intervention_Well_Summary;
            """
        ).fetchone()[0]

        if source_wells != EXPECTED_WELL_COUNT:
            raise AssertionError(
                f"Expected {EXPECTED_WELL_COUNT} intervention wells, "
                f"got {source_wells}"
            )

        if summary_wells != source_wells:
            raise AssertionError(
                f"Well summary reconciliation failed: "
                f"source={source_wells}, summary={summary_wells}"
            )

        print("QA-06 Well summary reconciliation            | PASS")

        # ---------------------------------------------------------------
        # QA-07 — Intervention type reconciliation
        # ---------------------------------------------------------------
        source_types = connection.execute(
            """
            SELECT COUNT(DISTINCT Intervention_Type_ID)
            FROM Fact_Intervention_Event;
            """
        ).fetchone()[0]

        summary_types = connection.execute(
            """
            SELECT COUNT(*)
            FROM vw_Intervention_Type_Summary;
            """
        ).fetchone()[0]

        if source_types != EXPECTED_TYPE_COUNT:
            raise AssertionError(
                f"Expected {EXPECTED_TYPE_COUNT} intervention types, "
                f"got {source_types}"
            )

        if summary_types != source_types:
            raise AssertionError(
                f"Intervention type reconciliation failed: "
                f"source={source_types}, summary={summary_types}"
            )

        print("QA-07 Intervention type reconciliation       | PASS")

        # ---------------------------------------------------------------
        # QA-08 — Annual summary reconciliation
        # ---------------------------------------------------------------
        source_years = connection.execute(
            """
            SELECT COUNT(DISTINCT strftime('%Y', Start_Date))
            FROM Fact_Intervention_Event;
            """
        ).fetchone()[0]

        summary_years = connection.execute(
            """
            SELECT COUNT(*)
            FROM vw_Intervention_Annual_Summary;
            """
        ).fetchone()[0]

        if source_years != EXPECTED_YEAR_COUNT:
            raise AssertionError(
                f"Expected {EXPECTED_YEAR_COUNT} years, "
                f"got {source_years}"
            )

        if summary_years != source_years:
            raise AssertionError(
                f"Annual summary reconciliation failed: "
                f"source={source_years}, summary={summary_years}"
            )

        print("QA-08 Annual summary reconciliation          | PASS")

        # ---------------------------------------------------------------
        # QA-09 — Intervention type totals
        # ---------------------------------------------------------------
        source_type_totals = connection.execute(
            """
            SELECT
                Intervention_Type_ID,
                COUNT(*),
                SUM(Duration_Days),
                SUM(Intervention_Cost_USD)
            FROM Fact_Intervention_Event
            GROUP BY Intervention_Type_ID
            ORDER BY Intervention_Type_ID;
            """
        ).fetchall()

        view_type_totals = connection.execute(
            """
            SELECT
                Intervention_Type_ID,
                Intervention_Count,
                Total_Intervention_Days,
                Total_Intervention_Cost_USD
            FROM vw_Intervention_Type_Summary
            ORDER BY Intervention_Type_ID;
            """
        ).fetchall()

        if len(source_type_totals) != len(view_type_totals):
            raise AssertionError(
                "Intervention type row-count mismatch"
            )

        for source, view in zip(source_type_totals, view_type_totals):
            if source[0] != view[0]:
                raise AssertionError(
                    f"Intervention type mismatch: "
                    f"{source[0]} vs {view[0]}"
                )

            if source[1] != view[1]:
                raise AssertionError(
                    f"{source[0]} event count mismatch"
                )

            assert_close(
                view[2],
                source[2],
                TOLERANCE_DAYS,
                f"{source[0]} duration"
            )

            assert_close(
                view[3],
                source[3],
                TOLERANCE_USD,
                f"{source[0]} cost"
            )

        print("QA-09 Intervention type totals                | PASS")

        # ---------------------------------------------------------------
        # QA-10 — Derived metric calculations
        # ---------------------------------------------------------------
        derived_check = connection.execute(
            """
            SELECT
                MAX(
                    ABS(
                        Cost_per_Intervention_Day_USD
                        - CASE
                            WHEN Duration_Days > 0
                            THEN Intervention_Cost_USD / Duration_Days
                            ELSE NULL
                          END
                    )
                ),
                MAX(
                    ABS(
                        Cost_per_Expected_bopd_USD
                        - CASE
                            WHEN Expected_Oil_Rate_bopd > 0
                            THEN Intervention_Cost_USD
                                 / Expected_Oil_Rate_bopd
                            ELSE NULL
                          END
                    )
                )
            FROM vw_Intervention_Economics;
            """
        ).fetchone()

        if any(
            value is not None and value > TOLERANCE_USD
            for value in derived_check
        ):
            raise AssertionError(
                f"Derived metric calculation error: {derived_check}"
            )

        print("QA-10 Derived metric calculations            | PASS")

        # ---------------------------------------------------------------
        # QA-11 — Required field NULL validation
        # ---------------------------------------------------------------
        null_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM vw_Intervention_Economics
            WHERE Intervention_ID IS NULL
               OR Well_ID IS NULL
               OR Intervention_Type_ID IS NULL
               OR Start_Date IS NULL
               OR End_Date IS NULL
               OR Duration_Days IS NULL
               OR Intervention_Cost_USD IS NULL
               OR Status IS NULL;
            """
        ).fetchone()[0]

        if null_count != 0:
            raise AssertionError(
                f"Required intervention fields contain "
                f"{null_count} NULL rows"
            )

        print("QA-11 Required field NULL validation          | PASS")

        # ---------------------------------------------------------------
        # QA-12 — Event grain preservation
        # ---------------------------------------------------------------
        duplicate_events = connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT Intervention_ID
                FROM vw_Intervention_Economics
                GROUP BY Intervention_ID
                HAVING COUNT(*) > 1
            );
            """
        ).fetchone()[0]

        if duplicate_events != 0:
            raise AssertionError(
                f"Duplicate intervention events detected: "
                f"{duplicate_events}"
            )

        print("QA-12 Event grain preservation                | PASS")

        # ---------------------------------------------------------------
        # Summary metrics
        # ---------------------------------------------------------------
        completed = connection.execute(
            """
            SELECT
                COUNT(*),
                SUM(Duration_Days),
                SUM(Intervention_Cost_USD)
            FROM vw_Intervention_Economics
            WHERE Status = 'Completed';
            """
        ).fetchone()

        cancelled = connection.execute(
            """
            SELECT
                COUNT(*),
                SUM(Duration_Days),
                SUM(Intervention_Cost_USD)
            FROM vw_Intervention_Economics
            WHERE Status = 'Cancelled';
            """
        ).fetchone()

        total = connection.execute(
            """
            SELECT
                COUNT(*),
                SUM(Duration_Days),
                SUM(Intervention_Cost_USD)
            FROM vw_Intervention_Economics;
            """
        ).fetchone()

    print()
    print("Intervention events       :", total[0])
    print("Intervention wells       :", source_wells)
    print("Intervention types       :", source_types)
    print("Completed events         :", completed[0])
    print("Completed days           :", completed[1])
    print("Completed cost           :", round(completed[2], 2))
    print("Cancelled events         :", cancelled[0])
    print("Cancelled days           :", cancelled[1])
    print("Cancelled cost           :", round(cancelled[2], 2))
    print("Total intervention days  :", total[1])
    print("Total intervention cost  :", round(total[2], 2))
    print()
    print("TOTAL CHECKS : 12")
    print("PASSED       : 12")
    print("FAILED       : 0")
    print("PHASE 5C.4 QA STATUS: PASS")


if __name__ == "__main__":
    main()