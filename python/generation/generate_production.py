"""Generate synthetic daily baseline production for Orion Deepwater Field.

Phase 4B establishes the natural production profile of producer wells.
Downtime and intervention effects are intentionally applied in later phases.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from python.generation.config import (
    END_DATE,
    RANDOM_SEED,
    RAW_DATA_DIR,
    START_DATE,
)


# ---------------------------------------------------------------------------
# Engineering parameters
# ---------------------------------------------------------------------------

HOURS_PER_DAY = 24.0

DAILY_RATE_NOISE_STD = 0.025

WATER_CUT_CAP = 0.85
WATER_CUT_GROWTH_MIN = 0.000015
WATER_CUT_GROWTH_MAX = 0.000045

GOR_NOISE_STD = 0.035

BASELINE_RUNTIME_MIN_HR = 22.5
BASELINE_RUNTIME_MAX_HR = 24.0


def load_wells() -> pd.DataFrame:
    """Load producer wells from Dim_Well."""
    path = RAW_DATA_DIR / "Dim_Well.csv"

    wells = pd.read_csv(path)

    producers = wells.loc[
        wells["Well_Type"].eq("Producer")
    ].copy()

    if producers.empty:
        raise ValueError("No producer wells found in Dim_Well.csv.")

    return producers


def generate_date_range() -> pd.DatetimeIndex:
    """Generate the production analysis calendar."""
    return pd.date_range(
        start=START_DATE,
        end=END_DATE,
        freq="D",
    )


def calculate_water_cut(
    initial_water_cut: float,
    elapsed_days: int,
    growth_rate: float,
) -> float:
    """Calculate gradually increasing water cut."""
    water_cut = initial_water_cut + (
        growth_rate * elapsed_days
    )

    return float(
        min(
            max(water_cut, 0.0),
            WATER_CUT_CAP,
        )
    )


def calculate_decline_rate(
    initial_rate: float,
    annual_decline: float,
    elapsed_days: int,
) -> float:
    """Calculate natural production decline."""
    elapsed_years = elapsed_days / 365.25

    return float(
        initial_rate
        * np.exp(
            -annual_decline * elapsed_years
        )
    )


def generate_well_production(
    well: pd.Series,
    dates: pd.DatetimeIndex,
    rng: np.random.Generator,
) -> list[dict]:
    """Generate daily baseline production for one producer."""
    rows = []

    first_production = pd.Timestamp(
        well["First_Production_Date"]
    )

    initial_oil_rate = float(
        well["Initial_Oil_Rate_bopd"]
    )

    annual_decline = float(
        well["Decline_Rate_pct"]
    )

    initial_water_cut = float(
        well["Initial_Water_Cut_pct"]
    )

    initial_gas_rate = float(
        well["Initial_Gas_Rate_Mscfd"]
    )

    water_growth_rate = float(
        rng.uniform(
            WATER_CUT_GROWTH_MIN,
            WATER_CUT_GROWTH_MAX,
        )
    )

    for date in dates:
        current_date = pd.Timestamp(date)

        if current_date < first_production:
            continue

        elapsed_days = (
            current_date - first_production
        ).days

        # Natural oil decline.
        natural_oil_rate = calculate_decline_rate(
            initial_rate=initial_oil_rate,
            annual_decline=annual_decline,
            elapsed_days=elapsed_days,
        )

        # Daily production variability.
        rate_factor = max(
            0.90,
            1.0
            + rng.normal(
                0.0,
                DAILY_RATE_NOISE_STD,
            ),
        )

        potential_oil = max(
            0.0,
            natural_oil_rate * rate_factor,
        )

        # Water-cut evolution.
        water_cut = calculate_water_cut(
            initial_water_cut=initial_water_cut,
            elapsed_days=elapsed_days,
            growth_rate=water_growth_rate,
        )

        water_bbl = (
            potential_oil
            * water_cut
            / max(
                1.0 - water_cut,
                0.001,
            )
        )

        liquid_potential_bbl = (
            potential_oil + water_bbl
        )

        # Gas behavior follows the oil production profile.
        gas_factor = max(
            0.90,
            1.0
            + rng.normal(
                0.0,
                GOR_NOISE_STD,
            ),
        )

        gas_rate_mscfd = max(
            0.0,
            initial_gas_rate
            * (
                potential_oil
                / max(
                    initial_oil_rate,
                    1.0,
                )
            )
            * gas_factor,
        )

        # Normal baseline operating availability.
        runtime_hr = float(
            rng.uniform(
                BASELINE_RUNTIME_MIN_HR,
                BASELINE_RUNTIME_MAX_HR,
            )
        )

        availability_factor = (
            runtime_hr / HOURS_PER_DAY
        )

        # Convert potential production into baseline production.
        actual_baseline_oil = (
            potential_oil
            * availability_factor
        )

        actual_baseline_water = (
            water_bbl
            * availability_factor
        )

        actual_baseline_gas = (
            gas_rate_mscfd
            * availability_factor
        )

        # ------------------------------------------------------------------
        # Critical reconciliation rule:
        # fundamental values are rounded first, and Liquid is derived from
        # those exact values.
        # ------------------------------------------------------------------

        oil_bbl = round(
            actual_baseline_oil,
            2,
        )

        water_bbl_actual = round(
            actual_baseline_water,
            2,
        )

        gas_mscf = round(
            actual_baseline_gas,
            2,
        )

        liquid_bbl = round(
            oil_bbl + water_bbl_actual,
            2,
        )

        rows.append(
            {
                "Date": current_date.strftime(
                    "%Y-%m-%d"
                ),
                "Well_ID": well["Well_ID"],
                "Potential_Oil_bbl": round(
                    potential_oil,
                    2,
                ),
                "Oil_bbl": oil_bbl,
                "Gas_Mscf": gas_mscf,
                "Water_bbl": water_bbl_actual,
                "Liquid_bbl": liquid_bbl,
                "Runtime_hr": round(
                    runtime_hr,
                    2,
                ),
                "Available_hr": HOURS_PER_DAY,
            }
        )

    return rows


def generate_production() -> pd.DataFrame:
    """Generate baseline daily production for all producer wells."""
    rng = np.random.default_rng(
        RANDOM_SEED
    )

    wells = load_wells()
    dates = generate_date_range()

    all_rows: list[dict] = []

    for _, well in wells.iterrows():
        all_rows.extend(
            generate_well_production(
                well=well,
                dates=dates,
                rng=rng,
            )
        )

    production = pd.DataFrame(
        all_rows
    )

    if production.empty:
        raise ValueError(
            "Production generator returned no records."
        )

    production.sort_values(
        ["Date", "Well_ID"],
        inplace=True,
    )

    production.reset_index(
        drop=True,
        inplace=True,
    )

    return production


def main() -> None:
    """Generate and save baseline production."""
    RAW_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    production = generate_production()

    output_path = (
        RAW_DATA_DIR
        / "Fact_Production_Daily.csv"
    )

    production.to_csv(
        output_path,
        index=False,
    )

    print(
        f"Generated {len(production):,} production records "
        f"â†’ {output_path}"
    )

    print(
        f"Producer wells: "
        f"{production['Well_ID'].nunique():,}"
    )

    print(
        f"Date range: "
        f"{production['Date'].min()} â†’ "
        f"{production['Date'].max()}"
    )

    print(
        f"Total baseline oil: "
        f"{production['Oil_bbl'].sum():,.0f} bbl"
    )


if __name__ == "__main__":
    main()
