-- ============================================================================
-- OFFSHORE PRODUCTION ASSET PERFORMANCE
-- PHASE 5A — SQLITE DATABASE INITIALIZATION
-- ============================================================================
--
-- Purpose:
--   Initialize the SQLite database architecture.
--
-- Scope:
--   1. Database metadata
--   2. Staging tables
--   3. Core relational tables
--   4. Indexes
--   5. Staging-load audit
--
-- Source of truth:
--   Phase 4E validated CSV data layer
--
-- Principle:
--   Phase 5A defines database structure only.
--   Phase 5B performs controlled CSV -> SQLite loading.
--   No analytical transformations are performed here.
--
-- ============================================================================


-- ============================================================================
-- 1. DATABASE METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS Database_Metadata (
    Metadata_Key   TEXT PRIMARY KEY,
    Metadata_Value TEXT NOT NULL
);


INSERT OR REPLACE INTO Database_Metadata
    (Metadata_Key, Metadata_Value)
VALUES
    ('Project', 'Offshore Production Asset Performance'),
    ('Project_Version', '1.0.0'),
    ('Database_Version', '1.0.0'),
    ('Source_Data_Phase', 'Phase 4E'),
    ('Database_Layer', 'SQLite'),
    ('Created_Date', '2026-09-28'),
    ('Data_Start_Date', '2023-01-01'),
    ('Data_End_Date', '2026-12-31');


-- ============================================================================
-- 2. STAGING TABLES
-- ============================================================================
--
-- Staging tables mirror the validated CSV structures.
-- No business transformations are applied.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 2.1 Dimensions
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS stg_Dim_Date (
    Date TEXT,
    Year INTEGER,
    Quarter INTEGER,
    Month INTEGER,
    Month_Name TEXT,
    Month_Start TEXT,
    Year_Month TEXT,
    Day INTEGER,
    Day_of_Week INTEGER,
    Day_Name TEXT
);


CREATE TABLE IF NOT EXISTS stg_Dim_Field (
    Field_ID TEXT,
    Field_Name TEXT,
    Basin TEXT,
    Development_Type TEXT,
    Water_Depth_ft REAL,
    Operator_Type TEXT,
    First_Production_Date TEXT,
    FPSO_Name TEXT
);


CREATE TABLE IF NOT EXISTS stg_Dim_Manifold (
    Manifold_ID TEXT,
    Manifold_Name TEXT,
    Field_ID TEXT,
    Water_Depth_ft REAL,
    Well_Count INTEGER,
    Installation_Date TEXT,
    Status TEXT
);


CREATE TABLE IF NOT EXISTS stg_Dim_Well (
    Well_ID TEXT,
    Well_Name TEXT,
    Well_Type TEXT,
    Field_ID TEXT,
    Manifold_ID TEXT,
    Reservoir TEXT,
    Water_Depth_ft REAL,
    Spud_Date TEXT,
    First_Production_Date TEXT,
    Well_Status TEXT,
    Initial_Oil_Rate_bopd REAL,
    Initial_Gas_Rate_Mscfd REAL,
    Decline_Rate_pct REAL,
    Initial_Water_Cut_pct REAL,
    Artificial_Lift_Type TEXT
);


CREATE TABLE IF NOT EXISTS stg_Dim_Equipment (
    Equipment_ID TEXT,
    Equipment_Name TEXT,
    Equipment_Type TEXT,
    Equipment_Category TEXT,
    Parent_Equipment_ID TEXT,
    Field_ID TEXT,
    Criticality TEXT,
    Installation_Date TEXT,
    Design_Life_Years REAL,
    Status TEXT
);


CREATE TABLE IF NOT EXISTS stg_Dim_Failure_Cause (
    Failure_Cause_ID TEXT,
    Failure_Category TEXT,
    Failure_Cause TEXT,
    Severity TEXT,
    Planned_Flag INTEGER
);


CREATE TABLE IF NOT EXISTS stg_Dim_Intervention (
    Intervention_Type_ID TEXT,
    Intervention_Type TEXT,
    Intervention_Category TEXT,
    Typical_Duration_hr REAL,
    Typical_Cost_USD REAL
);


CREATE TABLE IF NOT EXISTS stg_Dim_Scenario (
    Scenario_ID TEXT,
    Scenario_Name TEXT,
    Oil_Price_USD_bbl REAL
);


-- ----------------------------------------------------------------------------
-- 2.2 Fact tables
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS stg_Fact_Production_Daily (
    Date TEXT,
    Well_ID TEXT,
    Oil_bbl REAL,
    Gas_Mscf REAL,
    Water_bbl REAL,
    Liquid_bbl REAL,
    Runtime_hr REAL,
    Available_hr REAL,
    Potential_Oil_bbl REAL
);


CREATE TABLE IF NOT EXISTS stg_Fact_Downtime_Event (
    Downtime_ID TEXT,
    Date TEXT,
    Well_ID TEXT,
    Equipment_ID TEXT,
    Failure_Cause_ID TEXT,
    Downtime_Type TEXT,
    Start_Hour REAL,
    Duration_hr REAL,
    Severity TEXT,
    Failure_Severity TEXT,
    Planned_Flag INTEGER,
    Production_Affected TEXT
);


CREATE TABLE IF NOT EXISTS stg_Fact_Intervention_Event (
    Intervention_ID TEXT,
    Well_ID TEXT,
    Intervention_Type_ID TEXT,
    Start_Date TEXT,
    End_Date TEXT,
    Duration_Days INTEGER,
    Expected_Oil_Rate_bopd REAL,
    Target_Recovery_pct REAL,
    Intervention_Cost_USD REAL,
    Status TEXT
);

CREATE TABLE IF NOT EXISTS stg_Fact_Production_Impact_Daily (
    Date TEXT,
    Well_ID TEXT,
    Potential_Oil_bbl REAL,
    Baseline_Oil_bbl REAL,
    Downtime_Hours REAL,
    Effective_Downtime_Hours REAL,
    Available_hr REAL,
    Downtime_Event_Count INTEGER,
    Downtime_Deferred_Oil_bbl REAL,
    Intervention_Flag INTEGER,
    Intervention_ID TEXT,
    Intervention_Type_ID TEXT,
    Intervention_Days INTEGER,
    Intervention_Recovery_pct REAL,
    Expected_Oil_Rate_bopd REAL,
    Intervention_Cost_USD REAL,
    Intervention_Recovery_Oil_bbl REAL,
    Intervention_Production_Loss_bbl REAL,
    Actual_Oil_bbl REAL,
    Deferred_Oil_bbl REAL,
    Production_Impact_bbl REAL,
    Production_Availability_pct REAL,
    Production_Efficiency_pct REAL,
    Production_Impact_Flag INTEGER
);

-- ============================================================================
-- 3. CORE DIMENSION TABLES
-- ============================================================================


CREATE TABLE IF NOT EXISTS Dim_Date (
    Date TEXT PRIMARY KEY,
    Year INTEGER NOT NULL,
    Quarter INTEGER NOT NULL,
    Month INTEGER NOT NULL,
    Month_Name TEXT NOT NULL,
    Month_Start TEXT NOT NULL,
    Year_Month TEXT NOT NULL,
    Day INTEGER NOT NULL,
    Day_of_Week INTEGER NOT NULL,
    Day_Name TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS Dim_Field (
    Field_ID TEXT PRIMARY KEY,
    Field_Name TEXT NOT NULL,
    Basin TEXT NOT NULL,
    Development_Type TEXT NOT NULL,
    Water_Depth_ft REAL,
    Operator_Type TEXT NOT NULL,
    First_Production_Date TEXT,
    FPSO_Name TEXT
);


CREATE TABLE IF NOT EXISTS Dim_Manifold (
    Manifold_ID TEXT PRIMARY KEY,
    Manifold_Name TEXT NOT NULL,
    Field_ID TEXT NOT NULL,
    Water_Depth_ft REAL,
    Well_Count INTEGER,
    Installation_Date TEXT,
    Status TEXT
);


CREATE TABLE IF NOT EXISTS Dim_Well (
    Well_ID TEXT PRIMARY KEY,
    Well_Name TEXT NOT NULL,
    Well_Type TEXT NOT NULL,
    Field_ID TEXT NOT NULL,
    Manifold_ID TEXT,
    Reservoir TEXT,
    Water_Depth_ft REAL,
    Spud_Date TEXT,
    First_Production_Date TEXT,
    Well_Status TEXT NOT NULL,
    Initial_Oil_Rate_bopd REAL,
    Initial_Gas_Rate_Mscfd REAL,
    Decline_Rate_pct REAL,
    Initial_Water_Cut_pct REAL,
    Artificial_Lift_Type TEXT
);


CREATE TABLE IF NOT EXISTS Dim_Equipment (
    Equipment_ID TEXT PRIMARY KEY,
    Equipment_Name TEXT NOT NULL,
    Equipment_Type TEXT NOT NULL,
    Equipment_Category TEXT NOT NULL,
    Parent_Equipment_ID TEXT,
    Field_ID TEXT NOT NULL,
    Criticality TEXT NOT NULL,
    Installation_Date TEXT,
    Design_Life_Years REAL,
    Status TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS Dim_Failure_Cause (
    Failure_Cause_ID TEXT PRIMARY KEY,
    Failure_Category TEXT NOT NULL,
    Failure_Cause TEXT NOT NULL,
    Severity TEXT NOT NULL,
    Planned_Flag INTEGER NOT NULL
);


CREATE TABLE IF NOT EXISTS Dim_Intervention (
    Intervention_Type_ID TEXT PRIMARY KEY,
    Intervention_Type TEXT NOT NULL,
    Intervention_Category TEXT NOT NULL,
    Typical_Duration_hr REAL,
    Typical_Cost_USD REAL
);


CREATE TABLE IF NOT EXISTS Dim_Scenario (
    Scenario_ID TEXT PRIMARY KEY,
    Scenario_Name TEXT NOT NULL,
    Oil_Price_USD_bbl REAL NOT NULL
);


-- ============================================================================
-- 4. CORE FACT TABLES
-- ============================================================================


CREATE TABLE IF NOT EXISTS Fact_Production_Daily (
    Date TEXT NOT NULL,
    Well_ID TEXT NOT NULL,
    Potential_Oil_bbl REAL NOT NULL,
    Oil_bbl REAL NOT NULL,
    Gas_Mscf REAL NOT NULL,
    Water_bbl REAL NOT NULL,
    Liquid_bbl REAL NOT NULL,
    Runtime_hr REAL NOT NULL,
    Available_hr REAL NOT NULL,

    PRIMARY KEY (Date, Well_ID),

    FOREIGN KEY (Date)
        REFERENCES Dim_Date(Date),

    FOREIGN KEY (Well_ID)
        REFERENCES Dim_Well(Well_ID)
);


CREATE TABLE IF NOT EXISTS Fact_Downtime_Event (
    Downtime_ID TEXT PRIMARY KEY,
    Date TEXT NOT NULL,
    Well_ID TEXT NOT NULL,
    Equipment_ID TEXT NOT NULL,
    Failure_Cause_ID TEXT NOT NULL,
    Downtime_Type TEXT NOT NULL,
    Start_Hour REAL NOT NULL,
    Duration_hr REAL NOT NULL,
    Severity TEXT NOT NULL,
    Failure_Severity TEXT NOT NULL,
    Planned_Flag INTEGER NOT NULL,
    Production_Affected TEXT NOT NULL,

    FOREIGN KEY (Date)
        REFERENCES Dim_Date(Date),

    FOREIGN KEY (Well_ID)
        REFERENCES Dim_Well(Well_ID),

    FOREIGN KEY (Equipment_ID)
        REFERENCES Dim_Equipment(Equipment_ID),

    FOREIGN KEY (Failure_Cause_ID)
        REFERENCES Dim_Failure_Cause(Failure_Cause_ID)
);


CREATE TABLE IF NOT EXISTS Fact_Intervention_Event (
    Intervention_ID TEXT PRIMARY KEY,
    Well_ID TEXT NOT NULL,
    Intervention_Type_ID TEXT NOT NULL,
    Start_Date TEXT NOT NULL,
    End_Date TEXT NOT NULL,
    Duration_Days INTEGER NOT NULL,
    Expected_Oil_Rate_bopd REAL NOT NULL,
    Target_Recovery_pct REAL NOT NULL,
    Intervention_Cost_USD REAL NOT NULL,
    Status TEXT NOT NULL,

    FOREIGN KEY (Well_ID)
        REFERENCES Dim_Well(Well_ID),

    FOREIGN KEY (Intervention_Type_ID)
        REFERENCES Dim_Intervention(Intervention_Type_ID)
);


CREATE TABLE IF NOT EXISTS Fact_Production_Impact_Daily (
    Date TEXT NOT NULL,
    Well_ID TEXT NOT NULL,
    Potential_Oil_bbl REAL NOT NULL,
    Baseline_Oil_bbl REAL NOT NULL,
    Downtime_Hours REAL NOT NULL,
    Effective_Downtime_Hours REAL NOT NULL,
    Available_hr REAL NOT NULL,
    Downtime_Event_Count INTEGER NOT NULL,
    Downtime_Deferred_Oil_bbl REAL NOT NULL,
    Intervention_Flag INTEGER NOT NULL,
    Intervention_ID TEXT,
    Intervention_Type_ID TEXT,
    Intervention_Days INTEGER NOT NULL,
    Intervention_Recovery_pct REAL NOT NULL,
    Expected_Oil_Rate_bopd REAL NOT NULL,
    Intervention_Cost_USD REAL NOT NULL,
    Intervention_Recovery_Oil_bbl REAL NOT NULL,
    Intervention_Production_Loss_bbl REAL NOT NULL,
    Actual_Oil_bbl REAL NOT NULL,
    Deferred_Oil_bbl REAL NOT NULL,
    Production_Impact_bbl REAL NOT NULL,
    Production_Availability_pct REAL NOT NULL,
    Production_Efficiency_pct REAL NOT NULL,
    Production_Impact_Flag INTEGER NOT NULL,

    PRIMARY KEY (Date, Well_ID),

    FOREIGN KEY (Date)
        REFERENCES Dim_Date(Date),

    FOREIGN KEY (Well_ID)
        REFERENCES Dim_Well(Well_ID),

    FOREIGN KEY (Intervention_ID)
        REFERENCES Fact_Intervention_Event(Intervention_ID),

    FOREIGN KEY (Intervention_Type_ID)
        REFERENCES Dim_Intervention(Intervention_Type_ID)
);


-- ============================================================================
-- 5. STAGING LOAD AUDIT
-- ============================================================================


CREATE TABLE IF NOT EXISTS Staging_Load_Audit (
    Load_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Table_Name TEXT NOT NULL,
    Source_File TEXT NOT NULL,
    Source_Row_Count INTEGER NOT NULL,
    Loaded_Row_Count INTEGER NOT NULL,
    Row_Count_Difference INTEGER NOT NULL,
    Load_Status TEXT NOT NULL,
    Load_Timestamp TEXT NOT NULL
);


-- ============================================================================
-- 6. CORE INDEXES
-- ============================================================================


CREATE INDEX IF NOT EXISTS idx_fact_production_well
    ON Fact_Production_Daily (Well_ID);

CREATE INDEX IF NOT EXISTS idx_fact_production_date
    ON Fact_Production_Daily (Date);


CREATE INDEX IF NOT EXISTS idx_fact_downtime_well
    ON Fact_Downtime_Event (Well_ID);

CREATE INDEX IF NOT EXISTS idx_fact_downtime_date
    ON Fact_Downtime_Event (Date);

CREATE INDEX IF NOT EXISTS idx_fact_downtime_equipment
    ON Fact_Downtime_Event (Equipment_ID);

CREATE INDEX IF NOT EXISTS idx_fact_downtime_failure
    ON Fact_Downtime_Event (Failure_Cause_ID);


CREATE INDEX IF NOT EXISTS idx_fact_intervention_well
    ON Fact_Intervention_Event (Well_ID);

CREATE INDEX IF NOT EXISTS idx_fact_intervention_start
    ON Fact_Intervention_Event (Start_Date);


CREATE INDEX IF NOT EXISTS idx_fact_impact_well
    ON Fact_Production_Impact_Daily (Well_ID);

CREATE INDEX IF NOT EXISTS idx_fact_impact_date
    ON Fact_Production_Impact_Daily (Date);


-- ============================================================================
-- 7. DIMENSION INDEXES
-- ============================================================================


CREATE INDEX IF NOT EXISTS idx_dim_well_field
    ON Dim_Well (Field_ID);

CREATE INDEX IF NOT EXISTS idx_dim_well_manifold
    ON Dim_Well (Manifold_ID);

CREATE INDEX IF NOT EXISTS idx_dim_manifold_field
    ON Dim_Manifold (Field_ID);

CREATE INDEX IF NOT EXISTS idx_dim_equipment_field
    ON Dim_Equipment (Field_ID);

CREATE INDEX IF NOT EXISTS idx_dim_equipment_parent
    ON Dim_Equipment (Parent_Equipment_ID);


-- ============================================================================
-- 8. INITIALIZATION STATUS
-- ============================================================================


INSERT OR REPLACE INTO Database_Metadata
    (Metadata_Key, Metadata_Value)
VALUES
    ('Phase_5A_Status', 'INITIALIZED'),
    ('Phase_5B_Status', 'PENDING'),
    ('Phase_5C_Status', 'PENDING');


-- ============================================================================
-- END OF PHASE 5A
-- ============================================================================