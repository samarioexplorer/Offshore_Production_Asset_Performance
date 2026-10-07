from pathlib import Path
import sys

import numpy as np
import pandas as pd


# ============================================================================
# PHASE 4E — INTEGRATED DATA VALIDATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "validation"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------

EXPECTED_COUNTS = {
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

PRODUCER_COUNT = 24
INJECTOR_COUNT = 6

TOLERANCE_BBL = 0.01


# ----------------------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------------------

results = []


def record(check_id, category, description, actual, expected, status, notes=""):
    results.append(
        {
            "Check_ID": check_id,
            "Category": category,
            "Description": description,
            "Actual": actual,
            "Expected": expected,
            "Status": status,
            "Notes": notes,
        }
    )


def load_csv(name, folder):
    path = folder / f"{name}.csv"

    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    return pd.read_csv(path)


def assert_columns(df, required_columns, name):
    missing = [c for c in required_columns if c not in df.columns]

    record(
        f"SCHEMA-{name}",
        "Schema",
        f"{name} required columns",
        len(missing),
        0,
        "PASS" if not missing else "FAIL",
        "Missing: " + ", ".join(missing) if missing else "",
    )


# ----------------------------------------------------------------------------
# Main validation
# ----------------------------------------------------------------------------

def main():

    print("=" * 80)
    print("PHASE 4E — INTEGRATED DATA VALIDATION")
    print("=" * 80)
    print()
    print(f"Project root: {PROJECT_ROOT}")
    print()

    # ========================================================================
    # 1. LOAD DATA
    # ========================================================================

    print("[1/7] Loading datasets")

    dim_date = load_csv("Dim_Date", RAW_DIR)
    dim_field = load_csv("Dim_Field", RAW_DIR)
    dim_manifold = load_csv("Dim_Manifold", RAW_DIR)
    dim_well = load_csv("Dim_Well", RAW_DIR)
    dim_equipment = load_csv("Dim_Equipment", RAW_DIR)
    dim_failure = load_csv("Dim_Failure_Cause", RAW_DIR)
    dim_intervention = load_csv("Dim_Intervention", RAW_DIR)
    dim_scenario = load_csv("Dim_Scenario", RAW_DIR)

    production = load_csv("Fact_Production_Daily", RAW_DIR)
    downtime = load_csv("Fact_Downtime_Event", RAW_DIR)
    intervention = load_csv("Fact_Intervention_Event", RAW_DIR)
    impact = load_csv("Fact_Production_Impact_Daily", PROCESSED_DIR)

    print("      All required datasets loaded")
    print()

    # ========================================================================
    # 2. ROW COUNTS
    # ========================================================================

    print("[2/7] Validating row counts")

    datasets = {
        "Dim_Date": dim_date,
        "Dim_Field": dim_field,
        "Dim_Manifold": dim_manifold,
        "Dim_Well": dim_well,
        "Dim_Equipment": dim_equipment,
        "Dim_Failure_Cause": dim_failure,
        "Dim_Intervention": dim_intervention,
        "Dim_Scenario": dim_scenario,
        "Fact_Production_Daily": production,
        "Fact_Downtime_Event": downtime,
        "Fact_Intervention_Event": intervention,
        "Fact_Production_Impact_Daily": impact,
    }

    for name, df in datasets.items():
        actual = len(df)
        expected = EXPECTED_COUNTS[name]

        record(
            f"COUNT-{name}",
            "Row Count",
            f"{name} row count",
            actual,
            expected,
            "PASS" if actual == expected else "FAIL",
        )

    # ========================================================================
    # 3. SCHEMA VALIDATION
    # ========================================================================

    print("[3/7] Validating schemas")

    assert_columns(
        dim_well,
        [
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
        "Dim_Well",
    )

    assert_columns(
        production,
        [
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
        "Fact_Production_Daily",
    )

    assert_columns(
        downtime,
        [
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
        "Fact_Downtime_Event",
    )

    assert_columns(
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

    assert_columns(
        impact,
        [
            "Date",
            "Well_ID",
            "Potential_Oil_bbl",
            "Baseline_Oil_bbl",
            "Actual_Oil_bbl",
            "Deferred_Oil_bbl",
            "Effective_Downtime_Hours",
            "Available_hr",
            "Production_Impact_bbl",
        ],
        "Fact_Production_Impact_Daily",
    )

    # ========================================================================
    # 4. REFERENTIAL INTEGRITY
    # ========================================================================

    print("[4/7] Validating referential integrity")

    producer_wells = set(
        dim_well.loc[dim_well["Well_Type"] == "Producer", "Well_ID"]
    )

    all_wells = set(dim_well["Well_ID"])
    equipment_ids = set(dim_equipment["Equipment_ID"])
    failure_ids = set(dim_failure["Failure_Cause_ID"])
    intervention_type_ids = set(
        dim_intervention["Intervention_Type_ID"]
    )
    manifold_ids = set(dim_manifold["Manifold_ID"])

    # Producer count
    record(
        "REF-001",
        "Referential Integrity",
        "Producer well count",
        len(producer_wells),
        PRODUCER_COUNT,
        "PASS" if len(producer_wells) == PRODUCER_COUNT else "FAIL",
    )

    # Injector count
    injector_wells = set(
        dim_well.loc[dim_well["Well_Type"] == "Injector", "Well_ID"]
    )

    record(
        "REF-002",
        "Referential Integrity",
        "Injector well count",
        len(injector_wells),
        INJECTOR_COUNT,
        "PASS" if len(injector_wells) == INJECTOR_COUNT else "FAIL",
    )

    # Production wells
    production_wells = set(production["Well_ID"])

    orphan_production_wells = production_wells - producer_wells

    record(
        "REF-003",
        "Referential Integrity",
        "Production wells exist in producer dimension",
        len(orphan_production_wells),
        0,
        "PASS" if not orphan_production_wells else "FAIL",
    )

    # Downtime wells
    downtime_wells = set(downtime["Well_ID"])
    orphan_downtime_wells = downtime_wells - producer_wells

    record(
        "REF-004",
        "Referential Integrity",
        "Downtime wells exist in producer dimension",
        len(orphan_downtime_wells),
        0,
        "PASS" if not orphan_downtime_wells else "FAIL",
    )

    # Intervention wells
    intervention_wells = set(intervention["Well_ID"])
    orphan_intervention_wells = intervention_wells - producer_wells

    record(
        "REF-005",
        "Referential Integrity",
        "Intervention wells exist in producer dimension",
        len(orphan_intervention_wells),
        0,
        "PASS" if not orphan_intervention_wells else "FAIL",
    )

    # Impact wells
    impact_wells = set(impact["Well_ID"])
    orphan_impact_wells = impact_wells - producer_wells

    record(
        "REF-006",
        "Referential Integrity",
        "Impact wells exist in producer dimension",
        len(orphan_impact_wells),
        0,
        "PASS" if not orphan_impact_wells else "FAIL",
    )

    # Downtime equipment
    orphan_equipment = set(downtime["Equipment_ID"]) - equipment_ids

    record(
        "REF-007",
        "Referential Integrity",
        "Downtime equipment IDs exist",
        len(orphan_equipment),
        0,
        "PASS" if not orphan_equipment else "FAIL",
    )

    # Downtime failure causes
    orphan_failure = set(downtime["Failure_Cause_ID"]) - failure_ids

    record(
        "REF-008",
        "Referential Integrity",
        "Downtime failure-cause IDs exist",
        len(orphan_failure),
        0,
        "PASS" if not orphan_failure else "FAIL",
    )

    # Intervention types
    orphan_intervention_types = (
        set(intervention["Intervention_Type_ID"])
        - intervention_type_ids
    )

    record(
        "REF-009",
        "Referential Integrity",
        "Intervention type IDs exist",
        len(orphan_intervention_types),
        0,
        "PASS" if not orphan_intervention_types else "FAIL",
    )

    # Manifold references
    well_manifolds = set(
        dim_well.loc[
            dim_well["Well_Type"] == "Producer",
            "Manifold_ID",
        ]
    )

    orphan_manifolds = well_manifolds - manifold_ids

    record(
        "REF-010",
        "Referential Integrity",
        "Producer manifold IDs exist",
        len(orphan_manifolds),
        0,
        "PASS" if not orphan_manifolds else "FAIL",
    )

    # ========================================================================
    # 5. GRAIN / DUPLICATE VALIDATION
    # ========================================================================

    print("[5/7] Validating grain and duplicates")

    production_duplicates = production.duplicated(
        subset=["Date", "Well_ID"]
    ).sum()

    impact_duplicates = impact.duplicated(
        subset=["Date", "Well_ID"]
    ).sum()

    downtime_duplicates = downtime.duplicated(
        subset=["Downtime_ID"]
    ).sum()

    intervention_duplicates = intervention.duplicated(
        subset=["Intervention_ID"]
    ).sum()

    record(
        "GRAIN-001",
        "Grain",
        "Production duplicate well-days",
        production_duplicates,
        0,
        "PASS" if production_duplicates == 0 else "FAIL",
    )

    record(
        "GRAIN-002",
        "Grain",
        "Impact duplicate well-days",
        impact_duplicates,
        0,
        "PASS" if impact_duplicates == 0 else "FAIL",
    )

    record(
        "GRAIN-003",
        "Grain",
        "Downtime duplicate event IDs",
        downtime_duplicates,
        0,
        "PASS" if downtime_duplicates == 0 else "FAIL",
    )

    record(
        "GRAIN-004",
        "Grain",
        "Intervention duplicate event IDs",
        intervention_duplicates,
        0,
        "PASS" if intervention_duplicates == 0 else "FAIL",
    )

    # ========================================================================
    # 6. TEMPORAL VALIDATION
    # ========================================================================

    print("[6/7] Validating temporal integrity")

    production["Date"] = pd.to_datetime(production["Date"])
    downtime["Date"] = pd.to_datetime(downtime["Date"])
    intervention["Start_Date"] = pd.to_datetime(intervention["Start_Date"])
    intervention["End_Date"] = pd.to_datetime(intervention["End_Date"])
    impact["Date"] = pd.to_datetime(impact["Date"])

    invalid_intervention_dates = (
        intervention["End_Date"] < intervention["Start_Date"]
    ).sum()

    record(
        "TIME-001",
        "Temporal Integrity",
        "Intervention end date before start date",
        invalid_intervention_dates,
        0,
        "PASS" if invalid_intervention_dates == 0 else "FAIL",
    )

    production_min = production["Date"].min()
    production_max = production["Date"].max()

    impact_min = impact["Date"].min()
    impact_max = impact["Date"].max()

    record(
        "TIME-002",
        "Temporal Integrity",
        "Impact start date equals production start date",
        str(impact_min.date()),
        str(production_min.date()),
        "PASS" if impact_min == production_min else "FAIL",
    )

    record(
        "TIME-003",
        "Temporal Integrity",
        "Impact end date equals production end date",
        str(impact_max.date()),
        str(production_max.date()),
        "PASS" if impact_max == production_max else "FAIL",
    )

    # Every production well-day must exist in impact
    production_keys = set(
        zip(
            production["Date"],
            production["Well_ID"],
        )
    )

    impact_keys = set(
        zip(
            impact["Date"],
            impact["Well_ID"],
        )
    )

    missing_impact_keys = production_keys - impact_keys
    extra_impact_keys = impact_keys - production_keys

    record(
        "TIME-004",
        "Temporal Integrity",
        "Production well-days missing from impact",
        len(missing_impact_keys),
        0,
        "PASS" if not missing_impact_keys else "FAIL",
    )

    record(
        "TIME-005",
        "Temporal Integrity",
        "Impact well-days absent from production",
        len(extra_impact_keys),
        0,
        "PASS" if not extra_impact_keys else "FAIL",
    )

    # ========================================================================
    # 7. END-TO-END PRODUCTION RECONCILIATION
    # ========================================================================

    print("[7/7] Running end-to-end production reconciliation")

    # Baseline production versus impact layer
    merged = production[
        [
            "Date",
            "Well_ID",
            "Potential_Oil_bbl",
            "Oil_bbl",
        ]
    ].merge(
        impact[
            [
                "Date",
                "Well_ID",
                "Potential_Oil_bbl",
                "Baseline_Oil_bbl",
                "Actual_Oil_bbl",
                "Deferred_Oil_bbl",
            ]
        ],
        on=["Date", "Well_ID"],
        how="outer",
        indicator=True,
    )

    missing_joins = (merged["_merge"] != "both").sum()

    record(
        "REC-001",
        "Reconciliation",
        "Production-to-impact joins",
        missing_joins,
        0,
        "PASS" if missing_joins == 0 else "FAIL",
    )

    potential_difference = (
        merged["Potential_Oil_bbl_x"]
        - merged["Potential_Oil_bbl_y"]
    ).abs().max()

    baseline_difference = (
        merged["Oil_bbl"]
        - merged["Baseline_Oil_bbl"]
    ).abs().max()

    record(
        "REC-002",
        "Reconciliation",
        "Potential oil baseline difference",
        round(float(potential_difference), 6),
        f"<= {TOLERANCE_BBL}",
        "PASS"
        if potential_difference <= TOLERANCE_BBL
        else "FAIL",
    )

    record(
        "REC-003",
        "Reconciliation",
        "Baseline oil difference",
        round(float(baseline_difference), 6),
        f"<= {TOLERANCE_BBL}",
        "PASS"
        if baseline_difference <= TOLERANCE_BBL
        else "FAIL",
    )

    # Row-level reconciliation
    row_reconciliation = (
        impact["Potential_Oil_bbl"]
        - impact["Actual_Oil_bbl"]
        - impact["Deferred_Oil_bbl"]
    ).abs().max()

    record(
        "REC-004",
        "Reconciliation",
        "Maximum row-level production reconciliation error",
        round(float(row_reconciliation), 6),
        f"<= {TOLERANCE_BBL}",
        "PASS"
        if row_reconciliation <= TOLERANCE_BBL
        else "FAIL",
    )

    # Field reconciliation
    field_potential = impact["Potential_Oil_bbl"].sum()
    field_actual = impact["Actual_Oil_bbl"].sum()
    field_deferred = impact["Deferred_Oil_bbl"].sum()

    field_difference = (
        field_potential
        - field_actual
        - field_deferred
    )

    record(
        "REC-005",
        "Reconciliation",
        "Field-level potential = actual + deferred",
        round(float(field_difference), 6),
        f"<= {TOLERANCE_BBL}",
        "PASS"
        if abs(field_difference) <= TOLERANCE_BBL
        else "FAIL",
    )

    # ------------------------------------------------------------------------
    # Production impact sanity checks
    # ------------------------------------------------------------------------

    negative_actual = (impact["Actual_Oil_bbl"] < 0).sum()

    record(
        "REC-006",
        "Reconciliation",
        "Negative actual oil rows",
        negative_actual,
        0,
        "PASS" if negative_actual == 0 else "FAIL",
    )

    downtime_over_available = (
        impact["Effective_Downtime_Hours"]
        > impact["Available_hr"]
        + 1e-9
    ).sum()

    record(
        "REC-007",
        "Reconciliation",
        "Effective downtime exceeds available hours",
        downtime_over_available,
        0,
        "PASS" if downtime_over_available == 0 else "FAIL",
    )

    # Negative deferred oil is allowed because intervention recovery can exceed
    # 100 percent.
    negative_deferred = (impact["Deferred_Oil_bbl"] < 0).sum()

    record(
        "REC-008",
        "Reconciliation",
        "Negative deferred oil rows",
        negative_deferred,
        "Allowed",
        "PASS",
        "Negative values represent incremental production above potential.",
    )

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================

    results_df = pd.DataFrame(results)

    validation_path = OUTPUT_DIR / "phase_4_integrated_validation.csv"
    results_df.to_csv(validation_path, index=False)

    total_checks = len(results_df)
    failed_checks = (results_df["Status"] == "FAIL").sum()
    passed_checks = (results_df["Status"] == "PASS").sum()

    print()
    print("=" * 80)
    print("PHASE 4E — VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total checks : {total_checks}")
    print(f"Passed       : {passed_checks}")
    print(f"Failed       : {failed_checks}")
    print()

    if failed_checks == 0:
        print("QA STATUS: PASS")
        print()
        print("PHASE 4E COMPLETE")
    else:
        print("QA STATUS: FAIL")
        print()
        print("Review failed checks before proceeding.")

        failed = results_df[results_df["Status"] == "FAIL"]

        print()
        print("FAILED CHECKS:")
        print(failed.to_string(index=False))

        sys.exit(1)

    print()
    print(f"Validation report: {validation_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()