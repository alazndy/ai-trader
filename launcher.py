import sys
import os

# 1. Add User Site-Packages to Path dynamically
# This fixes the "No module named streamlit" error on Windows User Installs
user_site = os.path.expanduser("~") + r"\AppData\Roaming\Python\Python313\site-packages"
if os.path.exists(user_site) and user_site not in sys.path:
    print(f"Adding to PATH: {user_site}")
    sys.path.append(user_site)

# 2. Launch Streamlit
try:
    from streamlit.web import cli as stcli
    sys.argv = ["streamlit", "run", "dashboard.py", "--server.headless", "true"]
    sys.exit(stcli.main())
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import streamlit even after path fix.")
    print(f"Path: {sys.path}")
    print(f"Error: {e}")
    input("Press Enter to Exit...")
