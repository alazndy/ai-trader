from execution.paper_broker import PaperBroker
from execution.risk_manager import RiskManager
from utils.logger import setup_logger

logger = setup_logger("Test_Safety")

def test_stop_loss():
    logger.info("Testing Stop-Loss Logic...")
    
    # 1. Setup
    broker = PaperBroker()
    broker.risk_manager = RiskManager()
    
    # Manually inject a position
    # Bought THYAO at 100.00
    broker.positions['THYAO.IS'] = {'amount': 100, 'entry_price': 100.0}
    
    # 2. Case A: Price drops to 98 (2% Loss) -> Should HOLD (Threshold 3%)
    logger.info("Case A: Price 98 (2% Drop)")
    current_prices = {'THYAO.IS': 98.0}
    to_sell = broker.check_portfolio_safety(current_prices, stop_loss_pct=0.03)
    if not to_sell:
        logger.info("✅ Case A Passed: Held position.")
    else:
        logger.error(f"❌ Case A Failed: Sold {to_sell}")

    # 3. Case B: Price drops to 96 (4% Loss) -> Should SELL
    logger.info("Case B: Price 96 (4% Drop)")
    current_prices = {'THYAO.IS': 96.0}
    to_sell = broker.check_portfolio_safety(current_prices, stop_loss_pct=0.03)
    if 'THYAO.IS' in to_sell:
        logger.info("✅ Case B Passed: Triggered Sale.")
    else:
        logger.error("❌ Case B Failed: Did not trigger.")

if __name__ == "__main__":
    test_stop_loss()
