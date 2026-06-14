"""Causal inference visual proofs: Difference-in-Differences and Cohort Divergence."""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def setup_directories():
    """Ensure the charts directory exists."""
    os.makedirs("charts", exist_ok=True)


def generate_causal_charts():
    """Process panel data and generate causal inference visualizations."""
    print("Generating Causal Inference Visualizations...")
    df = pd.read_csv("data/processed/master_panel_data.csv")
    
    df["elec_gen_fossil_twh"] = df.groupby("country_name")["elec_gen_fossil_twh"].transform(lambda x: x.ffill().bfill())
    
    df_2010 = df[df["year"] == 2010].copy()
    quantiles = df_2010["co2_per_capita"].quantile([0.33, 0.66])
    
    def assign_cohort(val):
        return "High Intensity (Dirty Grid)" if val > quantiles.iloc[1] else "Low/Medium Intensity (Cleaner Grid)"
        
    df_2010["cohort"] = df_2010["co2_per_capita"].apply(assign_cohort)
    cohort_map = df_2010.set_index("country_name")["cohort"].to_dict()
    df["cohort"] = df["country_name"].map(cohort_map)
    
    base_year_gen = df[df["year"] == 2010].set_index("country_name")["elec_gen_fossil_twh"]
    df["fossil_gen_2010_base"] = df["country_name"].map(base_year_gen)
    
    df["fossil_index"] = (df["elec_gen_fossil_twh"] / df["fossil_gen_2010_base"].replace(0, 1)) * 100
    
    viz_df = df[df["fossil_index"] < 300].copy()

    sns.set_theme(style="whitegrid")

    
    fig, ax1 = plt.subplots(figsize=(12, 7))
    
    yearly_cohort_avg = viz_df.groupby(["year", "cohort"])["fossil_index"].mean().reset_index()
    
    sns.lineplot(
        data=yearly_cohort_avg, 
        x="year", 
        y="fossil_index", 
        hue="cohort", 
        palette={"High Intensity (Dirty Grid)": "#d62728", "Low/Medium Intensity (Cleaner Grid)": "#2ca02c"},
        linewidth=3,
        ax=ax1
    )
    
    ax1.set_ylabel("Fossil Generation (Indexed: 2010 = 100)", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Year", fontsize=12, fontweight="bold")
    ax1.set_title("The Causal Impact: How Carbon Pricing Forced Dirty Grids to Transition", fontsize=16, fontweight="bold")
    
    ax2 = ax1.twinx()
    yearly_price = viz_df.groupby("year")["carbon_price_eur_tonne"].mean().reset_index()
    ax2.fill_between(yearly_price["year"], 0, yearly_price["carbon_price_eur_tonne"], color="gray", alpha=0.15)
    ax2.plot(yearly_price["year"], yearly_price["carbon_price_eur_tonne"], color="black", linestyle="--", alpha=0.5, label="EU ETS Carbon Price")
    
    ax2.set_ylabel("Carbon Price (€ / Tonne)", fontsize=12, color="gray")
    
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper right")
    
    plt.tight_layout()
    plt.savefig("charts/causal_timeline_divergence.png", dpi=300)
    plt.close()
    print("[OK] Causal Timeline saved to charts/causal_timeline_divergence.png")

    
    plt.figure(figsize=(11, 6))
    
    cohorts = {
        "High Intensity (Dirty Grid)": "#d62728",
        "Low/Medium Intensity (Cleaner Grid)": "#2ca02c"
    }
    
    for cohort_name, color_hex in cohorts.items():
        subset = viz_df[viz_df["cohort"] == cohort_name]
        sns.regplot(
            data=subset,
            x="carbon_price_eur_tonne",
            y="fossil_index",
            color=color_hex,
            scatter_kws={"alpha": 0.5},
            line_kws={"linewidth": 3},
            label=cohort_name,
            x_jitter=1.5  
        )
        
    plt.title("Fossil Fuel Response to Carbon Price Spikes (By Grid Type)", fontsize=14, fontweight="bold")
    plt.xlabel("EU ETS Carbon Price (€ / Tonne)", fontsize=12)
    plt.ylabel("Fossil Generation (Indexed to 2010 Baseline)", fontsize=12)
    
    plt.legend(title="Cohort", bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig("charts/causal_slope_interaction.png", dpi=300)
    plt.close()
    print("[OK] Causal Slope chart saved to charts/causal_slope_interaction.png")


if __name__ == "__main__":
    setup_directories()
    generate_causal_charts()