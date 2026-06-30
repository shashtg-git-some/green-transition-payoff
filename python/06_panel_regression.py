"""Econometric panel regression models for the EU27 energy transition."""

import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
from linearmodels.panel import PanelOLS, PooledOLS, compare


def setup_regression_directories():
    """Create the output directory for regression results."""
    os.makedirs("data/outputs/regressions", exist_ok=True)


def load_and_prepare_panel():
    """Load the master dataset, securely handle all missing/negative values, and build MultiIndex."""
    df = pd.read_csv("data/processed/master_panel_data.csv")
    
    cols_to_fill = [
        "gdp", "renewable_capacity_mw", "elec_price_eur_kwh", 
        "net_imports_gwh", "elec_gen_fossil_twh", "elec_gen_clean_twh"
    ]
    
    for col in cols_to_fill:
        df[col] = df.groupby("country_name")[col].transform(lambda x: x.ffill().bfill())
        
        global_mean = df[col].mean()
        df[col] = df[col].fillna(global_mean if pd.notna(global_mean) else 0)
        
    df["ln_gdp"] = np.log(df["gdp"].clip(lower=1))
    df["ln_renewable_capacity"] = np.log(df["renewable_capacity_mw"].clip(lower=0) + 1)
    
    df_2010 = df[df["year"] == 2010].copy()
    quantiles = df_2010["co2_per_capita"].quantile([0.33, 0.66])
    
    def assign_high_intensity(val):
        return 1 if val > quantiles.iloc[1] else 0
        
    df_2010["is_high_intensity_2010"] = df_2010["co2_per_capita"].apply(assign_high_intensity)
    cohort_map = df_2010.set_index("country_name")["is_high_intensity_2010"].to_dict()
    df["is_high_intensity_2010"] = df["country_name"].map(cohort_map)
    
    df["carbon_price_x_high_intensity"] = df["carbon_price_eur_tonne"] * df["is_high_intensity_2010"]
    
    df = df.set_index(["country_name", "year"])
    
    return df


def run_pooled_ols_baseline(df):
    """Execute a baseline Pooled OLS regression for comparison."""
    print("Running Baseline Model: Pooled OLS...")
    dependent = df["elec_gen_fossil_twh"]
    exog_vars = [
        "carbon_price_eur_tonne", "ln_gdp", 
        "elec_price_eur_kwh", "net_imports_gwh"
    ]
    
    exog = sm.add_constant(df[exog_vars])
    model = PooledOLS(dependent, exog)
    
    return model.fit(cov_type="clustered", cluster_entity=True)


def run_fossil_entity_effects(df):
    """Execute an Entity Fixed Effects regression on fossil fuel generation."""
    print("Running Entity FE Model: Fossil Generation...")
    dependent = df["elec_gen_fossil_twh"]
    exog_vars = [
        "carbon_price_eur_tonne", "ln_gdp", 
        "elec_price_eur_kwh", "net_imports_gwh"
    ]
    
    exog = sm.add_constant(df[exog_vars])
    model = PanelOLS(dependent, exog, entity_effects=True, time_effects=False)
    
    return model.fit(cov_type="clustered", cluster_entity=True)


def run_clean_entity_effects(df):
    """Execute an Entity Fixed Effects regression on clean energy generation."""
    print("Running Entity FE Model: Clean Generation...")
    dependent = df["elec_gen_clean_twh"]
    exog_vars = [
        "carbon_price_eur_tonne", "ln_gdp", 
        "elec_price_eur_kwh", "net_imports_gwh"
    ]
    
    exog = sm.add_constant(df[exog_vars])
    model = PanelOLS(dependent, exog, entity_effects=True, time_effects=False)
    
    return model.fit(cov_type="clustered", cluster_entity=True)


def run_heterogeneous_twfe(df):
    """Execute a Two-Way Fixed Effects regression to isolate cohort interaction effects."""
    print("Running TWFE Model: Heterogeneous Cohort Effects...")
    dependent = df["elec_gen_fossil_twh"]
    exog_vars = [
        "carbon_price_x_high_intensity", "ln_gdp", 
        "elec_price_eur_kwh", "net_imports_gwh"
    ]
    
    exog = sm.add_constant(df[exog_vars])
    model = PanelOLS(dependent, exog, entity_effects=True, time_effects=True)
    
    return model.fit(cov_type="clustered", cluster_entity=True)


def export_regression_tables(pooled, fossil_fe, clean_fe, hetero_twfe):
    """Format and export all regression summaries to a unified text table."""
    print("Exporting regression summaries...")
    
    comparison = compare({
        "Pooled Baseline": pooled,
        "Fossil FE": fossil_fe,
        "Clean FE": clean_fe,
        "Hetero TWFE": hetero_twfe
    })
    
    output_path = "data/outputs/regressions/master_regression_results.txt"
    with open(output_path, "w") as f:
        f.write("EU27 Energy Transition: Panel Regression Results\n")
        f.write("="*80 + "\n\n")
        f.write(comparison.summary.as_text())
        
    print(f"Success! Regression results saved to {output_path}")


if __name__ == "__main__":
    setup_regression_directories()
    panel_data = load_and_prepare_panel()
    
    model_pooled = run_pooled_ols_baseline(panel_data)
    model_fossil = run_fossil_entity_effects(panel_data)
    model_clean = run_clean_entity_effects(panel_data)
    model_hetero = run_heterogeneous_twfe(panel_data)
    
    export_regression_tables(model_pooled, model_fossil, model_clean, model_hetero)