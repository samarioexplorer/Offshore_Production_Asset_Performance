from pathlib import Path
import sys
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW = PROJECT_ROOT / "data" / "raw"
PROCESSED = PROJECT_ROOT / "data" / "processed"

production_file = RAW / "Fact_Production_Daily.csv"
downtime_file = RAW / "Fact_Downtime_Event.csv"
intervention_file = RAW / "Fact_Intervention_Event.csv"
impact_file = PROCESSED / "Fact_Production_Impact_Daily.csv"


print("=" * 72)
print("QA-20 - PRODUCTION IMPACT RECONCILIATION")
print("=" * 72)


# ----------------------------------------------------------------------
# LOAD SOURCE DATA
# ----------------------------------------------------------------------

production = pd.read_csv(production_file)
downtime = pd.read_csv(downtime_file)
intervention = pd.read_csv(intervention_file)
impact = pd.read_csv(impact_file)

production["Date"] = pd.to_datetime(production["Date"])
downtime["Date"] = pd.to_datetime(downtime["Date"])
intervention["Start_Date"] = pd.to_datetime(intervention["Start_Date"])
intervention["End_Date"] = pd.to_datetime(intervention["End_Date"])
impact["Date"] = pd.to_datetime(impact["Date"])

for df in [production, downtime, intervention, impact]:
    df["Well_ID"] = df["Well_ID"].astype(str)


# ----------------------------------------------------------------------
# QA-20A - EVENT -> DAILY DOWNTIME RECONCILIATION
# ----------------------------------------------------------------------

affected = (
    downtime["Production_Affected"]
    .astype(str)
    .str.strip()
    .str.lower()
    .isin(["yes", "y", "true", "1"])
)

downtime_expected = downtime.copy()
downtime_expected["Affected_Duration_hr"] = np.where(
    affected,
    downtime_expected["Duration_hr"],
    0.0,
)

daily_expected = (
    downtime_expected
    .groupby(["Date", "Well_ID"], as_index=False)
    .agg(
        Expected_Downtime_Hours=(
            "Affected_Duration_hr",
            "sum",
        ),
        Expected_Downtime_Event_Count=(
            "Downtime_ID",
            "nunique",
        ),
    )
)

daily_actual = impact[
    [
        "Date",
        "Well_ID",
        "Downtime_Hours",
        "Downtime_Event_Count",
    ]
].copy()

daily_actual = daily_actual[
    (daily_actual["Downtime_Hours"] > 0)
    | (daily_actual["Downtime_Event_Count"] > 0)
]

daily_compare = daily_expected.merge(
    daily_actual,
    on=["Date", "Well_ID"],
    how="outer",
    indicator=True,
)

daily_compare["Expected_Downtime_Hours"] = (
    daily_compare["Expected_Downtime_Hours"].fillna(0.0)
)

daily_compare["Downtime_Hours"] = (
    daily_compare["Downtime_Hours"].fillna(0.0)
)

daily_compare["Expected_Downtime_Event_Count"] = (
    daily_compare["Expected_Downtime_Event_Count"]
    .fillna(0)
    .astype(int)
)

daily_compare["Downtime_Event_Count"] = (
    daily_compare["Downtime_Event_Count"]
    .fillna(0)
    .astype(int)
)

duration_diff = (
    daily_compare["Expected_Downtime_Hours"]
    - daily_compare["Downtime_Hours"]
).abs()

event_count_diff = (
    daily_compare["Expected_Downtime_Event_Count"]
    - daily_compare["Downtime_Event_Count"]
).abs()

qa20a_missing = (daily_compare["_merge"] != "both").sum()
qa20a_duration_mismatch = (duration_diff > 1e-4).sum()
qa20a_event_mismatch = (event_count_diff != 0).sum()


# ----------------------------------------------------------------------
# QA-20B - EFFECTIVE DOWNTIME RECONCILIATION
# ----------------------------------------------------------------------

impact["Expected_Effective_Downtime_Hours"] = (
    impact["Downtime_Hours"]
    .clip(
        lower=0.0,
        upper=impact["Available_hr"],
    )
)

effective_diff = (
    impact["Expected_Effective_Downtime_Hours"]
    - impact["Effective_Downtime_Hours"]
).abs()

qa20b_mismatch = (effective_diff > 1e-4).sum()

availability_expected = np.where(
    impact["Available_hr"] > 0,
    (
        1.0
        - (
            impact["Effective_Downtime_Hours"]
            / impact["Available_hr"]
        )
    ) * 100.0,
    100.0,
)

availability_diff = (
    pd.Series(availability_expected)
    - impact["Production_Availability_pct"]
).abs()

qa20b_availability_mismatch = (
    availability_diff > 1e-3
).sum()


# ----------------------------------------------------------------------
# QA-20C - ACTUAL / DEFERRED PRODUCTION RECONCILIATION
# ----------------------------------------------------------------------

expected_actual = (
    impact["Baseline_Oil_bbl"]
    * (
        impact["Intervention_Recovery_pct"]
        / 100.0
    )
)

expected_actual = (
    expected_actual
    * np.clip(
        np.where(
            impact["Available_hr"] > 0,
            (
                1.0
                - (
                    impact["Effective_Downtime_Hours"]
                    / impact["Available_hr"]
                )
            ),
            1.0,
        ),
        0.0,
        1.0,
    )
)

actual_diff = (
    expected_actual
    - impact["Actual_Oil_bbl"]
).abs()

qa20c_actual_mismatch = (
    actual_diff > 1e-3
).sum()


expected_deferred = (
    impact["Potential_Oil_bbl"]
    - impact["Actual_Oil_bbl"]
)

deferred_diff = (
    expected_deferred
    - impact["Deferred_Oil_bbl"]
).abs()

qa20c_deferred_mismatch = (
    deferred_diff > 1e-3
).sum()


expected_downtime_deferred = (
    impact["Baseline_Oil_bbl"]
    * (
        impact["Intervention_Recovery_pct"]
        / 100.0
    )
    * (
        impact["Effective_Downtime_Hours"]
        / impact["Available_hr"].replace(0, np.nan)
    )
).fillna(0.0)

downtime_deferred_diff = (
    expected_downtime_deferred
    - impact["Downtime_Deferred_Oil_bbl"]
).abs()

qa20c_downtime_deferred_mismatch = (
    downtime_deferred_diff > 1e-3
).sum()


# ----------------------------------------------------------------------
# QA-20D - PRODUCTION IMPACT / EFFICIENCY / FLAG
# ----------------------------------------------------------------------

expected_impact = (
    impact["Actual_Oil_bbl"]
    - impact["Baseline_Oil_bbl"]
)

impact_diff = (
    expected_impact
    - impact["Production_Impact_bbl"]
).abs()

qa20d_impact_mismatch = (
    impact_diff > 1e-3
).sum()


expected_efficiency = np.where(
    impact["Potential_Oil_bbl"] > 0,
    (
        impact["Actual_Oil_bbl"]
        / impact["Potential_Oil_bbl"]
    ) * 100.0,
    0.0,
)

efficiency_diff = (
    pd.Series(expected_efficiency)
    - impact["Production_Efficiency_pct"]
).abs()

qa20d_efficiency_mismatch = (
    efficiency_diff > 1e-3
).sum()


expected_flag = (
    (
        impact["Effective_Downtime_Hours"] > 0
    )
    | (
        impact["Intervention_Flag"] == 1
    )
).astype(int)

qa20d_flag_mismatch = (
    expected_flag
    != impact["Production_Impact_Flag"]
).sum()


# ----------------------------------------------------------------------
# STRUCTURAL CHECKS
# ----------------------------------------------------------------------

duplicate_days = impact.duplicated(
    subset=["Date", "Well_ID"]
).sum()

expected_rows = len(production)

row_count_ok = len(impact) == expected_rows

negative_actual = (
    impact["Actual_Oil_bbl"] < -1e-6
).sum()

effective_over_available = (
    impact["Effective_Downtime_Hours"]
    > impact["Available_hr"] + 1e-6
).sum()

negative_deferred = (
    impact["Deferred_Oil_bbl"] < -1e-6
).sum()


# ----------------------------------------------------------------------
# RESULTS
# ----------------------------------------------------------------------

print()
print("QA-20A - EVENT -> DAILY DOWNTIME")
print("-" * 72)
print(f"Expected daily downtime rows:       {len(daily_expected):,}")
print(f"Actual populated daily rows:        {len(daily_actual):,}")
print(f"Missing/extra daily rows:            {qa20a_missing:,}")
print(f"Downtime hour mismatches:            {qa20a_duration_mismatch:,}")
print(f"Event count mismatches:              {qa20a_event_mismatch:,}")


print()
print("QA-20B - EFFECTIVE DOWNTIME")
print("-" * 72)
print(f"Effective downtime mismatches:       {qa20b_mismatch:,}")
print(f"Availability mismatches:             {qa20b_availability_mismatch:,}")


print()
print("QA-20C - ACTUAL / DEFERRED OIL")
print("-" * 72)
print(f"Actual Oil mismatches:               {qa20c_actual_mismatch:,}")
print(f"Deferred Oil mismatches:             {qa20c_deferred_mismatch:,}")
print(
    "Downtime Deferred Oil mismatches:    "
    f"{qa20c_downtime_deferred_mismatch:,}"
)


print()
print("QA-20D - PRODUCTION IMPACT METRICS")
print("-" * 72)
print(f"Production Impact mismatches:        {qa20d_impact_mismatch:,}")
print(f"Production Efficiency mismatches:    {qa20d_efficiency_mismatch:,}")
print(f"Production Impact Flag mismatches:   {qa20d_flag_mismatch:,}")


print()
print("STRUCTURAL CONTROLS")
print("-" * 72)
print(f"Production source rows:              {expected_rows:,}")
print(f"Impact output rows:                  {len(impact):,}")
print(f"Row count matches:                   {row_count_ok}")
print(f"Duplicate Date + Well_ID rows:       {duplicate_days:,}")
print(f"Negative Actual Oil rows:             {negative_actual:,}")
print(f"Effective > Available rows:           {effective_over_available:,}")
print(f"Negative Deferred Oil rows:           {negative_deferred:,}")


qa20a_pass = (
    qa20a_missing == 0
    and qa20a_duration_mismatch == 0
    and qa20a_event_mismatch == 0
)

qa20b_pass = (
    qa20b_mismatch == 0
    and qa20b_availability_mismatch == 0
)

qa20c_pass = (
    qa20c_actual_mismatch == 0
    and qa20c_deferred_mismatch == 0
    and qa20c_downtime_deferred_mismatch == 0
)

qa20d_pass = (
    qa20d_impact_mismatch == 0
    and qa20d_efficiency_mismatch == 0
    and qa20d_flag_mismatch == 0
)

structural_pass = (
    row_count_ok
    and duplicate_days == 0
    and negative_actual == 0
    and effective_over_available == 0
)


print()
print("=" * 72)

if qa20a_pass:
    print("QA-20A STATUS: PASS")
else:
    print("QA-20A STATUS: FAIL")

if qa20b_pass:
    print("QA-20B STATUS: PASS")
else:
    print("QA-20B STATUS: FAIL")

if qa20c_pass:
    print("QA-20C STATUS: PASS")
else:
    print("QA-20C STATUS: FAIL")

if qa20d_pass:
    print("QA-20D STATUS: PASS")
else:
    print("QA-20D STATUS: FAIL")

if structural_pass:
    print("STRUCTURAL STATUS: PASS")
else:
    print("STRUCTURAL STATUS: FAIL")

overall = (
    qa20a_pass
    and qa20b_pass
    and qa20c_pass
    and qa20d_pass
    and structural_pass
)

print()
print(
    "QA-20 OVERALL STATUS: "
    + ("PASS" if overall else "FAIL")
)

print("=" * 72)
