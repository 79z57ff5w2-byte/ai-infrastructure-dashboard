
import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI Portfolio Engine v5", layout="wide")

# ================================
# Sample holdings (simplified)
# ================================
data = [
    ["IVV","MSFT","Microsoft",7.0],
    ["IVV","NVDA","NVIDIA",6.5],
    ["NDQ","NVDA","NVIDIA",8.5],
    ["NDQ","MSFT","Microsoft",7.8],
    ["SEMI","NVDA","NVIDIA",12.0],
    ["AINF","CEG","Constellation Energy",3.6],
    ["CRYP","COIN","Coinbase",5.0],
    ["GXAI","PLTR","Palantir",4.5],
]

df = pd.DataFrame(data, columns=["ETF","Ticker","Company","Weight"])

# Target AI universe (gap detection)
AI_TARGET = [
    ["NVDA","NVIDIA","Compute"],
    ["MSFT","Microsoft","Platforms"],
    ["GOOGL","Alphabet","Data"],
    ["AMZN","Amazon","Platforms"],
    ["META","Meta","Data"],
    ["TSM","TSMC","Compute"],
    ["ASML","ASML","Compute"],
    ["CEG","Constellation Energy","Energy"],
    ["NEE","NextEra Energy","Energy"],
    ["EQIX","Equinix","Data Centers"],
    ["DLR","Digital Realty","Data Centers"],
    ["PLTR","Palantir","Data"],
]

target_df = pd.DataFrame(AI_TARGET, columns=["Ticker","Company","Category"])

DEFAULT_WEIGHTS = {
    "IVV":22.0,
    "NDQ":22.0,
    "SEMI":4.0,
    "AINF":4.0,
    "CRYP":2.0,
    "GXAI":0.0,
}

# ================================
# Helpers
# ================================
def get_weights():
    etfs = sorted(df["ETF"].unique())
    weights = {}
    cols = st.columns(len(etfs))
    for i, etf in enumerate(etfs):
        with cols[i]:
            weights[etf] = st.number_input(etf,0.0,100.0,float(DEFAULT_WEIGHTS.get(etf,0.0)))
    total = sum(weights.values())
    if total != 100:
        st.warning(f"Total {total}%, normalising")
    norm = {k:(v/total if total else 0) for k,v in weights.items()}
    return norm

def calc_lookthrough(norm):
    work = df.copy()
    work["ETF Weight"] = work["ETF"].map(norm).fillna(0)
    work["Exposure"] = work["ETF Weight"] * work["Weight"]
    return work

# ================================
# App
# ================================
st.title("⚡ AI Portfolio Engine v5")

tabs = st.tabs(["Portfolio","Overlap","Gap Engine","Buy Signals"])

# Portfolio
with tabs[0]:
    norm = get_weights()
    work = calc_lookthrough(norm)
    res = work.groupby(["Ticker","Company"],as_index=False)["Exposure"].sum().sort_values("Exposure",ascending=False)
    st.dataframe(res)

# Overlap
with tabs[1]:
    norm = get_weights()
    work = calc_lookthrough(norm)
    overlap = work.groupby(["Ticker","Company"],as_index=False).agg(
        Exposure=("Exposure","sum"),
        ETF_Count=("ETF","nunique")
    ).sort_values("Exposure",ascending=False)
    st.dataframe(overlap)

# Gap Engine
with tabs[2]:
    st.subheader("Company Gap Engine")

    norm = get_weights()
    work = calc_lookthrough(norm)

    current = work.groupby("Ticker",as_index=False)["Exposure"].sum()
    merged = target_df.merge(current, on="Ticker", how="left").fillna(0)

    gaps = merged[merged["Exposure"] == 0]
    st.markdown("### Missing AI Exposure")
    st.dataframe(gaps)

    st.markdown("### Underweight (<1%)")
    under = merged[(merged["Exposure"] > 0) & (merged["Exposure"] < 1)]
    st.dataframe(under)

# Buy Signals
with tabs[3]:
    st.subheader("Buy Signals")

    norm = get_weights()
    work = calc_lookthrough(norm)

    current = work.groupby("Ticker",as_index=False)["Exposure"].sum()
    merged = target_df.merge(current, on="Ticker", how="left").fillna(0)

    signals = []

    for _, row in merged.iterrows():
        if row["Exposure"] == 0:
            signals.append(f"BUY: {row['Company']} (missing exposure)")
        elif row["Exposure"] < 1:
            signals.append(f"ADD: {row['Company']} (low exposure {row['Exposure']:.2f}%)")
        elif row["Exposure"] > 5:
            signals.append(f"TRIM: {row['Company']} (high exposure {row['Exposure']:.2f}%)")

    if signals:
        for s in signals:
            st.write("- " + s)
    else:
        st.write("No strong signals")

