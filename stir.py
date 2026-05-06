import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta

# --- 1. TERMINAL STYLING (The "CFR Look") ---
st.set_page_config(page_title="STIR Dashboard", layout="wide")

# This CSS forces the app to look like a bloomberg/terminal screen
st.markdown("""
    <style>
        body, [data-testid="stAppViewContainer"] { background-color: #000000; color: #E0E0E0; }
        [data-testid="stHeader"] { background: rgba(0,0,0,0); }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #000000; }
        .stTabs [data-baseweb="tab"] { height: 40px; background-color: #111; color: white; border-radius: 4px; padding: 0 20px; }
        .stTabs [aria-selected="true"] { background-color: #FF6B00 !important; }
        div[data-testid="stExpander"] { background-color: #080808; border: 1px solid #222; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CALCULATIONS FOR THE "SPREADS" MATRIX ---
def get_spread_matrix(data):
    # This creates the diagonal grid shown in your screenshot
    meetings = [d.strftime('%b %y') for d in data['date']]
    rates = data['rate'].values
    matrix = pd.DataFrame(index=meetings, columns=meetings)
    
    for i in range(len(meetings)):
        for j in range(len(meetings)):
            if i < j:
                matrix.iloc[i, j] = f"{(rates[j] - rates[i])*100:+.1f}"
    return matrix

# --- 3. THE "CB LVL" CHART (Central Bank Levels) ---
def plot_cb_levels(df, ocr):
    fig = go.Figure()
    
    # Add the "Rails" (25bp increments)
    for i in np.arange(0, 6, 0.25):
        fig.add_hline(y=i, line=dict(color="#1a1a1a", width=1))

    # Add the Path
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['rate'],
        line=dict(color="#FF6B00", width=3, shape='hv'),
        name="Implied Path"
    ))

    fig.update_layout(
        plot_bgcolor='#000000', paper_bgcolor='#000000',
        yaxis=dict(gridcolor='#222', title="Policy Rate %", tickformat=".2f"),
        xaxis=dict(gridcolor='#222', title="Meeting Date"),
        margin=dict(l=0, r=0, t=20, b=0), height=500
    )
    return fig

# --- 4. DATA & LAYOUT ---
# (Using the logic from the previous step)
fomc_dates = [date(2025, 1, 29), date(2025, 3, 19), date(2025, 5, 7), date(2025, 6, 18),
              date(2025, 7, 30), date(2025, 9, 17), date(2025, 10, 29), date(2025, 12, 10)]
mock_rates = [3.64, 3.45, 3.20, 3.15, 2.90, 2.75, 2.50, 2.50]
df_path = pd.DataFrame({"date": fomc_dates, "rate": mock_rates})

# UI
st.title("REPLICATION PLAYBOOK: US STIR")

tab1, tab2 = st.tabs(["PRODUCTS", "MEETINGS"])

with tab2:
    sub1, sub2, sub3 = st.tabs(["STRIP", "SPREADS", "CB LVL"])
    
    with sub2:
        st.write("MEETING-TO-MEETING SPREADS (BP)")
        matrix = get_spread_matrix(df_path)
        st.dataframe(matrix.style.background_gradient(cmap='RdYlGn', axis=None).format(precision=1))

    with sub3:
        st.write("CB LEVELS - 25BP POLICY RAILS")
        st.plotly_chart(plot_cb_levels(df_path, 3.64), use_container_width=True)
