from strategies.base_strategy import BaseStrategy
import numpy as np

class TrendStrategy(BaseStrategy):
    def __init__(self, name="TrendHunter", balance=1000.0, tickers=None):
        super().__init__(name, balance)
        self.tickers = tickers if tickers else []
        self.history = {} 

    def calculate_sma(self, data, period):
        if len(data) < period:
            return None
        return np.mean(data[-period:])

    def run_tick(self, market_data, timestamp):
        self.check_risk_management(market_data, timestamp)
        for ticker, price in market_data.items():
            if ticker not in self.history: self.history[ticker] = []
            self.history[ticker].append(price)
            if len(self.history[ticker]) > 50: self.history[ticker].pop(0) # Keep 50
            
            if len(self.history[ticker]) < 20: continue
            
            # Simple SMA 10/20
            fast_period = 10
            slow_period = 20
            
            fast_ma = self.calculate_sma(self.history[ticker], fast_period)
            slow_ma = self.calculate_sma(self.history[ticker], slow_period)
            
            if fast_ma is None or slow_ma is None: continue
            
            # Context
            context = {
                "fast_ma": fast_ma, 
                "slow_ma": slow_ma, 
                "diff_pct": (fast_ma - slow_ma)/slow_ma,
                "strategy": "TrendHunter"
            }
            
            # Golden Cross Logic (Fast crosses above Slow)
            if fast_ma > slow_ma:
                # BUY Signal
                 if self.broker.balance > price:
                     # Check if we already have a position?
                     amt = self.broker.get_position_amt(ticker)
                     if amt == 0:
                         self.broker.buy(ticker, price, timestamp, pct_portfolio=0.20, context=context)
            
            elif fast_ma < slow_ma:
                # SELL Signal (Death Cross)
                if self.broker.get_position_amt(ticker) > 0:
                     self.logger.info(f"Trend BROKEN for {ticker}. SELL.")
                     self.broker.sell(ticker, price, timestamp, pct_portfolio=1.0, context=context)
