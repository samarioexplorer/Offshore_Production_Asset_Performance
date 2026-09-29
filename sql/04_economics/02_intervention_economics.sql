-- ============================================================================
-- PHASE 5C.4 — INTERVENTION ECONOMICS
-- Offshore Production Asset Performance
--
-- Purpose:
--     Create event-grain intervention economics analytics.
--
-- Design principles:
--     1. Intervention cost remains at intervention-event grain.
--     2. Intervention cost is never summed from daily production rows.
--     3. No modification of source or core tables.
--     4. Completed and cancelled interventions remain distinguishable.
--     5. Production recovery / ROI is not inferred without an explicit
--        attribution methodology.
-- ============================================================================


-- ============================================================================
-- 1. INTERVENTION ECONOMICS
-- Grain: Intervention Event
-- ============================================================================

DROP VIEW IF EXISTS vw_Intervention_Economics;

CREATE VIEW vw_Intervention_Economics AS
SELECT
    i.Intervention_ID,
    i.Well_ID,
    w.Field_ID,
    w.Manifold_ID,

    i.Intervention_Type_ID,
    d.Intervention_Type,
    d.Intervention_Category,

    i.Start_Date,
    i.End_Date,
    i.Duration_Days,

    i.Expected_Oil_Rate_bopd,
    i.Target_Recovery_pct,

    i.Intervention_Cost_USD,
    i.Status,

    CASE
        WHEN i.Duration_Days > 0
        THEN i.Intervention_Cost_USD / i.Duration_Days
        ELSE NULL
    END AS Cost_per_Intervention_Day_USD,

    CASE
        WHEN i.Expected_Oil_Rate_bopd > 0
        THEN i.Intervention_Cost_USD
             / i.Expected_Oil_Rate_bopd
        ELSE NULL
    END AS Cost_per_Expected_bopd_USD,

    CASE
        WHEN i.Status = 'Completed'
        THEN 1
        ELSE 0
    END AS Completed_Flag,

    CASE
        WHEN i.Status = 'Cancelled'
        THEN 1
        ELSE 0
    END AS Cancelled_Flag

FROM Fact_Intervention_Event i

INNER JOIN Dim_Well w
    ON i.Well_ID = w.Well_ID

INNER JOIN Dim_Intervention d
    ON i.Intervention_Type_ID = d.Intervention_Type_ID;


-- ============================================================================
-- 2. INTERVENTION WELL SUMMARY
-- Grain: Well
-- ============================================================================

DROP VIEW IF EXISTS vw_Intervention_Well_Summary;

CREATE VIEW vw_Intervention_Well_Summary AS
SELECT
    Well_ID,
    Field_ID,
    Manifold_ID,

    COUNT(*) AS Intervention_Count,

    SUM(Completed_Flag)
        AS Completed_Interventions,

    SUM(Cancelled_Flag)
        AS Cancelled_Interventions,

    SUM(Duration_Days)
        AS Total_Intervention_Days,

    SUM(Intervention_Cost_USD)
        AS Total_Intervention_Cost_USD,

    AVG(Expected_Oil_Rate_bopd)
        AS Avg_Expected_Oil_Rate_bopd,

    AVG(Target_Recovery_pct)
        AS Avg_Target_Recovery_pct,

    CASE
        WHEN SUM(Duration_Days) > 0
        THEN SUM(Intervention_Cost_USD)
             / SUM(Duration_Days)
        ELSE NULL
    END AS Cost_per_Intervention_Day_USD

FROM vw_Intervention_Economics

GROUP BY
    Well_ID,
    Field_ID,
    Manifold_ID;


-- ============================================================================
-- 3. INTERVENTION TYPE SUMMARY
-- Grain: Intervention Type
-- ============================================================================

DROP VIEW IF EXISTS vw_Intervention_Type_Summary;

CREATE VIEW vw_Intervention_Type_Summary AS
SELECT
    Intervention_Type_ID,
    Intervention_Type,
    Intervention_Category,

    COUNT(*) AS Intervention_Count,

    SUM(Completed_Flag)
        AS Completed_Interventions,

    SUM(Cancelled_Flag)
        AS Cancelled_Interventions,

    SUM(Duration_Days)
        AS Total_Intervention_Days,

    SUM(Intervention_Cost_USD)
        AS Total_Intervention_Cost_USD,

    AVG(Intervention_Cost_USD)
        AS Avg_Intervention_Cost_USD,

    AVG(Expected_Oil_Rate_bopd)
        AS Avg_Expected_Oil_Rate_bopd,

    AVG(Target_Recovery_pct)
        AS Avg_Target_Recovery_pct,

    AVG(Cost_per_Intervention_Day_USD)
        AS Avg_Cost_per_Intervention_Day_USD,

    AVG(Cost_per_Expected_bopd_USD)
        AS Avg_Cost_per_Expected_bopd_USD

FROM vw_Intervention_Economics

GROUP BY
    Intervention_Type_ID,
    Intervention_Type,
    Intervention_Category;


-- ============================================================================
-- 4. ANNUAL INTERVENTION SUMMARY
-- Grain: Year
-- ============================================================================

DROP VIEW IF EXISTS vw_Intervention_Annual_Summary;

CREATE VIEW vw_Intervention_Annual_Summary AS
SELECT
    CAST(strftime('%Y', Start_Date) AS INTEGER)
        AS Year,

    COUNT(*) AS Intervention_Count,

    SUM(Completed_Flag)
        AS Completed_Interventions,

    SUM(Cancelled_Flag)
        AS Cancelled_Interventions,

    SUM(Duration_Days)
        AS Total_Intervention_Days,

    SUM(Intervention_Cost_USD)
        AS Total_Intervention_Cost_USD,

    AVG(Intervention_Cost_USD)
        AS Avg_Intervention_Cost_USD,

    AVG(Expected_Oil_Rate_bopd)
        AS Avg_Expected_Oil_Rate_bopd,

    AVG(Target_Recovery_pct)
        AS Avg_Target_Recovery_pct,

    AVG(Cost_per_Intervention_Day_USD)
        AS Avg_Cost_per_Intervention_Day_USD

FROM vw_Intervention_Economics

GROUP BY
    CAST(strftime('%Y', Start_Date) AS INTEGER);