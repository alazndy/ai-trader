import os

# Configuration Settings

# Active Mode: Read from Env Var or Default to "BIST"
# Options: "BIST", "GLOBAL", "CRYPTO"
ACTIVE_MODE = os.environ.get("AI_TRADER_MODE", "GLOBAL") 

# Market Configurations
MARKET_CONFIG = {
    "BIST": {
        "SAFE_TICKER": "ALTIN.S1", # Gold Certificate
        "SAFE_ALLOCATION": 0.0,    # Optimized: 0% (All-in active)
        "TICKERS": ["BIMAS.IS", "THYAO.IS", "AKBNK.IS", "SASA.IS", "KONTR.IS"],
        "CURRENCY": "TL"
    },
    "GLOBAL": {
        "SAFE_TICKER": "GLD",      # SPDR Gold Shares
        "SAFE_ALLOCATION": 0.0,    # Optimized: 0% (Enable Active Trading)
        # Note: 1.0 means bot effectively stops trading stocks. 
        # But for benchmarking active strategies, they might ignore this. 
        # Core-Satellite (Trend) will respect this.
        "TICKERS": ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN"],
        "CURRENCY": "USD"
    },
    "CRYPTO": {
        "SAFE_TICKER": "USDT-USD", # Tether
        "SAFE_ALLOCATION": 0.0,    # Optimized: 0% (All-in active)
        "TICKERS": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD"],
        "CURRENCY": "USD"
    },
    "CHIPS": {
        "SAFE_TICKER": "SOXQ",     # PHLX Semiconductor ETF (Sector ETF as Safe approach? Or just GLD?) 
                                   # Actually, user wants to trade chips. Safe asset should be Cash/Gold to Hedge.
                                   # Let's use "GLD" or "SHV" (Short Treasury). GLD is proven.
        "SAFE_TICKER": "GLD",
        "SAFE_ALLOCATION": 0.0,    # Aggressive Sector Fund
        "TICKERS": [
            "NVDA", # GPU King
            "AMD",  # CPU/GPU
            "INTC", # Legacy CPU
            "TSM",  # Foundry (The Fab)
            "MU",   # RAM/Memory
            "ASML", # Lithography (Equipment)
            "AVGO", # Connectivity/Custom Silicon
            "QCOM"  # Mobile Chips
        ],
        "CURRENCY": "USD"
    }
}

# Helper to get current config
def get_active_config():
    return MARKET_CONFIG.get(ACTIVE_MODE, MARKET_CONFIG["GLOBAL"])

# Legacy variables for compatibility (Dynamically loaded)
_cfg = get_active_config()
TICKERS = _cfg["TICKERS"]
SAFE_TICKER = _cfg["SAFE_TICKER"]
SAFE_ALLOCATION_PCT = _cfg["SAFE_ALLOCATION"]
CURRENCY = _cfg["CURRENCY"]

# Time Interval between checks (Seconds)
# 1 Hour = 3600
CHECK_INTERVAL_SECONDS = 3600

# Training Period
TRAINING_PERIOD = "2y"

# Risk Management
STOP_LOSS_PCT = 0.03   # 3% Loss -> Sell
KILL_SWITCH_PCT = 0.05 # 5% Portfolio Loss -> Stop Trading for Day
