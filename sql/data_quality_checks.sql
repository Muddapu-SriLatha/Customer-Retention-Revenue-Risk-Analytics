-- ==============================================================================
-- Customer Retention & Revenue Risk Analytics
-- Script: data_quality_checks.sql
-- Description: Automated data quality audit assertions.
-- All assertions should return 0 failed records.
-- ==============================================================================

-- 1. Check for Duplicate Customer Identifiers
-- Expected Result: 0 records
SELECT 
    customerID, 
    COUNT(*) AS occurrence_count
FROM telco_churn
GROUP BY customerID
HAVING COUNT(*) > 1;

-- 2. Check for Missing (NULL) Values in Critical Columns
-- Expected Result: All counts equal 0
SELECT 
    SUM(CASE WHEN customerID IS NULL THEN 1 ELSE 0 END) AS null_customerID,
    SUM(CASE WHEN tenure IS NULL THEN 1 ELSE 0 END) AS null_tenure,
    SUM(CASE WHEN MonthlyCharges IS NULL THEN 1 ELSE 0 END) AS null_MonthlyCharges,
    SUM(CASE WHEN TotalCharges IS NULL THEN 1 ELSE 0 END) AS null_TotalCharges,
    SUM(CASE WHEN Contract IS NULL THEN 1 ELSE 0 END) AS null_Contract,
    SUM(CASE WHEN PaymentMethod IS NULL THEN 1 ELSE 0 END) AS null_PaymentMethod,
    SUM(CASE WHEN Churn IS NULL THEN 1 ELSE 0 END) AS null_Churn,
    SUM(CASE WHEN churn_binary IS NULL THEN 1 ELSE 0 END) AS null_churn_binary
FROM telco_churn;

-- 3. Check Numerical Boundaries & Range Constraints
-- Expected Result: 0 invalid records
SELECT 
    COUNT(*) AS invalid_numeric_records
FROM telco_churn
WHERE tenure < 0 
   OR MonthlyCharges <= 0 
   OR TotalCharges < 0;

-- 4. Audit Zero-Tenure Records vs TotalCharges
-- Business Rule: Customers with 0 tenure must have TotalCharges = 0.00
-- Expected Result: 0 discrepancy records
SELECT 
    customerID,
    tenure,
    MonthlyCharges,
    TotalCharges,
    Churn
FROM telco_churn
WHERE tenure = 0 AND TotalCharges != 0.0;

-- 5. Audit Target Variable Consistency
-- Verify that Churn='Yes' strictly maps to churn_binary=1 and 'No' to 0
-- Expected Result: 0 mismatch records
SELECT 
    COUNT(*) AS flag_mismatch_count
FROM telco_churn
WHERE (Churn = 'Yes' AND churn_binary != 1)
   OR (Churn = 'No' AND churn_binary != 0);

-- 6. Revenue Exposure Proxy Consistency
-- Business Rule: mrr_exposure_proxy must equal MonthlyCharges when churn_binary=1, and 0 when churn_binary=0
-- Expected Result: 0 mismatch records
SELECT 
    COUNT(*) AS proxy_mismatch_count
FROM telco_churn
WHERE (churn_binary = 1 AND mrr_exposure_proxy != MonthlyCharges)
   OR (churn_binary = 0 AND mrr_exposure_proxy != 0.0);
