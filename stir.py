import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dataclasses import dataclass
from datetime import date, timedelta
from calendar import monthrange

# --- 1. CONFIG & STYLE (From Playbook Appendix A1) ---
st.set_page_config(page_title="STIR Replication Dashboard", layout="wide")

CFR = {
    "bg": "#000000", "panel": "#080808", "text": "#E0E0E0",
    "accent": "#FF6B00", "sofr": "#00D1FF", "ff": "#FF6B00",
    "grid": "#222222", "rail": "#333333"
}

@dataclass
class Contract:
    symbol: str
    root: str
    expiry: date
    settle: float

# --- 2. DATA LOADERS (Modified for Streamlit + Real 2026 Dates) ---
def get_fomc_dates():
    # Hard-coded FOMC dates for 2025-2026 as per Playbook recommendation
    return [
        date(2025, 1, 29), date(2025, 3, 19), date(2025, 5, 7), date(2025, 6, 18),
        date(2025, 7, 30), date(2025, 9, 17), date(2025, 10, 29), date(2025, 12, 10),
        date(2026, 1, 28), date(2026, 3, 18), date(2026, 4, 29), date(2026, 6, 17),
        date(2026, 7, 29), date(2026, 16, 16), date(2026, 10, 28), date(2026, 12, 9)
    ]

def load_mock_data():
    """Generates synthetic CME futures data based on current 3.64% rates."""
    today = date.today()
    # Mock Strip: Simulating a cutting cycle (rates going down)
    contracts = []
    for i in range(12):
        expiry = today + timedelta(days=30*i)
        # ZQ (Fed Funds)
        contracts.append(Contract(f"ZQ{i}", "ZQ", expiry, 100.0 - (3.64 - 0.10*i)))
        # SR3 (SOFR)
        if i % 3 == 0:
            contracts.append(Contract(f"SR3{i}", "SR3", expiry, 100.0 - (3.64 - 0.12*i)))
    
    df = pd.DataFrame([vars(c) for c in contracts])
    df["implied_rate"] = 100.0 - df["settle"]
    return df

# --- 3. MATH & COMPUTATION (From Playbook A3-A5) ---
def post_meeting_rate(contract_rate, prev_rate, meeting_day, days_in_month):
    days_after = days_in_month - meeting_day + 1
    if days_after <= 0: return contract_rate
    return (contract_rate * days_in_month - (meeting_day - 1) * prev_rate) / days_after

def build_meeting_path(zq_strip, effr, fomc_dates):
    path = []
    curr_rate = effr
    for _, row in zq_strip.iterrows():
        m_dates = [d for d in fomc_dates if d.year == row['expiry'].year and d.month == row['expiry'].month]
        if m_dates:
            d_in_m = monthrange(row['expiry'].year, row['expiry'].month)[1]
            post_rate = post_meeting_rate(row['implied_rate'], curr_rate, m_dates[0].day, d_in_m)
            path.append({"date": m_dates[0], "rate": post_rate})
            curr_rate = post_rate
    return pd.DataFrame(path)

# --- 4. VISUALIZATION ---
def plot_strip(df, ocr, title, color):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['expiry'], y=df['implied_rate'], marker_color=color, name="Implied Rate"))
    fig.add_hline(y=ocr, line_dash="dash", line_color="white", annotation_text=f"OCR: {ocr}%")
    fig.update_layout(title=title, template="plotly_dark", plot_bgcolor=CFR['bg'], paper_bgcolor=CFR['bg'])
    return fig

# --- 5. MAIN DASHBOARD ---
st.title("STIR REPLICATION DASHBOARD")
st.caption("CME-FedWatch Style • Fed Funds & SOFR Futures")

# Sidebar
effr_input = st.sidebar.number_input("Effective FFR (OCR)", value=3.64, step=0.01)
sofr_input = st.sidebar.number_input("Spot SOFR", value=3.64, step=0.01)

# Load Data
raw_data = load_mock_data()
fomc_dates = get_fomc_dates()

tab1, tab2 = st.tabs(["PRODUCTS", "MEETINGS"])

with tab1:
    prod = st.radio("Select Product", ["Fed Funds (ZQ)", "SOFR (SR3)"], horizontal=True)
    if "SOFR" in prod:
        view_df = raw_data[raw_data['root'] == "SR3"]
        st.plotly_chart(plot_strip(view_df, effr_input, "SOFR (SR3) Strip", CFR['sofr']), use_container_width=True)
    else:
        view_df = raw_data[raw_data['root'] == "ZQ"]
        st.plotly_chart(plot_strip(view_df, effr_input, "Fed Funds (ZQ) Strip", CFR['ff']), use_container_width=True)

with tab2:
    sub_tab1, sub_tab2 = st.tabs(["STRIP", "SPREADS"])
    zq_data = raw_data[raw_data['root'] == "ZQ"]
    path_df = build_meeting_path(zq_data, effr_input, fomc_dates)
    
    with sub_tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=path_df['date'], y=path_df['rate'], line_shape='hv', line_color=CFR['accent']))
        fig.update_layout(title="Implied Post-Meeting Rate Path", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
    with sub_tab2:
        st.write("Implied Post-Meeting Rates")
        st.dataframe(path_df)
