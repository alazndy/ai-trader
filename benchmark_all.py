import subprocess
import os
import sys

def run_benchmark():
    modes = ["BIST", "GLOBAL", "CRYPTO"]
    scripts = [
        ("Trend (Core-Sat)", "main_backtest_multi.py"),
        ("Mean Reversion", "main_mean_reversion.py"),
        ("Grid Trading", "main_grid_bot.py"),
        # ("Pairs Trading", "main_pairs.py"), # Data issues
        ("RL Agent", "main_rl_proto.py")
    ]
    
    print(f"{'MODE':<10} | {'STRATEGY':<20} | {'STATUS':<10}")
    print("-" * 50)
    
    results = []
    
    env = os.environ.copy()
    
    for mode in modes:
        env["AI_TRADER_MODE"] = mode
        
        for strat_name, script_name in scripts:
            print(f"Running {mode} - {strat_name}...", end="\r")
            
            try:
                # Run script and capture output to parse ROI? 
                # For now just let it print to stdout, or capture result.
                # Since scripts print to log, it's hard to parse exact ROI without modification.
                # We will just run them to ensure they work and let user see output logs.
                # Use verify logic: check return code.
                
                result = subprocess.run([sys.executable, script_name], env=env, capture_output=True, text=True)
                
                # Combine stdout and stderr for searching
                full_output = result.stdout + "\n" + result.stderr
                
                if result.returncode == 0:
                    status = "DONE"
                    # Try to grep ROI from output
                    lines = full_output.split('\n')
                    roi_lines = [l for l in lines if "ROI" in l]
                    roi_text = roi_lines[-1].strip() if roi_lines else "N/A"
                    # simplify log
                    if "ROI:" in roi_text:
                        roi_val = roi_text.split("ROI:")[-1].strip()
                    elif "ROI" in roi_text:
                        roi_val = roi_text.split("ROI")[-1].strip()
                    else:
                        roi_val = "N/A"
                        
                    results.append({"mode": mode, "strat": strat_name, "roi": roi_val})
                else:
                    status = "FAIL"
                    roi_val = "ERROR"
                    print(f"\nError in {mode} {strat_name}:\n{result.stderr}")
                    
            except Exception as e:
                status = "EXCEPTION"
                roi_val = str(e)
                
            print(f"{mode:<10} | {strat_name:<20} | {status} ({roi_val})")
            
    print("\n--- BENCHMARK MATRIX (2022-2025) ---")
    print(f"{'STRATEGY':<20} | {'BIST':<15} | {'GLOBAL':<15} | {'CRYPTO':<15}")
    print("-" * 75)
    
    # Re-organize
    matrix = {}
    for r in results:
        if r['strat'] not in matrix: matrix[r['strat']] = {}
        matrix[r['strat']][r['mode']] = r['roi']
        
    for strat in matrix:
        bist = matrix[strat].get("BIST", "-")
        glob = matrix[strat].get("GLOBAL", "-")
        cryp = matrix[strat].get("CRYPTO", "-")
        print(f"{strat:<20} | {bist:<15} | {glob:<15} | {cryp:<15}")

if __name__ == "__main__":
    run_benchmark()
