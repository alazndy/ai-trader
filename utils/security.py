import re

def sanitize_ticker(ticker):
    """
    Prevents injection or malformed tickers.
    Allows only alphanumeric and dots (e.g., 'AAPL', 'THYAO.IS').
    """
    if not isinstance(ticker, str):
        return None
    # Remove any dangerous chars
    clean = re.sub(r'[^A-Z0-9\.]', '', ticker.upper())
    if len(clean) > 10 or len(clean) < 1:
        return None
    return clean

def validate_price(price, last_price=None):
    """
    Checks for fat-finger or data glitches.
    - No negative/zero prices.
    - If last_price exists, reject >50% instant jumps (Data Glitch Protection).
    """
    try:
        p = float(price)
        if p <= 0 or p > 1_000_000: # Sanity limits
            return None
            
        if last_price:
            change = abs(p - last_price) / last_price
            if change > 0.50: # >50% change is suspicious for 1 minute
                return None
                
        return p
    except:
        return None
