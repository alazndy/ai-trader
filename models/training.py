import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, classification_report
from utils.logger import setup_logger

logger = setup_logger("Model_Trainer")

def train_and_evaluate(df: pd.DataFrame, feature_cols: list, target_col: str = 'Target'):
    """
    Splits data (Time-Series safe), trains Random Forest, and returns metrics.
    """
    # 1. Split Data (No Shuffling for Time Series!)
    # Train on first 80%, Test on last 20%
    split_idx = int(len(df) * 0.8)
    
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]
    
    logger.info(f"Training Data Size: {len(X_train)}, Test Data Size: {len(X_test)}")
    
    # 2. Train Model
    # n_estimators=100 (number of trees)
    # min_samples_split=100 (prevent overfitting)
    # random_state=1 (reproducibility)
    model = RandomForestClassifier(n_estimators=100, min_samples_split=50, random_state=1)
    model.fit(X_train, y_train)
    
    # 3. Predict matches
    preds = model.predict(X_test)
    preds_series = pd.Series(preds, index=X_test.index)
    
    # 4. Evaluate
    precision = precision_score(y_test, preds)
    logger.info(f"Model Precision Score: {precision:.4f}")
    
    # Classification Report
    report = classification_report(y_test, preds)
    print("\nClassification Report:\n", report)
    
    return model, precision, preds_series
