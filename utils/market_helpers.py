from datetime import datetime
import pytz

# Constants
BIST_TIMEZONE = pytz.timezone('Europe/Istanbul')
MARKET_OPEN_HOUR = 10
MARKET_CLOSE_HOUR = 18

def get_current_time():
    """Returns the current time in BIST timezone."""
    return datetime.now(BIST_TIMEZONE)

def is_market_open(current_time=None):
    """
    Checks if the BIST market is currently open.
    Note: This is a simplified check (Mon-Fri, 10:00-18:00).
    Does not account for official holidays yet.
    """
    if current_time is None:
        current_time = get_current_time()

    # Check weekend
    if current_time.weekday() >= 5: # 5=Sat, 6=Sun
        return False

    # Check hours
    if MARKET_OPEN_HOUR <= current_time.hour < MARKET_CLOSE_HOUR:
        return True
    
    return False

def to_bist_time(dt_object):
    """Converts a UTC datetime object to Europe/Istanbul time."""
    if dt_object.tzinfo is None:
        # Assume UTC if naive, or raise error. 
        # Ideally, we should receive timezone-aware objects.
        dt_object = pytz.utc.localize(dt_object)
    
    return dt_object.astimezone(BIST_TIMEZONE)
