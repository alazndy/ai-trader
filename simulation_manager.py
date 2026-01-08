import time
import pandas as pd
import yfinance as yf
from datetime import datetime
from colorama import Fore, Style, init

# Strategies
from strategies.grid_strategy import GridStrategy
from strategies.mean_reversion_strategy import MeanReversionStrategy
from strategies.trend_strategy import TrendStrategy
from strategies.dca_strategy import DCAStrategy
from strategies.chip_strategy import ChipMemoryStrategy
from strategies.advanced_strategies import BumTrendStrategy, MatrDipStrategy, GuaMomentumStrategy, MgbBandStrategy

# Utils
from utils.market_scanner import MarketScanner
from utils.notifier import send_notification
from utils.robustness import retry_connection
from config.settings import MARKET_CONFIG

init(autoreset=True)

class SimulationManager:
    def __init__(self):
        self.strategies = []
        self.scanner = MarketScanner()
        self.is_running = True
        
        # Benchmark Initial Prices (For comparison)
        self.benchmarks = {
            "GOLD": {"ticker": "GC=F", "start_price": 0},
            "USD": {"ticker": "TRY=X", "start_price": 0} # USD/TRY
        }
        
    def setup(self):
        print(Fore.CYAN + "--- INITIALIZING SIMULATION (1 MONTH BATTLE) ---")
        
        # 1. Initialize Strategies
        # Fixed Tickers per strategy
        bist_tickers = ["AKBNK.IS", "THYAO.IS", "BIMAS.IS"]
        
        # Standard
        self.strategies.append(GridStrategy(name="GridBot", balance=1000.0, tickers=bist_tickers))
        self.strategies.append(MeanReversionStrategy(name="MeanRev", balance=1000.0, tickers=bist_tickers))
        self.strategies.append(TrendStrategy(name="TrendHunter", balance=1000.0, tickers=bist_tickers))
        self.strategies.append(DCAStrategy(name="SmartDCA", balance=1000.0, tickers=bist_tickers))
        self.strategies.append(ChipMemoryStrategy(name="ChipHunter", balance=1000.0))
        
        # Advanced (New)
        self.strategies.append(BumTrendStrategy(name="BUM_Trend", balance=1000.0, tickers=bist_tickers))
        self.strategies.append(MatrDipStrategy(name="MATR_Dip", balance=1000.0, tickers=bist_tickers))
        self.strategies.append(GuaMomentumStrategy(name="RUA_Mom", balance=1000.0, tickers=bist_tickers))
        self.strategies.append(MgbBandStrategy(name="MGB_Band", balance=1000.0, tickers=bist_tickers))
        
        print(f"Initialized {len(self.strategies)} Strategies with 1000 TL each.")
        
        # 2. Benchmark Snapshot
        try:
            bench_tickers = [b["ticker"] for b in self.benchmarks.values()]
            data = yf.download(bench_tickers, period="1d", progress=False)['Close']
            for k, v in self.benchmarks.items():
                tick = v["ticker"]
                price = data[tick].iloc[-1] if not data.empty else 0
                self.benchmarks[k]["start_price"] = price
                print(f"Benchmark {k} Start: {price:.2f}")
        except Exception as e:
            print(f"Benchmark Error: {e}")

    @retry_connection(max_retries=3, delay=2)
    def fetch_live_data(self, all_tickers):
        """Fetch current prices for all needed tickers."""
        if not all_tickers: return {}
        try:
            # unique
            t_list = list(set(all_tickers))
            # 1m is ideal for 'Real Time' feel
            df = yf.download(t_list, period="1d", interval="1m", progress=False)['Close']
            
            prices = {}
            if df.empty: return {}
            
            # Helper to extract last valid price
            for t in t_list:
                try:
                    if isinstance(df, pd.Series):
                        val = df.iloc[-1]
                    elif t in df.columns:
                        val = df[t].dropna().iloc[-1]
                    else:
                        continue
                    prices[t] = val
                except:
                    pass
            return prices
        except:
            return {}

    def run_loop(self, interval=60):
        print(Fore.GREEN + "Simulation Started. Press Ctrl+C to stop.")
        
        try:
            while self.is_running:
                print(f"\n--- TICK {datetime.now().strftime('%H:%M:%S')} ---")
                
                # 1. Dynamic Scanner (Every 10 ticks? Let's do every tick for now or randomized)
                # In real app, scan every 1 hour.
                if datetime.now().minute % 60 == 0: # Hourly
                    opportunities = self.scanner.scan_for_opportunities("TREND")
                    if opportunities:
                        print(f"{Fore.YELLOW}Scanner found: {opportunities}")
                        # Add to Trend Strategy
                        for s in self.strategies:
                            if isinstance(s, TrendStrategy):
                                for op in opportunities:
                                    if op not in s.tickers:
                                        s.tickers.append(op)
                                        print(f"Added {op} to {s.name}")

                # 2. Collect all tickers from all strategies
                all_tickers = []
                for s in self.strategies:
                    all_tickers.extend(s.tickers)
                
                # 3. Fetch Data
                market_data = self.fetch_live_data(all_tickers)
                if not market_data:
                    print("No market data (Market closed?)")
                    time.sleep(interval)
                    continue
                    
                # 4. Run Strategies
                for strategy in self.strategies:
                    try:
                        # Capture Trade Count Before
                        prev_trades = len(strategy.broker.trade_log)
                        
                        strategy.run_tick(market_data, datetime.now())
                        
                        # Capture Trade Count After
                        curr_trades = len(strategy.broker.trade_log)
                        
                        if curr_trades > prev_trades:
                            # New Trade!
                            new_trade = strategy.broker.trade_log[-1]
                            msg = f"{strategy.name}: {new_trade['action']} {new_trade['ticker']} @ {new_trade['price']:.2f}"
                            print(f"{Fore.MAGENTA}NOTIFICATION: {msg}")
                            send_notification(title=f"AI Trader: {strategy.name}", message=msg, priority="high")
                        
                        # Log Status
                        # print(f"  {strategy.get_status()}") # Reduce spam
                        strategy.save() # Persist
                        
                    except Exception as e:
                        print(f"Error in {strategy.name}: {e}")
                
                 # Hourly Summary Notification
                 # ... (Omitted for brevity, can add later)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nStopping Simulation...")
            self.report_results()

    def report_results(self):
        print(Fore.CYAN + "\n--- FINAL REPORT ---")
        summary = "Final Results:\n"
        for s in self.strategies:
            line = f"{s.name}: Balance {s.broker.balance:.2f} | Equity: {s.get_status()}"
            print(line)
            summary += line + "\n"
        
        send_notification("AI Trader Completed", summary)

if __name__ == "__main__":
    sim = SimulationManager()
    sim.setup()
    sim.run_loop(interval=60) # 1 minute loops
