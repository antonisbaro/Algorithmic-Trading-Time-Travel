# src/data_preprocessor.py

import os
import pandas as pd
import logging
from typing import Tuple, Dict, List

from .config import (
    ZERO_VALUE_THRESHOLD,
    OUTLIER_STD_DEV_FACTOR,
    VOLUME_CONSTRAINT_FACTOR
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_and_preprocess_data(data_dir: str) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """
    Loads all stock data from .txt files, preprocesses, cleans, and combines them
    into a single sorted DataFrame.
    """
    all_data: List[pd.DataFrame] = []
    stock_dict: Dict[str, pd.DataFrame] = {}

    if not os.path.isdir(data_dir):
        logging.error(f"Data directory not found: {data_dir}")
        return pd.DataFrame(), {}

    logging.info(f"Starting data preprocessing from directory: {data_dir}")
    for file in os.listdir(data_dir):
        if file.endswith(".txt"):
            file_path = os.path.join(data_dir, file)
            stock_symbol = file.split('.')[0].upper()
            try:
                if os.stat(file_path).st_size == 0:
                    logging.warning(f"File {file} is empty. Skipping.")
                    continue

                df = pd.read_csv(file_path, sep=",")

                # *** FIX: Convert Date to datetime object early ***
                # This ensures both stock_dict and all_data get the correct data type.
                df['Date'] = pd.to_datetime(df['Date'])
                
                zero_values_ratio = ((df[['Low', 'High', 'Open', 'Close', 'Volume']] == 0).any(axis=1).mean())
                if zero_values_ratio > ZERO_VALUE_THRESHOLD:
                    logging.warning(f"Stock {file} has {zero_values_ratio*100:.2f}% days with zero values. Skipping.")
                    continue

                df = df[
                    (df['Low'] > 0) & (df['High'] > 0) & (df['Open'] > 0) &
                    (df['Close'] > 0) & (df['Volume'] > 0)
                ]
                if df.empty: continue

                logical_prices_mask = (df['Low'] <= df[['Open', 'Close', 'High']].min(axis=1)) & \
                                      (df['High'] >= df[['Open', 'Close', 'Low']].max(axis=1))
                
                num_illogical = len(df) - logical_prices_mask.sum()
                if num_illogical > 0:
                    logging.warning(f"Stock {stock_symbol}: Removing {num_illogical} rows with illogical prices.")
                    df = df[logical_prices_mask]

                if df.empty:
                    logging.warning(f"File {file} has no valid rows after filtering. Skipping.")
                    continue
                
                df['Max_Quantity'] = (VOLUME_CONSTRAINT_FACTOR * df['Volume']).astype(int)
                df['Range'] = df['High'] - df['Low']
                df['Stock'] = stock_symbol
                if "OpenInt" in df.columns:
                    df = df.drop(columns=["OpenInt"])

                all_data.append(df)
                stock_dict[stock_symbol] = df

            except pd.errors.EmptyDataError:
                logging.warning(f"File {file} contains no data. Skipping.")
            except Exception as e:
                logging.error(f"Error reading file {file}: {e}")

    processed_data = []
    for df in all_data:
        mean_range = df['Range'].mean()
        std_range = df['Range'].std()
        
        upper_threshold = mean_range + OUTLIER_STD_DEV_FACTOR * std_range
        lower_threshold = mean_range - OUTLIER_STD_DEV_FACTOR * std_range
        lower_threshold = max(0, lower_threshold)
        
        filtered_df = df[(df['Range'] >= lower_threshold) & (df['Range'] <= upper_threshold)]
        processed_data.append(filtered_df)

    if not processed_data:
        logging.critical("No valid data found after preprocessing. Exiting.")
        return pd.DataFrame(), {}

    combined_data = pd.concat(processed_data, ignore_index=True)
    logging.info(f"Successfully loaded and filtered data for {len(processed_data)} stocks.")

    # Sort the final combined DataFrame by date.
    combined_data.sort_values(by=["Date"], inplace=True, ignore_index=True)

    logging.info("Data preprocessing complete. Combined DataFrame is ready.")
    
    return combined_data, stock_dict

      