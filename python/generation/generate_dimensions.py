"""Generate Orion Deepwater field dimensions."""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from python.generation.config import (
    BASIN,
    DEVELOPMENT_TYPE,
    END_DATE,
    FIELD_ID,
    FIELD_NAME,
    FIRST_PRODUCTION_DATE,
    FPSO_NAME,
    INITIAL_WATER_CUT_MAX_PCT,
    INITIAL_WATER_CUT_MIN_PCT,
    INJECTOR_COUNT,
    MANIFOLD_COUNT,
    OPERATOR_TYPE,
    PRODUCER_COUNT,
    PRODUCER_DECLINE_MAX_PCT,
    PRODUCER_DECLINE_MIN_PCT,
    PRODUCER_INITIAL_OIL_RATE_MAX_BOPD,
    PRODUCER_INITIAL_OIL_RATE_MIN_BOPD,
    RANDOM_SEED,
    RAW_DATA_DIR,
    WATER_DEPTH_MAX_FT,
    WATER_DEPTH_MIN_FT,
    WATER_DEPTH_FT,
)


def generate_field() -> pd.DataFrame:
    """Generate the field dimension."""
    return pd.DataFrame(
        [
            {
                "Field_ID": FIELD_ID,
                "Field_Name": FIELD_NAME,
                "Basin": BASIN,
                "Development_Type": DEVELOPMENT_TYPE,
                "Water_Depth_ft": WATER_DEPTH_FT,
                "Operator_Type": OPERATOR_TYPE,
                "First_Production_Date": FIRST_PRODUCTION_DATE,
                "FPSO_Name": FPSO_NAME,
            }
        ]
    )


def generate_manifolds(rng: np.random.Generator) -> pd.DataFrame:
    """Generate subsea manifold dimension."""
    rows = []

    for index in range(1, MANIFOLD_COUNT + 1):
        manifold_id = f"M{index:02d}"

        installation_date = pd.Timestamp("2022-01-15") + timedelta(
            days=(index - 1) * 45
        )

        rows.append(
            {
                "Manifold_ID": manifold_id,
                "Manifold_Name": f"Orion Manifold {index:02d}",
                "Field_ID": FIELD_ID,
                "Water_Depth_ft": int(
                    rng.integers(WATER_DEPTH_MIN_FT, WATER_DEPTH_MAX_FT + 1)
                ),
                "Well_Count": PRODUCER_COUNT // MANIFOLD_COUNT,
                "Installation_Date": installation_date.strftime("%Y-%m-%d"),
                "Status": "Operational",
            }
        )

    return pd.DataFrame(rows)


def generate_wells(rng: np.random.Generator) -> pd.DataFrame:
    """Generate producer and injector wells."""
    rows = []

    wells_per_manifold = PRODUCER_COUNT // MANIFOLD_COUNT

    # Producers
    for index in range(1, PRODUCER_COUNT + 1):
        manifold_number = ((index - 1) // wells_per_manifold) + 1
        well_id = f"P{index:03d}"
        manifold_id = f"M{manifold_number:02d}"

        spud_date = pd.Timestamp("2021-06-01") + timedelta(
            days=int(rng.integers(0, 650))
        )

        first_production = pd.Timestamp("2023-01-18") + timedelta(
            days=int(rng.integers(0, 240))
        )

        rows.append(
            {
                "Well_ID": well_id,
                "Well_Name": f"Orion Producer {index:03d}",
                "Well_Type": "Producer",
                "Field_ID": FIELD_ID,
                "Manifold_ID": manifold_id,
                "Reservoir": rng.choice(["ORN-A", "ORN-B", "ORN-C"]),
                "Water_Depth_ft": int(
                    rng.integers(WATER_DEPTH_MIN_FT, WATER_DEPTH_MAX_FT + 1)
                ),
                "Spud_Date": spud_date.strftime("%Y-%m-%d"),
                "First_Production_Date": first_production.strftime("%Y-%m-%d"),
                "Well_Status": "Producing",
                "Initial_Oil_Rate_bopd": round(
                    float(
                        rng.uniform(
                            PRODUCER_INITIAL_OIL_RATE_MIN_BOPD,
                            PRODUCER_INITIAL_OIL_RATE_MAX_BOPD,
                        )
                    ),
                    1,
                ),
                "Initial_Gas_Rate_Mscfd": round(
                    float(rng.uniform(4500, 11000)),
                    1,
                ),
                "Decline_Rate_pct": round(
                    float(
                        rng.uniform(
                            PRODUCER_DECLINE_MIN_PCT,
                            PRODUCER_DECLINE_MAX_PCT,
                        )
                    ),
                    4,
                ),
                "Initial_Water_Cut_pct": round(
                    float(
                        rng.uniform(
                            INITIAL_WATER_CUT_MIN_PCT,
                            INITIAL_WATER_CUT_MAX_PCT,
                        )
                    ),
                    4,
                ),
                "Artificial_Lift_Type": rng.choice(
                    ["None", "None", "None", "ESP"]
                ),
            }
        )

    # Injectors
    for index in range(1, INJECTOR_COUNT + 1):
        well_id = f"I{index:03d}"
        manifold_number = ((index - 1) % MANIFOLD_COUNT) + 1

        spud_date = pd.Timestamp("2022-01-01") + timedelta(
            days=int(rng.integers(0, 300))
        )

        rows.append(
            {
                "Well_ID": well_id,
                "Well_Name": f"Orion Injector {index:03d}",
                "Well_Type": "Injector",
                "Field_ID": FIELD_ID,
                "Manifold_ID": f"M{manifold_number:02d}",
                "Reservoir": rng.choice(["ORN-A", "ORN-B", "ORN-C"]),
                "Water_Depth_ft": int(
                    rng.integers(WATER_DEPTH_MIN_FT, WATER_DEPTH_MAX_FT + 1)
                ),
                "Spud_Date": spud_date.strftime("%Y-%m-%d"),
                "First_Production_Date": "",
                "Well_Status": "Producing",
                "Initial_Oil_Rate_bopd": 0.0,
                "Initial_Gas_Rate_Mscfd": 0.0,
                "Decline_Rate_pct": 0.0,
                "Initial_Water_Cut_pct": 0.0,
                "Artificial_Lift_Type": "None",
            }
        )

    return pd.DataFrame(rows)


def generate_equipment(rng: np.random.Generator) -> pd.DataFrame:
    """Generate FPSO and subsea equipment."""
    equipment = [
        (
            "FPSO-001",
            "FPSO Orion",
            "Facility",
            "FPSO",
            "",
            "Critical",
        ),
        (
            "SEP-001",
            "Production Separator",
            "Process Equipment",
            "Separation",
            "FPSO-001",
            "Critical",
        ),
        (
            "COMP-001",
            "Gas Compressor 01",
            "Rotating Equipment",
            "Gas Compression",
            "FPSO-001",
            "Critical",
        ),
        (
            "COMP-002",
            "Gas Compressor 02",
            "Rotating Equipment",
            "Gas Compression",
            "FPSO-001",
            "Critical",
        ),
        (
            "WI-001",
            "Water Injection Package",
            "Process Equipment",
            "Water Injection",
            "FPSO-001",
            "High",
        ),
        (
            "GEN-001",
            "Power Generator 01",
            "Electrical",
            "Power Generation",
            "FPSO-001",
            "Critical",
        ),
        (
            "GEN-002",
            "Power Generator 02",
            "Electrical",
            "Power Generation",
            "FPSO-001",
            "Critical",
        ),
    ]

    rows = []

    for equipment_id, name, equipment_type, category, parent, criticality in equipment:
        rows.append(
            {
                "Equipment_ID": equipment_id,
                "Equipment_Name": name,
                "Equipment_Type": equipment_type,
                "Equipment_Category": category,
                "Parent_Equipment_ID": parent,
                "Field_ID": FIELD_ID,
                "Criticality": criticality,
                "Installation_Date": "2022-01-01",
                "Design_Life_Years": int(rng.choice([15, 20, 25])),
                "Status": "Operational",
            }
        )

    # Add four manifolds as subsea equipment.
    for index in range(1, MANIFOLD_COUNT + 1):
        rows.append(
            {
                "Equipment_ID": f"SUB-M{index:02d}",
                "Equipment_Name": f"Subsea Manifold M{index:02d}",
                "Equipment_Type": "Subsea Equipment",
                "Equipment_Category": "Manifold",
                "Parent_Equipment_ID": "",
                "Field_ID": FIELD_ID,
                "Criticality": "Critical",
                "Installation_Date": "2022-01-15",
                "Design_Life_Years": 25,
                "Status": "Operational",
            }
        )

    # Add well trees.
    for index in range(1, PRODUCER_COUNT + 1):
        rows.append(
            {
                "Equipment_ID": f"TREE-P{index:03d}",
                "Equipment_Name": f"Subsea Tree P{index:03d}",
                "Equipment_Type": "Subsea Equipment",
                "Equipment_Category": "Production Tree",
                "Parent_Equipment_ID": f"SUB-M{((index - 1) // 6) + 1:02d}",
                "Field_ID": FIELD_ID,
                "Criticality": "High",
                "Installation_Date": "2022-06-01",
                "Design_Life_Years": 25,
                "Status": "Operational",
            }
        )

    return pd.DataFrame(rows)


def generate_failure_causes() -> pd.DataFrame:
    """Generate controlled failure-cause dimension."""
    causes = [
        ("FC01", "Mechanical", "Pump Failure", "High", 0),
        ("FC02", "Mechanical", "Valve Failure", "High", 0),
        ("FC03", "Mechanical", "Seal Failure", "Medium", 0),
        ("FC04", "Electrical", "Power Failure", "High", 0),
        ("FC05", "Electrical", "Control System Failure", "Medium", 0),
        ("FC06", "Process", "Separator Constraint", "High", 0),
        ("FC07", "Process", "Gas Compression Limitation", "High", 0),
        ("FC08", "Process", "Water Handling Limitation", "Medium", 0),
        ("FC09", "Flow Assurance", "Hydrate Risk", "High", 0),
        ("FC10", "Flow Assurance", "Flow Restriction", "Medium", 0),
        ("FC11", "Subsea", "Subsea Tree Failure", "High", 0),
        ("FC12", "Subsea", "Manifold Failure", "Critical", 0),
        ("FC13", "Weather", "Severe Weather", "Medium", 0),
        ("FC14", "Logistics", "Vessel Unavailability", "Medium", 0),
        ("FC15", "Planned Maintenance", "Preventive Maintenance", "Low", 1),
        ("FC16", "Planned Maintenance", "Inspection", "Low", 1),
    ]

    return pd.DataFrame(
        causes,
        columns=[
            "Failure_Cause_ID",
            "Failure_Category",
            "Failure_Cause",
            "Severity",
            "Planned_Flag",
        ],
    )


def generate_interventions() -> pd.DataFrame:
    """Generate intervention-type dimension."""
    interventions = [
        ("INT01", "Well Intervention", "Well", 72, 1_500_000),
        ("INT02", "Workover", "Well", 240, 5_000_000),
        ("INT03", "Artificial Lift Optimization", "Well", 48, 350_000),
        ("INT04", "Subsea Repair", "Subsea", 120, 2_500_000),
        ("INT05", "Flowline Remediation", "Flow Assurance", 96, 1_800_000),
        ("INT06", "Process Debottleneck", "Facility", 168, 3_000_000),
    ]

    return pd.DataFrame(
        interventions,
        columns=[
            "Intervention_Type_ID",
            "Intervention_Type",
            "Intervention_Category",
            "Typical_Duration_hr",
            "Typical_Cost_USD",
        ],
    )


def generate_scenarios() -> pd.DataFrame:
    """Generate economic scenarios."""
    return pd.DataFrame(
        [
            {
                "Scenario_ID": "S01",
                "Scenario_Name": "Low",
                "Oil_Price_USD_bbl": 60.0,
            },
            {
                "Scenario_ID": "S02",
                "Scenario_Name": "Base",
                "Oil_Price_USD_bbl": 75.0,
            },
            {
                "Scenario_ID": "S03",
                "Scenario_Name": "High",
                "Oil_Price_USD_bbl": 90.0,
            },
        ]
    )


def save_dimension(df: pd.DataFrame, name: str) -> None:
    """Save a dimension as CSV."""
    output_path = RAW_DATA_DIR / f"{name}.csv"
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df):,} rows → {output_path}")


def main() -> None:
    """Generate all non-date dimensions."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(RANDOM_SEED)

    save_dimension(generate_field(), "Dim_Field")
    save_dimension(generate_manifolds(rng), "Dim_Manifold")
    save_dimension(generate_wells(rng), "Dim_Well")
    save_dimension(generate_equipment(rng), "Dim_Equipment")
    save_dimension(generate_failure_causes(), "Dim_Failure_Cause")
    save_dimension(generate_interventions(), "Dim_Intervention")
    save_dimension(generate_scenarios(), "Dim_Scenario")


if __name__ == "__main__":
    main()
