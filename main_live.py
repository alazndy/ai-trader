import time
import yfinance as yf
import pandas as pd
from datetime import datetime

from utils.logger import setup_logger
from utils.market_helpers import is_market_open
from utils.notifier import send_notification
from strategies.features import add_all_features
from data.labeling import add_target
from execution.paper_broker import PaperBroker
from config.settings import TICKERS, CHECK_INTERVAL_SECONDS, TRAINING_PERIOD, STOP_LOSS_PCT, KILL_SWITCH_PCT, SAFE_TICKER, SAFE_ALLOCATION_PCT, CURRENCY, ACTIVE_MODE

logger = setup_logger("Main_Live_Multi")

# ... (fetch_and_train_model stays same)
# ... (get_latest_prediction stays same)

def main():
    logger.info(f"--- AI TRADER BOT STARTED (Mode: {ACTIVE_MODE}) ---")
    logger.info(f"Tickers: {TICKERS}")
    logger.info(f"Vault: {SAFE_TICKER} ({SAFE_ALLOCATION_PCT*100}%) | Currency: {CURRENCY}")
    
    # Send Startup Notification
    send_notification("AI Trader Started 🚀", 
                      f"Mode: {ACTIVE_MODE}\nVault: {SAFE_TICKER}\nActive Tickers: {len(TICKERS)}\nCurrency: {CURRENCY}")

    # 1. Initialize Broker
    broker = PaperBroker()
    broker.load_state() 
    
    # 2. Train Models (One per Ticker)
    models = {}
    feature_sets = {}
    
    # Track Start of Day Balance for Kill Switch (Reset this daily in real logic, currently per session)
    # Ideally we load this from a file too or just use current balance as baseline for the session.
    start_of_session_equity = broker.get_portfolio_value({}) # Approx
    logger.info(f"Session Start Equity: {start_of_session_equity:.2f}")

    for ticker in TICKERS:
        model, feats = fetch_and_train_model(ticker)
        if model:
            models[ticker] = model
            feature_sets[ticker] = feats
        else:
            logger.error(f"Skipping {ticker} due to training failure.")
            
    logger.info(f"Ready. {len(models)} models active.")

    # 3. Infinite Loop
    try:
        while True:
            now = datetime.now()
            logger.info(f"--- Scan Cycle: {now.strftime('%H:%M')} ---")
            
            # A. Phase 1: Real-Time Safety Check (Crucial)
            # Fetch prices (Tickers + Safe Ticker)
            all_tickers = TICKERS + [SAFE_TICKER]
            current_prices = {}
            for t in all_tickers:
                try:
                    df = yf.download(t, period="1d", interval="1d", progress=False)
                    if not df.empty:
                        price = df['Adj Close'].iloc[-1]
                        if isinstance(price, pd.Series): price = price.iloc[0]
                        current_prices[t] = float(price)
                except:
                    pass
            
            # Kill Switch Check
            current_equity = broker.get_portfolio_value(current_prices)
            drawdown = (start_of_session_equity - current_equity) / start_of_session_equity
            
            if drawdown > KILL_SWITCH_PCT:
                msg = f"KILL SWITCH ACTIVATED! Loss {drawdown*100:.2f}% > {KILL_SWITCH_PCT*100}%"
                logger.error(msg)
                send_notification("EMERGENCY STOP", msg, priority="urgent")
                break # TERMINATE BOT
            
            # VAULT Rebalancing (New Phase 1.5)
            # Ensure we hold Gold
            broker.rebalance_vault(current_prices, SAFE_TICKER, SAFE_ALLOCATION_PCT)

            # Stop Loss Check
            tickers_to_dump = broker.check_portfolio_safety(current_prices, stop_loss_pct=STOP_LOSS_PCT)
            for ticker in tickers_to_dump:
                if ticker == SAFE_TICKER: continue # Never Stop-Loss the Vault? Or should we? Assuming Vault is safe.
                
                if broker.sell(ticker, current_prices[ticker], now):
                    msg = f"STOP LOSS: Sold {ticker} @ {current_prices[ticker]:.2f}"
                    send_notification("STOP LOSS", msg, priority="high")
                    broker.save_state()

            # B. Phase 2: Regular Trading Logic
            # Adjusted target allocation: 
            # If 50% is Gold, remaining 50% is shared by Tickers.
            # So if 5 tickers, each gets 10% of Total, OR 20% of 'Active Equity'.
            # PaperBroker.buy uses a confusing sizing logic currently (based on initial_balance in some concepts).
            # Let's set pct_portfolio such that it respects the remaining cash.
            # Simpler: Total Equity * (1 - Safe_Alloc) * (1/N)
            active_equity_ratio = (1.0 - SAFE_ALLOCATION_PCT)
            stock_weight = active_equity_ratio / len(TICKERS) # e.g. 0.5 / 5 = 0.10 (10% each)
            
            for ticker in TICKERS:
                if ticker not in models: continue
                
                # If we just stop-lossed it, maybe don't buy immediately? 
                # (Simple logic: if pred says buy, we buy again? Risk of churn. Let's ignore for now.)
                
                model = models[ticker]
                feats = feature_sets[ticker]
                
                pred, price, date = get_latest_prediction(model, feats, ticker)
                
                if pred is not None:
                    current_qty_data = broker.positions.get(ticker, {'amount': 0})
                    current_qty = current_qty_data['amount'] if isinstance(current_qty_data, dict) else current_qty_data
                    
                    if pred == 1 and current_qty == 0:
                        # BUY
                        if broker.buy(ticker, price, date, pct_portfolio=stock_weight):
                            msg = f"BUY {ticker} @ {price:.2f}"
                            logger.info(msg)
                            send_notification("TRADE SIGNAL", msg, priority="high")
                            broker.save_state()
                            
                    elif pred == 0 and current_qty > 0:
                        # SELL
                        if broker.sell(ticker, price, date):
                            msg = f"SELL {ticker} @ {price:.2f}"
                            logger.info(msg)
                            send_notification("TRADE SIGNAL", msg, priority="high")
                            broker.save_state()
            
            logger.info(f"Equity: {current_equity:.2f}. Sleep {CHECK_INTERVAL_SECONDS}s.")
            time.sleep(CHECK_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
        send_notification("AI Trader Stopped", "Manual shutdown.")

if __name__ == "__main__":
    main()
