import yfinance as yf
import pandas as pd
import numpy as np
from execution.paper_broker import PaperBroker
from utils.logger import setup_logger
from config.settings import MARKET_CONFIG, ACTIVE_MODE

logger = setup_logger("Pairs_Trading")

def fetch_pair_data(t1, t2):
    try:
        # Format tickers
        if ACTIVE_MODE == "BIST":
            if ".IS" not in t1: t1 += ".IS"
            if ".IS" not in t2: t2 += ".IS"
            
        start_date = "2022-01-01"
        end_date = "2025-12-31"
        data = yf.download([t1, t2], start=start_date, end=end_date, interval="1d", progress=False)['Adj Close']
        data.dropna(inplace=True)
        return data, t1, t2
    except Exception as e:
        logger.error(f"Error fetching pair {t1}/{t2}: {e}")
        return pd.DataFrame(), t1, t2

def run_pairs_strategy(ticker1, ticker2):
    logger.info(f"--- RUNNING PAIRS TRADING: {ticker1} vs {ticker2} ---")
    
    # 1. Fetch
    df, t1, t2 = fetch_pair_data(ticker1, ticker2)
    if df.empty: return

    # 2. Calculate Statistics
    # Ratio
    df['Ratio'] = df[t1] / df[t2]
    
    # Z-Score (Rolling)
    window = 20
    df['Mean'] = df['Ratio'].rolling(window=window).mean()
    df['Std'] = df['Ratio'].rolling(window=window).std()
    df['ZScore'] = (df['Ratio'] - df['Mean']) / df['Std']
    
    df.dropna(inplace=True)
    
    # 3. Simulate
    # Since we can't easily SHORT in this simple spot broker,
    # We will simulate a "Switch" strategy:
    # If Z > 1 (T1 expensive, T2 cheap) -> Hold T2
    # If Z < -1 (T1 cheap, T2 expensive) -> Hold T1
    # If Z ~ 0 -> Neutral (Cash or 50/50)
    
    broker = PaperBroker(initial_balance=10000.0)
    
    for date, row in df.iterrows():
        z = row['ZScore']
        p1 = row[t1]
        p2 = row[t2]
        
        # Check Positions
        q1 = broker.get_position_amt(t1)
        q2 = broker.get_position_amt(t2)
        
        # LOGIC
        if z > 1.5:
            # T1 is Expensive (Relative to T2).
            # Sell T1, Buy T2.
            if q1 > 0: broker.sell(t1, p1, date)
            if q2 == 0: broker.buy(t2, p2, date, pct_portfolio=0.9) # 90% allocation
            
        elif z < -1.5:
            # T1 is Cheap.
            # Sell T2, Buy T1.
            if q2 > 0: broker.sell(t2, p2, date)
            if q1 == 0: broker.buy(t1, p1, date, pct_portfolio=0.9)
            
        elif abs(z) < 0.5:
            # Reverted to Mean. Exit all or go 50/50?
            # Let's say we exit to Cash to lock profit.
            if q1 > 0: broker.sell(t1, p1, date)
            if q2 > 0: broker.sell(t2, p2, date)

    # Report
    final_prices = {t1: df[t1].iloc[-1], t2: df[t2].iloc[-1]}
    final_val = broker.get_portfolio_value(final_prices)
    roi = (final_val - 10000) / 10000 * 100
    logger.info(f"Final Balance: {final_val:.2f} (ROI: {roi:.2f}%)")
    
if __name__ == "__main__":
    # Select Pair
    if ACTIVE_MODE == "BIST":
        t1, t2 = "AKBNK", "GARAN" # Banking
    elif ACTIVE_MODE == "CRYPTO":
        t1, t2 = "BTC-USD", "ETH-USD"
    else:
        t1, t2 = "NVDA", "AMD"
        
    run_pairs_strategy(t1, t2)
