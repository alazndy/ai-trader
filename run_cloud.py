import time
import os
import pandas as pd
import yfinance as yf
from datetime import datetime
from colorama import Fore, Style, init

# Import Strategies
from strategies.grid_strategy import GridStrategy
from strategies.mean_reversion_strategy import MeanReversionStrategy
from strategies.trend_strategy import TrendStrategy
from strategies.dca_strategy import DCAStrategy
from strategies.advanced_strategies import BumTrendStrategy, GuaMomentumStrategy

# Import Firebase Broker
from execution.firebase_broker import FirebaseBroker
# Utils
from utils.notifier import send_notification
from config.settings import MARKET_CONFIG

init(autoreset=True)

class CloudBot:
    def __init__(self):
        self.strategies = []
        # No Scanner in Cloud/Cron mode for simplicity, just Strategy execution

    def setup_market(self, market_name):
        """Initializes strategies for a specific market."""
        self.strategies = [] # Clear previous
        
        cfg = MARKET_CONFIG.get(market_name)
        if not cfg: 
            print(f"Invalid Market: {market_name}")
            return

        tickers = cfg["TICKERS"]
        broker_class = FirebaseBroker
        
        # Instantiate Strategies with Cloud Naming (e.g. SmartDCA_BIST_Cloud)
        # We need unique names to avoid Firestore collisions if running multiple bots
        suffix = f"{market_name}_Cloud"
        
        self.strategies.append(DCAStrategy(name=f"SmartDCA_{suffix}", balance=1000.0, tickers=tickers, broker_cls=broker_class))
        self.strategies.append(TrendStrategy(name=f"Trend_{suffix}", balance=1000.0, tickers=tickers, broker_cls=broker_class))
        
        if market_name == "CRYPTO":
             self.strategies.append(GuaMomentumStrategy(name=f"GUA_{suffix}", balance=1000.0, tickers=tickers, broker_cls=broker_class))
        elif market_name == "BIST":
             self.strategies.append(BumTrendStrategy(name=f"BUM_{suffix}", balance=1000.0, tickers=tickers, broker_cls=broker_class))

        print(f"Loaded {len(self.strategies)} Strategies for {market_name}.")

    def run_market_tick(self, market_name):
        print(f"\n>>> PROCESSING MARKET: {market_name} <<<")
        self.setup_market(market_name)
        
        # Collect Tickers
        all_tickers = []
        for s in self.strategies: all_tickers.extend(s.tickers)
        all_tickers = list(set(all_tickers))
        
        if not all_tickers: return

        # Fetch Data (15m usually fine for cloud heartbeat)
        # If Crypto, maybe 1m? But GitHub Actions cron is min 5m. 
        # So we stick to 15m or 1h snapshot. 
        # The user wants "Continuous" so assume 15m check is acceptable for Cloud redundancy.
        interval = "15m" 
        period = "1d"
        
        print(f"Fetching {interval} data for {len(all_tickers)} tickers...")
        try:
            df = yf.download(all_tickers, period=period, interval=interval, progress=False)
            
            # YFinance Structure Handling
            prices = df['Close'] if 'Close' in df else df['Adj Close']
            
            market_data = {}
            for t in all_tickers:
                try:
                    val = None
                    if isinstance(prices, pd.Series):
                        val = prices.iloc[-1]
                    elif t in prices.columns:
                        val = prices[t].iloc[-1]
                    
                    if pd.notna(val):
                        market_data[t] = val
                except: pass
                
            if not market_data:
                print("Market data empty.")
                return

            # Run Strategies
            for strategy in self.strategies:
                try:
                    prev_trades = len(strategy.broker.trade_log)
                    
                    # RUN TICK
                    strategy.run_tick(market_data, datetime.now())
                    
                    curr_trades = len(strategy.broker.trade_log)
                    
                    if curr_trades > prev_trades:
                        new_trade = strategy.broker.trade_log[-1]
                        msg = f"☁️ {strategy.name}: {new_trade['action']} {new_trade['ticker']} @ {new_trade['price']:.2f}"
                        print(f"NOTIFICATION: {msg}")
                        send_notification(f"AI Cloud: {market_name}", msg)
                    
                    strategy.save() # Persist to Firestore
                    
                except Exception as e:
                    print(f"Error {strategy.name}: {e}")

        except Exception as e:
            print(f"Fetch Error: {e}")

    def run_all_markets(self):
        # Loop through all available markets in Settings
        markets = ["BIST", "GLOBAL", "CHIPS", "CRYPTO"]
        for m in markets:
            try:
                self.run_market_tick(m)
            except Exception as e:
                print(f"Critical Error in {m}: {e}")

if __name__ == "__main__":
    # Ensure env vars are set
    bot = CloudBot()
    bot.run_all_markets()
