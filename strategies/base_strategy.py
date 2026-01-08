from abc import ABC, abstractmethod
from execution.paper_broker import PaperBroker
from utils.logger import setup_logger

class BaseStrategy(ABC):
    def __init__(self, name="Base", balance=1000.0, broker_cls=None, stop_loss_pct=0.05, trailing_stop_pct=0.10):
        self.name = name
        self.logger = setup_logger(f"Strat_{name}")
        self.stop_loss_pct = stop_loss_pct
        self.trailing_stop_pct = trailing_stop_pct
        self.highest_prices = {} # Track high water mark for trailing stop
        
        # Default to PaperBroker if none provided
        if broker_cls:
            self.broker = broker_cls(start_balance=balance, strategy_name=name)
        else:
            from execution.paper_broker import PaperBroker
            self.broker = PaperBroker(start_balance=balance)
            self.broker.load_state(f"data/sim_{name}.json")

            
        self.scan_ticker_limit = 5 # max dynamic tickers to hold check

    def save(self):
        """Persist state."""
        self.broker.save_state(filepath=f"data/sim_{self.name}.json")

    def check_risk_management(self, market_data, timestamp):
        """
        Checks open positions for Stop Loss or Trailing Stop hits.
        Returns True if a sell occured to avoid duplicate logic.
        """
        for ticker, price in market_data.items():
            amt = self.broker.get_position_amt(ticker)
            if amt <= 0:
                if ticker in self.highest_prices: del self.highest_prices[ticker]
                continue
            
            # 1. Update High Water Mark
            if ticker not in self.highest_prices: self.highest_prices[ticker] = price
            if price > self.highest_prices[ticker]: self.highest_prices[ticker] = price
            
            avg_entry = self.broker.positions[ticker]["entry_price"]
            
            # 2. Stop Loss (Fixed)
            # If price < entry * (1 - stop_loss)
            if price < avg_entry * (1 - self.stop_loss_pct):
                self.logger.warning(f"STOP LOSS triggered for {ticker} at {price:.2f} (Entry: {avg_entry:.2f})")
                self.broker.sell(ticker, price, timestamp, amount=amt)
                continue
                
            # 3. Trailing Stop
            # If price < highest * (1 - trailing_stop)
            # Only activate if we are somewhat in profit? Or always? Usually always for safety.
            trigger_price = self.highest_prices[ticker] * (1 - self.trailing_stop_pct)
            if price < trigger_price:
                 self.logger.warning(f"TRAILING STOP triggered for {ticker} at {price:.2f} (High: {self.highest_prices[ticker]:.2f})")
                 self.broker.sell(ticker, price, timestamp, amount=amt)

    @abstractmethod
    def run_tick(self, market_data, timestamp):
        """
        Main execution step.
        strategies should call self.check_risk_management(market_data, timestamp) at the start!
        """
        pass
    
    def get_status(self):
        val = self.broker.get_portfolio_value({}) # Price map needed for accurate equity
        # We need updated prices for accurate report. 
        # For now, return balance + cost basis estimate if no price map
        return f"{self.name}: Balance={self.broker.balance:.2f}"
