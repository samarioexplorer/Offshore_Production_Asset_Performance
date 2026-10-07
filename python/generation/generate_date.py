"""Generate the Dim_Date calendar dimension."""

import pandas as pd

from python.generation.config import END_DATE, RAW_DATA_DIR, START_DATE


def generate_date_dimension() -> pd.DataFrame:
    """Create the project calendar dimension."""
    dates = pd.date_range(
        start=START_DATE,
        end=END_DATE,
        freq="D",
    )

    df = pd.DataFrame({"Date": dates})

    df["Year"] = df["Date"].dt.year
    df["Quarter"] = df["Date"].dt.quarter
    df["Month"] = df["Date"].dt.month
    df["Month_Name"] = df["Date"].dt.month_name()
    df["Month_Start"] = df["Date"].dt.to_period("M").dt.to_timestamp()
    df["Year_Month"] = df["Date"].dt.strftime("%Y-%m")
    df["Day"] = df["Date"].dt.day
    df["Day_of_Week"] = df["Date"].dt.dayofweek + 1
    df["Day_Name"] = df["Date"].dt.day_name()

    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    df["Month_Start"] = df["Month_Start"].dt.strftime("%Y-%m-%d")

    return df


def main() -> None:
    """Generate and save Dim_Date."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    df = generate_date_dimension()

    output_path = RAW_DATA_DIR / "Dim_Date.csv"
    df.to_csv(output_path, index=False)

    print(f"Generated {len(df):,} rows → {output_path}")


if __name__ == "__main__":
    main()
'@ | Set-Content -Encoding UTF8 python\generation\generate_date.py'