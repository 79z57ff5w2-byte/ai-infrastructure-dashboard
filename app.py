
import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI Portfolio Engine v6", layout="wide")

# ================================
# Sample holdings
# ================================
data = [
    ["IVV","MSFT","Microsoft",7.0],
    ["IVV","NVDA","NVIDIA",6.5],
    ["IVV","AAPL","Apple",6.0],
    ["IVV","AMZN","Amazon",4.0],
    ["IVV","GOOGL","Alphabet",3.5],

    ["NDQ","NVDA","NVIDIA",8.5],
    ["NDQ","MSFT","Microsoft",7.8],
    ["NDQ","AAPL","Apple",7.5],
    ["NDQ","AMZN","Amazon",5.5],
    ["NDQ","AVGO","Broadcom",4.8],
    ["NDQ","GOOGL","Alphabet",4.5],
    ["NDQ","META","Meta Platforms",4.6],

    ["SEMI","NVDA","NVIDIA",12.0],
    ["SEMI","TSM","TSMC",10.0],
    ["SEMI","ASML","ASML",9.0],
    ["SEMI","AVGO","Broadcom",8.0],
    ["SEMI","AMD","AMD",6.0],

    ["AINF","CEG","Constellation Energy",3.6],
    ["AINF","NEE","NextEra Energy",3.3],
    ["AINF","VRT","Vertiv",4.8],
    ["AINF","EQIX","Equinix",4.0],
    ["AINF","DLR","Digital Realty",3.8],

    ["CRYP","COIN","Coinbase",5.0],
    ["CRYP","IREN","IREN Ltd",9.7],
    ["CRYP","HUT","Hut 8 Corp",5.1],
    ["CRYP","CLSK","CleanSpark",4.5],
    ["CRYP","RIOT","Riot Platforms",4.0],
    ["CRYP","MARA","MARA Holdings",4.0],

    ["GXAI","PLTR","Palantir",4.5],
    ["GXAI","SNOW","Snowflake",4.0],
    ["GXAI","NVDA","NVIDIA",8.0],
    ["GXAI","MSFT","Microsoft",7.0],
]

df = pd.DataFrame(data, columns=["ETF","Ticker","Company","Weight"])

# ================================
# Target AI universe with base importance
# ================================
AI_TARGET = [
    ["NVDA","NVIDIA","Compute",100],
    ["TSM","TSMC","Compute",96],
    ["ASML","ASML","Compute",94],
    ["AVGO","Broadcom","Compute",88],
    ["AMD","AMD","Compute",78],

    ["CEG","Constellation Energy","Energy",95],
    ["NEE","NextEra Energy","Energy",86],
    ["GEV","GE Vernova","Energy",84],
    ["CCO","Cameco","Energy",82],

    ["VRT","Vertiv","Data Centers",92],
    ["EQIX","Equinix","Data Centers",88],
    ["DLR","Digital Realty","Data Centers",85],
    ["ETN","Eaton","Data Centers",84],

    ["MSFT","Microsoft","Platforms",90],
    ["AMZN","Amazon","Platforms",86],
    ["GOOGL","Alphabet","Data/Models",86],
    ["META","Meta Platforms","Data/Models",80],
    ["PLTR","Palantir","Data/Models",76],
    ["SNOW","Snowflake","Data/Models",72],

    ["IREN","IREN Ltd","Crypto AI Pivot",62],
    ["HUT","Hut 8 Corp","Crypto AI Pivot",58],
    ["CLSK","CleanSpark","Crypto AI Pivot",56],
    ["RIOT","Riot Platforms","Crypto AI Pivot",55],
    ["MARA","MARA Holdings","Crypto AI Pivot",55],
    ["COIN","Coinbase","Crypto AI Pivot",50],
]

target_df = pd.DataFrame(AI_TARGET, columns=["Ticker","Company","Category","Base Importance"])

DEFAULT_WEIGHTS = {
    "IVV":22.0,
    "NDQ":22.0,
    "SEMI":4.0,
    "AINF":4.0,
    "CRYP":2.0,
    "GXAI":0.0,
}

LAYER_PRESETS = {
    "Balanced AI Growth": {
        "Compute": 1.00,
        "Energy": 1.00,
        "Data Centers": 1.00,
        "Platforms": 0.85,
        "Data/Models": 0.85,
        "Crypto AI Pivot": 0.45,
    },
    "AI Infrastructure / Power Bottleneck": {
        "Compute": 0.85,
        "Energy": 1.30,
        "Data Centers": 1.25,
        "Platforms": 0.75,
        "Data/Models": 0.75,
        "Crypto AI Pivot": 0.55,
    },
    "Semiconductor Heavy": {
        "Compute": 1.35,
        "Energy": 0.85,
        "Data Centers": 0.90,
        "Platforms": 0.75,
        "Data/Models": 0.75,
        "Crypto AI Pivot": 0.40,
    },
    "Crypto AI Pivot Optionality": {
        "Compute": 0.90,
        "Energy": 1.00,
        "Data Centers": 1.05,
        "Platforms": 0.75,
        "Data/Models": 0.75,
        "Crypto AI Pivot": 1.20,
    },
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

def importance_multiplier(category, preset_name):
    return LAYER_PRESETS[preset_name].get(category, 0.70)

def dynamic_gap_score(row, preset_name):
    exposure = row["Exposure"]
    base = row["Base Importance"]
    multiplier = importance_multiplier(row["Category"], preset_name)

    dynamic_importance = base * multiplier

    # Gap penalty: the more you already own, the lower the score.
    # Below 1% exposure remains a meaningful gap.
    exposure_penalty = exposure * 14

    # Concentration penalty kicks in harder above 5%.
    concentration_penalty = max(exposure - 5, 0) * 20

    score = dynamic_importance - exposure_penalty - concentration_penalty
    return max(round(score, 1), 0)

def build_dynamic_ranking(norm, preset_name):
    merged, work = get_current_exposure(norm)

    merged["Layer Multiplier"] = merged["Category"].apply(lambda c: importance_multiplier(c, preset_name))
    merged["Dynamic Importance"] = (merged["Base Importance"] * merged["Layer Multiplier"]).round(1)
    merged["Gap Score"] = merged.apply(lambda r: dynamic_gap_score(r, preset_name), axis=1)

    def signal(row):
        exposure = row["Exposure"]
        score = row["Gap Score"]
        category = row["Category"]

        if exposure > 6:
            return "LIMIT"
        if score >= 90 and exposure < 1:
            return "STRONG BUY"
        if score >= 75:
            return "BUY"
        if score >= 55:
            return "ADD"
        if category == "Crypto AI Pivot" and score >= 35:
            return "OPTIONALITY"
        return "HOLD"

    merged["Signal"] = merged.apply(signal, axis=1)

    def reason(row):
        if row["Signal"] == "LIMIT":
            return f"High current exposure at {row['Exposure']:.2f}%"
        if row["Signal"] in ["STRONG BUY", "BUY"]:
            return f"High importance ({row['Dynamic Importance']:.1f}) and low exposure ({row['Exposure']:.2f}%)"
        if row["Signal"] == "ADD":
            return f"Moderate gap: importance {row['Dynamic Importance']:.1f}, exposure {row['Exposure']:.2f}%"
        if row["Signal"] == "OPTIONALITY":
            return "Crypto / AI infrastructure optionality — keep small"
        return f"Current exposure acceptable at {row['Exposure']:.2f}%"

    merged["Reason"] = merged.apply(reason, axis=1)

    priority = {"STRONG BUY":1, "BUY":2, "ADD":3, "OPTIONALITY":4, "LIMIT":5, "HOLD":6}
    merged["Priority"] = merged["Signal"].map(priority)

    return merged.sort_values(["Priority","Gap Score"], ascending=[True, False])

def suggest_etf_route(ticker):
    matches = df[df["Ticker"] == ticker].sort_values("Weight", ascending=False)
    if matches.empty:
        return "No mapped ETF route in sample data"
    return ", ".join([f"{r['ETF']} ({r['Weight']:.1f}%)" for _, r in matches.head(3).iterrows()])

# ================================
# App
# ================================
st.title("⚡ AI Portfolio Engine v6")
st.caption("Dynamic AI importance ranking + weighted buy signals")

tabs = st.tabs(["Portfolio","Overlap","Gap Engine","Dynamic Ranking","Weighted Buy Signals"])

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

# Dynamic ranking
with tabs[3]:
    st.subheader("Dynamic AI Importance Ranking")
    st.write("This upgrades the old static BUY/ADD/LIMIT rules by weighting companies based on the AI cycle scenario.")

    preset = st.selectbox(
        "Choose AI cycle / thesis preset",
        list(LAYER_PRESETS.keys()),
        key="ranking_preset"
    )

    norm = get_weights("ranking")
    ranking = build_dynamic_ranking(norm, preset)
    ranking["ETF Route"] = ranking["Ticker"].apply(suggest_etf_route)

    st.markdown("### Ranked AI Priority List")
    st.dataframe(
        ranking[[
            "Signal",
            "Ticker",
            "Company",
            "Category",
            "Base Importance",
            "Layer Multiplier",
            "Dynamic Importance",
            "Exposure",
            "Gap Score",
            "ETF Route",
            "Reason"
        ]],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Top Gap Scores")
    top = ranking.sort_values("Gap Score", ascending=False).head(15)
    st.bar_chart(top.set_index("Company")["Gap Score"])

# Weighted Buy Signals
with tabs[4]:
    st.subheader("Weighted Buy Signals")
    st.write("This is the clean decision output: what to prioritise next, adjusted for your AI thesis and current exposure.")

    preset = st.selectbox(
        "Choose signal preset",
        list(LAYER_PRESETS.keys()),
        key="signals_preset"
    )

    contribution = st.number_input(
        "Next contribution amount ($)",
        min_value=0,
        value=3000,
        step=500
    )

    norm = get_weights("signals")
    ranking = build_dynamic_ranking(norm, preset)
    ranking["ETF Route"] = ranking["Ticker"].apply(suggest_etf_route)

    actionable = ranking[ranking["Signal"].isin(["STRONG BUY","BUY","ADD","OPTIONALITY"])].copy()

    if actionable.empty:
        st.success("No high-priority additions detected.")
    else:
        top_actions = actionable.head(5).copy()
        score_sum = top_actions["Gap Score"].sum()

        if score_sum > 0:
            top_actions["Suggested $"] = (top_actions["Gap Score"] / score_sum * contribution).round(0)
        else:
            top_actions["Suggested $"] = 0

        st.markdown("### Suggested Next-Buy Plan")
        st.dataframe(
            top_actions[[
                "Signal",
                "Ticker",
                "Company",
                "Category",
                "Exposure",
                "Gap Score",
                "ETF Route",
                "Suggested $",
                "Reason"
            ]],
            use_container_width=True,
            hide_index=True
        )

    st.markdown("### Limit / Avoid Adding")
    limits = ranking[ranking["Signal"] == "LIMIT"]
    if limits.empty:
        st.success("No major concentration limits detected.")
    else:
        st.dataframe(
            limits[["Ticker","Company","Category","Exposure","Reason"]],
            use_container_width=True,
            hide_index=True
        )
