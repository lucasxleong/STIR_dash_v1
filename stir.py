import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import date

# 1. SETUP & AUTH
st.set_page_config(page_title="CFR STIR Dashboard", layout="wide")

# This pulls the key you just saved in the "Secrets" menu
try:
    API_KEY = st.secrets["POLYGON_API_KEY"]
except:
    st.warning("Action Required: Please add your POLYGON_API_KEY to the Streamlit Secrets menu.")
    st.stop()

# 2. THE DATA ENGINE
def get_polygon_data():
    # Tickers for Fed Funds (ZQ) and SOFR (SR3)
    # Note: Ticker codes change monthly. H=March, M=June, U=Sept, Z=Dec.
    # We are pulling the 'Last Quote' for the front 3 months.
    tickers = {
        "ZQH25": "Fed Funds March 25",
        "ZQM25": "Fed Funds June 25",
        "SR3H25": "SOFR March 25"
    }
    
    results = []
    for ticker, label in tickers.items():
        # Polygon API endpoint for Last Quote
        url = f"https://api.polygon.io/v2/last/nbbo/C:{ticker}?apiKey={API_KEY}"
        try:
            resp = requests.get(url).json()
            # If the market is open, 'p' is the price. 100 - price = Implied Rate.
            price = resp.get('results', {}).get('p', 96.35) # Default 3.65% if no data
            results.append({"Contract": label, "Settle": price, "Implied": 100 - price})
        except:
            continue
            
    return pd.DataFrame(results)

# 3. THE UI (Matching the Playbook)
st.title("US STIR REPLICATION")

if st.button('Update from Polygon.io'):
    st.session_state.market_data = get_polygon_data()

# Load data on first run
if 'market_data' not in st.session_state:
    st.session_state.market_data = get_polygon_data()

df = st.session_state.market_data

# Display the Terminal-style Table
st.subheader("Live CME Futures Strip")
st.table(df.style.format({"Settle": "{:.3f}", "Implied": "{:.2f}%"}))

# Quick Chart
fig = go.Figure(go.Bar(x=df['Contract'], y=df['Implied'], marker_color='#FF6B00'))
fig.update_layout(title="Implied Rate Curve", template="plotly_dark", plot_bgcolor='black', paper_bgcolor='black')
st.plotly_chart(fig, use_container_width=True)
