# Algorithmic Trading Strategy for a "Time-Travel" Scenario ⏳

This project tackles a unique algorithmic challenge: developing a profitable stock trading strategy given the ability to "time-travel" and trade on any day in the past. Starting with just $1 in 1960, the goal is to maximize the final profit by performing a series of buy/sell transactions on historical NYSE stock data, all while adhering to a complex set of constraints.

The project was developed for the "Programming Tools and Technologies for Data Science" course and is implemented entirely in **Python**, following best practices for code modularity and readability.

---

## 🚀 The Challenge: The "Time-Travel" Problem

The core of the problem is to devise a sequence of trades to maximize profit under these rules:
-   **Initial Capital**: Start with $1.
-   **Historical Data**: Access to daily `Open`, `High`, `Low`, `Close`, and `Volume` data for thousands of NYSE stocks over several decades.
-   **Transaction Types**: Ability to perform intra-day trades (`buy-open, sell-high` and `buy-low, sell-close`).
-   **Constraints**:
    -   1% transaction fee on every trade.
    -   Trades are only valid if sufficient cash or owned stock is available.
    -   Daily traded volume for any stock cannot exceed 10% of its total daily volume.
    -   A hard limit on the total number of transactions (e.g., 1,000 for "small" and 1,000,000 for "large" scenarios).

---

## 📂 Project Structure

The project is organized into a modular structure for clarity, maintainability, and ease of use.

-   `main.py`: The main entry point of the application. It uses `argparse` to handle command-line arguments for selecting the desired scenario (`small` or `large`).
-   `src/`: A directory containing the core logic of the project as a Python library.
    -   `config.py`: Centralized configuration for all parameters (e.g., file paths, commission rates, simulation constants).
    -   `data_preprocessor.py`: Handles loading, cleaning, filtering, and preparing the raw stock data.
    -   `strategies.py`: Contains the core recursive algorithms (`greedy_trading_recursive` and `extra_greedy_trading_recursive`).
    -   `trading_engine.py`: Implements the high-level logic that "wraps" the strategies, executing them on a year-by-year or month-by-month basis.
    -   `validator.py`: A crucial script that validates a generated sequence of moves against all problem constraints to ensure its correctness.
    -   `visualizer.py`: A utility for generating and saving plots of the portfolio balance over time.
-   `data/`: Directory where the historical stock data should be placed.
-   `results/`: Directory where the output files (move lists and plots) are saved.

---

## 🧠 Algorithmic Strategy & Evolution

Finding the globally optimal solution is computationally intractable. Instead, this project focuses on developing a sophisticated, heuristic-based greedy strategy.

### Step 1: Data Preprocessing
The first critical step was to clean and consolidate decades of raw `.txt` files into a single, usable `pandas` DataFrame using `data_preprocessor.py`. This involved:
-   Filtering out rows with invalid data (non-positive or illogical prices) instead of discarding entire files, maximizing data retention.
-   Filtering out entire stocks with a high percentage of zero-value days.
-   Detecting and removing outlier trading days based on a 3-sigma rule on the daily price range.

### Step 2: The Naive Greedy Algorithm
A simple recursive greedy algorithm (`greedy_trading_recursive`) was initially developed. At each step, it would find the single most profitable intra-day trade available across all stocks and all future dates, execute it, and then repeat the process. This logic forms the basis of the **Small Scenario**, which is executed on a year-by-year basis by `trading_engine.py` to encourage more transactions.

**Observation**: This base approach was "too greedy." It often picked a few trades with massive early gains, ignoring countless other smaller, profitable opportunities.

### Step 3: The Enhanced Greedy Algorithm with "Look-Back"
To overcome this, an enhanced recursive algorithm (`extra_greedy_trading_recursive`) was developed for the **Large Scenario**. This version introduced a "corrective look-back" mechanism:

1.  **Identify Best Move**: Just like before, the algorithm identifies the most profitable future trade.
2.  **Pause & Look Back**: Instead of executing it immediately, it *pauses* and **recursively calls itself on the historical data *before* the planned trade date**. This "corrective" recursive call operates with the capital that would be available *after* paying for the paused trade.
3.  **Exploit Past Opportunities**: This allows the algorithm to fill the historical gap with smaller, profitable trades that were previously ignored.
4.  **Dynamic Thresholds**: To avoid getting stuck on minuscule gains, dynamic parameters (`min_profit`) were introduced to prune unprofitable recursive paths, ensuring the 1,000,000 move limit is used efficiently.

The `trading_engine.py` runs this advanced strategy on a month-by-month basis to further distribute trades and maximize capital utilization.

---

## 📈 Results

-   **Small Scenario (max 1,000 moves)**: The final strategy executed **806 moves**, resulting in a final balance of over **$4.1 billion**.
-   **Large Scenario (max 1,000,000 moves)**: The final strategy executed **848,208 moves**, achieving a final balance of over **$232.8 billion**.

The `results` folder contains the generated transaction logs and valuation charts plotting the portfolio balance over time, showcasing the exponential growth achieved.

---

## 🚀 Getting Started & How to Run

### Prerequisites
-   Python 3.10+
-   Git

### Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Set up a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    # On Windows
    .venv\Scripts\activate
    # On macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Download the Data:**
    -   Download the dataset from Kaggle: [Price/Volume Data for all US Stocks & ETFs](https://www.kaggle.com/datasets/borismarjanovic/price-volume-data-for-all-us-stocks-etfs).
    -   Unzip the archive.
    -   Place the `Stocks` folder (containing all the `.txt` files) inside the `data` directory. The final structure should be `data/Stocks/a.us.txt`, etc.

### Execution

Run the simulation from the root directory of the project using the following commands:

-   **To run the Small scenario:**
    ```bash
    python main.py small
    ```

-   **To run the Large scenario:**
    ```bash
    python main.py large
    ```

The script will print progress to the console and save the output moves and plots in the `results/` directory.

---

## 💻 Technology Stack

-   **Language**: Python
-   **Core Libraries**: `Pandas`, `NumPy` for data manipulation and vectorized calculations.
-   `Matplotlib` for plotting the results.

---

## ✍️ Author

-   **Antonios Barotsakis**
