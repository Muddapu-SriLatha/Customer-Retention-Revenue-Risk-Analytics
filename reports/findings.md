# Customer Retention & Revenue Risk Analytics: Strategic Business Report

## Executive Summary

This empirical analysis investigates customer attrition patterns, segment vulnerabilities, and monthly revenue exposure across **7,043 customer accounts** from the canonical IBM Telco dataset.

### Key Portfolio Metrics

| Portfolio Metric | Empirical Value | Business Context |
|---|---|---|
| **Total Customer Base** | 7,043 | Active and recently churned accounts in audit |
| **Retained Accounts** | 5,174 (73.46%) | Stable account baseline |
| **Churned Accounts** | 1,869 (26.54%) | Accounts lost in the prior reporting cycle |
| **Total Monthly Billings** | $456,116.60 | Aggregate portfolio monthly recurring billing volume |
| **Monthly Revenue Exposure Proxy** | **$139,130.85** | **30.50% of monthly billings lost to churn** |
| **Annualized Run-Rate Exposure** | **$1,669,570.20** | Annualized proxy ($139,130.85 × 12 months) |
| **Total Historical Realized Revenue** | $16,056,168.70 | Cumulative customer lifetime spend across all accounts |

> [!IMPORTANT]
> **Revenue Exposure Definition & Caveat**:
> Monthly charges are utilized as an operational proxy for **Monthly Recurring Revenue (MRR) Exposure**. This metric represents the top-line billing volume associated with severed accounts. It is *not* identical to net lost cash flow, as it excludes customer acquisition costs (CAC), gross margin margins, contractual termination penalties, promotional credits, and future expansion value.

---

## 1. Core Analytical Findings

### Finding 1: The Contract Commitment Chasm
- **Month-to-Month Contracts**: Represent 55.02% of the customer base (3,875 accounts) but generate **86.86% of all churn revenue exposure** ($120,847.10 / $139,130.85).
  - Churn Rate: **42.71%** (1,655 churned accounts).
- **One-Year Contracts**: Churn rate plummets to **11.27%** (166 churned accounts, $14,118.45 monthly exposure).
- **Two-Year Contracts**: Churn rate falls to **2.83%** (48 churned accounts, $4,165.30 monthly exposure).
- **Statistical Significance**: Chi-Square = 1,184.60 (p = 5.86e-258, Cramér's V = 0.4098, Substantial effect size). Customers on month-to-month terms have **15.1x higher churn propensity** than two-year contract holders.

### Finding 2: The "First-Year Hazard Zone" (Onboarding Vulnerability)
- Customers with **0–12 months of tenure** experience a staggering **47.44% churn rate** (1,037 churned out of 2,186 accounts).
- For customers with **Month-to-Month contracts in their first 12 months**, the churn rate surges to **51.35%** (1,024 churned out of 1,994 accounts), accounting for **$68,301.45 in monthly exposure** (49.09% of all portfolio churn exposure).
- Retention stabilizes dramatically with account maturity:
  - 13–24 Months: 28.71% churn rate
  - 25–48 Months: 20.39% churn rate
  - 49–60 Months: 14.42% churn rate
  - 61–72 Months: 6.61% churn rate
- **Statistical Significance**: Welch's t = -34.82 (p = 1.20e-232, Cohen's d = -0.8522, Large effect size). Median tenure of retained customers is 38 months vs. 10 months for churned customers.

### Finding 3: Billing Burden & The High-Charge Paradox
- Churned customers pay significantly higher average monthly charges: **$74.44/month vs. $61.27/month** for retained customers (+$13.17/month difference, Welch's t = 18.41, p = 8.59e-73, Cohen's d = +0.4463).
- While high-billing customers generate greater top-line value per account, they exhibit significantly greater attrition sensitivity:
  - Very High Tier (>$90/mo): **34.20% churn rate**
  - High Tier ($70–$90/mo): **37.33% churn rate**
  - Medium Tier ($35–$70/mo): **24.50% churn rate**
  - Low Tier (<$35/mo): **10.87% churn rate**

### Finding 4: The Payment Gateway Friction Multiplier
- **Electronic Check**: 2,365 accounts (33.58% of portfolio) exhibit a **45.29% churn rate** (1,071 churned), exposing **$79,856.90 in monthly revenue** (57.40% of total churn exposure).
- In sharp contrast, automated payment mechanisms exhibit dramatically lower attrition:
  - Bank Transfer (Automatic): **16.71% churn rate**
  - Credit Card (Automatic): **15.24% churn rate**
  - Mailed Check: **19.11% churn rate**
- **Statistical Significance**: Chi-Square = 648.14 (p = 3.68e-140, Cramér's V = 0.3027, Substantial effect size).

### Finding 5: Product Complexity & Support Deficit
- **Fiber Optic Attrition**: Fiber optic subscribers suffer a **41.89% churn rate** (1,297 / 3,096 accounts, exposing $113,874.35/mo) compared to **18.96%** for DSL subscribers.
- **Tech Support as a Retention Anchor**: Customers without Tech Support have a **41.64% churn rate** (1,446 / 3,473 accounts), whereas customers subscribing to Tech Support churn at only **15.17%** (310 / 2,044 accounts).
- **The "High-Risk Toxic Quad"**:
  Customers with *Month-to-Month Contract + High Monthly Charges ($70–$90) + Electronic Check + No Tech Support* exhibit a **62.58% churn rate** (408 churned out of 652 accounts), representing a **Churn Risk Index of 235.8** (135.8% above portfolio baseline) and exposing **$32,622.20/month**.

---

## 2. Predictive Modeling & Machine Learning Synthesis

### Model Performance Audit (Holdout Test Set, N = 1,409)

| Model Architecture | Accuracy | Precision | Recall | F1-Score | ROC-AUC | PR-AUC | Primary Strength / Limitation |
|---|---|---|---|---|---|---|---|
| **Baseline (Most Frequent)** | 73.46% | 0.00% | 0.00% | 0.0000 | 0.5000 | 0.2654 | Fails completely on churners; highlights accuracy paradox |
| **Logistic Regression (Balanced)** | 73.81% | 50.43% | **78.34%** | 0.6136 | 0.8417 | 0.6331 | Highly interpretable coefficients & odds ratios; strong recall |
| **Random Forest (Balanced)** | **74.66%** | **51.46%** | **80.21%** | **0.6270** | **0.8429** | **0.6506** | Captures non-linear service interactions; best overall AUC |

### Why Accuracy is an Inadequate Metric
In this dataset, retained customers comprise 73.46% of the population. A naive model that classifies every customer as "Retained" achieves a deceptively high **73.46% accuracy** while capturing **0% of churners** and leaving **100% of revenue risk undetected**. Evaluation must center on **Recall** (risk coverage), **Precision** (campaign targeting efficiency), and **ROC-AUC / PR-AUC** (discrimination ability).

### Decision Threshold Optimization
Assuming standard commercial retention campaign economics:
- Campaign contact cost per account: $C_{contact} = \$25.00$
- Retained customer asset value: $V_{save} = \$400.00$
- Retention campaign rescue rate: $P_{success} = 25\%$
- Expected Net Benefit per True Positive: $(0.25 \times \$400) - \$25 = +\$75.00$
- Net Cost per False Positive: $-\$25.00$

| Threshold Strategy | Threshold Cutoff | Precision | Recall | Net Expected Campaign Value |
|---|---|---|---|---|
| **Default Model Threshold** | 0.50 | 50.43% | 78.34% | $14,775.00 |
| **Max F1 Threshold** | 0.57 | 54.15% | 73.26% | $14,750.00 |
| **Profit-Maximizing Threshold** | **0.44** | 48.02% | **84.22%** | **$15,100.00** |

By lowering the classification threshold to **0.44**, the business captures **84.22% of churners**, generating an incremental **+$325.00 in net value per 1,409 customer sample** ($15,100 vs $14,775) by trading minor precision for significantly expanded retention reach.

---

## 3. Financial Modeling & Break-Even Retention Analysis

### Target Campaign Segment: Early-Tenure Month-to-Month Cohort
- Target Population: Month-to-month customers in their first 12 months ($N = 1,994$).
- Current Churn Volume: 1,024 churned accounts (51.35% churn rate).
- Monthly Revenue Exposure: **$68,301.45/month** ($819,617.40 annualized).

### Proposed Retention Intervention: "Onboarding VIP Concierge"
- **Intervention Package**:
  1. Dedicated onboarding onboarding call and fiber connection health check within first 14 days.
  2. Free 6-month Tech Support and Online Security bundle.
  3. $10/month bill credit incentive upon switching from Electronic Check to Auto-Pay (Bank or Credit Card) for 12 months.
- **Estimated Intervention Cost**: $30.00 per targeted customer ($59,820 total campaign cost for 1,994 customers).

### Break-Even Calculations
1. **Average Annual Value per Saved Account**:
   $$\text{Avg Annual Value} = \$70.00/\text{mo} \times 12 = \$840.00/\text{year}$$
2. **Break-Even Customers Required**:
   $$\text{Required Saved Accounts} = \frac{\text{Total Campaign Cost}}{\text{Annual Value}} = \frac{\$59,820}{\$840} = 71.21 \approx 72 \text{ accounts}$$
3. **Break-Even Churn Reduction**:
   - Baseline Churned Accounts: 1,024
   - Required Reduction in Churn: $72 / 1,024 = \mathbf{7.03\%}$ relative reduction.
   - Absolute Churn Rate Target: Reducing churn rate from **51.35% to 47.74%** (a reduction of only 3.61 percentage points).
4. **ROI Scenarios**:
   - *Conservative Case (10% relative churn reduction)*: 102 accounts saved $\rightarrow$ \$85,680 saved revenue $\rightarrow$ **+$25,860 net gain (43.2% ROI)**.
   - *Target Case (20% relative churn reduction)*: 205 accounts saved $\rightarrow$ \$172,200 saved revenue $\rightarrow$ **+$112,380 net gain (187.9% ROI)**.
   - *Optimistic Case (30% relative churn reduction)*: 307 accounts saved $\rightarrow$ \$257,880 saved revenue $\rightarrow$ **+$198,060 net gain (331.1% ROI)**.

---

## 4. Strategic Business Recommendations

### Recommendation 1: Redesign Onboarding & First-Year Engagement
- **Problem**: 51.35% of month-to-month customers churn within 12 months.
- **Action**: Implement milestone check-ins at Day 7, Day 30, and Day 90. Automatically route early-tenure support tickets to senior technical specialists.
- **Measurable Goal**: Reduce first-year month-to-month churn from 51.35% to under 45% within 6 months.

### Recommendation 2: Contract Migration & Auto-Pay Incentivization
- **Problem**: Month-to-month accounts drive 86.86% of revenue exposure, and Electronic Check users churn at 45.29%.
- **Action**: Offer an automated bill credit ($5–$10/mo for 12 months) for customers transitioning from month-to-month and electronic check to an annual contract with auto-debit billing.
- **Measurable Goal**: Shift 25% of month-to-month accounts to 1-year commitments and convert 30% of electronic check users to automated payment.

### Recommendation 3: Bundle Technical Support with High-Speed Fiber Optic
- **Problem**: Fiber optic customers experience an unacceptable 41.89% churn rate, but subscribing to Tech Support reduces churn by nearly two-thirds (from 41.64% to 15.17%).
- **Action**: Repackage premium fiber tiers to include complimentary Tech Support and Device Protection for the initial 6 months.
- **Measurable Goal**: Increase Tech Support attachment among Fiber users from 37% to 65%.

---

## 5. Analytical Limitations & Governance Notice

1. **Cross-Sectional Dataset**:
   The IBM Telco dataset is a cross-sectional snapshot representing a single monthly observation window. Longitudinal cohort tracking over multi-year panels was not available in this dataset.
2. **Revenue Proxy vs. Net Profit**:
   `MonthlyCharges` reflects gross top-line billings. Net customer profitability requires margin cost accounting, infrastructure delivery costs, and customer acquisition costs (CAC).
3. **Causation vs. Correlation**:
   Observing high churn among Electronic Check users does not prove that the payment method causes dissatisfaction. It may indicate that transient or credit-constrained customers self-select into non-automated payment methods. Interventions must be validated through controlled A/B experimentation before widespread deployment.
