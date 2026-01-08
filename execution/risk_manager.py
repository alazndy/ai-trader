from utils.logger import setup_logger

logger = setup_logger("Risk_Manager")

class RiskManager:
    def __init__(self, commission_rate=0.002, slippage_rate=0.001):
        """
        Args:
            commission_rate (float): Exchange fee (default 0.2% for BIST).
            slippage_rate (float): Est. price impact/spread (default 0.1%).
        """
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate

    def calculate_cost(self, amount: float, price: float) -> float:
        """Calculates total commission cost for a trade."""
        return amount * price * self.commission_rate

    def apply_slippage(self, price: float, mode: str) -> float:
        """
        Adjusts price to simulating bad execution.
        Buy -> Pay more (Price * 1+slippage)
        Sell -> Get less (Price * 1-slippage)
        """
        if mode.lower() == 'buy':
            return price * (1 + self.slippage_rate)
        elif mode.lower() == 'sell':
            return price * (1 - self.slippage_rate)
        else:
            return price

    def check_stop_loss(self, current_price, entry_price, threshold=0.03):
        """
        Returns True if Stop-Loss is triggered.
        Stop Trigger: Current Price < Entry Price * (1 - threshold)
        """
        if entry_price == 0:
            return False
            
        return current_price < (entry_price * (1 - threshold))
