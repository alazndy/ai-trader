import yfinance as yf
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from strategies.features import add_all_features
from data.labeling import add_target
from execution.paper_broker import PaperBroker
from utils.logger import setup_logger
from config.settings import TICKERS, STOP_LOSS_PCT, SAFE_TICKER, SAFE_ALLOCATION_PCT, CURRENCY, ACTIVE_MODE, MARKET_CONFIG

logger = setup_logger("Backtest_Multi_Mode")

def fetch_and_prepare(ticker, mode, start_date, end_date):
    """Fetches and prepares data for a single ticker based on Mode."""
    
    # --- SPECIAL BIST LOGIC (VAULT PROXY) ---
    if mode == "BIST" and ("ALTIN" in ticker or "GLDTR" in ticker):
        logger.info(f"Synthesizing Gold/TRY (Proxy) for {ticker}...")
        try:
            gold = yf.download("GC=F", start=start_date, end=end_date, interval="1d", auto_adjust=False, progress=False)
            usd_try = yf.download("TRY=X", start=start_date, end=end_date, interval="1d", auto_adjust=False, progress=False)
            
            # Droplevels if needed
            if hasattr(gold.columns, 'nlevels') and gold.columns.nlevels > 1: gold.columns = gold.columns.droplevel(1)
            if hasattr(usd_try.columns, 'nlevels') and usd_try.columns.nlevels > 1: usd_try.columns = usd_try.columns.droplevel(1)
            
            common_idx = gold.index.intersection(usd_try.index)
            
            g_close = gold.loc[common_idx]['Close'] if 'Close' in gold.columns else gold.loc[common_idx]['Adj Close']
            u_close = usd_try.loc[common_idx]['Close'] if 'Close' in usd_try.columns else usd_try.loc[common_idx]['Adj Close']
            
            # Approx Gram Gold Calculation
            gram_gold_try = (g_close * u_close) / 31.1035
            
            df = pd.DataFrame(index=common_idx)
            df['Adj Close'] = gram_gold_try
            df['Close'] = gram_gold_try
            df['Volume'] = 1000000 # Fake volume
            return df
        except Exception as e:
            logger.error(f"Proxy failed: {e}")
            return pd.DataFrame()

    # --- STANDARD FETCH ---
    yf_ticker = ticker
    
    # Append .IS only for BIST stocks (and avoid doing it to Proxies/Crypto/US)
    if mode == "BIST" and ".IS" not in yf_ticker and "GC=F" not in yf_ticker and "TRY=X" not in yf_ticker:
        yf_ticker = f"{ticker}.IS"
        
    # logger.info(f"Fetching {yf_ticker} ({mode})...")
    
    try:
        df = yf.download(yf_ticker, start=start_date, end=end_date, interval="1d", auto_adjust=False, progress=False)
        
        if hasattr(df.columns, 'nlevels') and df.columns.nlevels > 1:
            df.columns = df.columns.droplevel(1)
            
        if 'Adj Close' not in df.columns and 'Close' in df.columns:
            df['Adj Close'] = df['Close']
            
        if df.empty:
            logger.warning(f"No data for {yf_ticker}")
            return pd.DataFrame()
            
        return df
    except Exception as e:
        logger.error(f"Error fetching {yf_ticker}: {e}")
        return pd.DataFrame()

def prepare_ai_data(df):
    """Adds features for AI models."""
    df = add_all_features(df).dropna()
    df = add_target(df)
    return df

def run_backtest(mode):
    config = MARKET_CONFIG[mode]
    SAFE_TICKER = config["SAFE_TICKER"]
    SAFE_ALLOCATION_PCT = config["SAFE_ALLOCATION"]
    TICKERS = config["TICKERS"]
    CURRENCY = config["CURRENCY"]
    
    logger.info(f"==========================================")
    logger.info(f"RUNNING BACKTEST: {mode} [{CURRENCY}]")
    logger.info(f"Vault: {SAFE_TICKER} | Satellites: {TICKERS}")
    logger.info(f"==========================================")
    
    start_date = "2022-01-01"
    end_date = "2025-12-31"
    split_date = "2023-01-01" # Test 2023-2025
    
    # 1. Fetch Safe Asset
    safe_df = fetch_and_prepare(SAFE_TICKER, mode, start_date, end_date)
    if safe_df.empty:
        logger.error(f"CRITICAL: Vault {SAFE_TICKER} missing. Skipping {mode}.")
        return

    # 2. Train Models
    models = {}
    test_datasets = {}
    from sklearn.ensemble import RandomForestClassifier
    features = ['RSI', 'SMA_50', 'SMA_200', 'macd', 'macd_signal', 'macd_hist', 'ATR']
    
    active_tickers = []
    
    for ticker in TICKERS:
        raw = fetch_and_prepare(ticker, mode, start_date, end_date)
        if raw.empty: continue
        
        # Check sufficient history
        if len(raw) < 200:
             logger.warning(f"{ticker}: Insufficient history.")
             continue
             
        df = prepare_ai_data(raw)
        train_df = df.loc[df.index < split_date]
        test_df = df.loc[df.index >= split_date]
        
        if train_df.empty or test_df.empty:
            logger.warning(f"{ticker}: Missing train or test data.")
            continue
            
        test_datasets[ticker] = test_df
        active_tickers.append(ticker)
        
        # Train
        model = RandomForestClassifier(n_estimators=100, min_samples_split=50, random_state=1)
        model.fit(train_df[features], train_df['Target'])
        models[ticker] = model

    if not active_tickers:
        logger.error("No active tickers trained. Aborting.")
        return

    # 3. Clock
    safe_test_df = safe_df.loc[safe_df.index >= split_date]
    master_clock = safe_test_df.index
    
    # 4. Sim
    broker = PaperBroker(initial_balance=100000.0)
    stock_alloc = (1.0 - SAFE_ALLOCATION_PCT) / len(active_tickers)
    
    for current_date in master_clock:
        current_prices = {}
        
        # Safe Price
        if current_date in safe_test_df.index:
            current_prices[SAFE_TICKER] = float(safe_test_df.loc[current_date]['Adj Close'])
        else: continue
            
        # Stock Prices
        for t in active_tickers:
            if current_date in test_datasets[t].index:
                current_prices[t] = float(test_datasets[t].loc[current_date]['Adj Close'])
        
        # Vault Rebalance
        broker.rebalance_vault(current_prices, SAFE_TICKER, SAFE_ALLOCATION_PCT)
        
        # Stop Loss (exclude Safe)
        dumps = broker.check_portfolio_safety(current_prices, STOP_LOSS_PCT)
        for t in dumps:
            if t != SAFE_TICKER and t in current_prices:
                broker.sell(t, current_prices[t], current_date)
                
        # AI Trading
        for t in active_tickers:
            if t not in current_prices: continue
            
            row = test_datasets[t].loc[current_date]
            model = models[t]
            pred = model.predict(row[features].values.reshape(1, -1))[0]
            price = current_prices[t]
            
            qty = broker.get_position_amt(t)
            
            if pred == 1 and qty == 0:
                broker.buy(t, price, current_date, pct_portfolio=stock_alloc)
            elif pred == 0 and qty > 0:
                broker.sell(t, price, current_date)
                
    # 5. Report
    final_prices = {}
    last_idx = master_clock[-1]
    if last_idx in safe_test_df.index: final_prices[SAFE_TICKER] = safe_test_df.loc[last_idx]['Adj Close']
    for t in active_tickers:
        if last_idx in test_datasets[t].index: final_prices[t] = test_datasets[t].loc[last_idx]['Adj Close']
    
    final_eq = broker.get_portfolio_value(final_prices)
    roi = ((final_eq - broker.initial_balance) / broker.initial_balance) * 100
    
    # Approx Benchmark (Vault B&H)
    v_start = safe_test_df.iloc[0]['Adj Close']
    v_end = float(final_prices[SAFE_TICKER])
    v_roi = (v_end - v_start)/v_start * 100

    print(f"\nRESULTS [{mode}]:")
    print(f"Final Balance: {final_eq:.2f} {CURRENCY}")
    print(f"ROI: {roi:.2f}%")
    print(f"Benchmark (Vault Only): {v_roi:.2f}%")
    if roi > v_roi: print("BEAT VAULT")
    else: print("UNDERPERFORMED VAULT")
    print("-" * 30)

if __name__ == "__main__":
    for m in ["BIST", "GLOBAL", "CRYPTO"]:
        run_backtest(m)
