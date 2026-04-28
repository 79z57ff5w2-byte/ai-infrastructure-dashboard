
import streamlit as st
import pandas as pd
import datetime as dt
import yfinance as yf

st.set_page_config(page_title="AI Portfolio Engine v10", layout="wide")

# ============================================================
# Ticker mapping
# ============================================================

# Map internal ticker labels to Yahoo Finance tickers.
# Update this map as you expand the universe.
YAHOO_TICKER_MAP = {
    "NVDA": "NVDA",
    "MSFT": "MSFT",
    "GOOGL": "GOOGL",
    "AMZN": "AMZN",
    "META": "META",
    "TSM": "TSM",
    "ASML": "ASML",
    "AVGO": "AVGO",
    "AMD": "AMD",
    "INTC": "INTC",
    "CEG": "CEG",
    "NEE": "NEE",
    "GEV": "GEV",
    "CCO": "CCJ",      # Cameco US ADR equivalent
    "EQIX": "EQIX",
    "DLR": "DLR",
    "VRT": "VRT",
    "ETN": "ETN",
    "PLTR": "PLTR",
    "SNOW": "SNOW",
    "ADBE": "ADBE",
    "CRM": "CRM",
    "NOW": "NOW",
    "TSLA": "TSLA",
    "ORCL": "ORCL",
    "IBM": "IBM",
    "COIN": "COIN",
    "IREN": "IREN",
    "HUT": "HUT",
    "CLSK": "CLSK",
    "RIOT": "RIOT",
    "MARA": "MARA",
    "CIFR": "CIFR",
    "MSTR": "MSTR",

    # ASX ETFs if needed later
    "IVV.AX": "IVV.AX",
    "NDQ.AX": "NDQ.AX",
    "VHY.AX": "VHY.AX",
    "VEU.AX": "VEU.AX",
    "SEMI.AX": "SEMI.AX",
    "CRYP.AX": "CRYP.AX",
    "GXAI.AX": "GXAI.AX",
}

# ============================================================
# Sample current signals
# Replace this with your dynamic ranking output later.
# ============================================================

SAMPLE_SIGNALS = [
    ["CEG", "Energy & Power Infrastructure", "STRONG BUY", 95],
    ["EQIX", "Data Centers & Physical Infrastructure", "BUY", 82],
    ["TSM", "Compute Hardware & Semiconductors", "BUY", 78],
    ["ASML", "Compute Hardware & Semiconductors", "ADD", 68],
    ["PLTR", "Data & Input Layer", "ADD", 60],
    ["IREN", "Crypto AI Pivot", "OPTIONALITY", 55],
    ["NVDA", "Compute Hardware & Semiconductors", "LIMIT", 20],
]

current_signals = pd.DataFrame(
    SAMPLE_SIGNALS,
    columns=["Ticker", "Layer", "Signal", "Gap Score"]
)

# ============================================================
# Session state
# ============================================================

if "signal_history" not in st.session_state:
    st.session_state.signal_history = pd.DataFrame(columns=[
        "Signal ID",
        "Date Logged",
        "Ticker",
        "Yahoo Ticker",
        "Layer",
        "Signal",
        "Gap Score",
        "Entry Price",
        "Price 7D",
        "Return 7D %",
        "Price 30D",
        "Return 30D %",
        "Price 90D",
        "Return 90D %",
        "Status"
    ])

# ============================================================
# Market data helpers
# ============================================================

@st.cache_data(ttl=3600)
def get_price_on_or_after(yahoo_ticker: str, target_date: dt.date, lookahead_days: int = 7):
    """
    Returns the first available adjusted close price on or after target_date.
    Uses a lookahead window to handle weekends/holidays.
    """
    try:
        start = pd.Timestamp(target_date)
        end = pd.Timestamp(target_date + dt.timedelta(days=lookahead_days + 2))

        data = yf.download(
            yahoo_ticker,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True
        )

        if data is None or data.empty:
            return None

        # Prefer Close because auto_adjust=True already adjusts.
        close = data["Close"].dropna()

        if close.empty:
            return None

        return float(close.iloc[0])

    except Exception:
        return None

@st.cache_data(ttl=3600)
def get_latest_price(yahoo_ticker: str):
    try:
        data = yf.download(
            yahoo_ticker,
            period="5d",
            progress=False,
            auto_adjust=True
        )

        if data is None or data.empty:
            return None

        close = data["Close"].dropna()

        if close.empty:
            return None

        return float(close.iloc[-1])

    except Exception:
        return None

def calculate_return(entry_price, exit_price):
    if entry_price is None or exit_price is None:
        return None
    if entry_price == 0:
        return None
    return round(((exit_price / entry_price) - 1) * 100, 2)

def resolve_yahoo_ticker(ticker):
    return YAHOO_TICKER_MAP.get(ticker, ticker)

def log_signals(signals_df):
    today = dt.date.today()
    history = st.session_state.signal_history.copy()
    new_rows = []

    actionable = signals_df[signals_df["Signal"].isin(["STRONG BUY", "BUY", "ADD", "OPTIONALITY"])].copy()

    for _, row in actionable.iterrows():
        ticker = row["Ticker"]
        yahoo_ticker = resolve_yahoo_ticker(ticker)
        entry_price = get_price_on_or_after(yahoo_ticker, today)

        signal_id = f"{today}_{ticker}_{row['Signal']}_{len(history) + len(new_rows) + 1}"

        new_rows.append({
            "Signal ID": signal_id,
            "Date Logged": today.isoformat(),
            "Ticker": ticker,
            "Yahoo Ticker": yahoo_ticker,
            "Layer": row["Layer"],
            "Signal": row["Signal"],
            "Gap Score": row["Gap Score"],
            "Entry Price": entry_price,
            "Price 7D": None,
            "Return 7D %": None,
            "Price 30D": None,
            "Return 30D %": None,
            "Price 90D": None,
            "Return 90D %": None,
            "Status": "Logged"
        })

    if new_rows:
        st.session_state.signal_history = pd.concat(
            [history, pd.DataFrame(new_rows)],
            ignore_index=True
        )

def refresh_signal_returns():
    if st.session_state.signal_history.empty:
        return

    today = dt.date.today()
    history = st.session_state.signal_history.copy()

    for idx, row in history.iterrows():
        logged = dt.date.fromisoformat(str(row["Date Logged"]))
        yahoo_ticker = row["Yahoo Ticker"]
        entry = row["Entry Price"]

        if pd.isna(entry) or entry is None:
            entry = get_price_on_or_after(yahoo_ticker, logged)
            history.at[idx, "Entry Price"] = entry

        # 7D
        if (today - logged).days >= 7 and pd.isna(row["Price 7D"]):
            price_7d = get_price_on_or_after(yahoo_ticker, logged + dt.timedelta(days=7))
            history.at[idx, "Price 7D"] = price_7d
            history.at[idx, "Return 7D %"] = calculate_return(entry, price_7d)

        # 30D
        if (today - logged).days >= 30 and pd.isna(row["Price 30D"]):
            price_30d = get_price_on_or_after(yahoo_ticker, logged + dt.timedelta(days=30))
            history.at[idx, "Price 30D"] = price_30d
            history.at[idx, "Return 30D %"] = calculate_return(entry, price_30d)

        # 90D
        if (today - logged).days >= 90 and pd.isna(row["Price 90D"]):
            price_90d = get_price_on_or_after(yahoo_ticker, logged + dt.timedelta(days=90))
            history.at[idx, "Price 90D"] = price_90d
            history.at[idx, "Return 90D %"] = calculate_return(entry, price_90d)

        # Status
        age = (today - logged).days
        if age < 7:
            status = "Waiting for 7D"
        elif age < 30:
            status = "7D measured"
        elif age < 90:
            status = "30D measured"
        else:
            status = "90D measured"

        history.at[idx, "Status"] = status

    st.session_state.signal_history = history

def performance_summary(history):
    if history.empty:
        return pd.DataFrame()

    rows = []

    for horizon in ["7D", "30D", "90D"]:
        col = f"Return {horizon} %"
        valid = history[pd.notna(history[col])].copy()

        if valid.empty:
            continue

        rows.append({
            "Horizon": horizon,
            "Signals Measured": len(valid),
            "Average Return %": round(valid[col].mean(), 2),
            "Median Return %": round(valid[col].median(), 2),
            "Win Rate %": round((valid[col] > 0).mean() * 100, 1),
            "Best Return %": round(valid[col].max(), 2),
            "Worst Return %": round(valid[col].min(), 2)
        })

    return pd.DataFrame(rows)

def layer_summary(history, horizon="30D"):
    col = f"Return {horizon} %"
    if history.empty or col not in history.columns:
        return pd.DataFrame()

    valid = history[pd.notna(history[col])].copy()

    if valid.empty:
        return pd.DataFrame()

    out = (
        valid.groupby("Layer", as_index=False)
        .agg(
            Signals=("Ticker", "count"),
            Avg_Return=(col, "mean"),
            Median_Return=(col, "median"),
            Win_Rate=(col, lambda x: (x > 0).mean() * 100)
        )
    )

    out["Avg_Return"] = out["Avg_Return"].round(2)
    out["Median_Return"] = out["Median_Return"].round(2)
    out["Win_Rate"] = out["Win_Rate"].round(1)

    return out.sort_values("Avg_Return", ascending=False)

# ============================================================
# UI
# ============================================================

st.title("📊 AI Portfolio Engine v10")
st.caption("Signal Performance Tracker with real market data via yfinance")

tabs = st.tabs([
    "Current Signals",
    "Signal Tracker",
    "Performance Analysis",
    "Ticker Mapping",
    "Instructions"
])

# ============================================================
# Current signals
# ============================================================

with tabs[0]:
    st.subheader("Current Signals")
    st.write("These are sample signals for now. Later, this tab can be connected directly to your v8 Weighted Buy Signals output.")

    st.dataframe(current_signals, use_container_width=True, hide_index=True)

    if st.button("Log actionable signals with real entry prices"):
        log_signals(current_signals)
        st.success("Signals logged with entry prices where available.")

    st.markdown("### Latest Price Check")
    price_rows = []

    for ticker in current_signals["Ticker"].unique():
        yahoo_ticker = resolve_yahoo_ticker(ticker)
        latest = get_latest_price(yahoo_ticker)
        price_rows.append({
            "Ticker": ticker,
            "Yahoo Ticker": yahoo_ticker,
            "Latest Price": latest
        })

    st.dataframe(pd.DataFrame(price_rows), use_container_width=True, hide_index=True)

# ============================================================
# Tracker
# ============================================================

with tabs[1]:
    st.subheader("Signal Tracker")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Refresh real market returns"):
            refresh_signal_returns()
            st.success("Signal returns refreshed.")

    with c2:
        if st.button("Clear signal history"):
            st.session_state.signal_history = st.session_state.signal_history.iloc[0:0]
            st.success("Signal history cleared.")

    history = st.session_state.signal_history.copy()

    if history.empty:
        st.info("No signals logged yet.")
    else:
        st.dataframe(history, use_container_width=True, hide_index=True)

# ============================================================
# Performance Analysis
# ============================================================

with tabs[2]:
    st.subheader("Performance Analysis")

    history = st.session_state.signal_history.copy()

    if history.empty:
        st.info("No logged signal history yet.")
    else:
        summary = performance_summary(history)

        if summary.empty:
            st.warning("Signals are logged, but not enough time has passed to calculate forward returns.")
        else:
            st.markdown("### Overall Performance")
            st.dataframe(summary, use_container_width=True, hide_index=True)

            latest_horizon = "30D"
            layer_perf = layer_summary(history, horizon=latest_horizon)

            if layer_perf.empty:
                st.info("No 30D layer performance yet. Try 7D once signals are old enough.")
                layer_perf = layer_summary(history, horizon="7D")
                latest_horizon = "7D"

            if not layer_perf.empty:
                st.markdown(f"### Performance by Layer ({latest_horizon})")
                st.dataframe(layer_perf, use_container_width=True, hide_index=True)
                st.bar_chart(layer_perf.set_index("Layer")["Avg_Return"])

            st.markdown("### Signal Quality by Signal Type")
            valid_cols = [c for c in ["Return 7D %", "Return 30D %", "Return 90D %"] if c in history.columns]

            if valid_cols:
                selected_col = st.selectbox("Return horizon", valid_cols)
                valid = history[pd.notna(history[selected_col])].copy()

                if not valid.empty:
                    signal_perf = (
                        valid.groupby("Signal", as_index=False)
                        .agg(
                            Count=("Ticker", "count"),
                            Avg_Return=(selected_col, "mean"),
                            Win_Rate=(selected_col, lambda x: (x > 0).mean() * 100)
                        )
                    )
                    signal_perf["Avg_Return"] = signal_perf["Avg_Return"].round(2)
                    signal_perf["Win_Rate"] = signal_perf["Win_Rate"].round(1)

                    st.dataframe(signal_perf, use_container_width=True, hide_index=True)

# ============================================================
# Ticker mapping
# ============================================================

with tabs[3]:
    st.subheader("Ticker Mapping")
    st.write("The tracker uses Yahoo Finance tickers. Edit this map in `app.py` when you add new companies or ASX ETFs.")

    mapping_df = pd.DataFrame([
        {"Internal Ticker": k, "Yahoo Finance Ticker": v}
        for k, v in YAHOO_TICKER_MAP.items()
    ])

    st.dataframe(mapping_df, use_container_width=True, hide_index=True)

# ============================================================
# Instructions
# ============================================================

with tabs[4]:
    st.subheader("Instructions")

    st.markdown("""
### How this works

1. The app logs actionable signals:
   - STRONG BUY
   - BUY
   - ADD
   - OPTIONALITY

2. It records the market price at the time of logging.

3. When enough time has passed, click **Refresh real market returns**.

4. The app calculates:
   - 7-day forward return
   - 30-day forward return
   - 90-day forward return

5. You can then analyse:
   - which AI layers perform best
   - which signals work best
   - whether your system is improving decision quality

### Important limitations

- This uses Yahoo Finance via `yfinance`.
- Some tickers may need manual mapping.
- Private companies like OpenAI, Anthropic, Databricks and xAI cannot be tracked directly.
- ASX tickers usually need the `.AX` suffix.
- This is research tooling only, not financial advice.

### Next integration step

The next build can merge this tracker back into your full v8 decision engine so the system logs actual weighted buy signals directly.
""")
