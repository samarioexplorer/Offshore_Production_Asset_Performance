from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "offshore_production_asset_performance.db"
)

ROW_COUNT_EXPECTED = {
    "Dim_Date": 1461,
    "Dim_Field": 1,
    "Dim_Manifold": 4,
    "Dim_Well": 30,
    "Dim_Equipment": 35,
    "Dim_Failure_Cause": 16,
    "Dim_Intervention": 6,
    "Dim_Scenario": 3,
    "Fact_Production_Daily": 32250,
    "Fact_Downtime_Event": 660,
    "Fact_Intervention_Event": 39,
    "Fact_Production_Impact_Daily": 32250,
}

CORE_STAGING_PAIRS = [
    ("Dim_Date", "stg_Dim_Date"),
    ("Dim_Field", "stg_Dim_Field"),
    ("Dim_Manifold", "stg_Dim_Manifold"),
    ("Dim_Well", "stg_Dim_Well"),
    ("Dim_Equipment", "stg_Dim_Equipment"),
    ("Dim_Failure_Cause", "stg_Dim_Failure_Cause"),
    ("Dim_Intervention", "stg_Dim_Intervention"),
    ("Dim_Scenario", "stg_Dim_Scenario"),
    ("Fact_Production_Daily", "stg_Fact_Production_Daily"),
    ("Fact_Downtime_Event", "stg_Fact_Downtime_Event"),
    ("Fact_Intervention_Event", "stg_Fact_Intervention_Event"),
    (
        "Fact_Production_Impact_Daily",
        "stg_Fact_Production_Impact_Daily",
    ),
]

PRIMARY_KEYS = [
    ("Dim_Date", "Date"),
    ("Dim_Field", "Field_ID"),
    ("Dim_Manifold", "Manifold_ID"),
    ("Dim_Well", "Well_ID"),
    ("Dim_Equipment", "Equipment_ID"),
    ("Dim_Failure_Cause", "Failure_Cause_ID"),
    ("Dim_Intervention", "Intervention_Type_ID"),
    ("Dim_Scenario", "Scenario_ID"),
    ("Fact_Production_Daily", "Date, Well_ID"),
    ("Fact_Downtime_Event", "Downtime_ID"),
    ("Fact_Intervention_Event", "Intervention_ID"),
    ("Fact_Production_Impact_Daily", "Date, Well_ID"),
]

REQUIRED_COLUMNS = {
    "Dim_Date": [
        "Date",
        "Year",
        "Quarter",
        "Month",
        "Month_Name",
        "Month_Start",
        "Year_Month",
        "Day",
        "Day_of_Week",
        "Day_Name",
    ],
    "Dim_Field": [
        "Field_ID",
        "Field_Name",
        "Basin",
        "Development_Type",
        "Operator_Type",
    ],
    "Dim_Manifold": [
        "Manifold_ID",
        "Manifold_Name",
        "Field_ID",
    ],
    "Dim_Well": [
        "Well_ID",
        "Well_Name",
        "Well_Type",
        "Field_ID",
        "Well_Status",
    ],
    "Dim_Equipment": [
        "Equipment_ID",
        "Equipment_Name",
        "Equipment_Type",
        "Equipment_Category",
        "Field_ID",
        "Criticality",
        "Status",
    ],
    "Dim_Failure_Cause": [
        "Failure_Cause_ID",
        "Failure_Category",
        "Failure_Cause",
        "Severity",
        "Planned_Flag",
    ],
    "Dim_Intervention": [
        "Intervention_Type_ID",
        "Intervention_Type",
        "Intervention_Category",
        "Typical_Duration_hr",
        "Typical_Cost_USD",
    ],
    "Dim_Scenario": [
        "Scenario_ID",
        "Scenario_Name",
        "Oil_Price_USD_bbl",
    ],
    "Fact_Production_Daily": [
        "Date",
        "Well_ID",
        "Potential_Oil_bbl",
        "Oil_bbl",
        "Gas_Mscf",
        "Water_bbl",
        "Liquid_bbl",
        "Runtime_hr",
        "Available_hr",
    ],
    "Fact_Downtime_Event": [
        "Downtime_ID",
        "Date",
        "Well_ID",
        "Equipment_ID",
        "Failure_Cause_ID",
        "Downtime_Type",
        "Start_Hour",
        "Duration_hr",
        "Severity",
        "Failure_Severity",
        "Planned_Flag",
        "Production_Affected",
    ],
    "Fact_Intervention_Event": [
        "Intervention_ID",
        "Well_ID",
        "Intervention_Type_ID",
        "Start_Date",
        "End_Date",
        "Duration_Days",
        "Expected_Oil_Rate_bopd",
        "Target_Recovery_pct",
        "Intervention_Cost_USD",
        "Status",
    ],
    "Fact_Production_Impact_Daily": [
        "Date",
        "Well_ID",
        "Potential_Oil_bbl",
        "Baseline_Oil_bbl",
        "Downtime_Hours",
        "Effective_Downtime_Hours",
        "Available_hr",
        "Downtime_Event_Count",
        "Downtime_Deferred_Oil_bbl",
        "Intervention_Flag",
        "Intervention_Days",
        "Intervention_Recovery_pct",
        "Expected_Oil_Rate_bopd",
        "Intervention_Cost_USD",
        "Intervention_Recovery_Oil_bbl",
        "Intervention_Production_Loss_bbl",
        "Actual_Oil_bbl",
        "Deferred_Oil_bbl",
        "Production_Impact_bbl",
        "Production_Availability_pct",
        "Production_Efficiency_pct",
        "Production_Impact_Flag",
    ],
}


def check_row_counts(connection):
    violations = []

    for core_table, staging_table in CORE_STAGING_PAIRS:
        core_count = connection.execute(
            f"SELECT COUNT(*) FROM {core_table}"
        ).fetchone()[0]

        staging_count = connection.execute(
            f"SELECT COUNT(*) FROM {staging_table}"
        ).fetchone()[0]

        expected_count = ROW_COUNT_EXPECTED[core_table]

        if core_count != staging_count or core_count != expected_count:
            violations.append(
                (
                    core_table,
                    core_count,
                    staging_count,
                    expected_count,
                )
            )

    return violations


def check_primary_keys(connection):
    violations = []

    for table, key in PRIMARY_KEYS:
        duplicate_count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT {key}
                FROM {table}
                GROUP BY {key}
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]

        if duplicate_count != 0:
            violations.append((table, key, duplicate_count))

    return violations


def check_foreign_keys(connection):
    violations = []

    if connection.execute("PRAGMA foreign_keys;").fetchone()[0] != 1:
        violations.append(("Foreign-key enforcement", "OFF"))

    for table in [
        "Dim_Manifold",
        "Dim_Well",
        "Dim_Equipment",
        "Fact_Production_Daily",
        "Fact_Downtime_Event",
        "Fact_Intervention_Event",
        "Fact_Production_Impact_Daily",
    ]:
        result = connection.execute(
            f"PRAGMA foreign_key_check({table});"
        ).fetchall()

        if result:
            violations.append((table, len(result)))

    return violations


def check_required_columns(connection):
    violations = []

    for table, columns in REQUIRED_COLUMNS.items():
        for column in columns:
            null_count = connection.execute(
                f"""
                SELECT COUNT(*)
                FROM {table}
                WHERE {column} IS NULL
                """
            ).fetchone()[0]

            if null_count != 0:
                violations.append(
                    (table, column, null_count)
                )

    return violations


def check_dimension_hierarchy(connection):
    checks = [
        (
            "Dim_Manifold -> Dim_Field",
            """
            SELECT COUNT(*)
            FROM Dim_Manifold m
            LEFT JOIN Dim_Field f
                ON m.Field_ID = f.Field_ID
            WHERE f.Field_ID IS NULL
            """,
        ),
        (
            "Dim_Well -> Dim_Field",
            """
            SELECT COUNT(*)
            FROM Dim_Well w
            LEFT JOIN Dim_Field f
                ON w.Field_ID = f.Field_ID
            WHERE f.Field_ID IS NULL
            """,
        ),
        (
            "Dim_Well -> Dim_Manifold",
            """
            SELECT COUNT(*)
            FROM Dim_Well w
            LEFT JOIN Dim_Manifold m
                ON w.Manifold_ID = m.Manifold_ID
            WHERE w.Manifold_ID IS NOT NULL
              AND m.Manifold_ID IS NULL
            """,
        ),
        (
            "Dim_Equipment -> Dim_Field",
            """
            SELECT COUNT(*)
            FROM Dim_Equipment e
            LEFT JOIN Dim_Field f
                ON e.Field_ID = f.Field_ID
            WHERE f.Field_ID IS NULL
            """,
        ),
    ]

    violations = []

    for name, sql in checks:
        count = connection.execute(sql).fetchone()[0]

        if count != 0:
            violations.append((name, count))

    return violations


def check_intervention_relationships(connection):
    checks = [
        (
            "Impact Intervention_ID -> Event",
            """
            SELECT COUNT(*)
            FROM Fact_Production_Impact_Daily p
            LEFT JOIN Fact_Intervention_Event i
                ON p.Intervention_ID = i.Intervention_ID
            WHERE p.Intervention_ID IS NOT NULL
              AND i.Intervention_ID IS NULL
            """,
        ),
        (
            "Intervention_Flag=1 with missing Intervention_ID",
            """
            SELECT COUNT(*)
            FROM Fact_Production_Impact_Daily
            WHERE Intervention_Flag = 1
              AND Intervention_ID IS NULL
            """,
        ),
        (
            "Impact Intervention_Type_ID -> Dimension",
            """
            SELECT COUNT(*)
            FROM Fact_Production_Impact_Daily p
            LEFT JOIN Dim_Intervention i
                ON p.Intervention_Type_ID =
                   i.Intervention_Type_ID
            WHERE p.Intervention_Type_ID IS NOT NULL
              AND i.Intervention_Type_ID IS NULL
            """,
        ),
        (
            "Intervention_ID / Type_ID mismatch",
            """
            SELECT COUNT(*)
            FROM Fact_Production_Impact_Daily p
            JOIN Fact_Intervention_Event e
                ON p.Intervention_ID = e.Intervention_ID
            WHERE p.Intervention_Type_ID !=
                  e.Intervention_Type_ID
            """,
        ),
    ]

    violations = []

    for name, sql in checks:
        count = connection.execute(sql).fetchone()[0]

        if count != 0:
            violations.append((name, count))

    return violations


def check_production_reconciliation(connection):
    potential, actual, deferred, difference = connection.execute(
        """
        SELECT
            SUM(Potential_Oil_bbl),
            SUM(Actual_Oil_bbl),
            SUM(Deferred_Oil_bbl),
            SUM(Potential_Oil_bbl)
                - SUM(Actual_Oil_bbl)
                - SUM(Deferred_Oil_bbl)
        FROM Fact_Production_Impact_Daily
        """
    ).fetchone()

    tolerance = 0.01

    if abs(difference) > tolerance:
        return {
            "potential": potential,
            "actual": actual,
            "deferred": deferred,
            "difference": difference,
            "tolerance": tolerance,
        }

    return None


def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    print("=" * 72)
    print("PHASE 5B.2 — CORE RELATIONAL QA")
    print("=" * 72)
    print()

    checks = []

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")

        qa01 = check_row_counts(connection)
        checks.append(("QA-01", "Core vs staging row counts", not qa01))

        qa02 = check_primary_keys(connection)
        checks.append(("QA-02", "Primary-key uniqueness", not qa02))

        qa03 = check_foreign_keys(connection)
        checks.append(("QA-03", "Foreign-key integrity", not qa03))

        qa04 = check_required_columns(connection)
        checks.append(
            ("QA-04", "Required-column NULL validation", not qa04)
        )

        qa05 = check_dimension_hierarchy(connection)
        checks.append(
            ("QA-05", "Dimension hierarchy integrity", not qa05)
        )

        qa06 = check_intervention_relationships(connection)
        checks.append(
            ("QA-06", "Intervention relationship integrity", not qa06)
        )

        qa07 = check_production_reconciliation(connection)
        checks.append(
            ("QA-07", "Production reconciliation", qa07 is None)
        )

        print("-" * 72)

        for qa_id, description, passed in checks:
            print(
                f"{qa_id} | "
                f"{description:<42} | "
                f"{'PASS' if passed else 'FAIL'}"
            )

        print("-" * 72)

        passed_count = sum(result for _, _, result in checks)
        failed_count = len(checks) - passed_count

        print(f"TOTAL CHECKS : {len(checks)}")
        print(f"PASSED       : {passed_count}")
        print(f"FAILED       : {failed_count}")
        print("-" * 72)

        if failed_count == 0:
            print("PHASE 5B.2 QA STATUS: PASS")
        else:
            print("PHASE 5B.2 QA STATUS: FAIL")
            print()
            print("Validation details:")

            if qa01:
                print("QA-01:", qa01)

            if qa02:
                print("QA-02:", qa02)

            if qa03:
                print("QA-03:", qa03)

            if qa04:
                print("QA-04:", qa04)

            if qa05:
                print("QA-05:", qa05)

            if qa06:
                print("QA-06:", qa06)

            if qa07:
                print("QA-07:", qa07)

            raise SystemExit(1)


if __name__ == "__main__":
    main()