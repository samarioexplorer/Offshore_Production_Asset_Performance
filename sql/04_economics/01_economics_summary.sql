-- ============================================================================
-- PHASE 5C.3 — ECONOMICS ANALYTICS
-- Offshore Production Asset Performance
--
-- Purpose:
--     Create scenario-based economics views from the validated production
--     impact model.
--
-- Design principles:
--     1. No modification of source fact or dimension tables.
--     2. Oil price comes exclusively from Dim_Scenario.
--     3. Physical production remains scenario-independent.
--     4. Economic valuation changes only with scenario oil price.
--     5. Production reconciliation established in Phase 5B.2 is preserved.
-- ============================================================================


-- ============================================================================
-- 1. DAILY ECONOMICS
-- Grain: Date × Well × Scenario
-- ============================================================================

DROP VIEW IF EXISTS vw_Economics_Daily;

CREATE VIEW vw_Economics_Daily AS
SELECT
    p.Date,
    p.Well_ID,

    s.Scenario_ID,
    s.Scenario_Name,
    s.Oil_Price_USD_bbl,

    p.Potential_Oil_bbl,
    p.Actual_Oil_bbl,
    p.Deferred_Oil_bbl,
    p.Production_Impact_bbl,

    p.Potential_Oil_bbl
        * s.Oil_Price_USD_bbl
        AS Potential_Revenue_USD,

    p.Actual_Oil_bbl
        * s.Oil_Price_USD_bbl
        AS Actual_Revenue_USD,

    p.Deferred_Oil_bbl
        * s.Oil_Price_USD_bbl
        AS Deferred_Value_USD,

    p.Production_Impact_bbl
        * s.Oil_Price_USD_bbl
        AS Production_Impact_Value_USD

FROM Fact_Production_Impact_Daily p
CROSS JOIN Dim_Scenario s;


-- ============================================================================
-- 2. WELL ECONOMICS SUMMARY
-- Grain: Well × Scenario
-- ============================================================================

DROP VIEW IF EXISTS vw_Economics_Well_Summary;

CREATE VIEW vw_Economics_Well_Summary AS
SELECT
    Well_ID,
    Scenario_ID,
    Scenario_Name,
    Oil_Price_USD_bbl,

    SUM(Potential_Oil_bbl)
        AS Potential_Oil_bbl,

    SUM(Actual_Oil_bbl)
        AS Actual_Oil_bbl,

    SUM(Deferred_Oil_bbl)
        AS Deferred_Oil_bbl,

    SUM(Production_Impact_bbl)
        AS Production_Impact_bbl,

    SUM(Potential_Oil_bbl)
        * Oil_Price_USD_bbl
        AS Potential_Revenue_USD,

    SUM(Actual_Oil_bbl)
        * Oil_Price_USD_bbl
        AS Actual_Revenue_USD,

    SUM(Deferred_Oil_bbl)
        * Oil_Price_USD_bbl
        AS Deferred_Value_USD,

    SUM(Production_Impact_bbl)
        * Oil_Price_USD_bbl
        AS Production_Impact_Value_USD

FROM vw_Economics_Daily

GROUP BY
    Well_ID,
    Scenario_ID,
    Scenario_Name,
    Oil_Price_USD_bbl;


-- ============================================================================
-- 3. FIELD ECONOMICS SUMMARY
-- Grain: Field × Scenario
-- ============================================================================

DROP VIEW IF EXISTS vw_Economics_Field_Summary;

CREATE VIEW vw_Economics_Field_Summary AS
SELECT
    w.Field_ID,

    e.Scenario_ID,
    e.Scenario_Name,
    e.Oil_Price_USD_bbl,

    SUM(e.Potential_Oil_bbl)
        AS Potential_Oil_bbl,

    SUM(e.Actual_Oil_bbl)
        AS Actual_Oil_bbl,

    SUM(e.Deferred_Oil_bbl)
        AS Deferred_Oil_bbl,

    SUM(e.Production_Impact_bbl)
        AS Production_Impact_bbl,

    SUM(e.Potential_Revenue_USD)
        AS Potential_Revenue_USD,

    SUM(e.Actual_Revenue_USD)
        AS Actual_Revenue_USD,

    SUM(e.Deferred_Value_USD)
        AS Deferred_Value_USD,

    SUM(e.Production_Impact_Value_USD)
        AS Production_Impact_Value_USD

FROM vw_Economics_Daily e

INNER JOIN Dim_Well w
    ON e.Well_ID = w.Well_ID

GROUP BY
    w.Field_ID,
    e.Scenario_ID,
    e.Scenario_Name,
    e.Oil_Price_USD_bbl;


-- ============================================================================
-- 4. SCENARIO ECONOMICS SUMMARY
-- Grain: Scenario
-- ============================================================================

DROP VIEW IF EXISTS vw_Economics_Scenario_Summary;

CREATE VIEW vw_Economics_Scenario_Summary AS
SELECT
    Scenario_ID,
    Scenario_Name,
    Oil_Price_USD_bbl,

    SUM(Potential_Oil_bbl)
        AS Potential_Oil_bbl,

    SUM(Actual_Oil_bbl)
        AS Actual_Oil_bbl,

    SUM(Deferred_Oil_bbl)
        AS Deferred_Oil_bbl,

    SUM(Production_Impact_bbl)
        AS Production_Impact_bbl,

    SUM(Potential_Revenue_USD)
        AS Potential_Revenue_USD,

    SUM(Actual_Revenue_USD)
        AS Actual_Revenue_USD,

    SUM(Deferred_Value_USD)
        AS Deferred_Value_USD,

    SUM(Production_Impact_Value_USD)
        AS Production_Impact_Value_USD

FROM vw_Economics_Daily

GROUP BY
    Scenario_ID,
    Scenario_Name,
    Oil_Price_USD_bbl;


-- ============================================================================
-- 5. ANNUAL ECONOMICS SUMMARY
-- Grain: Year × Scenario
-- ============================================================================

DROP VIEW IF EXISTS vw_Economics_Annual_Summary;

CREATE VIEW vw_Economics_Annual_Summary AS
SELECT
    CAST(strftime('%Y', Date) AS INTEGER)
        AS Year,

    Scenario_ID,
    Scenario_Name,
    Oil_Price_USD_bbl,

    SUM(Potential_Oil_bbl)
        AS Potential_Oil_bbl,

    SUM(Actual_Oil_bbl)
        AS Actual_Oil_bbl,

    SUM(Deferred_Oil_bbl)
        AS Deferred_Oil_bbl,

    SUM(Production_Impact_bbl)
        AS Production_Impact_bbl,

    SUM(Potential_Revenue_USD)
        AS Potential_Revenue_USD,

    SUM(Actual_Revenue_USD)
        AS Actual_Revenue_USD,

    SUM(Deferred_Value_USD)
        AS Deferred_Value_USD,

    SUM(Production_Impact_Value_USD)
        AS Production_Impact_Value_USD

FROM vw_Economics_Daily

GROUP BY
    CAST(strftime('%Y', Date) AS INTEGER),
    Scenario_ID,
    Scenario_Name,
    Oil_Price_USD_bbl;