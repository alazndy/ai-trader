import yfinance as yf
import pandas as pd
import numpy as np
from config.settings import MARKET_CONFIG
import time

def fetch_data(tickers, period="1y"):
    """
    Fetches daily adjusted close prices for the given tickers.
    """
    if not tickers:
        return pd.DataFrame()
    
    print(f"Fetching data for: {', '.join(tickers)}...")
    try:
        # Fetch data
        df = yf.download(tickers, period=period, interval="1d", progress=False)
        
        # Debug: Print columns to understand structure
        # print(f"Columns: {df.columns}")
        
        if 'Adj Close' in df.columns:
            data = df['Adj Close']
        elif 'Close' in df.columns:
            data = df['Close']
        else:
            print(f"Unavailable columns. Returned: {df.columns}")
            return pd.DataFrame()

        # If single ticker and data is Series, convert to DF with ticker name
        if isinstance(data, pd.Series):
            data = data.to_frame(name=tickers[0])
            
        # If it's a single stock DF with 'Adj Close' as column name (not MultiIndex)
        # We need to make sure columns are Tickers
        if len(tickers) == 1 and not isinstance(data.columns, pd.MultiIndex):
             if data.shape[1] == 1 and data.columns[0] == 'Adj Close':
                 data.columns = tickers
        
        # Drop columns with all NaNs
        data.dropna(axis=1, how='all', inplace=True)
        # Forward fill then backward fill to handle missing days
        data.fillna(method='ffill', inplace=True)
        data.fillna(method='bfill', inplace=True)
        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def analyze_correlation(df, threshold=0.8):
    """
    Finds pairs with correlation higher than threshold.
    """
    corr_matrix = df.corr()
    high_corr_pairs = []
    
    # Iterate over the correlation matrix
    columns = corr_matrix.columns
    for i in range(len(columns)):
        for j in range(i + 1, len(columns)):
            t1 = columns[i]
            t2 = columns[j]
            score = corr_matrix.iloc[i, j]
            
            if abs(score) >= threshold:
                high_corr_pairs.append((t1, t2, score))
                
    return high_corr_pairs

def analyze_lead_lag(df, lag=1, threshold=0.5):
    """
    Finds potential lead-lag relationships.
    Checks if Ticker1(t-lag) is correlated with Ticker2(t).
    """
    lead_lag_pairs = []
    columns = df.columns
    
    for t1 in columns:
        for t2 in columns:
            if t1 == t2: continue
            
            # Create lagged series for t1
            t1_lagged = df[t1].shift(lag)
            
            # Calculate correlation between standard t2 and lagged t1
            # We need to align them, pandas does this automatically with corr() if passed properly
            # Or manually:
            valid_idx = t1_lagged.notna()
            if valid_idx.sum() < 30: # Need enough data points
                continue
                
            score = t1_lagged.corr(df[t2])
            
            if abs(score) >= threshold:
                lead_lag_pairs.append((t1, t2, lag, score))
                
    return lead_lag_pairs

def get_best_pairs(market_config_override=None):
    """
    Analyzes markets and returns best correlated and lead-lag pairs.
    Returns a dict with 'correlation' and 'lead_lag' lists.
    """
    results = {
        "correlation": [], # (t1, t2, score)
        "lead_lag": []     # (leader, follower, lag, score)
    }
    
    # Use provided config or all
    configs_to_check = market_config_override if market_config_override else MARKET_CONFIG
    
    for market, config in configs_to_check.items():
        # print(f"Analyzing {market}...")
        tickers = config.get("TICKERS", [])
        if not tickers: continue
        
        data = fetch_data(tickers)
        if data.empty: continue
        
        # 1. Correlation
        corrs = analyze_correlation(data, threshold=0.85)
        results["correlation"].extend(corrs)
        
        # 2. Lead-Lag
        leads = analyze_lead_lag(data, lag=1, threshold=0.75) # Higher threshold for auto-trading
        results["lead_lag"].extend(leads)
        
    return results

def main():
    print("--- Finding Consecutive Stocks Analysis ---")
    
    # Just use the helper function but print specifics for the User
    results = get_best_pairs(MARKET_CONFIG)
    
    print("\n[HIGH CORRELATION] (Threshold: 0.85)")
    for t1, t2, score in sorted(results["correlation"], key=lambda x: x[2], reverse=True):
        print(f"  {t1} <-> {t2} : {score:.4f}")
        
    print("\n[LEAD-LAG] (Lag: 1 Day, Threshold: 0.75)")
    for t1, t2, lag, score in sorted(results["lead_lag"], key=lambda x: x[3], reverse=True):
        print(f"  {t1} LEADS {t2} : {score:.4f}")

    print("\n--- Done ---")

if __name__ == "__main__":
    main()
