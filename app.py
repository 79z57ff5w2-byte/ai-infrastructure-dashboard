
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="AI Portfolio Decision Engine",
    page_icon="⚡",
    layout="wide"
)

# -----------------------------
# Core models
# -----------------------------

LAYERS = [
    "Energy",
    "Data Centers",
    "Compute",
    "Data/Models",
    "Platforms/Apps",
    "Crypto AI Pivot",
    "Diversification"
]

LAYER_IMPORTANCE = {
    "Energy": 92,
    "Data Centers": 90,
    "Compute": 98,
    "Data/Models": 78,
    "Platforms/Apps": 75,
    "Crypto AI Pivot": 58,
    "Diversification": 30
}

def classify_holding(company, ticker):
    text = f"{company} {ticker}".lower()

    keyword_map = {
        "Energy": [
            "constellation", "nextera", "duke", "southern", "vistra", "ge vernova",
            "cameco", "uranium", "woodside", "bhp", "freeport", "southern copper"
        ],
        "Data Centers": [
            "equinix", "digital realty", "iron mountain", "coreweave", "vertiv",
            "schneider", "eaton", "super micro", "dell"
        ],
        "Compute": [
            "nvidia", "amd", "broadcom", "asml", "tsmc", "taiwan semiconductor",
            "intel", "qualcomm", "micron", "marvell", "applied materials", "lam research"
        ],
        "Data/Models": [
            "snowflake", "palantir", "databricks", "meta", "alphabet", "google",
            "mongodb", "elastic", "cloudflare"
        ],
        "Platforms/Apps": [
            "microsoft", "amazon", "apple", "salesforce", "adobe", "servicenow",
            "oracle", "ibm", "tesla", "shopify", "intuit", "sap", "accenture"
        ],
        "Crypto AI Pivot": [
            "coinbase", "microstrategy", "strategy", "bitmine", "iren", "hut 8",
            "cleanspark", "riot", "marathon", "mara", "cipher", "bitcoin", "block",
            "galaxy", "mining", "miner"
        ],
    }

    for layer, keywords in keyword_map.items():
        if any(k in text for k in keywords):
            return layer

    return "Diversification"

def layer_score(layer):
    return LAYER_IMPORTANCE.get(layer, 30)

def calculate_holdings_exposures(holdings):
    h = holdings.copy()
    h["Weight"] = pd.to_numeric(h["Weight"], errors="coerce").fillna(0)
    h["AI Layer"] = h.apply(lambda r: classify_holding(str(r["Company"]), str(r["Holding Ticker"])), axis=1)
    h["Layer Score"] = h["AI Layer"].apply(layer_score)
    h["Weighted AI Score"] = h["Weight"] * h["Layer Score"] / 100

    exposures = h.pivot_table(index="ETF", columns="AI Layer", values="Weight", aggfunc="sum", fill_value=0).reset_index()

    for layer in LAYERS:
        if layer not in exposures.columns:
            exposures[layer] = 0.0

    scores = h.groupby("ETF")["Weighted AI Score"].sum().reset_index()
    scores.rename(columns={"Weighted AI Score": "AI Exposure Score"}, inplace=True)

    total_weight = h.groupby("ETF")["Weight"].sum().reset_index()
    total_weight.rename(columns={"Weight": "Mapped Holdings Weight"}, inplace=True)

    result = exposures.merge(scores, on="ETF", how="left").merge(total_weight, on="ETF", how="left")
    result["AI Exposure Score"] = result["AI Exposure Score"].round(1)
    return h, result[["ETF"] + LAYERS + ["AI Exposure Score", "Mapped Holdings Weight"]]

def portfolio_exposure(weights, etf_exposures):
    total = sum(weights.values())
    out = {layer: 0 for layer in LAYERS + ["AI Exposure Score"]}
    if total == 0:
        return out

    for etf, weight in weights.items():
        row = etf_exposures[etf_exposures["ETF"] == etf]
        if row.empty:
            continue
        row = row.iloc[0]
        for layer in LAYERS + ["AI Exposure Score"]:
            out[layer] += (weight / total) * float(row[layer])

    return {k: round(v, 1) for k, v in out.items()}

def calculate_overlap(holdings, weights):
    h = holdings.copy()
    h["Weight"] = pd.to_numeric(h["Weight"], errors="coerce").fillna(0)
    total = sum(weights.values()) or 100
    h["Portfolio ETF Weight"] = h["ETF"].map(weights).fillna(0)
    h["Portfolio Contribution %"] = (h["Portfolio ETF Weight"] / total) * h["Weight"]

    grouped = h.groupby(["Holding Ticker", "Company"], as_index=False).agg(
        Portfolio_Exposure=("Portfolio Contribution %", "sum"),
        ETF_Count=("ETF", "nunique"),
        ETFs=("ETF", lambda x: ", ".join(sorted(set(x)))),
        Max_Single_ETF_Holding=("Weight", "max")
    )

    grouped["AI Layer"] = grouped.apply(
        lambda r: classify_holding(str(r["Company"]), str(r["Holding Ticker"])),
        axis=1
    )

    grouped["Overlap Flag"] = grouped.apply(
        lambda r: "High overlap" if r["ETF_Count"] >= 3 else ("Moderate overlap" if r["ETF_Count"] == 2 else "Single ETF"),
        axis=1
    )

    return grouped.sort_values("Portfolio_Exposure", ascending=False)

def concentration_warnings(overlap_df):
    warnings = []
    if overlap_df.empty:
        return warnings

    top = overlap_df.iloc[0]
    if top["Portfolio_Exposure"] >= 8:
        warnings.append(
            f"High single-company concentration: {top['Company']} is {top['Portfolio_Exposure']:.1f}% of mapped portfolio exposure."
        )

    nvda = overlap_df[overlap_df["Holding Ticker"].str.upper() == "NVDA"]
    if not nvda.empty and nvda.iloc[0]["Portfolio_Exposure"] >= 5:
        warnings.append(
            f"NVIDIA stack risk: NVDA appears across {int(nvda.iloc[0]['ETF_Count'])} ETFs and contributes {nvda.iloc[0]['Portfolio_Exposure']:.1f}% of mapped portfolio exposure."
        )

    crypto = overlap_df[overlap_df["AI Layer"] == "Crypto AI Pivot"]["Portfolio_Exposure"].sum()
    if crypto >= 2:
        warnings.append(
            f"Crypto AI pivot exposure: crypto miners/platforms contribute {crypto:.1f}% of mapped portfolio exposure. This is high-upside but higher-risk optionality."
        )

    compute = overlap_df[overlap_df["AI Layer"] == "Compute"]["Portfolio_Exposure"].sum()
    energy = overlap_df[overlap_df["AI Layer"] == "Energy"]["Portfolio_Exposure"].sum()
    if compute > energy * 3 and compute > 5:
        warnings.append(
            "Compute-heavy imbalance: compute exposure is much larger than energy exposure, which may miss the AI power bottleneck thesis."
        )

    return warnings

def company_importance_rank(company, ticker, layer):
    name = f"{company} {ticker}".lower()
    base = LAYER_IMPORTANCE.get(layer, 30)

    # Company-specific strategic weightings
    boosts = {
        "nvidia": 25,
        "tsmc": 24,
        "asml": 23,
        "broadcom": 20,
        "microsoft": 19,
        "amazon": 17,
        "alphabet": 17,
        "constellation": 18,
        "nextera": 15,
        "equinix": 16,
        "digital realty": 15,
        "vertiv": 20,
        "cameco": 13,
        "ge vernova": 14,
        "palantir": 12,
        "snowflake": 10,
        "meta": 12,
        "coinbase": 8,
        "strategy": 7,
        "bitmine": 7,
        "iren": 8,
        "hut 8": 7,
        "cleanspark": 7,
        "riot": 7,
        "marathon": 7,
        "mara": 7
    }

    boost = 0
    for key, value in boosts.items():
        if key in name:
            boost = max(boost, value)

    return min(base + boost, 100)

def build_company_gap_engine(overlap_df):
    # Critical AI company universe.
    critical_companies = pd.DataFrame([
        ["NVDA", "NVIDIA", "Compute"],
        ["TSM", "TSMC", "Compute"],
        ["ASML", "ASML", "Compute"],
        ["AVGO", "Broadcom", "Compute"],
        ["AMD", "AMD", "Compute"],
        ["AMAT", "Applied Materials", "Compute"],
        ["MSFT", "Microsoft", "Platforms/Apps"],
        ["AMZN", "Amazon", "Platforms/Apps"],
        ["GOOGL", "Alphabet", "Data/Models"],
        ["META", "Meta Platforms", "Data/Models"],
        ["PLTR", "Palantir Technologies", "Data/Models"],
        ["SNOW", "Snowflake", "Data/Models"],
        ["CEG", "Constellation Energy", "Energy"],
        ["NEE", "NextEra Energy", "Energy"],
        ["GEV", "GE Vernova", "Energy"],
        ["CCO", "Cameco Corporation", "Energy"],
        ["VRT", "Vertiv", "Data Centers"],
        ["EQIX", "Equinix", "Data Centers"],
        ["DLR", "Digital Realty", "Data Centers"],
        ["ETN", "Eaton", "Data Centers"],
        ["IREN", "IREN Ltd", "Crypto AI Pivot"],
        ["HUT", "Hut 8 Corp", "Crypto AI Pivot"],
        ["CLSK", "CleanSpark", "Crypto AI Pivot"],
        ["RIOT", "Riot Platforms", "Crypto AI Pivot"],
        ["MARA", "MARA Holdings", "Crypto AI Pivot"],
    ], columns=["Holding Ticker", "Company", "AI Layer"])

    gap = critical_companies.merge(
        overlap_df[["Holding Ticker", "Company", "Portfolio_Exposure", "ETF_Count", "ETFs"]],
        on=["Holding Ticker", "Company"],
        how="left"
    )

    gap["Portfolio_Exposure"] = gap["Portfolio_Exposure"].fillna(0)
    gap["ETF_Count"] = gap["ETF_Count"].fillna(0).astype(int)
    gap["ETFs"] = gap["ETFs"].fillna("None")

    gap["Dynamic Importance Score"] = gap.apply(
        lambda r: company_importance_rank(r["Company"], r["Holding Ticker"], r["AI Layer"]),
        axis=1
    )

    # Gap score rewards important companies with low current exposure.
    # >6% means likely enough / concentration risk.
    gap["Gap Score"] = gap.apply(
        lambda r: max(r["Dynamic Importance Score"] - (r["Portfolio_Exposure"] * 10), 0),
        axis=1
    ).round(1)

    def signal(row):
        exposure = row["Portfolio_Exposure"]
        importance = row["Dynamic Importance Score"]
        if exposure >= 8:
            return "🔴 LIMIT — high concentration"
        if exposure >= 5 and importance >= 90:
            return "🟠 HOLD / WATCH — important but already meaningful"
        if exposure < 1 and importance >= 85:
            return "🟢 ADD — critical gap"
        if exposure < 3 and importance >= 75:
            return "🟡 BUILD — underweight"
        if row["AI Layer"] == "Crypto AI Pivot" and exposure < 3:
            return "🟣 OPTIONALITY — small satellite only"
        return "⚖️ OK / monitor"

    gap["Company-Level Buy Signal"] = gap.apply(signal, axis=1)
    return gap.sort_values(["Gap Score", "Dynamic Importance Score"], ascending=False)

def suggest_etf_for_company(company_row, mapped_holdings):
    ticker = company_row["Holding Ticker"]
    company = company_row["Company"]
    matches = mapped_holdings[
        (mapped_holdings["Holding Ticker"] == ticker) |
        (mapped_holdings["Company"] == company)
    ].copy()

    if matches.empty:
        return "No mapped ETF in starter data"

    matches = matches.sort_values("Weight", ascending=False)
    return ", ".join([f"{r['ETF']} ({r['Weight']:.1f}%)" for _, r in matches.head(3).iterrows()])

def build_decision_plan(company_gap, etf_exposures, mapped_holdings, contribution, target_mode):
    # Focus on top actionable gaps.
    actionable = company_gap[
        company_gap["Company-Level Buy Signal"].str.contains("ADD|BUILD|OPTIONALITY", regex=True)
    ].copy()

    if actionable.empty:
        return pd.DataFrame(columns=["Priority", "Action", "Reason", "ETF Route", "Suggested $"])

    actionable["ETF Route"] = actionable.apply(lambda r: suggest_etf_for_company(r, mapped_holdings), axis=1)
    top = actionable.head(5).copy()

    # Allocate dollars by Gap Score, capped so optionality doesn't dominate.
    weights = top["Gap Score"].clip(lower=0)
    if weights.sum() == 0:
        top["Suggested $"] = 0
    else:
        top["Suggested $"] = (weights / weights.sum() * contribution).round(0)

    top["Priority"] = range(1, len(top) + 1)
    top["Action"] = top["Company-Level Buy Signal"]
    top["Reason"] = top.apply(
        lambda r: f"{r['Company']} is in {r['AI Layer']} with importance {r['Dynamic Importance Score']} and current exposure {r['Portfolio_Exposure']:.1f}%",
        axis=1
    )

    return top[["Priority", "Action", "Company", "AI Layer", "Reason", "ETF Route", "Suggested $"]]

# -----------------------------
# Starter holdings
# -----------------------------

starter_holdings = pd.DataFrame([
    ["IVV", "MSFT", "Microsoft", 7.0],
    ["IVV", "NVDA", "NVIDIA", 6.5],
    ["IVV", "AAPL", "Apple", 6.0],
    ["IVV", "AMZN", "Amazon", 4.0],
    ["IVV", "GOOGL", "Alphabet", 3.5],
    ["IVV", "META", "Meta Platforms", 2.5],
    ["IVV", "AVGO", "Broadcom", 2.0],
    ["IVV", "TSLA", "Tesla", 1.5],
    ["IVV", "JPM", "JPMorgan Chase", 1.3],
    ["IVV", "XOM", "Exxon Mobil", 1.2],

    ["VEU", "ASML", "ASML", 1.5],
    ["VEU", "TSM", "TSMC", 1.4],
    ["VEU", "SAP", "SAP", 1.0],
    ["VEU", "NESN", "Nestle", 1.0],
    ["VEU", "NOVO", "Novo Nordisk", 0.9],
    ["VEU", "TM", "Toyota Motor", 0.8],
    ["VEU", "SHEL", "Shell", 0.7],
    ["VEU", "AZN", "AstraZeneca", 0.7],
    ["VEU", "TCEHY", "Tencent", 0.7],
    ["VEU", "BHP", "BHP Group", 0.6],

    ["NDQ", "NVDA", "NVIDIA", 8.5],
    ["NDQ", "MSFT", "Microsoft", 7.8],
    ["NDQ", "AAPL", "Apple", 7.5],
    ["NDQ", "AMZN", "Amazon", 5.5],
    ["NDQ", "AVGO", "Broadcom", 4.8],
    ["NDQ", "META", "Meta Platforms", 4.6],
    ["NDQ", "GOOGL", "Alphabet", 4.5],
    ["NDQ", "TSLA", "Tesla", 3.0],
    ["NDQ", "COST", "Costco", 2.5],
    ["NDQ", "NFLX", "Netflix", 2.3],

    ["VHY", "BHP", "BHP Group", 10.3],
    ["VHY", "CBA", "Commonwealth Bank of Australia", 9.8],
    ["VHY", "NAB", "National Australia Bank", 6.8],
    ["VHY", "WDS", "Woodside Energy", 6.7],
    ["VHY", "WBC", "Westpac Banking", 6.0],
    ["VHY", "ANZ", "ANZ Group", 5.5],
    ["VHY", "MQG", "Macquarie Group", 3.5],
    ["VHY", "RIO", "Rio Tinto", 3.2],
    ["VHY", "TLS", "Telstra", 2.8],
    ["VHY", "WOW", "Woolworths", 2.5],

    ["AINF", "GEV", "GE Vernova", 5.9],
    ["AINF", "CCO", "Cameco Corporation", 5.4],
    ["AINF", "SCCO", "Southern Copper", 5.4],
    ["AINF", "FCX", "Freeport-McMoRan", 5.0],
    ["AINF", "VRT", "Vertiv", 4.8],
    ["AINF", "ETN", "Eaton", 4.5],
    ["AINF", "EQIX", "Equinix", 4.0],
    ["AINF", "DLR", "Digital Realty", 3.8],
    ["AINF", "CEG", "Constellation Energy", 3.6],
    ["AINF", "NEE", "NextEra Energy", 3.3],

    ["SEMI", "NVDA", "NVIDIA", 12.0],
    ["SEMI", "TSM", "TSMC", 10.0],
    ["SEMI", "ASML", "ASML", 9.0],
    ["SEMI", "AVGO", "Broadcom", 8.0],
    ["SEMI", "AMD", "AMD", 6.0],
    ["SEMI", "AMAT", "Applied Materials", 5.0],
    ["SEMI", "LRCX", "Lam Research", 4.5],
    ["SEMI", "MU", "Micron Technology", 4.0],
    ["SEMI", "QCOM", "Qualcomm", 3.5],
    ["SEMI", "INTC", "Intel", 3.0],

    ["CRYP", "BMNR", "BitMine Immersion Technologies", 10.4],
    ["CRYP", "MSTR", "Strategy Inc", 9.8],
    ["CRYP", "IREN", "IREN Ltd", 9.7],
    ["CRYP", "HUT", "Hut 8 Corp", 5.1],
    ["CRYP", "COIN", "Coinbase Global", 5.0],
    ["CRYP", "CLSK", "CleanSpark", 4.5],
    ["CRYP", "RIOT", "Riot Platforms", 4.0],
    ["CRYP", "MARA", "MARA Holdings", 4.0],
    ["CRYP", "CIFR", "Cipher Mining", 3.6],
    ["CRYP", "GLXY", "Galaxy Digital", 3.2],

    ["GXAI", "NVDA", "NVIDIA", 8.0],
    ["GXAI", "MSFT", "Microsoft", 7.0],
    ["GXAI", "GOOGL", "Alphabet", 6.0],
    ["GXAI", "META", "Meta Platforms", 5.0],
    ["GXAI", "PLTR", "Palantir Technologies", 4.5],
    ["GXAI", "SNOW", "Snowflake", 4.0],
    ["GXAI", "ADBE", "Adobe", 3.5],
    ["GXAI", "NOW", "ServiceNow", 3.0],
    ["GXAI", "CRM", "Salesforce", 3.0],
    ["GXAI", "AMZN", "Amazon", 3.0],
], columns=["ETF", "Holding Ticker", "Company", "Weight"])

# -----------------------------
# App state / data ingestion
# -----------------------------

st.title("⚡ AI Portfolio Decision Engine")
st.caption("Holdings → overlap → company gaps → dynamic AI importance → next-buy actions.")

tabs = st.tabs([
    "Decision Engine",
    "Dynamic Importance Ranking",
    "Company Gap Engine",
    "Overlap Engine",
    "ETF Optimizer",
    "Holdings Engine",
    "Upload Official Holdings",
    "Methodology"
])

with tabs[6]:
    st.subheader("Upload Official Holdings")
    st.write("Upload a CSV with columns: ETF, Holding Ticker, Company, Weight")
    uploaded = st.file_uploader("Upload holdings CSV", type=["csv"])

    st.download_button(
        "Download starter holdings template",
        starter_holdings.to_csv(index=False).encode("utf-8"),
        file_name="holdings_template.csv",
        mime="text/csv"
    )

if "uploaded" in locals() and uploaded:
    try:
        holdings = pd.read_csv(uploaded)
        required_cols = {"ETF", "Holding Ticker", "Company", "Weight"}
        if not required_cols.issubset(set(holdings.columns)):
            st.error("CSV must include columns: ETF, Holding Ticker, Company, Weight")
            holdings = starter_holdings.copy()
        else:
            st.success("Official holdings uploaded successfully. The engine is using your uploaded data.")
    except Exception as e:
        st.error(f"Could not read uploaded file: {e}")
        holdings = starter_holdings.copy()
else:
    holdings = starter_holdings.copy()

mapped_holdings, etf_exposures = calculate_holdings_exposures(holdings)

default_weights = {
    "IVV": 22.0,
    "VEU": 22.0,
    "NDQ": 22.0,
    "VHY": 24.0,
    "AINF": 4.0,
    "SEMI": 4.0,
    "CRYP": 2.0,
    "GXAI": 0.0
}

available_etfs = sorted(etf_exposures["ETF"].unique().tolist())

# -----------------------------
# Sidebar shared inputs
# -----------------------------

with st.sidebar:
    st.header("Portfolio Inputs")
    st.caption("Used across the decision engine.")
    weights = {}
    for etf in available_etfs:
        weights[etf] = st.number_input(
            f"{etf} weight %",
            min_value=0.0,
            max_value=100.0,
            value=float(default_weights.get(etf, 0.0)),
            step=1.0,
            key=f"shared_weight_{etf}"
        )

    contribution = st.number_input(
        "Next contribution amount ($)",
        min_value=0,
        value=3000,
        step=500
    )

    target_mode = st.selectbox(
        "Target mode",
        ["Balanced AI Growth", "AI Infrastructure Tilt", "Semiconductor Heavy", "Crypto AI Pivot"]
    )

target_presets = {
    "Balanced AI Growth": {"Energy": 5, "Data Centers": 5, "Compute": 12, "Data/Models": 8, "Platforms/Apps": 14, "Crypto AI Pivot": 1},
    "AI Infrastructure Tilt": {"Energy": 8, "Data Centers": 8, "Compute": 15, "Data/Models": 4, "Platforms/Apps": 8, "Crypto AI Pivot": 1},
    "Semiconductor Heavy": {"Energy": 2, "Data Centers": 2, "Compute": 25, "Data/Models": 3, "Platforms/Apps": 8, "Crypto AI Pivot": 1},
    "Crypto AI Pivot": {"Energy": 3, "Data Centers": 4, "Compute": 10, "Data/Models": 4, "Platforms/Apps": 8, "Crypto AI Pivot": 5},
}

target = target_presets[target_mode]
current_profile = portfolio_exposure(weights, etf_exposures)
overlap = calculate_overlap(mapped_holdings, weights)
company_gap = build_company_gap_engine(overlap)
decision_plan = build_decision_plan(company_gap, etf_exposures, mapped_holdings, contribution, target_mode)

# -----------------------------
# Decision Engine
# -----------------------------

with tabs[0]:
    st.subheader("Full Decision Engine")
    st.write("This tab combines the optimizer, overlap engine, gap engine, and company-level buy signals into one action plan.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Portfolio AI Score", current_profile["AI Exposure Score"])
    c2.metric("Compute", current_profile["Compute"])
    c3.metric("Energy", current_profile["Energy"])
    c4.metric("Data Centers", current_profile["Data Centers"])

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Data/Models", current_profile["Data/Models"])
    c6.metric("Platforms/Apps", current_profile["Platforms/Apps"])
    c7.metric("Crypto AI Pivot", current_profile["Crypto AI Pivot"])
    c8.metric("Diversification", current_profile["Diversification"])

    st.markdown("### Key Warnings")
    warnings = concentration_warnings(overlap)
    if warnings:
        for warning in warnings:
            st.warning(warning)
    else:
        st.success("No major concentration warnings detected in mapped holdings.")

    st.markdown("### Recommended Next-Buy Action Plan")
    st.dataframe(decision_plan, use_container_width=True, hide_index=True)

    if not decision_plan.empty:
        top_action = decision_plan.iloc[0]
        st.success(
            f"Top action: {top_action['Action']} — {top_action['Company']} via {top_action['ETF Route']}"
        )

    st.markdown("### Why this decision?")
    st.write(
        "The engine prioritises critical AI companies that are strategically important, under-owned in your current ETF mix, and accessible through your mapped ETFs."
    )

# -----------------------------
# Dynamic Importance Ranking
# -----------------------------

with tabs[1]:
    st.subheader("Dynamic AI Importance Ranking")
    st.write("Ranks critical AI companies by strategic importance, then compares that to your actual exposure.")

    ranking = company_gap.sort_values("Dynamic Importance Score", ascending=False)
    st.dataframe(
        ranking[[
            "Holding Ticker",
            "Company",
            "AI Layer",
            "Dynamic Importance Score",
            "Portfolio_Exposure",
            "ETF_Count",
            "ETFs",
            "Company-Level Buy Signal"
        ]],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Importance vs Exposure")
    chart = ranking.set_index("Company")[["Dynamic Importance Score", "Portfolio_Exposure"]].head(15)
    st.bar_chart(chart)

# -----------------------------
# Company Gap Engine
# -----------------------------

with tabs[2]:
    st.subheader("Company Gap Engine")
    st.write("Shows critical AI companies you are missing or underweight, then maps them to ETFs.")

    gap_view = company_gap.copy()
    gap_view["ETF Route"] = gap_view.apply(lambda r: suggest_etf_for_company(r, mapped_holdings), axis=1)

    st.dataframe(
        gap_view[[
            "Holding Ticker",
            "Company",
            "AI Layer",
            "Dynamic Importance Score",
            "Portfolio_Exposure",
            "Gap Score",
            "Company-Level Buy Signal",
            "ETF Route"
        ]],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Highest Gap Scores")
    st.bar_chart(gap_view.head(15).set_index("Company")["Gap Score"])

# -----------------------------
# Overlap Engine
# -----------------------------

with tabs[3]:
    st.subheader("Overlap Engine")
    st.write("Shows hidden company-level concentration across ETFs.")

    st.dataframe(
        overlap[[
            "Holding Ticker",
            "Company",
            "AI Layer",
            "Portfolio_Exposure",
            "ETF_Count",
            "ETFs",
            "Overlap Flag"
        ]],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Top 10 Company Exposures")
    st.bar_chart(overlap.head(10).set_index("Company")["Portfolio_Exposure"])

    st.markdown("### Layer-Level Contribution")
    layer_overlap = overlap.groupby("AI Layer", as_index=False)["Portfolio_Exposure"].sum().sort_values("Portfolio_Exposure", ascending=False)
    st.dataframe(layer_overlap, use_container_width=True, hide_index=True)
    st.bar_chart(layer_overlap.set_index("AI Layer")["Portfolio_Exposure"])

# -----------------------------
# ETF Optimizer
# -----------------------------

with tabs[4]:
    st.subheader("ETF Optimizer")

    st.markdown(f"### Target Mode: {target_mode}")
    gaps = {layer: round(target[layer] - current_profile.get(layer, 0), 1) for layer in target}
    gap_df = pd.DataFrame([{"Layer": k, "Current": current_profile[k], "Target": v, "Gap": gaps[k]} for k, v in target.items()])
    st.dataframe(gap_df, use_container_width=True, hide_index=True)

    ranked = etf_exposures.copy()

    def etf_optimizer_score(row):
        score = 0
        for layer, target_value in target.items():
            gap = max(target_value - current_profile.get(layer, 0), 0)
            score += gap * row[layer]
        score += row["AI Exposure Score"] * 2
        return round(score, 1)

    ranked["Optimizer Score"] = ranked.apply(etf_optimizer_score, axis=1)
    ranked = ranked.sort_values("Optimizer Score", ascending=False)

    st.markdown("### Suggested ETF Buy Priority")
    st.dataframe(
        ranked[["ETF", "AI Exposure Score", "Energy", "Data Centers", "Compute", "Data/Models", "Platforms/Apps", "Crypto AI Pivot", "Optimizer Score"]],
        use_container_width=True,
        hide_index=True
    )

    top3 = ranked.head(3).copy()
    positive = top3["Optimizer Score"].clip(lower=0)
    if positive.sum() > 0:
        top3["Suggested $"] = (positive / positive.sum() * contribution).round(0)
    else:
        top3["Suggested $"] = 0

    st.markdown("### No-Sell ETF Allocation Plan")
    st.dataframe(top3[["ETF", "Optimizer Score", "Suggested $"]], use_container_width=True, hide_index=True)

# -----------------------------
# Holdings Engine
# -----------------------------

with tabs[5]:
    st.subheader("Holdings Engine")
    st.write("Every holding is mapped to an AI layer.")

    etf_filter = st.multiselect(
        "ETF filter",
        sorted(mapped_holdings["ETF"].unique()),
        default=sorted(mapped_holdings["ETF"].unique())
    )

    layer_filter = st.multiselect(
        "AI layer filter",
        sorted(mapped_holdings["AI Layer"].unique()),
        default=sorted(mapped_holdings["AI Layer"].unique())
    )

    view = mapped_holdings[
        mapped_holdings["ETF"].isin(etf_filter)
        & mapped_holdings["AI Layer"].isin(layer_filter)
    ].sort_values(["ETF", "Weight"], ascending=[True, False])

    st.dataframe(view, use_container_width=True, hide_index=True)

    st.markdown("### ETF Exposure Table")
    st.dataframe(etf_exposures.sort_values("AI Exposure Score", ascending=False), use_container_width=True, hide_index=True)

# -----------------------------
# Methodology
# -----------------------------

with tabs[7]:
    st.subheader("Methodology")

    st.markdown("""
### What this full decision engine does

The app now runs a complete decision loop:

1. **Holdings Engine**  
   Maps ETF holdings to AI layers.

2. **Overlap Engine**  
   Finds hidden company concentration across ETFs.

3. **Dynamic AI Importance Ranking**  
   Scores companies by strategic importance to the AI value chain.

4. **Company Gap Engine**  
   Compares your actual exposure to critical AI companies.

5. **Company-Level Buy Signals**  
   Generates ADD / BUILD / LIMIT style signals.

6. **ETF Optimizer**  
   Converts those gaps into a no-sell next-buy plan.

### Why CRYP is included

CRYP is treated as **Crypto AI Pivot** exposure because some crypto miners may have:
- power access
- data-center sites
- cooling infrastructure
- high-density compute operating experience
- optionality to pivot toward AI/HPC hosting

This is higher-risk optionality, not the same as core AI exposure like NVIDIA, TSMC, ASML or Microsoft.

### Important

The bundled holdings are starter rows and should be replaced with official full holdings where possible.

This is a research and education tool only. It is not personal financial advice.
""")
