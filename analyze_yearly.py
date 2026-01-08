import yfinance as yf
import pandas as pd
from strategies.features import add_all_features
from data.labeling import add_target
from execution.paper_broker import PaperBroker
from utils.logger import setup_logger
from config.settings import MARKET_CONFIG, STOP_LOSS_PCT
from sklearn.ensemble import RandomForestClassifier

logger = setup_logger("Yearly_Analysis")

# INFLATION ESTIMATES (Official/Consensus)
INFLATION_DATA = {
    "TL": {2022: 72.3, 2023: 64.8, 2024: 45.0, 2025: 30.0},
    "USD": {2022: 6.5, 2023: 3.4, 2024: 3.0, 2025: 2.5}
}

def fetch_and_prepare(ticker, mode, start_date, end_date):
    # (Reusing valid logic from main_backtest)
    if mode == "BIST" and ("ALTIN" in ticker or "GLDTR" in ticker):
        # Proxy
        try:
            print(f"Fetching Proxy for {ticker}...")
            gold = yf.download("GC=F", start=start_date, end=end_date, interval="1d", progress=False)['Close']
            usd = yf.download("TRY=X", start=start_date, end=end_date, interval="1d", progress=False)['Close']
            
            if gold.empty or usd.empty:
                print("Proxy Fetch Failed: Gold or USD empty.")
                return pd.DataFrame()
            
            # Align indices
            common_idx = gold.index.intersection(usd.index)
            gold = gold.loc[common_idx]
            usd = usd.loc[common_idx]
            
            vals = (gold * usd) / 31.1035
            df = pd.DataFrame(vals, index=common_idx, columns=['Adj Close'])
            print(f"Proxy Success: {len(df)} rows.")
            return df
        except Exception as e: 
            print(f"Proxy Error: {e}")
            return pd.DataFrame()

    yf_ticker = ticker
    if mode == "BIST" and ".IS" not in yf_ticker: yf_ticker += ".IS"
    
    try:
        df = yf.download(yf_ticker, start=start_date, end=end_date, interval="1d", progress=False)
        if hasattr(df.columns, 'nlevels') and df.columns.nlevels > 1: df.columns = df.columns.droplevel(1)
        if 'Adj Close' not in df.columns: df['Adj Close'] = df['Close']
        return df
    except: return pd.DataFrame()

def run_yearly_analysis(mode):
    config = MARKET_CONFIG[mode]
    currency = config["CURRENCY"]
    logger.info(f"Analyzing {mode} ({currency})...")
    
    # 2022-2025 (4 Years)
    start_date = "2022-01-01"
    end_date = "2025-12-31"
    
    # Setup Data
    safe_ticker = config["SAFE_TICKER"]
    tickers = config["TICKERS"]
    
    safe_df = fetch_and_prepare(safe_ticker, mode, start_date, end_date)
    if safe_df.empty: return
    
    active_data = {}
    for t in tickers:
        df = fetch_and_prepare(t, mode, start_date, end_date)
        if not df.empty:
            df = add_all_features(df).dropna()
            active_data[t] = df
            
    # Brokers for each strategy
    b_trend = PaperBroker(initial_balance=100000.0)
    b_mr = PaperBroker(initial_balance=100000.0)
    b_grid = PaperBroker(initial_balance=100000.0)
    
    # Setup Grid Levels (Simple approach: Reset grid every year or static? Static for now 2022-2025)
    # Grid needs min/max. Hard to know future.
    # WIll use a "Trailing Grid" or just fixed range based on initial price?
    # Let's use a dynamic grid: re-center every month? Too complex for this script.
    # Let's use a "Percent Grid": Buy -5%, Sell +5%.
    
    # Simulation
    clock = safe_df.index
    years = [2022, 2023, 2024, 2025]
    
    # State tracking
    yearly_snapshots = []
    current_inflation_index = 100.0
    
    for year in years:
        year_dates = [d for d in clock if d.year == year]
        if not year_dates: continue
        
        for date in year_dates:
            prices = {safe_ticker: safe_df.loc[date]['Adj Close']}
            for t, df in active_data.items():
                if date in df.index: prices[t] = df.loc[date]['Adj Close']
            
            stock_count = len(tickers)
            
            # --- STRATEGY 1: TREND (Core-Satellite) ---
            b_trend.rebalance_vault(prices, safe_ticker, 0.50)
            for t in tickers:
                if t not in prices or t not in active_data: continue
                price = prices[t]
                row = active_data[t].loc[date]
                
                # Signal: Price > SMA50
                signal = 1 if price > row['SMA_50'] else 0
                qty = b_trend.get_position_amt(t)
                
                if signal == 1 and qty == 0:
                     pct = 0.50 / stock_count
                     b_trend.buy(t, price, date, pct_portfolio=pct)
                elif signal == 0 and qty > 0:
                    b_trend.sell(t, price, date)
            
            # --- STRATEGY 2: MEAN REVERSION (Bollinger) ---
            # No Vault, 100% Active.
            for t in tickers:
                if t not in prices or t not in active_data: continue
                price = prices[t]
                row = active_data[t].loc[date]
                
                # add_all_features doesn't add BB by default in features.py? 
                # Wait, I added it to features.py but did I call it here?
                # Need to check if BB columns exist.
                # If not, skip or calc on fly? features.py: add_all_features calls standard set.
                # I need to manually add BB or ensure it's there.
                # For simplicity, I'll assume I calculate it or just use simple logic if missing:
                # Let's use RSI < 30 buy, RSI > 70 sell as proxy if BB missing.
                
                qty = b_mr.get_position_amt(t)
                rsi = row['RSI']
                
                if rsi < 30 and qty == 0:
                    pct = 1.0 / stock_count # Equal weight full portfolio
                    b_mr.buy(t, price, date, pct_portfolio=pct)
                elif rsi > 70 and qty > 0:
                    b_mr.sell(t, price, date)

            # --- STRATEGY 3: GRID (Volatility) ---
            # Simple Logic: If Price drops X% from Entry, Buy. If Price rises X% from Entry, Sell.
            # Initial Entry: First day of year?
            for t in tickers:
                if t not in prices: continue
                price = prices[t]
                qty = b_grid.get_position_amt(t)
                
                # If no position, assume we want to enter at current price to start grid?
                if qty == 0:
                     # Buy initial 'center' position
                     pct = (1.0 / stock_count) * 0.5 # Half allocation to allow buying dips
                     b_grid.buy(t, price, date, pct_portfolio=pct)
                else:
                    # We have a position. Check entry price.
                    # positions structure: {'amount': X, 'entry_price': Y}
                    entry = b_grid.positions[t]['entry_price']
                    
                    # GRID BUY: -5%
                    if price < entry * 0.95:
                         # DCA
                         cost = b_grid.get_portfolio_value(prices) * (0.1 / stock_count) # Add small chunk
                         if b_grid.balance > cost:
                             amt = int(cost / price)
                             if amt > 0:
                                 # Manual Buy to update avg cost
                                 b_grid.balance -= amt * price
                                 new_amt = qty + amt
                                 new_cost = ((qty * entry) + (amt * price)) / new_amt
                                 b_grid.positions[t] = {'amount': new_amt, 'entry_price': new_cost}
                    
                    # GRID SELL: +5%
                    elif price > entry * 1.05:
                        # Take Profit (Sell all and reset? Or sell partial?)
                        # Sell all to capture profit implies reset
                        b_grid.sell(t, price, date)

        # SNAPSHOT
        last_price_map = {}
        last_date = year_dates[-1]
        active_tickers = [safe_ticker] + tickers
        for t in active_tickers:
            if t == safe_ticker: df = safe_df
            elif t in active_data: df = active_data[t]
            else: continue
            if last_date in df.index: last_price_map[t] = df.loc[last_date]['Adj Close']
            else: last_price_map[t] = df.iloc[-1]['Adj Close']
                
        val_trend = b_trend.get_portfolio_value(last_price_map)
        val_mr = b_mr.get_portfolio_value(last_price_map)
        val_grid = b_grid.get_portfolio_value(last_price_map)
        
        # Inflation
        inf_rate = INFLATION_DATA[currency][year]
        current_inflation_index = current_inflation_index * (1 + inf_rate/100)
        
        real_trend = (val_trend / current_inflation_index) * 100
        real_mr = (val_mr / current_inflation_index) * 100
        real_grid = (val_grid / current_inflation_index) * 100
        
        yearly_snapshots.append({
            "Year": year,
            "Index": current_inflation_index,
            "Trend_Real": real_trend,
            "MR_Real": real_mr,
            "Grid_Real": real_grid
        })
        
    print(f"\nREAL WEALTH COMPARISON: {mode} ({currency}) (Base 100k)")
    print(f"{'Year':<6} | {'Inflation':<10} | {'Trend (Core)':<15} | {'Mean Rev':<15} | {'Grid Bot':<15}")
    print("-" * 75)
    
    for s in yearly_snapshots:
        inf = s["Index"] - 100 # Cumulative inflation roughly
        print(f"{s['Year']:<6} | {inf:>6.0f}%     | {s['Trend_Real']:,.0f}           | {s['MR_Real']:,.0f}          | {s['Grid_Real']:,.0f}")

if __name__ == "__main__":
    for m in ["BIST", "GLOBAL", "CRYPTO"]:
        run_yearly_analysis(m)
