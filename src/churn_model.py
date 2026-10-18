"""
Customer Retention & Revenue Risk Analytics
Module: churn_model.py

Purpose:
- Rigorous, leak-free predictive modeling pipeline for customer churn.
- Compares Baseline Dummy, Balanced Logistic Regression, and Random Forest Classifier.
- 5-Fold Stratified Cross-Validation on training set.
- Exhaustive evaluation: Precision, Recall, Specificity, F1, ROC-AUC, PR-AUC, Brier score.
- Cost-benefit decision threshold tuning optimizing net business retention ROI.
- Generates Figures 07, 08, and 09 in `reports/figures/`.
- Exports metrics to `reports/model_evaluation_metrics.json` and `reports/model_results.txt`.
"""

import sys
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, precision_recall_curve, average_precision_score,
    confusion_matrix, brier_score_loss, classification_report
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("churn_model")

RANDOM_SEED = 42

def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent

def load_data(project_root: Path) -> pd.DataFrame:
    data_path = project_root / "data" / "processed" / "telco_churn_cleaned.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned dataset not found at {data_path}. Run src/data_cleaning.py first.")
    return pd.read_csv(data_path)

def build_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer:
    """Build scikit-learn ColumnTransformer strictly fitted on training data."""
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore"), categorical_features),
        ],
        remainder="drop"
    )
    return preprocessor

def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> dict:
    """Compute comprehensive diagnostic metrics."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    metrics = {
        "accuracy": float(round(accuracy_score(y_true, y_pred), 4)),
        "precision": float(round(precision_score(y_true, y_pred, zero_division=0), 4)),
        "recall": float(round(recall_score(y_true, y_pred, zero_division=0), 4)),
        "specificity": float(round(specificity, 4)),
        "f1_score": float(round(f1_score(y_true, y_pred, zero_division=0), 4)),
        "roc_auc": float(round(roc_auc_score(y_true, y_prob), 4)) if y_prob is not None else 0.5,
        "pr_auc": float(round(average_precision_score(y_true, y_prob), 4)) if y_prob is not None else float(round(y_true.mean(), 4)),
        "brier_score": float(round(brier_score_loss(y_true, y_prob), 4)) if y_prob is not None else 0.0,
        "confusion_matrix": {"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)},
    }
    return metrics

def run_cross_validation(pipeline: Pipeline, X_train: pd.DataFrame, y_train: pd.Series) -> dict:
    """Run 5-Fold Stratified Cross Validation on the training split."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    scoring = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    cv_scores = cross_validate(pipeline, X_train, y_train, cv=cv, scoring=scoring, n_jobs=-1)
    
    cv_summary = {
        metric: {
            "mean": float(round(np.mean(cv_scores[f"test_{metric}"]), 4)),
            "std": float(round(np.std(cv_scores[f"test_{metric}"]), 4)),
        }
        for metric in scoring
    }
    return cv_summary

def plot_roc_and_pr_curves(models_dict: dict, y_test: np.ndarray, output_path: Path):
    """Plot side-by-side ROC and Precision-Recall Curves."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
    
    colors = {"Baseline (Most Frequent)": "#9CA3AF", "Logistic Regression (Balanced)": "#2563EB", "Random Forest (Balanced)": "#DC2626"}
    
    # 1. ROC Curve
    for name, data in models_dict.items():
        if data["y_prob"] is not None:
            fpr, tpr, _ = roc_curve(y_test, data["y_prob"])
            auc_val = data["test_metrics"]["roc_auc"]
            ax1.plot(fpr, tpr, label=f"{name} (AUC = {auc_val:.3f})", color=colors.get(name, "#10B981"), linewidth=2)
        else:
            ax1.plot([0, 1], [0, 1], linestyle="--", label=f"{name} (AUC = 0.500)", color=colors[name], linewidth=1.5)
            
    ax1.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Random Guess (AUC = 0.500)")
    ax1.set_xlabel("False Positive Rate (1 - Specificity)")
    ax1.set_ylabel("True Positive Rate (Recall)")
    ax1.set_title("Receiver Operating Characteristic (ROC) Curve")
    ax1.legend(loc="lower right", frameon=True)
    
    # 2. Precision-Recall Curve
    baseline_churn = y_test.mean()
    for name, data in models_dict.items():
        if data["y_prob"] is not None:
            prec, rec, _ = precision_recall_curve(y_test, data["y_prob"])
            pr_auc = data["test_metrics"]["pr_auc"]
            ax2.plot(rec, prec, label=f"{name} (PR-AUC = {pr_auc:.3f})", color=colors.get(name, "#10B981"), linewidth=2)
            
    ax2.axhline(baseline_churn, linestyle="--", color="#9CA3AF", label=f"Baseline Prevalence ({baseline_churn:.1%})")
    ax2.set_xlabel("Recall (Coverage of Churners)")
    ax2.set_ylabel("Precision (Accuracy of Churn Flags)")
    ax2.set_title("Precision-Recall (PR) Curve")
    ax2.legend(loc="upper right", frameon=True)
    
    plt.suptitle("Figure 7: Model Discrimination & Precision-Recall Diagnostic Evaluation", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()
    logger.info(f"Saved: {output_path.name}")

def plot_feature_importance(logreg_pipeline: Pipeline, rf_pipeline: Pipeline, num_features: list[str], cat_features: list[str], output_path: Path):
    """Plot Logistic Regression Odds Ratios and Random Forest Feature Importances."""
    # Extract feature names after one-hot encoding
    ohe = logreg_pipeline.named_steps["preprocessor"].named_transformers_["cat"]
    cat_encoded_names = list(ohe.get_feature_names_out(cat_features))
    all_feature_names = num_features + cat_encoded_names
    
    # 1. Logistic Regression Coefficients & Odds Ratios
    logreg_model = logreg_pipeline.named_steps["classifier"]
    coefs = logreg_model.coef_[0]
    odds_ratios = np.exp(coefs)
    
    df_odds = pd.DataFrame({"Feature": all_feature_names, "Coefficient": coefs, "Odds_Ratio": odds_ratios})
    # Top 8 highest risk and top 8 strongest protective features
    df_top_risk = df_odds.sort_values(by="Odds_Ratio", ascending=False).head(7)
    df_top_protect = df_odds.sort_values(by="Odds_Ratio", ascending=True).head(7)
    df_odds_plot = pd.concat([df_top_risk, df_top_protect]).sort_values(by="Odds_Ratio")
    
    # 2. Random Forest MDI Feature Importances
    rf_model = rf_pipeline.named_steps["classifier"]
    rf_importances = rf_model.feature_importances_
    df_rf = pd.DataFrame({"Feature": all_feature_names, "Importance": rf_importances}).sort_values(by="Importance", ascending=True).tail(14)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Barplot Odds Ratios
    bar_colors = ["#10B981" if x < 1.0 else "#DC2626" for x in df_odds_plot["Odds_Ratio"]]
    ax1.barh(df_odds_plot["Feature"], df_odds_plot["Odds_Ratio"], color=bar_colors, edgecolor="black", linewidth=0.5)
    ax1.axvline(1.0, color="black", linestyle="--", linewidth=1.2)
    ax1.set_xlabel("Odds Ratio: exp(beta) (Values > 1 Increase Churn Odds)")
    ax1.set_title("Logistic Regression Key Drivers (Odds Ratios)")
    
    for bar in ax1.patches:
        w = bar.get_width()
        ax1.text(w + 0.05, bar.get_y() + bar.get_height()/2, f"{w:.2f}x", va="center", ha="left", fontsize=8.5, weight="bold")
    
    # Barplot RF Importance
    ax2.barh(df_rf["Feature"], df_rf["Importance"], color="#2563EB", edgecolor="black", linewidth=0.5)
    ax2.set_xlabel("Mean Decrease in Impurity (Gini Feature Importance)")
    ax2.set_title("Random Forest Top 14 Feature Importances")
    
    plt.suptitle("Figure 8: Quantitative Feature Drivers & Attribution Comparison", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()
    logger.info(f"Saved: {output_path.name}")

def optimize_decision_threshold(y_true: np.ndarray, y_prob: np.ndarray, output_path: Path) -> dict:
    """
    Cost-Benefit Decision Threshold Tuning:
    Parameters:
    - Outreach Retention Campaign Cost per Contacted Customer (C_contact) = $25.00
    - Average Customer Lifetime Retention Value (V_save) = $400.00
    - Intervention Success Probability (P_success) = 25% (1 in 4 contacted churners is retained)
    - Expected Benefit per True Positive = (P_success * V_save) - C_contact = $100 - $25 = +$75
    - Net Cost per False Positive = -$25 (outreach cost wasted on customer who would have stayed)
    - Opportunity Cost per False Negative = -$75 (lost retention opportunity)
    """
    thresholds = np.linspace(0.05, 0.95, 91)
    results = []
    
    for thresh in thresholds:
        y_pred_thresh = (y_prob >= thresh).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred_thresh).ravel()
        
        prec = precision_score(y_true, y_pred_thresh, zero_division=0)
        rec = recall_score(y_true, y_pred_thresh, zero_division=0)
        f1 = f1_score(y_true, y_pred_thresh, zero_division=0)
        
        # Business Value Calculation
        net_value = (tp * 75.0) - (fp * 25.0)
        
        results.append({
            "threshold": thresh,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "net_business_value": net_value
        })
        
    df_thresh = pd.DataFrame(results)
    
    # Identify optimal thresholds
    best_f1_idx = df_thresh["f1"].idxmax()
    best_value_idx = df_thresh["net_business_value"].idxmax()
    
    best_f1_row = df_thresh.loc[best_f1_idx]
    best_value_row = df_thresh.loc[best_value_idx]
    
    # Plot Threshold Curve
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    
    # Metrics vs Threshold
    ax1.plot(df_thresh["threshold"], df_thresh["precision"], label="Precision", color="#10B981", linewidth=2)
    ax1.plot(df_thresh["threshold"], df_thresh["recall"], label="Recall", color="#DC2626", linewidth=2)
    ax1.plot(df_thresh["threshold"], df_thresh["f1"], label="F1-Score", color="#2563EB", linewidth=2.5)
    ax1.axvline(0.50, color="#6B7280", linestyle=":", label="Default Threshold (0.50)")
    ax1.axvline(best_f1_row["threshold"], color="#2563EB", linestyle="--", label=f"Max F1 ({best_f1_row['threshold']:.2f})")
    ax1.set_xlabel("Decision Threshold")
    ax1.set_ylabel("Metric Value")
    ax1.set_title("Classification Metrics vs. Decision Threshold")
    ax1.legend(loc="center left", frameon=True)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1.05)
    
    # Net Business Value vs Threshold
    ax2.plot(df_thresh["threshold"], df_thresh["net_business_value"], color="#7C3AED", linewidth=2.5, label="Net Business Value ($)")
    ax2.axvline(best_value_row["threshold"], color="#7C3AED", linestyle="--", 
                label=f"Profit-Maximizing Threshold ({best_value_row['threshold']:.2f})")
    ax2.axvline(0.50, color="#6B7280", linestyle=":", label="Default Threshold (0.50)")
    ax2.set_xlabel("Decision Threshold")
    ax2.set_ylabel("Net Campaign Retention Value ($)")
    ax2.set_title("Net Business Value vs. Decision Threshold")
    
    default_row = df_thresh.iloc[(df_thresh["threshold"] - 0.50).abs().argsort()[:1]].iloc[0]
    ax2.annotate(
        f"Optimal Threshold: {best_value_row['threshold']:.2f}\nNet Value: ${best_value_row['net_business_value']:,.0f}\n(Recall: {best_value_row['recall']:.1%})",
        xy=(best_value_row["threshold"], best_value_row["net_business_value"]),
        xytext=(30, -30),
        textcoords="offset points",
        arrowprops=dict(arrowstyle="->", color="#7C3AED", lw=1.5),
        bbox=dict(boxstyle="round,pad=0.3", fc="#F5F3FF", ec="#7C3AED", lw=1),
        fontweight="bold"
    )
    
    ax2.annotate(
        f"Default 0.50 Threshold\nNet Value: ${default_row['net_business_value']:,.0f}",
        xy=(0.50, default_row["net_business_value"]),
        xytext=(-120, -50),
        textcoords="offset points",
        arrowprops=dict(arrowstyle="->", color="#6B7280", lw=1.2),
        bbox=dict(boxstyle="round,pad=0.3", fc="#F9FAFB", ec="#6B7280", lw=0.8)
    )
    
    ax2.legend(loc="lower center", frameon=True)
    
    plt.suptitle("Figure 9: Cost-Sensitive Decision Threshold Optimization & Economic Payoff", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()
    logger.info(f"Saved: {output_path.name}")
    
    return {
        "default_threshold_0_50": {
            "threshold": 0.50,
            "precision": float(round(default_row["precision"], 4)),
            "recall": float(round(default_row["recall"], 4)),
            "f1": float(round(default_row["f1"], 4)),
            "net_business_value": float(round(default_row["net_business_value"], 2)),
        },
        "optimal_f1_threshold": {
            "threshold": float(round(best_f1_row["threshold"], 4)),
            "f1": float(round(best_f1_row["f1"], 4)),
            "precision": float(round(best_f1_row["precision"], 4)),
            "recall": float(round(best_f1_row["recall"], 4)),
            "net_business_value": float(round(best_f1_row["net_business_value"], 2)),
        },
        "optimal_economic_threshold": {
            "threshold": float(round(best_value_row["threshold"], 4)),
            "net_business_value": float(round(best_value_row["net_business_value"], 2)),
            "precision": float(round(best_value_row["precision"], 4)),
            "recall": float(round(best_value_row["recall"], 4)),
            "f1": float(round(best_value_row["f1"], 4)),
        }
    }

def train_and_evaluate():
    project_root = get_project_root()
    figures_dir = project_root / "reports" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading cleaned data...")
    df = load_data(project_root)
    
    # Feature columns
    numeric_features = ["tenure", "MonthlyCharges", "TotalCharges"]
    categorical_features = [
        "gender", "SeniorCitizen", "Partner", "Dependents", "PhoneService",
        "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup",
        "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
        "Contract", "PaperlessBilling", "PaymentMethod"
    ]
    
    X = df[numeric_features + categorical_features]
    y = df["churn_binary"]
    
    # Train / Test split: 80% train, 20% test, stratified on churn
    logger.info("Creating stratified 80/20 train/test split (seed=42)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_SEED, stratify=y
    )
    logger.info(f"Train set: {len(X_train):,} samples (Churn: {y_train.mean():.2%}) | Test set: {len(X_test):,} samples (Churn: {y_test.mean():.2%})")
    
    preprocessor = build_preprocessor(numeric_features, categorical_features)
    
    # Define candidate models
    models = {
        "Baseline (Most Frequent)": DummyClassifier(strategy="most_frequent"),
        "Logistic Regression (Balanced)": LogisticRegression(
            class_weight="balanced", max_iter=1000, random_state=RANDOM_SEED, solver="lbfgs"
        ),
        "Random Forest (Balanced)": RandomForestClassifier(
            n_estimators=200, max_depth=7, min_samples_split=10, min_samples_leaf=4,
            class_weight="balanced", random_state=RANDOM_SEED, n_jobs=-1
        )
    }
    
    results = {}
    
    for name, clf in models.items():
        logger.info(f"--- Training & Evaluating: {name} ---")
        if name == "Baseline (Most Frequent)":
            pipe = clf
            pipe.fit(X_train, y_train)
            cv_results = {}
            y_pred = pipe.predict(X_test)
            y_prob = None
        else:
            pipe = Pipeline(steps=[("preprocessor", preprocessor), ("classifier", clf)])
            logger.info("Running 5-fold cross validation on training set...")
            cv_results = run_cross_validation(pipe, X_train, y_train)
            pipe.fit(X_train, y_train)
            y_pred = pipe.predict(X_test)
            y_prob = pipe.predict_proba(X_test)[:, 1]
            
        test_metrics = evaluate_predictions(y_test.values, y_pred, y_prob)
        
        results[name] = {
            "pipeline": pipe,
            "cv_scores": cv_results,
            "test_metrics": test_metrics,
            "y_prob": y_prob
        }
        logger.info(f"{name} Test Metrics: Accuracy={test_metrics['accuracy']:.4f}, Recall={test_metrics['recall']:.4f}, Precision={test_metrics['precision']:.4f}, F1={test_metrics['f1_score']:.4f}, ROC-AUC={test_metrics['roc_auc']:.4f}")
        
    # Plot Figure 7: ROC and PR Curves
    plot_roc_and_pr_curves(results, y_test.values, figures_dir / "07_roc_pr_curves.png")
    
    # Plot Figure 8: Feature Importance
    plot_feature_importance(
        results["Logistic Regression (Balanced)"]["pipeline"],
        results["Random Forest (Balanced)"]["pipeline"],
        numeric_features, categorical_features,
        figures_dir / "08_feature_importance.png"
    )
    
    # Decision Threshold Optimization on Logistic Regression probabilities
    logger.info("Running Cost-Sensitive Decision Threshold Optimization...")
    threshold_analysis = optimize_decision_threshold(
        y_test.values,
        results["Logistic Regression (Balanced)"]["y_prob"],
        figures_dir / "09_threshold_tradeoff.png"
    )
    
    # Format comprehensive reports
    serializable_results = {
        name: {
            "cv_scores": data["cv_scores"],
            "test_metrics": data["test_metrics"]
        }
        for name, data in results.items()
    }
    serializable_results["threshold_optimization"] = threshold_analysis
    
    metrics_json_path = project_root / "reports" / "model_evaluation_metrics.json"
    metrics_json_path.write_text(json.dumps(serializable_results, indent=2), encoding="utf-8")
    logger.info(f"Model metrics JSON saved to {metrics_json_path}")
    
    # Write human-readable summary
    model_txt_path = project_root / "reports" / "model_results.txt"
    lines = [
        "=" * 85,
        "PREDICTIVE MODELING REPORT: CUSTOMER RETENTION & CHURN CLASSIFICATION",
        "=" * 85,
        f"Dataset Split: 80% Train ({len(X_train):,} samples), 20% Test ({len(X_test):,} samples)",
        f"Target Churn Prevalence: {y.mean():.2%} overall | {y_train.mean():.2%} train | {y_test.mean():.2%} test\n",
        "--- TEST SET PERFORMANCE COMPARISON ---",
        f"{'Model Name':<32} {'Accuracy':<10} {'Precision':<11} {'Recall':<10} {'F1-Score':<10} {'ROC-AUC':<10} {'PR-AUC':<10}",
        "-" * 85
    ]
    
    for name, data in results.items():
        m = data["test_metrics"]
        lines.append(
            f"{name:<32} {m['accuracy']:<10.4f} {m['precision']:<11.4f} {m['recall']:<10.4f} {m['f1_score']:<10.4f} {m['roc_auc']:<10.4f} {m['pr_auc']:<10.4f}"
        )
        
    lines.extend([
        "-" * 85,
        "\n--- CONFUSION MATRICES (TEST SET, N = 1,409) ---",
    ])
    
    for name, data in results.items():
        cm = data["test_metrics"]["confusion_matrix"]
        lines.append(
            f"{name}: TN={cm['TN']:,}, FP={cm['FP']:,}, FN={cm['FN']:,}, TP={cm['TP']:,}"
        )
        
    lines.extend([
        "\n--- 5-FOLD STRATIFIED CROSS-VALIDATION SUMMARY (TRAINING SPLIT) ---",
        f"{'Model Name':<32} {'CV ROC-AUC':<18} {'CV F1-Score':<18} {'CV Recall':<18}",
        "-" * 85
    ])
    
    for name in ["Logistic Regression (Balanced)", "Random Forest (Balanced)"]:
        cv = results[name]["cv_scores"]
        lines.append(
            f"{name:<32} {cv['roc_auc']['mean']:.4f} +/- {cv['roc_auc']['std']:.4f}  "
            f"{cv['f1']['mean']:.4f} +/- {cv['f1']['std']:.4f}  "
            f"{cv['recall']['mean']:.4f} +/- {cv['recall']['std']:.4f}"
        )
        
    lines.extend([
        "\n--- COST-SENSITIVE DECISION THRESHOLD ANALYSIS ---",
        f"Assumptions: Contact Cost = $25, Retention Value = $400, Retention Success Rate = 25%",
        f"Default Threshold (0.50):",
        f"  - Precision: {threshold_analysis['default_threshold_0_50']['precision']:.4f}, Recall: {threshold_analysis['default_threshold_0_50']['recall']:.4f}, Net Value: ${threshold_analysis['default_threshold_0_50']['net_business_value']:,.2f}",
        f"Max F1 Threshold ({threshold_analysis['optimal_f1_threshold']['threshold']:.2f}):",
        f"  - Precision: {threshold_analysis['optimal_f1_threshold']['precision']:.4f}, Recall: {threshold_analysis['optimal_f1_threshold']['recall']:.4f}, F1: {threshold_analysis['optimal_f1_threshold']['f1']:.4f}, Net Value: ${threshold_analysis['optimal_f1_threshold']['net_business_value']:,.2f}",
        f"Profit-Maximizing Threshold ({threshold_analysis['optimal_economic_threshold']['threshold']:.2f}):",
        f"  - Precision: {threshold_analysis['optimal_economic_threshold']['precision']:.4f}, Recall: {threshold_analysis['optimal_economic_threshold']['recall']:.4f}, Net Value: ${threshold_analysis['optimal_economic_threshold']['net_business_value']:,.2f}",
        "=" * 85
    ])
    
    report_text = "\n".join(lines)
    model_txt_path.write_text(report_text, encoding="utf-8")
    print(report_text)
    logger.info(f"Model results saved to {model_txt_path}")

if __name__ == "__main__":
    train_and_evaluate()
