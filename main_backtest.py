import yfinance as yf
import pandas as pd
from strategies.features import add_all_features
from data.labeling import add_target
from models.training import train_and_evaluate
from execution.paper_broker import PaperBroker
from utils.logger import setup_logger

logger = setup_logger("Main_Backtest_Long")

def main():
    logger.info("Starting Extended Backtesting: 2023, 2024, 2025")
    
    ticker = "THYAO.IS"
    
    # 1. Fetch Data (Start from 2020 to give enough training data before 2023)
    start_date = "2020-01-01"
    end_date = "2026-01-01"
    
    logger.info(f"Fetching data from {start_date} to {end_date}...")
    df = yf.download(ticker, start=start_date, end=end_date, interval="1d", auto_adjust=False, progress=False)
    
    if hasattr(df.columns, 'nlevels') and df.columns.nlevels > 1:
        df.columns = df.columns.droplevel(1)

    # 2. Prepare Data
    logger.info("Generating Features...")
    df = add_all_features(df)
    df = df.dropna()
    df_labeled = add_target(df)
    
    features = ['RSI', 'SMA_50', 'SMA_200', 'macd', 'macd_signal', 'macd_hist', 'ATR']
    
    # 3. Split Data Based on Time
    # Train: Before 2023
    # Test: 2023, 2024, 2025
    
    split_date = "2023-01-01"
    
    train_df = df_labeled.loc[df_labeled.index < split_date]
    test_df = df_labeled.loc[df_labeled.index >= split_date]
    
    if len(train_df) == 0 or len(test_df) == 0:
        logger.error("Insufficient data for split! Check date ranges.")
        return

    logger.info(f"Training Period: {train_df.index[0].date()} -> {train_df.index[-1].date()} ({len(train_df)} days)")
    logger.info(f"Testing Period:  {test_df.index[0].date()} -> {test_df.index[-1].date()} ({len(test_df)} days)")
    
    # 4. Train Model
    logger.info("Training Random Forest...")
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(n_estimators=100, min_samples_split=50, random_state=1)
    
    X_train = train_df[features]
    y_train = train_df['Target']
    model.fit(X_train, y_train)
    
    # 5. Simulation Loop
    broker = PaperBroker(initial_balance=100000.0)
    in_position = False
    
    logger.info("Running Simulation Loop...")
    for i in range(len(test_df)):
        current_data = test_df.iloc[i]
        current_date = test_df.index[i]
        current_price = current_data['Adj Close']
        
        last_features = current_data[features].values.reshape(1, -1)
        prediction = model.predict(last_features)[0]
        
        if prediction == 1 and not in_position:
            if broker.buy(ticker, current_price, current_date):
                in_position = True
        
        elif prediction == 0 and in_position:
            if broker.sell(ticker, current_price, current_date):
                in_position = False
                
    # 6. Report
    final_equity = broker.get_portfolio_value({ticker: test_df.iloc[-1]['Adj Close']})
    roi = ((final_equity - broker.initial_balance) / broker.initial_balance) * 100
    
    logger.info("------------------------------------------------")
    logger.info(f"Initial Balance: {broker.initial_balance:.2f} TL")
    logger.info(f"Final Balance:   {final_equity:.2f} TL")
    logger.info(f"Return (ROI):    {roi:.2f}%")
    logger.info("------------------------------------------------")
    
    # Benchmark
    start_price = test_df.iloc[0]['Adj Close']
    end_price = test_df.iloc[-1]['Adj Close']
    benchmark_roi = ((end_price - start_price) / start_price) * 100
    logger.info(f"Benchmark (Buy & Hold) ROI: {benchmark_roi:.2f}%")
    
    if roi > benchmark_roi:
        logger.info("✅ Strategy BEAT the market!")
    else:
        logger.warning("⚠️ Strategy UNDERPERFORMED the market.")

if __name__ == "__main__":
    main()
