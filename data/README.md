# Data Documentation & Provenance

## 1. Dataset Origin & Provenance
- **Dataset Name**: IBM Telco Customer Churn Dataset (`Telco-Customer-Churn.csv`)
- **Origin / Source**: Originally released by IBM as a business sample dataset for IBM Cognos Analytics and IBM Cloud Pak for Data.
- **Canonical Repository**: [IBM/telco-customer-churn-on-icp4d](https://github.com/IBM/telco-customer-churn-on-icp4d)
- **Direct Download URL**: `https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv`
- **License / Terms**: Apache License 2.0 / Public Sample Dataset. Authorized for research, educational, and portfolio analytics demonstration.
- **Scope**: Cross-sectional sample of 7,043 telecommunications customers in California providing home phone and Internet services.

## 2. Raw vs. Processed Data
- `data/raw/Telco-Customer-Churn.csv`: Raw, unmodified dataset as ingested directly from the IBM repository.
- `data/processed/telco_churn_cleaned.csv`: Cleaned dataset following standard enterprise data quality protocols.
- `data/processed/telco_churn_powerbi.csv`: Enriched dataset with calculated segmentation attributes (tenure cohorts, charge tiers, revenue risk flags) prepared for Power BI reporting.
- `data/processed/telco_churn.db`: Self-contained SQLite database populated with the schema and cleaned data for reproducible SQL queries.

## 3. Data Dictionary

| Column Name | Data Type (Raw) | Data Type (Cleaned) | Description | Example Values |
|---|---|---|---|---|
| `customerID` | string (object) | string | Unique alphanumeric identifier for each customer | `7590-VHVEG`, `5575-GNVDE` |
| `gender` | string (object) | string | Customer gender | `Female`, `Male` |
| `SeniorCitizen` | integer (int64) | integer (0/1) | Whether the customer is a senior citizen (1) or not (0) | `0`, `1` |
| `Partner` | string (object) | string | Whether the customer has a partner | `Yes`, `No` |
| `Dependents` | string (object) | string | Whether the customer has dependents | `Yes`, `No` |
| `tenure` | integer (int64) | integer | Number of months the customer has stayed with the company | `1`, `34`, `72` |
| `PhoneService` | string (object) | string | Whether the customer has a phone service | `Yes`, `No` |
| `MultipleLines` | string (object) | string | Whether customer has multiple phone lines | `No phone service`, `No`, `Yes` |
| `InternetService` | string (object) | string | Customer's internet service provider type | `DSL`, `Fiber optic`, `No` |
| `OnlineSecurity` | string (object) | string | Whether the customer has online security add-on | `Yes`, `No`, `No internet service` |
| `OnlineBackup` | string (object) | string | Whether the customer has online backup add-on | `Yes`, `No`, `No internet service` |
| `DeviceProtection` | string (object) | string | Whether the customer has tech device protection add-on | `Yes`, `No`, `No internet service` |
| `TechSupport` | string (object) | string | Whether the customer has premium technical support add-on | `Yes`, `No`, `No internet service` |
| `StreamingTV` | string (object) | string | Whether the customer uses internet streaming TV | `Yes`, `No`, `No internet service` |
| `StreamingMovies` | string (object) | string | Whether the customer uses internet streaming movies | `Yes`, `No`, `No internet service` |
| `Contract` | string (object) | string | Customer contract commitment term | `Month-to-month`, `One year`, `Two year` |
| `PaperlessBilling` | string (object) | string | Whether customer is enrolled in paperless billing | `Yes`, `No` |
| `PaymentMethod` | string (object) | string | Payment method used for monthly invoices | `Electronic check`, `Mailed check`, `Bank transfer (automatic)`, `Credit card (automatic)` |
| `MonthlyCharges` | float (float64) | float64 | The amount charged to the customer monthly (USD) | `29.85`, `56.95`, `108.15` |
| `TotalCharges` | string (object) | float64 | The total amount charged over customer lifetime (USD) | `29.85`, `1889.50` |
| `Churn` | string (object) | string / int (0/1) | Target variable: Whether customer churned within last month | `No`, `Yes` |

## 4. Key Data Quality Findings & Cleaning Decisions

1. **Whitespace in `TotalCharges` (11 records)**:
   - *Observation*: 11 rows in `TotalCharges` contained blank whitespace (`" "`) instead of numeric values, causing the column to be parsed as an `object` string type.
   - *Diagnosis*: Cross-tabulation showed all 11 records have `tenure == 0` and `Churn == 'No'`. These are newly onboarded customers who have not yet reached their first billing cycle.
   - *Cleaning Action*: Converted `TotalCharges` to `float64`, replacing the whitespace with `0.0`. This preserves all 7,043 customer records without introducing synthetic bias or discarding valid recent customer acquisitions.
2. **Missing Values**:
   - Zero missing (`NaN` / `null`) values across all other 20 columns.
3. **Duplicates**:
   - Zero duplicate records on `customerID`. Every record uniquely represents a distinct customer account.
4. **Class Distribution**:
   - Retained (`No`): 5,174 (73.46%)
   - Churned (`Yes`): 1,869 (26.54%)
   - Baseline Churn Rate: 26.54% (moderate class imbalance).
5. **Feature Engineering for Analytics**:
   - `tenure_group`: Grouped into 5 analytical cohorts: `0-12 Months`, `13-24 Months`, `25-48 Months`, `49-60 Months`, `61-72 Months`.
   - `MonthlyCharges_tier`: Categorized into `Low (<$35)`, `Medium ($35-$70)`, `High ($70-$90)`, `Very High (>$90)`.
   - `churn_binary`: Numeric indicator (1 for Churned, 0 for Retained) for mathematical aggregation and machine learning.
   - `has_internet`: Binary flag (1 if `InternetService != 'No'`, else 0).
   - `online_security_flag`, `tech_support_flag`: Cleaned binary indicators separating active subscribers from non-subscribers.
