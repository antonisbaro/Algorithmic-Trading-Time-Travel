# src/validator.py

import pandas as pd
import datetime
from typing import List, Tuple, Dict
import logging

# Import constants from config
from .config import BUY_COST_FACTOR, SELL_REVENUE_FACTOR

def validate_moves(
    initial_cash: float,
    moves: List[Tuple[str, str, str, str]],
    stock_dict: Dict[str, pd.DataFrame]
) -> float:
    """
    Validates the compatibility of a given list of moves, preserving the
    original author's validation logic. This function checks if the move
    sequence is chronologically valid and financially possible.

    It does NOT sort the moves; it expects them to be in the correct order
    and will fail if they are not.

    Args:
        initial_cash (float): The starting cash amount.
        moves (List[Tuple[str, str, str, str]]): A list of move tuples (date, action, stock, quantity).
        stock_dict (Dict[str, pd.DataFrame]): A dictionary mapping stock symbols to their data.

    Returns:
        float: The final cash balance after all moves. Returns -1.0 if validation fails.
    """
    logging.info("Starting move validation...")
    
    current_date = None
    daily_cash = 0.0
    daily_revenue = 0.0

    # The moves list is iterated as-is to check for chronological errors.
    for move in moves:
        date_str, action, stock, quantity_str = move
        
        try:
            move_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            quantity = int(quantity_str)
        except ValueError:
            logging.error(f"Invalid data format in move: {move}. Validation failed.")
            return -1.0

        if current_date is None:
            # Set initial date and cash for the first move.
            current_date = move_date
            daily_cash = initial_cash
            daily_revenue = 0
        elif current_date < move_date:
            # On a new day, add the previous day's revenue to the cash balance.
            daily_cash += daily_revenue
            daily_revenue = 0
            current_date = move_date
        elif current_date > move_date:
            # CRITICAL CHECK: Fail if a move is out of chronological order.
            logging.error(f"Inconsistent move dates: {current_date} > {move_date}. Moves are not chronological.")
            return -1.0

        try:
            # Get the stock data for the specific day of the trade.
            df_stock = stock_dict[stock]
            # Convert the DataFrame's 'Date' column to date objects for comparison
            row = df_stock.loc[df_stock['Date'].dt.date == move_date]
            if row.empty:
                logging.error(f"No data found for stock {stock} on date {date_str}.")
                return -1.0
            row = row.iloc[0]
        except (KeyError, IndexError):
            logging.error(f"Could not retrieve data for move: {move}.")
            return -1.0
        
        # Check volume constraint
        if quantity > row['Max_Quantity']:
            logging.error(f"Volume constraint violated for move {move}. Trade Qty: {quantity}, Max Allowed: {row['Max_Quantity']}.")
            return -1.0

        # Process the trade
        if action == 'buy-low':
            cost = row["Low"] * BUY_COST_FACTOR * quantity
            if daily_cash < cost:
                logging.error(f"Insufficient cash for move {move}. Needed: ${cost:,.2f}, Available: ${daily_cash:,.2f}")
                return -1.0
            daily_cash -= cost
        elif action == 'buy-open':
            cost = row["Open"] * BUY_COST_FACTOR * quantity
            if daily_cash < cost:
                logging.error(f"Insufficient cash for move {move}. Needed: ${cost:,.2f}, Available: ${daily_cash:,.2f}")
                return -1.0
            daily_cash -= cost
        elif action == 'sell-close':
            revenue = row["Close"] * SELL_REVENUE_FACTOR * quantity
            daily_revenue += revenue
        elif action == 'sell-high':
            revenue = row["High"] * SELL_REVENUE_FACTOR * quantity
            daily_revenue += revenue
        else:
            logging.warning(f"Unsupported action '{action}' in move: {move}")

    final_balance = daily_cash + daily_revenue
    logging.info(f"Move validation complete. Final calculated balance: ${final_balance:,.2f}")
    return final_balance