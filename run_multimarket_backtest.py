import pandas as pd
import yfinance as yf
from colorama import Fore, Style, init
from backtest_engine import BacktestEngine

# Strategies
from strategies.trend_strategy import TrendStrategy
from strategies.dca_strategy import DCAStrategy
from strategies.advanced_strategies import BumTrendStrategy, MatrDipStrategy, GuaMomentumStrategy

init(autoreset=True)

# --- CONFIGURATION ---

# 1. Inflation Data (Approx Annual)
INFLATION_TR = {
    2015: 8.81, 2016: 8.53, 2017: 11.92, 2018: 20.30, 2019: 11.84,
    2020: 14.60, 2021: 36.08, 2022: 64.27, 2023: 64.77, 2024: 70.00, 2025: 45.00
}

INFLATION_US = {
    2015: 0.12, 2016: 1.26, 2017: 2.13, 2018: 2.44, 2019: 1.81,
    2020: 1.23, 2021: 4.70, 2022: 8.00, 2023: 4.10, 2024: 3.10, 2025: 2.50
}

# 2. Ticker Pools
POOLS = {
    "BIST (Istanbul)": {
        "currency": "TRY",
        "inflation": INFLATION_TR,
        "tickers": ["THYAO.IS", "AKBNK.IS", "GARAN.IS", "SAHOL.IS", "KCHOL.IS", "ASELS.IS", "BIMAS.IS", "FROTO.IS", "TUPRS.IS"]
    },
    "GLOBAL (US Tech/Bluechip)": {
        "currency": "USD",
        "inflation": INFLATION_US,
        "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "BRK-B", "JPM", "V"]
    },
    "CHIPS (Semiconductors)": {
        "currency": "USD",
        "inflation": INFLATION_US,
        "tickers": ["NVDA", "AMD", "INTC", "TSM", "AVGO", "MU", "QCOM", "TXN", "LRCX"]
    }
}

def get_strategies(tickers, balance=1000.0):
    return [
        DCAStrategy(name="SmartDCA", balance=balance, tickers=tickers),
        BumTrendStrategy(name="BUM_Trend", balance=balance, tickers=tickers),
        TrendStrategy(name="TrendHunter", balance=balance, tickers=tickers),
        GuaMomentumStrategy(name="RUA_Mom", balance=balance, tickers=tickers)
    ]

def fetch_all_data():
    all_tickers = []
    for p in POOLS.values():
        all_tickers.extend(p['tickers'])
    all_tickers = list(set(all_tickers))
    
    print(Fore.CYAN + f"Bulk Fetching Data for {len(all_tickers)} Tickers (2015-2025)...")
    raw = yf.download(all_tickers, start="2015-01-01", end="2026-01-01", interval="1d", progress=False)
    prices = raw['Close'] if 'Close' in raw else raw['Adj Close']
    print(Fore.GREEN + f"Loaded {prices.shape[0]} rows.")
    return prices

def run_multimarket_test():
    prices_df = fetch_all_data()
    
    print(Fore.YELLOW + "\n=== MULTI-MARKET DECADE BACKTEST (2015-2025) ===")
    
    for market_name, config in POOLS.items():
        print(Fore.MAGENTA + f"\n>>> MARKET: {market_name} ({config['currency']})")
        print(f"{'YEAR':<6} | {'INFLATION':<10} | {'WINNER':<12} | {'NOMINAL':<10} | {'REAL ROI':<10}")
        print("-" * 65)
        
        market_tickers = config['tickers']
        inflation_map = config['inflation']
        
        agg_real_roi = 0
        winning_counts = {}
        
        for year in range(2015, 2026):
            start = f"{year}-01-01"
            end = f"{year}-12-31"
            inf = inflation_map.get(year, 0)
            
            strats = get_strategies(market_tickers)
            engine = BacktestEngine(start, end, strats, preloaded_data=prices_df)
            results = engine.run()
            
            if not results:
                print(f"{year:<6} | {inf:<9.1f}% | {'NO DATA':<12} | {'-':<10} | {'-':<10}")
                continue
                
            # Find Winner
            best_strat = None
            best_roi = -9999
            
            for sname, res in results.items():
                if res['roi'] > best_roi:
                    best_roi = res['roi']
                    best_strat = sname
            
            # Real Return Calculation
            user_nom = 1 + (best_roi / 100.0)
            user_inf = 1 + (inf / 100.0)
            real_roi = ((user_nom / user_inf) - 1) * 100.0
            
            agg_real_roi += real_roi
            winning_counts[best_strat] = winning_counts.get(best_strat, 0) + 1
            
            print(f"{year:<6} | {inf:<9.1f}% | {best_strat:<12} | {best_roi:<9.1f}% | {real_roi:<9.1f}%")
            
        print("-" * 65)
        print(f"Aggregated Real Return (10 Years): {agg_real_roi:.1f}% (Sum of annual real returns)")
        print(f"Dominant Strategy: {max(winning_counts, key=winning_counts.get)} ({max(winning_counts.values())} wins)")

if __name__ == "__main__":
    run_multimarket_test()
