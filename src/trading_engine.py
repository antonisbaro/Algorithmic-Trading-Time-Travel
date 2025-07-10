# src/trading_engine.py

import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, List

# Import the core strategies and configuration parameters
from .strategies import greedy_trading_recursive, extra_greedy_trading_recursive
from .config import dynamic_minimum_profit

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def run_small_scenario(df: pd.DataFrame, initial_cash: float) -> Tuple[float, Dict[int, float], List[Tuple]]:
    """
    Executes the 'small' scenario strategy by applying the simple greedy algorithm
    on a year-by-year basis. The cash compounds annually.

    Args:
        df (pd.DataFrame): The preprocessed and sorted DataFrame with all stock data.
        initial_cash (float): The starting capital.

    Returns:
        Tuple[float, Dict[int, float], List[Tuple]]: A tuple containing:
            - The final total cash.
            - A dictionary tracking the cash balance at the end of each year.
            - A list of all executed moves.
    """
    logging.info("Starting Small Scenario: Greedy trading by year.")
    df['Year'] = pd.to_datetime(df['Date']).dt.year
    years = sorted(df['Year'].unique())

    cash = initial_cash
    cash_per_year: Dict[int, float] = {}
    all_moves: List[Tuple] = []

    for year in years:
        logging.info(f"Processing year: {year} with available cash: ${cash:,.2f}")

        # Filter data for the specific year.
        yearly_data = df[df['Year'] == year].copy()

        # Apply the simple greedy strategy for the year.
        # Note: The original `moves` list from the previous year is not passed,
        # ensuring each year starts fresh, only carrying over the cash.
        cash, moves = greedy_trading_recursive(yearly_data, cash, moves=[])
        cash_per_year[year] = cash

        # Append the moves from this year to the master list.
        all_moves.extend(moves)
    
    logging.info(f"Small Scenario finished. Final cash: ${cash:,.2f}")
    return cash, cash_per_year, all_moves


def _dynamic_max_pairs(initial_max_pairs: float, current_year: int, last_year: int) -> float:
    """
    Helper function to calculate `max_past_pairs` dynamically based on the
    distance from the last year of data. The number of allowed corrective
    moves increases as we get closer to the present.

    Args:
        initial_max_pairs (float): The base number of corrective trades.
        current_year (int): The current year being processed.
        last_year (int): The final year in the dataset.

    Returns:
        float: A dynamically adjusted number of allowed past pairs.
    """
    if initial_max_pairs == np.inf:
        return np.inf

    remaining_years = last_year - current_year

    if remaining_years >= 40:
        return int(initial_max_pairs * (1 + 20000 / (remaining_years + 1)**2))
    else:
        return int(initial_max_pairs * (1 + 15000 / (remaining_years + 1)))


def run_large_scenario(df: pd.DataFrame, initial_cash: float, initial_max_past_pairs: float = np.inf) -> Tuple[float, Dict[int, float], List[Tuple]]:
    """
    Executes the 'large' scenario strategy by applying the extra greedy algorithm
    (with lookback) on a month-by-month basis.

    Args:
        df (pd.DataFrame): The preprocessed and sorted DataFrame with all stock data.
        initial_cash (float): The starting capital.
        initial_max_past_pairs (float): The base number for max corrective trades.

    Returns:
        Tuple[float, Dict[int, float], List[Tuple]]: A tuple containing:
            - The final total cash.
            - A dictionary tracking the cash balance at the end of each year.
            - A list of all executed moves.
    """
    logging.info("Starting Large Scenario: Extra greedy trading by month.")
    df['Year'] = pd.to_datetime(df['Date']).dt.year
    df['Month'] = pd.to_datetime(df['Date']).dt.month
    
    years = sorted(df['Year'].unique())
    max_year = max(years)
    months = sorted(df['Month'].unique())

    cash = initial_cash
    cash_per_year: Dict[int, float] = {}
    all_moves: List[Tuple] = []

    for year in years:
        logging.info(f"Processing year: {year} with available cash: ${cash:,.2f}")
        for month in months:
            # Filter data for the specific month and year.
            monthly_data = df[(df['Year'] == year) & (df['Month'] == month)].copy()
            if monthly_data.empty:
                continue
            
            # Get the dynamic parameters for the strategy call.
            max_past_pairs = _dynamic_max_pairs(initial_max_past_pairs, year, max_year)
            min_profit = dynamic_minimum_profit(cash)

            # Apply the extra greedy strategy for the month.
            cash, moves = extra_greedy_trading_recursive(
                df=monthly_data,
                cash=cash,
                moves=[],
                past=False,
                max_past_pairs=max_past_pairs,
                min_profit=min_profit
            )
            
            # Append the moves from this month to the master list.
            all_moves.extend(moves)
        
        # Record the cash at the end of the year.
        cash_per_year[year] = cash
    
    logging.info(f"Large Scenario finished. Final cash: ${cash:,.2f}")
    return cash, cash_per_year, all_moves