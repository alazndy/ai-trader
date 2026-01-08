import yfinance as yf
from utils.logger import setup_logger
from utils.market_helpers import is_market_open, get_current_time
from data.validation import validate_dataframe

# 1. Setup Logging
logger = setup_logger("Main_Paper_Trader")

def main():
    logger.info("Starting AI Trader Bot - Phase 1 MVP")

    # 2. Market Status Check
    now = get_current_time()
    market_open = is_market_open(now)
    logger.info(f"Current BIST Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Is Market Open? {'YES' if market_open else 'NO'}")

    # 3. Data Fetching
    ticker = "THYAO.IS"
    logger.info(f"Fetching 1 year of data for {ticker}...")

    try:
        # Download data
        # auto_adjust=False ensures we get 'Adj Close' column explicitly separate from 'Close'
        df = yf.download(ticker, period="1y", interval="1d", auto_adjust=False, progress=False)

        # Handle MultiIndex columns (yfinance > 0.2.x common issue)
        if hasattr(df.columns, 'nlevels') and df.columns.nlevels > 1:
            # Drop the Ticker level (level 1)
            df.columns = df.columns.droplevel(1)
        
        # 4. Data Validation
        if validate_dataframe(df):
            logger.info("Data Fetch Successful. Showing last 5 rows:")
            # Use print for the DataFrame table to avoid log clutter, or log it
            print(df.tail())
            
            last_price = df['Adj Close'].iloc[-1]
            logger.info(f"Last Adjusted Price: {last_price}")
        else:
            logger.error("Data validation failed.")

    except Exception as e:
        logger.exception("An error occurred during execution:")

if __name__ == "__main__":
    main()
