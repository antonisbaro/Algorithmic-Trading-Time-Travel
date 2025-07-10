# main.py

import sys
import os
import argparse
import logging

# Set the recursion limit before importing other modules
# This is crucial for the deep recursive strategies.
sys.setrecursionlimit(10**6)

# Import all necessary modules from our 'src' library
from src import config
from src.data_preprocessor import load_and_preprocess_data
from src.trading_engine import run_small_scenario, run_large_scenario
from src.validator import validate_moves
from src.visualizer import plot_balance_history

# Configure basic logging for the main script execution
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    The main execution function of the Time-Travel Trading project.
    """
    # 1. --- Setup and Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Run the Time-Travel Trading simulation."
    )
    parser.add_argument(
        'scenario',
        type=str,
        choices=['small', 'large'],
        help="The trading scenario to execute ('small' or 'large')."
    )
    args = parser.parse_args()
    
    logging.info(f"Starting execution for '{args.scenario.capitalize()}' scenario.")
    
    # 2. --- Data Loading and Preprocessing ---
    # Ensure the results directory exists before we start.
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    
    combined_data, stock_dict = load_and_preprocess_data(config.DATA_DIR)

    # If data loading fails, exit gracefully.
    if combined_data.empty:
        logging.critical("Data preprocessing failed to produce data. Cannot continue.")
        sys.exit(1)
        
    # 3. --- Run Trading Scenario ---
    if args.scenario == 'small':
        final_cash, cash_per_year, moves = run_small_scenario(
            df=combined_data,
            initial_cash=config.INITIAL_CASH
        )
        moves_output_path = os.path.join(config.RESULTS_DIR, config.SMALL_MOVES_FILENAME)
        plot_output_path = os.path.join(config.RESULTS_DIR, config.SMALL_PLOT_FILENAME)
        
    elif args.scenario == 'large':
        final_cash, cash_per_year, moves = run_large_scenario(
            df=combined_data,
            initial_cash=config.INITIAL_CASH
        )
        moves_output_path = os.path.join(config.RESULTS_DIR, config.LARGE_MOVES_FILENAME)
        plot_output_path = os.path.join(config.RESULTS_DIR, config.LARGE_PLOT_FILENAME)

    # 4. --- Save Results and Visualize ---
    if not moves:
        logging.warning("The strategy produced no moves. No output files will be generated.")
    else:
        # Save the list of moves to a .txt file.
        try:
            with open(moves_output_path, "w") as f:
                f.write(str(len(moves)) + "\n")
                for move in moves:
                    f.write(" ".join(move) + "\n")
            logging.info(f"Successfully saved {len(moves)} moves to {moves_output_path}")
        except Exception as e:
            logging.error(f"Failed to save moves file: {e}")

        # Generate and save the balance history plot.
        plot_balance_history(cash_per_year, plot_output_path, args.scenario)

    # 5. --- Validate the Generated Moves ---
    validated_cash = validate_moves(
        initial_cash=config.INITIAL_CASH,
        moves=moves,
        stock_dict=stock_dict
    )

    # 6. --- Final Summary Report ---
    print("\n" + "="*50)
    print("           EXECUTION SUMMARY")
    print("="*50)
    print(f"Scenario Executed:      {args.scenario.capitalize()}")
    print(f"Total Moves Generated:  {len(moves)}")
    print(f"Final Cash (Strategy):  ${final_cash:,.2f}")
    print(f"Final Cash (Validator): ${validated_cash:,.2f}")
    print("-"*50)

    # Check if the validator's result matches the strategy's result.
    if validated_cash != -1 and abs(final_cash - validated_cash) < 0.01:
        print("VALIDATION STATUS: SUCCESS! The generated moves are valid.")
    else:
        print("VALIDATION STATUS: FAILURE! The moves are invalid or balances do not match.")
    
    print(f"\nOutput files saved in: '{config.RESULTS_DIR}'")
    print("="*50)


if __name__ == "__main__":
    main()