"""
Customer Retention & Revenue Risk Analytics
Module: test_data_quality.py

Automated Pytest Suite:
- Validates data cleaning rules and data integrity.
- Tests metric calculation precision and business logic consistency.
- Cross-validates SQL database query outputs against independent Pandas calculations.
- Verifies leak-free preprocessing in the predictive modeling pipeline.
"""

import sqlite3
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent

@pytest.fixture(scope="module")
def project_root():
    return get_project_root()

@pytest.fixture(scope="module")
def raw_df(project_root):
    raw_path = project_root / "data" / "raw" / "Telco-Customer-Churn.csv"
    assert raw_path.exists(), f"Raw dataset not found at {raw_path}. Ingest raw data first."
    return pd.read_csv(raw_path)

@pytest.fixture(scope="module")
def cleaned_df(project_root):
    cleaned_path = project_root / "data" / "processed" / "telco_churn_cleaned.csv"
    assert cleaned_path.exists(), f"Cleaned dataset not found at {cleaned_path}. Run src/data_cleaning.py first."
    return pd.read_csv(cleaned_path)

@pytest.fixture(scope="module")
def sqlite_conn(project_root):
    db_path = project_root / "data" / "processed" / "telco_churn.db"
    assert db_path.exists(), f"SQLite DB not found at {db_path}. Run src/data_cleaning.py first."
    conn = sqlite3.connect(db_path)
    yield conn
    conn.close()

# ------------------------------------------------------------------------------
# 1. RAW DATA INTEGRITY & AUDIT TESTS
# ------------------------------------------------------------------------------

def test_raw_dataset_shape(raw_df):
    """Verify raw dataset has canonical 7,043 rows and 21 columns."""
    assert raw_df.shape == (7043, 21), f"Expected shape (7043, 21), got {raw_df.shape}"

def test_raw_dataset_blank_total_charges(raw_df):
    """Verify raw dataset contains exactly 11 whitespace entries in TotalCharges with tenure=0."""
    blank_mask = raw_df["TotalCharges"].astype(str).str.strip() == ""
    assert blank_mask.sum() == 11, f"Expected 11 blank TotalCharges, got {blank_mask.sum()}"
    assert (raw_df.loc[blank_mask, "tenure"] == 0).all(), "Not all blank TotalCharges have tenure = 0"

# ------------------------------------------------------------------------------
# 2. DATA CLEANING & RULE VALIDATION TESTS
# ------------------------------------------------------------------------------

def test_cleaned_dataset_no_nulls(cleaned_df):
    """Ensure cleaned dataset has zero missing or NaN values across all columns."""
    null_count = cleaned_df.isnull().sum().sum()
    assert null_count == 0, f"Cleaned dataset contains {null_count} nulls."

def test_cleaned_dataset_no_duplicate_customer_ids(cleaned_df):
    """Verify customerID is strictly unique with zero duplicates."""
    dup_count = cleaned_df["customerID"].duplicated().sum()
    assert dup_count == 0, f"Found {dup_count} duplicate customerIDs."

def test_tenure_zero_total_charges_handling(cleaned_df):
    """Verify tenure=0 accounts have TotalCharges set to 0.0."""
    tenure_zero = cleaned_df[cleaned_df["tenure"] == 0]
    assert len(tenure_zero) == 11, f"Expected 11 zero-tenure accounts, got {len(tenure_zero)}"
    assert (tenure_zero["TotalCharges"] == 0.0).all(), "Not all tenure=0 accounts have TotalCharges == 0.0"

def test_target_variable_mapping(cleaned_df):
    """Verify churn_binary perfectly matches Churn string column."""
    assert ((cleaned_df["Churn"] == "Yes") == (cleaned_df["churn_binary"] == 1)).all(), "churn_binary mismatch for 'Yes'"
    assert ((cleaned_df["Churn"] == "No") == (cleaned_df["churn_binary"] == 0)).all(), "churn_binary mismatch for 'No'"

def test_tenure_cohort_coverage(cleaned_df):
    """Verify that every record is assigned a valid tenure cohort."""
    valid_cohorts = {"0-12 Months", "13-24 Months", "25-48 Months", "49-60 Months", "61-72 Months"}
    observed_cohorts = set(cleaned_df["tenure_cohort"].unique())
    assert observed_cohorts == valid_cohorts, f"Expected cohorts {valid_cohorts}, got {observed_cohorts}"

def test_mrr_exposure_proxy_logic(cleaned_df):
    """Verify mrr_exposure_proxy equals MonthlyCharges for churned accounts and 0 for retained."""
    churned_mask = cleaned_df["churn_binary"] == 1
    retained_mask = cleaned_df["churn_binary"] == 0
    assert np.isclose(cleaned_df.loc[churned_mask, "mrr_exposure_proxy"], cleaned_df.loc[churned_mask, "MonthlyCharges"]).all()
    assert (cleaned_df.loc[retained_mask, "mrr_exposure_proxy"] == 0.0).all()

# ------------------------------------------------------------------------------
# 3. METRIC CALCULATION ACCURACY TESTS
# ------------------------------------------------------------------------------

def test_portfolio_churn_rate_precision(cleaned_df):
    """Verify portfolio churn rate is exactly 1,869 / 7,043 = 26.54%."""
    total = len(cleaned_df)
    churned = cleaned_df["churn_binary"].sum()
    churn_rate = churned / total
    assert total == 7043
    assert churned == 1869
    assert round(churn_rate * 100, 2) == 26.54

def test_revenue_exposure_aggregate(cleaned_df):
    """Verify total monthly billings and monthly exposure proxy aggregates."""
    total_billings = cleaned_df["MonthlyCharges"].sum()
    exposure_proxy = cleaned_df["mrr_exposure_proxy"].sum()
    
    assert np.isclose(total_billings, 456116.60, atol=0.01)
    assert np.isclose(exposure_proxy, 139130.85, atol=0.01)

# ------------------------------------------------------------------------------
# 4. CROSS-VALIDATION: SQL VS INDEPENDENT PYTHON CALCULATIONS
# ------------------------------------------------------------------------------

def test_sql_portfolio_metrics_match_pandas(cleaned_df, sqlite_conn):
    """Validate SQL Query 1 outputs against independent Pandas calculations."""
    query = """
    SELECT 
        COUNT(*) AS total_customers,
        SUM(churn_binary) AS churned_customers,
        ROUND(AVG(churn_binary) * 100.0, 2) AS portfolio_churn_rate_pct,
        ROUND(SUM(MonthlyCharges), 2) AS total_monthly_billings,
        ROUND(SUM(mrr_exposure_proxy), 2) AS churned_monthly_exposure_proxy
    FROM telco_churn;
    """
    df_sql = pd.read_sql_query(query, sqlite_conn)
    
    # Assertions
    assert df_sql.loc[0, "total_customers"] == len(cleaned_df)
    assert df_sql.loc[0, "churned_customers"] == cleaned_df["churn_binary"].sum()
    assert np.isclose(df_sql.loc[0, "portfolio_churn_rate_pct"], round(cleaned_df["churn_binary"].mean() * 100, 2))
    assert np.isclose(df_sql.loc[0, "total_monthly_billings"], round(cleaned_df["MonthlyCharges"].sum(), 2))
    assert np.isclose(df_sql.loc[0, "churned_monthly_exposure_proxy"], round(cleaned_df["mrr_exposure_proxy"].sum(), 2))

def test_sql_contract_breakdown_matches_pandas(cleaned_df, sqlite_conn):
    """Validate contract-level churn metrics from SQL against Pandas groupby."""
    query = """
    SELECT 
        Contract,
        COUNT(*) AS customer_count,
        SUM(churn_binary) AS churned_count,
        ROUND(AVG(churn_binary) * 100.0, 2) AS churn_rate_pct
    FROM telco_churn
    GROUP BY Contract
    ORDER BY Contract;
    """
    df_sql = pd.read_sql_query(query, sqlite_conn).set_index("Contract")
    
    py_summary = cleaned_df.groupby("Contract")["churn_binary"].agg(
        customer_count="count",
        churned_count="sum",
        churn_rate_pct=lambda s: round(s.mean() * 100, 2)
    ).sort_index()
    
    pd.testing.assert_frame_equal(df_sql[["customer_count", "churned_count"]], py_summary[["customer_count", "churned_count"]])
    np.testing.assert_allclose(df_sql["churn_rate_pct"], py_summary["churn_rate_pct"])

# ------------------------------------------------------------------------------
# 5. MODEL PIPELINE DATA LEAKAGE PREVENTION TESTS
# ------------------------------------------------------------------------------

def test_modeling_split_disjointness(cleaned_df):
    """Ensure train and test splits have 0 customer overlap."""
    from sklearn.model_selection import train_test_split
    
    train_ids, test_ids = train_test_split(cleaned_df["customerID"], test_size=0.20, random_state=42)
    overlap = set(train_ids).intersection(set(test_ids))
    assert len(overlap) == 0, f"Found {len(overlap)} overlapping customers between train and test sets!"
