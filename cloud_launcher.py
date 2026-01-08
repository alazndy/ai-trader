import os
import threading
import subprocess
import time
from run_cloud import CloudBot

def run_bot_loop():
    """Background Thread: Runs the Trading Bot continuously."""
    print("🚀 Background Bot Thread Started!")
    bot = CloudBot()
    
    # Cloud Run Loop
    while True:
        try:
            bot.run_all_markets() 
        except Exception as e:
            print(f"Bot Error: {e}")
        
        # Sleep for 15 minutes (900s) to respect quotas/logic
        # Or faster if user wants "Continuous"
        # Let's do 5 minutes (300s) as compromise for "Always On" container.
        time.sleep(300)

def run_streamlit():
    """Foreground Process: Runs the Dashboard."""
    # Cloud Run expects the server to listen on $PORT
    port = os.environ.get("PORT", "8080")
    
    # We use subprocess to run streamlit cli
    # streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0
    cmd = [
        "streamlit", "run", "dashboard.py",
        "--server.port", port,
        "--server.address", "0.0.0.0",
        "--theme.base", "dark"
    ]
    print(f"🎬 Starting Dashboard on port {port}...")
    subprocess.run(cmd)

if __name__ == "__main__":
    # 1. Start Bot in Background Thread
    bot_thread = threading.Thread(target=run_bot_loop, daemon=True)
    bot_thread.start()
    
    # 2. Start Streamlit in Main Thread (Blocks)
    run_streamlit()
