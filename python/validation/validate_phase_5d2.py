from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "offshore_production_asset_performance.db"
)


def check_unique(connection, query):
    return connection.execute(query).fetchone()[0] == 0


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    results = []

    with sqlite3.connect(DATABASE_PATH) as connection:

               # ================================================================
        # PRODUCTION GRAIN
        # ================================================================

        # QA-01 — Daily production: Date × Well
        qa01 = check_unique(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Date, Well_ID
                FROM vw_Production_Daily
                GROUP BY Date, Well_ID
                HAVING COUNT(*) > 1
            )
            """
        )
        results.append(
            ("QA-01 Production daily grain", qa01)
        )

        # QA-02 — Monthly production: Month
        qa02 = check_unique(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Production_Month
                FROM vw_Production_Monthly
                GROUP BY Production_Month
                HAVING COUNT(*) > 1
            )
            """
        )
        results.append(
            ("QA-02 Production monthly grain", qa02)
        )

        # QA-03 — Annual production: Year
        qa03 = check_unique(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Production_Year
                FROM vw_Production_Annual
                GROUP BY Production_Year
                HAVING COUNT(*) > 1
            )
            """
        )
        results.append(
            ("QA-03 Production annual grain", qa03)
        )

        # QA-04 — Well production: Well
        qa04 = check_unique(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Well_ID
                FROM vw_Well_Production_Summary
                GROUP BY Well_ID
                HAVING COUNT(*) > 1
            )
            """
        )
        results.append(
            ("QA-04 Well production summary grain", qa04)
        )

        # QA-05 — Field production: Field
        qa05 = check_unique(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Field_ID
                FROM vw_Field_Production_Summary
                GROUP BY Field_ID
                HAVING COUNT(*) > 1
            )
            """
        )
        results.append(
            ("QA-05 Field production summary grain", qa05)
        )

        # ================================================================
        # RELIABILITY GRAIN
        # ================================================================

        qa06 = check_unique(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Downtime_ID
                FROM vw_Downtime_Summary
                GROUP BY Downtime_ID
                HAVING COUNT(*) > 1
            )
            """
        )
        results.append(
            ("QA-06 Downtime event grain", qa06)
        )

        qa07 = check_unique(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Failure_Cause_ID
                FROM vw_Failure_Cause_Analysis
                GROUP BY Failure_Cause_ID
                HAVING COUNT(*) > 1
            )
            """
        )
        results.append(
            ("QA-07 Failure cause grain", qa07)
        )

        qa08 = check_unique(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Well_ID
                FROM vw_Well_Reliability_Summary
                GROUP BY Well_ID
                HAVING COUNT(*) > 1
            )
            """
        )
        results.append(
            ("QA-08 Well reliability grain", qa08)
        )

        # ================================================================
        # ECONOMICS GRAIN
        # ================================================================

        qa09 = check_unique(
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
        results.append(
            ("QA-09 Economics daily grain", qa09)
        )

        qa10 = check_unique(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Well_ID, Scenario_ID
                FROM vw_Economics_Well_Summary
                GROUP BY Well_ID, Scenario_ID
                HAVING COUNT(*) > 1
            )
            """
        )
        results.append(
            ("QA-10 Economics well grain", qa10)
        )

        qa11 = check_unique(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Field_ID, Scenario_ID
                FROM vw_Economics_Field_Summary
                GROUP BY Field_ID, Scenario_ID
                HAVING COUNT(*) > 1
            )
            """
        )
        results.append(
            ("QA-11 Economics field grain", qa11)
        )

        qa12 = check_unique(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Scenario_ID
                FROM vw_Economics_Scenario_Summary
                GROUP BY Scenario_ID
                HAVING COUNT(*) > 1
            )
            """
        )
        results.append(
            ("QA-12 Economics scenario grain", qa12)
        )

        qa13 = check_unique(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Year, Scenario_ID
                FROM vw_Economics_Annual_Summary
                GROUP BY Year, Scenario_ID
                HAVING COUNT(*) > 1
            )
            """
        )
        results.append(
            ("QA-13 Economics annual grain", qa13)
        )

        # ================================================================
        # INTERVENTION GRAIN
        # ================================================================

        qa14 = check_unique(
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
        results.append(
            ("QA-14 Intervention event grain", qa14)
        )

        qa15 = check_unique(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Well_ID
                FROM vw_Intervention_Well_Summary
                GROUP BY Well_ID
                HAVING COUNT(*) > 1
            )
            """
        )
        results.append(
            ("QA-15 Intervention well grain", qa15)
        )

        qa16 = check_unique(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Intervention_Type_ID
                FROM vw_Intervention_Type_Summary
                GROUP BY Intervention_Type_ID
                HAVING COUNT(*) > 1
            )
            """
        )
        results.append(
            ("QA-16 Intervention type grain", qa16)
        )

        qa17 = check_unique(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT Year
                FROM vw_Intervention_Annual_Summary
                GROUP BY Year
                HAVING COUNT(*) > 1
            )
            """
        )
        results.append(
            ("QA-17 Intervention annual grain", qa17)
        )

        # ================================================================
        # BUSINESS RULES
        # ================================================================

        # QA-18 — Economics daily must contain exactly 3 scenarios
        qa18 = connection.execute(
            """
            SELECT
                COUNT(DISTINCT Scenario_ID) = 3
            FROM vw_Economics_Daily
            """
        ).fetchone()[0] == 1

        results.append(
            ("QA-18 Economics scenario completeness", qa18)
        )

        # QA-19 — Physical production must be identical across scenarios
        qa19 = connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT
                    Date,
                    Well_ID,
                    MAX(Potential_Oil_bbl) - MIN(Potential_Oil_bbl)
                        AS Potential_Diff,
                    MAX(Actual_Oil_bbl) - MIN(Actual_Oil_bbl)
                        AS Actual_Diff,
                    MAX(Deferred_Oil_bbl) - MIN(Deferred_Oil_bbl)
                        AS Deferred_Diff
                FROM vw_Economics_Daily
                GROUP BY Date, Well_ID
                HAVING
                    ABS(Potential_Diff) > 0.000001
                    OR ABS(Actual_Diff) > 0.000001
                    OR ABS(Deferred_Diff) > 0.000001
            )
            """
        ).fetchone()[0] == 0

        results.append(
            ("QA-19 Scenario physical independence", qa19)
        )

        # QA-20 — Economics valuation must equal physical volume × price
        qa20 = connection.execute(
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
            """
        ).fetchone()[0] == 0

        results.append(
            ("QA-20 Economics valuation rule", qa20)
        )

        # QA-21 — Production impact reconciliation
        qa21 = connection.execute(
            """
            SELECT COUNT(*)
            FROM vw_Production_Daily
            WHERE
                ABS(
                    Deferred_Oil_bbl
                    - (Potential_Oil_bbl - Actual_Oil_bbl)
                ) > 0.01
            """
        ).fetchone()[0] == 0

        results.append(
            ("QA-21 Production impact reconciliation", qa21)
        )

        # QA-22 — Cancelled interventions must not be marked completed
        qa22 = connection.execute(
            """
            SELECT COUNT(*)
            FROM vw_Intervention_Economics
            WHERE
                Status = 'Cancelled'
                AND Completed_Flag <> 0
            """
        ).fetchone()[0] == 0

        results.append(
            ("QA-22 Intervention status logic", qa22)
        )

        # QA-23 — Completed interventions must have completed flag
        qa23 = connection.execute(
            """
            SELECT COUNT(*)
            FROM vw_Intervention_Economics
            WHERE
                Status = 'Completed'
                AND Completed_Flag <> 1
            """
        ).fetchone()[0] == 0

        results.append(
            ("QA-23 Completed intervention logic", qa23)
        )

        # QA-24 — Downtime production-impact flag must use Yes/No semantics
        qa24 = connection.execute(
            """
            SELECT COUNT(*)
            FROM vw_Downtime_Summary
            WHERE Production_Affected NOT IN ('Yes', 'No')
            """
        ).fetchone()[0] == 0

        results.append(
            ("QA-24 Downtime impact flag logic", qa24)
        )

        # QA-25 — Intervention event grain must preserve event-level cost
        qa25 = connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT
                    Intervention_ID,
                    COUNT(*) AS Row_Count
                FROM vw_Intervention_Economics
                GROUP BY Intervention_ID
                HAVING COUNT(*) <> 1
            )
            """
        ).fetchone()[0] == 0

        results.append(
            ("QA-25 Intervention cost grain", qa25)
        )

    # ================================================================
    # REPORT
    # ================================================================

    print("=" * 72)
    print("PHASE 5D.2 — ANALYTICAL GRAIN & BUSINESS-RULE QA")
    print("=" * 72)
    print()

    passed = 0
    failed = 0

    for name, status in results:
        print(
            f"{name:<52} | "
            f"{'PASS' if status else 'FAIL'}"
        )

        if status:
            passed += 1
        else:
            failed += 1

    print()
    print("-" * 72)
    print(f"TOTAL CHECKS : {len(results)}")
    print(f"PASSED       : {passed}")
    print(f"FAILED       : {failed}")
    print("-" * 72)

    if failed == 0:
        print("PHASE 5D.2 SQL QA STATUS: PASS")
    else:
        print("PHASE 5D.2 SQL QA STATUS: FAIL")
        raise SystemExit(1)


if __name__ == "__main__":
    main()