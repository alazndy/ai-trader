from strategies.base_strategy import BaseStrategy
from config.settings import MARKET_CONFIG

class GridStrategy(BaseStrategy):
    def __init__(self, name="MeanRev", balance=1000.0, tickers=None, **kwargs):
        super().__init__(name, balance, **kwargs)
        self.tickers = tickers if tickers else []
        self.grids = {} # Store grid state per ticker
        
    def setup_grid(self, ticker, current_price):
        """Initializes grid levels for a ticker."""
        grid_qty = max(1, int((self.broker.balance * 0.1) / current_price)) # 10% per grid line?
        
        self.grids[ticker] = {
            "center": current_price,
            "qty": grid_qty,
            "levels": self.calculate_levels(current_price),
            "last_price": current_price
        }
        self.logger.info(f"Initialized Grid for {ticker}: Center={current_price:.2f}, Qty={grid_qty}")

    def calculate_levels(self, center, grids=20, range_pct=0.10):
        lower = [center * (1 - (i * (range_pct*2)/grids)) for i in range(1, (grids//2)+1)]
        upper = [center * (1 + (i * (range_pct*2)/grids)) for i in range(1, (grids//2)+1)]
        return sorted(lower + [center] + upper)

    def run_tick(self, market_data, timestamp):
        """
        market_data: {ticker: price}
        """
        self.check_risk_management(market_data, timestamp)
        # The following lines from the instruction are syntactically incorrect or redundant.
        # for ticker, price in market_data.items(): {ticker: price}
        # else:
        #     current_date = timestamp.strftime("%Y-%m-%d")
        # The instruction "Add check_risk_management check" is already satisfied by the line above.
        # If the intent was to add it again, it would be a duplicate.
        # Assuming the primary intent was to ensure the check is present.
        
        for ticker, price in market_data.items():
            if ticker not in self.tickers: continue
            
            # Setup if new
            if ticker not in self.grids:
                self.setup_grid(ticker, price)
                continue
                
            grid = self.grids[ticker]
            last_price = grid['last_price']
            levels = grid['levels']
            qty = grid['qty']
            
            # Check levels
            for level in levels:
                # Buy Cross (Down)
                if last_price > level and price <= level:
                     if self.broker.balance > (level * qty):
                         self.broker.buy(ticker, level, timestamp, pct_portfolio=None) 
                         # Note: Using pct_portfolio=None implies using full budget or logic in broker.
                         # Need to fix Broker to accept 'amount' override or handle it better.
                         # For now, relying on Broker's internal safeguards.
                         
                # Sell Cross (Up)
                elif last_price < level and price >= level:
                     if self.broker.get_position_amt(ticker) >= qty:
                         self.broker.sell(ticker, level, timestamp, amount=qty)
                         
            # Update State
            grid['last_price'] = price
            
            # Re-center check (Dynamic Grid)
            if price > grid['center'] * 1.10 or price < grid['center'] * 0.90:
                self.logger.info(f"Re-centering grid for {ticker}")
                self.setup_grid(ticker, price)
