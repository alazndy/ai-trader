from execution.paper_broker import PaperBroker
from abc import ABC, abstractmethod

class RealExchangeInterface(ABC):
    """
    Interface for Real Exchange APIs (Binance, Alpaca, InfoYatirim, etc.)
    """
    @abstractmethod
    def get_market_price(self, ticker): pass
    
    @abstractmethod
    def place_order(self, ticker, amount, side, order_type="MARKET"): pass
    
    @abstractmethod
    def get_balance(self): pass

class RealBroker(PaperBroker):
    """
    Hybrid Broker: Tracks state locally but executes logic on Real API.
    WARNING: Real Money involved!
    """
    def __init__(self, api_key, api_secret, start_balance=0.0):
        # In real trading, balance comes from exchange, not init.
        # But we inherit to keep compatibility with Backtest engine logic if needed.
        super().__init__(start_balance=start_balance)
        self.api_key = api_key
        self.api_secret = api_secret
        self.live_mode = True
        
    def connect(self):
        print("Connecting to Real Exchange API...")
        # e.g. client = binance.Client(key, secret)
        pass
        
    def buy(self, ticker, price, timestamp, amount=None, pct_portfolio=0.10, context=None):
        # 1. Place Real Order
        print(f"🔊 REAL ORDER: BUY {ticker} (Simulated for Safety)")
        # exchange.create_market_buy_order(ticker, quantity)
        
        # 2. If success, log internally as usual
        return super().buy(ticker, price, timestamp, amount, pct_portfolio, context)

    def sell(self, ticker, price, timestamp, amount=None, pct_portfolio=1.0, context=None):
        # 1. Place Real Order
        print(f"🔊 REAL ORDER: SELL {ticker} (Simulated for Safety)")
        # exchange.create_market_sell_order(ticker, quantity)
        
        # 2. If success, log internally
        return super().sell(ticker, price, timestamp, amount, pct_portfolio, context)
