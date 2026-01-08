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
from strategies.chip_strategy import ChipMemoryStrategy
from strategies.advanced_strategies import BumTrendStrategy, MatrDipStrategy, GuaMomentumStrategy, MgbBandStrategy

# Import Firebase Broker
from execution.firebase_broker import FirebaseBroker
# Utils
from utils.market_scanner import MarketScanner
from utils.notifier import send_notification

init(autoreset=True)

class CloudBot:
    def __init__(self):
        self.strategies = []
        self.scanner = MarketScanner()

    def setup(self):
        print("--- INITIALIZING CLOUD BOT (FIREBASE MODE) ---")
        
        # Use FirebaseBroker for all
        broker_class = FirebaseBroker
        
        bist_tickers = ["AKBNK.IS", "THYAO.IS", "BIMAS.IS"]
        
        # Initialize with broker_cls
        self.strategies.append(GridStrategy(name="GridBot_Cloud", balance=1000.0, tickers=bist_tickers, broker_cls=broker_class))
        self.strategies.append(MeanReversionStrategy(name="MeanRev_Cloud", balance=1000.0, tickers=bist_tickers, broker_cls=broker_class))
        self.strategies.append(TrendStrategy(name="TrendHunter_Cloud", balance=1000.0, tickers=bist_tickers, broker_cls=broker_class))
        self.strategies.append(DCAStrategy(name="SmartDCA_Cloud", balance=1000.0, tickers=bist_tickers, broker_cls=broker_class))
        # self.strategies.append(ChipMemoryStrategy(name="ChipHunter_Cloud", balance=1000.0, broker_cls=broker_class))
        # Advanced
        self.strategies.append(BumTrendStrategy(name="BUM_Trend_Cloud", balance=1000.0, tickers=bist_tickers, broker_cls=broker_class))
        # ... add others if needed
        
        print(f"Loaded {len(self.strategies)} Cloud Strategies.")

    def run_once(self):
        """Runs a single iteration (Tick) and Exits."""
        print(f"--- RUNNING TICK {datetime.now()} ---")
        
        # 1. Scanner (Optional in cloud freq? Maybe every 4th run if running every 15m)
        # For now, skip or implement simple
        
        # 2. Collect Tickers
        all_tickers = []
        for s in self.strategies: all_tickers.extend(s.tickers)
        all_tickers = list(set(all_tickers))
        
        if not all_tickers:
            print("No tickers to check.")
            return

        # 3. Fetch Data
        # In GitHub actions, ip might be US. yfinance might give delayed data for BIST.
        # But for 'Day' trading it's ok. 
        print(f"Fetching data for {len(all_tickers)} tickers...")
        try:
            df = yf.download(all_tickers, period="1d", interval="15m", progress=False)['Close']
            market_data = {}
            for t in all_tickers:
                try:
                    if isinstance(df, pd.Series):
                        market_data[t] = df.iloc[-1]
                    elif t in df.columns:
                        market_data[t] = df[t].iloc[-1]
                except: pass
        except Exception as e:
            print(f"Data Fetch Error: {e}")
            return

        if not market_data:
            print("Market data empty (Closed?).")
            return

        # 4. Run Strategies
        for strategy in self.strategies:
            try:
                # Capture Trade Count Before
                prev_trades = len(strategy.broker.trade_log)
                
                strategy.run_tick(market_data, datetime.now())
                
                # Capture Trade Count After
                curr_trades = len(strategy.broker.trade_log)
                
                if curr_trades > prev_trades:
                    new_trade = strategy.broker.trade_log[-1]
                    msg = f"☁️ {strategy.name}: {new_trade['action']} {new_trade['ticker']} @ {new_trade['price']:.2f}"
                    print(f"NOTIFICATION: {msg}")
                    send_notification("AI Cloud Trader", msg)
                
                strategy.save() # Saves to Firestore
                
            except Exception as e:
                print(f"Error {strategy.name}: {e}")
        
        print("--- TICK COMPLETE ---")

if __name__ == "__main__":
    # Ensure env vars are set: 
    # GOOGLE_APPLICATION_CREDENTIALS (json content or path)
    # NTFY_TOPIC
    
    bot = CloudBot()
    bot.setup()
    bot.run_once()
