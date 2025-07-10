# src/config.py

import os
import numpy as np

# --- Project Structure Paths ---
# Establishes the root directory of the project to build robust paths.
# __file__ is the path to this config.py file.
# os.path.dirname(__file__) is the 'src' directory.
# os.path.dirname(os.path.dirname(__file__)) is the project root.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to the directory containing the stock data .txt files.
DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'Stocks')

# Path to the directory where results (move files, plots) will be saved.
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')


# --- Data Preprocessing Parameters ---

# The threshold for the proportion of days with zero values in a stock's history.
# If a stock exceeds this, it's considered unreliable and is skipped.
ZERO_VALUE_THRESHOLD = 0.1

# The number of standard deviations to use for the 3-sigma rule in outlier detection.
# This is applied to the daily price range (High - Low).
OUTLIER_STD_DEV_FACTOR = 3


# --- Trading Simulation Parameters ---

# The initial capital available for trading.
INITIAL_CASH = 1.0

# The commission rate for each transaction (buy or sell).
COMMISSION_RATE = 0.01

# Multipliers derived from the commission rate for cleaner calculations.
BUY_COST_FACTOR = 1 + COMMISSION_RATE
SELL_REVENUE_FACTOR = 1 - COMMISSION_RATE

# The constraint on trading volume. Trades cannot exceed this fraction of the daily volume.
VOLUME_CONSTRAINT_FACTOR = 0.1

# Python's recursion limit. Increased to handle deep recursive calls in the strategies.
# This should be set at the start of the main script.
RECURSION_LIMIT = 10**6


# --- Output File Parameters ---

# Filenames for the output move lists for both scenarios.
SMALL_MOVES_FILENAME = "small_moves.txt"
LARGE_MOVES_FILENAME = "large_moves.txt"

# Filenames for the output balance history plots.
SMALL_PLOT_FILENAME = "balance_small.png"
LARGE_PLOT_FILENAME = "balance_large.png"


# --- Large Scenario Dynamic Parameters ---
# These parameters control the behavior of the 'extra_greedy' strategy,
# specifically for the large scenario, to manage the number of moves effectively.

def dynamic_minimum_profit(cash: float) -> float:
    """
    Calculates the minimum required profit for a "corrective" past trade
    based on the current available cash. This prevents wasting moves on
    trades with negligible profit.

    Args:
        cash (float): The current available capital.

    Returns:
        float: The minimum profit threshold.
    """
    if cash < 1e3:
        # For very low cash, allow any positive profit.
        return -np.inf
    elif cash <= 1e7:
        # Require a profit of at least 1% of the cash.
        return cash / 100
    else:
        # For very high cash, set a fixed high threshold.
        return 1e5