
# AI Portfolio Engine v13 (Full System + ETF Upgrade Engine)

import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# ======================
# SAMPLE DATA (simplified)
# ======================

data = [
    ["NDQ","NVDA",8.5],
    ["SEMI","NVDA",12.0],
    ["NDQ","MSFT",7.8],
    ["IVV","MSFT",7.0],
    ["AINF","CEG",3.6],
    ["AINF","NEE",3.3],
]

df = pd.DataFrame(data, columns=["ETF","Ticker","Weight"])

DEFAULT_WEIGHTS = {
    "IVV":22,
    "NDQ":22,
    "VHY":24,
    "AINF":4,
    "SEMI":4,
    "CRYP":2
}

# ======================
# INPUT
# ======================

st.sidebar.header("Portfolio Weights")

weights = {}
for etf in DEFAULT_WEIGHTS:
    weights[etf] = st.sidebar.number_input(etf,0,100,DEFAULT_WEIGHTS[etf])

total = sum(weights.values())
norm = {k:v/total for k,v in weights.items()}

# ======================
# ETF TRANSLATION ENGINE
# ======================

def best_etf_for_company_dynamic(ticker):
    matches = df[df["Ticker"] == ticker].copy()
    if matches.empty:
        return "No ETF route"

    matches["ETF Weight"] = matches["ETF"].map(norm).fillna(0)
    matches["Score"] = matches["Weight"] * (1 + matches["ETF Weight"])
    return matches.sort_values("Score", ascending=False).iloc[0]["ETF"]

# ======================
# SAMPLE SIGNALS
# ======================

signals = pd.DataFrame([
    ["NVDA","STRONG BUY",95],
    ["MSFT","BUY",80],
    ["CEG","BUY",85]
], columns=["Ticker","Signal","Score"])

# ======================
# ETF DEMAND AGGREGATION
# ======================

def aggregate_etf_demand():
    demand = {}

    for _, row in signals.iterrows():
        ticker = row["Ticker"]
        score = row["Score"]

        matches = df[df["Ticker"] == ticker]

        for _, m in matches.iterrows():
            etf = m["ETF"]
            demand[etf] = demand.get(etf,0) + score * m["Weight"]

    return pd.DataFrame([
        {"ETF":k,"Demand":v}
        for k,v in demand.items()
    ]).sort_values("Demand",ascending=False)

# ======================
# ETF UPGRADE ENGINE
# ======================

def etf_upgrade_engine():
    missing = []
    all_signal_tickers = set(signals["Ticker"])
    covered = set(df["Ticker"])

    for t in all_signal_tickers:
        if t not in covered:
            missing.append(t)

    return missing

# ======================
# UI
# ======================

st.title("AI Portfolio Engine v13")

tab1, tab2, tab3 = st.tabs([
    "Radar",
    "ETF Demand",
    "ETF Upgrade Engine"
])

# ======================
# RADAR
# ======================

with tab1:
    st.subheader("Signals")

    signals["Best ETF"] = signals["Ticker"].apply(best_etf_for_company_dynamic)

    st.dataframe(signals)

# ======================
# ETF DEMAND
# ======================

with tab2:
    st.subheader("ETF Demand")

    demand = aggregate_etf_demand()

    st.dataframe(demand)

    st.bar_chart(demand.set_index("ETF"))

# ======================
# ETF UPGRADE ENGINE
# ======================

with tab3:
    st.subheader("ETF Upgrade Engine")

    missing = etf_upgrade_engine()

    if not missing:
        st.success("All signals covered by current ETFs")
    else:
        st.warning("Missing exposure detected")

        for m in missing:
            st.write(f"Missing: {m}")

