import sqlite3
from pathlib import Path


DB_PATH = Path(
    r"C:\Users\aniba\Documents\Offshore_Production_Asset_Performance"
) / "database" / "offshore_production_asset_performance.db"


def check_unique(conn, table, columns):
    cols = ", ".join(f'"{c}"' for c in columns)

    sql = f"""
        SELECT COUNT(*) AS duplicate_groups
        FROM (
            SELECT {cols}
            FROM "{table}"
            GROUP BY {cols}
            HAVING COUNT(*) > 1
        )
    """

    return conn.execute(sql).fetchone()[0]


def check_null_keys(conn, table, columns):
    conditions = " OR ".join(
        f'"{c}" IS NULL' for c in columns
    )

    sql = f"""
        SELECT COUNT(*)
        FROM "{table}"
        WHERE {conditions}
    """

    return conn.execute(sql).fetchone()[0]


def check_orphans(conn, child_table, child_key, parent_table, parent_key):
    sql = f"""
        SELECT COUNT(*)
        FROM "{child_table}" AS c
        LEFT JOIN "{parent_table}" AS p
            ON c."{child_key}" = p."{parent_key}"
        WHERE c."{child_key}" IS NOT NULL
          AND p."{parent_key}" IS NULL
    """

    return conn.execute(sql).fetchone()[0]


def check_orphans_composite(
    conn,
    child_table,
    child_columns,
    parent_table,
    parent_columns,
):
    join_condition = " AND ".join(
        f'c."{child}" = p."{parent}"'
        for child, parent in zip(child_columns, parent_columns)
    )

    null_condition = " OR ".join(
        f'c."{child}" IS NOT NULL'
        for child in child_columns
    )

    sql = f"""
        SELECT COUNT(*)
        FROM "{child_table}" AS c
        LEFT JOIN "{parent_table}" AS p
            ON {join_condition}
        WHERE {null_condition}
          AND p."{parent_columns[0]}" IS NULL
    """

    return conn.execute(sql).fetchone()[0]


def row_count(conn, table):
    return conn.execute(
        f'SELECT COUNT(*) FROM "{table}"'
    ).fetchone()[0]


def main():

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)

    checks = []

    def add(name, actual, expected):
        status = "PASS" if actual == expected else "FAIL"
        checks.append((name, actual, expected, status))

    print("=" * 78)
    print("PHASE 6B.3B — POWER BI KEY / GRAIN QA")
    print("=" * 78)
    print()

    # ------------------------------------------------------------------
    # EXPECTED ROW COUNTS
    # ------------------------------------------------------------------

    expected_rows = {
        "Dim_Date": 1461,
        "Dim_Field": 1,
        "Dim_Manifold": 4,
        "Dim_Well": 30,
        "Dim_Equipment": 35,
        "Dim_Failure_Cause": 16,
        "Dim_Intervention": 6,
        "Dim_Scenario": 3,
        "Fact_Production_Impact_Daily": 32250,
        "Fact_Downtime_Event": 660,
        "Fact_Intervention_Event": 39,
        "vw_Economics_Daily": 96750,
    }

    for table, expected in expected_rows.items():
        actual = row_count(conn, table)
        add(
            f"ROWCOUNT {table}",
            actual,
            expected,
        )

    # ------------------------------------------------------------------
    # DIMENSION KEY UNIQUENESS
    # ------------------------------------------------------------------

    dimension_keys = {
        "Dim_Date": ["Date"],
        "Dim_Field": ["Field_ID"],
        "Dim_Manifold": ["Manifold_ID"],
        "Dim_Well": ["Well_ID"],
        "Dim_Equipment": ["Equipment_ID"],
        "Dim_Failure_Cause": ["Failure_Cause_ID"],
        "Dim_Intervention": ["Intervention_Type_ID"],
        "Dim_Scenario": ["Scenario_ID"],
    }

    for table, keys in dimension_keys.items():

        duplicate_groups = check_unique(
            conn,
            table,
            keys,
        )

        null_keys = check_null_keys(
            conn,
            table,
            keys,
        )

        add(
            f"UNIQUE {table} [{', '.join(keys)}]",
            duplicate_groups,
            0,
        )

        add(
            f"NULLKEY {table} [{', '.join(keys)}]",
            null_keys,
            0,
        )

    # ------------------------------------------------------------------
    # FACT GRAIN
    # ------------------------------------------------------------------

    fact_grains = {
        "Fact_Production_Impact_Daily": ["Date", "Well_ID"],
        "Fact_Downtime_Event": ["Downtime_ID"],
        "Fact_Intervention_Event": ["Intervention_ID"],
        "vw_Economics_Daily": [
            "Date",
            "Well_ID",
            "Scenario_ID",
        ],
    }

    for table, grain in fact_grains.items():

        duplicate_groups = check_unique(
            conn,
            table,
            grain,
        )

        null_keys = check_null_keys(
            conn,
            table,
            grain,
        )

        add(
            f"GRAIN {table} [{', '.join(grain)}]",
            duplicate_groups,
            0,
        )

        add(
            f"NULLGRAIN {table} [{', '.join(grain)}]",
            null_keys,
            0,
        )

    # ------------------------------------------------------------------
    # FOREIGN KEY / ORPHAN CHECKS
    # ------------------------------------------------------------------

    single_relationships = [
        (
            "Dim_Well → Dim_Field",
            "Dim_Well",
            "Field_ID",
            "Dim_Field",
            "Field_ID",
        ),
        (
            "Dim_Well → Dim_Manifold",
            "Dim_Well",
            "Manifold_ID",
            "Dim_Manifold",
            "Manifold_ID",
        ),
        (
            "Dim_Equipment → Dim_Field",
            "Dim_Equipment",
            "Field_ID",
            "Dim_Field",
            "Field_ID",
        ),
        (
            "Fact_Downtime_Event → Dim_Well",
            "Fact_Downtime_Event",
            "Well_ID",
            "Dim_Well",
            "Well_ID",
        ),
        (
            "Fact_Downtime_Event → Dim_Equipment",
            "Fact_Downtime_Event",
            "Equipment_ID",
            "Dim_Equipment",
            "Equipment_ID",
        ),
        (
            "Fact_Downtime_Event → Dim_Failure_Cause",
            "Fact_Downtime_Event",
            "Failure_Cause_ID",
            "Dim_Failure_Cause",
            "Failure_Cause_ID",
        ),
        (
            "Fact_Intervention_Event → Dim_Well",
            "Fact_Intervention_Event",
            "Well_ID",
            "Dim_Well",
            "Well_ID",
        ),
        (
            "Fact_Intervention_Event → Dim_Intervention",
            "Fact_Intervention_Event",
            "Intervention_Type_ID",
            "Dim_Intervention",
            "Intervention_Type_ID",
        ),
        (
            "Fact_Production_Impact_Daily → Dim_Well",
            "Fact_Production_Impact_Daily",
            "Well_ID",
            "Dim_Well",
            "Well_ID",
        ),
        (
            "vw_Economics_Daily → Dim_Well",
            "vw_Economics_Daily",
            "Well_ID",
            "Dim_Well",
            "Well_ID",
        ),
        (
            "vw_Economics_Daily → Dim_Scenario",
            "vw_Economics_Daily",
            "Scenario_ID",
            "Dim_Scenario",
            "Scenario_ID",
        ),
    ]

    for (
        name,
        child_table,
        child_key,
        parent_table,
        parent_key,
    ) in single_relationships:

        orphans = check_orphans(
            conn,
            child_table,
            child_key,
            parent_table,
            parent_key,
        )

        add(
            f"ORPHAN {name}",
            orphans,
            0,
        )

    # ------------------------------------------------------------------
    # DATE COVERAGE
    # ------------------------------------------------------------------

    date_relationships = [
        (
            "Fact_Production_Impact_Daily → Dim_Date",
            "Fact_Production_Impact_Daily",
            "Date",
        ),
        (
            "Fact_Downtime_Event → Dim_Date",
            "Fact_Downtime_Event",
            "Date",
        ),
        (
            "vw_Economics_Daily → Dim_Date",
            "vw_Economics_Daily",
            "Date",
        ),
    ]

    for name, child_table, child_key in date_relationships:

        orphans = check_orphans(
            conn,
            child_table,
            child_key,
            "Dim_Date",
            "Date",
        )

        add(
            f"DATE {name}",
            orphans,
            0,
        )

    # ------------------------------------------------------------------
    # REPORT
    # ------------------------------------------------------------------

    print(
        f"{'CHECK':60} {'ACTUAL':>10} "
        f"{'EXPECTED':>10} {'STATUS':>8}"
    )
    print("-" * 92)

    for name, actual, expected, status in checks:
        print(
            f"{name:60} "
            f"{actual:>10} "
            f"{expected:>10} "
            f"{status:>8}"
        )

    passed = sum(
        1 for _, _, _, status in checks
        if status == "PASS"
    )

    failed = sum(
        1 for _, _, _, status in checks
        if status == "FAIL"
    )

    print()
    print("=" * 78)
    print(f"TOTAL CHECKS : {len(checks)}")
    print(f"PASSED       : {passed}")
    print(f"FAILED       : {failed}")

    if failed == 0:
        print("POWER BI KEY / GRAIN QA STATUS: PASS")
    else:
        print("POWER BI KEY / GRAIN QA STATUS: FAIL")

    print("=" * 78)

    conn.close()

    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()