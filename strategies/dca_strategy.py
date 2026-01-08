from strategies.base_strategy import BaseStrategy
from datetime import datetime

class DCAStrategy(BaseStrategy):
    def __init__(self, name="SmartDCA", balance=1000.0, tickers=None):
        super().__init__(name, balance)
        self.tickers = tickers if tickers else []
        self.last_buy_date = {} # {ticker: date_str}

    def run_tick(self, market_data, timestamp):
        # We assume timestamp is a datetime-like object or string.
        # If it's a string from backtest, use it directly.
        if isinstance(timestamp, str):
            current_date = timestamp.split(" ")[0] # Just YYYY-MM-DD
        else:
            current_date = timestamp.strftime("%Y-%m-%d")
        
        for ticker, price in market_data.items():
            if ticker not in self.tickers: continue
            
            last = self.last_buy_date.get(ticker)
            
            # Buy Daily (for simulation speed) or Weekly?
            # User wants 1 month sim. Daily DCA is good.
            if last != current_date:
                # Buy Small Amount (e.g., 50 TL)
                # If balance allows
                if self.broker.balance >= 50:
                    self.logger.info(f"DCA Buy for {ticker}. Routine.")
                    # Manually calculate amount since broker.buy uses logic I haven't fully fixed yet
                    # Actually relying on 'broker.buy' logic which tries to use pct_portfolio if passed, or defaults.
                    # Let's override broker logic locally:
                    self.broker.execute_vault_buy(ticker, price, 50.0, current_date) # Reusing vault helper for direct amt
                    self.last_buy_date[ticker] = current_date
