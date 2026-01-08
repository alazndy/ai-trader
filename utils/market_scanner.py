import yfinance as yf
import pandas as pd
from config.settings import MARKET_CONFIG

class MarketScanner:
    def __init__(self):
        # In a real app, this would be a much larger universe.
        # For this prototype, we'll scan a superset of known tickers + some popular ones.
        self.universe = [
            # BIST
            "THYAO.IS", "BIMAS.IS", "AKBNK.IS", "GARAN.IS", "ASELS.IS", "SISE.IS", "KCHOL.IS", "SASA.IS", "HEKTS.IS",
            # GLOBAL
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "AMD", "INTC",
            # CRYPTO
            "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD"
        ]
        
    def scan_for_opportunities(self, strategy_type="TREND"):
        """
        Scans the universe and returns tickers matching the strategy criteria.
        """
        print(f"Scanning market for {strategy_type} opportunities...")
        
        # Optimize: Batch fetch
        try:
            # period="5d" to get some history for MA/RSI calculations if needed
            data = yf.download(self.universe, period="5d", interval="1d", progress=False)['Close']
            
            candidates = []
            
            if data.empty:
                return []

            # If single ticker
            if isinstance(data, pd.Series):
                 # Not enough data to scan really
                 return []
                 
            for ticker in data.columns:
                series = data[ticker].dropna()
                if len(series) < 2: continue
                
                last_price = series.iloc[-1]
                prev_price = series.iloc[-2]
                pct_change = (last_price - prev_price) / prev_price
                
                if strategy_type == "TREND":
                    # Simple Momentum: Price is up > 2% today (or last close)
                    if pct_change > 0.02:
                        candidates.append(ticker)
                        
                elif strategy_type == "MEAN_REVERSION":
                    # Simple Oversold: Price is down > 3%
                    if pct_change < -0.03:
                        candidates.append(ticker)
                        
                elif strategy_type == "VOLATILITY":
                    # High movement
                    if abs(pct_change) > 0.04:
                        candidates.append(ticker)

            print(f"  Found {len(candidates)} candidates for {strategy_type}.")
            return candidates

        except Exception as e:
            print(f"Scanner Error: {e}")
            return []

if __name__ == "__main__":
    scanner = MarketScanner()
    print("Trend Candidates:", scanner.scan_for_opportunities("TREND"))
    print("Dip Candidates:", scanner.scan_for_opportunities("MEAN_REVERSION"))
