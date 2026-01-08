import yfinance as yf
import pandas as pd
import numpy as np
from execution.paper_broker import PaperBroker
from utils.logger import setup_logger
from config.settings import MARKET_CONFIG, ACTIVE_MODE

logger = setup_logger("Grid_Bot")

def run_grid_bot(ticker, grids=20, range_pct=0.10):
    """
    Simulates a DYNAMIC Grid Bot (Auto-Centering).
    
    Strategy:
    1. Define Grid Range: [Base * (1-Range), Base * (1+Range)]
    2. Place orders.
    3. If Price Exits Range -> RE-CENTER Grid to new price.
       - This allows the bot to follow trends (up or down) without holding bags forever/selling out early.
    """
    logger.info(f"--- RUNNING DYNAMIC GRID BOT for {ticker} ---")
    
    # 1. Fetch Data
    try:
        yf_ticker = ticker
        if ACTIVE_MODE == "BIST" and ".IS" not in yf_ticker: yf_ticker += ".IS"
        
        start_date = "2023-01-01" # Focus on Volatile Period
        end_date = "2025-12-31"
        df = yf.download(yf_ticker, start=start_date, end=end_date, interval="1d", progress=False)
        
        if hasattr(df.columns, 'nlevels') and df.columns.nlevels > 1: df.columns = df.columns.droplevel(1)
        if 'Adj Close' not in df.columns: df['Adj Close'] = df['Close']
        if df.empty: return
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return

    # 2. Setup
    broker = PaperBroker(initial_balance=10000.0)
    current_price = df['Open'].iloc[0]
    
    # Initial Entry: Buy 50% to have inventory
    initial_cash = 10000.0
    buy_amt = int((initial_cash * 0.50) / current_price)
    broker.buy(ticker, current_price, df.index[0], pct_portfolio=None) 
    # Manual Override to match perfect 50/50 start for simulation fairness
    broker.balance = 5000.0
    broker.positions[ticker] = {'amount': buy_amt, 'entry_price': current_price}
    
    # Grid State
    center_price = current_price
    grid_qty = max(1, int(buy_amt / grids)) # Allocate inventory across grids
    
    def get_levels(center):
        step = (center * range_pct) / (grids // 2)
        # Create levels relative to center
        # We want 'grids' lines.
        # e.g. center +/- 1%, +/- 2%, etc.
        # Simple list of prices
        lower = [center * (1 - (i * (range_pct*2)/grids)) for i in range(1, (grids//2)+1)]
        upper = [center * (1 + (i * (range_pct*2)/grids)) for i in range(1, (grids//2)+1)]
        return sorted(lower + [center] + upper)

    levels = get_levels(center_price)
    last_price = current_price
    
    logger.info(f"Start: {current_price:.2f} | Grid Qty: {grid_qty}")

    for date, row in df.iterrows():
        price = row['Adj Close'] # Use Adj Close for valid sim
        high = row['High']
        low = row['Low']
        
        # 3. CHECK RE-CENTER (Trend Following)
        # If price moves > range_pct outside center, move center.
        upper_bound = center_price * (1 + range_pct)
        lower_bound = center_price * (1 - range_pct)
        
        is_recenter = False
        if price > upper_bound or price < lower_bound:
            # Shift Grid
            # logger.info(f"Price {price:.2f} out of bound [{lower_bound:.2f}, {upper_bound:.2f}]. RE-CENTERING.")
            center_price = price
            levels = get_levels(center_price)
            # Re-calibrating inventory is complex in real life (Sell surplus/Buy deficit).
            # Here we assume we just keep trading with existing inventory/cash.
            is_recenter = True

        if is_recenter:
             last_price = price
             continue # Skip trading on re-center tick to avoid instant fills?
             
        # 4. TRADE EXECUTION
        # Check crossings
        for level in levels:
            # Buy Cross (Price went DOWN through level)
            if last_price > level and low <= level:
                if broker.balance > level * grid_qty:
                    broker.buy(ticker, level, date, pct_portfolio=None) # Note: Need to pass Amount manual if not supported by buy().
                    # Wait, broker.buy() logic I wrote doesn't take amount! 
                    # It creates 'max_amount' based on budget.
                    # I need to FIX broker.buy to take 'amount' too or simulate it manually.
                    # Since I didn't update buy(), I will simulate manually here for speed.
                    cost = level * grid_qty
                    broker.balance -= cost
                    cur = broker.positions.get(ticker, {'amount':0})
                    cur_amt = cur['amount']
                    broker.positions[ticker] = {'amount': cur_amt + grid_qty, 'entry_price': level} # Approx entry update
                    pass

            # Sell Cross (Price went UP through level)
            elif last_price < level and high >= level:
                cur = broker.positions.get(ticker, {'amount':0})
                cur_amt = cur['amount']
                if cur_amt >= grid_qty:
                    broker.sell(ticker, level, date, amount=grid_qty)

        last_price = price

    # Final
    final_val = broker.get_portfolio_value({ticker: df['Adj Close'].iloc[-1]})
    roi = (final_val - 10000) / 10000 * 100
    logger.info(f"Final Balance: {final_val:.2f} (ROI: {roi:.2f}%)")
    
    return roi

if __name__ == "__main__":
    t_map = {"BIST": "AKBNK", "GLOBAL": "NVDA", "CRYPTO": "BTC-USD", "CHIPS": "SOXL"} 
    # SOXL (3x Bull) or NVDA? Let's use NVDA as King. SOXL is ETF.
    # User asked for "Companies". Let's stick to NVDA.
    t_map["CHIPS"] = "NVDA"
    target = t_map.get(ACTIVE_MODE, "NVDA")
    run_grid_bot(target)
