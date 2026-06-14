"""Exploratory business analytics: Pearson correlations, OLS regression, and visualizations for EU renewable energy investments."""

import os
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns

def setup_directories():
    """Ensure the charts and regression output directories exist."""
    os.makedirs("charts", exist_ok=True)
    os.makedirs("data/outputs/regressions", exist_ok=True)

def run_business_analytics():
    """Execute correlation analysis, OLS regression, and generate analytical charts."""
    df = pd.read_csv("data/processed/master_panel_data.csv")
    
    # Forward/Backward Fill Missing Economic Data
    cols_to_fill = ["net_imports_gwh", "elec_gen_fossil_twh", "elec_gen_clean_twh", "elec_gen_renewables_twh"]
    for col in cols_to_fill:
        if col in df.columns:
            df[col] = df.groupby("country_name")[col].transform(lambda x: x.ffill().bfill())
            global_mean = df[col].mean()
            df[col] = df[col].fillna(global_mean if pd.notna(global_mean) else 0)
            
    # DATA ENGINEERING PATCH: Derive missing capacity data from actual generation
    df["renewable_capacity_mw"] = df["elec_gen_renewables_twh"] * 456.62
    
    df = df.sort_values(["country_name", "year"])
    df["carbon_price_lag1"] = df.groupby("country_name")["carbon_price_eur_tonne"].shift(1)
    
    total_gen = df["elec_gen_clean_twh"] + df["elec_gen_fossil_twh"]
    total_gen = total_gen.replace(0, 1) 
    df["renewable_share"] = df["elec_gen_renewables_twh"] / total_gen
    
    analysis_df = df.dropna(subset=["carbon_price_lag1", "renewable_capacity_mw", "net_imports_gwh"])
    
    print("\n" + "="*50)
    print("PART 1: CORRELATION ANALYSIS")
    print("="*50)
    
    corr_a = analysis_df["renewable_capacity_mw"].corr(analysis_df["net_imports_gwh"])
    print(f"\n(a) Renewable Capacity vs. Net Imports: {corr_a:.3f}")
    
    corr_b = analysis_df["carbon_price_lag1"].corr(analysis_df["renewable_capacity_mw"])
    print(f"\n(b) Lagged Carbon Price vs. Renewable Capacity: {corr_b:.3f}")
    
    df_crisis = df[df["year"].isin([2021, 2022])].copy()
    crisis_agg = df_crisis.groupby("country_name").agg({
        "elec_price_eur_kwh": "std",
        "renewable_share": "mean"
    }).dropna()
    
    corr_c = crisis_agg["renewable_share"].corr(crisis_agg["elec_price_eur_kwh"])
    print(f"\n(c) Renewable Share vs. Price Volatility (2021-2022): {corr_c:.3f}")
    
    print("\n" + "="*50)
    print("PART 2: OLS REGRESSION")
    print("="*50)
    
    X = analysis_df["carbon_price_lag1"]
    X = sm.add_constant(X)
    y = analysis_df["renewable_capacity_mw"]
    
    model = sm.OLS(y, X).fit()
    print(model.summary())
    
    coef_mw = model.params['carbon_price_lag1']
    coef_gw = coef_mw / 1000
    
    interpretation_note = (
        f"\n--- Plain English Interpretation ---\n"
        f"A €1 increase in the EU ETS carbon price in year T is associated with a "
        f"{coef_gw:.3f} GW increase in renewable capacity investment in year T+1."
    )
    print(interpretation_note)
    
    output_path = "data/outputs/regressions/ols_regression_summary.txt"
    with open(output_path, "w") as f:
        f.write("Simple OLS Regression: Renewable Capacity vs Lagged Carbon Price\n")
        f.write("="*80 + "\n\n")
        f.write(model.summary().as_text())
        f.write("\n")
        f.write(interpretation_note)
        
    print(f"\n[OK] Regression summary successfully saved to {output_path}")

    print("\n" + "="*50)
    print("PART 3: GENERATING BUSINESS CHARTS")
    print("="*50)
    
    sns.set_theme(style="whitegrid")
    
    # Chart 1: OLS Scatter Trend (Lagged Carbon Price vs Renewable Capacity)
    plt.figure(figsize=(10, 6))
    sns.regplot(
        data=analysis_df, 
        x="carbon_price_lag1", 
        y="renewable_capacity_mw",
        scatter_kws={"alpha": 0.5, "color": "#1f77b4"},
        line_kws={"color": "#d62728", "linewidth": 2}
    )
    plt.title("Impact of Lagged Carbon Price on Renewable Capacity", fontsize=14, fontweight="bold")
    plt.xlabel("EU ETS Carbon Price (Lagged 1 Year) [€/Tonne]", fontsize=12)
    plt.ylabel("Renewable Capacity [MW]", fontsize=12)
    plt.tight_layout()
    plt.savefig("charts/ols_scatter_trend.png", dpi=300)
    plt.close()
    print("[OK] Trend scatter plot saved to charts/ols_scatter_trend.png")
    
    # Chart 2: Crisis Resilience (Renewable Share vs Price Volatility)
    plt.figure(figsize=(10, 6))
    sns.regplot(
        data=crisis_agg, 
        x="renewable_share", 
        y="elec_price_eur_kwh",
        scatter_kws={"alpha": 0.7, "color": "#2ca02c", "s": 80},
        line_kws={"color": "#17becf", "linewidth": 2}
    )
    plt.title("Grid Resilience (2021-2022): Renewable Share vs. Price Volatility", fontsize=14, fontweight="bold")
    plt.xlabel("Average Renewable Generation Share", fontsize=12)
    plt.ylabel("Electricity Price Volatility (Standard Deviation)", fontsize=12)
    plt.tight_layout()
    plt.savefig("charts/crisis_volatility_vs_renewables.png", dpi=300)
    plt.close()
    print("[OK] Crisis resilience chart saved to charts/crisis_volatility_vs_renewables.png")

if __name__ == "__main__":
    setup_directories()
    run_business_analytics()