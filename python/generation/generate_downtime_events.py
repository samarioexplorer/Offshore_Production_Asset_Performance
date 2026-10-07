from pathlib import Path

import numpy as np
import pandas as pd

from .event_config import (
    DOWNTIME_EVENT_MIN,
    DOWNTIME_EVENT_MAX,
    DOWNTIME_DURATION_MIN_HR,
    DOWNTIME_DURATION_MAX_HR,
    PRODUCTION_IMPACT_PROBABILITY,
    DOWNTIME_TYPES,
    EVENT_RANDOM_SEED,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def load_inputs():
    """Load authoritative Phase 4A dimensions and production baseline."""

    wells = pd.read_csv(
        RAW_DATA_DIR / "Dim_Well.csv"
    )

    equipment = pd.read_csv(
        RAW_DATA_DIR / "Dim_Equipment.csv"
    )

    failure_causes = pd.read_csv(
        RAW_DATA_DIR / "Dim_Failure_Cause.csv"
    )

    production = pd.read_csv(
        RAW_DATA_DIR / "Fact_Production_Daily.csv"
    )

    return (
        wells,
        equipment,
        failure_causes,
        production,
    )


def prepare_producer_population(
    wells,
    production,
):
    """Prepare valid producer well-days from the baseline."""

    producers = wells[
        wells["Well_Type"].eq("Producer")
    ].copy()

    production_dates = production[
        ["Date", "Well_ID"]
    ].drop_duplicates().copy()

    production_dates["Date"] = pd.to_datetime(
        production_dates["Date"]
    )

    producer_dates = production_dates.merge(
        producers[
            [
                "Well_ID",
                "Manifold_ID",
            ]
        ],
        on="Well_ID",
        how="inner",
    )

    return producers, producer_dates


def build_tree_mapping(
    equipment,
):
    """
    Build deterministic mapping between producer wells
    and their corresponding subsea production trees.

    TREE-P001 -> P001
    TREE-P002 -> P002
    ...
    """

    trees = equipment[
        equipment["Equipment_Category"].eq(
            "Production Tree"
        )
    ].copy()

    trees["Well_ID"] = (
        trees["Equipment_ID"]
        .str.replace(
            "TREE-",
            "",
            regex=False,
        )
    )

    return trees[
        [
            "Equipment_ID",
            "Well_ID",
            "Parent_Equipment_ID",
        ]
    ].copy()


def select_event_population(
    rng,
    producer_dates,
    event_count,
):
    """Select unique valid producer well-days."""

    if len(producer_dates) < event_count:
        raise ValueError(
            "Insufficient producer well-day combinations "
            "for requested downtime events."
        )

    selected_indices = rng.choice(
        producer_dates.index.to_numpy(),
        size=event_count,
        replace=False,
    )

    return producer_dates.loc[
        selected_indices
    ].reset_index(drop=True)


def classify_duration(
    duration_hr,
):
    """Classify event duration."""

    if duration_hr <= 8:
        return "Low"

    if duration_hr <= 24:
        return "Medium"

    return "High"


def select_equipment(
    rng,
    equipment,
    tree_mapping,
    well_id,
):
    """
    Select equipment using a weighted engineering hierarchy.

    Most events are associated with the well's production tree,
    while a smaller share is associated with manifold/FPSO
    equipment.
    """

    tree = tree_mapping[
        tree_mapping["Well_ID"].eq(well_id)
    ]

    if tree.empty:
        raise ValueError(
            f"No production tree found for {well_id}."
        )

    tree_row = tree.iloc[0]

    selection = rng.random()

    if selection < 0.60:
        return tree_row["Equipment_ID"]

    manifold_id = tree_row[
        "Parent_Equipment_ID"
    ]

    if selection < 0.80:
        manifold = equipment[
            equipment["Equipment_ID"].eq(
                manifold_id
            )
        ]

        if not manifold.empty:
            return manifold.iloc[0][
                "Equipment_ID"
            ]

    fps0_equipment = equipment[
        equipment["Parent_Equipment_ID"].eq(
            "FPSO-001"
        )
    ]

    if fps0_equipment.empty:
        return tree_row["Equipment_ID"]

    return fps0_equipment.iloc[
        rng.integers(
            0,
            len(fps0_equipment),
        )
    ]["Equipment_ID"]


def generate_downtime_events():
    """Generate deterministic synthetic downtime events."""

    rng = np.random.default_rng(
        EVENT_RANDOM_SEED
    )

    (
        wells,
        equipment,
        failure_causes,
        production,
    ) = load_inputs()

    (
        producers,
        producer_dates,
    ) = prepare_producer_population(
        wells,
        production,
    )

    tree_mapping = build_tree_mapping(
        equipment
    )

    if len(producers) != 24:
        raise ValueError(
            f"Expected 24 producer wells; "
            f"found {len(producers)}."
        )

    if len(tree_mapping) != 24:
        raise ValueError(
            f"Expected 24 production trees; "
            f"found {len(tree_mapping)}."
        )

    event_count = int(
        rng.integers(
            DOWNTIME_EVENT_MIN,
            DOWNTIME_EVENT_MAX + 1,
        )
    )

    selected = select_event_population(
        rng,
        producer_dates,
        event_count,
    )

    rows = []

    for idx, event in selected.iterrows():

        well_id = event["Well_ID"]

        equipment_id = select_equipment(
            rng,
            equipment,
            tree_mapping,
            well_id,
        )

        failure_index = int(
            rng.integers(
                0,
                len(failure_causes),
            )
        )

        failure = failure_causes.iloc[
            failure_index
        ]

        duration_hr = round(
            float(
                rng.uniform(
                    DOWNTIME_DURATION_MIN_HR,
                    DOWNTIME_DURATION_MAX_HR,
                )
            ),
            2,
        )

        start_hour = round(
            float(
                rng.uniform(
                    0,
                    24,
                )
            ),
            2,
        )

        downtime_type = str(
            rng.choice(
                DOWNTIME_TYPES
            )
        )

        production_affected = (
            rng.random()
            < PRODUCTION_IMPACT_PROBABILITY
        )

        rows.append(
            {
                "Downtime_ID":
                    f"DT{idx + 1:04d}",

                "Date":
                    event["Date"].strftime(
                        "%Y-%m-%d"
                    ),

                "Well_ID":
                    well_id,

                "Equipment_ID":
                    equipment_id,

                "Failure_Cause_ID":
                    failure[
                        "Failure_Cause_ID"
                    ],

                "Downtime_Type":
                    downtime_type,

                "Start_Hour":
                    start_hour,

                "Duration_hr":
                    duration_hr,

                "Severity":
                    classify_duration(
                        duration_hr
                    ),

                "Failure_Severity":
                    failure[
                        "Severity"
                    ],

                "Planned_Flag":
                    failure[
                        "Planned_Flag"
                    ],

                "Production_Affected":
                    (
                        "Yes"
                        if production_affected
                        else "No"
                    ),
            }
        )

    downtime = pd.DataFrame(rows)

    downtime = downtime.sort_values(
        [
            "Date",
            "Well_ID",
            "Start_Hour",
        ]
    ).reset_index(drop=True)

    output_path = (
        RAW_DATA_DIR
        / "Fact_Downtime_Event.csv"
    )

    downtime.to_csv(
        output_path,
        index=False,
    )

    print(
        f"Generated {len(downtime):,} downtime events "
        f"-> {output_path}"
    )

    print(
        f"Producer wells represented: "
        f"{downtime['Well_ID'].nunique()}"
    )

    print(
        f"Date range: "
        f"{downtime['Date'].min()} -> "
        f"{downtime['Date'].max()}"
    )

    print(
        f"Total downtime hours: "
        f"{downtime['Duration_hr'].sum():,.2f}"
    )

    print(
        f"Production-affected events: "
        f"{(downtime['Production_Affected'] == 'Yes').sum():,}"
    )


def main():
    generate_downtime_events()


if __name__ == "__main__":
    main()
