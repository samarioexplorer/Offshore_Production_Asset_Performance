from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW = PROJECT_ROOT / "data" / "raw"
PROCESSED = PROJECT_ROOT / "data" / "processed"

production_file = RAW / "Fact_Production_Daily.csv"
intervention_file = RAW / "Fact_Intervention_Event.csv"
impact_file = PROCESSED / "Fact_Production_Impact_Daily.csv"


print("=" * 72)
print("QA-21 - PRODUCTION IMPACT OUTPUT INTEGRITY")
print("=" * 72)


# ----------------------------------------------------------------------
# LOAD
# ----------------------------------------------------------------------

production = pd.read_csv(production_file)
intervention = pd.read_csv(intervention_file)
impact = pd.read_csv(impact_file)

production["Date"] = pd.to_datetime(production["Date"])
impact["Date"] = pd.to_datetime(impact["Date"])

intervention["Start_Date"] = pd.to_datetime(
    intervention["Start_Date"]
)
intervention["End_Date"] = pd.to_datetime(
    intervention["End_Date"]
)

for df in [production, intervention, impact]:
    df["Well_ID"] = df["Well_ID"].astype(str)


# ----------------------------------------------------------------------
# QA-21A - OUTPUT SCHEMA
# ----------------------------------------------------------------------

required_columns = [
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

missing_columns = [
    c for c in required_columns
    if c not in impact.columns
]

extra_columns = [
    c for c in impact.columns
    if c not in required_columns
]


# ----------------------------------------------------------------------
# QA-21B - GRAIN
# ----------------------------------------------------------------------

duplicate_grain = impact.duplicated(
    subset=["Date", "Well_ID"]
).sum()

production_grain = production.duplicated(
    subset=["Date", "Well_ID"]
).sum()

expected_rows = len(production)
actual_rows = len(impact)

row_count_match = (
    expected_rows == actual_rows
)

grain_match = (
    duplicate_grain == 0
    and production_grain == 0
)


# ----------------------------------------------------------------------
# QA-21C - PRODUCTION WELL REFERENTIAL INTEGRITY
# ----------------------------------------------------------------------

production_wells = set(
    production["Well_ID"].dropna().unique()
)

impact_wells = set(
    impact["Well_ID"].dropna().unique()
)

orphan_impact_wells = sorted(
    impact_wells - production_wells
)

missing_production_wells = sorted(
    production_wells - impact_wells
)

date_min_match = (
    impact["Date"].min() == production["Date"].min()
)

date_max_match = (
    impact["Date"].max() == production["Date"].max()
)


# ----------------------------------------------------------------------
# QA-21D - INTERVENTION REFERENTIAL INTEGRITY
# ----------------------------------------------------------------------

intervention_ids = set(
    intervention["Intervention_ID"]
    .dropna()
    .astype(str)
)

impact_intervention_ids = set(
    impact.loc[
        impact["Intervention_Flag"] == 1,
        "Intervention_ID"
    ]
    .dropna()
    .astype(str)
)

orphan_intervention_ids = sorted(
    impact_intervention_ids - intervention_ids
)

missing_intervention_ids = sorted(
    intervention_ids - impact_intervention_ids
)

# Intervention IDs should only appear when the flag is 1.
flag_zero_with_id = (
    (
        impact["Intervention_Flag"] == 0
    )
    & impact["Intervention_ID"].notna()
).sum()


# ----------------------------------------------------------------------
# QA-21E - NULL / DEFAULT INTEGRITY
# ----------------------------------------------------------------------

critical_columns = [
    "Date",
    "Well_ID",
    "Potential_Oil_bbl",
    "Baseline_Oil_bbl",
    "Downtime_Hours",
    "Effective_Downtime_Hours",
    "Available_hr",
    "Downtime_Event_Count",
    "Actual_Oil_bbl",
    "Deferred_Oil_bbl",
    "Production_Impact_bbl",
    "Production_Availability_pct",
    "Production_Efficiency_pct",
    "Production_Impact_Flag",
]

null_counts = impact[critical_columns].isna().sum()
critical_nulls = int(null_counts.sum())


# ----------------------------------------------------------------------
# QA-21F - NUMERIC RANGE INTEGRITY
# ----------------------------------------------------------------------

negative_potential = (
    impact["Potential_Oil_bbl"] < 0
).sum()

negative_baseline = (
    impact["Baseline_Oil_bbl"] < 0
).sum()

negative_actual = (
    impact["Actual_Oil_bbl"] < 0
).sum()

negative_downtime = (
    impact["Downtime_Hours"] < 0
).sum()

negative_effective = (
    impact["Effective_Downtime_Hours"] < 0
).sum()

effective_over_available = (
    impact["Effective_Downtime_Hours"]
    > impact["Available_hr"] + 1e-6
).sum()

negative_available = (
    impact["Available_hr"] < 0
).sum()

negative_event_count = (
    impact["Downtime_Event_Count"] < 0
).sum()

non_integer_event_count = (
    impact["Downtime_Event_Count"]
    % 1 != 0
).sum()

negative_intervention_cost = (
    impact["Intervention_Cost_USD"] < 0
).sum()

negative_intervention_days = (
    impact["Intervention_Days"] < 0
).sum()


# ----------------------------------------------------------------------
# QA-21G - PERCENTAGE / RATE INTEGRITY
# ----------------------------------------------------------------------

recovery_below_zero = (
    impact["Intervention_Recovery_pct"] < 0
).sum()

availability_below_zero = (
    impact["Production_Availability_pct"] < -1e-6
).sum()

availability_above_100 = (
    impact["Production_Availability_pct"] > 100.000001
).sum()

efficiency_below_zero = (
    impact["Production_Efficiency_pct"] < -1e-6
).sum()

intervention_flag_values = sorted(
    impact["Intervention_Flag"]
    .dropna()
    .unique()
    .tolist()
)

impact_flag_values = sorted(
    impact["Production_Impact_Flag"]
    .dropna()
    .unique()
    .tolist()
)


# ----------------------------------------------------------------------
# QA-21H - BASELINE PRODUCTION RECONCILIATION
# ----------------------------------------------------------------------

baseline_compare = impact.merge(
    production[
        [
            "Date",
            "Well_ID",
            "Oil_bbl",
            "Potential_Oil_bbl",
            "Available_hr",
        ]
    ],
    on=["Date", "Well_ID"],
    how="outer",
    indicator=True,
)

baseline_compare["Baseline_Oil_bbl"] = (
    baseline_compare["Baseline_Oil_bbl"].fillna(0)
)

baseline_compare["Oil_bbl"] = (
    baseline_compare["Oil_bbl"].fillna(0)
)

baseline_compare["Potential_Oil_bbl_x"] = (
    baseline_compare["Potential_Oil_bbl_x"].fillna(0)
)

baseline_compare["Potential_Oil_bbl_y"] = (
    baseline_compare["Potential_Oil_bbl_y"].fillna(0)
)

baseline_oil_diff = (
    baseline_compare["Baseline_Oil_bbl"]
    - baseline_compare["Oil_bbl"]
).abs()

potential_diff = (
    baseline_compare["Potential_Oil_bbl_x"]
    - baseline_compare["Potential_Oil_bbl_y"]
).abs()

available_diff = (
    baseline_compare["Available_hr_x"]
    - baseline_compare["Available_hr_y"]
).abs()

baseline_orphans = (
    baseline_compare["_merge"] != "both"
).sum()

baseline_oil_mismatch = (
    baseline_oil_diff > 1e-4
).sum()

potential_mismatch = (
    potential_diff > 1e-4
).sum()

available_mismatch = (
    available_diff > 1e-4
).sum()


# ----------------------------------------------------------------------
# QA-21I - INTERVENTION FLAG CONSISTENCY
# ----------------------------------------------------------------------

intervention_flag_nonbinary = (
    ~impact["Intervention_Flag"].isin([0, 1])
).sum()

intervention_id_when_flag_one = (
    (
        impact["Intervention_Flag"] == 1
    )
    & impact["Intervention_ID"].isna()
).sum()

intervention_recovery_without_flag = (
    (
        impact["Intervention_Flag"] == 0
    )
    & (
        impact["Intervention_Recovery_pct"] != 100
    )
).sum()


# ----------------------------------------------------------------------
# QA-21J - PRODUCTION IMPACT FLAG CONSISTENCY
# ----------------------------------------------------------------------

expected_impact_flag = (
    (
        impact["Effective_Downtime_Hours"] > 0
    )
    | (
        impact["Intervention_Flag"] == 1
    )
).astype(int)

impact_flag_mismatch = (
    expected_impact_flag
    != impact["Production_Impact_Flag"]
).sum()


# ----------------------------------------------------------------------
# QA-21K - DISTRIBUTION / TOTALS
# ----------------------------------------------------------------------

print()
print("OUTPUT SUMMARY")
print("-" * 72)
print(f"Rows:                                {len(impact):,}")
print(f"Distinct wells:                      {impact['Well_ID'].nunique():,}")
print(f"Distinct dates:                      {impact['Date'].nunique():,}")
print(
    f"Date range:                          "
    f"{impact['Date'].min().date()} to "
    f"{impact['Date'].max().date()}"
)

print()
print("PRODUCTION TOTALS")
print("-" * 72)
print(
    f"Potential Oil:                      "
    f"{impact['Potential_Oil_bbl'].sum():,.2f}"
)
print(
    f"Baseline Oil:                       "
    f"{impact['Baseline_Oil_bbl'].sum():,.2f}"
)
print(
    f"Actual Oil:                         "
    f"{impact['Actual_Oil_bbl'].sum():,.2f}"
)
print(
    f"Deferred Oil:                       "
    f"{impact['Deferred_Oil_bbl'].sum():,.2f}"
)
print(
    f"Production Impact:                  "
    f"{impact['Production_Impact_bbl'].sum():,.2f}"
)

print()
print("INTERVENTION DISTRIBUTION")
print("-" * 72)
print(
    impact["Intervention_Flag"]
    .value_counts()
    .sort_index()
    .to_string()
)

print()
print("PRODUCTION IMPACT FLAG DISTRIBUTION")
print("-" * 72)
print(
    impact["Production_Impact_Flag"]
    .value_counts()
    .sort_index()
    .to_string()
)


# ----------------------------------------------------------------------
# RESULTS
# ----------------------------------------------------------------------

print()
print("=" * 72)
print("QA-21A - OUTPUT SCHEMA")
print("-" * 72)
print(f"Missing required columns:             {len(missing_columns)}")
print(f"Extra columns:                         {len(extra_columns)}")

print()
print("QA-21B - GRAIN")
print("-" * 72)
print(f"Expected production rows:             {expected_rows:,}")
print(f"Impact output rows:                   {actual_rows:,}")
print(f"Row count match:                      {row_count_match}")
print(f"Impact duplicate Date + Well_ID:      {duplicate_grain:,}")
print(f"Production duplicate Date + Well_ID:  {production_grain:,}")

print()
print("QA-21C - PRODUCTION RI")
print("-" * 72)
print(f"Orphan impact wells:                  {len(orphan_impact_wells)}")
print(f"Missing production wells:             {len(missing_production_wells)}")
print(f"Minimum date matches:                 {date_min_match}")
print(f"Maximum date matches:                 {date_max_match}")

print()
print("QA-21D - INTERVENTION RI")
print("-" * 72)
print(f"Orphan intervention IDs:              {len(orphan_intervention_ids)}")
print(f"Interventions absent from impact:     {len(missing_intervention_ids)}")
print(f"Flag 0 with Intervention_ID:          {flag_zero_with_id}")

print()
print("QA-21E - NULL INTEGRITY")
print("-" * 72)
print(f"Critical null cells:                  {critical_nulls}")

print()
print("QA-21F - NUMERIC INTEGRITY")
print("-" * 72)
print(f"Negative Potential Oil:               {negative_potential}")
print(f"Negative Baseline Oil:                {negative_baseline}")
print(f"Negative Actual Oil:                  {negative_actual}")
print(f"Negative Downtime Hours:              {negative_downtime}")
print(f"Negative Effective Downtime:          {negative_effective}")
print(f"Effective > Available:                {effective_over_available}")
print(f"Negative Available Hours:             {negative_available}")
print(f"Negative Event Count:                 {negative_event_count}")
print(f"Non-integer Event Count:              {non_integer_event_count}")
print(f"Negative Intervention Cost:            {negative_intervention_cost}")
print(f"Negative Intervention Days:            {negative_intervention_days}")

print()
print("QA-21G - PERCENTAGE / FLAG INTEGRITY")
print("-" * 72)
print(f"Recovery < 0:                         {recovery_below_zero}")
print(f"Availability < 0:                    {availability_below_zero}")
print(f"Availability > 100:                  {availability_above_100}")
print(f"Efficiency < 0:                      {efficiency_below_zero}")
print(f"Intervention Flag values:             {intervention_flag_values}")
print(f"Production Impact Flag values:        {impact_flag_values}")

print()
print("QA-21H - BASELINE RECONCILIATION")
print("-" * 72)
print(f"Date/Well orphans:                    {baseline_orphans}")
print(f"Baseline Oil mismatches:              {baseline_oil_mismatch}")
print(f"Potential Oil mismatches:             {potential_mismatch}")
print(f"Available Hours mismatches:           {available_mismatch}")

print()
print("QA-21I - INTERVENTION CONSISTENCY")
print("-" * 72)
print(f"Non-binary Intervention Flags:        {intervention_flag_nonbinary}")
print(f"Flag 1 without Intervention_ID:       {intervention_id_when_flag_one}")
print(
    "Flag 0 with Recovery != 100%:         "
    f"{intervention_recovery_without_flag}"
)

print()
print("QA-21J - IMPACT FLAG CONSISTENCY")
print("-" * 72)
print(f"Production Impact Flag mismatches:    {impact_flag_mismatch}")


# ----------------------------------------------------------------------
# STATUS LOGIC
# ----------------------------------------------------------------------

qa21a = (
    len(missing_columns) == 0
)

qa21b = (
    row_count_match
    and duplicate_grain == 0
    and production_grain == 0
)

qa21c = (
    len(orphan_impact_wells) == 0
    and len(missing_production_wells) == 0
    and date_min_match
    and date_max_match
)

qa21d = (
    len(orphan_intervention_ids) == 0
    and flag_zero_with_id == 0
)

qa21e = (
    critical_nulls == 0
)

qa21f = (
    negative_potential == 0
    and negative_baseline == 0
    and negative_actual == 0
    and negative_downtime == 0
    and negative_effective == 0
    and effective_over_available == 0
    and negative_available == 0
    and negative_event_count == 0
    and non_integer_event_count == 0
    and negative_intervention_cost == 0
    and negative_intervention_days == 0
)

qa21g = (
    recovery_below_zero == 0
    and availability_below_zero == 0
    and availability_above_100 == 0
    and efficiency_below_zero == 0
    and set(intervention_flag_values).issubset({0, 1})
    and set(impact_flag_values).issubset({0, 1})
)

qa21h = (
    baseline_orphans == 0
    and baseline_oil_mismatch == 0
    and potential_mismatch == 0
    and available_mismatch == 0
)

qa21i = (
    intervention_flag_nonbinary == 0
    and intervention_id_when_flag_one == 0
    and intervention_recovery_without_flag == 0
)

qa21j = (
    impact_flag_mismatch == 0
)

overall = all([
    qa21a,
    qa21b,
    qa21c,
    qa21d,
    qa21e,
    qa21f,
    qa21g,
    qa21h,
    qa21i,
    qa21j,
])


print()
print("=" * 72)

statuses = [
    ("QA-21A", qa21a),
    ("QA-21B", qa21b),
    ("QA-21C", qa21c),
    ("QA-21D", qa21d),
    ("QA-21E", qa21e),
    ("QA-21F", qa21f),
    ("QA-21G", qa21g),
    ("QA-21H", qa21h),
    ("QA-21I", qa21i),
    ("QA-21J", qa21j),
]

for name, passed in statuses:
    print(
        f"{name} STATUS: "
        + ("PASS" if passed else "FAIL")
    )

print()
print(
    "QA-21 OVERALL STATUS: "
    + ("PASS" if overall else "FAIL")
)

print("=" * 72)
