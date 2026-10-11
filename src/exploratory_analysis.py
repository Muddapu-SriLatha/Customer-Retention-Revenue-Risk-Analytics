"""
Customer Retention & Revenue Risk Analytics
Module: exploratory_analysis.py

Purpose:
- Generate portfolio-quality, high-resolution exploratory figures.
- Analyze customer churn by contract, tenure, monthly charges, payment method, and service features.
- Distinguish observations from hypotheses, avoiding correlation-causation fallacies.
- Save figures directly to `reports/figures/`.
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("exploratory_analysis")

# Aesthetics & Design Settings
PALETTE_PRIMARY = "#1E3A8A"     # Deep corporate blue (Retained)
PALETTE_ACCENT = "#DC2626"      # Vivid crimson red (Churned)
PALETTE_NEUTRAL = "#6B7280"     # Slate grey
PALETTE_BG = "#F9FAFB"          # Soft light background

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "axes.labelweight": "bold",
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 15,
    "figure.titleweight": "bold",
    "figure.dpi": 300,
})

def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent

def load_data(project_root: Path) -> pd.DataFrame:
    data_path = project_root / "data" / "processed" / "telco_churn_cleaned.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned dataset not found at {data_path}. Run src/data_cleaning.py first.")
    return pd.read_csv(data_path)

def plot_01_churn_distribution(df: pd.DataFrame, output_dir: Path):
    """Figure 1: Overall Churn Distribution and Class Imbalance."""
    counts = df["Churn"].value_counts()
    percentages = df["Churn"].value_counts(normalize=True) * 100

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Donut Chart
    colors = [PALETTE_PRIMARY, PALETTE_ACCENT]
    wedges, texts, autotexts = ax1.pie(
        counts,
        labels=["Retained (No)", "Churned (Yes)"],
        autopct="%1.1f%%",
        startangle=90,
        colors=colors,
        pctdistance=0.75,
        explode=(0, 0.06),
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2)
    )
    plt.setp(autotexts, size=11, weight="bold", color="white")
    plt.setp(texts, size=11, weight="semibold")
    ax1.set_title("Overall Customer Composition\n(N = 7,043)", pad=15)

    # Bar Chart with Counts & Percentages
    bars = ax2.bar(["Retained (No)", "Churned (Yes)"], counts, color=colors, width=0.55, edgecolor="black", linewidth=0.5)
    ax2.set_ylabel("Customer Count")
    ax2.set_title("Class Imbalance Count Comparison", pad=15)
    ax2.set_ylim(0, 6000)

    for bar, pct in zip(bars, percentages):
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2.0, yval + 120, f"{yval:,}\n({pct:.1f}%)", ha="center", va="bottom", weight="bold")

    plt.suptitle("Figure 1: Customer Churn Distribution & Class Imbalance Audit", y=1.02)
    plt.tight_layout()
    output_path = output_dir / "01_churn_distribution.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved: {output_path.name}")

def plot_02_churn_by_contract(df: pd.DataFrame, output_dir: Path):
    """Figure 2: Churn Rate and Customer Volume by Contract Commitment."""
    summary = df.groupby("Contract")["churn_binary"].agg(Total="count", Churned="sum", Rate="mean").reset_index()
    summary["Retained"] = summary["Total"] - summary["Churned"]
    summary["RatePct"] = summary["Rate"] * 100

    # Sort order
    order = ["Month-to-month", "One year", "Two year"]
    summary = summary.set_index("Contract").loc[order].reset_index()

    fig, ax1 = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(summary))
    width = 0.35

    rects1 = ax1.bar(x - width/2, summary["Retained"], width, label="Retained", color=PALETTE_PRIMARY, edgecolor="black", linewidth=0.5)
    rects2 = ax1.bar(x + width/2, summary["Churned"], width, label="Churned", color=PALETTE_ACCENT, edgecolor="black", linewidth=0.5)

    ax1.set_ylabel("Customer Count", weight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(summary["Contract"], weight="semibold")
    ax1.set_title("Figure 2: Customer Volume and Churn Propensity by Contract Type", pad=20)
    ax1.legend(loc="upper right", frameon=True)
    ax1.set_ylim(0, 4200)

    # Annotate churn rates above bars
    for idx, row in summary.iterrows():
        churn_h = row["Churned"]
        ax1.annotate(
            f"Churn Rate: {row['RatePct']:.1f}%\n({int(row['Churned']):,} / {int(row['Total']):,})",
            xy=(idx + width/2, churn_h),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9.5,
            fontweight="bold",
            color=PALETTE_ACCENT,
            bbox=dict(boxstyle="round,pad=0.25", fc="#FEF2F2", ec=PALETTE_ACCENT, lw=0.8)
        )

    plt.tight_layout()
    output_path = output_dir / "02_churn_by_contract.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved: {output_path.name}")

def plot_03_tenure_distribution(df: pd.DataFrame, output_dir: Path):
    """Figure 3: Customer Tenure Distribution by Churn Status."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # KDE overlay
    sns.kdeplot(data=df[df["Churn"] == "No"]["tenure"], ax=ax1, color=PALETTE_PRIMARY, fill=True, alpha=0.35, label="Retained", linewidth=2)
    sns.kdeplot(data=df[df["Churn"] == "Yes"]["tenure"], ax=ax1, color=PALETTE_ACCENT, fill=True, alpha=0.35, label="Churned", linewidth=2)
    ax1.set_xlabel("Tenure (Months)")
    ax1.set_ylabel("Density")
    ax1.set_title("Tenure Kernel Density Estimation (KDE)")
    ax1.legend(frameon=True)

    # Tenure Cohort Churn Rates
    cohort_order = ["0-12 Months", "13-24 Months", "25-48 Months", "49-60 Months", "61-72 Months"]
    cohort_summary = df.groupby("tenure_cohort", observed=True)["churn_binary"].agg(Count="count", Rate="mean").loc[cohort_order]
    
    bars = ax2.bar(cohort_summary.index, cohort_summary["Rate"] * 100, color="#E11D48", width=0.55, edgecolor="black", linewidth=0.5)
    ax2.set_ylabel("Churn Rate (%)")
    ax2.set_title("Churn Rate by Tenure Cohort")
    ax2.set_xticks(range(len(cohort_order)))
    ax2.set_xticklabels(cohort_order, rotation=20, ha="right")
    ax2.set_ylim(0, 58)

    for bar, rate, count in zip(bars, cohort_summary["Rate"] * 100, cohort_summary["Count"]):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5, f"{rate:.1f}%\n(n={count:,})", ha="center", va="bottom", fontsize=8.5, weight="bold")

    plt.suptitle("Figure 3: Customer Lifecycle & Early-Tenure Attrition Hazard", y=1.03)
    plt.tight_layout()
    output_path = output_dir / "03_tenure_distribution_by_churn.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved: {output_path.name}")

def plot_04_monthly_charges_distribution(df: pd.DataFrame, output_dir: Path):
    """Figure 4: Distribution of Monthly Charges across Churn Status."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # Boxplot with overlaid mean diamonds
    sns.boxplot(
        data=df,
        x="Churn",
        y="MonthlyCharges",
        hue="Churn",
        palette=[PALETTE_PRIMARY, PALETTE_ACCENT],
        width=0.45,
        ax=ax1,
        legend=False,
        showmeans=True,
        meanprops={"marker": "D", "markeredgecolor": "black", "markerfacecolor": "yellow", "markersize": 7}
    )
    ax1.set_title("Monthly Charges Boxplot (Mean = Yellow Diamond)")
    ax1.set_xlabel("Customer Churn Status")
    ax1.set_ylabel("Monthly Charges (USD)")

    # Overlay empirical medians & means
    retained_mean = df[df["Churn"] == "No"]["MonthlyCharges"].mean()
    churn_mean = df[df["Churn"] == "Yes"]["MonthlyCharges"].mean()
    ax1.text(0, retained_mean + 3, f"Mean: ${retained_mean:.2f}", ha="center", weight="bold", color=PALETTE_PRIMARY)
    ax1.text(1, churn_mean + 3, f"Mean: ${churn_mean:.2f}", ha="center", weight="bold", color=PALETTE_ACCENT)

    # Charge Tier Churn Rates
    tier_order = ["Low (<$35)", "Medium ($35-$70)", "High ($70-$90)", "Very High (>$90)"]
    tier_summary = df.groupby("charge_tier", observed=True)["churn_binary"].agg(Count="count", Rate="mean").loc[tier_order]

    tier_bars = ax2.bar(tier_summary.index, tier_summary["Rate"] * 100, color="#2563EB", width=0.55, edgecolor="black", linewidth=0.5)
    ax2.set_ylabel("Churn Rate (%)")
    ax2.set_title("Churn Rate by Monthly Billing Tier")
    ax2.set_xticks(range(len(tier_order)))
    ax2.set_xticklabels(tier_order, rotation=20, ha="right")
    ax2.set_ylim(0, 48)

    for bar, rate, count in zip(tier_bars, tier_summary["Rate"] * 100, tier_summary["Count"]):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.2, f"{rate:.1f}%\n(n={count:,})", ha="center", va="bottom", fontsize=8.5, weight="bold")

    plt.suptitle("Figure 4: Financial Exposure & Monthly Billing Burden vs. Churn", y=1.03)
    plt.tight_layout()
    output_path = output_dir / "04_monthly_charges_distribution.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved: {output_path.name}")

def plot_05_internet_and_tech_support(df: pd.DataFrame, output_dir: Path):
    """Figure 5: Churn Rate by Internet Service and Technical Support Add-on."""
    pivot = df.groupby(["InternetService", "TechSupport"])["churn_binary"].agg(Rate="mean", Count="count").reset_index()
    pivot["RatePct"] = pivot["Rate"] * 100

    fig, ax = plt.subplots(figsize=(10, 5.5))
    sns.barplot(
        data=pivot,
        x="InternetService",
        y="RatePct",
        hue="TechSupport",
        palette=["#EF4444", "#9CA3AF", "#10B981"],
        edgecolor="black",
        linewidth=0.5,
        ax=ax
    )

    ax.set_title("Figure 5: Churn Hazard by Internet Provider Architecture & Tech Support Status", pad=15)
    ax.set_xlabel("Internet Service Provider Technology")
    ax.set_ylabel("Churn Rate (%)")
    ax.set_ylim(0, 55)
    ax.legend(title="Tech Support Status", frameon=True)

    # Label bars
    for p in ax.patches:
        h = p.get_height()
        if not np.isnan(h) and h > 0:
            ax.annotate(f"{h:.1f}%", (p.get_x() + p.get_width() / 2., h),
                        ha="center", va="bottom", xytext=(0, 3), textcoords="offset points", fontsize=8.5, weight="bold")

    plt.tight_layout()
    output_path = output_dir / "05_churn_by_internet_techsupport.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved: {output_path.name}")

def plot_06_payment_method(df: pd.DataFrame, output_dir: Path):
    """Figure 6: Churn Rate and Customer Volume by Payment Method."""
    summary = df.groupby("PaymentMethod")["churn_binary"].agg(Count="count", Rate="mean", Churned="sum").reset_index()
    summary["RatePct"] = summary["Rate"] * 100
    summary = summary.sort_values(by="RatePct", ascending=False)

    fig, ax1 = plt.subplots(figsize=(11, 5))
    bars = ax1.barh(summary["PaymentMethod"], summary["RatePct"], color=["#DC2626", "#F59E0B", "#3B82F6", "#10B981"], edgecolor="black", linewidth=0.5)
    ax1.set_xlabel("Churn Rate (%)", weight="bold")
    ax1.set_title("Figure 6: Churn Propensity Across Billing & Payment Gateways", pad=15)
    ax1.set_xlim(0, 55)

    for bar, (_, row) in zip(bars, summary.iterrows()):
        w = bar.get_width()
        ax1.text(w + 1, bar.get_y() + bar.get_height()/2, f"{row['RatePct']:.1f}% (n={int(row['Count']):,} customers | {int(row['Churned']):,} churned)",
                 va="center", ha="left", fontsize=9.5, weight="bold")

    plt.tight_layout()
    output_path = output_dir / "06_churn_by_payment_method.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved: {output_path.name}")

def run_eda():
    project_root = get_project_root()
    output_dir = project_root / "reports" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading cleaned dataset...")
    df = load_data(project_root)

    logger.info("Generating Figure 1: Churn Distribution & Class Imbalance...")
    plot_01_churn_distribution(df, output_dir)

    logger.info("Generating Figure 2: Churn by Contract Type...")
    plot_02_churn_by_contract(df, output_dir)

    logger.info("Generating Figure 3: Tenure Distribution...")
    plot_03_tenure_distribution(df, output_dir)

    logger.info("Generating Figure 4: Monthly Charges Distribution...")
    plot_04_monthly_charges_distribution(df, output_dir)

    logger.info("Generating Figure 5: Internet Service & Tech Support...")
    plot_05_internet_and_tech_support(df, output_dir)

    logger.info("Generating Figure 6: Payment Method Churn...")
    plot_06_payment_method(df, output_dir)

    logger.info("All exploratory figures generated successfully in reports/figures/.")

if __name__ == "__main__":
    run_eda()
