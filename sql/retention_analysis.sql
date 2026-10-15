-- ==============================================================================
-- Customer Retention & Revenue Risk Analytics
-- Script: retention_analysis.sql
-- Database Engine: SQLite / PostgreSQL Compatible ANSI SQL
-- Description: Core analytical queries covering portfolio metrics, customer
--              segmentation, window function ranking, and revenue risk exposure.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- QUERY 1: Overall Portfolio Performance & Churn Rate
-- Metric Definitions:
-- - total_customers: Total active and churned customer count in the dataset.
-- - churned_customers: Count of customers who severed service in the prior month.
-- - portfolio_churn_rate_pct: (churned_customers / total_customers) * 100.
-- - total_monthly_billings: Aggregate monthly billing volume across all accounts.
-- - monthly_exposure_proxy: Aggregate monthly billing volume lost to churned accounts.
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_customers,
    SUM(churn_binary) AS churned_customers,
    COUNT(*) - SUM(churn_binary) AS retained_customers,
    ROUND(AVG(churn_binary) * 100.0, 2) AS portfolio_churn_rate_pct,
    ROUND(SUM(MonthlyCharges), 2) AS total_monthly_billings,
    ROUND(SUM(mrr_exposure_proxy), 2) AS churned_monthly_exposure_proxy,
    ROUND((SUM(mrr_exposure_proxy) / SUM(MonthlyCharges)) * 100.0, 2) AS pct_monthly_revenue_exposed,
    ROUND(SUM(TotalCharges), 2) AS total_historical_realized_revenue
FROM telco_churn;


-- ------------------------------------------------------------------------------
-- QUERY 2: Churn Propensity & Volume by Contract Commitment Term
-- Business Context: Examines contractual friction vs customer switching flexibility.
-- ------------------------------------------------------------------------------
SELECT 
    Contract,
    COUNT(*) AS customer_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM telco_churn), 2) AS pct_of_customer_base,
    SUM(churn_binary) AS churned_count,
    ROUND(AVG(churn_binary) * 100.0, 2) AS churn_rate_pct,
    ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charges,
    ROUND(SUM(mrr_exposure_proxy), 2) AS total_mrr_exposure_proxy
FROM telco_churn
GROUP BY Contract
ORDER BY churn_rate_pct DESC;


-- ------------------------------------------------------------------------------
-- QUERY 3: Customer Lifecycle Cohort Analysis (Tenure Group x Contract)
-- Business Context: Identifies the vulnerable "onboarding hazard zone" in early tenure.
-- ------------------------------------------------------------------------------
SELECT 
    tenure_cohort,
    Contract,
    COUNT(*) AS cohort_size,
    SUM(churn_binary) AS churned_count,
    ROUND(AVG(churn_binary) * 100.0, 2) AS churn_rate_pct,
    ROUND(SUM(mrr_exposure_proxy), 2) AS cohort_mrr_exposure_proxy
FROM telco_churn
GROUP BY tenure_cohort, Contract
ORDER BY 
    CASE tenure_cohort
        WHEN '0-12 Months' THEN 1
        WHEN '13-24 Months' THEN 2
        WHEN '25-48 Months' THEN 3
        WHEN '49-60 Months' THEN 4
        WHEN '61-72 Months' THEN 5
        ELSE 6
    END,
    churn_rate_pct DESC;


-- ------------------------------------------------------------------------------
-- QUERY 4: Financial Metrics & Billing Burden Comparison by Churn Status
-- Business Context: Tests whether churned customers had systematically higher price burden.
-- ------------------------------------------------------------------------------
SELECT 
    Churn,
    COUNT(*) AS customer_count,
    ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charges,
    ROUND(MIN(MonthlyCharges), 2) AS min_monthly_charges,
    ROUND(MAX(MonthlyCharges), 2) AS max_monthly_charges,
    ROUND(AVG(TotalCharges), 2) AS avg_lifetime_charges,
    ROUND(AVG(tenure), 1) AS avg_tenure_months,
    -- Proxy for average revenue per customer per month of relationship
    ROUND(AVG(TotalCharges / NULLIF(tenure, 0)), 2) AS realized_monthly_yield
FROM telco_churn
GROUP BY Churn;


-- ------------------------------------------------------------------------------
-- QUERY 5: Multi-Dimensional Customer Segmentation (Internet x Tech Support x Billing)
-- Business Context: Pinpoints the specific product configurations that drive attrition.
-- ------------------------------------------------------------------------------
SELECT 
    InternetService,
    TechSupport,
    PaymentMethod,
    COUNT(*) AS segment_size,
    SUM(churn_binary) AS churned_count,
    ROUND(AVG(churn_binary) * 100.0, 2) AS churn_rate_pct,
    ROUND(SUM(MonthlyCharges), 2) AS segment_monthly_billings,
    ROUND(SUM(mrr_exposure_proxy), 2) AS segment_mrr_exposure_proxy
FROM telco_churn
GROUP BY InternetService, TechSupport, PaymentMethod
HAVING COUNT(*) >= 50
ORDER BY churn_rate_pct DESC;


-- ------------------------------------------------------------------------------
-- QUERY 6: Ranking High-Risk Customer Segments Using Window Functions
-- Business Context:
-- Ranks segments by monthly charge exposure and churn rate.
-- Computes running cumulative percentage of portfolio revenue exposure.
-- ------------------------------------------------------------------------------
WITH SegmentMetrics AS (
    SELECT 
        Contract,
        InternetService,
        PaymentMethod,
        COUNT(*) AS total_customers,
        SUM(churn_binary) AS churned_customers,
        ROUND(AVG(churn_binary) * 100.0, 2) AS segment_churn_rate_pct,
        ROUND(SUM(MonthlyCharges), 2) AS total_segment_monthly_revenue,
        ROUND(SUM(mrr_exposure_proxy), 2) AS segment_mrr_exposure_proxy
    FROM telco_churn
    GROUP BY Contract, InternetService, PaymentMethod
)
SELECT 
    Contract,
    InternetService,
    PaymentMethod,
    total_customers,
    churned_customers,
    segment_churn_rate_pct,
    segment_mrr_exposure_proxy,
    -- Window Function: Rank segments by absolute MRR exposure
    DENSE_RANK() OVER (ORDER BY segment_mrr_exposure_proxy DESC) AS exposure_rank,
    -- Window Function: Rank segments by churn rate
    DENSE_RANK() OVER (ORDER BY segment_churn_rate_pct DESC) AS churn_rate_rank,
    -- Window Function: Cumulative MRR Exposure
    ROUND(SUM(segment_mrr_exposure_proxy) OVER (
        ORDER BY segment_mrr_exposure_proxy DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS cumulative_mrr_exposure,
    -- Window Function: Cumulative Percentage of Total Churned Exposure
    ROUND(
        SUM(segment_mrr_exposure_proxy) OVER (
            ORDER BY segment_mrr_exposure_proxy DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) * 100.0 / (SELECT SUM(mrr_exposure_proxy) FROM telco_churn), 
        2
    ) AS cumulative_pct_of_total_exposure
FROM SegmentMetrics
ORDER BY segment_mrr_exposure_proxy DESC;


-- ------------------------------------------------------------------------------
-- QUERY 7: Advanced CTE - Segment Risk Index vs Portfolio Baseline
-- Business Context:
-- Calculates a "Risk Index" = (Segment Churn Rate / Baseline Churn Rate) * 100.
-- Identifies hyper-vulnerable clusters where risk index > 150 (50% above baseline).
-- ------------------------------------------------------------------------------
WITH Baseline AS (
    SELECT 
        AVG(churn_binary) * 100.0 AS baseline_churn_rate,
        SUM(mrr_exposure_proxy) AS total_portfolio_exposure
    FROM telco_churn
),
CohortAnalysis AS (
    SELECT 
        Contract,
        charge_tier,
        is_electronic_check,
        has_tech_support,
        COUNT(*) AS customer_count,
        SUM(churn_binary) AS churned_count,
        ROUND(AVG(churn_binary) * 100.0, 2) AS cohort_churn_rate,
        ROUND(SUM(mrr_exposure_proxy), 2) AS cohort_mrr_exposure
    FROM telco_churn
    GROUP BY Contract, charge_tier, is_electronic_check, has_tech_support
)
SELECT 
    c.Contract,
    c.charge_tier,
    CASE WHEN c.is_electronic_check = 1 THEN 'Electronic Check' ELSE 'Other Payment' END AS payment_channel,
    CASE WHEN c.has_tech_support = 1 THEN 'Yes' ELSE 'No' END AS tech_support_status,
    c.customer_count,
    c.churned_count,
    c.cohort_churn_rate,
    ROUND((c.cohort_churn_rate / b.baseline_churn_rate) * 100.0, 1) AS churn_risk_index,
    c.cohort_mrr_exposure,
    ROUND((c.cohort_mrr_exposure / b.total_portfolio_exposure) * 100.0, 2) AS pct_of_total_portfolio_exposure
FROM CohortAnalysis c
CROSS JOIN Baseline b
WHERE c.customer_count >= 30
ORDER BY churn_risk_index DESC;
