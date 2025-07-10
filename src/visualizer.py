# src/visualizer.py

import os
import matplotlib.pyplot as plt
from typing import Dict
import logging

def plot_balance_history(cash_per_year: Dict[int, float], output_path: str, scenario_name: str):
    """
    Generates and saves a plot of the account balance over the years.

    Args:
        cash_per_year (Dict[int, float]): A dictionary with years as keys and cash as values.
        output_path (str): The full path (including filename) to save the plot image.
        scenario_name (str): The name of the scenario (e.g., "Small", "Large") for the plot title.
    """
    if not cash_per_year:
        logging.warning("Cash history is empty. Skipping plot generation.")
        return

    years = list(cash_per_year.keys())
    balances = list(cash_per_year.values())

    plt.figure(figsize=(12, 7))
    plt.plot(years, balances, color='darkred', marker='o', linestyle='-', markersize=4)
    plt.fill_between(years, balances, color='darkred', alpha=0.3)

    # Set ticks for every 2 years for better readability.
    start_year = min(years) if years else 1962
    end_year = max(years) if years else 2018
    ticks = range(start_year, end_year + 1, 2)
    plt.xticks(ticks, rotation=45)

    # Use logarithmic scale for the y-axis to handle large growth.
    plt.yscale('log')
    plt.xlabel('Year')
    plt.ylabel('Balance (Log Scale)')
    plt.title(f'Balance Over Years - {scenario_name.capitalize()} Scenario')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()

    try:
        plt.savefig(output_path)
        logging.info(f"Successfully saved plot to {output_path}")
    except Exception as e:
        logging.error(f"Failed to save plot to {output_path}: {e}")
    
    plt.close() # Close the plot to free up memory.