from pathlib import Path
from datetime import datetime, timezone
import sqlite3

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "offshore_production_asset_performance.db"
)

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


DATASETS = [
    {
        "source": RAW_DATA_DIR / "Dim_Date.csv",
        "table": "stg_Dim_Date",
        "expected_rows": 1461,
        "columns": [
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
    },
    {
        "source": RAW_DATA_DIR / "Dim_Field.csv",
        "table": "stg_Dim_Field",
        "expected_rows": 1,
        "columns": [
            "Field_ID",
            "Field_Name",
            "Basin",
            "Development_Type",
            "Water_Depth_ft",
            "Operator_Type",
            "First_Production_Date",
            "FPSO_Name",
        ],
    },
    {
        "source": RAW_DATA_DIR / "Dim_Manifold.csv",
        "table": "stg_Dim_Manifold",
        "expected_rows": 4,
        "columns": [
            "Manifold_ID",
            "Manifold_Name",
            "Field_ID",
            "Water_Depth_ft",
            "Well_Count",
            "Installation_Date",
            "Status",
        ],
    },
    {
        "source": RAW_DATA_DIR / "Dim_Well.csv",
        "table": "stg_Dim_Well",
        "expected_rows": 30,
        "columns": [
            "Well_ID",
            "Well_Name",
            "Well_Type",
            "Field_ID",
            "Manifold_ID",
            "Reservoir",
            "Water_Depth_ft",
            "Spud_Date",
            "First_Production_Date",
            "Well_Status",
            "Initial_Oil_Rate_bopd",
            "Initial_Gas_Rate_Mscfd",
            "Decline_Rate_pct",
            "Initial_Water_Cut_pct",
            "Artificial_Lift_Type",
        ],
    },
    {
        "source": RAW_DATA_DIR / "Dim_Equipment.csv",
        "table": "stg_Dim_Equipment",
        "expected_rows": 35,
        "columns": [
            "Equipment_ID",
            "Equipment_Name",
            "Equipment_Type",
            "Equipment_Category",
            "Parent_Equipment_ID",
            "Field_ID",
            "Criticality",
            "Installation_Date",
            "Design_Life_Years",
            "Status",
        ],
    },
    {
        "source": RAW_DATA_DIR / "Dim_Failure_Cause.csv",
        "table": "stg_Dim_Failure_Cause",
        "expected_rows": 16,
        "columns": [
            "Failure_Cause_ID",
            "Failure_Category",
            "Failure_Cause",
            "Severity",
            "Planned_Flag",
        ],
    },
    {
        "source": RAW_DATA_DIR / "Dim_Intervention.csv",
        "table": "stg_Dim_Intervention",
        "expected_rows": 6,
        "columns": [
            "Intervention_Type_ID",
            "Intervention_Type",
            "Intervention_Category",
            "Typical_Duration_hr",
            "Typical_Cost_USD",
        ],
    },
    {
        "source": RAW_DATA_DIR / "Dim_Scenario.csv",
        "table": "stg_Dim_Scenario",
        "expected_rows": 3,
        "columns": [
            "Scenario_ID",
            "Scenario_Name",
            "Oil_Price_USD_bbl",
        ],
    },
    {
        "source": RAW_DATA_DIR / "Fact_Production_Daily.csv",
        "table": "stg_Fact_Production_Daily",
        "expected_rows": 32250,
        "columns": [
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
    },
    {
        "source": RAW_DATA_DIR / "Fact_Downtime_Event.csv",
        "table": "stg_Fact_Downtime_Event",
        "expected_rows": 660,
        "columns": [
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
    },
    {
        "source": RAW_DATA_DIR / "Fact_Intervention_Event.csv",
        "table": "stg_Fact_Intervention_Event",
        "expected_rows": 39,
        "columns": [
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
    },
    {
        "source": PROCESSED_DATA_DIR / "Fact_Production_Impact_Daily.csv",
        "table": "stg_Fact_Production_Impact_Daily",
        "expected_rows": 32250,
        "columns": [
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
            "Intervention_ID",
            "Intervention_Type_ID",
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
    },
]


def validate_source_file(dataset: dict) -> pd.DataFrame:
    """Read and validate one authoritative CSV source."""

    source = dataset["source"]

    if not source.exists():
        raise FileNotFoundError(
            f"Required source file not found: {source}"
        )

    df = pd.read_csv(source)

    actual_columns = list(df.columns)
    expected_columns = dataset["columns"]

    if actual_columns != expected_columns:
        raise ValueError(
            f"Column mismatch for {source.name}\n"
            f"Expected: {expected_columns}\n"
            f"Actual:   {actual_columns}"
        )

    source_rows = len(df)

    if source_rows != dataset["expected_rows"]:
        raise ValueError(
            f"Unexpected row count for {source.name}: "
            f"expected {dataset['expected_rows']}, "
            f"found {source_rows}"
        )

    return df


def load_dataset(
    connection: sqlite3.Connection,
    dataset: dict,
) -> tuple[int, int]:
    """Load one validated CSV into its staging table."""

    df = validate_source_file(dataset)

    table = dataset["table"]
    source_rows = len(df)

    connection.execute(f"DELETE FROM {table}")

    df.to_sql(
        table,
        connection,
        if_exists="append",
        index=False,
    )

    loaded_rows = connection.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    difference = source_rows - loaded_rows

    status = "PASS" if difference == 0 else "FAIL"

    connection.execute(
        """
        INSERT INTO Staging_Load_Audit (
            Table_Name,
            Source_File,
            Source_Row_Count,
            Loaded_Row_Count,
            Row_Count_Difference,
            Load_Status,
            Load_Timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            table,
            dataset["source"].name,
            source_rows,
            loaded_rows,
            difference,
            status,
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    if difference != 0:
        raise RuntimeError(
            f"Row-count mismatch for {table}: "
            f"source={source_rows}, loaded={loaded_rows}"
        )

    return source_rows, loaded_rows


def load_staging() -> None:
    """Execute the complete controlled staging load."""

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    print("=" * 72)
    print("PHASE 5B.1 — CONTROLLED CSV → SQLITE STAGING LOAD")
    print("=" * 72)
    print()
    print(f"Database: {DATABASE_PATH}")
    print()

    total_source_rows = 0
    total_loaded_rows = 0

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")

        try:
            for dataset in DATASETS:
                source_rows, loaded_rows = load_dataset(
                    connection,
                    dataset,
                )

                total_source_rows += source_rows
                total_loaded_rows += loaded_rows

                print(
                    f"PASS | {dataset['table']:<35} "
                    f"{loaded_rows:>6} rows"
                )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

    print()
    print("-" * 72)
    print(f"Total source rows : {total_source_rows}")
    print(f"Total loaded rows : {total_loaded_rows}")
    print(
        f"Total difference  : "
        f"{total_source_rows - total_loaded_rows}"
    )
    print("-" * 72)
    print()
    print("STAGING LOAD STATUS: PASS")
    print("PHASE 5B.1 COMPLETE")


if __name__ == "__main__":
    load_staging()