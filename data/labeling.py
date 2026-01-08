import pandas as pd

def add_target(df: pd.DataFrame, threshold: float = 0.0) -> pd.DataFrame:
    """
    Creates the 'Target' column.
    Target = 1 if Tomorrow's Return > threshold, else 0.
    """
    df = df.copy()
    
    # Calculate next day's return: (Close[t+1] - Close[t]) / Close[t]
    # We use 'Close' or 'Adj Close'? Generally 'Adj Close' is better for returns.
    next_return = df['Adj Close'].pct_change().shift(-1)
    
    # Create Binary Target
    df['Target'] = (next_return > threshold).astype(int)
    
    # Drop the last row because it will have NaN target (can't predict unknown future)
    df = df.dropna()
    
    return df
