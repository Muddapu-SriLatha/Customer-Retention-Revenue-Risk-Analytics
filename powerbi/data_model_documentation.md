# Power BI Data Model Architecture & Schema Specification

## 1. Data Model Overview
The Power BI solution is structured around an enriched dimensional model designed for fast analytical slicing, clear DAX evaluation contexts, and zero ambiguous relationships.

### Architecture Options
1. **Flat Model (Fastest Setup)**:
   - Ingest `telco_churn_powerbi.csv` directly as a single denormalized analytical table `telco_churn`.
   - Host all measures in a dedicated, isolated measure table `_Measures`.
2. **Star Schema (Enterprise Best Practice)**:
   - Central Fact Table: `FactCustomerBilling` (granularity: 1 row per customerID).
   - Conformed Dimensions:
     - `DimContract` (`Contract`, `ContractCategory`, `DefaultTermMonths`)
     - `DimPaymentMethod` (`PaymentMethod`, `PaymentType` [Automatic vs Manual])
     - `DimTenureCohort` (`tenure_cohort`, `SortOrder`, `MinTenure`, `MaxTenure`)
     - `DimChargeTier` (`charge_tier`, `SortOrder`, `MinCharge`, `MaxCharge`)

---

## 2. Field Specifications & Formatting

| Column Name | Power BI Data Type | Format String | Summarization | Notes / Sort By Column |
|---|---|---|---|---|
| `customerID` | Text | None | Do Not Summarize | Primary Key |
| `gender` | Text | None | Do Not Summarize | Demographic attribute |
| `SeniorCitizen` | Whole Number | `0` | Do Not Summarize | Categorical flag (0/1) |
| `Partner` | Text | None | Do Not Summarize | "Yes" / "No" |
| `Dependents` | Text | None | Do Not Summarize | "Yes" / "No" |
| `tenure` | Whole Number | `#,##0` | Average / Do Not Summarize | Months as customer |
| `PhoneService` | Text | None | Do Not Summarize | "Yes" / "No" |
| `MultipleLines` | Text | None | Do Not Summarize | "Yes", "No", "No phone service" |
| `InternetService` | Text | None | Do Not Summarize | "DSL", "Fiber optic", "No" |
| `OnlineSecurity` | Text | None | Do Not Summarize | Add-on service status |
| `OnlineBackup` | Text | None | Do Not Summarize | Add-on service status |
| `DeviceProtection` | Text | None | Do Not Summarize | Add-on service status |
| `TechSupport` | Text | None | Do Not Summarize | Add-on service status |
| `StreamingTV` | Text | None | Do Not Summarize | Add-on service status |
| `StreamingMovies` | Text | None | Do Not Summarize | Add-on service status |
| `Contract` | Text | None | Do Not Summarize | "Month-to-month", "One year", "Two year" |
| `PaperlessBilling` | Text | None | Do Not Summarize | "Yes" / "No" |
| `PaymentMethod` | Text | None | Do Not Summarize | Billing gateway channel |
| `MonthlyCharges` | Decimal Number | `$#,##0.00` | Average / Sum | Monthly invoice amount |
| `TotalCharges` | Decimal Number | `$#,##0.00` | Sum | Cumulative lifetime billing |
| `Churn` | Text | None | Do Not Summarize | Target variable ("Yes" / "No") |
| `churn_binary` | Whole Number | `0` | Do Not Summarize | Mathematical target (1 = Churn, 0 = Retained) |
| `tenure_cohort` | Text | None | Do Not Summarize | **Must sort by Tenure Sort Order** |
| `charge_tier` | Text | None | Do Not Summarize | **Must sort by Charge Tier Order** |
| `mrr_exposure_proxy`| Decimal Number | `$#,##0.00` | Sum | Revenue exposure proxy |

---

## 3. Sort Order Configuration (Critical for Proper Ordering)

To prevent Power BI from sorting cohorts alphabetically (e.g., sorting "0-12 Months" next to "49-60 Months" instead of chronological sequence):
1. Create a calculated column or conditional column in Power Query:
```dax
Tenure Sort Order = 
SWITCH(
    'telco_churn'[tenure_cohort],
    "0-12 Months", 1,
    "13-24 Months", 2,
    "25-48 Months", 3,
    "49-60 Months", 4,
    "61-72 Months", 5,
    6
)
```
2. In Power BI Data View, select `tenure_cohort`, navigate to **Column Tools** $\rightarrow$ **Sort by Column**, and choose `Tenure Sort Order`.

3. Repeat for `charge_tier`:
```dax
Charge Tier Sort Order = 
SWITCH(
    'telco_churn'[charge_tier],
    "Low (<$35)", 1,
    "Medium ($35-$70)", 2,
    "High ($70-$90)", 3,
    "Very High (>$90)", 4,
    5
)
```
Select `charge_tier` $\rightarrow$ **Sort by Column** $\rightarrow$ `Charge Tier Sort Order`.
