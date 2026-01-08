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

# Data Loading
@st.cache_data(ttl=refresh_rate)
def load_data():
    files = glob.glob("data/sim_*.json")
    strategies = []
    
    for f in files:
        try:
            with open(f, 'r') as file:
                data = json.load(file)
                # Parse Filename for Name
                basename = os.path.basename(f)
                name = basename.replace("sim_", "").replace(".json", "")
                
                # Check structure
                balance = data.get("balance", 0)
                positions = data.get("positions", {})
                trade_log = data.get("trade_log", [])
                
                # Calculate Equity (Estimated)
                # Need live price? For now use entry price for rough estimate or 0
                # A dashboard usually has access to price feeder.
                # Let's assume cash only for speed or use cached 'last_price' if we stored it.
                # GridStrategy stores 'last_price' in grids, but generic PaperBroker doesn't.
                # We will just show Cash + Cost Basis for now.
                equity = balance + sum([p['amount'] * p['entry_price'] for p in positions.values()])
                
                strategies.append({
                    "Name": name,
                    "Balance": balance,
                    "Equity (Est)": equity,
                    "Positions": len(positions),
                    "Trades": len(trade_log)
                })
        except:
            pass
            
    return pd.DataFrame(strategies)

def load_trade_log(strategy_name):
    try:
        with open(f"data/sim_{strategy_name}.json", 'r') as file:
            data = json.load(file)
            return pd.DataFrame(data.get("trade_log", []))
    except:
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
    c1.metric("Total AUM", f"{total_equity:.2f} TL")
    c2.metric("Avg ROI", f"{avg_roi:.2f} %")
    c3.metric("Active Bots", len(df))
    
    # Leaderboard
    st.subheader("🏆 Leaderboard")
    st.dataframe(df.sort_values(by="ROI %", ascending=False).style.format({"Balance": "{:.2f}", "Equity (Est)": "{:.2f}", "ROI %": "{:.2f}"}), use_container_width=True)
    
    # Charts (If we had history, we would plot equity curve. For now, bar chart of ROI)
    st.bar_chart(df.set_index("Name")["ROI %"])
    
    # Detail View
    st.subheader("🕵️ Strategy Inspector")
    selected = st.selectbox("Select Strategy", df["Name"])
    
    if selected:
        logs = load_trade_log(selected)
        if not logs.empty:
            st.write("Recent Trades")
            st.dataframe(logs.iloc[::-1]) # Reverse order
        else:
            st.info("No trades yet.")
else:
    st.warning("No simulation data found in 'data/' folder. Run simulation_manager.py first.")

if st.button("Refresh Now"):
    st.rerun()
