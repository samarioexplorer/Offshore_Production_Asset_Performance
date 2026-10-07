import pandas as pd

FILE = r"data\raw\Fact_Downtime_Event.csv"

d = pd.read_csv(
    FILE,
    usecols=[
        "Downtime_ID",
        "Well_ID",
        "Date",
        "Start_Hour",
        "Duration_hr",
        "Downtime_Type",
        "Failure_Cause_ID",
        "Production_Affected",
    ],
)

d["Date"] = pd.to_datetime(d["Date"])

d["Start_Timestamp"] = (
    d["Date"] +
    pd.to_timedelta(d["Start_Hour"], unit="h")
)

d["End_Timestamp"] = (
    d["Start_Timestamp"] +
    pd.to_timedelta(d["Duration_hr"], unit="h")
)


def merge_intervals(group):

    events = (
        group
        .sort_values("Start_Timestamp")
        [["Start_Timestamp", "End_Timestamp"]]
        .itertuples(index=False, name=None)
    )

    merged = []

    for start, end in events:

        if not merged:
            merged.append([start, end])

        elif start >= merged[-1][1]:
            merged.append([start, end])

        elif end > merged[-1][1]:
            merged[-1][1] = end

    return merged


results = []

for well, group in d.groupby("Well_ID"):

    raw_hours = group["Duration_hr"].sum()

    intervals = merge_intervals(group)

    unique_hours = sum(
        (end - start).total_seconds() / 3600
        for start, end in intervals
    )

    overlap_hours = raw_hours - unique_hours

    results.append(
        {
            "Well_ID": well,
            "Events": len(group),
            "Raw_Event_Hours": raw_hours,
            "Unique_Downtime_Hours": unique_hours,
            "Overlap_Hours": overlap_hours,
            "Overlap_Pct_of_Raw": (
                overlap_hours / raw_hours * 100
                if raw_hours > 0
                else 0
            ),
        }
    )


r = pd.DataFrame(results)

total_raw = d["Duration_hr"].sum()
total_unique = r["Unique_Downtime_Hours"].sum()
total_overlap = total_raw - total_unique
overlap_pct = total_overlap / total_raw * 100


print("=" * 72)
print("QA-17 - OVERLAP DURATION / UNIQUE DOWNTIME RECONCILIATION")
print("=" * 72)

print(f"Downtime events:                 {len(d):,}")
print(f"Distinct wells:                  {d['Well_ID'].nunique():,}")
print(f"Raw event-hours:                 {total_raw:,.2f}")
print(f"Unique elapsed downtime hours:   {total_unique:,.2f}")
print(f"Potential overlap hours:         {total_overlap:,.2f}")
print(f"Overlap as percent of raw:       {overlap_pct:.2f}%")

print()
print("WELLS WITH OVERLAP")
print("-" * 72)

overlap_wells = (
    r[r["Overlap_Hours"] > 0]
    .sort_values("Overlap_Hours", ascending=False)
)

if len(overlap_wells) > 0:

    print(
        overlap_wells.to_string(
            index=False,
            formatters={
                "Raw_Event_Hours": "{:,.2f}".format,
                "Unique_Downtime_Hours": "{:,.2f}".format,
                "Overlap_Hours": "{:,.2f}".format,
                "Overlap_Pct_of_Raw": "{:.2f}".format,
            },
        )
    )

else:

    print("None")


print()
print("STATUS")
print("-" * 72)

if abs(total_overlap) < 0.01:

    print("PASS - No material overlapping downtime hours detected.")

else:

    print(
        "REVIEW - Overlapping events create "
        f"{total_overlap:,.2f} hours of potential double-counting "
        f"({overlap_pct:.2f}% of raw event-hours)."
    )
