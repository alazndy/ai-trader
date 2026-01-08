import pandas as pd
import numpy as np

def calculate_sma(series: pd.Series, window: int) -> pd.Series:
    """Calculates Simple Moving Average."""
    return series.rolling(window=window).mean()

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculates Relative Strength Index (RSI).
    Formula: 100 - (100 / (1 + RS))
    Where RS = Average Gain / Average Loss
    """
    delta = series.diff()
    # Create two series: one for gains (positive delta), one for losses (negative delta)
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(0) # Fill initial NaNs

def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Calculates MACD (Moving Average Convergence Divergence).
    Returns a DataFrame with 'macd', 'macd_signal', 'macd_hist'.
    """
    # EMA (Exponential Moving Average)
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return pd.DataFrame({
        'macd': macd_line,
        'macd_signal': signal_line,
        'macd_hist': histogram
    })

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculates Average True Range (ATR) for volatility.
    TR = Max(High-Low, Abs(High-PrevClose), Abs(Low-PrevClose))
    """
    high_low = df['High'] - df['Low']
    high_pc = (df['High'] - df['Close'].shift(1)).abs()
    low_pc = (df['Low'] - df['Close'].shift(1)).abs()
    
    # True Range is the max of the three
    tr = pd.concat([high_low, high_pc, low_pc], axis=1).max(axis=1)
    
    # ATR is the moving average of TR
    atr = tr.rolling(window=period).mean()
    return atr

def add_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
    """Adds Bollinger Bands (Upper, Middle, Lower) to the DataFrame."""
    df = df.copy() # Work on a copy to avoid modifying original df
    src = df['Adj Close'] # Assuming 'Adj Close' is the price source
    
    df['BB_Middle'] = src.rolling(window=period).mean()
    df['BB_Std'] = src.rolling(window=period).std()
    df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * std_dev)
    df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * std_dev)
    
    df.drop(['BB_Std'], axis=1, inplace=True) # Remove temporary std column
    return df

def add_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """Helper feature to add all indicators to the dataframe."""
    df = df.copy()
    
    # Price source usually Adj Close
    src = df['Adj Close']
    
    # SMA
    df['SMA_50'] = calculate_sma(src, 50)
    df['SMA_200'] = calculate_sma(src, 200)
    
    # RSI
    df['RSI'] = calculate_rsi(src)
    
    # MACD
    macd_df = calculate_macd(src)
    df = pd.concat([df, macd_df], axis=1)
    
    # ATR
    df['ATR'] = calculate_atr(df)
    
    return df
