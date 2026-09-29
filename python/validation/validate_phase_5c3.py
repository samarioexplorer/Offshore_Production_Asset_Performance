from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "offshore_production_asset_performance.db"
)

EXPECTED_VIEWS = {
    "vw_Economics_Annual_Summary",
    "vw_Economics_Daily",
    "vw_Economics_Field_Summary",
    "vw_Economics_Scenario_Summary",
    "vw_Economics_Well_Summary",
}

EXPECTED_SCENARIOS = {
    "S01": ("Low", 60.0),
    "S02": ("Base", 75.0),
    "S03": ("High", 90.0),
}

EXPECTED_DAILY_ROWS = 32250 * 3
EXPECTED_PRODUCER_WELLS = 24

TOLERANCE_BBL = 0.01
TOLERANCE_USD = 0.01


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
        # QA-01 — Expected economics views
        # ---------------------------------------------------------------
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'view'
              AND name LIKE 'vw_Economics_%'
            ORDER BY name;
            """
        ).fetchall()

        actual_views = {row[0] for row in rows}

        if actual_views != EXPECTED_VIEWS:
            raise AssertionError(
                f"Unexpected economics views. "
                f"Expected={sorted(EXPECTED_VIEWS)}, "
                f"Actual={sorted(actual_views)}"
            )

        print("QA-01 Expected economics views                  | PASS")

        # ---------------------------------------------------------------
        # QA-02 — Scenario completeness
        # ---------------------------------------------------------------
        scenario_rows = connection.execute(
            """
            SELECT
                Scenario_ID,
                Scenario_Name,
                Oil_Price_USD_bbl,
                COUNT(*) AS Row_Count
            FROM vw_Economics_Daily
            GROUP BY
                Scenario_ID,
                Scenario_Name,
                Oil_Price_USD_bbl
            ORDER BY Scenario_ID;
            """
        ).fetchall()

        if len(scenario_rows) != 3:
            raise AssertionError(
                f"Expected 3 scenarios, found {len(scenario_rows)}"
            )

        for scenario_id, name, price, row_count in scenario_rows:
            if scenario_id not in EXPECTED_SCENARIOS:
                raise AssertionError(
                    f"Unexpected scenario: {scenario_id}"
                )

            expected_name, expected_price = EXPECTED_SCENARIOS[scenario_id]

            if name != expected_name:
                raise AssertionError(
                    f"{scenario_id}: expected name "
                    f"{expected_name}, got {name}"
                )

            if price != expected_price:
                raise AssertionError(
                    f"{scenario_id}: expected price "
                    f"{expected_price}, got {price}"
                )

            if row_count != 32250:
                raise AssertionError(
                    f"{scenario_id}: expected 32250 rows, "
                    f"got {row_count}"
                )

        print("QA-02 Scenario completeness                      | PASS")

        # ---------------------------------------------------------------
        # QA-03 — Daily row reconciliation
        # ---------------------------------------------------------------
        daily_rows = connection.execute(
            """
            SELECT COUNT(*)
            FROM vw_Economics_Daily;
            """
        ).fetchone()[0]

        if daily_rows != EXPECTED_DAILY_ROWS:
            raise AssertionError(
                f"Expected {EXPECTED_DAILY_ROWS} daily economics rows, "
                f"got {daily_rows}"
            )

        print("QA-03 Daily row reconciliation                   | PASS")

        # ---------------------------------------------------------------
        # QA-04 — Physical production reconciliation
        # ---------------------------------------------------------------
        production = connection.execute(
            """
            SELECT
                SUM(Potential_Oil_bbl),
                SUM(Actual_Oil_bbl),
                SUM(Deferred_Oil_bbl),
                SUM(Production_Impact_bbl)
            FROM vw_Economics_Daily
            WHERE Scenario_ID = 'S02';
            """
        ).fetchone()

        potential, actual, deferred, impact = production

        # The economics view contains one physical dataset per scenario.
        # Therefore compare the Base scenario against the authoritative
        # production-impact fact table.
        source = connection.execute(
            """
            SELECT
                SUM(Potential_Oil_bbl),
                SUM(Actual_Oil_bbl),
                SUM(Deferred_Oil_bbl),
                SUM(Production_Impact_bbl)
            FROM Fact_Production_Impact_Daily;
            """
        ).fetchone()

        source_potential, source_actual, source_deferred, source_impact = source

        assert_close(
            potential,
            source_potential,
            TOLERANCE_BBL,
            "Potential Oil"
        )

        assert_close(
            actual,
            source_actual,
            TOLERANCE_BBL,
            "Actual Oil"
        )

        assert_close(
            deferred,
            source_deferred,
            TOLERANCE_BBL,
            "Deferred Oil"
        )

        assert_close(
            impact,
            source_impact,
            TOLERANCE_BBL,
            "Production Impact"
        )

        print("QA-04 Physical production reconciliation        | PASS")

        # ---------------------------------------------------------------
        # QA-05 — Scenario independence of physical production
        # ---------------------------------------------------------------
        scenario_totals = connection.execute(
            """
            SELECT
                Scenario_ID,
                SUM(Potential_Oil_bbl),
                SUM(Actual_Oil_bbl),
                SUM(Deferred_Oil_bbl),
                SUM(Production_Impact_bbl)
            FROM vw_Economics_Daily
            GROUP BY Scenario_ID
            ORDER BY Scenario_ID;
            """
        ).fetchall()

        reference = scenario_totals[0][1:]

        for row in scenario_totals:
            if any(
                abs(value - reference[index]) > TOLERANCE_BBL
                for index, value in enumerate(row[1:])
            ):
                raise AssertionError(
                    "Physical production differs between scenarios"
                )

        print("QA-05 Scenario physical independence          | PASS")

        # ---------------------------------------------------------------
        # QA-06 — Revenue calculation
        # ---------------------------------------------------------------
        revenue_check = connection.execute(
            """
            SELECT
                MAX(
                    ABS(
                        Potential_Revenue_USD
                        - Potential_Oil_bbl * Oil_Price_USD_bbl
                    )
                ),
                MAX(
                    ABS(
                        Actual_Revenue_USD
                        - Actual_Oil_bbl * Oil_Price_USD_bbl
                    )
                ),
                MAX(
                    ABS(
                        Deferred_Value_USD
                        - Deferred_Oil_bbl * Oil_Price_USD_bbl
                    )
                ),
                MAX(
                    ABS(
                        Production_Impact_Value_USD
                        - Production_Impact_bbl * Oil_Price_USD_bbl
                    )
                )
            FROM vw_Economics_Daily;
            """
        ).fetchone()

        if any(value > TOLERANCE_USD for value in revenue_check):
            raise AssertionError(
                f"Revenue calculation error: {revenue_check}"
            )

        print("QA-06 Revenue calculation                      | PASS")

        # ---------------------------------------------------------------
        # QA-07 — Scenario valuation monotonicity
        # ---------------------------------------------------------------
        scenario_values = connection.execute(
            """
            SELECT
                Scenario_ID,
                SUM(Actual_Revenue_USD),
                SUM(Deferred_Value_USD),
                SUM(Production_Impact_Value_USD)
            FROM vw_Economics_Daily
            GROUP BY Scenario_ID
            ORDER BY Oil_Price_USD_bbl;
            """
        ).fetchall()

        if not (
            scenario_values[0][1] < scenario_values[1][1]
            < scenario_values[2][1]
        ):
            raise AssertionError(
                "Actual revenue is not increasing with oil price"
            )

        if not (
            scenario_values[0][2] < scenario_values[1][2]
            < scenario_values[2][2]
        ):
            raise AssertionError(
                "Deferred value is not increasing with oil price"
            )

        print("QA-07 Scenario valuation monotonicity          | PASS")

        # ---------------------------------------------------------------
        # QA-08 — Well summary reconciliation
        # ---------------------------------------------------------------
        daily_well_count = connection.execute(
            """
            SELECT COUNT(DISTINCT Well_ID)
            FROM vw_Economics_Daily;
            """
        ).fetchone()[0]

        summary_well_count = connection.execute(
            """
            SELECT COUNT(DISTINCT Well_ID)
            FROM vw_Economics_Well_Summary;
            """
        ).fetchone()[0]

        if (
            daily_well_count != EXPECTED_PRODUCER_WELLS
            or summary_well_count != EXPECTED_PRODUCER_WELLS
        ):
            raise AssertionError(
                f"Expected {EXPECTED_PRODUCER_WELLS} producer wells"
            )

        print("QA-08 Well summary reconciliation               | PASS")

        # ---------------------------------------------------------------
        # QA-09 — Field summary reconciliation
        # ---------------------------------------------------------------
        field_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM vw_Economics_Field_Summary;
            """
        ).fetchone()[0]

        if field_count != 3:
            raise AssertionError(
                f"Expected 3 field-scenario rows, got {field_count}"
            )

        print("QA-09 Field summary reconciliation             | PASS")

        # ---------------------------------------------------------------
        # QA-10 — Annual summary reconciliation
        # ---------------------------------------------------------------
        annual_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM vw_Economics_Annual_Summary;
            """
        ).fetchone()[0]

        if annual_count != 12:
            raise AssertionError(
                f"Expected 12 annual scenario rows, got {annual_count}"
            )

        print("QA-10 Annual summary reconciliation            | PASS")

        # ---------------------------------------------------------------
        # Summary metrics
        # ---------------------------------------------------------------
        base_summary = connection.execute(
            """
            SELECT
                SUM(Potential_Oil_bbl),
                SUM(Actual_Oil_bbl),
                SUM(Deferred_Oil_bbl),
                SUM(Actual_Revenue_USD),
                SUM(Deferred_Value_USD)
            FROM vw_Economics_Daily
            WHERE Scenario_ID = 'S02';
            """
        ).fetchone()

    print()
    print("Daily economics rows       :", daily_rows)
    print("Producer wells             :", daily_well_count)
    print("Potential Oil              :", round(base_summary[0], 2))
    print("Actual Oil                 :", round(base_summary[1], 2))
    print("Deferred Oil               :", round(base_summary[2], 2))
    print("Base Actual Revenue       :", round(base_summary[3], 2))
    print("Base Deferred Value       :", round(base_summary[4], 2))
    print()
    print("TOTAL CHECKS : 10")
    print("PASSED       : 10")
    print("FAILED       : 0")
    print("PHASE 5C.3 QA STATUS: PASS")


if __name__ == "__main__":
    main()