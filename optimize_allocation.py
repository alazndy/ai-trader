import yfinance as yf
import pandas as pd
from strategies.features import add_all_features
from execution.paper_broker import PaperBroker
from utils.logger import setup_logger
from config.settings import MARKET_CONFIG

logger = setup_logger("Allocation_Optimizer")

INFLATION_DATA = {
    "TL": {2022: 72.3, 2023: 64.8, 2024: 45.0, 2025: 30.0},
    "USD": {2022: 6.5, 2023: 3.4, 2024: 3.0, 2025: 2.5}
}

def fetch_and_prepare(ticker, mode, start_date, end_date):
    if mode == "BIST" and ("ALTIN" in ticker or "GLDTR" in ticker):
        try:
            gold = yf.download("GC=F", start=start_date, end=end_date, interval="1d", progress=False)['Close']
            usd = yf.download("TRY=X", start=start_date, end=end_date, interval="1d", progress=False)['Close']
            if gold.empty or usd.empty: return pd.DataFrame()
            common_idx = gold.index.intersection(usd.index)
            gold = gold.loc[common_idx]
            usd = usd.loc[common_idx]
            vals = (gold * usd) / 31.1035
            df = pd.DataFrame(vals, index=common_idx, columns=['Adj Close'])
            return df
        except: return pd.DataFrame()

    yf_ticker = ticker
    if mode == "BIST" and ".IS" not in yf_ticker: yf_ticker += ".IS"
    try:
        df = yf.download(yf_ticker, start=start_date, end=end_date, interval="1d", progress=False)
        if hasattr(df.columns, 'nlevels') and df.columns.nlevels > 1: df.columns = df.columns.droplevel(1)
        if 'Adj Close' not in df.columns: df['Adj Close'] = df['Close']
        return df
    except: return pd.DataFrame()

def run_optimization(mode):
    config = MARKET_CONFIG[mode]
    currency = config["CURRENCY"]
    logger.info(f"Optimizing Allocation for {mode}...")
    
    start_date = "2022-01-01"
    end_date = "2025-12-31"
    
    # Data Setup
    safe_ticker = config["SAFE_TICKER"]
    tickers = config["TICKERS"]
    
    safe_df = fetch_and_prepare(safe_ticker, mode, start_date, end_date)
    active_data = {}
    for t in tickers:
        df = fetch_and_prepare(t, mode, start_date, end_date)
        if not df.empty:
            df = add_all_features(df).dropna()
            active_data[t] = df
            
    clock = safe_df.index
    years = [2022, 2023, 2024, 2025]
    
    # Ratios to test
    ratios = [0.0, 0.20, 0.40, 0.60, 0.80, 1.0]
    
    results = {}
    
    for ratio in ratios:
        # print(f"Testing Ratio: {ratio*100:.0f}% Vault")
        broker = PaperBroker(initial_balance=100000.0)
        
        for date in clock:
            prices = {safe_ticker: safe_df.loc[date]['Adj Close']}
            for t, df in active_data.items():
                if date in df.index: prices[t] = df.loc[date]['Adj Close']
            
            # REBALANCE VAULT to target Ratio
            broker.rebalance_vault(prices, safe_ticker, ratio)
            
            # Active Trading (Trend Logic)
            # Only use remaining capital (1 - ratio) actually implied by rebalance logic
            stock_count = len(tickers)
            
            # Note: PaperBroker rebalances vault to 'ratio' of TOTAL Portfolio.
            # So remaining is (1-ratio).
            # We must verify we have Cash to buy active stocks.
            
            for t in tickers:
                if t not in prices or t not in active_data: continue
                price = prices[t]
                row = active_data[t].loc[date]
                
                signal = 1 if price > row['SMA_50'] else 0
                qty = broker.get_position_amt(t)
                
                if signal == 1 and qty == 0:
                     # Buy Logic
                     # Allocation: If 20% Vault, 80% Active.
                     # Each Stock gets (1 - ratio) / N
                     active_pct = (1.0 - ratio) / stock_count
                     if active_pct > 0:
                         broker.buy(t, price, date, pct_portfolio=active_pct)
                elif signal == 0 and qty > 0:
                    broker.sell(t, price, date)
                    
        # Final Real Calc
        last_price_map = {}
        last_date = clock[-1]
        active_tickers = [safe_ticker] + tickers
        for t in active_tickers:
            if t == safe_ticker: df = safe_df
            elif t in active_data: df = active_data[t]
            else: continue
            if last_date in df.index: last_price_map[t] = df.loc[last_date]['Adj Close']
            else: last_price_map[t] = df.iloc[-1]['Adj Close']
            
        nominal = broker.get_portfolio_value(last_price_map)
        
        # Cumulative Inflation Index
        cpi_index = 100.0
        for y in years:
            cpi_index *= (1 + INFLATION_DATA[currency][y]/100)
            
        real_purchasing_power = (nominal / cpi_index) * 100
        results[ratio] = real_purchasing_power
        
    print(f"\nOPTIMIZATION RESULTS: {mode} (Base 100k)")
    print(f"{'Vault %':<10} | {'Active %':<10} | {'Real Wealth':<15}")
    print("-" * 45)
    
    best_ratio = 0
    best_val = -999999
    
    for r in ratios:
        val = results[r]
        if val > best_val:
            best_val = val
            best_ratio = r
        print(f"{r*100:>3.0f}%      | {(1-r)*100:>3.0f}%      | {val:,.0f}")
        
    print(f"SWEET SPOT: {best_ratio*100:.0f}% Vault ({best_val:,.0f} Real)")

if __name__ == "__main__":
    for m in ["BIST", "GLOBAL", "CRYPTO"]:
        run_optimization(m)
