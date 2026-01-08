import yfinance as yf
import pandas as pd
from strategies.features import add_all_features, add_bollinger_bands
from execution.paper_broker import PaperBroker
from utils.logger import setup_logger
from config.settings import MARKET_CONFIG, ACTIVE_MODE

logger = setup_logger("Mean_Reversion")

def fetch_data(ticker, active_mode):
    """Fetches data based on mode."""
    # Logic similar to main_backtest logic (proxy etc) but let's keep it simple for now
    # We just fetch the ticker.
    try:
        if active_mode == "BIST" and ".IS" not in ticker: ticker += ".IS"
        # 2022-2025 Benchmark
        start_date = "2022-01-01"
        end_date = "2025-12-31"
        df = yf.download(ticker, start=start_date, end=end_date, interval="1d", progress=False)
        if hasattr(df.columns, 'nlevels') and df.columns.nlevels > 1: df.columns = df.columns.droplevel(1)
        if 'Adj Close' not in df.columns and 'Close' in df.columns: df['Adj Close'] = df['Close']
        return df
    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        return pd.DataFrame()

def run_strategy(ticker):
    logger.info(f"Running MEAN REVERSION on {ticker}...")
    
    # 1. Fetch
    df = fetch_data(ticker, ACTIVE_MODE)
    if df.empty or len(df) < 50:
        logger.warning("Insufficient data.")
        return

    # 2. Add Features
    df = add_all_features(df) # Adds RSI
    df = add_bollinger_bands(df)
    df.dropna(inplace=True)
    
    # 3. Simulation
    broker = PaperBroker(initial_balance=10000.0)
    
    for date, row in df.iterrows():
        price = row['Adj Close']
        rsi = row['RSI']
        bb_upper = row['BB_Upper']
        bb_lower = row['BB_Lower']
        
        # Position Check
        if isinstance(broker.positions.get(ticker), dict):
             qty = broker.positions[ticker]['amount']
        else:
             qty = broker.positions.get(ticker, 0)
        
        # LOGIC
        # BUY: Price below Lower Band (Extended downside) AND RSI < 30 (Oversold)
        if price < bb_lower and rsi < 30 and qty == 0:
            logger.info(f"SIGNAL: BUY {ticker} @ {price:.2f} (RSI: {rsi:.1f}, BB_Low: {bb_lower:.2f})")
            broker.buy(ticker, price, date, pct_portfolio=1.0) # All in for single ticker test
            
        # SELL: Price above Upper Band (Extended upside) OR RSI > 70 (Overbought)
        elif (price > bb_upper or rsi > 70) and qty > 0:
            logger.info(f"SIGNAL: SELL {ticker} @ {price:.2f} (RSI: {rsi:.1f}, BB_Up: {bb_upper:.2f})")
            broker.sell(ticker, price, date)

    # Report
    final_val = broker.get_portfolio_value({ticker: df['Adj Close'].iloc[-1]})
    roi = (final_val - 10000) / 10000 * 100
    logger.info(f"Result for {ticker}: ROI {roi:.2f}%")
    return roi

if __name__ == "__main__":
    # Test on the current active Satellite tickers
    config = MARKET_CONFIG[ACTIVE_MODE]
    tickers = config["TICKERS"]
    
    logger.info(f"--- MEAN REVERSION BACKTEST ({ACTIVE_MODE}) ---")
    for t in tickers:
        run_strategy(t)
