
import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI Portfolio Engine v5", layout="wide")

# ================================
# Sample holdings
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

# Target AI universe
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
def get_weights(key_prefix):
    etfs = sorted(df["ETF"].unique())
    weights = {}
    cols = st.columns(len(etfs))

    for i, etf in enumerate(etfs):
        with cols[i]:
            weights[etf] = st.number_input(
                label=f"{etf} %",
                min_value=0.0,
                max_value=100.0,
                value=float(DEFAULT_WEIGHTS.get(etf,0.0)),
                step=1.0,
                key=f"{key_prefix}_{etf}_weight"
            )

    total = sum(weights.values())

    if abs(total - 100) > 0.1:
        st.warning(f"Total {total:.1f}%, normalising.")
    else:
        st.success("Weights total 100%.")

    norm = {k:(v/total if total else 0) for k,v in weights.items()}
    return norm

def calc_lookthrough(norm):
    work = df.copy()
    work["ETF Weight"] = work["ETF"].map(norm).fillna(0)
    work["Exposure"] = work["ETF Weight"] * work["Weight"]
    return work

def get_current_exposure(norm):
    work = calc_lookthrough(norm)
    current = work.groupby("Ticker", as_index=False)["Exposure"].sum()
    merged = target_df.merge(current, on="Ticker", how="left").fillna(0)
    return merged, work

# ================================
# App
# ================================
st.title("⚡ AI Portfolio Engine v5")
st.caption("Gap Engine + Buy Signals — fixed widget keys")

tabs = st.tabs(["Portfolio","Overlap","Gap Engine","Buy Signals"])

# Portfolio
with tabs[0]:
    st.subheader("Portfolio")
    norm = get_weights("portfolio")
    work = calc_lookthrough(norm)

    res = (
        work.groupby(["Ticker","Company"],as_index=False)["Exposure"]
        .sum()
        .sort_values("Exposure",ascending=False)
    )

    st.dataframe(res, use_container_width=True, hide_index=True)

    if not res.empty:
        st.bar_chart(res.set_index("Company")["Exposure"])

# Overlap
with tabs[1]:
    st.subheader("Overlap Engine")
    norm = get_weights("overlap")
    work = calc_lookthrough(norm)

    overlap = (
        work.groupby(["Ticker","Company"],as_index=False)
        .agg(
            Exposure=("Exposure","sum"),
            ETF_Count=("ETF","nunique"),
            ETFs=("ETF", lambda x: ", ".join(sorted(set(x))))
        )
        .sort_values("Exposure",ascending=False)
    )

    st.dataframe(overlap, use_container_width=True, hide_index=True)

    st.markdown("### Overlap Risks")
    risks = overlap[overlap["ETF_Count"] >= 2]

    if risks.empty:
        st.success("No overlap risk detected.")
    else:
        st.dataframe(risks, use_container_width=True, hide_index=True)

# Gap Engine
with tabs[2]:
    st.subheader("Company Gap Engine")
    norm = get_weights("gap")
    merged, work = get_current_exposure(norm)

    st.markdown("### Missing AI Exposure")
    gaps = merged[merged["Exposure"] == 0].sort_values("Category")
    st.dataframe(gaps, use_container_width=True, hide_index=True)

    st.markdown("### Underweight Exposure (<1%)")
    under = merged[(merged["Exposure"] > 0) & (merged["Exposure"] < 1)].sort_values("Exposure")
    st.dataframe(under, use_container_width=True, hide_index=True)

    st.markdown("### Full Target Universe")
    st.dataframe(merged.sort_values("Exposure", ascending=False), use_container_width=True, hide_index=True)

# Buy Signals
with tabs[3]:
    st.subheader("Buy Signals")
    norm = get_weights("signals")
    merged, work = get_current_exposure(norm)

    signal_rows = []

    for _, row in merged.iterrows():
        if row["Exposure"] == 0:
            signal = "BUY"
            reason = "Missing exposure"
        elif row["Exposure"] < 1:
            signal = "ADD"
            reason = f"Low exposure: {row['Exposure']:.2f}%"
        elif row["Exposure"] > 5:
            signal = "LIMIT"
            reason = f"High exposure: {row['Exposure']:.2f}%"
        else:
            signal = "HOLD"
            reason = f"Exposure acceptable: {row['Exposure']:.2f}%"

        signal_rows.append({
            "Signal": signal,
            "Ticker": row["Ticker"],
            "Company": row["Company"],
            "Category": row["Category"],
            "Exposure": round(row["Exposure"], 2),
            "Reason": reason,
        })

    signals_df = pd.DataFrame(signal_rows)

    priority_order = {"BUY": 1, "ADD": 2, "LIMIT": 3, "HOLD": 4}
    signals_df["Priority"] = signals_df["Signal"].map(priority_order)
    signals_df = signals_df.sort_values(["Priority","Category","Company"]).drop(columns=["Priority"])

    st.dataframe(signals_df, use_container_width=True, hide_index=True)

    st.markdown("### Action Summary")
    buy_count = len(signals_df[signals_df["Signal"] == "BUY"])
    add_count = len(signals_df[signals_df["Signal"] == "ADD"])
    limit_count = len(signals_df[signals_df["Signal"] == "LIMIT"])

    c1, c2, c3 = st.columns(3)
    c1.metric("BUY signals", buy_count)
    c2.metric("ADD signals", add_count)
    c3.metric("LIMIT signals", limit_count)
