import pandas as pd
import yfinance as yf
from datetime import datetime
from colorama import Fore, Style, init

# Utils
from config.settings import MARKET_CONFIG

init(autoreset=True)

class BacktestEngine:
    def __init__(self, start_date, end_date, strategies, preloaded_data=None):
        self.start_date = start_date
        self.end_date = end_date
        self.strategies = strategies
        self.preloaded_data = preloaded_data
        self.data_cache = {}

    def fetch_data(self):
        # 1. Use Preloaded if available
        if self.preloaded_data is not None:
            # Filter by date
            mask = (self.preloaded_data.index >= self.start_date) & (self.preloaded_data.index <= self.end_date)
            # Filter by tickers
            needed = []
            for s in self.strategies: needed.extend(s.tickers)
            needed = list(set(needed))
            
            # Slice columns if possible (if preloaded has all tickers)
            # If preloaded has more columns, just take what we need
            return self.preloaded_data.loc[mask, needed]

        # 2. Daily Fetch (Legacy)
        all_tickers = []
        for s in self.strategies: all_tickers.extend(s.tickers)
        all_tickers = list(set(all_tickers))
        
        if not all_tickers: return None
        
        print(f"   Fetching history for {len(all_tickers)} tickers ({self.start_date} to {self.end_date})...")
        try:
            # interval 1d is standard for long backtests
            data = yf.download(all_tickers, start=self.start_date, end=self.end_date, interval="1d", progress=False)
            
            # Extract 'Close' or 'Adj Close'
            prices = data['Close'] if 'Close' in data else data['Adj Close']
            return prices
        except Exception as e:
            print(f"   Data Fetch Error: {e}")
            return None

    def run(self):
        prices_df = self.fetch_data()
        if prices_df is None or prices_df.empty:
            print("   No data.")
            return {}

        # Replay
        last_prices = {}
        for timestamp, row in prices_df.iterrows():
            market_data = {}
            # row_dict = row.to_dict() # Might be Series or Dict depending on columns
            
            # Handle MultiIndex if necessary, but yfinance simple structure usually fits
            # If 1 ticker, row is scalar/float? No, usually Series with Ticker index if multiple
            
            for ticker in row.index:
                # If ticker is a column name (Multi-ticker)
                val = row[ticker]
                if pd.notna(val):
                    market_data[ticker] = val
                    last_prices[ticker] = val
            
            if not market_data: continue

            # Execute Strategies
            for strategy in self.strategies:
                try:
                    strategy.run_tick(market_data, timestamp)
                    
                    # Track Daily Equity
                    current_equity = strategy.broker.get_portfolio_value(last_prices)
                    if not hasattr(strategy, "equity_curve"): strategy.equity_curve = []
                    strategy.equity_curve.append({
                        "date": timestamp, 
                        "equity": current_equity
                    })
                    
                except Exception as e:
                    # print(f"Err {strategy.name}: {e}")
                    pass
        
        # Calculate Final Results
        results = {}
        for s in self.strategies:
            equity = s.broker.get_portfolio_value(last_prices)
            roi = ((equity - s.broker.initial_balance) / s.broker.initial_balance) * 100
            results[s.name] = {
                "equity": equity,
                "roi": roi,
                "balance": s.broker.balance,
                "trades": len(s.broker.trade_log),
                "history": getattr(s, "equity_curve", [])
            }
            
        return results
