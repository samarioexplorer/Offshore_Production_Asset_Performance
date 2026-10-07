"""
Phase 4D — Production Impact & Deferred Production Engine

Project: Offshore Production Asset Performance
Field: Orion Deepwater Field

Purpose
-------
Integrate the locked baseline production dataset with:

    Fact_Downtime_Event
    Fact_Intervention_Event

to calculate daily production impact, actual production,
deferred production, and intervention recovery.

Important
---------
The raw baseline production dataset is NOT modified.

Output
------
data/processed/Fact_Production_Impact_Daily.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

PRODUCTION_PATH = RAW_DATA_DIR / "Fact_Production_Daily.csv"
DOWNTIME_PATH = RAW_DATA_DIR / "Fact_Downtime_Event.csv"
INTERVENTION_PATH = RAW_DATA_DIR / "Fact_Intervention_Event.csv"

OUTPUT_PATH = PROCESSED_DATA_DIR / "Fact_Production_Impact_Daily.csv"


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def fail(message: str) -> None:
    print(f"\nERROR: {message}\n")
    sys.exit(1)


def validate_columns(
    df: pd.DataFrame,
    required: list[str],
    dataset_name: str,
) -> None:
    missing = [column for column in required if column not in df.columns]

    if missing:
        fail(
            f"{dataset_name} is missing required column(s): "
            + ", ".join(missing)
        )


# ---------------------------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------------------------

def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    for path in [
        PRODUCTION_PATH,
        DOWNTIME_PATH,
        INTERVENTION_PATH,
    ]:
        if not path.exists():
            fail(f"Required input file not found: {path}")

    production = pd.read_csv(PRODUCTION_PATH)
    downtime = pd.read_csv(DOWNTIME_PATH)
    intervention = pd.read_csv(INTERVENTION_PATH)

    validate_columns(
        production,
        [
            "Date",
            "Well_ID",
            "Potential_Oil_bbl",
            "Oil_bbl",
            "Runtime_hr",
            "Available_hr",
        ],
        "Fact_Production_Daily",
    )

    validate_columns(
        downtime,
        [
            "Downtime_ID",
            "Date",
            "Well_ID",
            "Duration_hr",
            "Production_Affected",
        ],
        "Fact_Downtime_Event",
    )

    validate_columns(
        intervention,
        [
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
        "Fact_Intervention_Event",
    )

    return production, downtime, intervention


# ---------------------------------------------------------------------------
# DOWNTIME AGGREGATION
# ---------------------------------------------------------------------------

def build_downtime_daily(
    downtime: pd.DataFrame,
) -> pd.DataFrame:

    df = downtime.copy()

    df["Date"] = pd.to_datetime(df["Date"])
    df["Well_ID"] = df["Well_ID"].astype(str)

    # Normalize the production-affect flag.
    affected = (
        df["Production_Affected"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["yes", "y", "true", "1"])
    )

    df["Affected_Duration_hr"] = np.where(
        affected,
        df["Duration_hr"],
        0.0,
    )

    daily = (
        df.groupby(
            ["Date", "Well_ID"],
            as_index=False,
        )
        .agg(
            Downtime_Hours=(
                "Affected_Duration_hr",
                "sum",
            ),
            Downtime_Event_Count=(
                "Downtime_ID",
                "nunique",
            ),
        )
    )

    return daily


# ---------------------------------------------------------------------------
# INTERVENTION DAILY EXPANSION
# ---------------------------------------------------------------------------

def expand_interventions(
    intervention: pd.DataFrame,
) -> pd.DataFrame:

    df = intervention.copy()

    df["Start_Date"] = pd.to_datetime(df["Start_Date"])
    df["End_Date"] = pd.to_datetime(df["End_Date"])
    df["Well_ID"] = df["Well_ID"].astype(str)

    # Cancelled interventions are retained in the event layer but have
    # no production effect.
    completed = df.loc[
        df["Status"].astype(str).str.strip().str.lower().eq("completed")
    ].copy()

    if completed.empty:
        return pd.DataFrame(
            columns=[
                "Date",
                "Well_ID",
                "Intervention_ID",
                "Intervention_Type_ID",
                "Intervention_Days",
                "Intervention_Recovery_pct",
                "Expected_Oil_Rate_bopd",
                "Intervention_Cost_USD",
            ]
        )

    records: list[dict] = []

    for row in completed.itertuples(index=False):

        dates = pd.date_range(
            start=row.Start_Date,
            end=row.End_Date,
            freq="D",
        )

        for date in dates:
            records.append(
                {
                    "Date": date,
                    "Well_ID": row.Well_ID,
                    "Intervention_ID": row.Intervention_ID,
                    "Intervention_Type_ID": (
                        row.Intervention_Type_ID
                    ),
                    "Intervention_Days": 1,
                    "Intervention_Recovery_pct": (
                        row.Target_Recovery_pct
                    ),
                    "Expected_Oil_Rate_bopd": (
                        row.Expected_Oil_Rate_bopd
                    ),
                    "Intervention_Cost_USD": (
                        row.Intervention_Cost_USD
                    ),
                }
            )

    expanded = pd.DataFrame(records)

    return expanded


# ---------------------------------------------------------------------------
# VALIDATE INTERVENTION EXPANSION
# ---------------------------------------------------------------------------

def aggregate_interventions(
    intervention_daily: pd.DataFrame,
) -> pd.DataFrame:

    if intervention_daily.empty:
        return pd.DataFrame(
            columns=[
                "Date",
                "Well_ID",
                "Intervention_Flag",
                "Intervention_Days",
                "Intervention_Recovery_pct",
                "Expected_Oil_Rate_bopd",
                "Intervention_Cost_USD",
                "Intervention_Count",
            ]
        )

    # The generator guarantees no overlapping interventions on the same
    # well. Therefore each well-day should have at most one intervention.
    duplicate_days = (
        intervention_daily
        .groupby(["Date", "Well_ID"])
        .size()
        .gt(1)
        .sum()
    )

    if duplicate_days:
        fail(
            f"Found {duplicate_days} well-days with overlapping "
            "interventions."
        )

    daily = intervention_daily.copy()

    daily["Intervention_Flag"] = 1

    daily = daily.rename(
        columns={
            "Intervention_Days": "Intervention_Days",
            "Intervention_Recovery_pct": (
                "Intervention_Recovery_pct"
            ),
        }
    )

    return daily[
        [
            "Date",
            "Well_ID",
            "Intervention_ID",
            "Intervention_Type_ID",
            "Intervention_Flag",
            "Intervention_Days",
            "Intervention_Recovery_pct",
            "Expected_Oil_Rate_bopd",
            "Intervention_Cost_USD",
        ]
    ]


# ---------------------------------------------------------------------------
# PRODUCTION IMPACT
# ---------------------------------------------------------------------------

def calculate_production_impact(
    production: pd.DataFrame,
    downtime_daily: pd.DataFrame,
    intervention_daily: pd.DataFrame,
) -> pd.DataFrame:

    df = production.copy()

    df["Date"] = pd.to_datetime(df["Date"])
    df["Well_ID"] = df["Well_ID"].astype(str)

    # Preserve the Phase 4B baseline values.
    df = df.rename(
        columns={
            "Oil_bbl": "Baseline_Oil_bbl",
        }
    )

    # ------------------------------------------------------------------
    # Downtime
    # ------------------------------------------------------------------

    df = df.merge(
        downtime_daily,
        on=["Date", "Well_ID"],
        how="left",
        validate="one_to_one",
    )

    df["Downtime_Hours"] = (
        df["Downtime_Hours"].fillna(0.0)
    )

    df["Downtime_Event_Count"] = (
        df["Downtime_Event_Count"].fillna(0).astype(int)
    )

    # A daily well cannot lose more production time than its available
    # operating window.
    df["Effective_Downtime_Hours"] = (
        df["Downtime_Hours"]
        .clip(
            lower=0.0,
            upper=df["Available_hr"],
        )
    )

    # ------------------------------------------------------------------
    # Intervention
    # ------------------------------------------------------------------

    df = df.merge(
        intervention_daily,
        on=["Date", "Well_ID"],
        how="left",
        validate="one_to_one",
    )

    df["Intervention_Flag"] = (
        df["Intervention_Flag"]
        .fillna(0)
        .astype(int)
    )

    df["Intervention_Days"] = (
        df["Intervention_Days"]
        .fillna(0)
        .astype(int)
    )

    df["Intervention_Recovery_pct"] = (
        df["Intervention_Recovery_pct"]
        .fillna(100.0)
    )

    df["Expected_Oil_Rate_bopd"] = (
        df["Expected_Oil_Rate_bopd"]
        .fillna(df["Baseline_Oil_bbl"])
    )

    df["Intervention_Cost_USD"] = (
        df["Intervention_Cost_USD"]
        .fillna(0.0)
    )

    # ------------------------------------------------------------------
    # INTERVENTION EFFECT
    # ------------------------------------------------------------------

    # For intervention days:
    #
    #   recovery factor = Target Recovery %
    #
    # For normal days:
    #
    #   recovery factor = 100%
    #
    # Therefore:
    #
    #   intervention-adjusted oil =
    #       baseline oil × recovery factor
    #
    # This deliberately allows >100% recovery to represent incremental
    # production opportunity.

    recovery_factor = (
        df["Intervention_Recovery_pct"] / 100.0
    )

    df["Intervention_Adjusted_Oil_bbl"] = (
        df["Baseline_Oil_bbl"]
        * recovery_factor
    )

    df["Intervention_Impact_bbl"] = (
        df["Intervention_Adjusted_Oil_bbl"]
        - df["Baseline_Oil_bbl"]
    )

    # ------------------------------------------------------------------
    # DOWNTIME EFFECT
    # ------------------------------------------------------------------

    # Downtime is applied after the intervention adjustment.
    #
    # This establishes a deterministic precedence:
    #
    #   baseline
    #       ↓
    #   intervention recovery
    #       ↓
    #   remaining downtime
    #
    # This prevents the same production loss from being counted twice.

    downtime_factor = np.where(
        df["Available_hr"] > 0,
        (
            1.0
            - (
                df["Effective_Downtime_Hours"]
                / df["Available_hr"]
            )
        ),
        1.0,
    )

    downtime_factor = np.clip(
        downtime_factor,
        0.0,
        1.0,
    )

    df["Actual_Oil_bbl"] = (
        df["Intervention_Adjusted_Oil_bbl"]
        * downtime_factor
    )

    # ------------------------------------------------------------------
    # DEFERRED / INCREMENTAL PRODUCTION
    # ------------------------------------------------------------------

    df["Deferred_Oil_bbl"] = (
        df["Potential_Oil_bbl"]
        - df["Actual_Oil_bbl"]
    )

    # Numerical noise protection.
    df["Deferred_Oil_bbl"] = (
        df["Deferred_Oil_bbl"]
        .where(
            df["Deferred_Oil_bbl"].abs() >= 1e-10,
            0.0,
        )
    )

    df["Downtime_Deferred_Oil_bbl"] = (
        df["Intervention_Adjusted_Oil_bbl"]
        * (
            df["Effective_Downtime_Hours"]
            / df["Available_hr"].replace(0, np.nan)
        )
    ).fillna(0.0)

    df["Intervention_Recovery_Oil_bbl"] = (
        df["Intervention_Impact_bbl"]
        .clip(lower=0.0)
    )

    df["Intervention_Production_Loss_bbl"] = (
        (-df["Intervention_Impact_bbl"])
        .clip(lower=0.0)
    )

    df["Production_Impact_bbl"] = (
        df["Actual_Oil_bbl"]
        - df["Baseline_Oil_bbl"]
    )

    # ------------------------------------------------------------------
    # PERFORMANCE METRICS
    # ------------------------------------------------------------------

    df["Production_Availability_pct"] = (
        downtime_factor * 100.0
    )

    df["Production_Efficiency_pct"] = np.where(
        df["Potential_Oil_bbl"] > 0,
        (
            df["Actual_Oil_bbl"]
            / df["Potential_Oil_bbl"]
        )
        * 100.0,
        0.0,
    )

    # Flag whether the day experienced any production-impacting event.
    df["Production_Impact_Flag"] = (
        (
            df["Effective_Downtime_Hours"] > 0
        )
        | (
            df["Intervention_Flag"] == 1
        )
    ).astype(int)

    return df


# ---------------------------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------------------------

def build_output(df: pd.DataFrame) -> pd.DataFrame:

    columns = [
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
    ]

    output = df[columns].copy()

    output["Date"] = pd.to_datetime(
        output["Date"]
    ).dt.strftime("%Y-%m-%d")

    numeric_columns = [
        "Potential_Oil_bbl",
        "Baseline_Oil_bbl",
        "Downtime_Hours",
        "Effective_Downtime_Hours",
        "Downtime_Deferred_Oil_bbl",
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
    ]

    output[numeric_columns] = output[numeric_columns].round(4)

    return output.sort_values(
        ["Date", "Well_ID"]
    ).reset_index(drop=True)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def run_qa(
    output: pd.DataFrame,
    production: pd.DataFrame,
    downtime: pd.DataFrame,
    intervention: pd.DataFrame,
) -> None:

    print("\n" + "=" * 72)
    print("PHASE 4D — PRODUCTION IMPACT QA")
    print("=" * 72)

    # ---------------------------------------------------------------
    # Row-level structural QA
    # ---------------------------------------------------------------

    print(f"Rows: {len(output):,}")

    expected_rows = len(production)
    print(f"Expected baseline rows: {expected_rows:,}")

    assert len(output) == expected_rows

    duplicate_days = output.duplicated(
        ["Date", "Well_ID"]
    ).sum()

    print(f"Duplicate well-days: {duplicate_days:,}")

    assert duplicate_days == 0

    null_values = int(
        output.isna().sum().sum()
    )

    print(f"Null values: {null_values:,}")

    # Intervention ID is legitimately null on non-intervention days.
    # Therefore perform a targeted null test instead.
    required_columns = [
        "Date",
        "Well_ID",
        "Potential_Oil_bbl",
        "Baseline_Oil_bbl",
        "Actual_Oil_bbl",
        "Deferred_Oil_bbl",
    ]

    required_nulls = int(
        output[required_columns]
        .isna()
        .sum()
        .sum()
    )

    print(
        "Required-column null values: "
        f"{required_nulls:,}"
    )

    assert required_nulls == 0

    # ---------------------------------------------------------------
    # Production reconciliation
    # ---------------------------------------------------------------

    reconciliation = (
        output["Potential_Oil_bbl"]
        - output["Actual_Oil_bbl"]
        - output["Deferred_Oil_bbl"]
    )

    max_reconciliation_error = float(
        reconciliation.abs().max()
    )

    print(
        "Maximum potential/actual/deferred "
        f"reconciliation error: "
        f"{max_reconciliation_error:.10f}"
    )

    assert max_reconciliation_error <= 0.01

    # ---------------------------------------------------------------
    # Baseline integrity
    # ---------------------------------------------------------------

    production_check = production.copy()
    production_check["Date"] = pd.to_datetime(
        production_check["Date"]
    )

    output_check = output.copy()
    output_check["Date"] = pd.to_datetime(
        output_check["Date"]
    )

    baseline_compare = output_check.merge(
        production_check[
            [
                "Date",
                "Well_ID",
                "Potential_Oil_bbl",
                "Oil_bbl",
            ]
        ],
        on=["Date", "Well_ID"],
        how="inner",
        validate="one_to_one",
        suffixes=("_impact", "_raw"),
    )

    potential_error = (
        baseline_compare["Potential_Oil_bbl_impact"]
        - baseline_compare["Potential_Oil_bbl_raw"]
    ).abs().max()

    oil_error = (
        baseline_compare["Baseline_Oil_bbl"]
        - baseline_compare["Oil_bbl"]
    ).abs().max()

    print(
        "Maximum Potential Oil baseline difference: "
        f"{potential_error:.10f}"
    )

    print(
        "Maximum Baseline Oil difference: "
        f"{oil_error:.10f}"
    )

    assert potential_error <= 0.01
    assert oil_error <= 0.01

    # ---------------------------------------------------------------
    # Physical constraints
    # ---------------------------------------------------------------

    negative_actual = (
        output["Actual_Oil_bbl"] < 0
    ).sum()

    negative_deferred = (
        output["Deferred_Oil_bbl"] < 0
    ).sum()

    print(
        f"Negative Actual Oil rows: "
        f"{negative_actual:,}"
    )

    print(
        f"Negative Deferred Oil rows: "
        f"{negative_deferred:,}"
    )

    # Negative deferred oil is permitted when an intervention produces
    # more than potential production. It represents an incremental
    # production opportunity rather than deferment.
    assert negative_actual == 0

    # Downtime must never exceed available time.
    downtime_violation = (
        output["Effective_Downtime_Hours"]
        > output["Available_hr"]
    ).sum()

    print(
        "Downtime > Available Hours: "
        f"{downtime_violation:,}"
    )

    assert downtime_violation == 0

    # ---------------------------------------------------------------
    # Intervention QA
    # ---------------------------------------------------------------

    completed_count = (
        intervention["Status"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("completed")
        .sum()
    )

    cancelled_count = (
        intervention["Status"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("cancelled")
        .sum()
    )

    impact_days = (
        output["Intervention_Flag"] == 1
    ).sum()

    print(
        f"Completed interventions: {completed_count:,}"
    )

    print(
        f"Cancelled interventions: {cancelled_count:,}"
    )

    print(
        f"Intervention-impact days: {impact_days:,}"
    )

    # ---------------------------------------------------------------
    # Field-level reconciliation
    # ---------------------------------------------------------------

    potential_total = (
        output["Potential_Oil_bbl"].sum()
    )

    actual_total = (
        output["Actual_Oil_bbl"].sum()
    )

    deferred_total = (
        output["Deferred_Oil_bbl"].sum()
    )

    field_difference = (
        potential_total
        - actual_total
        - deferred_total
    )

    print("\nFIELD PRODUCTION RECONCILIATION")

    print(
        f"Potential Oil: "
        f"{potential_total:,.2f} bbl"
    )

    print(
        f"Actual Oil: "
        f"{actual_total:,.2f} bbl"
    )

    print(
        f"Deferred / Net Impact: "
        f"{deferred_total:,.2f} bbl"
    )

    print(
        f"Reconciliation Difference: "
        f"{field_difference:,.10f} bbl"
    )

    assert abs(field_difference) <= 0.01

    print("\nQA STATUS: PASS")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:

    print("=" * 72)
    print("PHASE 4D — PRODUCTION IMPACT & DEFERRED PRODUCTION ENGINE")
    print("=" * 72)

    print(f"\nProject root: {PROJECT_ROOT}")
    print(f"Output path : {OUTPUT_PATH}")

    production, downtime, intervention = load_data()

    print("\n[1/5] Inputs loaded")
    print(
        f"      Production rows: "
        f"{len(production):,}"
    )
    print(
        f"      Downtime events: "
        f"{len(downtime):,}"
    )
    print(
        f"      Intervention events: "
        f"{len(intervention):,}"
    )

    print("\n[2/5] Aggregating downtime events")

    downtime_daily = build_downtime_daily(
        downtime
    )

    print(
        f"      Affected well-days: "
        f"{len(downtime_daily):,}"
    )

    print("\n[3/5] Expanding completed interventions")

    intervention_expanded = expand_interventions(
        intervention
    )

    print(
        f"      Intervention-days: "
        f"{len(intervention_expanded):,}"
    )

    intervention_daily = aggregate_interventions(
        intervention_expanded
    )

    print("\n[4/5] Calculating daily production impact")

    result = calculate_production_impact(
        production,
        downtime_daily,
        intervention_daily,
    )

    output = build_output(result)

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        f"      Output rows: "
        f"{len(output):,}"
    )

    print(
        f"      Output: "
        f"{OUTPUT_PATH}"
    )

    print("\n[5/5] Running QA")

    run_qa(
        output,
        production,
        downtime,
        intervention,
    )

    print("\n" + "=" * 72)
    print("PHASE 4D COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()