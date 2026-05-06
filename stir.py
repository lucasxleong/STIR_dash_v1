import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import date

# --- 1. CONFIG & TERMINAL CSS ---
st.set_page_config(page_title="CFR STIR TERMINAL", layout="wide")

st.markdown("""
    <style>
        body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #000000 !important;
            color: #E0E0E0 !important;
        }
        .stTabs [data-baseweb="tab-list"] { background-color: #000000; gap: 8px; }
        .stTabs [data-baseweb="tab"] { 
            background-color: #111; border: 1px solid #222; border-radius: 4px; padding: 10px 20px;
        }
        .stTabs [aria-selected="true"] { 
            background-color: #FF6B00 !important; color: white !important; border: 1px solid #FF6B00 !important;
        }
        div[data-testid="stTable"] table { border: 1px solid #222; width: 100%; background-color: #050505; }
        th { color: #FF6B00 !important; text-transform: uppercase; border-bottom: 2px solid #222 !important; }
        td { border-bottom: 1px solid #111 !important; font-family: 'Courier New', monospace; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LIVE API ENGINE (POLYGON.IO) ---
def get_live_market_data():
    try:
        api_key = st.secrets["POLYGON_API_KEY"]
    except:
        return None, None

    # Tickers for ZQ (Fed Funds) and SR3 (SOFR) - Using 2025/26 Month Codes
    # H=Mar, M=Jun, U=Sep, Z=Dec
    tickers = {
        "C:ZQH2025": "MAR 25", "C:ZQM2025": "JUN 25", 
        "C:ZQU2025": "SEP 25", "C:ZQZ2025": "DEC 25",
        "C:ZQH2026": "MAR 26", "C:ZQM2026": "JUN 26"
    }
    
    names, rates = [], []
    for t, label in tickers.items():
        url = f"https://api.polygon.io/v2/last/nbbo/{t}?apiKey={api_key}"
        try:
            r = requests.get(url).json()
            price = r['results']['p']
            names.append(label)
            rates.append(round(100 - price, 3))
        except:
            continue
    
    # If API fails or market is closed, use fallback for visual integrity
    if not rates:
        names = ["MAR 25", "JUN 25", "SEP 25", "DEC 25", "MAR 26", "JUN 26"]
        rates = [3.64, 3.35, 3.10, 2.85, 2.65, 2.50]
        
    return names, rates

# --- 3. MATH FOR SPREAD MATRIX ---
def build_spread_matrix(names, rates):
    df = pd.DataFrame(index=names, columns=names)
    for i in range(len(names)):
        for j in range(len(names)):
            if i < j:
                diff = (rates[j] - rates[i]) * 100
                df.iloc[i, j] = f"{diff:+.1f}"
            elif i == j:
                df.iloc[i, j] = "—"
    return df.fillna("")

# --- 4. MAIN DASHBOARD ---
st.write(f"**CAPITAL FLOWS RESEARCH** |  LIVE TERMINAL  |  {date.today()}")
st.title("REPLICATION PLAYBOOK: US STIR")

# Data fetch
names, rates = get_live_market_data()

# Sidebar (The Controls)
with st.sidebar:
    st.header("FIXINGS")
    effr = st.number_input("EFFR (OCR)", value=3.640, step=0.001, format="%.3f")
    sofr = st.number_input("SOFR SPOT", value=3.642, step=0.001, format="%.3f")
    st.markdown(f"**BASIS:** <span style='color:#FF6B00'>{(sofr-effr)*100:+.1f} BP</span>", unsafe_allow_html=True)
    if st.button("REFRESH MARKET DATA"):
        st.rerun()

tab_prod, tab_meet = st.tabs(["PRODUCTS", "MEETINGS"])

with tab_prod:
    col_sel, col_chart = st.columns([1, 4])
    with col_sel:
        st.radio("TICKER", ["SOFR (SR3)", "FED FUNDS (ZQ)"])
    
    fig = go.Figure(go.Bar(x=names, y=rates, marker_color='#FF6B00'))
    fig.add_hline(y=effr, line_dash="dash", line_color="white", annotation_text="CURRENT OCR")
    fig.update_layout(template="plotly_dark", plot_bgcolor='black', paper_bgcolor='black', height=500)
    st.plotly_chart(fig, use_container_width=True)

with tab_meet:
    s1, s2, s3 = st.tabs(["STRIP", "SPREADS", "CB LVL"])
    
    with s2:
        st.subheader("MEETING-TO-MEETING SPREADS (BP)")
        matrix = build_spread_matrix(names, rates)
        st.table(matrix)

    with s3:
        st.subheader("CB LEVELS - 25BP RAILS")
        fig_cb = go.Figure()
        # Add the "Rails" from 2% to 5%
        for rail in np.arange(2.0, 5.25, 0.25):
            fig_cb.add_hline(y=rail, line=dict(color="#111", width=1))
        
        fig_cb.add_trace(go.Scatter(x=names, y=rates, line=dict(color='#FF6B00', width=4), mode='lines+markers'))
        fig_cb.update_layout(template="plotly_dark", plot_bgcolor='black', paper_bgcolor='black', height=500)
        st.plotly_chart(fig_cb, use_container_width=True)
