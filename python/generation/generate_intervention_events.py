"""
Phase 4C.3 â€” Synthetic Intervention Event Engine

Project: Offshore Production Asset Performance
Field: Orion Deepwater Field

Purpose
-------
Generate a deterministic intervention-event fact table using:

    Dim_Well
    Dim_Intervention
    Fact_Production_Daily

The intervention layer represents engineering events and assumptions.
It does NOT modify the baseline production dataset and does NOT calculate
production restored or economic impact.

Those effects are calculated later in Phase 4D.

Output
------
data/raw/Fact_Intervention_Event.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from event_config import (
    EVENT_RANDOM_SEED,
    EXPECTED_PRODUCER_COUNT,
    INTERVENTION_COST_MAX_USD,
    INTERVENTION_COST_MIN_USD,
    INTERVENTION_DURATION_MAX_DAYS,
    INTERVENTION_DURATION_MIN_DAYS,
    INTERVENTION_EVENT_MAX,
    INTERVENTION_EVENT_MIN,
    INTERVENTION_RECOVERY_MAX_PCT,
    INTERVENTION_RECOVERY_MIN_PCT,
)


# ---------------------------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"

WELL_PATH = RAW_DATA_DIR / "Dim_Well.csv"
INTERVENTION_PATH = RAW_DATA_DIR / "Dim_Intervention.csv"
PRODUCTION_PATH = RAW_DATA_DIR / "Fact_Production_Daily.csv"

OUTPUT_PATH = RAW_DATA_DIR / "Fact_Intervention_Event.csv"


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def fail(message: str) -> None:
    print(f"\nERROR: {message}\n")
    sys.exit(1)


def validate_required_columns(
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
# LOAD INPUTS
# ---------------------------------------------------------------------------

def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not WELL_PATH.exists():
        fail(f"Missing input file: {WELL_PATH}")

    if not INTERVENTION_PATH.exists():
        fail(f"Missing input file: {INTERVENTION_PATH}")

    if not PRODUCTION_PATH.exists():
        fail(f"Missing input file: {PRODUCTION_PATH}")

    wells = pd.read_csv(WELL_PATH)
    interventions = pd.read_csv(INTERVENTION_PATH)
    production = pd.read_csv(PRODUCTION_PATH)

    validate_required_columns(
        wells,
        [
            "Well_ID",
            "Well_Type",
            "Well_Status",
            "Initial_Oil_Rate_bopd",
        ],
        "Dim_Well",
    )

    validate_required_columns(
        interventions,
        [
            "Intervention_Type_ID",
            "Intervention_Type",
            "Intervention_Category",
            "Typical_Duration_hr",
            "Typical_Cost_USD",
        ],
        "Dim_Intervention",
    )

    validate_required_columns(
        production,
        [
            "Well_ID",
            "Date",
            "Oil_bbl",
        ],
        "Fact_Production_Daily",
    )

    return wells, interventions, production


# ---------------------------------------------------------------------------
# BUILD VALID PRODUCER-DAY POOL
# ---------------------------------------------------------------------------

def build_producer_day_pool(
    wells: pd.DataFrame,
    production: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str]]:
    producers = wells.loc[
        wells["Well_Type"].eq("Producer")
    ].copy()

    producer_ids = sorted(producers["Well_ID"].astype(str).unique())

    if len(producer_ids) != EXPECTED_PRODUCER_COUNT:
        fail(
            f"Expected {EXPECTED_PRODUCER_COUNT} producer wells, "
            f"found {len(producer_ids)}."
        )

    production = production.copy()
    production["Well_ID"] = production["Well_ID"].astype(str)
    production["Date"] = pd.to_datetime(production["Date"])

    production_producers = set(
        production["Well_ID"].unique()
    )

    missing = sorted(set(producer_ids) - production_producers)

    if missing:
        fail(
            "Producer wells missing from production baseline: "
            + ", ".join(missing)
        )

    pool = production.loc[
        production["Well_ID"].isin(producer_ids),
        ["Well_ID", "Date", "Oil_bbl"],
    ].copy()

    pool = pool.sort_values(
        ["Well_ID", "Date"]
    ).reset_index(drop=True)

    if pool.empty:
        fail("Producer production day pool is empty.")

    return pool, producer_ids


# ---------------------------------------------------------------------------
# SELECT INTERVENTION EVENTS
# ---------------------------------------------------------------------------

def select_event_count(rng: np.random.Generator) -> int:
    return int(
        rng.integers(
            INTERVENTION_EVENT_MIN,
            INTERVENTION_EVENT_MAX + 1,
        )
    )


def select_event_days(
    pool: pd.DataFrame,
    event_count: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """
    Select intervention starts while avoiding overlapping interventions
    on the same well.

    A candidate start is accepted only when its full intervention window
    remains within the available production history and does not overlap
    another intervention already assigned to that well.
    """

    candidates = pool.copy()

    candidates = candidates.sample(
        frac=1.0,
        random_state=int(rng.integers(0, 2**32 - 1)),
    ).reset_index(drop=True)

    selected: list[dict] = []
    occupied: dict[str, list[tuple[pd.Timestamp, pd.Timestamp]]] = {}

    max_attempts = len(candidates) * 3
    attempts = 0

    for row in candidates.itertuples(index=False):
        if len(selected) >= event_count:
            break

        attempts += 1

        if attempts > max_attempts:
            break

        well_id = str(row.Well_ID)
        start_date = pd.Timestamp(row.Date)

        duration = int(
            rng.integers(
                INTERVENTION_DURATION_MIN_DAYS,
                INTERVENTION_DURATION_MAX_DAYS + 1,
            )
        )

        end_date = start_date + pd.Timedelta(
            days=duration - 1
        )

        well_history = candidates.loc[
            candidates["Well_ID"].eq(well_id),
            "Date",
        ]

        if end_date > well_history.max():
            continue

        overlaps = False

        for existing_start, existing_end in occupied.get(
            well_id,
            [],
        ):
            if (
                start_date <= existing_end
                and end_date >= existing_start
            ):
                overlaps = True
                break

        if overlaps:
            continue

        occupied.setdefault(well_id, []).append(
            (start_date, end_date)
        )

        selected.append(
            {
                "Well_ID": well_id,
                "Start_Date": start_date,
                "End_Date": end_date,
                "Duration_Days": duration,
                "Baseline_Oil_bopd": float(row.Oil_bbl),
            }
        )

    if len(selected) < event_count:
        fail(
            f"Could only create {len(selected)} non-overlapping "
            f"intervention events out of requested {event_count}."
        )

    return pd.DataFrame(selected)


# ---------------------------------------------------------------------------
# GENERATE EVENT ATTRIBUTES
# ---------------------------------------------------------------------------

def generate_events(
    selected: pd.DataFrame,
    wells: pd.DataFrame,
    interventions: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:

    intervention_types = interventions[
        [
            "Intervention_Type_ID",
            "Intervention_Type",
            "Intervention_Category",
            "Typical_Duration_hr",
            "Typical_Cost_USD",
        ]
    ].copy()

    intervention_type_ids = intervention_types[
        "Intervention_Type_ID"
    ].astype(str).tolist()

    if len(intervention_type_ids) != 6:
        fail(
            "Expected exactly 6 intervention types in "
            "Dim_Intervention."
        )

    selected = selected.copy()

    selected["Intervention_Type_ID"] = rng.choice(
        intervention_type_ids,
        size=len(selected),
        replace=True,
    )

    selected = selected.merge(
        intervention_types,
        on="Intervention_Type_ID",
        how="left",
        validate="many_to_one",
    )

    well_rates = wells[
        [
            "Well_ID",
            "Initial_Oil_Rate_bopd",
        ]
    ].copy()

    well_rates["Well_ID"] = well_rates["Well_ID"].astype(str)

    selected = selected.merge(
        well_rates,
        on="Well_ID",
        how="left",
        validate="many_to_one",
    )

    # Target recovery is expressed as a multiplier relative to the
    # production rate immediately before intervention.
    selected["Target_Recovery_pct"] = (
        rng.uniform(
            INTERVENTION_RECOVERY_MIN_PCT,
            INTERVENTION_RECOVERY_MAX_PCT,
            size=len(selected),
        )
        * 100.0
    ).round(2)

    # Expected post-intervention oil rate.
    #
    # The intervention target is anchored to the current baseline rate,
    # not the original initial rate. This preserves decline behavior.
    selected["Expected_Oil_Rate_bopd"] = (
        selected["Baseline_Oil_bopd"]
        * selected["Target_Recovery_pct"]
        / 100.0
    ).round(2)

    # Cost is centered around the authoritative typical cost while still
    # introducing controlled engineering variability.
    cost_factor = rng.uniform(
        0.85,
        1.15,
        size=len(selected),
    )

    selected["Intervention_Cost_USD"] = (
        selected["Typical_Cost_USD"]
        * cost_factor
    ).clip(
        lower=INTERVENTION_COST_MIN_USD,
        upper=INTERVENTION_COST_MAX_USD,
    ).round(2)

    # Historical synthetic dataset: interventions are predominantly
    # completed. A small cancelled share creates realistic operational data.
    status_draw = rng.random(len(selected))

    selected["Status"] = np.where(
        status_draw < 0.95,
        "Completed",
        "Cancelled",
    )

    selected["Intervention_ID"] = [
        f"INTV-{index:04d}"
        for index in range(1, len(selected) + 1)
    ]

    return selected


# ---------------------------------------------------------------------------
# BUILD FINAL FACT TABLE
# ---------------------------------------------------------------------------

def build_output(events: pd.DataFrame) -> pd.DataFrame:
    output_columns = [
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
    ]

    output = events[output_columns].copy()

    output["Start_Date"] = pd.to_datetime(
        output["Start_Date"]
    ).dt.strftime("%Y-%m-%d")

    output["End_Date"] = pd.to_datetime(
        output["End_Date"]
    ).dt.strftime("%Y-%m-%d")

    output = output.sort_values(
        ["Start_Date", "Well_ID", "Intervention_ID"]
    ).reset_index(drop=True)

    return output


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def run_qa(
    output: pd.DataFrame,
    wells: pd.DataFrame,
    interventions: pd.DataFrame,
    production: pd.DataFrame,
) -> None:

    print("\n" + "=" * 72)
    print("PHASE 4C.3 â€” INTERVENTION EVENT QA")
    print("=" * 72)

    producers = set(
        wells.loc[
            wells["Well_Type"].eq("Producer"),
            "Well_ID",
        ].astype(str)
    )

    valid_intervention_types = set(
        interventions["Intervention_Type_ID"].astype(str)
    )

    production_days = set(
        zip(
            production["Well_ID"].astype(str),
            pd.to_datetime(production["Date"]),
        )
    )

    start_dates = pd.to_datetime(output["Start_Date"])
    end_dates = pd.to_datetime(output["End_Date"])

    print(f"Rows: {len(output):,}")
    print(
        "Unique Intervention IDs: "
        f"{output['Intervention_ID'].nunique():,}"
    )

    duplicate_ids = output["Intervention_ID"].duplicated().sum()
    print(f"Duplicate Intervention IDs: {duplicate_ids:,}")

    unique_wells = output["Well_ID"].nunique()
    print(f"Producer wells represented: {unique_wells:,}")

    invalid_wells = (
        ~output["Well_ID"].astype(str).isin(producers)
    ).sum()
    print(f"Invalid Well_ID: {invalid_wells:,}")

    invalid_types = (
        ~output["Intervention_Type_ID"]
        .astype(str)
        .isin(valid_intervention_types)
    ).sum()
    print(
        f"Invalid Intervention_Type_ID: "
        f"{invalid_types:,}"
    )

    duration_invalid = (
        (output["Duration_Days"] < INTERVENTION_DURATION_MIN_DAYS)
        | (
            output["Duration_Days"]
            > INTERVENTION_DURATION_MAX_DAYS
        )
    ).sum()

    print(
        f"Duration outside configured range: "
        f"{duration_invalid:,}"
    )

    invalid_dates = (end_dates < start_dates).sum()
    print(f"End date before start date: {invalid_dates:,}")

    invalid_recovery = (
        (output["Target_Recovery_pct"] < INTERVENTION_RECOVERY_MIN_PCT * 100)
        | (
            output["Target_Recovery_pct"]
            > INTERVENTION_RECOVERY_MAX_PCT * 100
        )
    ).sum()

    print(
        f"Recovery outside configured range: "
        f"{invalid_recovery:,}"
    )

    invalid_cost = (
        (output["Intervention_Cost_USD"] < INTERVENTION_COST_MIN_USD)
        | (
            output["Intervention_Cost_USD"]
            > INTERVENTION_COST_MAX_USD
        )
    ).sum()

    print(
        f"Cost outside configured range: "
        f"{invalid_cost:,}"
    )

    invalid_start_days = 0

    for row in output.itertuples(index=False):
        key = (
            str(row.Well_ID),
            pd.Timestamp(row.Start_Date),
        )

        if key not in production_days:
            invalid_start_days += 1

    print(
        "Events without matching production start day: "
        f"{invalid_start_days:,}"
    )

    null_values = int(output.isna().sum().sum())
    print(f"Null values: {null_values:,}")

    # Check intervention overlap.
    overlap_count = 0

    qa_events = output.copy()
    qa_events["Start_Date"] = pd.to_datetime(
        qa_events["Start_Date"]
    )
    qa_events["End_Date"] = pd.to_datetime(
        qa_events["End_Date"]
    )

    for well_id, group in qa_events.groupby("Well_ID"):
        group = group.sort_values("Start_Date")

        previous_end = None

        for row in group.itertuples(index=False):
            if (
                previous_end is not None
                and row.Start_Date <= previous_end
            ):
                overlap_count += 1

            if (
                previous_end is None
                or row.End_Date > previous_end
            ):
                previous_end = row.End_Date

    print(
        f"Overlapping intervention windows: "
        f"{overlap_count:,}"
    )

    # Hard QA assertions.
    assert duplicate_ids == 0
    assert invalid_wells == 0
    assert invalid_types == 0
    assert duration_invalid == 0
    assert invalid_dates == 0
    assert invalid_recovery == 0
    assert invalid_cost == 0
    assert invalid_start_days == 0
    assert null_values == 0
    assert overlap_count == 0

    print("\nQA STATUS: PASS")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print("PHASE 4C.3 â€” SYNTHETIC INTERVENTION EVENT ENGINE")
    print("=" * 72)

    print(f"\nProject root: {PROJECT_ROOT}")
    print(f"Output path : {OUTPUT_PATH}")
    print(f"Random seed : {EVENT_RANDOM_SEED}")

    wells, interventions, production = load_inputs()

    print("\n[1/4] Inputs loaded")
    print(f"      Wells: {len(wells):,}")
    print(f"      Intervention types: {len(interventions):,}")
    print(f"      Production rows: {len(production):,}")

    producer_pool, producer_ids = build_producer_day_pool(
        wells,
        production,
    )

    print("\n[2/4] Producer-day pool validated")
    print(f"      Producer wells: {len(producer_ids):,}")
    print(f"      Producer-days: {len(producer_pool):,}")

    rng = np.random.default_rng(EVENT_RANDOM_SEED)

    event_count = select_event_count(rng)

    print(
        "\n[3/4] Generating intervention events"
    )
    print(f"      Requested events: {event_count:,}")

    selected = select_event_days(
        producer_pool,
        event_count,
        rng,
    )

    events = generate_events(
        selected,
        wells,
        interventions,
        rng,
    )

    output = build_output(events)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(f"      Generated events: {len(output):,}")
    print(f"      Output: {OUTPUT_PATH}")

    run_qa(
        output,
        wells,
        interventions,
        production,
    )

    print("\n" + "=" * 72)
    print("PHASE 4C.3 COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
