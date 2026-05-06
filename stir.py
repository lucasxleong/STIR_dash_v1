import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta
from calendar import monthrange

# --- 1. CONFIG & BRANDING (From Playbook A1) ---
st.set_page_config(page_title="STIR Dashboard", layout="wide")

CFR = {
    "bg": "#000000", "panel": "#080808", "text": "#D0D0D0",
    "orange": "#FE7C04", "orangeHot": "#FF9533", "orangeDim": "#5A2C00"
}

st.markdown(f"""
    <style>
        body, [data-testid="stAppViewContainer"] {{ background-color: {CFR['bg']}; color: {CFR['text']}; }}
        .stTabs [data-baseweb="tab-list"] {{ background-color: {CFR['bg']}; }}
        .stTabs [aria-selected="true"] {{ background-color: {CFR['orange']} !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOADERS (Playbook A2) ---
def get_mock_data():
    # Synthetic data for ZQ (Fed Funds) and SR3 (SOFR)
    today = date.today()
    contracts = []
    # Create 12 months of Fed Funds (ZQ)
    for i in range(12):
        exp = date(today.year + (today.month + i - 1) // 12, ((today.month - 1 + i) % 12) + 1, 28)
        contracts.append({"symbol": f"ZQ{exp.strftime('%b%y')}", "root": "ZQ", "expiry": exp, "settle": 100 - (3.64 - 0.1*i)})
    # Create 4 quarters of SOFR (SR3)
    for i in range(4):
        exp = date(today.year, [3, 6, 9, 12][i], 20)
        contracts.append({"symbol": f"SR3{exp.strftime('%b%y')}", "root": "SR3", "expiry": exp, "settle": 100 - (3.60 - 0.08*i)})
    
    df = pd.DataFrame(contracts)
    df["implied_rate"] = 100.0 - df["settle"]
    return df

# --- 3. PLOTTING FUNCTION (Playbook A3) ---
def plot_strip(df, ocr, title):
    # Highlight the 'Terminal' rate (the trough/peak) as per playbook 
    best_idx = df['implied_rate'].idxmin() 
    colors = [CFR["orangeHot"] if i == best_idx else CFR["orangeDim"] for i in range(len(df))]
    
    fig = go.Figure(go.Bar(
        x=df['symbol'], y=df['implied_rate'],
        marker_color=colors, marker_line_color="#9A4A02"
    ))
    fig.add_hline(y=ocr, line_dash="dash", line_color=CFR["orange"], annotation_text="EFFECTIVE FFR")
    fig.update_layout(
        title=title, template="plotly_dark", 
        paper_bgcolor=CFR["bg"], plot_bgcolor=CFR["panel"],
        margin=dict(l=40, r=20, t=60, b=40), height=450
    )
    return fig

# --- 4. MAIN UI ---
st.title("STIR REPLICATION DASHBOARD")
df_all = get_mock_data()
effr_today = 3.64

tab1, tab2 = st.tabs(["PRODUCTS", "MEETINGS"])

with tab1:
    # THE MISSING TOGGLE 
    prod = st.radio("SELECT PRODUCT", ["SOFR (SR3)", "FED FUNDS (ZQ)"], horizontal=True)
    
    if "SOFR" in prod:
        df_view = df_all[df_all["root"] == "SR3"].copy()
        st.plotly_chart(plot_strip(df_view, effr_today, "SOFR FUTURES STRIP"), use_container_width=True)
    else:
        df_view = df_all[df_all["root"] == "ZQ"].copy()
        st.plotly_chart(plot_strip(df_view, effr_today, "FED FUNDS FUTURES STRIP"), use_container_width=True)

with tab2:
    st.info("Meetings tab logic (Spreads & CB Lvl) remains active below.")
    # (Include your meeting path/matrix code here)
