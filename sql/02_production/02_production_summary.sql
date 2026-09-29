-- ============================================================================
-- PHASE 5C.1 — PRODUCTION ANALYTICS SUMMARY
-- Offshore Production Asset Performance
--
-- Purpose:
--     Create analytics-ready production views from the validated relational
--     core model.
--
-- Design principles:
--     1. Core fact tables remain unchanged.
--     2. No production-generation logic is recreated here.
--     3. Views provide reusable analytical interfaces.
--     4. Daily production impact remains the authoritative production source.
--     5. Monthly and well-level summaries are derived from daily records.
-- ============================================================================


-- ============================================================================
-- 1. DAILY PRODUCTION ANALYTICS
-- ============================================================================

DROP VIEW IF EXISTS vw_Production_Daily;

CREATE VIEW vw_Production_Daily AS
SELECT
    i.Date,
    i.Well_ID,

    w.Well_Name,
    w.Well_Type,
    w.Field_ID,
    w.Manifold_ID,
    w.Reservoir,
    w.Artificial_Lift_Type,

    i.Potential_Oil_bbl,
    i.Baseline_Oil_bbl,
    i.Actual_Oil_bbl,
    i.Deferred_Oil_bbl,

    i.Intervention_Flag,
    i.Intervention_ID,
    i.Intervention_Type_ID

FROM Fact_Production_Impact_Daily AS i
LEFT JOIN Dim_Well AS w
    ON i.Well_ID = w.Well_ID;


-- ============================================================================
-- 2. MONTHLY FIELD PRODUCTION
-- ============================================================================

DROP VIEW IF EXISTS vw_Production_Monthly;

CREATE VIEW vw_Production_Monthly AS
SELECT
    substr(Date, 1, 7) AS Production_Month,

    SUM(Potential_Oil_bbl) AS Potential_Oil_bbl,
    SUM(Baseline_Oil_bbl) AS Baseline_Oil_bbl,
    SUM(Actual_Oil_bbl) AS Actual_Oil_bbl,
    SUM(Deferred_Oil_bbl) AS Deferred_Oil_bbl,

    CASE
        WHEN SUM(Potential_Oil_bbl) = 0 THEN NULL
        ELSE
            SUM(Deferred_Oil_bbl)
            / SUM(Potential_Oil_bbl)
    END AS Deferred_Oil_pct,

    COUNT(DISTINCT Well_ID) AS Producer_Well_Count,
    COUNT(*) AS Producer_Days

FROM Fact_Production_Impact_Daily

GROUP BY
    substr(Date, 1, 7)

ORDER BY
    Production_Month;


-- ============================================================================
-- 3. ANNUAL FIELD PRODUCTION
-- ============================================================================

DROP VIEW IF EXISTS vw_Production_Annual;

CREATE VIEW vw_Production_Annual AS
SELECT
    substr(Date, 1, 4) AS Production_Year,

    SUM(Potential_Oil_bbl) AS Potential_Oil_bbl,
    SUM(Baseline_Oil_bbl) AS Baseline_Oil_bbl,
    SUM(Actual_Oil_bbl) AS Actual_Oil_bbl,
    SUM(Deferred_Oil_bbl) AS Deferred_Oil_bbl,

    CASE
        WHEN SUM(Potential_Oil_bbl) = 0 THEN NULL
        ELSE
            SUM(Deferred_Oil_bbl)
            / SUM(Potential_Oil_bbl)
    END AS Deferred_Oil_pct,

    COUNT(DISTINCT Well_ID) AS Producer_Well_Count,
    COUNT(*) AS Producer_Days

FROM Fact_Production_Impact_Daily

GROUP BY
    substr(Date, 1, 4)

ORDER BY
    Production_Year;


-- ============================================================================
-- 4. WELL PRODUCTION SUMMARY
-- ============================================================================

DROP VIEW IF EXISTS vw_Well_Production_Summary;

CREATE VIEW vw_Well_Production_Summary AS
SELECT
    i.Well_ID,

    w.Well_Name,
    w.Well_Type,
    w.Field_ID,
    w.Manifold_ID,
    w.Reservoir,
    w.Water_Depth_ft,
    w.Initial_Oil_Rate_bopd,
    w.Decline_Rate_pct,
    w.Initial_Water_Cut_pct,
    w.Artificial_Lift_Type,

    MIN(i.Date) AS First_Production_Record,
    MAX(i.Date) AS Last_Production_Record,

    COUNT(*) AS Production_Days,

    SUM(i.Potential_Oil_bbl) AS Potential_Oil_bbl,
    SUM(i.Baseline_Oil_bbl) AS Baseline_Oil_bbl,
    SUM(i.Actual_Oil_bbl) AS Actual_Oil_bbl,
    SUM(i.Deferred_Oil_bbl) AS Deferred_Oil_bbl,

    CASE
        WHEN SUM(i.Potential_Oil_bbl) = 0 THEN NULL
        ELSE
            SUM(i.Deferred_Oil_bbl)
            / SUM(i.Potential_Oil_bbl)
    END AS Deferred_Oil_pct,

    SUM(
        CASE
            WHEN i.Intervention_Flag = 1 THEN 1
            ELSE 0
        END
    ) AS Intervention_Impact_Days

FROM Fact_Production_Impact_Daily AS i

LEFT JOIN Dim_Well AS w
    ON i.Well_ID = w.Well_ID

GROUP BY
    i.Well_ID,
    w.Well_Name,
    w.Well_Type,
    w.Field_ID,
    w.Manifold_ID,
    w.Reservoir,
    w.Water_Depth_ft,
    w.Initial_Oil_Rate_bopd,
    w.Decline_Rate_pct,
    w.Initial_Water_Cut_pct,
    w.Artificial_Lift_Type;


-- ============================================================================
-- 5. FIELD PRODUCTION SUMMARY
-- ============================================================================

DROP VIEW IF EXISTS vw_Field_Production_Summary;

CREATE VIEW vw_Field_Production_Summary AS
SELECT
    f.Field_ID,
    f.Field_Name,

    MIN(i.Date) AS First_Production_Record,
    MAX(i.Date) AS Last_Production_Record,

    COUNT(*) AS Producer_Days,
    COUNT(DISTINCT i.Well_ID) AS Producer_Well_Count,

    SUM(i.Potential_Oil_bbl) AS Potential_Oil_bbl,
    SUM(i.Baseline_Oil_bbl) AS Baseline_Oil_bbl,
    SUM(i.Actual_Oil_bbl) AS Actual_Oil_bbl,
    SUM(i.Deferred_Oil_bbl) AS Deferred_Oil_bbl,

    CASE
        WHEN SUM(i.Potential_Oil_bbl) = 0 THEN NULL
        ELSE
            SUM(i.Deferred_Oil_bbl)
            / SUM(i.Potential_Oil_bbl)
    END AS Deferred_Oil_pct,

    SUM(
        CASE
            WHEN i.Intervention_Flag = 1 THEN 1
            ELSE 0
        END
    ) AS Intervention_Impact_Days

FROM Fact_Production_Impact_Daily AS i

LEFT JOIN Dim_Well AS w
    ON i.Well_ID = w.Well_ID

LEFT JOIN Dim_Field AS f
    ON w.Field_ID = f.Field_ID

GROUP BY
    f.Field_ID,
    f.Field_Name;