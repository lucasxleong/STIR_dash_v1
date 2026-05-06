import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import date

# --- 1. CRITICAL TERMINAL STYLING (The "Bloomberg" Look) ---
st.set_page_config(page_title="CFR STIR TERMINAL", layout="wide")

st.markdown("""
    <style>
        /* Force Black Theme */
        body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #000000 !important;
            color: #E0E0E0 !important;
        }
        /* Custom Header Styling */
        .main-header { font-size: 12px; color: #888; letter-spacing: 1px; margin-bottom: -10px; }
        .main-title { font-size: 28px; color: #FFF; font-weight: 700; margin-bottom: 20px; }
        
        /* Tab Styling - Orange Highlight */
        .stTabs [data-baseweb="tab-list"] { background-color: #000000; gap: 20px; }
        .stTabs [data-baseweb="tab"] { 
            height: 50px; background-color: transparent; border: none; color: #666; font-weight: bold;
        }
        .stTabs [aria-selected="true"] { 
            color: #FF6B00 !important; border-bottom: 3px solid #FF6B00 !important;
        }
        
        /* Grid / Table Styling to match your image */
        div[data-testid="stTable"] table { 
            border-collapse: collapse; width: 100%; background-color: #000000; border: 1px solid #222;
        }
        th { background-color: #080808 !important; color: #FF6B00 !important; padding: 15px !important; border: 1px solid #222 !important; }
        td { padding: 15px !important; border: 1px solid #222 !important; font-family: monospace; font-size: 14px; text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LIVE DATA ENGINE (POLYGON.IO) ---
def get_market_data():
    try:
        api_key = st.secrets["POLYGON_API_KEY"]
    except:
        st.error("MISSING API KEY IN SECRETS")
        return ["MAR 26", "JUN 26", "SEP 26", "DEC 26", "MAR 27"], [3.64, 3.35, 3.10, 2.85, 2.60]

    # ZQ (Fed Funds) Tickers - Matching the front curve
    tickers = {"C:ZQH2026": "MAR 26", "C:ZQM2026": "JUN 26", "C:ZQU2026": "SEP 26", "C:ZQZ2026": "DEC 26", "C:ZQH2027": "MAR 27"}
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
    
    # Fallback if API is empty/delayed
    if not rates:
        return ["MAR 26", "JUN 26", "SEP 26", "DEC 26", "MAR 27"], [3.640, 3.350, 3.105, 2.855, 2.600]
    return names, rates

# --- 3. DASHBOARD TOP BAR ---
st.markdown('<p class="main-header">CAPITAL FLOWS RESEARCH | US STIR REPLICATION</p>', unsafe_allow_html=True)
st.markdown('<p class="main-title">MEETING-TO-MEETING SPREADS (BP)</p>', unsafe_allow_html=True)

# Controls Row (Inline instead of Sidebar)
c1, c2, c3, c4 = st.columns([1,1,1,2])
effr = c1.number_input("EFFR (OCR)", value=3.640, step=0.001, format="%.3f")
sofr = c2.number_input("SOFR SPOT", value=3.642, step=0.001, format="%.3f")
c3.markdown(f"<br><b>BASIS:</b> <span style='color:#FF6B00'>{(sofr-effr)*100:+.1f} BP</span>", unsafe_allow_html=True)
if c4.button("REFRESH DATA"):
    st.rerun()

# --- 4. TABS & CONTENT ---
names, rates = get_market_data()

tab_strip, tab_spreads, tab_cblvl = st.tabs(["STRIP", "SPREADS", "CB LVL"])

with tab_spreads:
    # Build the Diagonal Spread Matrix
    matrix = pd.DataFrame(index=names, columns=names)
    for i in range(len(names)):
        for j in range(len(names)):
            if i < j:
                diff = (rates[j] - rates[i]) * 100
                matrix.iloc[i, j] = f"{diff:+.1f}"
            elif i == j:
                matrix.iloc[i, j] = "—"
    
    # Display the grid
    st.table(matrix.fillna(""))

with tab_strip:
    fig = go.Figure(go.Bar(x=names, y=rates, marker_color='#FF6B00'))
    fig.add_hline(y=effr, line_dash="dash", line_color="white")
    fig.update_layout(template="plotly_dark", plot_bgcolor='black', paper_bgcolor='black', height=400)
    st.plotly_chart(fig, use_container_width=True)

with tab_cblvl:
    fig_cb = go.Figure()
    for rail in np.arange(min(rates)-0.5, max(rates)+0.5, 0.25):
        fig_cb.add_hline(y=rail, line=dict(color="#111", width=1))
    fig_cb.add_trace(go.Scatter(x=names, y=rates, line=dict(color='#FF6B00', width=4), mode='lines+markers'))
    fig_cb.update_layout(template="plotly_dark", plot_bgcolor='black', paper_bgcolor='black', height=500)
    st.plotly_chart(fig_cb, use_container_width=True)
