import pandas as pd
from utils.logger import setup_logger

logger = setup_logger("Data_Validator")

def validate_dataframe(df):
    """
    Performs critical checks on the OHLCV dataframe.
    
    Args:
        df (pd.DataFrame): The stock data dataframe.
        
    Returns:
        bool: True if data is valid enough to proceed, False otherwise.
    """
    if df is None or df.empty:
        logger.error("DataFrame is empty or None.")
        return False

    # 1. Check for Required Columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing columns: {missing_cols}")
        return False

    # 2. Check for NaNs
    nan_counts = df[required_cols].isna().sum()
    if nan_counts.sum() > 0:
        logger.warning(f"Found NaNs in data:\n{nan_counts[nan_counts > 0]}")
        # In a real scenario, we might drop or fill them.
        # For now, just logging it.

    # 3. Check for Zero Volume (Untradable days)
    zero_vol_days = (df['Volume'] == 0).sum()
    if zero_vol_days > 0:
        logger.warning(f"Found {zero_vol_days} days with 0 Volume.")

    # 4. Check Adjusted Close validity
    # Adj Close shoud generally be <= High (mostly). 
    # If Split happened, it might be vastly different, which is what we want.
    # Just checking it's positive.
    if (df['Adj Close'] <= 0).any():
        logger.error("Found non-positive Adjusted Close prices!")
        return False

    logger.info("Data validation passed with warnings (if any).")
    return True
