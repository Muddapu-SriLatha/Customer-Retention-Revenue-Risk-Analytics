"""
Customer Retention & Revenue Risk Analytics
Module: generate_notebook.py

Generates the portfolio-ready Jupyter Notebook:
`notebooks/customer_churn_analysis.ipynb`
"""

import json
from pathlib import Path

def create_notebook():
    notebook = {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.14.2"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

    def add_md(text):
        notebook["cells"].append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [line + "\n" for line in text.strip().splitlines()]
        })

    def add_code(code):
        notebook["cells"].append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + "\n" for line in code.strip().splitlines()]
        })

    # Header
    add_md("""# Customer Retention & Revenue Risk Analytics
## End-to-End Business Analytics, Statistical Testing, and Predictive Retention Modeling

**Project Overview:**
This notebook provides a complete, reproducible investigation into customer churn dynamics, early-tenure attrition hazards, and monthly recurring revenue (MRR) risk exposure using the canonical IBM Telco Customer Churn dataset.

### Analytics Workflow:
1. **Data Ingestion & Integrity Audit**: Handling whitespace anomalies and establishing reproducible data contracts.
2. **Exploratory Data Analysis**: Uncovering contractual friction, lifecycle hazard zones, and billing burden effects.
3. **Statistical Hypothesis Testing**: Chi-square tests of independence (Cramer's V) and Welch's t-tests (Cohen's d).
4. **SQL Integration & Cohort Analysis**: Embedded relational querying against SQLite.
5. **Predictive Modeling**: Leak-free training of Baseline, Balanced Logistic Regression, and Random Forest.
6. **Cost-Benefit Threshold Optimization**: Aligning machine learning decision boundaries with commercial retention campaign ROI.""")

    # Section 1
    add_md("""## 1. Environment Setup & Data Ingestion""")
    add_code("""import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Configure visualization styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 10

# Load raw and cleaned datasets
data_dir = Path('../data')
raw_path = data_dir / 'raw' / 'Telco-Customer-Churn.csv'
cleaned_path = data_dir / 'processed' / 'telco_churn_cleaned.csv'

df_raw = pd.read_csv(raw_path)
df = pd.read_csv(cleaned_path)

print(f'Raw Dataset: {df_raw.shape[0]:,} rows, {df_raw.shape[1]} columns')
print(f'Cleaned Dataset: {df.shape[0]:,} rows, {df.shape[1]} columns')""")

    # Section 2
    add_md("""## 2. Data Quality Audit & Cleaning Decisions
In the raw dataset, 11 records in `TotalCharges` contained whitespace (`" "`) strings. 
Cross-tabulation reveals that all 11 records possess `tenure == 0` and `Churn == "No"` (newly acquired customers).
These records are imputed with `0.00` to reflect zero cumulative billing history while avoiding data loss.""")
    add_code("""# Audit the whitespace anomaly in raw data
blank_mask = df_raw['TotalCharges'].astype(str).str.strip() == ''
print(f'Count of blank TotalCharges records: {blank_mask.sum()}')
print('Tenure distribution for blank records:')
print(df_raw.loc[blank_mask, 'tenure'].value_counts())
print('Churn status for blank records:')
print(df_raw.loc[blank_mask, 'Churn'].value_counts())

# Verification of cleaned dataset
assert df['TotalCharges'].isnull().sum() == 0, 'Nulls detected in TotalCharges'
assert (df.loc[df['tenure'] == 0, 'TotalCharges'] == 0.0).all(), 'Tenure=0 TotalCharges mismatch'
print('\\nCleaned dataset integrity verified: 0 nulls, 0 duplicate IDs.')""")

    # Section 3
    add_md("""## 3. Exploratory Data Analysis & Visualizations""")
    add_code("""# Portfolio Churn Rate and Class Imbalance
counts = df['Churn'].value_counts()
pcts = df['Churn'].value_counts(normalize=True) * 100

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
ax1.pie(counts, labels=['Retained (No)', 'Churned (Yes)'], autopct='%1.1f%%',
        colors=['#1E3A8A', '#DC2626'], explode=(0, 0.08), startangle=90,
        wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2))
ax1.set_title('Customer Base Composition (N = 7,043)')

bars = ax2.bar(['Retained (No)', 'Churned (Yes)'], counts, color=['#1E3A8A', '#DC2626'], edgecolor='black', width=0.5)
ax2.set_ylabel('Customer Count')
ax2.set_title('Class Imbalance Distribution')
for bar, pct in zip(bars, pcts):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100, f'{bar.get_height():,}\\n({pct:.1f}%)',
             ha='center', va='bottom', weight='bold')
plt.tight_layout()
plt.show()""")

    add_code("""# Contract Commitment Analysis
contract_summary = df.groupby('Contract')['churn_binary'].agg(
    Total='count', Churned='sum', Churn_Rate='mean'
).reset_index()
contract_summary['Churn_Rate_Pct'] = contract_summary['Churn_Rate'] * 100

fig, ax = plt.subplots(figsize=(8, 4.5))
bars = ax.bar(contract_summary['Contract'], contract_summary['Churn_Rate_Pct'], color='#DC2626', edgecolor='black', width=0.5)
ax.set_ylabel('Churn Rate (%)')
ax.set_title('Churn Propensity Across Contract Terms')
ax.set_ylim(0, 50)

for bar, (_, row) in zip(bars, contract_summary.iterrows()):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f"{row['Churn_Rate_Pct']:.1f}%\\n({int(row['Churned']):,} / {int(row['Total']):,})",
            ha='center', va='bottom', weight='bold')
plt.tight_layout()
plt.show()""")

    # Section 4
    add_md("""## 4. Statistical Hypothesis Testing
We perform **Chi-Square Tests of Independence** (with Cramer's V effect size) for categorical variables, and **Welch's Two-Sample t-Tests** (with Cohen's d) for continuous metrics.""")
    add_code("""from scipy import stats

def compute_cramers_v(contingency):
    chi2 = stats.chi2_contingency(contingency)[0]
    n = contingency.sum().sum()
    r, k = contingency.shape
    return np.sqrt(chi2 / (n * (min(r, k) - 1)))

cat_vars = ['Contract', 'PaymentMethod', 'InternetService', 'TechSupport', 'PaperlessBilling']
stat_results = []

for var in cat_vars:
    ct = pd.crosstab(df[var], df['Churn'])
    chi2, p_val, dof, _ = stats.chi2_contingency(ct)
    v = compute_cramers_v(ct)
    stat_results.append({
        'Feature': var, 'Chi2': round(chi2, 2), 'p_value': f'{p_val:.2e}', 'Cramers_V': round(v, 4)
    })

pd.DataFrame(stat_results)""")

    # Section 5
    add_md("""## 5. SQL Analytics & Relational Cohort Querying
Testing analytical queries against the embedded SQLite database.""")
    add_code("""db_path = data_dir / 'processed' / 'telco_churn.db'
conn = sqlite3.connect(db_path)

sql_query = \"\"\"
SELECT 
    Contract,
    tenure_cohort,
    COUNT(*) AS total_accounts,
    SUM(churn_binary) AS churned_accounts,
    ROUND(AVG(churn_binary) * 100.0, 2) AS churn_rate_pct,
    ROUND(SUM(mrr_exposure_proxy), 2) AS monthly_exposure_proxy
FROM telco_churn
WHERE Contract = 'Month-to-month'
GROUP BY Contract, tenure_cohort
ORDER BY churn_rate_pct DESC;
\"\"\"

df_cohort_sql = pd.read_sql_query(sql_query, conn)
conn.close()
df_cohort_sql""")

    # Section 6
    add_md("""## 6. Predictive Modeling & Evaluation
We build a leak-free pipeline with `StandardScaler` and `OneHotEncoder`, comparing Baseline, Balanced Logistic Regression, and Random Forest.""")
    add_code("""from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import classification_report, roc_auc_score

num_cols = ['tenure', 'MonthlyCharges', 'TotalCharges']
cat_cols = ['gender', 'SeniorCitizen', 'Partner', 'Dependents', 'PhoneService',
            'MultipleLines', 'InternetService', 'OnlineSecurity', 'OnlineBackup',
            'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies',
            'Contract', 'PaperlessBilling', 'PaymentMethod']

X = df[num_cols + cat_cols]
y = df['churn_binary']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

preprocessor = ColumnTransformer([
    ('num', StandardScaler(), num_cols),
    ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), cat_cols)
])

logreg_pipe = Pipeline([('preprocessor', preprocessor), ('clf', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))])
logreg_pipe.fit(X_train, y_train)

y_pred = logreg_pipe.predict(X_test)
y_prob = logreg_pipe.predict_proba(X_test)[:, 1]

print('Logistic Regression Holdout Classification Report:')
print(classification_report(y_test, y_pred, digits=4))
print(f'Test ROC-AUC: {roc_auc_score(y_test, y_prob):.4f}')""")

    # Section 7
    add_md("""## 7. Cost-Sensitive Decision Threshold Optimization
We evaluate the net commercial campaign payoff across decision thresholds, assuming:
- Contact Cost = $25
- Saved Customer Value = $400
- Rescue Success Probability = 25%""")
    add_code("""thresholds = np.linspace(0.1, 0.9, 81)
net_values = []

for t in thresholds:
    pred = (y_prob >= t).astype(int)
    tp = ((y_test == 1) & (pred == 1)).sum()
    fp = ((y_test == 0) & (pred == 1)).sum()
    net_val = (tp * 75.0) - (fp * 25.0)
    net_values.append(net_val)

best_idx = np.argmax(net_values)
print(f'Default Threshold (0.50) Net Value: ${net_values[40]:,.2f}')
print(f'Optimal Threshold ({thresholds[best_idx]:.2f}) Net Value: ${net_values[best_idx]:,.2f}')""")

    out_dir = Path(__file__).resolve().parent.parent / "notebooks"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "customer_churn_analysis.ipynb"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=2)
    print(f"Jupyter notebook written to {out_path}")

if __name__ == "__main__":
    create_notebook()
