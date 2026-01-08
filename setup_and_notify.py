import os
import subprocess
import time
import urllib.request
import urllib.parse
import platform

# Configuration
REPO_URL = "https://github.com/alazndy/ai-trader.git"
NTFY_TOPIC = "aitrader_test" # Default topic, change if needed
HOSTNAME = platform.node()

def run_command(command, desc):
    print(f"🔹 {desc}...")
    try:
        if platform.system() == "Windows":
            subprocess.check_call(command, shell=True)
        else:
            subprocess.check_call(command, shell=True)
        print(f"✅ {desc} Complete.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {desc} Failed: {e}")
        return False

def send_notification(message):
    print(f"🔹 Sending Notification: {message}")
    url = f"https://ntfy.sh/{NTFY_TOPIC}"
    data = message.encode('utf-8')
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Title", f"Server Setup: {HOSTNAME}")
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("✅ Notification Sent Successfully.")
            else:
                print(f"⚠️ Notification Clicked but returned {response.status}")
    except Exception as e:
        print(f"❌ Notification Failed: {e}")

def main():
    print(f"=== AI TRADER AUTO-SETUP ({HOSTNAME}) ===")
    
    # 1. Update/Clone (Assumes we are inside the repo or just pulled)
    # If this script is inside the repo, we assume git clone is done. 
    # Let's ensure we are up to date.
    if os.path.isdir(".git"):
        run_command("git pull", "Pulling Latest Updates")
    
    # 2. Install Dependencies
    if os.path.exists("requirements.txt"):
        success = run_command("pip install -r requirements.txt", "Installing Dependencies")
        if not success:
            send_notification(f"Setup Failed on {HOSTNAME}: Pip Install Error")
            return
    else:
        print("⚠️ requirements.txt not found.")
    
    # 3. Notify Success
    send_notification(f"Setup Complete on {HOSTNAME}. Starting Bots...")
    
    # 4. Launch Master Start
    bat_file = "MASTER_START.bat"
    if os.path.exists(bat_file) and platform.system() == "Windows":
        print(f"🚀 Launching {bat_file}...")
        # Start detached to not block this script (or let it finish)
        os.startfile(bat_file)
    else:
        print(f"❌ Could not find {bat_file} or not on Windows.")
        send_notification(f"Launch Failed on {HOSTNAME}: {bat_file} missing")

if __name__ == "__main__":
    main()
