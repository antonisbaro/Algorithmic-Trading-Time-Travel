# src/strategies.py

import pandas as pd
import numpy as np
from typing import Tuple, List, Optional

# Import constants from the config file for cleaner calculations.
from .config import BUY_COST_FACTOR, SELL_REVENUE_FACTOR


def greedy_trading_recursive(df: pd.DataFrame, cash: float, moves: Optional[List[Tuple]] = None) -> Tuple[float, List[Tuple]]:
    """
    Implements a simple, forward-looking greedy trading strategy.
    In each recursive step, it finds the single most profitable intra-day trade
    that can be afforded with the current cash and executes it.

    Args:
        df (pd.DataFrame): A DataFrame with historical stock data, sorted by date.
        cash (float): The current available capital.
        moves (Optional[List[Tuple]]): The list of trades executed so far.

    Returns:
        Tuple[float, List[Tuple]]: A tuple containing:
            - The final cash amount after all trades.
            - The complete list of executed moves.
    """
    if moves is None:
        moves = []

    df = df[(df['Open'] * BUY_COST_FACTOR <= cash) | (df['Low'] * BUY_COST_FACTOR <= cash)].reset_index(drop=True)

    # Base case for recursion: stop if no affordable data is left.
    if df.empty:
        return cash, moves

    # Vectorized profit calculation.
    quantity_open = np.minimum(df['Max_Quantity'], cash // (df['Open'] * BUY_COST_FACTOR))
    profit_open = quantity_open * (df['High'] * SELL_REVENUE_FACTOR - df['Open'] * BUY_COST_FACTOR)

    quantity_low = np.minimum(df['Max_Quantity'], cash // (df['Low'] * BUY_COST_FACTOR))
    profit_low = quantity_low * (df['Close'] * SELL_REVENUE_FACTOR - df['Low'] * BUY_COST_FACTOR)

    # Find the best move.
    max_profit_per_trade = np.maximum(profit_open, profit_low)
    best_profit_idx = np.argmax(max_profit_per_trade)
    best_profit = max_profit_per_trade[best_profit_idx]

    # If the max profit is not positive, stop.
    if best_profit <= 0:
        return cash, moves

    # Execute the best move.
    row = df.iloc[best_profit_idx]
    trade_date_str = str(row['Date'])[:10]
    stock_symbol = str(row['Stock'])

    if profit_open[best_profit_idx] > profit_low[best_profit_idx]:
        quantity = int(min(row['Max_Quantity'], cash / (row['Open'] * BUY_COST_FACTOR)))
        cost = quantity * row['Open'] * BUY_COST_FACTOR
        revenue = quantity * row['High'] * SELL_REVENUE_FACTOR
        cash = cash - cost + revenue
        moves.append((trade_date_str, 'buy-open', stock_symbol, str(quantity)))
        moves.append((trade_date_str, 'sell-high', stock_symbol, str(quantity)))
    else:
        quantity = int(min(row['Max_Quantity'], cash / (row['Low'] * BUY_COST_FACTOR)))
        cost = quantity * row['Low'] * BUY_COST_FACTOR
        revenue = quantity * row['Close'] * SELL_REVENUE_FACTOR
        cash = cash - cost + revenue
        moves.append((trade_date_str, 'buy-low', stock_symbol, str(quantity)))
        moves.append((trade_date_str, 'sell-close', stock_symbol, str(quantity)))

    # Update DataFrame (filter for subsequent days).
    df = df[df['Date'] > row['Date']]

    # Recursive call for the remaining days.
    return greedy_trading_recursive(df, cash, moves)


def extra_greedy_trading_recursive(df: pd.DataFrame, cash: float, moves: Optional[List[Tuple]] = None, 
                                     past: bool = False, max_past_pairs: float = np.inf, min_profit: float = -np.inf
                                    ) -> Tuple[float, List[Tuple]]:
    """
    Implements an advanced greedy strategy with a "lookback" mechanism,
    exactly preserving the user's original zig-zag recursive logic.

    Args:
        df (pd.DataFrame): DataFrame with historical stock data, sorted by date.
        cash (float): The current available capital.
        moves (Optional[List[Tuple]]): The list of trades executed so far.
        past (bool): Flag indicating if the function is in a "lookback" (corrective) call.
        max_past_pairs (float): Max number of trade pairs to execute in a corrective lookback.
        min_profit (float): Minimum profit required for a corrective trade to be executed.

    Returns:
        Tuple[float, List[Tuple]]: A tuple containing:
            - The final cash amount after all trades.
            - The complete list of executed moves.
    """
    if moves is None:
        moves = []

    # Limit the number of moves in the past.
    if past and (len(moves) // 2 >= max_past_pairs):
        return cash, moves
        
    df = df[(df['Open'] * BUY_COST_FACTOR <= cash) | (df['Low'] * BUY_COST_FACTOR <= cash)].reset_index(drop=True)
    
    # Base case for recursion: stop if no affordable data is left.
    if df.empty:
        return cash, moves

    # Vectorized profit calculation.
    quantity_open = np.minimum(df['Max_Quantity'], cash // (df['Open'] * BUY_COST_FACTOR))
    profit_open = quantity_open * (df['High'] * SELL_REVENUE_FACTOR - df['Open'] * BUY_COST_FACTOR)

    quantity_low = np.minimum(df['Max_Quantity'], cash // (df['Low'] * BUY_COST_FACTOR))
    profit_low = quantity_low * (df['Close'] * SELL_REVENUE_FACTOR - df['Low'] * BUY_COST_FACTOR)
    
    # Find the best move.
    max_profit_per_trade = np.maximum(profit_open, profit_low)
    best_profit_idx = np.argmax(max_profit_per_trade)
    best_profit = max_profit_per_trade[best_profit_idx]

    # If the max profit is not positive, stop.
    if best_profit <= 0:
        return cash, moves

    # The selected row.
    row = df.iloc[best_profit_idx]
    
    # Only in corrective calls (past=True), we want to guarantee that the correction is worthwhile based on the set min_profit.
    if (not past) or (best_profit >= min_profit):
        
        trade_date_str = str(row['Date'])[:10]
        stock_symbol = str(row['Stock'])

        # Execute the best move.
        if profit_open[best_profit_idx] > profit_low[best_profit_idx]:
            quantity = int(min(row['Max_Quantity'], cash / (row['Open'] * BUY_COST_FACTOR)))
            cost = quantity * row['Open'] * BUY_COST_FACTOR
            revenue = quantity * row['High'] * SELL_REVENUE_FACTOR
            
            # Recursively call the function for the past with available cash-cost.
            cash, in_between_moves = extra_greedy_trading_recursive(
                df=df[df['Date'] <= row['Date']].drop(index=best_profit_idx), 
                cash=cash-cost, 
                moves=[], 
                past=True, 
                max_past_pairs=max_past_pairs - 1, 
                min_profit=min_profit)
            
            cash = cash + revenue
            # The "past" moves are placed between the moves from the initial call and the move the algorithm just selected.
            moves = moves + in_between_moves
            moves.append((trade_date_str, 'buy-open', stock_symbol, str(quantity)))
            moves.append((trade_date_str, 'sell-high', stock_symbol, str(quantity)))
        else:
            quantity = int(min(row['Max_Quantity'], cash / (row['Low'] * BUY_COST_FACTOR)))
            cost = quantity * row['Low'] * BUY_COST_FACTOR
            revenue = quantity * row['Close'] * SELL_REVENUE_FACTOR

            # Recursively call the function for the past with available cash-cost.
            cash, in_between_moves = extra_greedy_trading_recursive(
                df=df[df['Date'] <= row['Date']].drop(index=best_profit_idx), 
                cash=cash-cost, 
                moves=[],
                past=True, 
                max_past_pairs=max_past_pairs - 1, 
                min_profit=min_profit)

            cash = cash + revenue
            # The "past" moves are placed between the moves from the initial call and the move the algorithm just selected.
            moves = moves + in_between_moves
            moves.append((trade_date_str, 'buy-low', stock_symbol, str(quantity)))
            moves.append((trade_date_str, 'sell-close', stock_symbol, str(quantity)))
    else:
        # If we are in a corrective call (past=True) and the check with min_profit fails, it is pointless to continue,
        # since the algorithm chose the best affordable move, therefore all others would also fail the min_profit check.
        return cash, moves

    # Update DataFrame (filter for subsequent days).
    # Using '>' and not '>=' is crucial to avoid violating the condition that we must have the funds for the day's
    # purchases available at the start of the day.
    df = df[df['Date'] > row['Date']]

    # Recursive call for the remaining days.
    if not past:
        return extra_greedy_trading_recursive(
            df=df, cash=cash, moves=moves, past=False, 
            max_past_pairs=max_past_pairs, min_profit=min_profit)
    else:
        # The number of moves for the limit is adjusted based on the moves made in the current corrective branch.
        return extra_greedy_trading_recursive(
            df=df, cash=cash, moves=moves, past=True, 
            max_past_pairs=(max_past_pairs - (len(moves) // 2)), min_profit=min_profit)