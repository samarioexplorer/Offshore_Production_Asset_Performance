import pandas as pd

DOWNTIME_FILE = r"data\raw\Fact_Downtime_Event.csv"
PRODUCTION_FILE = r"data\raw\Fact_Production_Daily.csv"

downtime = pd.read_csv(
    DOWNTIME_FILE,
    usecols=[
        "Downtime_ID",
        "Well_ID",
        "Date",
        "Duration_hr",
        "Production_Affected",
    ],
)

production = pd.read_csv(
    PRODUCTION_FILE,
    usecols=[
        "Date",
        "Well_ID",
        "Potential_Oil_bbl",
        "Oil_bbl",
        "Runtime_hr",
        "Available_hr",
    ],
)

downtime["Date"] = pd.to_datetime(downtime["Date"])
production["Date"] = pd.to_datetime(production["Date"])


# ------------------------------------------------------------
# 1. Production runtime loss
# ------------------------------------------------------------

production["Runtime_Loss_hr"] = (
    production["Available_hr"] -
    production["Runtime_hr"]
)


# ------------------------------------------------------------
# 2. Match downtime events to production well-day
# ------------------------------------------------------------

m = downtime.merge(
    production,
    on=["Well_ID", "Date"],
    how="left",
    indicator=True,
)

matched = m[m["_merge"] == "both"].copy()
unmatched = m[m["_merge"] != "both"].copy()


# ------------------------------------------------------------
# 3. Runtime integrity
# ------------------------------------------------------------

runtime_over_available = (
    matched["Runtime_hr"] >
    matched["Available_hr"]
).sum()

runtime_nonpositive = (
    matched["Runtime_hr"] <= 0
).sum()

runtime_loss_negative = (
    matched["Runtime_Loss_hr"] < 0
).sum()

runtime_loss_gt_available = (
    matched["Runtime_Loss_hr"] >
    matched["Available_hr"]
).sum()


# ------------------------------------------------------------
# 4. Production_Affected distribution
# ------------------------------------------------------------

affected_counts = (
    matched["Production_Affected"]
    .value_counts()
    .sort_index()
)


# ------------------------------------------------------------
# 5. Production_Affected vs Runtime_Loss
# ------------------------------------------------------------

affected_runtime = (
    matched
    .groupby("Production_Affected", dropna=False)
    .agg(
        Events=("Downtime_ID", "count"),
        Mean_Duration_hr=("Duration_hr", "mean"),
        Median_Duration_hr=("Duration_hr", "median"),
        Total_Duration_hr=("Duration_hr", "sum"),
        Mean_Runtime_Loss_hr=("Runtime_Loss_hr", "mean"),
        Total_Runtime_Loss_hr=("Runtime_Loss_hr", "sum"),
        Min_Runtime_Loss_hr=("Runtime_Loss_hr", "min"),
        Max_Runtime_Loss_hr=("Runtime_Loss_hr", "max"),
        Mean_Oil_bbl=("Oil_bbl", "mean"),
        Mean_Potential_Oil_bbl=("Potential_Oil_bbl", "mean"),
    )
    .reset_index()
)


# ------------------------------------------------------------
# 6. Potentially suspicious combinations
# ------------------------------------------------------------

yes_zero_runtime_loss = matched[
    (matched["Production_Affected"] == "Yes") &
    (matched["Runtime_Loss_hr"] <= 0)
]

no_positive_runtime_loss = matched[
    (matched["Production_Affected"] == "No") &
    (matched["Runtime_Loss_hr"] > 0)
]

yes_zero_oil = matched[
    (matched["Production_Affected"] == "Yes") &
    (matched["Oil_bbl"] <= 0)
]

no_zero_oil = matched[
    (matched["Production_Affected"] == "No") &
    (matched["Oil_bbl"] <= 0)
]


# ------------------------------------------------------------
# 7. Duration vs runtime-loss relationship
# ------------------------------------------------------------

duration_le_runtime_loss = (
    matched["Duration_hr"] <=
    matched["Runtime_Loss_hr"]
).sum()

duration_gt_runtime_loss = (
    matched["Duration_hr"] >
    matched["Runtime_Loss_hr"]
).sum()


# ------------------------------------------------------------
# 8. Output
# ------------------------------------------------------------

print("=" * 72)
print("QA-18 - DOWNTIME COVERAGE VS PRODUCTION AFFECTED / RUNTIME LOSS")
print("=" * 72)

print()
print("COVERAGE")
print("-" * 72)

print(f"Downtime events:                 {len(downtime):,}")
print(f"Matched production well-days:   {len(matched):,}")
print(f"Unmatched downtime events:       {len(unmatched):,}")
print(
    f"Coverage:                        "
    f"{len(matched) / len(downtime) * 100:.2f}%"
)

print()
print("RUNTIME INTEGRITY")
print("-" * 72)

print(f"Runtime > Available:             {runtime_over_available:,}")
print(f"Runtime <= 0:                    {runtime_nonpositive:,}")
print(f"Runtime Loss < 0:                {runtime_loss_negative:,}")
print(
    f"Runtime Loss > Available:        "
    f"{runtime_loss_gt_available:,}"
)

print()
print("PRODUCTION_AFFECTED DISTRIBUTION")
print("-" * 72)

print(affected_counts.to_string())


print()
print("PRODUCTION_AFFECTED VS RUNTIME LOSS")
print("-" * 72)

print(
    affected_runtime.to_string(
        index=False,
        formatters={
            "Mean_Duration_hr": "{:,.2f}".format,
            "Median_Duration_hr": "{:,.2f}".format,
            "Total_Duration_hr": "{:,.2f}".format,
            "Mean_Runtime_Loss_hr": "{:,.2f}".format,
            "Total_Runtime_Loss_hr": "{:,.2f}".format,
            "Min_Runtime_Loss_hr": "{:,.2f}".format,
            "Max_Runtime_Loss_hr": "{:,.2f}".format,
            "Mean_Oil_bbl": "{:,.2f}".format,
            "Mean_Potential_Oil_bbl": "{:,.2f}".format,
        },
    )
)


print()
print("DURATION VS RUNTIME LOSS")
print("-" * 72)

print(f"Duration <= Runtime Loss:        {duration_le_runtime_loss:,}")
print(f"Duration > Runtime Loss:         {duration_gt_runtime_loss:,}")


print()
print("POTENTIALLY SUSPICIOUS COMBINATIONS")
print("-" * 72)

print(
    f"Production_Affected=Yes with Runtime_Loss<=0: "
    f"{len(yes_zero_runtime_loss):,}"
)

print(
    f"Production_Affected=No with Runtime_Loss>0: "
    f"{len(no_positive_runtime_loss):,}"
)

print(
    f"Production_Affected=Yes with Oil_bbl<=0: "
    f"{len(yes_zero_oil):,}"
)

print(
    f"Production_Affected=No with Oil_bbl<=0: "
    f"{len(no_zero_oil):,}"
)


print()
print("EXAMPLES: YES + ZERO RUNTIME LOSS")
print("-" * 72)

if len(yes_zero_runtime_loss):
    print(
        yes_zero_runtime_loss[
            [
                "Downtime_ID",
                "Well_ID",
                "Date",
                "Duration_hr",
                "Production_Affected",
                "Runtime_hr",
                "Available_hr",
                "Runtime_Loss_hr",
                "Oil_bbl",
            ]
        ].to_string(index=False)
    )
else:
    print("None")


print()
print("STATUS")
print("-" * 72)

if (
    len(unmatched) == 0
    and runtime_over_available == 0
    and runtime_nonpositive == 0
    and runtime_loss_negative == 0
    and runtime_loss_gt_available == 0
    and len(yes_zero_oil) == 0
    and len(no_zero_oil) == 0
):
    print(
        "PASS - Downtime events have complete production coverage "
        "and production/runtime controls are valid."
    )
else:
    print(
        "REVIEW - One or more coverage, runtime, or production "
        "consistency conditions require investigation."
    )
