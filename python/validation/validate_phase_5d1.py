from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "offshore_production_asset_performance.db"
)


TOLERANCE_BBL = 0.01
TOLERANCE_USD = 0.01


def fetch_value(connection, sql, params=()):
    row = connection.execute(sql, params).fetchone()
    return row[0] if row else None


def check_equal(actual, expected, tolerance=0.0):
    if actual is None or expected is None:
        return False

    if tolerance > 0:
        return abs(actual - expected) <= tolerance

    return actual == expected


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    checks = []

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")

        # ================================================================
        # SOURCE BASELINES
        # ================================================================

        source_production = connection.execute(
            """
            SELECT
                COUNT(*) AS rows,
                COUNT(DISTINCT Well_ID) AS wells,
                SUM(Potential_Oil_bbl) AS potential_oil,
                SUM(Actual_Oil_bbl) AS actual_oil,
                SUM(Deferred_Oil_bbl) AS deferred_oil
            FROM Fact_Production_Impact_Daily;
            """
        ).fetchone()

        (
            source_production_rows,
            source_production_wells,
            source_potential_oil,
            source_actual_oil,
            source_deferred_oil,
        ) = source_production

        source_downtime = connection.execute(
            """
            SELECT
                COUNT(*) AS events,
                COUNT(DISTINCT Well_ID) AS wells,
                SUM(Duration_hr) AS downtime_hours,
                SUM(
                    CASE
                        WHEN Production_Affected = 'Yes'
                        THEN 1
                        ELSE 0
                    END
                ) AS affected_events
            FROM Fact_Downtime_Event;
            """
        ).fetchone()

        (
            source_downtime_events,
            source_downtime_wells,
            source_downtime_hours,
            source_affected_events,
        ) = source_downtime

        source_intervention = connection.execute(
            """
            SELECT
                COUNT(*) AS events,
                COUNT(DISTINCT Well_ID) AS wells,
                COUNT(DISTINCT Intervention_Type_ID) AS types,
                SUM(Duration_Days) AS duration_days,
                SUM(Intervention_Cost_USD) AS total_cost,
                SUM(
                    CASE
                        WHEN Status = 'Completed'
                        THEN 1
                        ELSE 0
                    END
                ) AS completed_events,
                SUM(
                    CASE
                        WHEN Status = 'Cancelled'
                        THEN 1
                        ELSE 0
                    END
                ) AS cancelled_events
            FROM Fact_Intervention_Event;
            """
        ).fetchone()

        (
            source_intervention_events,
            source_intervention_wells,
            source_intervention_types,
            source_intervention_days,
            source_intervention_cost,
            source_completed_events,
            source_cancelled_events,
        ) = source_intervention

        # ================================================================
        # QA-01 — PRODUCTION DAILY ROW RECONCILIATION
        # ================================================================

        production_daily_rows = fetch_value(
            connection,
            """
            SELECT COUNT(*)
            FROM vw_Production_Daily;
            """
        )

        checks.append(
            (
                "QA-01 Production daily row reconciliation",
                check_equal(
                    production_daily_rows,
                    source_production_rows,
                ),
            )
        )

        # ================================================================
        # QA-02 — PRODUCTION VOLUME RECONCILIATION
        # ================================================================

        production_daily = connection.execute(
            """
            SELECT
                SUM(Potential_Oil_bbl),
                SUM(Actual_Oil_bbl),
                SUM(Deferred_Oil_bbl)
            FROM vw_Production_Daily;
            """
        ).fetchone()

        checks.append(
            (
                "QA-02 Production volume reconciliation",
                all(
                    check_equal(
                        actual,
                        expected,
                        TOLERANCE_BBL,
                    )
                    for actual, expected in zip(
                        production_daily,
                        (
                            source_potential_oil,
                            source_actual_oil,
                            source_deferred_oil,
                        ),
                    )
                ),
            )
        )

        # ================================================================
        # QA-03 — WELL PRODUCTION SUMMARY
        # ================================================================

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

        checks.append(
            (
                "QA-03 Well production summary reconciliation",
                (
                    well_summary[0] == source_production_wells
                    and well_summary[1] == source_production_wells
                    and check_equal(
                        well_summary[2],
                        source_potential_oil,
                        TOLERANCE_BBL,
                    )
                    and check_equal(
                        well_summary[3],
                        source_actual_oil,
                        TOLERANCE_BBL,
                    )
                    and check_equal(
                        well_summary[4],
                        source_deferred_oil,
                        TOLERANCE_BBL,
                    )
                ),
            )
        )

        # ================================================================
        # QA-04 — FIELD PRODUCTION SUMMARY
        # ================================================================

        field_summary = connection.execute(
            """
            SELECT
                SUM(Potential_Oil_bbl),
                SUM(Actual_Oil_bbl),
                SUM(Deferred_Oil_bbl)
            FROM vw_Field_Production_Summary;
            """
        ).fetchone()

        checks.append(
            (
                "QA-04 Field production summary reconciliation",
                all(
                    check_equal(
                        actual,
                        expected,
                        TOLERANCE_BBL,
                    )
                    for actual, expected in zip(
                        field_summary,
                        (
                            source_potential_oil,
                            source_actual_oil,
                            source_deferred_oil,
                        ),
                    )
                ),
            )
        )

        # ================================================================
        # QA-05 — DOWNTIME EVENT RECONCILIATION
        # ================================================================

        downtime_summary = connection.execute(
            """
         SELECT
            COUNT(*),
            COUNT(DISTINCT Well_ID),
            SUM(Duration_hr),
            SUM(
               CASE
                   WHEN Production_Affected = 'Yes' THEN 1
                   ELSE 0
               END
               )
          FROM vw_Downtime_Summary
            """
        ).fetchone()

        checks.append(
            (
                "QA-05 Downtime event reconciliation",
                (
                    downtime_summary[0] == source_downtime_events
                    and downtime_summary[1] == source_downtime_wells
                    and check_equal(
                        downtime_summary[2],
                        source_downtime_hours,
                        0.01,
                    )
                    and downtime_summary[3] == source_affected_events
                ),
            )
        )

        # ================================================================
        # QA-06 — FAILURE CAUSE RECONCILIATION
        # ================================================================

        failure_summary = connection.execute(
            """
            SELECT
                SUM(Downtime_Event_Count),
                SUM(Downtime_Hours),
                SUM(Production_Affected_Events)
            FROM vw_Failure_Cause_Analysis;
            """
        ).fetchone()

        checks.append(
            (
                "QA-06 Failure cause reconciliation",
                (
                    failure_summary[0] == source_downtime_events
                    and check_equal(
                        failure_summary[1],
                        source_downtime_hours,
                        0.01,
                    )
                    and failure_summary[2] == source_affected_events
                ),
            )
        )

        # ================================================================
        # QA-07 — WELL RELIABILITY RECONCILIATION
        # ================================================================

        well_reliability = connection.execute(
            """
            SELECT
                COUNT(*),
                SUM(Downtime_Event_Count),
                SUM(Downtime_Hours),
                SUM(Production_Affected_Events)
            FROM vw_Well_Reliability_Summary;
            """
        ).fetchone()

        checks.append(
            (
                "QA-07 Well reliability reconciliation",
                (
                    well_reliability[0] == source_downtime_wells
                    and well_reliability[1] == source_downtime_events
                    and check_equal(
                        well_reliability[2],
                        source_downtime_hours,
                        0.01,
                    )
                    and well_reliability[3] == source_affected_events
                ),
            )
        )

        # ================================================================
        # QA-08 — INTERVENTION EVENT RECONCILIATION
        # ================================================================

        intervention_view = connection.execute(
            """
            SELECT
                COUNT(*),
                COUNT(DISTINCT Well_ID),
                COUNT(DISTINCT Intervention_Type_ID),
                SUM(Duration_Days),
                SUM(Intervention_Cost_USD),
                SUM(Completed_Flag),
                SUM(Cancelled_Flag)
            FROM vw_Intervention_Economics;
            """
        ).fetchone()

        checks.append(
            (
                "QA-08 Intervention event reconciliation",
                (
                    intervention_view[0] == source_intervention_events
                    and intervention_view[1] == source_intervention_wells
                    and intervention_view[2] == source_intervention_types
                    and intervention_view[3] == source_intervention_days
                    and check_equal(
                        intervention_view[4],
                        source_intervention_cost,
                        TOLERANCE_USD,
                    )
                    and intervention_view[5] == source_completed_events
                    and intervention_view[6] == source_cancelled_events
                ),
            )
        )

        # ================================================================
        # QA-09 — INTERVENTION TYPE RECONCILIATION
        # ================================================================

        intervention_type = connection.execute(
            """
            SELECT
                SUM(Intervention_Count),
                SUM(Total_Intervention_Days),
                SUM(Total_Intervention_Cost_USD),
                SUM(Completed_Interventions),
                SUM(Cancelled_Interventions)
            FROM vw_Intervention_Type_Summary;
            """
        ).fetchone()

        checks.append(
            (
                "QA-09 Intervention type reconciliation",
                (
                    intervention_type[0] == source_intervention_events
                    and intervention_type[1] == source_intervention_days
                    and check_equal(
                        intervention_type[2],
                        source_intervention_cost,
                        TOLERANCE_USD,
                    )
                    and intervention_type[3] == source_completed_events
                    and intervention_type[4] == source_cancelled_events
                ),
            )
        )

        # ================================================================
        # QA-10 — INTERVENTION ANNUAL RECONCILIATION
        # ================================================================

        intervention_annual = connection.execute(
            """
            SELECT
                SUM(Intervention_Count),
                SUM(Total_Intervention_Days),
                SUM(Total_Intervention_Cost_USD),
                SUM(Completed_Interventions),
                SUM(Cancelled_Interventions)
            FROM vw_Intervention_Annual_Summary;
            """
        ).fetchone()

        checks.append(
            (
                "QA-10 Intervention annual reconciliation",
                (
                    intervention_annual[0] == source_intervention_events
                    and intervention_annual[1] == source_intervention_days
                    and check_equal(
                        intervention_annual[2],
                        source_intervention_cost,
                        TOLERANCE_USD,
                    )
                    and intervention_annual[3] == source_completed_events
                    and intervention_annual[4] == source_cancelled_events
                ),
            )
        )

        # ================================================================
        # QA-11 — ECONOMICS DAILY PHYSICAL RECONCILIATION
        # ================================================================

        scenario_count = fetch_value(
            connection,
            """
            SELECT COUNT(*)
            FROM Dim_Scenario;
            """
        )

        economics_daily = connection.execute(
            """
            SELECT
                COUNT(*),
                SUM(Potential_Oil_bbl),
                SUM(Actual_Oil_bbl),
                SUM(Deferred_Oil_bbl)
            FROM vw_Economics_Daily;
            """
        ).fetchone()

        expected_economics_rows = (
            source_production_rows * scenario_count
        )

        checks.append(
            (
                "QA-11 Economics daily physical reconciliation",
                (
                    economics_daily[0] == expected_economics_rows
                    and check_equal(
                        economics_daily[1],
                        source_potential_oil * scenario_count,
                        TOLERANCE_BBL,
                    )
                    and check_equal(
                        economics_daily[2],
                        source_actual_oil * scenario_count,
                        TOLERANCE_BBL,
                    )
                    and check_equal(
                        economics_daily[3],
                        source_deferred_oil * scenario_count,
                        TOLERANCE_BBL,
                    )
                ),
            )
        )

        # ================================================================
        # QA-12 — SCENARIO PHYSICAL INDEPENDENCE
        # ================================================================

        scenario_physical = connection.execute(
            """
            SELECT
                Scenario_ID,
                SUM(Potential_Oil_bbl),
                SUM(Actual_Oil_bbl),
                SUM(Deferred_Oil_bbl)
            FROM vw_Economics_Scenario_Summary
            GROUP BY Scenario_ID
            ORDER BY Scenario_ID;
            """
        ).fetchall()

        scenario_independent = (
            len(scenario_physical) == scenario_count
            and all(
                check_equal(
                    row[1],
                    source_potential_oil,
                    TOLERANCE_BBL,
                )
                and check_equal(
                    row[2],
                    source_actual_oil,
                    TOLERANCE_BBL,
                )
                and check_equal(
                    row[3],
                    source_deferred_oil,
                    TOLERANCE_BBL,
                )
                for row in scenario_physical
            )
        )

        checks.append(
            (
                "QA-12 Scenario physical independence",
                scenario_independent,
            )
        )

        # ================================================================
        # QA-13 — SCENARIO REVENUE CALCULATION
        # ================================================================

        revenue_errors = fetch_value(
            connection,
            """
            SELECT COUNT(*)
            FROM vw_Economics_Daily
            WHERE
                ABS(
                    Potential_Revenue_USD
                    - Potential_Oil_bbl * Oil_Price_USD_bbl
                ) > 0.01
                OR ABS(
                    Actual_Revenue_USD
                    - Actual_Oil_bbl * Oil_Price_USD_bbl
                ) > 0.01
                OR ABS(
                    Deferred_Value_USD
                    - Deferred_Oil_bbl * Oil_Price_USD_bbl
                ) > 0.01
                OR ABS(
                    Production_Impact_Value_USD
                    - Production_Impact_bbl * Oil_Price_USD_bbl
                ) > 0.01;
            """
        )

        checks.append(
            (
                "QA-13 Economics valuation calculation",
                revenue_errors == 0,
            )
        )

        # ================================================================
        # QA-14 — INTERVENTION EVENT GRAIN PRESERVATION
        # ================================================================

        duplicate_interventions = fetch_value(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Intervention_ID
                FROM vw_Intervention_Economics
                GROUP BY Intervention_ID
                HAVING COUNT(*) <> 1
            );
            """
        )

        checks.append(
            (
                "QA-14 Intervention event grain preservation",
                duplicate_interventions == 0,
            )
        )

        # ================================================================
        # QA-15 — ECONOMICS DAILY GRAIN PRESERVATION
        # ================================================================

        duplicate_economics = fetch_value(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT
                    Date,
                    Well_ID,
                    Scenario_ID
                FROM vw_Economics_Daily
                GROUP BY
                    Date,
                    Well_ID,
                    Scenario_ID
                HAVING COUNT(*) <> 1
            );
            """
        )

        checks.append(
            (
                "QA-15 Economics daily grain preservation",
                duplicate_economics == 0,
            )
        )

        # ================================================================
        # OUTPUT
        # ================================================================

        print("=" * 72)
        print("PHASE 5D.1 — CROSS-LAYER SQL RECONCILIATION")
        print("=" * 72)
        print()

        for name, passed in checks:
            status = "PASS" if passed else "FAIL"
            print(f"{name:<52} | {status}")

        print()
        print("-" * 72)
        print(f"TOTAL CHECKS : {len(checks)}")
        print(f"PASSED       : {sum(passed for _, passed in checks)}")
        print(f"FAILED       : {sum(not passed for _, passed in checks)}")
        print("-" * 72)

        if all(passed for _, passed in checks):
            print()
            print("PHASE 5D.1 SQL QA STATUS: PASS")
        else:
            print()
            print("PHASE 5D.1 SQL QA STATUS: FAIL")
            raise SystemExit(1)


if __name__ == "__main__":
    main()