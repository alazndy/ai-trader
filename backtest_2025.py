import pandas as pd
import yfinance as yf
from datetime import datetime
from colorama import Fore, Style, init

# Strategies (Reusing the same classes!)
from strategies.grid_strategy import GridStrategy
from strategies.mean_reversion_strategy import MeanReversionStrategy
from strategies.trend_strategy import TrendStrategy
from strategies.dca_strategy import DCAStrategy
from strategies.chip_strategy import ChipMemoryStrategy
from strategies.advanced_strategies import BumTrendStrategy, MatrDipStrategy, GuaMomentumStrategy, MgbBandStrategy

# Utils
from utils.market_scanner import MarketScanner # Scanner might need mocking for backtest speed
from config.settings import MARKET_CONFIG

init(autoreset=True)

class BacktestManager:
    def __init__(self):
        self.strategies = []
        self.start_date = "2025-01-01"
        self.end_date = "2025-12-31" 
        
    def setup(self):
        print(Fore.CYAN + "--- INITIALIZING 2025 BACKTEST ENGINE ---")
        
        # 1. Initialize Strategies (Fresh Wallets)
        bist_tickers = ["AKBNK.IS", "THYAO.IS", "BIMAS.IS"]
        
        # Standard
        self.strategies.append(GridStrategy(name="GridBot_BT", balance=1000.0, tickers=bist_tickers))
        self.strategies.append(MeanReversionStrategy(name="MeanRev_BT", balance=1000.0, tickers=bist_tickers))
        self.strategies.append(TrendStrategy(name="TrendHunter_BT", balance=1000.0, tickers=bist_tickers))
        self.strategies.append(DCAStrategy(name="SmartDCA_BT", balance=1000.0, tickers=bist_tickers))
        self.strategies.append(ChipMemoryStrategy(name="ChipHunter_BT", balance=1000.0))
        
        # Advanced (New)
        self.strategies.append(BumTrendStrategy(name="BUM_Trend_BT", balance=1000.0, tickers=bist_tickers))
        self.strategies.append(MatrDipStrategy(name="MATR_Dip_BT", balance=1000.0, tickers=bist_tickers))
        self.strategies.append(GuaMomentumStrategy(name="RUA_Mom_BT", balance=1000.0, tickers=bist_tickers))
        self.strategies.append(MgbBandStrategy(name="MGB_Band_BT", balance=1000.0, tickers=bist_tickers))
        
        print(f"Initialized {len(self.strategies)} Strategies.")

    def run_year(self):
        print(Fore.GREEN + f"Fetching Data for {self.start_date} to {self.end_date}...")
        
        # 1. Collect Tickers
        all_tickers = []
        for s in self.strategies:
            all_tickers.extend(s.tickers)
        all_tickers = list(set(all_tickers))
        
        # 2. Bulk Download
        # We need Daily resolution for 2025.
        data = yf.download(all_tickers, start=self.start_date, end=self.end_date, interval="1d", progress=True)
        
        # If MultiIndex (Ticker, OHLC), we need to handle it.
        # yfinance v0.2+ returns MultiIndex columns if multiple tickers.
        # Structure: (PriceType, Ticker) -> data['Adj Close']['AAPL']
        
        if data.empty:
            print("No data found for 2025.")
            return

        # Use Close or Adj Close
        if 'Adj Close' in data.columns:
            prices_df = data['Adj Close']
        else:
            prices_df = data['Close']
            
        print(Fore.YELLOW + "Starting Day-by-Day Replay...")
        
        # 3. Replay Loop
        market_data = {}
        for timestamp, row in prices_df.iterrows():
            # Construct market_data for this day
            market_data = {}
            for ticker in all_tickers:
                # Handle potential NaN
                val = row.get(ticker)
                if pd.notna(val):
                    market_data[ticker] = val
            
            if not market_data: continue
            
            # Run Strategies
            for strategy in self.strategies:
                try:
                    strategy.run_tick(market_data, timestamp)
                except Exception as e:
                    print(f"Error {strategy.name}: {e}")
                    
        print(Fore.CYAN + "Backtest Complete.")
        print(Fore.CYAN + "Backtest Complete.")
        
        # Use the last market_data from the loop for valuation
        self.report_results(market_data)

    def report_results(self, last_prices):
        print("\n--- 2025 FINAL RESULTS (1000 TL START) ---")
        best_strat = None
        best_val = -1
        
        # We need final prices to calculate Equity
        # Strategy.get_status() calls broker.get_portfolio_value using INTERNAL price map?
        # Broker doesn't store price map. It requires it passed.
        # BaseStrategy.get_status() passes {} empty dict, so it returns Balance + 0 equity for stocks!
        # We need to manually calculate equity here using last known prices.
        
        # Since backtest loop finished, we don't have 'current market_data' handy easily in this scope 
        # without fetching again or caching.
        # Let's trust Balance for sold items, but for held items we need value.
        # Hack: Pass 0 prices -> Equity = Balance. This is wrong if they hold stock.
        # FIX: We need the last prices from the loop.
        
        print(f"{'STRATEGY':<15} | {'BALANCE':<10} | {'EQUITY':<10} | {'ROI':<10}")
        print("-" * 50)
        
        for s in self.strategies:
            # Calculate Equity using the last known prices from the backtest
            equity = s.broker.get_portfolio_value(last_prices)
            roi = (equity - 1000.0) / 1000.0 * 100.0
            print(f"{s.name:<15} | {s.broker.balance:<10.2f} | {equity:<10.2f} | {roi:<10.2f}%")
            
            if equity > best_val:
                best_val = equity
                best_strat = s.name
                
        print("-" * 50)
        print(Fore.GREEN + f"WINNER: {best_strat} with {best_val:.2f} TL")

if __name__ == "__main__":
    bt = BacktestManager()
    bt.setup()
    bt.run_year()
