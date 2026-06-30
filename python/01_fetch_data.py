"""Data ingestion script for downloading and verifying project raw data files."""

import os
import requests
import pandas as pd


def download_owid_data():
    """Download the comprehensive historical CO2 dataset from Our World in Data."""
    url = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
    output_path = "data/raw/owid_co2_data.csv"
    
    if os.path.exists(output_path):
        print("Our World in Data CO2 dataset already exists. Skipping download.")
        return
        
    print("Downloading Our World in Data CO2 dataset...")
    response = requests.get(url)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)
    print(f"Success! Saved to {output_path}")


def generate_carbon_prices():
    """Hardcoded annual EU ETS carbon prices (manually compiled from public EU ETS records)."""
    output_path = "data/raw/ember_carbon_prices.csv"
    print("Generating verified annual EU ETS Carbon Prices...")

    data = {
        "year": list(range(2010, 2024)),
        "carbon_price_eur_tonne": [
            14.38, 13.07, 7.33, 4.45, 5.96, 7.68, 5.35, 5.83, 15.88, 24.84, 24.75, 53.55, 80.87, 85.30
        ]
    }
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Success! Saved to {output_path}")


def check_manual_files():
    """Verify that all required manual Eurostat and Ember data files exist."""
    required_files = [
        "eurostat_renewable_capacity.csv",
        "eurostat_imports.csv",
        "eurostat_elec_prices.csv",
        "ember_electricity_mix.csv",
    ]

    all_present = True
    print("\nChecking for manual downloads in data/raw/...")

    for file in required_files:
        path = os.path.join("data/raw", file)
        if os.path.exists(path):
            print(f"[OK] Found {file}")
        else:
            print(f"[MISSING] {file} is not in data/raw/")
            all_present = False

    if all_present:
        print("\nAll raw data files are present and accounted for!")
    else:
        print(
            "\nPlease download the missing files manually before proceeding to Phase 3."
        )


if __name__ == "__main__":
    download_owid_data()
    generate_carbon_prices()
    check_manual_files()