import time
import functools
from colorama import Fore

def retry_connection(max_retries=3, delay=2, backoff=2):
    """
    Decorator to retry a function if it raises an exception.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    print(Fore.RED + f"Error in {func.__name__}: {e}. Retrying ({retries}/{max_retries}) in {current_delay}s...")
                    if retries == max_retries:
                        print(Fore.RED + f"FAILED {func.__name__} after {max_retries} attempts.")
                        raise e
                    time.sleep(current_delay)
                    current_delay *= backoff # Exponential backoff
        return wrapper
    return decorator
