-- ============================================================================
-- PHASE 5B.2 — CORE RELATIONAL LOAD
-- Offshore Production Asset Performance
--
-- Purpose:
--     Promote validated staging data into the relational core model.
--
-- Design principles:
--     1. No business transformations.
--     2. Staging remains the source layer.
--     3. Core tables enforce relational integrity.
--     4. Dimensions load before facts.
--     5. Transactional execution.
-- ============================================================================

BEGIN TRANSACTION;

-- ============================================================================
-- 1. CLEAR CORE TABLES
-- Reverse dependency order supports safe reruns.
-- ============================================================================

DELETE FROM Fact_Production_Impact_Daily;
DELETE FROM Fact_Intervention_Event;
DELETE FROM Fact_Downtime_Event;
DELETE FROM Fact_Production_Daily;

DELETE FROM Dim_Scenario;
DELETE FROM Dim_Intervention;
DELETE FROM Dim_Failure_Cause;
DELETE FROM Dim_Equipment;
DELETE FROM Dim_Well;
DELETE FROM Dim_Manifold;
DELETE FROM Dim_Field;
DELETE FROM Dim_Date;

-- ============================================================================
-- 2. LOAD DIMENSIONS
-- ============================================================================

INSERT INTO Dim_Date (
    Date,
    Year,
    Quarter,
    Month,
    Month_Name,
    Month_Start,
    Year_Month,
    Day,
    Day_of_Week,
    Day_Name
)
SELECT
    Date,
    Year,
    Quarter,
    Month,
    Month_Name,
    Month_Start,
    Year_Month,
    Day,
    Day_of_Week,
    Day_Name
FROM stg_Dim_Date;

INSERT INTO Dim_Field (
    Field_ID,
    Field_Name,
    Basin,
    Development_Type,
    Water_Depth_ft,
    Operator_Type,
    First_Production_Date,
    FPSO_Name
)
SELECT
    Field_ID,
    Field_Name,
    Basin,
    Development_Type,
    Water_Depth_ft,
    Operator_Type,
    First_Production_Date,
    FPSO_Name
FROM stg_Dim_Field;

INSERT INTO Dim_Manifold (
    Manifold_ID,
    Manifold_Name,
    Field_ID,
    Water_Depth_ft,
    Well_Count,
    Installation_Date,
    Status
)
SELECT
    Manifold_ID,
    Manifold_Name,
    Field_ID,
    Water_Depth_ft,
    Well_Count,
    Installation_Date,
    Status
FROM stg_Dim_Manifold;

INSERT INTO Dim_Well (
    Well_ID,
    Well_Name,
    Well_Type,
    Field_ID,
    Manifold_ID,
    Reservoir,
    Water_Depth_ft,
    Spud_Date,
    First_Production_Date,
    Well_Status,
    Initial_Oil_Rate_bopd,
    Initial_Gas_Rate_Mscfd,
    Decline_Rate_pct,
    Initial_Water_Cut_pct,
    Artificial_Lift_Type
)
SELECT
    Well_ID,
    Well_Name,
    Well_Type,
    Field_ID,
    Manifold_ID,
    Reservoir,
    Water_Depth_ft,
    Spud_Date,
    First_Production_Date,
    Well_Status,
    Initial_Oil_Rate_bopd,
    Initial_Gas_Rate_Mscfd,
    Decline_Rate_pct,
    Initial_Water_Cut_pct,
    Artificial_Lift_Type
FROM stg_Dim_Well;

INSERT INTO Dim_Equipment (
    Equipment_ID,
    Equipment_Name,
    Equipment_Type,
    Equipment_Category,
    Parent_Equipment_ID,
    Field_ID,
    Criticality,
    Installation_Date,
    Design_Life_Years,
    Status
)
SELECT
    Equipment_ID,
    Equipment_Name,
    Equipment_Type,
    Equipment_Category,
    Parent_Equipment_ID,
    Field_ID,
    Criticality,
    Installation_Date,
    Design_Life_Years,
    Status
FROM stg_Dim_Equipment;

INSERT INTO Dim_Failure_Cause (
    Failure_Cause_ID,
    Failure_Category,
    Failure_Cause,
    Severity,
    Planned_Flag
)
SELECT
    Failure_Cause_ID,
    Failure_Category,
    Failure_Cause,
    Severity,
    Planned_Flag
FROM stg_Dim_Failure_Cause;

INSERT INTO Dim_Intervention (
    Intervention_Type_ID,
    Intervention_Type,
    Intervention_Category,
    Typical_Duration_hr,
    Typical_Cost_USD
)
SELECT
    Intervention_Type_ID,
    Intervention_Type,
    Intervention_Category,
    Typical_Duration_hr,
    Typical_Cost_USD
FROM stg_Dim_Intervention;

INSERT INTO Dim_Scenario (
    Scenario_ID,
    Scenario_Name,
    Oil_Price_USD_bbl
)
SELECT
    Scenario_ID,
    Scenario_Name,
    Oil_Price_USD_bbl
FROM stg_Dim_Scenario;

-- ============================================================================
-- 3. LOAD FACT TABLES
-- ============================================================================

INSERT INTO Fact_Production_Daily (
    Date,
    Well_ID,
    Potential_Oil_bbl,
    Oil_bbl,
    Gas_Mscf,
    Water_bbl,
    Liquid_bbl,
    Runtime_hr,
    Available_hr
)
SELECT
    Date,
    Well_ID,
    Potential_Oil_bbl,
    Oil_bbl,
    Gas_Mscf,
    Water_bbl,
    Liquid_bbl,
    Runtime_hr,
    Available_hr
FROM stg_Fact_Production_Daily;

INSERT INTO Fact_Downtime_Event (
    Downtime_ID,
    Date,
    Well_ID,
    Equipment_ID,
    Failure_Cause_ID,
    Downtime_Type,
    Start_Hour,
    Duration_hr,
    Severity,
    Failure_Severity,
    Planned_Flag,
    Production_Affected
)
SELECT
    Downtime_ID,
    Date,
    Well_ID,
    Equipment_ID,
    Failure_Cause_ID,
    Downtime_Type,
    Start_Hour,
    Duration_hr,
    Severity,
    Failure_Severity,
    Planned_Flag,
    Production_Affected
FROM stg_Fact_Downtime_Event;

INSERT INTO Fact_Intervention_Event (
    Intervention_ID,
    Well_ID,
    Intervention_Type_ID,
    Start_Date,
    End_Date,
    Duration_Days,
    Expected_Oil_Rate_bopd,
    Target_Recovery_pct,
    Intervention_Cost_USD,
    Status
)
SELECT
    Intervention_ID,
    Well_ID,
    Intervention_Type_ID,
    Start_Date,
    End_Date,
    Duration_Days,
    Expected_Oil_Rate_bopd,
    Target_Recovery_pct,
    Intervention_Cost_USD,
    Status
FROM stg_Fact_Intervention_Event;

INSERT INTO Fact_Production_Impact_Daily (
    Date,
    Well_ID,
    Potential_Oil_bbl,
    Baseline_Oil_bbl,
    Downtime_Hours,
    Effective_Downtime_Hours,
    Available_hr,
    Downtime_Event_Count,
    Downtime_Deferred_Oil_bbl,
    Intervention_Flag,
    Intervention_ID,
    Intervention_Type_ID,
    Intervention_Days,
    Intervention_Recovery_pct,
    Expected_Oil_Rate_bopd,
    Intervention_Cost_USD,
    Intervention_Recovery_Oil_bbl,
    Intervention_Production_Loss_bbl,
    Actual_Oil_bbl,
    Deferred_Oil_bbl,
    Production_Impact_bbl,
    Production_Availability_pct,
    Production_Efficiency_pct,
    Production_Impact_Flag
)
SELECT
    Date,
    Well_ID,
    Potential_Oil_bbl,
    Baseline_Oil_bbl,
    Downtime_Hours,
    Effective_Downtime_Hours,
    Available_hr,
    Downtime_Event_Count,
    Downtime_Deferred_Oil_bbl,
    Intervention_Flag,
    Intervention_ID,
    Intervention_Type_ID,
    Intervention_Days,
    Intervention_Recovery_pct,
    Expected_Oil_Rate_bopd,
    Intervention_Cost_USD,
    Intervention_Recovery_Oil_bbl,
    Intervention_Production_Loss_bbl,
    Actual_Oil_bbl,
    Deferred_Oil_bbl,
    Production_Impact_bbl,
    Production_Availability_pct,
    Production_Efficiency_pct,
    Production_Impact_Flag
FROM stg_Fact_Production_Impact_Daily;

COMMIT;