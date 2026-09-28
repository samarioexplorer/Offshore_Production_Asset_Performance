-- ============================================================================
-- PHASE 5C.2 — RELIABILITY ANALYTICS SUMMARY
-- Offshore Production Asset Performance
--
-- Purpose:
--     Create analytics-ready reliability views from the validated relational
--     downtime model.
--
-- Design principles:
--     1. Core fact tables remain unchanged.
--     2. Downtime events remain the authoritative reliability source.
--     3. Views provide reusable analytical interfaces.
--     4. Production impact is not recalculated here.
--     5. Reliability metrics remain traceable to source events.
-- ============================================================================


-- ============================================================================
-- 1. DOWNTIME EVENT ANALYTICS
-- ============================================================================

DROP VIEW IF EXISTS vw_Downtime_Summary;

CREATE VIEW vw_Downtime_Summary AS
SELECT
    d.Downtime_ID,
    d.Date,
    d.Well_ID,
    d.Equipment_ID,
    d.Failure_Cause_ID,

    d.Downtime_Type,
    d.Start_Hour,
    d.Duration_hr,
    d.Severity,
    d.Failure_Severity,
    d.Planned_Flag,
    d.Production_Affected,

    w.Well_Name,
    w.Well_Type,
    w.Field_ID,
    w.Manifold_ID,

    e.Equipment_Name,
    e.Equipment_Type,
    e.Equipment_Category,
    e.Criticality,

    fc.Failure_Category,
    fc.Failure_Cause

FROM Fact_Downtime_Event AS d

LEFT JOIN Dim_Well AS w
    ON d.Well_ID = w.Well_ID

LEFT JOIN Dim_Equipment AS e
    ON d.Equipment_ID = e.Equipment_ID

LEFT JOIN Dim_Failure_Cause AS fc
    ON d.Failure_Cause_ID = fc.Failure_Cause_ID;


-- ============================================================================
-- 2. FAILURE CAUSE ANALYSIS
-- ============================================================================

DROP VIEW IF EXISTS vw_Failure_Cause_Analysis;

CREATE VIEW vw_Failure_Cause_Analysis AS
SELECT
    d.Failure_Cause_ID,

    fc.Failure_Category,
    fc.Failure_Cause,
    fc.Severity AS Reference_Severity,

    COUNT(*) AS Downtime_Event_Count,

    SUM(d.Duration_hr) AS Downtime_Hours,

    AVG(d.Duration_hr) AS Average_Downtime_Hours,

    MAX(d.Duration_hr) AS Maximum_Downtime_Hours,

    SUM(
        CASE
            WHEN d.Production_Affected = 'Yes' THEN 1
            ELSE 0
        END
    ) AS Production_Affected_Events,

    SUM(
        CASE
            WHEN d.Planned_Flag = 1 THEN 1
            ELSE 0
        END
    ) AS Planned_Events,

    SUM(
        CASE
            WHEN d.Planned_Flag = 0 THEN 1
            ELSE 0
        END
    ) AS Unplanned_Events

FROM Fact_Downtime_Event AS d

LEFT JOIN Dim_Failure_Cause AS fc
    ON d.Failure_Cause_ID = fc.Failure_Cause_ID

GROUP BY
    d.Failure_Cause_ID,
    fc.Failure_Category,
    fc.Failure_Cause,
    fc.Severity;


-- ============================================================================
-- 3. WELL RELIABILITY SUMMARY
-- ============================================================================

DROP VIEW IF EXISTS vw_Well_Reliability_Summary;

CREATE VIEW vw_Well_Reliability_Summary AS
SELECT
    d.Well_ID,

    w.Well_Name,
    w.Well_Type,
    w.Field_ID,
    w.Manifold_ID,
    w.Reservoir,
    w.Artificial_Lift_Type,

    COUNT(*) AS Downtime_Event_Count,

    SUM(d.Duration_hr) AS Downtime_Hours,

    AVG(d.Duration_hr) AS Average_Downtime_Hours,

    MAX(d.Duration_hr) AS Maximum_Downtime_Hours,

    SUM(
        CASE
            WHEN d.Production_Affected = 'Yes' THEN 1
            ELSE 0
        END
    ) AS Production_Affected_Events,

    SUM(
        CASE
            WHEN d.Planned_Flag = 1 THEN 1
            ELSE 0
        END
    ) AS Planned_Events,

    SUM(
        CASE
            WHEN d.Planned_Flag = 0 THEN 1
            ELSE 0
        END
    ) AS Unplanned_Events,

    SUM(
        CASE
            WHEN d.Severity = 'High' THEN 1
            ELSE 0
        END
    ) AS High_Severity_Events,

    SUM(
        CASE
            WHEN d.Severity = 'Medium' THEN 1
            ELSE 0
        END
    ) AS Medium_Severity_Events,

    SUM(
        CASE
            WHEN d.Severity = 'Low' THEN 1
            ELSE 0
        END
    ) AS Low_Severity_Events

FROM Fact_Downtime_Event AS d

LEFT JOIN Dim_Well AS w
    ON d.Well_ID = w.Well_ID

GROUP BY
    d.Well_ID,
    w.Well_Name,
    w.Well_Type,
    w.Field_ID,
    w.Manifold_ID,
    w.Reservoir,
    w.Artificial_Lift_Type;