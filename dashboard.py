import streamlit as st
import pandas as pd
import json
import os
import glob
from datetime import datetime

# Page Config
st.set_page_config(page_title="AI Trader Dashboard", layout="wide", page_icon="📈")

st.title("🤖 AI Trader: Live Performance Hub")
st.caption(f"Last Refreshed: {datetime.now().strftime('%H:%M:%S')}")

# Side bar
st.sidebar.header("Configuration")
refresh_rate = st.sidebar.slider("Refresh Rate (s)", 5, 60, 10)

# Check Mode (Cloud vs Local)
# In Cloud Run, we should have GOOGLE_CLOUD_PROJECT or we implicitly know.
# Let's use an explicit Env Var or check for Firebase Creds.
IS_CLOUD = os.getenv("K_SERVICE") is not None or os.getenv("CLOUD_MODE") == "True"

if IS_CLOUD:
    st.sidebar.success("☁️ Mode: Cloud (Firestore)")
else:
    st.sidebar.info("💻 Mode: Local (JSON)")

# Data Loading
@st.cache_data(ttl=refresh_rate)
def load_data():
    strategies = []
    
    if IS_CLOUD:
        # Load from Firestore
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            if not firebase_admin._apps:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
            
            db = firestore.client()
            docs = db.collection('trader_strategies').stream()
            
            for doc in docs:
                data = doc.to_dict()
                name = doc.id
                
                balance = data.get("balance", 0)
                positions = data.get("positions", {})
                trade_log = data.get("trade_log", [])
                
                # Estimate Equity (Cash + Cost Basis)
                equity = balance + sum([p.get('amount',0) * p.get('entry_price',0) for p in positions.values()])
                
                strategies.append({
                    "Name": name,
                    "Balance": balance,
                    "Equity (Est)": equity,
                    "Positions": len(positions),
                    "Trades": len(trade_log)
                })
        except Exception as e:
            st.error(f"Firestore Error: {e}")
            
    else:
        # Load from Local JSON
        files = glob.glob("data/sim_*.json")
        for f in files:
            try:
                with open(f, 'r') as file:
                    data = json.load(file)
                    basename = os.path.basename(f)
                    name = basename.replace("sim_", "").replace(".json", "")
                    
                    balance = data.get("balance", 0)
                    positions = data.get("positions", {})
                    trade_log = data.get("trade_log", [])
                    
                    equity = balance + sum([p['amount'] * p['entry_price'] for p in positions.values()])
                    
                    strategies.append({
                        "Name": name,
                        "Balance": balance,
                        "Equity (Est)": equity,
                        "Positions": len(positions),
                        "Trades": len(trade_log)
                    })
            except: pass
            
    return pd.DataFrame(strategies)

def load_trade_log(strategy_name):
    if IS_CLOUD:
        try:
            import firebase_admin
            from firebase_admin import firestore
            if not firebase_admin._apps: firebase_admin.initialize_app()
            db = firestore.client()
            
            doc = db.collection('trader_strategies').document(strategy_name).get()
            if doc.exists:
                return pd.DataFrame(doc.to_dict().get("trade_log", []))
        except: pass
    else:
        try:
            with open(f"data/sim_{strategy_name}.json", 'r') as file:
                data = json.load(file)
                return pd.DataFrame(data.get("trade_log", []))
        except: pass
    return pd.DataFrame()

# Main UI
df = load_data()

if not df.empty:
    # ROI
    df["ROI %"] = ((df["Equity (Est)"] - 1000) / 1000) * 100
    
    # Metrics
    total_equity = df["Equity (Est)"].sum()
    avg_roi = df["ROI %"].mean()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total AUM", f"{total_equity:.2f}")
    c2.metric("Avg ROI", f"{avg_roi:.2f} %")
    c3.metric("Active Bots", len(df))
    
    # Leaderboard
    st.subheader("🏆 Leaderboard")
    st.dataframe(df.sort_values(by="ROI %", ascending=False).style.format({"Balance": "{:.2f}", "Equity (Est)": "{:.2f}", "ROI %": "{:.2f}"}), use_container_width=True)
    
    # Charts
    st.bar_chart(df.set_index("Name")["ROI %"])
    
    # Detail View
    st.subheader("🕵️ Strategy Inspector")
    selected = st.selectbox("Select Strategy", df["Name"])
    
    if selected:
        logs = load_trade_log(selected)
        if not logs.empty:
            st.write("Recent Trades (Last 50)")
            st.dataframe(logs.iloc[::-1]) # Reverse order
        else:
            st.info("No trades yet.")
else:
    if IS_CLOUD:
        st.warning("No strategies found in Firestore. (Wait for the bot to run once)")
    else:
        st.warning("No simulation data found in 'data/' folder. Run simulation_manager.py first.")

if st.button("Refresh Now"):
    st.rerun()
