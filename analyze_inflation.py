import yfinance as yf
import pandas as pd

def calculate_real_returns():
    print("--- INFLATION & REAL RETURN ANALYSIS (2023-2025) ---")
    
    # 1. Fetch Currency Data for BIST Deflator
    # We use USD/TRY change as a proxy for "Real Hard Currency" inflation in TR
    try:
        usd_try = yf.download("TRY=X", start="2023-01-01", end="2026-01-01", progress=False)['Adj Close']
        start_rate = float(usd_try.iloc[0])
        end_rate = float(usd_try.iloc[-1])
        usd_devaluation = ((end_rate - start_rate) / start_rate) * 100
        print(f"USD/TRY Change (2023-2025): +{usd_devaluation:.2f}% (Rate: {start_rate:.2f} -> {end_rate:.2f})")
    except:
        start_rate = 18.7
        end_rate = 36.0 # Approx
        usd_devaluation = 92.5
        print(f"USD/TRY (Approx): +{usd_devaluation:.2f}%")

    # 2. Define Inflation Rates (Cumulative Estimates)
    # TR Inflation (Official vs Shadow)
    # 2023: 65%, 2024: 45%, 2025: 30% (Simulated)
    tr_cpi_factor = 1.65 * 1.45 * 1.30
    tr_inflation_pct = (tr_cpi_factor - 1) * 100
    
    # US Inflation
    # 2023: 3.4%, 2024: 3.0%, 2025: 2.5%
    us_cpi_factor = 1.034 * 1.03 * 1.025
    us_inflation_pct = (us_cpi_factor - 1) * 100
    
    print(f"Cumulative Inflation (Estimates):")
    print(f"  TR CPI: +{tr_inflation_pct:.2f}%")
    print(f"  US CPI: +{us_inflation_pct:.2f}%")
    print("-" * 30)

    # 3. Analyze Strategies
    strategies = [
        {"name": "BIST (Nominal TL)", "roi": 212.0, "currency": "TL", "deflator": tr_inflation_pct, "deflator_name": "TR CPI"},
        {"name": "BIST (Hard Currency)", "roi": 212.0, "currency": "TL", "deflator": usd_devaluation, "deflator_name": "USD/TRY"},
        {"name": "GLOBAL (Nominal USD)", "roi": 87.0, "currency": "USD", "deflator": us_inflation_pct, "deflator_name": "US CPI"},
        {"name": "CRYPTO (Nominal USD)", "roi": 42.0, "currency": "USD", "deflator": us_inflation_pct, "deflator_name": "US CPI"},
    ]
    
    print(f"{'STRATEGY':<25} | {'NOMINAL':<10} | {'REAL ROI':<10} | {'PURCHASING POWER':<15}")
    print("-" * 75)
    
    for s in strategies:
        nominal_multiplier = 1 + (s["roi"] / 100)
        deflator_multiplier = 1 + (s["deflator"] / 100)
        
        real_multiplier = nominal_multiplier / deflator_multiplier
        real_roi = (real_multiplier - 1) * 100
        
        # Purchasing Power Change
        # 100 -> 312 (Nominal) vs Cost 100 -> 311 (Inflation)
        pp_change = "RETAINED" if real_roi >= 0 else "LOST"
        
        print(f"{s['name']:<25} | {s['roi']:>+6.1f}%   | {real_roi:>+6.1f}%   | {pp_change} ({real_multiplier:.2f}x)")
        
    print("-" * 75)
    print("\nCONCLUSION:")
    
    print("1. BIST Strategy Analysis:")
    print(f"   Nominally (+212%), you tripled your money.")
    # Recalc variables for print text
    bist_real_roi = ((1 + 2.12) / (1 + tr_inflation_pct/100) - 1) * 100
    bist_usd_roi = ((1 + 2.12) / (1 + usd_devaluation/100) - 1) * 100
    
    if bist_real_roi > 0:
        print(f"   You BEAT inflation by {bist_real_roi:.1f}%. Your wealth grew.")
    else:
        print(f"   You lagged inflation by {bist_real_roi:.1f}%. Purchasing power dropped.")
        
    print(f"   In USD Terms: You made {bist_usd_roi:.1f}% profit in Dollars.")

    # Global Analysis
    global_real_roi = ((1 + 0.87) / (1 + us_inflation_pct/100) - 1) * 100
    print("\n2. GLOBAL Strategy Analysis:")
    print(f"   Nominal: +87% USD.")
    print(f"   Real (vs US CPI): +{global_real_roi:.1f}% unique purchasing power gain.")
    print("   This is 'Cleaner' profit because USD inflation is low.")

if __name__ == "__main__":
    calculate_real_returns()
