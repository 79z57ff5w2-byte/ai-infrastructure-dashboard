
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="AI Infrastructure Intelligence Dashboard",
    page_icon="⚡",
    layout="wide"
)

companies = pd.DataFrame([
    {"Company": "NVIDIA", "Ticker": "NVDA", "Sector": "Semiconductors", "Role": "Compute", "AI Exposure Score": 98, "Investment Signal": "Bullish", "Notes": "Core AI compute bottleneck company"},
    {"Company": "TSMC", "Ticker": "TSM", "Sector": "Semiconductors", "Role": "Fabrication", "AI Exposure Score": 94, "Investment Signal": "Bullish", "Notes": "Backbone of advanced AI chip production"},
    {"Company": "ASML", "Ticker": "ASML", "Sector": "Semiconductors", "Role": "Equipment", "AI Exposure Score": 90, "Investment Signal": "Bullish", "Notes": "Critical lithography equipment provider"},
    {"Company": "Vertiv", "Ticker": "VRT", "Sector": "Cooling", "Role": "Cooling / Power", "AI Exposure Score": 88, "Investment Signal": "Bullish", "Notes": "Direct AI data center cooling and power exposure"},
    {"Company": "Broadcom", "Ticker": "AVGO", "Sector": "Semiconductors", "Role": "Networking / ASICs", "AI Exposure Score": 86, "Investment Signal": "Bullish", "Notes": "Important for AI networking and custom chips"},
    {"Company": "Arista Networks", "Ticker": "ANET", "Sector": "Networking", "Role": "Data Center Networking", "AI Exposure Score": 84, "Investment Signal": "Bullish", "Notes": "AI clusters need high-speed networking"},
    {"Company": "AMD", "Ticker": "AMD", "Sector": "Semiconductors", "Role": "Compute", "AI Exposure Score": 82, "Investment Signal": "Bullish", "Notes": "Second-source AI accelerator exposure"},
    {"Company": "Constellation Energy", "Ticker": "CEG", "Sector": "Energy", "Role": "Power", "AI Exposure Score": 80, "Investment Signal": "Bullish", "Notes": "Potential winner from firm clean power demand"},
    {"Company": "Applied Materials", "Ticker": "AMAT", "Sector": "Semiconductors", "Role": "Equipment", "AI Exposure Score": 78, "Investment Signal": "Neutral", "Notes": "Broad semiconductor equipment exposure"},
    {"Company": "Equinix", "Ticker": "EQIX", "Sector": "Data Centers", "Role": "Data Center", "AI Exposure Score": 76, "Investment Signal": "Neutral", "Notes": "AI data center demand beneficiary"},
    {"Company": "Digital Realty", "Ticker": "DLR", "Sector": "Data Centers", "Role": "Data Center REIT", "AI Exposure Score": 74, "Investment Signal": "Neutral", "Notes": "Large AI data center demand beneficiary"},
    {"Company": "NextEra Energy", "Ticker": "NEE", "Sector": "Energy", "Role": "Power", "AI Exposure Score": 70, "Investment Signal": "Neutral", "Notes": "Large clean energy exposure"},
])

etfs = pd.DataFrame([
    {"ETF Name": "Global X Artificial Intelligence Infrastructure ETF", "Ticker": "AINF", "Core or Satellite": "Satellite", "AI Exposure Score": 88, "Semiconductor Exposure (%)": 25, "Data Center Exposure (%)": 20, "Energy Exposure (%)": 20, "Strengths": "Direct AI infrastructure and energy bottleneck exposure", "Weaknesses": "Thematic concentration", "Suggested Role": "Primary AI infrastructure satellite"},
    {"ETF Name": "Global X Semiconductor ETF", "Ticker": "SEMI", "Core or Satellite": "Satellite", "AI Exposure Score": 86, "Semiconductor Exposure (%)": 70, "Data Center Exposure (%)": 0, "Energy Exposure (%)": 0, "Strengths": "High direct chip supply chain exposure", "Weaknesses": "Little energy/data center exposure", "Suggested Role": "Semiconductor satellite"},
    {"ETF Name": "BetaShares Nasdaq 100 ETF", "Ticker": "NDQ", "Core or Satellite": "Core / Satellite", "AI Exposure Score": 78, "Semiconductor Exposure (%)": 22, "Data Center Exposure (%)": 2, "Energy Exposure (%)": 1, "Strengths": "Strong mega-cap AI exposure", "Weaknesses": "Weak energy exposure", "Suggested Role": "High-growth tech exposure"},
    {"ETF Name": "iShares S&P 500 ETF", "Ticker": "IVV", "Core or Satellite": "Core", "AI Exposure Score": 62, "Semiconductor Exposure (%)": 12, "Data Center Exposure (%)": 3, "Energy Exposure (%)": 4, "Strengths": "Broad US exposure with major AI leaders", "Weaknesses": "Not targeted", "Suggested Role": "Core market exposure"},
    {"ETF Name": "Vanguard FTSE All-World ex-US ETF", "Ticker": "VEU", "Core or Satellite": "Core", "AI Exposure Score": 38, "Semiconductor Exposure (%)": 8, "Data Center Exposure (%)": 1, "Energy Exposure (%)": 5, "Strengths": "Global diversification outside the US", "Weaknesses": "Low targeted AI exposure", "Suggested Role": "Global diversification core"},
])

capex = pd.DataFrame([
    {"Event": "Hyperscaler AI data center buildout", "Company": "Microsoft", "Capex Amount ($B)": 50, "AI Relevance": "High", "Signal Strength": "Strong", "Likely Beneficiaries": "NVIDIA, TSMC, Vertiv, Constellation Energy, Arista Networks"},
    {"Event": "Cloud AI infrastructure expansion", "Company": "Amazon", "Capex Amount ($B)": 60, "AI Relevance": "High", "Signal Strength": "Strong", "Likely Beneficiaries": "NVIDIA, Broadcom, TSMC, Vertiv, Digital Realty"},
    {"Event": "AI training and inference capacity expansion", "Company": "Alphabet", "Capex Amount ($B)": 45, "AI Relevance": "High", "Signal Strength": "Strong", "Likely Beneficiaries": "Broadcom, NVIDIA, TSMC, Arista Networks, NextEra Energy"},
    {"Event": "Advanced foundry capacity investment", "Company": "TSMC", "Capex Amount ($B)": 35, "AI Relevance": "High", "Signal Strength": "Moderate", "Likely Beneficiaries": "ASML, Applied Materials, NVIDIA, AMD"},
    {"Event": "Nuclear power demand from data centers", "Company": "Constellation Energy", "Capex Amount ($B)": 5, "AI Relevance": "High", "Signal Strength": "Moderate", "Likely Beneficiaries": "Constellation Energy, data center operators"},
])

st.title("⚡ AI Infrastructure Intelligence Dashboard")
st.caption("Track the AI infrastructure value chain, ETF exposure, and capex signals.")

tabs = st.tabs([
    "Executive View",
    "Infrastructure Tracker",
    "ETF Exposure Analyzer",
    "AI Capex Monitor",
    "Methodology"
])

with tabs[0]:
    st.subheader("Executive View")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Companies Tracked", len(companies))
    col2.metric("ETFs Tracked", len(etfs))
    col3.metric("Capex Events", len(capex))
    col4.metric("Avg AI Score", round(companies["AI Exposure Score"].mean(), 1))

    st.subheader("🔥 Highest AI Exposure Companies")
    st.dataframe(
        companies.sort_values("AI Exposure Score", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    st.subheader("📊 ETF AI Exposure Snapshot")
    st.dataframe(
        etfs.sort_values("AI Exposure Score", ascending=False),
        use_container_width=True,
        hide_index=True
    )

with tabs[1]:
    st.subheader("Infrastructure Tracker")

    selected_sectors = st.multiselect(
        "Filter by sector",
        sorted(companies["Sector"].unique()),
        default=sorted(companies["Sector"].unique())
    )

    min_score = st.slider("Minimum AI Exposure Score", 0, 100, 0)

    filtered = companies[
        (companies["Sector"].isin(selected_sectors)) &
        (companies["AI Exposure Score"] >= min_score)
    ]

    st.dataframe(filtered, use_container_width=True, hide_index=True)

    st.subheader("AI Exposure Scores")
    st.bar_chart(
        filtered.sort_values("AI Exposure Score", ascending=False)
        .set_index("Company")["AI Exposure Score"]
    )

with tabs[2]:
    st.subheader("ETF Exposure Analyzer")

    selected = st.selectbox("Select ETF", etfs["Ticker"].tolist())
    row = etfs[etfs["Ticker"] == selected].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AI Exposure Score", int(row["AI Exposure Score"]))
    c2.metric("Semiconductor Exposure", f'{row["Semiconductor Exposure (%)"]}%')
    c3.metric("Data Center Exposure", f'{row["Data Center Exposure (%)"]}%')
    c4.metric("Energy Exposure", f'{row["Energy Exposure (%)"]}%')

    st.markdown(f"### {row['ETF Name']} ({row['Ticker']})")
    st.write(f"**Suggested Role:** {row['Suggested Role']}")
    st.write(f"**Strengths:** {row['Strengths']}")
    st.write(f"**Weaknesses:** {row['Weaknesses']}")

    st.subheader("ETF Comparison")
    st.dataframe(etfs, use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("AI Capex Monitor")
    st.dataframe(capex, use_container_width=True, hide_index=True)

    st.subheader("Capex by Company")
    st.bar_chart(capex.set_index("Company")["Capex Amount ($B)"])

with tabs[4]:
    st.subheader("Methodology")
    st.markdown("""
This MVP uses a simple rules-based scoring framework.

**AI Exposure Score** estimates how directly a company or ETF participates in the AI infrastructure value chain.

**Capex signal strength** reflects whether a development may change future demand for chips, energy, data centers, networking, or cooling.

This app is for research and education only. It is not personal financial advice.
""")
