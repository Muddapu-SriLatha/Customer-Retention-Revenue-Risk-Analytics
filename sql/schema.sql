-- ==============================================================================
-- Customer Retention & Revenue Risk Analytics
-- Script: schema.sql
-- Database Engine: SQLite / PostgreSQL ANSI Compatible
-- Description: Table schema definition and indexing for Telco Customer Churn.
-- ==============================================================================

DROP TABLE IF EXISTS telco_churn;

CREATE TABLE telco_churn (
    customerID VARCHAR(20) PRIMARY KEY,
    gender VARCHAR(10) NOT NULL,
    SeniorCitizen INTEGER NOT NULL CHECK (SeniorCitizen IN (0, 1)),
    Partner VARCHAR(5) NOT NULL CHECK (Partner IN ('Yes', 'No')),
    Dependents VARCHAR(5) NOT NULL CHECK (Dependents IN ('Yes', 'No')),
    tenure INTEGER NOT NULL CHECK (tenure >= 0),
    PhoneService VARCHAR(5) NOT NULL CHECK (PhoneService IN ('Yes', 'No')),
    MultipleLines VARCHAR(25) NOT NULL,
    InternetService VARCHAR(25) NOT NULL,
    OnlineSecurity VARCHAR(25) NOT NULL,
    OnlineBackup VARCHAR(25) NOT NULL,
    DeviceProtection VARCHAR(25) NOT NULL,
    TechSupport VARCHAR(25) NOT NULL,
    StreamingTV VARCHAR(25) NOT NULL,
    StreamingMovies VARCHAR(25) NOT NULL,
    Contract VARCHAR(25) NOT NULL,
    PaperlessBilling VARCHAR(5) NOT NULL CHECK (PaperlessBilling IN ('Yes', 'No')),
    PaymentMethod VARCHAR(40) NOT NULL,
    MonthlyCharges NUMERIC(8, 2) NOT NULL CHECK (MonthlyCharges >= 0),
    TotalCharges NUMERIC(10, 2) NOT NULL CHECK (TotalCharges >= 0),
    Churn VARCHAR(5) NOT NULL CHECK (Churn IN ('Yes', 'No')),
    
    -- Feature engineered attributes
    churn_binary INTEGER NOT NULL CHECK (churn_binary IN (0, 1)),
    tenure_cohort VARCHAR(20) NOT NULL,
    charge_tier VARCHAR(25) NOT NULL,
    has_internet INTEGER NOT NULL CHECK (has_internet IN (0, 1)),
    has_tech_support INTEGER NOT NULL CHECK (has_tech_support IN (0, 1)),
    has_online_security INTEGER NOT NULL CHECK (has_online_security IN (0, 1)),
    has_multiple_lines INTEGER NOT NULL CHECK (has_multiple_lines IN (0, 1)),
    is_electronic_check INTEGER NOT NULL CHECK (is_electronic_check IN (0, 1)),
    is_month_to_month INTEGER NOT NULL CHECK (is_month_to_month IN (0, 1)),
    mrr_exposure_proxy NUMERIC(8, 2) NOT NULL DEFAULT 0.0
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_telco_churn_contract ON telco_churn(Contract);
CREATE INDEX IF NOT EXISTS idx_telco_churn_tenure ON telco_churn(tenure);
CREATE INDEX IF NOT EXISTS idx_telco_churn_payment ON telco_churn(PaymentMethod);
CREATE INDEX IF NOT EXISTS idx_telco_churn_status ON telco_churn(churn_binary);
CREATE INDEX IF NOT EXISTS idx_telco_churn_internet ON telco_churn(InternetService);
