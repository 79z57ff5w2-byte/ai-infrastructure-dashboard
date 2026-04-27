
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="AI Infrastructure Intelligence Dashboard",
    page_icon="⚡",
    layout="wide"
)

DATA_DIR = Path(__file__).parent / "data"

@st.cache_data
def load_data():
    companies = pd.read_csv(DATA_DIR / "companies.csv")
    etfs = pd.read_csv(DATA_DIR / "etfs.csv")
    capex = pd.read_csv(DATA_DIR / "capex_events.csv")
    return companies, etfs, capex

def score_badge(score):
    if score >= 75:
        return "High"
    if score >= 50:
        return "Medium"
    return "Low"

companies, etfs, capex = load_data()

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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Companies Tracked", len(companies))
    c2.metric("ETFs Tracked", len(etfs))
    c3.metric("Capex Events", len(capex))
    c4.metric("Avg Company AI Score", round(companies["AI Exposure Score"].mean(), 1))

    st.divider()

    st.subheader("🔥 Highest AI Exposure Companies")
    st.dataframe(
        companies.sort_values("AI Exposure Score", ascending=False).head(10)[
            ["Company", "Ticker", "Sector", "AI Value Chain Role", "AI Exposure Score", "Investment Signal"]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.subheader("⚡ Latest Strong Capex Signals")
    st.dataframe(
        capex.sort_values("Date", ascending=False)[
            ["Date", "Event Name", "Company", "Event Type", "Capex Amount ($B)", "AI Relevance", "Signal Strength", "Investment Interpretation"]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.subheader("📊 ETF AI Exposure Snapshot")
    st.dataframe(
        etfs.sort_values("AI Exposure Score", ascending=False)[
            ["ETF Name", "Ticker", "Core or Satellite", "AI Exposure Score", "Semiconductor Exposure (%)", "Data Center Exposure (%)", "Energy Exposure (%)", "Suggested Role"]
        ],
        use_container_width=True,
        hide_index=True
    )

with tabs[1]:
    st.subheader("Infrastructure Tracker")

    col1, col2, col3 = st.columns(3)
    with col1:
        sector_filter = st.multiselect("Sector", sorted(companies["Sector"].unique()), default=sorted(companies["Sector"].unique()))
    with col2:
        role_filter = st.multiselect("AI Value Chain Role", sorted(companies["AI Value Chain Role"].unique()), default=sorted(companies["AI Value Chain Role"].unique()))
    with col3:
        min_score = st.slider("Minimum AI Exposure Score", 0, 100, 0)

    filtered = companies[
        (companies["Sector"].isin(sector_filter)) &
        (companies["AI Value Chain Role"].isin(role_filter)) &
        (companies["AI Exposure Score"] >= min_score)
    ]

    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.subheader("AI Exposure by Company")
    st.bar_chart(filtered.sort_values("AI Exposure Score", ascending=False).set_index("Company")["AI Exposure Score"])

with tabs[2]:
    st.subheader("ETF Exposure Analyzer")

    selected_etf = st.selectbox("Select ETF", etfs["Ticker"].tolist())
    row = etfs[etfs["Ticker"] == selected_etf].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AI Exposure Score", int(row["AI Exposure Score"]), score_badge(row["AI Exposure Score"]))
    c2.metric("Semiconductor Exposure", f'{row["Semiconductor Exposure (%)"]}%')
    c3.metric("Data Center Exposure", f'{row["Data Center Exposure (%)"]}%')
    c4.metric("Energy Exposure", f'{row["Energy Exposure (%)"]}%')

    st.markdown(f"### {row['ETF Name']} ({row['Ticker']})")
    st.write(f"**Role:** {row['Suggested Role']}")
    st.write(f"**Strengths:** {row['Strengths']}")
    st.write(f"**Weaknesses:** {row['Weaknesses']}")
    st.write(f"**Top Holdings:** {row['Top Holdings']}")

    st.subheader("Compare ETFs")
    st.dataframe(etfs, use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("AI Capex Monitor")

    col1, col2 = st.columns(2)
    with col1:
        relevance_filter = st.multiselect("AI Relevance", sorted(capex["AI Relevance"].unique()), default=sorted(capex["AI Relevance"].unique()))
    with col2:
        signal_filter = st.multiselect("Signal Strength", sorted(capex["Signal Strength"].unique()), default=sorted(capex["Signal Strength"].unique()))

    filtered_capex = capex[
        (capex["AI Relevance"].isin(relevance_filter)) &
        (capex["Signal Strength"].isin(signal_filter))
    ].sort_values("Date", ascending=False)

    st.dataframe(filtered_capex, use_container_width=True, hide_index=True)
    st.subheader("Capex by Company")
    st.bar_chart(filtered_capex.groupby("Company")["Capex Amount ($B)"].sum().sort_values(ascending=False))

with tabs[4]:
    st.subheader("Methodology")
    st.markdown("""
This MVP uses a rules-based scoring framework.

**AI Exposure Score** estimates how directly a company or ETF participates in the AI infrastructure value chain.

**Company score inputs:**
- Direct AI demand exposure
- Position in the physical AI stack
- Revenue growth
- Capex sensitivity
- Contract/customer relevance

**ETF score inputs:**
- Semiconductor exposure
- Data center exposure
- Energy/power exposure
- Networking exposure
- Concentration in key AI infrastructure companies

**Capex signal strength** reflects whether a development may change future demand for chips, energy, data centers, networking, or cooling.
""")
    st.warning("This app is for research and education only. It is not personal financial advice.")
