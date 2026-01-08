import time
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from colorama import Fore, Style, init
from find_consecutive_stocks import get_best_pairs
from config.settings import MARKET_CONFIG

# Initialize Colorama
init(autoreset=True)

def fetch_current_price(tickers):
    """
    Fetches the latest available price for the tickers.
    Uses '1d' interval to get the latest close (which is current price during market hours).
    Ideally valid for stocks.
    """
    if not tickers: return {}
    
    try:
        # We fetch 1 day history to get the 'latest' close/adjust close
        # Use '1m' if possible for better granularity, but 1d is safer for all markets
        # For 'Real Time', we want the last price.
        data = yf.download(tickers, period="1d", interval="1m", progress=False)['Close']
        
        latest_prices = {}
        if isinstance(data, pd.Series): # Single ticker
             latest_prices[tickers[0]] = data.iloc[-1]
        else:
            for t in tickers:
                if t in data.columns:
                    # Get last valid index
                    val = data[t].dropna().iloc[-1]
                    latest_prices[t] = val
                    
        return latest_prices
    except Exception as e:
        # Fallback to 1d if 1m fails (e.g. market closed or not supported)
        try:
             data = yf.download(tickers, period="1d", progress=False)['Close']
             latest_prices = {}
             if isinstance(data, pd.Series):
                 latest_prices[tickers[0]] = data.iloc[-1]
             else:
                 for t in tickers:
                    if t in data.columns:
                        latest_prices[t] = data[t].dropna().iloc[-1]
             return latest_prices
        except:
             print(f"Error fetching prices: {e}")
             return {}

def monitor_pairs(interval=60):
    print(f"{Fore.CYAN}--- STARTING REAL-TIME PAIRS MONITOR ---{Style.RESET_ALL}")
    
    # 1. Discovery Phase
    print(f"{Fore.YELLOW}Discovering best pairs...{Style.RESET_ALL}")
    best_pairs = get_best_pairs(MARKET_CONFIG)
    
    print(f"{Fore.GREEN}Tracking {len(best_pairs['correlation'])} Correlated Pairs and {len(best_pairs['lead_lag'])} Lead-Lag Pairs.{Style.RESET_ALL}")
    
    watching_tickers = set()
    for t1, t2, _ in best_pairs['correlation']:
        watching_tickers.add(t1)
        watching_tickers.add(t2)
    for t1, t2, _, _ in best_pairs['lead_lag']:
        watching_tickers.add(t1)
        watching_tickers.add(t2)
        
    watching_tickers = list(watching_tickers)
    
    # Baseline Storage (To calculate changes)
    # in a real app, we'd have a database. Here we just store the initial price.
    last_prices = {} 
    
    print(f"{Fore.CYAN}Monitoring started. Press Ctrl+C to stop.{Style.RESET_ALL}")
    
    try:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n--- Check at {timestamp} ---")
            
            current_prices = fetch_current_price(watching_tickers)
            
            if not current_prices:
                print("No price data received. Market might be closed.")
                time.sleep(interval)
                continue
                
            # Check Correlated Pairs (Divergence Strategy)
            for t1, t2, score in best_pairs['correlation']:
                p1 = current_prices.get(t1)
                p2 = current_prices.get(t2)
                
                if p1 and p2:
                    # Simple Ratio Check
                    ratio = p1 / p2
                    # In a full version, we'd compare this to the Moving Average Ratio (Z-Score)
                    # For now, we print the ratio and price change if we have previous data
                    
                    if t1 in last_prices and t2 in last_prices:
                        chg1 = (p1 - last_prices[t1]) / last_prices[t1] * 100
                        chg2 = (p2 - last_prices[t2]) / last_prices[t2] * 100
                        
                        # Divergence Alert: If they move in opposite directions significantly
                        diff = abs(chg1 - chg2)
                        if diff > 1.0: # 1% Divergence in one interval
                            print(f"{Fore.RED}[ALERT] Divergence on {t1}-{t2}! {t1}:{chg1:.2f}%, {t2}:{chg2:.2f}%{Style.RESET_ALL}")
                        else:
                            # Print status occasionally/verbose
                            pass
                            
            # Check Lead-Lag (Follow Strategy)
            for leader, follower, lag, score in best_pairs['lead_lag']:
                p_lead = current_prices.get(leader)
                p_fol = current_prices.get(follower)
                
                if p_lead and p_fol:
                    if leader in last_prices:
                        lead_chg = (p_lead - last_prices[leader]) / last_prices[leader] * 100
                        
                        # Leader Move Alert
                        if abs(lead_chg) > 1.0: # Leader moved 1%
                             print(f"{Fore.GREEN}[SIGNAL] Leader {leader} moved {lead_chg:.2f}%. Watch {follower}!{Style.RESET_ALL}")

            # Update Last Prices
            last_prices = current_prices
            
            print(f"Updated {len(current_prices)} prices.")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nStopping monitor...")

if __name__ == "__main__":
    monitor_pairs(interval=60)
