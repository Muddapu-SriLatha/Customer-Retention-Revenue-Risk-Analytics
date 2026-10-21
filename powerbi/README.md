# Power BI Dashboard Implementation Guide: Customer Retention & Revenue Risk

This guide provides end-to-end instructions for assembling the portfolio-grade interactive Power BI dashboard using the pre-processed dataset (`data/processed/telco_churn_powerbi.csv`) and validated DAX measures (`powerbi/dax_measures.dax`).

---

## 1. Prerequisites & Source Ingestion

1. **Launch Power BI Desktop** (free download from Microsoft Store or official website).
2. Click **Get Data** $\rightarrow$ **Text/CSV**.
3. Navigate to your local project directory and select:
   `data/processed/telco_churn_powerbi.csv`
4. Click **Transform Data** to open the Power Query Editor.
   - Verify all 21 columns loaded with correct headers.
   - Confirm `tenure` is Whole Number, `MonthlyCharges` and `TotalCharges` are Decimal Number.
   - Confirm `churn_binary` is Whole Number.
5. Click **Close & Apply**.

---

## 2. Setting Up the Dedicated Measure Table

To maintain a clean, enterprise-ready data model:
1. In the **Home** ribbon, click **Enter Data**.
2. Name the table `_Measures` and click **Load**.
3. In the Data pane, right-click `_Measures` $\rightarrow$ **New Measure**.
4. Copy and paste each DAX formula from [`powerbi/dax_measures.dax`](./dax_measures.dax).
5. Delete the blank `Column1` from `_Measures`. The `_Measures` table will automatically move to the top with a calculator icon.

---

## 3. Page Layouts & Visual Configurations

### Page 1: Executive Overview
*Objective: Deliver high-impact C-suite KPIs, high-level churn prevalence, and top-level contractual drivers.*

1. **Header Banner**:
   - Title: `Executive Retention & Revenue Risk Dashboard`
   - Subtitle: `Portfolio Health, Churn Exposure & Account Attrition Insights`
2. **Top KPI Scorecard (5 Multi-Row / Card Visuals)**:
   - **Card 1**: `[Total Customers]` (Display: `7,043`, Format: `#,##0`)
   - **Card 2**: `[Churned Customers]` (Display: `1,869`, Format: `#,##0`, Color: `#DC2626`)
   - **Card 3**: `[Churn Rate]` (Display: `26.54%`, Format: `0.00%`, Data Callout: High risk indicator)
   - **Card 4**: `[Average Monthly Charges]` (Display: `$64.76`, Format: `$#,##0.00`)
   - **Card 5**: `[Monthly Revenue Exposure Proxy]` (Display: `$139.13K`, Format: `$#,##0.00`, Accent: Red)
3. **Left Visual - Customer Base Composition**:
   - *Type*: Donut Chart
   - *Legend*: `Churn`
   - *Values*: `[Total Customers]`
   - *Colors*: Retained = Deep Blue (`#1E3A8A`), Churned = Crimson (`#DC2626`)
4. **Center Visual - Churn Volume & Rate by Contract**:
   - *Type*: Clustered Column Chart
   - *X-Axis*: `Contract` (Month-to-month, One year, Two year)
   - *Y-Axis (Columns)*: `[Retained Customers]`, `[Churned Customers]`
   - *Line Y-Axis*: `[Churn Rate]`
5. **Right Visual - Financial Exposure by Contract**:
   - *Type*: 100% Stacked Bar Chart
   - *Y-Axis*: `Contract`
   - *X-Axis*: `[Monthly Revenue Exposure Proxy]`
6. **Top Slicers**:
   - `InternetService` (Dropdown: All, DSL, Fiber optic, No)
   - `PaymentMethod` (Dropdown: All, Electronic check, Mailed check, Bank transfer, Credit card)

---

### Page 2: Customer Segmentation & Lifecycle Hazards
*Objective: Analyze behavioural and operational segments to pinpoint vulnerability cohorts.*

1. **Top Visual - Churn Hazard by Tenure Cohort**:
   - *Type*: Clustered Column Chart
   - *X-Axis*: `tenure_cohort` (Sorted chronologically by `Tenure Sort Order`)
   - *Y-Axis*: `[Total Customers]`
   - *Tooltips / Data Labels*: `[Churn Rate]`, `[Churned Customers]`
   - *Key Takeaway*: Highlights the 47.4% churn rate during the first 12 months.
2. **Bottom-Left Visual - Payment Gateway Propensity**:
   - *Type*: Horizontal Bar Chart
   - *Y-Axis*: `PaymentMethod`
   - *X-Axis*: `[Churn Rate]` (Sorted descending)
   - *Conditional Formatting*: Color bars red if Churn Rate > 30%, green if < 20%.
3. **Bottom-Right Visual - Service Ecosystem Matrix**:
   - *Type*: Matrix Table
   - *Rows*: `InternetService`, `TechSupport`, `OnlineSecurity`
   - *Values*: `[Total Customers]`, `[Churned Customers]`, `[Churn Rate]`, `[Monthly Revenue Exposure Proxy]`
   - *Formatting*: Heatmap background color scale on `[Churn Rate]`.
4. **Interactive Slicers**:
   - `charge_tier` (Tiles: Low, Medium, High, Very High)
   - `Contract` (Single select pills)
   - `SeniorCitizen` (Checkbox toggle)

---

### Page 3: Revenue Risk & Retention Strategy Simulator
*Objective: Quantify financial exposure at the segment level and evaluate campaign ROI scenarios.*

1. **Top KPI Strip**:
   - **Card 1**: `[Annualized Revenue Exposure Proxy]` (Display: `$1.67M`)
   - **Card 2**: `[Pct Monthly Billings Exposed]` (Display: `30.50%`)
   - **Card 3**: `[Monthly Billing Premium - Churned vs Retained]` (Display: `+$13.17/mo`)
2. **Main Visual - High-Exposure Segment Ranking (Window Function Proxy)**:
   - *Type*: Clustered Bar Chart
   - *Y-Axis*: Segment Combined (`Contract` + `InternetService` + `PaymentMethod`)
   - *X-Axis*: `[Monthly Revenue Exposure Proxy]`
   - *Highlights*: Top segment (Month-to-month + Fiber optic + Electronic check) accounts for over $32K/month in lost billing exposure.
3. **Interactive What-If Scenario Simulator**:
   - *Visual*: Sliders for `Target Churn Reduction %` (e.g., 5% to 30%) and `Campaign Outreach Cost ($)`.
   - *Calculated Output Cards*:
     - `[Simulated Saved Customers]`
     - `[Simulated Monthly Recovered Revenue]`
     - `[Simulated Annual Recovered Revenue]`
     - `[Net Retention Campaign ROI %]`

---

## 4. Color Palette & Accessibility Guidelines

| Role | Color Name | Hex Code | Purpose |
|---|---|---|---|
| Primary Retained | Corporate Navy Blue | `#1E3A8A` | Retained customer volume, baseline bars |
| Primary Risk | Crimson Red | `#DC2626` | Churn indicators, risk metrics, exposure |
| Positive Action | Emerald Green | `#10B981` | Safe segments, automated pay, recovered revenue |
| Warning / Neutral | Amber / Slate | `#F59E0B` / `#6B7280` | Moderate risk, subtext, axis grids |
| Card Background | Soft Off-White | `#F9FAFB` | Card borders and card backplates |

---

## 5. Dashboard Refresh & Maintenance Protocol

1. When a new batch of raw customer data is acquired:
   ```bash
   python src/data_cleaning.py
   ```
2. In Power BI Desktop, navigate to the **Home** ribbon and click **Refresh**.
3. All DAX measures, visualizations, and segment tables will automatically recompute against the updated data.
