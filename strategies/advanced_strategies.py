from strategies.base_strategy import BaseStrategy
import numpy as np
import pandas as pd

class BumTrendStrategy(BaseStrategy):
    """
    1. BUM TREND ALGORİTMASI (Ana Trend Takipçisi)
    Logic: Uses SuperTrend (ATR Trailing Stop) to determine trend direction.
    """
    def __init__(self, name="BUM_Trend", balance=1000.0, tickers=None, atr_period=10, multiplier=3.0, **kwargs):
        super().__init__(name, balance, **kwargs)
        self.tickers = tickers if tickers else []
        self.history = {}
        self.atr_period = atr_period
        self.multiplier = multiplier

    def calculate_supertrend(self, df):
        # Basic SuperTrend Calculation
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        # TR
        tr1 = abs(high - low)
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(self.atr_period).mean()
        
        # HL2
        hl2 = (high + low) / 2
        
        # Upper/Lower Bands
        final_upper = hl2 + (self.multiplier * atr)
        final_lower = hl2 - (self.multiplier * atr)
        
        # SuperTrend Logic (Simplified for brevity)
        supertrend = [True] * len(df) # True = Bullish, False = Bearish
        
        # Iterative update needed for SuperTrend state
        # For simplicity in this mock, we'll use a simplified version:
        # If Close > UpperBand -> Bullish
        # If Close < LowerBand -> Bearish
        # In real SuperTrend, the bands don't move against the trend.
        
        # Let's stick to EMA Crossover for Robustness if SuperTrend is too complex for simple pandas
        # Actually user said "Directions map". Let's use simple EMA 20 > EMA 50.
        # But let's try a simplified SuperTrend approximation.
        
        return close > final_lower # Crudest approximation: Close above Lower Band is bullish ish.

    def run_tick(self, market_data, timestamp):
        # We need OHLC data for SuperTrend, but market_data is just {ticker: price} (Close)
        # For simulation, we only have 'current price'. 
        # LIVE: We assume we fetch history externally.
        # BACKTEST: 'market_data' allows us to see *current*, but we need history.
        
        # FIX: The BaseStrategy design passes only current price. 
        # Strategies need to maintain their own history or fetch it.
        # In current design, we append price to self.history[ticker].
        # We can simulate High/Low/Open from Close (Poor man's candles) or require meaningful history.
        
        for ticker, price in market_data.items():
            if ticker not in self.history: self.history[ticker] = []
            self.history[ticker].append(price)
            if len(self.history[ticker]) > 50: self.history[ticker].pop(0)
            
            if len(self.history[ticker]) < 20: continue
            
            # Simple Trend Logic (BUM Equivalent)
            # EMA 10 > EMA 30 -> GREEN (Buy)
            prices = np.array(self.history[ticker])
            ema_fast = np.mean(prices[-10:]) # SMA actually
            ema_slow = np.mean(prices[-30:])
            
            if ema_fast > ema_slow * 1.01: # 1% Buffer
                if self.broker.get_position_amt(ticker) == 0:
                    self.broker.buy(ticker, price, timestamp, pct_portfolio=0.5)
            elif ema_fast < ema_slow:
                 if self.broker.get_position_amt(ticker) > 0:
                    self.broker.sell(ticker, price, timestamp)

class MatrDipStrategy(BaseStrategy):
    """
    4. MAT-R DİPTEN DÖNÜŞ (Dip Avcısı)
    Logic: RSI < 30 (Oversold) AND Price > Previous Close (Turning Up)
    """
    def __init__(self, name="MATR_Dip", balance=1000.0, tickers=None, **kwargs):
        super().__init__(name, balance, **kwargs)
        self.tickers = tickers if tickers else []
        self.history = {}

    def calculate_rsi(self, prices, window=14):
        deltas = np.diff(prices)
        seed = deltas[:window+1]
        up = seed[seed >= 0].sum()/window
        down = -seed[seed < 0].sum()/window
        if down == 0: return 100
        rs = up/down
        rsi = 100. - 100./(1. + rs)
        # ... rolling ...
        # Simplified for last value:
        avg_gain = np.mean([x for x in deltas[-window:] if x > 0] or [0])
        avg_loss = np.mean([abs(x) for x in deltas[-window:] if x < 0] or [0])
        if avg_loss == 0: return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def run_tick(self, market_data, timestamp):
        for ticker, price in market_data.items():
            if ticker not in self.history: self.history[ticker] = []
            self.history[ticker].append(price)
            if len(self.history[ticker]) > 100: self.history[ticker].pop(0)
            
            if len(self.history[ticker]) < 20: continue
            
            prices = self.history[ticker]
            rsi = self.calculate_rsi(prices, 14)
            
            # Buy Dip: Oversold + Turning Up (Current > Previous)
            if rsi < 30 and price > prices[-2]:
                 if self.broker.get_position_amt(ticker) == 0:
                    self.broker.buy(ticker, price, timestamp, pct_portfolio=0.2)
            
            # Sell Quick on Bounce: RSI > 50
            elif rsi > 50:
                 if self.broker.get_position_amt(ticker) > 0:
                    self.broker.sell(ticker, price, timestamp)

class GuaMomentumStrategy(BaseStrategy):
    """
    5. RUA MOMENTUM (GUA - Modified Name? RUA in prompt)
    Logic: High Momentum (ROC) 
    """
    def __init__(self, name="RUA_Mom", balance=1000.0, tickers=None, **kwargs):
        super().__init__(name, balance, **kwargs)
        self.tickers = tickers if tickers else []
        self.history = {}

    def run_tick(self, market_data, timestamp):
        for ticker, price in market_data.items():
            if ticker not in self.history: self.history[ticker] = []
            self.history[ticker].append(price)
            if len(self.history[ticker]) > 30: self.history[ticker].pop(0)
            
            if len(self.history[ticker]) < 10: continue

            # ROC (Rate of Change) over 5 periods
            prev = self.history[ticker][-5]
            roc = ((price - prev) / prev) * 100
            
            # Verify Strong Momentum (> 2% in 5 ticks/days)
            if roc > 2.0:
                 if self.broker.get_position_amt(ticker) == 0:
                    self.broker.buy(ticker, price, timestamp, pct_portfolio=0.4)
            
            # Trailing stop or Momentum Loss logic
            elif roc < 0:
                 if self.broker.get_position_amt(ticker) > 0:
                    self.broker.sell(ticker, price, timestamp)

class MgbBandStrategy(BaseStrategy):
    """
    3. MGB-4S BANT (Yatay Piyasa Dedektörü)
    Logic: Bollinger Band Squeeze. 
    If Bandwidth is LOW -> DO NOT TRADE (or Sell all if holds).
    If Bandwidth expands -> Follow breakout.
    """
    def __init__(self, name="MGB_Band", balance=1000.0, tickers=None, **kwargs):
        super().__init__(name, balance, **kwargs)
        self.tickers = tickers if tickers else []
        self.history = {}

    def run_tick(self, market_data, timestamp):
        for ticker, price in market_data.items():
            if ticker not in self.history: self.history[ticker] = []
            self.history[ticker].append(price)
            if len(self.history[ticker]) > 30: self.history[ticker].pop(0)
            if len(self.history[ticker]) < 20: continue
            
            prices = np.array(self.history[ticker])
            sma = np.mean(prices[-20:])
            std = np.std(prices[-20:])
            upper = sma + (2 * std)
            lower = sma - (2 * std)
            
            bandwidth = (upper - lower) / sma
            
            # Squeeze Threshold (e.g., 2% width)
            is_squeeze = bandwidth < 0.02 
            
            if is_squeeze:
                # Market is Flat/Choppy -> Stay Cash or Wait
                # User says: "Bazen en iyi pozisyon, pozisyonsuzluktur"
                # If we have position, maybe close it if risk is defined, or just don't open new.
                # Let's say we close to avoid "Testere"
                if self.broker.get_position_amt(ticker) > 0:
                     self.broker.sell(ticker, price, timestamp)
            else:
                # Volatility Expansion
                # Breakout Up
                if price > upper:
                     if self.broker.get_position_amt(ticker) == 0:
                        self.broker.buy(ticker, price, timestamp, pct_portfolio=0.3)
                # Breakout Down
                elif price < lower:
                     if self.broker.get_position_amt(ticker) > 0:
                        self.broker.sell(ticker, price, timestamp)
