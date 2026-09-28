from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "offshore_production_asset_performance.db"

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

-- ============================================================
-- DIMENSION TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS Dim_Date (
    Date TEXT PRIMARY KEY,
    Year INTEGER NOT NULL,
    Quarter TEXT NOT NULL,
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
    Water_Depth_ft REAL NOT NULL,
    Operator_Type TEXT NOT NULL,
    First_Production_Date TEXT,
    FPSO_Name TEXT
);

CREATE TABLE IF NOT EXISTS Dim_Manifold (
    Manifold_ID TEXT PRIMARY KEY,
    Manifold_Name TEXT NOT NULL,
    Field_ID TEXT NOT NULL,
    Water_Depth_ft REAL NOT NULL,
    Well_Count INTEGER NOT NULL,
    Installation_Date TEXT,
    Status TEXT NOT NULL,
    FOREIGN KEY (Field_ID) REFERENCES Dim_Field(Field_ID)
);

CREATE TABLE IF NOT EXISTS Dim_Well (
    Well_ID TEXT PRIMARY KEY,
    Well_Name TEXT NOT NULL,
    Well_Type TEXT NOT NULL,
    Field_ID TEXT NOT NULL,
    Manifold_ID TEXT,
    Reservoir TEXT NOT NULL,
    Water_Depth_ft REAL NOT NULL,
    Spud_Date TEXT,
    First_Production_Date TEXT,
    Well_Status TEXT NOT NULL,
    Initial_Oil_Rate_bopd REAL NOT NULL,
    Initial_Gas_Rate_Mscfd REAL NOT NULL,
    Decline_Rate_pct REAL NOT NULL,
    Initial_Water_Cut_pct REAL NOT NULL,
    Artificial_Lift_Type TEXT,
    FOREIGN KEY (Field_ID) REFERENCES Dim_Field(Field_ID),
    FOREIGN KEY (Manifold_ID) REFERENCES Dim_Manifold(Manifold_ID)
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
    Design_Life_Years INTEGER NOT NULL,
    Status TEXT NOT NULL,
    FOREIGN KEY (Field_ID) REFERENCES Dim_Field(Field_ID)
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
    Typical_Duration_hr REAL NOT NULL,
    Typical_Cost_USD REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS Dim_Scenario (
    Scenario_ID TEXT PRIMARY KEY,
    Scenario_Name TEXT NOT NULL,
    Oil_Price_USD_bbl REAL NOT NULL
);

-- ============================================================
-- FACT TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS Fact_Production_Daily (
    Date TEXT NOT NULL,
    Well_ID TEXT NOT NULL,
    Oil_bbl REAL NOT NULL,
    Gas_Mscf REAL NOT NULL,
    Water_bbl REAL NOT NULL,
    Liquid_bbl REAL NOT NULL,
    Potential_Oil_bbl REAL NOT NULL,
    Runtime_hr REAL NOT NULL,
    PRIMARY KEY (Date, Well_ID),
    FOREIGN KEY (Date) REFERENCES Dim_Date(Date),
    FOREIGN KEY (Well_ID) REFERENCES Dim_Well(Well_ID)
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
    FOREIGN KEY (Date) REFERENCES Dim_Date(Date),
    FOREIGN KEY (Well_ID) REFERENCES Dim_Well(Well_ID),
    FOREIGN KEY (Equipment_ID) REFERENCES Dim_Equipment(Equipment_ID),
    FOREIGN KEY (Failure_Cause_ID) REFERENCES Dim_Failure_Cause(Failure_Cause_ID)
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
    FOREIGN KEY (Well_ID) REFERENCES Dim_Well(Well_ID),
    FOREIGN KEY (Intervention_Type_ID)
        REFERENCES Dim_Intervention(Intervention_Type_ID)
);

CREATE TABLE IF NOT EXISTS Fact_Production_Impact_Daily (
    Date TEXT NOT NULL,
    Well_ID TEXT NOT NULL,
    Baseline_Oil_bbl REAL NOT NULL,
    Potential_Oil_bbl REAL NOT NULL,
    Actual_Oil_bbl REAL NOT NULL,
    Deferred_Oil_bbl REAL NOT NULL,
    Downtime_Hours REAL NOT NULL,
    Intervention_Impact_Flag INTEGER NOT NULL,
    PRIMARY KEY (Date, Well_ID),
    FOREIGN KEY (Date) REFERENCES Dim_Date(Date),
    FOREIGN KEY (Well_ID) REFERENCES Dim_Well(Well_ID)
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_production_well
    ON Fact_Production_Daily(Well_ID);

CREATE INDEX IF NOT EXISTS idx_production_date
    ON Fact_Production_Daily(Date);

CREATE INDEX IF NOT EXISTS idx_downtime_well_date
    ON Fact_Downtime_Event(Well_ID, Date);

CREATE INDEX IF NOT EXISTS idx_downtime_equipment
    ON Fact_Downtime_Event(Equipment_ID);

CREATE INDEX IF NOT EXISTS idx_intervention_well
    ON Fact_Intervention_Event(Well_ID);

CREATE INDEX IF NOT EXISTS idx_intervention_dates
    ON Fact_Intervention_Event(Start_Date, End_Date);

CREATE INDEX IF NOT EXISTS idx_impact_well_date
    ON Fact_Production_Impact_Daily(Well_ID, Date);

CREATE INDEX IF NOT EXISTS idx_impact_date
    ON Fact_Production_Impact_Daily(Date);
"""


def initialize_database() -> None:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")
        connection.executescript(SCHEMA_SQL)

    print("=" * 72)
    print("PHASE 5A — SQLITE DATABASE INITIALIZATION")
    print("=" * 72)
    print()
    print(f"Database: {DATABASE_PATH}")
    print()
    print("Schema initialized successfully.")
    print("Foreign-key enforcement: ON")
    print()


if __name__ == "__main__":
    initialize_database()