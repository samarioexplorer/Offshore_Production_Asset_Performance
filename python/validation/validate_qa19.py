from pathlib import Path
import sys

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from python.generation.event_config import (
    DOWNTIME_EVENT_MIN,
    DOWNTIME_EVENT_MAX,
    DOWNTIME_DURATION_MIN_HR,
    DOWNTIME_DURATION_MAX_HR,
    PRODUCTION_IMPACT_PROBABILITY,
    DOWNTIME_TYPES,
    EVENT_RANDOM_SEED,
)

from python.generation.generate_downtime_events import (
    load_inputs,
    prepare_producer_population,
    build_tree_mapping,
    select_event_population,
    select_equipment,
)


RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def main():

    print("=" * 72)
    print("QA-19 - PRODUCTION_AFFECTED CLASSIFICATION LOGIC")
    print("=" * 72)

    fact_path = RAW_DATA_DIR / "Fact_Downtime_Event.csv"

    fact = pd.read_csv(fact_path)

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

    rng = np.random.default_rng(
        EVENT_RANDOM_SEED
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

    expected = []

    for idx, event in selected.iterrows():

        well_id = event["Well_ID"]

        select_equipment(
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

        failure_causes.iloc[
            failure_index
        ]

        rng.uniform(
            DOWNTIME_DURATION_MIN_HR,
            DOWNTIME_DURATION_MAX_HR,
        )

        rng.uniform(
            0,
            24,
        )

        rng.choice(
            DOWNTIME_TYPES
        )

        production_affected = (
            rng.random()
            < PRODUCTION_IMPACT_PROBABILITY
        )

        expected.append(
            {
                "Downtime_ID":
                    f"DT{idx + 1:04d}",

                "Expected_Production_Affected":
                    (
                        "Yes"
                        if production_affected
                        else "No"
                    ),
            }
        )

    expected_df = pd.DataFrame(
        expected
    )

    comparison = fact[
        [
            "Downtime_ID",
            "Production_Affected",
        ]
    ].merge(
        expected_df,
        on="Downtime_ID",
        how="outer",
        indicator=True,
    )

    comparison["Match"] = (
        comparison["Production_Affected"]
        == comparison[
            "Expected_Production_Affected"
        ]
    )

    missing = comparison[
        comparison["_merge"] != "both"
    ]

    mismatches = comparison[
        (comparison["_merge"] == "both")
        & (~comparison["Match"])
    ]

    print()
    print("CONFIGURATION")
    print("-" * 72)
    print(
        f"Random seed:                 "
        f"{EVENT_RANDOM_SEED}"
    )
    print(
        f"Impact probability:          "
        f"{PRODUCTION_IMPACT_PROBABILITY:.4f}"
    )
    print(
        f"Configured event range:      "
        f"{DOWNTIME_EVENT_MIN} - "
        f"{DOWNTIME_EVENT_MAX}"
    )

    print()
    print("RECONSTRUCTION")
    print("-" * 72)
    print(
        f"CSV events:                  "
        f"{len(fact):,}"
    )
    print(
        f"Reconstructed events:        "
        f"{len(expected_df):,}"
    )
    print(
        f"CSV Yes:                     "
        f"{(fact['Production_Affected'] == 'Yes').sum():,}"
    )
    print(
        f"CSV No:                      "
        f"{(fact['Production_Affected'] == 'No').sum():,}"
    )
    print(
        f"Expected Yes:                "
        f"{(expected_df['Expected_Production_Affected'] == 'Yes').sum():,}"
    )
    print(
        f"Expected No:                 "
        f"{(expected_df['Expected_Production_Affected'] == 'No').sum():,}"
    )

    print()
    print("COMPARISON")
    print("-" * 72)
    print(
        f"Rows missing from either side: "
        f"{len(missing):,}"
    )
    print(
        f"Classification mismatches:     "
        f"{len(mismatches):,}"
    )

    if len(comparison) > 0:
        mismatch_rate = (
            len(mismatches)
            / len(comparison)
            * 100
        )
    else:
        mismatch_rate = 0.0

    print(
        f"Mismatch rate:                 "
        f"{mismatch_rate:.2f}%"
    )

    print()
    print("CLASSIFICATION CROSS-TAB")
    print("-" * 72)

    cross_tab = pd.crosstab(
        fact["Production_Affected"],
        expected_df[
            "Expected_Production_Affected"
        ],
    )

    print(cross_tab)

    if len(mismatches) > 0:

        print()
        print("MISMATCH DETAILS")
        print("-" * 72)

        print(
            mismatches[
                [
                    "Downtime_ID",
                    "Production_Affected",
                    "Expected_Production_Affected",
                ]
            ].to_string(index=False)
        )

    print()
    print("STATUS")
    print("-" * 72)

    if (
        len(fact) == event_count
        and len(expected_df) == event_count
        and len(missing) == 0
        and len(mismatches) == 0
    ):

        print("PASS")

        print(
            "Production_Affected classifications "
            "exactly match the seeded generation logic."
        )

    else:

        print("FAIL")

        print(
            "Production_Affected classifications do "
            "not fully reconcile with the generation logic."
        )

    print("=" * 72)


if __name__ == "__main__":
    main()
