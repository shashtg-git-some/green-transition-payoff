"""Data cleaning, normalization, and panel dataset construction for EU27 countries."""

import os
import pandas as pd
import numpy as np


def setup_directories():
    """Ensure the processed data directory exists before writing output files."""
    os.makedirs("data/processed", exist_ok=True)


def get_eu27_mapping():
    """Return a standardized dictionary mapping ISO-2 country codes to full names."""
    return {
        "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "CY": "Cyprus",
        "CZ": "Czechia", "DE": "Germany", "DK": "Denmark", "EE": "Estonia",
        "EL": "Greece", "ES": "Spain", "FI": "Finland", "FR": "France",
        "HR": "Croatia", "HU": "Hungary", "IE": "Ireland", "IT": "Italy",
        "LT": "Lithuania", "LU": "Luxembourg", "LV": "Latvia", "MT": "Malta",
        "NL": "Netherlands", "PL": "Poland", "PT": "Portugal", "RO": "Romania",
        "SE": "Sweden", "SI": "Slovenia", "SK": "Slovakia"
    }


def clean_owid_emissions():
    """Extract and standardize EU27 CO2 emissions data from the Our World in Data dataset."""
    print("Cleaning OWID CO2 data...")
    df = pd.read_csv("data/raw/owid_co2_data.csv")
    
    df = df[(df["year"] >= 2010) & (df["year"] <= 2023)]
    
    eu_countries = list(get_eu27_mapping().values())
    df = df[df["country"].isin(eu_countries)]
    
    columns_to_keep = [
        "country", "year", "co2", "co2_per_capita", 
        "coal_co2", "gas_co2", "oil_co2", "gdp"
    ]
    df = df[columns_to_keep]
    
    df.rename(columns={"country": "country_name"}, inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    return df


def clean_eurostat_sdmx(file_name, value_col_name):
    """Parse and normalize Eurostat SDMX-CSV formats into an annual country-year panel."""
    print(f"Cleaning Eurostat file: {file_name}...")
    path = os.path.join("data/raw", file_name)
    df = pd.read_csv(path)
    
    eu_mapping = get_eu27_mapping()
    df = df[df["geo"].isin(eu_mapping.keys())]
    
    df["country_name"] = df["geo"].map(eu_mapping)
    df.rename(columns={"TIME_PERIOD": "year", "OBS_VALUE": value_col_name}, inplace=True)
    
    df["year"] = df["year"].astype(str).str[:4].astype(int)
    
    columns_to_keep = ["country_name", "year", value_col_name]
    df = df[columns_to_keep]
    
    df[value_col_name] = pd.to_numeric(df[value_col_name], errors="coerce")
    
    df = df.groupby(["country_name", "year"], as_index=False)[value_col_name].mean()
    
    df[value_col_name] = df.groupby("country_name")[value_col_name].transform(
        lambda x: x.interpolate(method="linear", limit_direction="both")
    )
    
    return df


def clean_ember_electricity():
    """Extract, filter, and pivot generation metrics from long to wide panel format."""
    print("Cleaning and pivoting Ember electricity mix data...")
    df = pd.read_csv("data/raw/ember_electricity_mix.csv")
    
    df.rename(columns={"Area": "country_name", "Year": "year"}, inplace=True)
    
    eu_countries = list(get_eu27_mapping().values())
    df = df[df["country_name"].isin(eu_countries)]
    df = df[(df["year"] >= 2010) & (df["year"] <= 2023)]
    
    df = df[df["Unit"] == "TWh"]
    
    pivot_df = df.pivot_table(
        index=["country_name", "year"],
        columns="Variable",
        values="Value",
        aggfunc="first"
    ).reset_index()
    
    rename_dict = {
        "Clean": "elec_gen_clean_twh",
        "Fossil": "elec_gen_fossil_twh",
        "Hydro": "elec_gen_hydro_twh",
        "Nuclear": "elec_gen_nuclear_twh",
        "Renewables": "elec_gen_renewables_twh",
        "Solar": "elec_gen_solar_twh",
        "Wind": "elec_gen_wind_twh",
        "Total Generation": "elec_gen_total_twh"
    }
    
    existing_columns = {k: v for k, v in rename_dict.items() if k in pivot_df.columns}
    pivot_df.rename(columns=existing_columns, inplace=True)
    
    columns_to_ensure = list(rename_dict.values())
    for col in columns_to_ensure:
        if col not in pivot_df.columns:
            pivot_df[col] = np.nan
            
    keep_cols = ["country_name", "year"] + columns_to_ensure
    return pivot_df[keep_cols]


def load_carbon_prices():
    """Load the pre-verified annual EU ETS carbon price dataset."""
    print("Loading verified carbon prices...")
    return pd.read_csv("data/raw/ember_carbon_prices.csv")


def construct_master_panel():
    """Merge all cleaned dataframes into a unified master panel dataset."""
    print("Constructing master panel dataset...")
    
    owid_df = clean_owid_emissions()
    capacity_df = clean_eurostat_sdmx("eurostat_renewable_capacity.csv", "renewable_capacity_mw")
    imports_df = clean_eurostat_sdmx("eurostat_imports.csv", "net_imports_gwh")
    prices_df = clean_eurostat_sdmx("eurostat_elec_prices.csv", "elec_price_eur_kwh")
    elec_mix_df = clean_ember_electricity()
    carbon_df = load_carbon_prices()
    
    master_df = pd.merge(owid_df, capacity_df, on=["country_name", "year"], how="left")
    master_df = pd.merge(master_df, imports_df, on=["country_name", "year"], how="left")
    master_df = pd.merge(master_df, prices_df, on=["country_name", "year"], how="left")
    master_df = pd.merge(master_df, elec_mix_df, on=["country_name", "year"], how="left")
    master_df = pd.merge(master_df, carbon_df, on=["year"], how="left")
    
    expected_rows = 27 * 14
    if len(master_df) != expected_rows:
        print(f"[WARNING] Row mismatch: Found {len(master_df)} rows instead of {expected_rows}.")
    else:
        print(f"[OK] Panel dimensions verified: Exactly {expected_rows} observations.")
        
    master_df.to_csv("data/processed/master_panel_data.csv", index=False)
    print("Success! Master panel dataset saved to data/processed/master_panel_data.csv")
    
    return master_df


def generate_data_quality_report(df):
    """Generate and save a statistical summary to validate the cleaning process."""
    print("Generating data quality and summary report...")
    
    summary_stats = df.describe().T
    summary_stats["missing_values"] = df.isnull().sum()
    summary_stats["completeness_pct"] = ((len(df) - summary_stats["missing_values"]) / len(df)) * 100
    
    summary_stats.to_csv("data/processed/data_quality_report.csv")
    print("Success! Quality report saved to data/processed/data_quality_report.csv")


if __name__ == "__main__":
    setup_directories()
    panel_df = construct_master_panel()
    generate_data_quality_report(panel_df)