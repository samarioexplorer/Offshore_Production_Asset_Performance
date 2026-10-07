import pandas as pd
import numpy as np

DOWNTIME_FILE = r"data\raw\Fact_Downtime_Event.csv"
IMPACT_FILE = r"data\processed\Fact_Production_Impact_Daily.csv"

d = pd.read_csv(DOWNTIME_FILE)
p = pd.read_csv(IMPACT_FILE)

# ---------------------------------------------------------------------
# Prepare downtime timestamps
# ---------------------------------------------------------------------

d["Date"] = pd.to_datetime(d["Date"])
d["Start_TS"] = d["Date"] + pd.to_timedelta(d["Start_Hour"], unit="h")
d["End_TS"] = d["Start_TS"] + pd.to_timedelta(
    d["Duration_hr"], unit="h"
)

affected = (
    d["Production_Affected"]
    .astype(str)
    .str.strip()
    .str.lower()
    .isin(["yes", "y", "true", "1"])
)

d["Affected_Duration_hr"] = np.where(
    affected,
    d["Duration_hr"],
    0.0,
)

# ---------------------------------------------------------------------
# Raw / affected event hours
# ---------------------------------------------------------------------

raw_hours = d["Duration_hr"].sum()
affected_hours = d["Affected_Duration_hr"].sum()

# ---------------------------------------------------------------------
# Calculate unique elapsed downtime by well
# ---------------------------------------------------------------------

unique_all = 0.0
unique_affected = 0.0

for well, g in d.groupby("Well_ID"):

    intervals = sorted(
        zip(g["Start_TS"], g["End_TS"])
    )

    merged = []

    for start, end in intervals:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        elif end > merged[-1][1]:
            merged[-1][1] = end

    unique_all += sum(
        (end - start).total_seconds() / 3600
        for start, end in merged
    )

    # Production-affected events only
    ga = g[g["Affected_Duration_hr"] > 0]

    intervals_affected = sorted(
        zip(ga["Start_TS"], ga["End_TS"])
    )

    merged_affected = []

    for start, end in intervals_affected:
        if not merged_affected or start > merged_affected[-1][1]:
            merged_affected.append([start, end])
        elif end > merged_affected[-1][1]:
            merged_affected[-1][1] = end

    unique_affected += sum(
        (end - start).total_seconds() / 3600
        for start, end in merged_affected
    )

overlap_all = raw_hours - unique_all
overlap_affected = affected_hours - unique_affected

# ---------------------------------------------------------------------
# Production impact layer
# ---------------------------------------------------------------------

impact_hours = p["Downtime_Hours"].sum()
effective_hours = p["Effective_Downtime_Hours"].sum()

availability_mean = p["Production_Availability_pct"].mean()
availability_min = p["Production_Availability_pct"].min()
availability_max = p["Production_Availability_pct"].max()

# ---------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------

impact_matches_affected = (
    abs(impact_hours - affected_hours) <= 1e-6
)

effective_le_downtime = (
    p["Effective_Downtime_Hours"]
    <= p["Downtime_Hours"] + 1e-9
).all()

effective_le_available = (
    p["Effective_Downtime_Hours"]
    <= p["Available_hr"] + 1e-9
).all()

availability_valid = (
    (p["Production_Availability_pct"] >= 0)
    & (p["Production_Availability_pct"] <= 100)
).all()

# ---------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------

print("=" * 72)
print("QA-23 - UNIQUE DOWNTIME / AVAILABILITY RECONCILIATION")
print("=" * 72)
print()

print("RAW EVENT HOURS")
print(f"Total event duration:       {raw_hours:,.2f}")
print(f"Affected event duration:    {affected_hours:,.2f}")
print()

print("UNIQUE ELAPSED HOURS")
print(f"Unique all-event hours:     {unique_all:,.2f}")
print(f"All-event overlap hours:    {overlap_all:,.2f}")
print(f"Unique affected hours:      {unique_affected:,.2f}")
print(f"Affected overlap hours:     {overlap_affected:,.2f}")
print()

print("PRODUCTION IMPACT LAYER")
print(f"Impact Downtime_Hours:      {impact_hours:,.2f}")
print(f"Effective Downtime_Hours:   {effective_hours:,.2f}")
print(
    "Impact vs affected event:   "
    f"{impact_hours - affected_hours:,.2f}"
)
print()

print("AVAILABILITY")
print(f"Mean Availability %:        {availability_mean:.4f}")
print(f"Minimum Availability %:     {availability_min:.4f}")
print(f"Maximum Availability %:     {availability_max:.4f}")
print()

print("CONTROL CHECKS")
print(
    "Impact matches affected:    "
    f"{impact_matches_affected}"
)
print(
    "Effective <= Downtime:      "
    f"{effective_le_downtime}"
)
print(
    "Effective <= Available:     "
    f"{effective_le_available}"
)
print(
    "Availability within 0-100:  "
    f"{availability_valid}"
)
print()

status = (
    impact_matches_affected
    and effective_le_downtime
    and effective_le_available
    and availability_valid
)

print(
    "QA-23 STATUS:",
    "PASS" if status else "REVIEW"
)
