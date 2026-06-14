"""Exploratory data analysis and econometric diagnostics for the EU27 panel."""

import os
import pandas as pd
import numpy as np


def setup_output_directories():
    """Create the output directory for analysis results if it does not exist."""
    os.makedirs("data/outputs", exist_ok=True)


def load_panel_data():
    """Load the cleaned master panel dataset from the processed data folder."""
    return pd.read_csv("data/processed/master_panel_data.csv")


def calculate_basic_descriptives(df):
    """Calculate and save summary statistics including skewness and kurtosis."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    descriptives = df[numeric_cols].describe().T
    descriptives["skewness"] = df[numeric_cols].skew()
    descriptives["kurtosis"] = df[numeric_cols].kurt()
    descriptives.to_csv("data/outputs/basic_descriptive_statistics.csv")
    return descriptives


def calculate_panel_decomposition(df, country_col, year_col):
    """Decompose panel variance into within-country and between-country components."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    numeric_cols = [c for c in numeric_cols if c != year_col]
    grand_means = df[numeric_cols].mean()
    total_sds = df[numeric_cols].std()
    country_means = df.groupby(country_col)[numeric_cols].mean()
    between_sds = country_means.std()
    within_df = df.copy()
    for col in numeric_cols:
        mapped_means = df[country_col].map(country_means[col])
        within_df[col] = df[col] - mapped_means + grand_means[col]
    within_sds = within_df[numeric_cols].std()
    decomposition_df = pd.DataFrame({
        "grand_mean": grand_means,
        "total_sd": total_sds,
        "between_sd": between_sds,
        "within_sd": within_sds
    })
    decomposition_df.to_csv("data/outputs/panel_variance_decomposition.csv")
    return decomposition_df


def calculate_correlation_matrix(df):
    """Compute and save the pairwise correlation matrix for all numeric features."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    corr_matrix = df[numeric_cols].corr()
    corr_matrix.to_csv("data/outputs/panel_correlation_matrix.csv")
    return corr_matrix


def calculate_growth_rates(df, country_col, year_col):
    """Calculate year-over-year percentage growth rates for all numeric variables."""
    sorted_df = df.sort_values(by=[country_col, year_col]).reset_index(drop=True)
    numeric_cols = sorted_df.select_dtypes(include=[np.number]).columns
    numeric_cols = [c for c in numeric_cols if c != year_col]
    growth_df = sorted_df[[country_col, year_col]].copy()
    for col in numeric_cols:
        growth_df[f"{col}_pct_change"] = sorted_df.groupby(country_col)[col].pct_change(fill_method=None) * 100
    growth_df.to_csv("data/outputs/panel_growth_rates.csv", index=False)
    return growth_df


def analyze_sigma_convergence(df, country_col, year_col):
    """Evaluate sigma-convergence of CO2 intensity across EU member states."""
    df_copy = df.copy()
    df_copy["co2_intensity_gdp"] = df_copy["co2"] / (df_copy["gdp"] / 1e9)
    cv_series = df_copy.groupby(year_col)["co2_intensity_gdp"].std() / df_copy.groupby(year_col)["co2_intensity_gdp"].mean()
    sd_log_series = df_copy.groupby(year_col).apply(lambda x: np.log(x["co2_intensity_gdp"]).std(), include_groups=False)
    convergence_df = pd.DataFrame({
        "coefficient_of_variation": cv_series,
        "sd_of_logs": sd_log_series
    })
    convergence_df.to_csv("data/outputs/sigma_convergence_metrics.csv")
    return convergence_df


def analyze_initial_intensity_cohorts(df, country_col, year_col):
    """Track emission and price trajectories based on 2010 intensity cohorts."""
    df_2010 = df[df[year_col] == 2010].copy()
    df_2010["initial_co2_per_capita"] = df_2010["co2_per_capita"]
    quantiles = df_2010["initial_co2_per_capita"].quantile([0.33, 0.66])
    def assign_cohort(val):
        if val <= quantiles.iloc[0]:
            return "Low Intensity"
        elif val <= quantiles.iloc[1]:
            return "Medium Intensity"
        return "High Intensity"
    df_2010["cohort"] = df_2010["initial_co2_per_capita"].apply(assign_cohort)
    cohort_map = df_2010.set_index(country_col)["cohort"].to_dict()
    df_cohorts = df.copy()
    df_cohorts["cohort"] = df_cohorts[country_col].map(cohort_map)
    cohort_summary = df_cohorts.groupby(["cohort", year_col])[["co2_per_capita", "elec_price_eur_kwh", "renewable_capacity_mw"]].mean().reset_index()
    cohort_summary.to_csv("data/outputs/cohort_trajectory_analysis.csv", index=False)
    return cohort_summary


def calculate_structural_generation_shifts(df, country_col, year_col):
    """Calculate the annual share of clean versus fossil generation in total electricity."""
    df_shifts = df.copy()
    
    # Mathematically derive total generation to bypass missing dataset columns
    clean_gen = df_shifts["elec_gen_clean_twh"].fillna(0)
    fossil_gen = df_shifts["elec_gen_fossil_twh"].fillna(0)
    total_gen = clean_gen + fossil_gen
    
    # Calculate the ratios using our derived total
    df_shifts["clean_generation_ratio"] = clean_gen / total_gen
    df_shifts["fossil_generation_ratio"] = fossil_gen / total_gen
    
    summary_shifts = df_shifts.groupby(year_col)[["clean_generation_ratio", "fossil_generation_ratio"]].mean()
    summary_shifts.to_csv("data/outputs/structural_generation_shifts.csv")
    return summary_shifts


if __name__ == "__main__":
    setup_output_directories()
    panel_df = load_panel_data()
    calculate_basic_descriptives(panel_df)
    calculate_panel_decomposition(panel_df, "country_name", "year")
    calculate_correlation_matrix(panel_df)
    calculate_growth_rates(panel_df, "country_name", "year")
    analyze_sigma_convergence(panel_df, "country_name", "year")
    analyze_initial_intensity_cohorts(panel_df, "country_name", "year")
    calculate_structural_generation_shifts(panel_df, "country_name", "year")
    print("Success! All extended exploratory analysis modules executed smoothly.")