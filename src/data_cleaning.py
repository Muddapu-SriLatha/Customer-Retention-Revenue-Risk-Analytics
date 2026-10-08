"""
Customer Retention & Revenue Risk Analytics
Module: data_cleaning.py

Purpose:
- Ingest and validate the IBM Telco Customer Churn dataset.
- Preserve the raw source dataset unchanged in `data/raw/`.
- Handle whitespace values in TotalCharges, type casting, duplicate checks, and missingness checks.
- Engineer analytical cohorts (tenure cohorts, monthly charge tiers, binary flags).
- Export cleaned datasets to `data/processed/` (CSV) and populate local SQLite database `data/processed/telco_churn.db`.
"""

import sys
import os
import logging
import sqlite3
import urllib.request
from pathlib import Path
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("data_cleaning")

CANONICAL_DATASET_URL = (
    "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
)

def get_project_root() -> Path:
    """Return the absolute path of the project root directory."""
    return Path(__file__).resolve().parent.parent

def ensure_directories(project_root: Path) -> dict:
    """Ensure data/raw and data/processed directories exist."""
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    return {"raw": raw_dir, "processed": processed_dir}

def ingest_raw_data(raw_file_path: Path, url: str = CANONICAL_DATASET_URL) -> pd.DataFrame:
    """
    Ingest raw dataset. If local copy does not exist, download from canonical URL.
    Preserves raw data verbatim.
    """
    if not raw_file_path.exists():
        logger.info(f"Raw dataset not found locally. Downloading from {url}...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
        with open(raw_file_path, "wb") as f:
            f.write(content)
        logger.info(f"Raw dataset successfully saved to {raw_file_path} ({len(content):,} bytes).")
    else:
        logger.info(f"Loading existing raw dataset from {raw_file_path}...")

    df_raw = pd.read_csv(raw_file_path)
    logger.info(f"Raw dataset loaded: {df_raw.shape[0]:,} rows, {df_raw.shape[1]} columns.")
    return df_raw

def inspect_raw_data(df: pd.DataFrame) -> dict:
    """Perform data quality checks on raw data and log findings."""
    total_rows = len(df)
    dup_ids = df["customerID"].duplicated().sum()
    null_counts = df.isnull().sum().to_dict()
    blank_total_charges = (df["TotalCharges"].astype(str).str.strip() == "").sum()

    logger.info("--- RAW DATA QUALITY AUDIT ---")
    logger.info(f"Total Rows: {total_rows:,}")
    logger.info(f"Total Columns: {len(df.columns)}")
    logger.info(f"Duplicate customerID count: {dup_ids}")
    logger.info(f"Blank/Whitespace TotalCharges entries: {blank_total_charges}")
    logger.info(f"Standard nulls per column: {sum(null_counts.values())}")
    
    return {
        "total_rows": total_rows,
        "duplicate_ids": dup_ids,
        "blank_total_charges": blank_total_charges,
        "null_counts": null_counts,
    }

def clean_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the raw dataframe according to documented decisions:
    1. Strip whitespace from TotalCharges and cast to float64.
       Tenure=0 customers with blank TotalCharges are assigned 0.0 (new customers with 0 tenure).
    2. Ensure customerID has no leading/trailing whitespace.
    3. Create churn_binary (1 = Yes, 0 = No).
    4. Categorize tenure into analytical cohorts:
       - 0-12 Months
       - 13-24 Months
       - 25-48 Months
       - 49-60 Months
       - 61-72 Months
    5. Categorize MonthlyCharges into charge tiers:
       - Low (< $35)
       - Medium ($35 - $70)
       - High ($70 - $90)
       - Very High (> $90)
    6. Create service and billing summary indicators.
    """
    df = df_raw.copy()

    # 1. Clean customerID
    df["customerID"] = df["customerID"].astype(str).str.strip()

    # 2. Handle TotalCharges blank strings
    # Check tenure for blank TotalCharges
    blank_mask = df["TotalCharges"].astype(str).str.strip() == ""
    logger.info(f"Replacing {blank_mask.sum()} blank TotalCharges with 0.0 (all corresponding to tenure=0).")
    
    # Coerce to float; NaN introduced for blanks will be filled with 0.0
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"].astype(str).str.strip(), errors="coerce")
    df["TotalCharges"] = df["TotalCharges"].fillna(0.0)

    # 3. Clean SeniorCitizen to binary integer
    df["SeniorCitizen"] = df["SeniorCitizen"].astype(int)

    # 4. Target variable: churn_binary
    df["churn_binary"] = (df["Churn"] == "Yes").astype(int)

    # 5. Tenure Cohort
    bins = [-1, 12, 24, 48, 60, 72]
    labels = ["0-12 Months", "13-24 Months", "25-48 Months", "49-60 Months", "61-72 Months"]
    df["tenure_cohort"] = pd.cut(df["tenure"], bins=bins, labels=labels)

    # 6. Monthly Charges Tier
    charge_bins = [0, 35, 70, 90, 200]
    charge_labels = ["Low (<$35)", "Medium ($35-$70)", "High ($70-$90)", "Very High (>$90)"]
    df["charge_tier"] = pd.cut(df["MonthlyCharges"], bins=charge_bins, labels=charge_labels)

    # 7. Additional analytical flags
    df["has_internet"] = (df["InternetService"] != "No").astype(int)
    df["has_tech_support"] = (df["TechSupport"] == "Yes").astype(int)
    df["has_online_security"] = (df["OnlineSecurity"] == "Yes").astype(int)
    df["has_multiple_lines"] = (df["MultipleLines"] == "Yes").astype(int)
    df["is_electronic_check"] = (df["PaymentMethod"] == "Electronic check").astype(int)
    df["is_month_to_month"] = (df["Contract"] == "Month-to-month").astype(int)

    # 8. Monthly Recurring Charge exposure proxy for churned customers
    # Explicitly labeled as a proxy for revenue exposure
    df["mrr_exposure_proxy"] = np.where(df["churn_binary"] == 1, df["MonthlyCharges"], 0.0)

    # Final validation
    assert df.isnull().sum().sum() == 0, "Cleaned dataset contains unexpected null values!"
    assert len(df) == len(df_raw), "Row count changed during cleaning!"
    assert df["customerID"].duplicated().sum() == 0, "Duplicate customerID found after cleaning!"

    logger.info("Data cleaning completed successfully. 0 nulls, 0 duplicates.")
    return df

def save_to_sqlite(df: pd.DataFrame, db_path: Path):
    """Save cleaned dataset into an SQLite database table."""
    logger.info(f"Populating SQLite database at {db_path}...")
    with sqlite3.connect(db_path) as conn:
        # Convert category types to strings for SQLite compatibility
        df_sql = df.copy()
        for col in df_sql.select_dtypes(include="category").columns:
            df_sql[col] = df_sql[col].astype(str)
        
        df_sql.to_sql("telco_churn", conn, if_exists="replace", index=False)
        
        # Verify row count
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM telco_churn;")
        count = cursor.fetchone()[0]
        cursor.execute("SELECT sum(churn_binary), count(*) FROM telco_churn;")
        churned, total = cursor.fetchone()
        churn_rate = (churned / total) * 100
        logger.info(f"SQLite table 'telco_churn' created: {count:,} rows. Churn Rate: {churn_rate:.2f}% ({churned}/{total}).")

def run_pipeline() -> pd.DataFrame:
    """Execute the full data cleaning and validation pipeline."""
    project_root = get_project_root()
    dirs = ensure_directories(project_root)

    raw_path = dirs["raw"] / "Telco-Customer-Churn.csv"
    cleaned_csv_path = dirs["processed"] / "telco_churn_cleaned.csv"
    powerbi_csv_path = dirs["processed"] / "telco_churn_powerbi.csv"
    sqlite_path = dirs["processed"] / "telco_churn.db"

    # Ingest & inspect
    df_raw = ingest_raw_data(raw_path)
    inspect_raw_data(df_raw)

    # Clean
    df_cleaned = clean_data(df_raw)

    # Export CSVs
    df_cleaned.to_csv(cleaned_csv_path, index=False)
    logger.info(f"Cleaned dataset saved to {cleaned_csv_path}")

    df_cleaned.to_csv(powerbi_csv_path, index=False)
    logger.info(f"Power BI enriched dataset saved to {powerbi_csv_path}")

    # Export to SQLite
    save_to_sqlite(df_cleaned, sqlite_path)

    return df_cleaned

if __name__ == "__main__":
    run_pipeline()
