import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta
from calendar import monthrange
from dataclasses import dataclass

# --- 1. THEME & PALETTE (From Playbook A1) ---
CFR = {
    "bg": "#000000",
    "panel": "#0e0e0e",
    "orange": "#FE7C04",
    "orangeHot": "#FF9933",
    "orangeDim": "#5A2C00",
    "text": "#DEBEBE",
    "green": "#00FF41", # Terminals/Hikes
    "red": "#FF1744"    # Cuts
}

# --- 2. CORE LOGIC (From Playbook A3, A4, A5) ---
def implied_rate(settle):
    return 100.0 - settle

def find_terminal(strip, ocr):
    if strip.empty: return None
    hiking = (100 - strip.iloc[0]['settle']) >= ocr
    best = strip.iloc[0]
    for _, row in strip.iterrows():
        rate = 100 - row['settle']
        best_rate = 100 - best['settle']
        if hiking and rate >= best_rate: best = row
        elif not hiking and rate <= best_rate: best = row
        else: break
    return best

def post_meeting_rate(contract_rate, prev_rate, d, n):
    days_after = n - d + 1
    if days_after <= 0: return contract_rate
    return (contract_rate * n - (d - 1) * prev_rate) / days_after

# --- 3. DATA LOADERS (MOCKED - Connect Polygon Here) ---
def get_market_data():
    # In production, use: requests.get(f"https://api.polygon.io/v2/aggs/ticker/{ticker}/prev?apiKey={ST_KEY}")
    # Following the 'make_mock' schema from Playbook A2
    today = date.today()
    
    # Mock Fed Funds Data (ZQ)
    ff_data = []
    for i in range(18):
        exp = today + timedelta(days=30*i)
        ff_data.append({'symbol': f'ZQ{i}', 'root': 'ZQ', 'expiry': exp, 'settle': 96.36 - (i*0.02)})
    
    # Mock SOFR Data (SR3)
    sofr_data = []
    for i in range(8):
        exp = today + timedelta(days=90*i)
        sofr_data.append({'symbol': f'SR3{i}', 'root': 'SR3', 'expiry': exp, 'settle': 96.37 - (i*0.05)})
        
    return pd.DataFrame(ff_data), pd.DataFrame(sofr_data), 3.64, 3.63 # OCR and SOFR Spot

# --- 4. UI COMPONENTS ---
def draw_kpi_box(label, value, subtext, color=CFR["green"]):
    st.markdown(f"""
        <div style="background-color:{CFR['panel']}; padding:20px; border-radius:5px; border-left: 5px solid {color};">
            <p style="color:{CFR['text']}; font-size:12px; margin:0;">{label}</p>
            <h2 style="color:{color}; margin:0;">{value}</h2>
            <p style="color:#555; font-size:10px; margin:0;">{subtext}</p>
        </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN APP ---
def main():
    st.set_page_config(layout="wide", page_title="US STIR Dashboard")
    st.markdown("<style>body {background-color: black; color: white;}</style>", unsafe_allow_html=True)
    
    # Data Fetching
    ff_strip, sofr_strip, ocr, sofr_spot = get_market_data()
    
    # Header
    cols = st.columns([2, 3])
    with cols[0]:
        st.title("US STIR")
        st.write(f"EFFECTIVE FFR: **{ocr:.2f}** | SOFR SPOT: **{sofr_spot:.3f}** | BASIS: **{(sofr_spot-ocr)*100:.1f}bp**")
    
    with cols[1]:
        tab_select = st.radio("", ["MEETINGS", "STRIP", "SPREADS", "CB LVL"], horizontal=True)

    st.divider()

    # Product Selector
    prod_select = st.segmented_control("PRODUCT", ["SOFR FUTURES", "FED FUNDS FUTURES"], default="SOFR FUTURES")
    active_df = sofr_strip if prod_select == "SOFR FUTURES" else ff_strip
    
    # KPI Row
    term = find_terminal(active_df, ocr)
    term_rate = 100 - term['settle']
    
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        draw_kpi_box("TERMINAL RATE (T)", f"{term_rate:.3f}%", f"{term['symbol']} | PEAK HIKES PRICED")
    with k2:
        diff = (term_rate - ocr) * 100
        draw_kpi_box("EFF FFR TO TERMINAL", f"+{diff:.1f}bp", f"vs {term['symbol']}")
    with k3:
        draw_kpi_box("TERMINAL TO +6 MONTHS", "-8.0bp", "Spread Projection", color=CFR["red"])
    with k4:
        draw_kpi_box("TERMINAL TO +12 MONTHS", "-20.0bp", "Spread Projection", color=CFR["red"])

    # Chart Area
    st.subheader("FED FUNDS IMPLIED PATH")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=active_df['expiry'], 
        y=100 - active_df['settle'],
        mode='lines+markers',
        line=dict(color=CFR["orangeHot"], width=3, shape='hv'),
        fill='tozeroy',
        fillcolor='rgba(254, 124, 4, 0.1)'
    ))
    
    fig.add_hline(y=ocr, line_dash="dash", line_color=CFR["orange"], annotation_text="EFF FFR")
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="black",
        plot_bgcolor="black",
        yaxis=dict(gridcolor="#222", title="Rate %"),
        xaxis=dict(gridcolor="#222"),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    # Probability Table (Simplified)
    st.subheader("MEETING PROBABILITIES")
    st.table(active_df[['symbol', 'expiry']].assign(RATE=(100-active_df['settle']).round(3)).head(10))

if __name__ == "__main__":
    main()
