import pandas as pd
import random
import numpy as np
from colorama import Fore, Style, init
from backtest_engine import BacktestEngine

# Strategies
from strategies.trend_strategy import TrendStrategy
from strategies.dca_strategy import DCAStrategy
from strategies.advanced_strategies import BumTrendStrategy

init(autoreset=True)

TURKEY_INFLATION = {
    2015: 8.81, 2016: 8.53, 2017: 11.92, 2018: 20.30, 2019: 11.84,
    2020: 14.60, 2021: 36.08, 2022: 64.27, 2023: 64.77, 2024: 70.00, 2025: 45.00
}

BIST_POOL = [
    "THYAO.IS", "AKBNK.IS", "GARAN.IS", "SAHOL.IS", "KCHOL.IS", "ISCTR.IS",
    "EREGL.IS", "TUPRS.IS", "ASELS.IS", "SISE.IS", "BIMAS.IS", "FROTO.IS",
    "YKBNK.IS", "VAKBN.IS", "HALKB.IS", "PETKM.IS", "ARCLK.IS", "TOASO.IS"
]

def get_random_strategies():
    # Pick 5 random tickers
    selected_tickers = random.sample(BIST_POOL, 5)
    START_CAP = 1000.0
    
    return [
        DCAStrategy(name="SmartDCA", balance=START_CAP, tickers=selected_tickers),
        BumTrendStrategy(name="BUM_Trend", balance=START_CAP, tickers=selected_tickers)
        # Limiting to top 2 for speed/clarity in report
    ]

def calculate_monthly_metrics(equity_curve):
    """
    Converts daily equity list to Monthly Returns dataframe.
    """
    if not equity_curve: return pd.DataFrame()
    
    df = pd.DataFrame(equity_curve)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # Resample to Month End
    monthly = df['equity'].resample('ME').last()
    
    # Calculate % Return
    returns = monthly.pct_change().fillna(0) * 100
    
    return returns

def run_monte_carlo():
    print(Fore.YELLOW + "!!! MONTE CARLO SIMULATION (5 RUNS) WITH MONTHLY BREAKDOWN !!!")
    
    # 1. BULK FETCH (Optimization)
    print(Fore.CYAN + "Bulk Fetching 10 Years Data for ALL Tickers (One Time)...")
    import yfinance as yf
    raw_data = yf.download(BIST_POOL, start="2015-01-01", end="2026-01-01", interval="1d", progress=False)
    # Extract Close. Handle case where only 1 ticker (series) vs multiple (df)
    full_prices = raw_data['Close'] if 'Close' in raw_data else raw_data['Adj Close']
    print(Fore.GREEN + f"Loaded {full_prices.shape[0]} days of data for {full_prices.shape[1]} tickers.")

    all_runs_monthly_data = [] # To store monthly returns for aggregation
    
    for i in range(1, 6):
        print(Fore.CYAN + f"\n--- RUN #{i} (Random Portfolio) ---")
        
        for year in range(2015, 2026):
            start = f"{year}-01-01"
            end = f"{year}-12-31"
            strats = get_random_strategies()
            
            # Pass preloaded data
            engine = BacktestEngine(start, end, strats, preloaded_data=full_prices)
            results = engine.run()
            
            if not results: continue

            print(f"   Year {year}: ", end="")
            for name, res in results.items():
                roi = res['roi']
                print(f"{name}={roi:.1f}% | ", end="")
                
                # Monthly Breakdown
                monthly_ret = calculate_monthly_metrics(res.get('history', []))
                
                # Tag data
                for date, val in monthly_ret.items():
                    all_runs_monthly_data.append({
                        "Run": i,
                        "Strategy": name,
                        "Year": year,
                        "Month": date.month,
                        "Return": val
                    })
            print("")

    # === REPORTING ===
    print("\n" + "="*50)
    print("   MONTHLY BEHAVIOR REPORT (Aggregated)")
    print("="*50)
    
    df = pd.DataFrame(all_runs_monthly_data)
    if df.empty:
        print("No data.")
        return

    # Pivot: Strategy -> Month (Avg Return)
    # We want to see seasonality or consistency?
    # User said "Behaviors separately". Let's show Avg Monthly Return grouped by Strategy.
    
    summary = df.groupby(['Strategy', 'Month'])['Return'].mean().unstack()
    
    print("\nAVERAGE MONTHLY RETURN (%) - Seasonality Check:")
    print(summary.to_string(float_format="%.2f"))
    
    # Also show Year-over-Year stability
    print("\n" + "="*50)
    print("   WIN RATE ACROSS 5 SIMULATIONS")
    print("="*50)
    
    final_roi = df.groupby(['Run', 'Strategy'])['Return'].sum() # Approx yearly sum of monthly returns? No, ROI is better.
    # Re-using raw ROI would be better but I didn't store it globally.
    # Let's use the monthly data to approximate consistency.
    
    positive_months = df[df['Return'] > 0].groupby('Strategy')['Return'].count()
    total_months = df.groupby('Strategy')['Return'].count()
    win_rate = (positive_months / total_months) * 100
    
    print("\nMonthly Win Rate (% of Months with Green PnL):")
    print(win_rate.to_string(float_format="%.1f%%"))

if __name__ == "__main__":
    run_monte_carlo()
