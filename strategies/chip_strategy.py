from strategies.trend_strategy import TrendStrategy

class ChipMemoryStrategy(TrendStrategy):
    def __init__(self, name="ChipHunter", balance=1000.0, tickers=None):
        # Default Sector Tickers if none provided
        sector_tickers = tickers if tickers else [
            "NVDA", "AMD", "TSM", "MU", "INTC", "ASML", "AVGO", "QCOM"
        ]
        super().__init__(name, balance, tickers=sector_tickers)
        
    def run_tick(self, market_data, timestamp):
        # Just use Trend Logic but maybe cleaner logging or specific tweaks?
        # For now, inherit Trend logic exactly.
        super().run_tick(market_data, timestamp)
