
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.title("🏢 AFI Stock Dashboard")
st.subheader("Australian Foundation Investment Company")

# Get AFI data
@st.cache_data
def load_data():
    ticker = yf.Ticker("AFI.AX")
    hist = ticker.history(period="1y")
    info = ticker.info
    return hist, info

hist, info = load_data()

# Current price
current_price = hist['Close'].iloc[-1]
prev_price = hist['Close'].iloc[-2]
change = ((current_price - prev_price) / prev_price) * 100

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Current Price", f"${current_price:.2f}", f"{change:+.2f}%")
with col2:
    st.metric("52W High", f"${hist['High'].max():.2f}")
with col3:
    st.metric("52W Low", f"${hist['Low'].min():.2f}")

# Price chart
fig = go.Figure()
fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name='AFI Price', line=dict(color='blue')))
fig.update_layout(title="AFI Stock Price (1 Year)", xaxis_title="Date", yaxis_title="Price (AUD)")
st.plotly_chart(fig, use_container_width=True)

# Volume chart
fig2 = go.Figure()
fig2.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='Volume'))
fig2.update_layout(title="AFI Trading Volume", xaxis_title="Date", yaxis_title="Volume")
st.plotly_chart(fig2, use_container_width=True)

# Company info
st.subheader("Company Information")
col1, col2 = st.columns(2)
with col1:
    st.write(f"**Market Cap:** ${info.get('marketCap', 0):,.0f}")
    st.write(f"**Sector:** {info.get('sector', 'N/A')}")
with col2:
    st.write(f"**Industry:** {info.get('industry', 'N/A')}")
    st.write(f"**Dividend Yield:** {info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "**Dividend Yield:** N/A")
