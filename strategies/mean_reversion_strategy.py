from strategies.base_strategy import BaseStrategy
import pandas as pd
import numpy as np

class MeanReversionStrategy(BaseStrategy):
    def __init__(self, name="MeanRev", balance=1000.0, tickers=None):
        super().__init__(name, balance)
        self.tickers = tickers if tickers else []
        self.history = {} # Store recent prices for RSI calc: {ticker: [prices]}

    def calculate_rsi(self, prices, window=14):
        if len(prices) < window + 1: return 50 # Default neutral
        
        deltas = np.diff(prices)
        seed = deltas[:window+1]
        up = seed[seed >= 0].sum()/window
        down = -seed[seed < 0].sum()/window
        rs = up/down
        rsi = np.zeros_like(prices)
        rsi[:window] = 100. - 100./(1. + rs)

        for i in range(window, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up*(window-1) + upval)/window
            down = (down*(window-1) + downval)/window
            rs = up/down
            rsi[i] = 100. - 100./(1. + rs)
            
        return rsi[-1]

    def run_tick(self, market_data, timestamp):
        for ticker, price in market_data.items():
            # Add to history
            if ticker not in self.history: self.history[ticker] = []
            self.history[ticker].append(price)
            if len(self.history[ticker]) > 30: self.history[ticker].pop(0)
            
            # Need enough data for RSI
            if len(self.history[ticker]) < 15: continue
            # Calculate RSI
            rsi = self.calculate_rsi(history)
            
            # Context for AI
            context = {"rsi": rsi, "strategy": "MeanReversion"}
            
            # Logic
            if rsi < 30:
                # Buy
                # Only if we have cash
                if self.broker.balance > price:
                    # check if we already hold? (Simple logic: Buy more if really low?)
                    # For now just buy if not full.
                   self.broker.buy(ticker, price, timestamp, pct_portfolio=0.20, context=context)
            
            elif rsi > 70:
                # Sell
                self.broker.sell(ticker, price, timestamp, pct_portfolio=1.0, context=context)
                self.logger.info(f"RSI Overbought ({rsi:.2f}) for {ticker}. SELLING.")
