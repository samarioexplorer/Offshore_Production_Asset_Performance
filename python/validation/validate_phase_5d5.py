from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "offshore_production_asset_performance.db"
)

DOCUMENTATION_FILES = [
    PROJECT_ROOT
    / "documentation"
    / "data_dictionary"
    / "sql_view_inventory.md",
    PROJECT_ROOT
    / "documentation"
    / "methodology"
    / "sql_analytics_methodology.md",
]

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


def fetch_one(connection, sql, params=()):
    return connection.execute(sql, params).fetchone()[0]


def almost_equal(value_a, value_b, tolerance=0.01):
    return abs(float(value_a) - float(value_b)) <= tolerance


def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    passed = 0
    failed = 0

    def check(label, condition):
        nonlocal passed, failed

        status = "PASS" if condition else "FAIL"

        if condition:
            passed += 1
        else:
            failed += 1

        print(f"{label:<55} | {status}")

    with sqlite3.connect(DATABASE_PATH) as connection:

        connection.execute("PRAGMA foreign_keys = ON;")

        # ------------------------------------------------------------------
        # 01 — DATABASE OBJECT INTEGRITY
        # ------------------------------------------------------------------

        view_rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'view'
            """
        ).fetchall()

        actual_views = {row[0] for row in view_rows}

        check(
            "QA-01 All expected analytical views exist",
            set(EXPECTED_VIEWS).issubset(actual_views),
        )

        check(
            "QA-02 Expected analytical view count",
            len(EXPECTED_VIEWS) == 17,
        )

        # ------------------------------------------------------------------
        # 02 — PRODUCTION INTEGRATION
        # ------------------------------------------------------------------

        source_daily_rows = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM Fact_Production_Impact_Daily
            """
        )

        view_daily_rows = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM vw_Production_Daily
            """
        )

        check(
            "QA-03 Production daily row reconciliation",
            source_daily_rows == view_daily_rows,
        )

        source_potential = fetch_one(
            connection,
            """
            SELECT COALESCE(SUM(Potential_Oil_bbl), 0)
            FROM Fact_Production_Impact_Daily
            """
        )

        view_potential = fetch_one(
            connection,
            """
            SELECT COALESCE(SUM(Potential_Oil_bbl), 0)
            FROM vw_Production_Daily
            """
        )

        source_actual = fetch_one(
            connection,
            """
            SELECT COALESCE(SUM(Actual_Oil_bbl), 0)
            FROM Fact_Production_Impact_Daily
            """
        )

        view_actual = fetch_one(
            connection,
            """
            SELECT COALESCE(SUM(Actual_Oil_bbl), 0)
            FROM vw_Production_Daily
            """
        )

        check(
            "QA-04 Production volume reconciliation",
            almost_equal(source_potential, view_potential)
            and almost_equal(source_actual, view_actual),
        )

        monthly_actual = fetch_one(
            connection,
            """
            SELECT COALESCE(SUM(Actual_Oil_bbl), 0)
            FROM vw_Production_Monthly
            """
        )

        annual_actual = fetch_one(
            connection,
            """
            SELECT COALESCE(SUM(Actual_Oil_bbl), 0)
            FROM vw_Production_Annual
            """
        )

        check(
            "QA-05 Monthly-to-annual production reconciliation",
            almost_equal(monthly_actual, annual_actual),
        )

        field_actual = fetch_one(
            connection,
            """
            SELECT COALESCE(SUM(Actual_Oil_bbl), 0)
            FROM vw_Field_Production_Summary
            """
        )

        check(
            "QA-06 Field production reconciliation",
            almost_equal(source_actual, field_actual),
        )

        well_actual = fetch_one(
            connection,
            """
            SELECT COALESCE(SUM(Actual_Oil_bbl), 0)
            FROM vw_Well_Production_Summary
            """
        )

        check(
            "QA-07 Well production reconciliation",
            almost_equal(source_actual, well_actual),
        )

        # ------------------------------------------------------------------
        # 03 — RELIABILITY INTEGRATION
        # ------------------------------------------------------------------

        downtime_events = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM Fact_Downtime_Event
            """
        )

        reliability_events = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM vw_Downtime_Summary
            """
        )

        check(
            "QA-08 Downtime event reconciliation",
            downtime_events == reliability_events,
        )

        downtime_hours = fetch_one(
            connection,
            """
            SELECT COALESCE(SUM(Duration_hr), 0)
            FROM Fact_Downtime_Event
            """
        )

        reliability_hours = fetch_one(
            connection,
            """
            SELECT COALESCE(SUM(Duration_hr), 0)
            FROM vw_Downtime_Summary
            """
        )

        check(
            "QA-09 Downtime hours reconciliation",
            almost_equal(downtime_hours, reliability_hours),
        )

        affected_source = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM Fact_Downtime_Event
            WHERE Production_Affected = 'Yes'
            """
        )

        affected_view = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM vw_Downtime_Summary
            WHERE Production_Affected = 'Yes'
            """
        )

        check(
            "QA-10 Production-affected downtime reconciliation",
            affected_source == affected_view,
        )

        failure_events = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM vw_Failure_Cause_Analysis
            """
        )

        distinct_failure_causes = fetch_one(
            connection,
            """
            SELECT COUNT(DISTINCT Failure_Cause_ID)
            FROM Fact_Downtime_Event
            """
        )

        check(
            "QA-11 Failure-cause coverage",
            failure_events == distinct_failure_causes,
        )

        well_reliability_rows = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM vw_Well_Reliability_Summary
            """
        )

        producer_wells = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM Dim_Well
            WHERE Well_Type = 'Producer'
            """
        )

        check(
            "QA-12 Well reliability coverage",
            well_reliability_rows == producer_wells,
        )

        # ------------------------------------------------------------------
        # 04 — INTERVENTION INTEGRATION
        # ------------------------------------------------------------------

        intervention_events = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM Fact_Intervention_Event
            """
        )

        intervention_view_events = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM vw_Intervention_Economics
            """
        )

        check(
            "QA-13 Intervention event reconciliation",
            intervention_events == intervention_view_events,
        )

        source_intervention_cost = fetch_one(
            connection,
            """
            SELECT COALESCE(SUM(Intervention_Cost_USD), 0)
            FROM Fact_Intervention_Event
            """
        )

        view_intervention_cost = fetch_one(
            connection,
            """
            SELECT COALESCE(SUM(Intervention_Cost_USD), 0)
            FROM vw_Intervention_Economics
            """
        )

        check(
            "QA-14 Intervention cost reconciliation",
            almost_equal(
                source_intervention_cost,
                view_intervention_cost,
            ),
        )

        completed_source = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM Fact_Intervention_Event
            WHERE Status = 'Completed'
            """
        )

        completed_view = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM vw_Intervention_Economics
            WHERE Status = 'Completed'
            """
        )

        cancelled_source = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM Fact_Intervention_Event
            WHERE Status = 'Cancelled'
            """
        )

        cancelled_view = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM vw_Intervention_Economics
            WHERE Status = 'Cancelled'
            """
        )

        check(
            "QA-15 Intervention status reconciliation",
            completed_source == completed_view
            and cancelled_source == cancelled_view,
        )

        type_rows = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM vw_Intervention_Type_Summary
            """
        )

        intervention_types = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM Dim_Intervention
            """
        )

        check(
            "QA-16 Intervention type coverage",
            type_rows == intervention_types,
        )

        annual_intervention_rows = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM vw_Intervention_Annual_Summary
            """
        )

        intervention_years = fetch_one(
            connection,
            """
            SELECT COUNT(DISTINCT strftime('%Y', Start_Date))
            FROM Fact_Intervention_Event
            """
        )

        check(
            "QA-17 Intervention annual coverage",
            annual_intervention_rows == intervention_years,
        )

        # ------------------------------------------------------------------
        # 05 — ECONOMICS INTEGRATION
        # ------------------------------------------------------------------

        scenario_count = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM Dim_Scenario
            """
        )

        check(
            "QA-18 Scenario completeness",
            scenario_count == 3,
        )

        expected_economics_rows = source_daily_rows * scenario_count

        economics_daily_rows = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM vw_Economics_Daily
            """
        )

        check(
            "QA-19 Economics daily row reconciliation",
            economics_daily_rows == expected_economics_rows,
        )

        economics_actual = fetch_one(
            connection,
            """
            SELECT COALESCE(SUM(Actual_Oil_bbl), 0)
            FROM vw_Economics_Daily
            """
        )

        expected_economics_actual = source_actual * scenario_count

        check(
            "QA-20 Economics physical-volume reconciliation",
            almost_equal(
                economics_actual,
                expected_economics_actual,
            ),
        )

        scenario_physical = connection.execute(
            """
            SELECT
                Scenario_ID,
                SUM(Actual_Oil_bbl) AS Actual_Oil_bbl
            FROM vw_Economics_Daily
            GROUP BY Scenario_ID
            ORDER BY Scenario_ID
            """
        ).fetchall()

        scenario_independent = (
            len(scenario_physical) == 3
            and all(
                almost_equal(
                    row[1],
                    scenario_physical[0][1],
                )
                for row in scenario_physical
            )
        )

        check(
            "QA-21 Scenario physical independence",
            scenario_independent,
        )

        # ------------------------------------------------------------------
        # 06 — ECONOMIC VALUATION RULE
        # ------------------------------------------------------------------

        valuation_rows = connection.execute(
            """
            SELECT
                Actual_Oil_bbl,
                Oil_Price_USD_bbl,
                Actual_Revenue_USD
            FROM vw_Economics_Daily
            LIMIT 1000
            """
        ).fetchall()

        valuation_correct = all(
            almost_equal(
                row[2],
                row[0] * row[1],
                tolerance=0.01,
            )
            for row in valuation_rows
        )

        check(
            "QA-22 Economics valuation rule",
            valuation_correct,
        )

        # ------------------------------------------------------------------
        # 07 — ANALYTICAL GRAIN
        # ------------------------------------------------------------------

        duplicate_economics = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Date, Well_ID, Scenario_ID
                FROM vw_Economics_Daily
                GROUP BY Date, Well_ID, Scenario_ID
                HAVING COUNT(*) > 1
            )
            """
        )

        check(
            "QA-23 Economics daily grain uniqueness",
            duplicate_economics == 0,
        )

        duplicate_interventions = fetch_one(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Intervention_ID
                FROM vw_Intervention_Economics
                GROUP BY Intervention_ID
                HAVING COUNT(*) > 1
            )
            """
        )

        check(
            "QA-24 Intervention event grain preservation",
            duplicate_interventions == 0,
        )

        # ------------------------------------------------------------------
        # 08 — PRODUCTION IMPACT RECONCILIATION
        # ------------------------------------------------------------------

        impact_difference = fetch_one(
            connection,
            """
            SELECT
                COALESCE(
                    SUM(Potential_Oil_bbl)
                    - SUM(Actual_Oil_bbl)
                    - SUM(Deferred_Oil_bbl),
                    0
                )
            FROM Fact_Production_Impact_Daily
            """
        )

        check(
            "QA-25 Production impact reconciliation",
            abs(float(impact_difference)) <= 0.01,
        )

        # ------------------------------------------------------------------
        # 09 — INTERVENTION COST GRAIN CONTROL
        # ------------------------------------------------------------------

        source_cost = fetch_one(
            connection,
            """
            SELECT COALESCE(SUM(Intervention_Cost_USD), 0)
            FROM Fact_Intervention_Event
            """
        )

        event_view_cost = fetch_one(
            connection,
            """
            SELECT COALESCE(SUM(Intervention_Cost_USD), 0)
            FROM vw_Intervention_Economics
            """
        )

        check(
            "QA-26 Intervention cost event-grain preservation",
            almost_equal(source_cost, event_view_cost),
        )

        # ------------------------------------------------------------------
        # 10 — DOCUMENTATION
        # ------------------------------------------------------------------

        documentation_complete = all(
            path.exists() and path.stat().st_size > 0
            for path in DOCUMENTATION_FILES
        )

        check(
            "QA-27 SQL documentation completeness",
            documentation_complete,
        )

    # ----------------------------------------------------------------------
    # FINAL SUMMARY
    # ----------------------------------------------------------------------

    print()
    print("-" * 72)
    print(f"TOTAL CHECKS : {passed + failed}")
    print(f"PASSED       : {passed}")
    print(f"FAILED       : {failed}")
    print("-" * 72)

    if failed == 0:
        print()
        print("PHASE 5D.5 SQL QA STATUS: PASS")
        print()
        print("FINAL SQL QUALITY GATE: PASS")
    else:
        print()
        print("PHASE 5D.5 SQL QA STATUS: FAIL")
        print()
        print("FINAL SQL QUALITY GATE: FAIL")
        raise SystemExit(1)


if __name__ == "__main__":
    main()