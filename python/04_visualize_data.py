"""Generate publication-ready econometrics visualizations from diagnostic data."""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def setup_chart_directories():
    """Ensure the charts directory exists before saving images."""
    os.makedirs("charts", exist_ok=True)


def plot_sigma_convergence():
    """Plot the coefficient of variation to visualize sigma-convergence."""
    print("Generating Sigma-Convergence plot...")
    df = pd.read_csv("data/outputs/sigma_convergence_metrics.csv")
    plt.figure(figsize=(10, 6))
    sns.lineplot(
        data=df, x="year", y="coefficient_of_variation", 
        marker="o", color="#2ca02c", linewidth=2
    )
    plt.title("Sigma-Convergence of CO2 Intensity in the EU27 (2010-2023)")
    plt.ylabel("Coefficient of Variation")
    plt.xlabel("Year")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig("charts/sigma_convergence.png", dpi=300)
    plt.close()


def plot_structural_shifts():
    """Plot the EU-wide shift from fossil to clean electricity generation."""
    print("Generating Structural Shifts plot...")
    df = pd.read_csv("data/outputs/structural_generation_shifts.csv")
    plt.figure(figsize=(10, 6))
    plt.plot(
        df["year"], df["clean_generation_ratio"] * 100, 
        label="Clean Energy Share (%)", color="#1f77b4", marker="s", linewidth=2
    )
    plt.plot(
        df["year"], df["fossil_generation_ratio"] * 100, 
        label="Fossil Energy Share (%)", color="#d62728", marker="X", linewidth=2
    )
    plt.title("Structural Shift in EU Electricity Generation")
    plt.ylabel("Percentage of Total Generation")
    plt.xlabel("Year")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig("charts/structural_shifts.png", dpi=300)
    plt.close()


def plot_cohort_trajectories():
    """Plot CO2 per capita trajectories by initial 2010 intensity cohorts."""
    print("Generating Cohort Trajectories plot...")
    df = pd.read_csv("data/outputs/cohort_trajectory_analysis.csv")
    plt.figure(figsize=(10, 6))
    sns.lineplot(
        data=df, x="year", y="co2_per_capita", 
        hue="cohort", marker="o", linewidth=2
    )
    plt.title("Emissions Trajectories by 2010 Initial Intensity Cohort")
    plt.ylabel("CO2 per Capita (Tonnes)")
    plt.xlabel("Year")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend(title="Initial 2010 Cohort")
    plt.tight_layout()
    plt.savefig("charts/cohort_trajectories.png", dpi=300)
    plt.close()


if __name__ == "__main__":
    setup_chart_directories()
    plot_sigma_convergence()
    plot_structural_shifts()
    plot_cohort_trajectories()
    print("Success! High-resolution charts saved to the 'charts/' directory.")