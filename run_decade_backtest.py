import pandas as pd
from colorama import Fore, Style, init
from backtest_engine import BacktestEngine

# Strategies
from strategies.grid_strategy import GridStrategy
from strategies.mean_reversion_strategy import MeanReversionStrategy
from strategies.trend_strategy import TrendStrategy
from strategies.dca_strategy import DCAStrategy
from strategies.advanced_strategies import BumTrendStrategy, MatrDipStrategy, GuaMomentumStrategy, MgbBandStrategy

init(autoreset=True)

# TURKEY INFLATION DATA (Annual CPI / TÜFE)
# Approximate Year-End or Average Annual Inflation
TURKEY_INFLATION = {
    2015: 8.81,
    2016: 8.53,
    2017: 11.92,
    2018: 20.30,
    2019: 11.84,
    2020: 14.60,
    2021: 36.08,
    2022: 64.27,
    2023: 64.77,
    2024: 70.00, # Estimate/High 
    2025: 45.00  # Projection
}

def get_fresh_strategies():
    # Helper to reset state every year
    tickers = ["AKBNK.IS", "THYAO.IS", "BIMAS.IS", "ASELS.IS", "KCHOL.IS"] # Classic BIST 30 mix
    
    # We use fewer tickers for speed in 10-year test, but representative ones.
    # Capital: 1000 TL start per year
    START_CAP = 1000.0
    
    return [
        TrendStrategy(name="TrendHunter", balance=START_CAP, tickers=tickers),
        MeanReversionStrategy(name="MeanRev", balance=START_CAP, tickers=tickers),
        BumTrendStrategy(name="BUM_Trend", balance=START_CAP, tickers=tickers),
        # GridBot usually fails high volatility long term, assume we test it too
        GridStrategy(name="GridBot", balance=START_CAP, tickers=tickers),
        DCAStrategy(name="SmartDCA", balance=START_CAP, tickers=tickers), # Benchmark
        GuaMomentumStrategy(name="RUA_Mom", balance=START_CAP, tickers=tickers)
    ]

def run_decade():
    print(Fore.YELLOW + "--- STARTING 10-YEAR HISTORICAL BACKTEST (INFLATION ADJUSTED) ---")
    print("-" * 80)
    print(f"{'YEAR':<6} | {'INFLATION':<10} | {'BEST STRATEGY':<15} | {'NOMINAL ROI':<12} | {'REAL ROI (Net)':<15}")
    print("-" * 80)
    
    overall_records = []
    
    for year in range(2015, 2026):
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        inflation = TURKEY_INFLATION.get(year, 0)
        
        strats = get_fresh_strategies()
        engine = BacktestEngine(start_date, end_date, strats)
        
        results = engine.run()
        
        if not results:
            print(f"{year:<6} | {inflation:<9.1f}% | {'NO DATA':<15} | {'0.0%':<12} | {'0.0%':<15}")
            continue

        # Find Winner
        best_strat = None
        best_roi = -9999
        
        for name, res in results.items():
            roi = res['roi']
            if roi > best_roi:
                best_roi = roi
                best_strat = name
        
        # Calculate Real ROI
        # Formula: (1 + Nominal) / (1 + Inflation) - 1
        nominal_multiplier = 1 + (best_roi / 100.0)
        inflation_multiplier = 1 + (inflation / 100.0)
        real_roi = ((nominal_multiplier / inflation_multiplier) - 1) * 100.0
        
        print(f"{year:<6} | {inflation:<9.1f}% | {best_strat:<15} | {best_roi:<11.1f}% | {real_roi:<14.1f}%")
        
        overall_records.append({
            "year": year,
            "inflation": inflation,
            "winner": best_strat,
            "nominal": best_roi,
            "real": real_roi,
            "all_results": results
        })

    print("-" * 80)
    print(Fore.CYAN + "DONE. Analyzing consistency...")
    
    # Simple consistency check
    winners = [r['winner'] for r in overall_records]
    from collections import Counter
    counts = Counter(winners)
    print("\nMost Frequent Winners:")
    for s, c in counts.items():
        print(f"{s}: {c} years")

if __name__ == "__main__":
    run_decade()
