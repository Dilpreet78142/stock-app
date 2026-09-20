import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from signals import generate_signals, get_latest_signal

# ── Page Config ──
st.set_page_config(
    page_title="📈 Stock Signal Analyzer",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Real-Time Stock Buy/Sell Signal Analyzer")
st.markdown("*Powered by Technical Analysis — RSI, MACD, Bollinger Bands, SMA & more*")
st.divider()

# ── Sidebar ──
with st.sidebar:
    st.header("⚙️ Settings")
    ticker = st.text_input("Stock Ticker", value="AAPL").upper()
    period = st.selectbox(
        "Time Period",
        ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=3,
    )
    interval = st.selectbox(
        "Interval",
        ["1d", "1wk", "1h", "5m"],
        index=0,
    )
    st.caption("⚠️ Intraday intervals (1h, 5m) limited to last 60 days by Yahoo Finance.")
    st.divider()
    st.markdown("### 📊 Indicators Used")
    st.markdown("""
    - ✅ RSI (14)
    - ✅ MACD (12, 26, 9)
    - ✅ SMA (20, 50, 200)
    - ✅ EMA (12, 26)
    - ✅ Bollinger Bands
    - ✅ Stochastic Oscillator
    - ✅ ADX (Trend Strength)
    - ✅ Volume Analysis
    """)

# ── Fetch Data ──
@st.cache_data(ttl=60)
def load_data(ticker, period, interval):
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    if df.empty:
        return df
    # Flatten multi-level columns if present (yfinance >= 0.2.31)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

with st.spinner(f"Fetching live data for **{ticker}**..."):
    df = load_data(ticker, period, interval)

if df.empty:
    st.error(f"❌ No data found for **{ticker}**. Check the ticker symbol.")
    st.stop()

# ── Generate Signals ──
df_signals = generate_signals(df)
latest = get_latest_signal(df_signals)

# ── Top Metrics ──
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("💰 Price", f"${latest['close']}")
col2.metric("📡 Signal", latest["signal"])
col3.metric("📊 Net Score", latest["net_score"])
col4.metric("RSI (14)", latest["rsi"])
col5.metric("ADX", latest["adx"])

# ── Signal Explanation ──
st.divider()
signal = latest["signal"]
if "BUY" in signal:
    st.success(f"### {signal} — {ticker}")
    st.info(
        f"Multiple indicators are bullish. RSI is at **{latest['rsi']}**, "
        f"MACD is **{'above' if latest['macd'] > latest['macd_signal'] else 'below'}** "
        f"its signal line. Bollinger: {latest['bb_position']}."
    )
elif "SELL" in signal:
    st.error(f"### {signal} — {ticker}")
    st.warning(
        f"Multiple indicators are bearish. RSI is at **{latest['rsi']}**, "
        f"MACD is **{'above' if latest['macd'] > latest['macd_signal'] else 'below'}** "
        f"its signal line. Bollinger: {latest['bb_position']}."
    )
else:
    st.info(f"### ⏸️ HOLD — {ticker}")
    st.caption("No strong buy or sell consensus. Wait for clearer signals.")

# ── Charts ──
st.divider()
st.subheader("📉 Price & Indicators Chart")

fig = make_subplots(
    rows=4, cols=1, shared_xaxes=True,
    vertical_spacing=0.03,
    row_heights=[0.45, 0.2, 0.15, 0.2],
    subplot_titles=("Price + Bollinger Bands + SMA", "MACD", "RSI", "Volume"),
)

# Row 1: Price
fig.add_trace(go.Candlestick(
    x=df_signals.index, open=df_signals["Open"], high=df_signals["High"],
    low=df_signals["Low"], close=df_signals["Close"], name="Price",
    increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
), row=1, col=1)

for col_name, color in [("SMA_20", "orange"), ("SMA_50", "blue"), ("SMA_200", "red")]:
    if col_name in df_signals.columns:
        fig.add_trace(go.Scatter(
            x=df_signals.index, y=df_signals[col_name],
            name=col_name, line=dict(width=1, color=color),
        ), row=1, col=1)

fig.add_trace(go.Scatter(
    x=df_signals.index, y=df_signals["BB_Upper"],
    name="BB Upper", line=dict(width=1, dash="dot", color="gray"),
), row=1, col=1)
fig.add_trace(go.Scatter(
    x=df_signals.index, y=df_signals["BB_Lower"],
    name="BB Lower", line=dict(width=1, dash="dot", color="gray"),
    fill="tonexty", fillcolor="rgba(128,128,128,0.1)",
), row=1, col=1)

# Buy/Sell markers
buys = df_signals[df_signals["Signal"].str.contains("BUY")]
sells = df_signals[df_signals["Signal"].str.contains("SELL")]
fig.add_trace(go.Scatter(
    x=buys.index, y=buys["Close"], mode="markers",
    marker=dict(symbol="triangle-up", size=14, color="green"),
    name="Buy Signal",
), row=1, col=1)
fig.add_trace(go.Scatter(
    x=sells.index, y=sells["Close"], mode="markers",
    marker=dict(symbol="triangle-down", size=14, color="red"),
    name="Sell Signal",
), row=1, col=1)

# Row 2: MACD
fig.add_trace(go.Scatter(
    x=df_signals.index, y=df_signals["MACD"],
    name="MACD", line=dict(color="blue", width=1),
), row=2, col=1)
fig.add_trace(go.Scatter(
    x=df_signals.index, y=df_signals["MACD_Signal"],
    name="Signal", line=dict(color="orange", width=1),
), row=2, col=1)
colors = ["green" if v >= 0 else "red" for v in df_signals["MACD_Hist"]]
fig.add_trace(go.Bar(
    x=df_signals.index, y=df_signals["MACD_Hist"],
    name="Histogram", marker_color=colors,
), row=2, col=1)

# Row 3: RSI
fig.add_trace(go.Scatter(
    x=df_signals.index, y=df_signals["RSI"],
    name="RSI", line=dict(color="purple", width=1),
), row=3, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

# Row 4: Volume
vol_colors = ["green" if c >= o else "red" for c, o in zip(df_signals["Close"], df_signals["Open"])]
fig.add_trace(go.Bar(
    x=df_signals.index, y=df_signals["Volume"],
    name="Volume", marker_color=vol_colors, opacity=0.6,
), row=4, col=1)

fig.update_layout(
    height=900, template="plotly_dark",
    xaxis_rangeslider_visible=False,
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)
st.plotly_chart(fig, use_container_width=True)

# ── Signal History Table ──
st.divider()
st.subheader("📋 Recent Signal History")
signal_rows = df_signals[df_signals["Signal"] != "HOLD"].tail(20).copy()
if not signal_rows.empty:
    display_cols = ["Close", "RSI", "MACD", "Signal", "Net_Score"]
    st.dataframe(
        signal_rows[display_cols].sort_index(ascending=False),
        use_container_width=True,
    )
else:
    st.caption("No buy/sell signals in the selected period (all HOLD).")

# ── Disclaimer ──
st.divider()
st.warning(
    "⚠️ **DISCLAIMER:** This tool is for **educational purposes only**. "
    "It does NOT constitute financial advice. Always do your own research "
    "and consult a licensed financial advisor before making investment decisions. "
    "Past performance is not indicative of future results."
)