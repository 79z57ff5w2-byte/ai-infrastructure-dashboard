
import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="AI Infrastructure Intelligence Dashboard", page_icon="⚡", layout="wide")

COMPANIES_CSV = """Company,Ticker,Sector,Sub-Sector,Region,AI Value Chain Role,AI Exposure Score,Revenue Growth YoY (%),Capex Intensity (%),Key Customers,Investment Signal,Notes
NVIDIA,NVDA,Semiconductors,GPUs/AI Accelerators,US,Compute,98,200,5,Hyperscalers; AI labs,Bullish,Core compute bottleneck company
AMD,AMD,Semiconductors,GPUs/CPUs,US,Compute,82,15,5,Hyperscalers; enterprises,Bullish,Second-source AI compute exposure
ASML,ASML,Semiconductors,Lithography Equipment,Europe,Equipment,90,20,10,TSMC; Samsung; Intel,Bullish,Critical semiconductor equipment position
Applied Materials,AMAT,Semiconductors,Semiconductor Equipment,US,Equipment,78,8,8,Foundries; memory makers,Neutral,Broad chip equipment exposure
TSMC,TSM,Semiconductors,Foundry,Asia,Fabrication,94,30,35,NVIDIA; Apple; AMD,Bullish,Backbone of advanced AI chip production
Broadcom,AVGO,Semiconductors,Networking/ASICs,US,Networking,86,40,6,Hyperscalers,Bullish,Important for AI networking and custom chips
Equinix,EQIX,Data Centers,Colocation,US,Data Center,76,12,35,Cloud providers; enterprises,Neutral,AI demand beneficiary but power availability matters
Digital Realty,DLR,Data Centers,Data Center REIT,US,Data Center,74,10,40,Hyperscalers; enterprises,Neutral,Large AI data center demand beneficiary
Constellation Energy,CEG,Energy,Nuclear Power,US,Power,80,5,45,Utilities; hyperscalers,Bullish,Potential winner from firm clean power demand
NextEra Energy,NEE,Energy,Renewables/Utility,US,Power,70,6,50,Utilities; corporates,Neutral,Large clean energy exposure
Vertiv,VRT,Cooling,Power/Cooling Infrastructure,US,Cooling,88,20,10,Data centers; hyperscalers,Bullish,Direct AI data center thermal management exposure
Arista Networks,ANET,Networking,Cloud Networking,US,Networking,84,25,7,Hyperscalers; cloud providers,Bullish,AI clusters need high-speed networking
"""

ETFS_CSV = """ETF Name,Ticker,Region,Core or Satellite,Top Holdings,Semiconductor Exposure (%),Data Center Exposure (%),Energy Exposure (%),Networking Exposure (%),AI Exposure Score,Overlap Score,Strengths,Weaknesses,Suggested Role
iShares S&P 500 ETF,IVV,US,Core,"Microsoft; NVIDIA; Apple; Amazon; Alphabet",12,3,4,3,62,70,Broad US exposure with major AI leaders,Not targeted; limited direct energy/data center tilt,Core market exposure
BetaShares Nasdaq 100 ETF,NDQ,US,Core,"NVIDIA; Microsoft; Apple; Amazon; Broadcom; Alphabet",22,2,1,5,78,82,Strong mega-cap AI and semiconductor exposure,High concentration; weak energy exposure,High-growth tech core/satellite hybrid
Global X Artificial Intelligence Infrastructure ETF,AINF,Global,Satellite,"AI infrastructure companies across data centers; energy; semis",25,20,20,10,88,45,Direct AI infrastructure and energy bottleneck exposure,Newer fund; thematic concentration,Primary AI infrastructure satellite
Global X Semiconductor ETF,SEMI,Global,Satellite,"NVIDIA; TSMC; ASML; Broadcom; AMD",70,0,0,8,86,55,High direct chip supply chain exposure,Cyclical; little energy/data center exposure,Semiconductor satellite
Vanguard FTSE All-World ex-US ETF,VEU,Global,Core,"Nestle; ASML; TSMC; global ex-US equities",8,1,5,1,38,20,Diversifies outside US and includes some global AI suppliers,Low targeted AI exposure,Global diversification core
"""

CAPEX_CSV = """Event Name,Company,Event Type,Capex Amount ($B),YoY Change (%),AI Relevance,Beneficiaries,Market Reaction,Signal Strength,Investment Interpretation,Date
Hyperscaler AI data center buildout,Microsoft,Capex Announcement,50,35,High,"NVIDIA; TSMC; Vertiv; Constellation Energy; Arista Networks",Positive,Strong,Large AI capex supports compute networking power and cooling demand,2026-04-27
Cloud AI infrastructure expansion,Amazon,Capex Announcement,60,30,High,"NVIDIA; Broadcom; TSMC; Vertiv; Digital Realty",Positive,Strong,Continued cloud AI spending supports full infrastructure stack,2026-04-27
AI training and inference capacity expansion,Alphabet,Capex Announcement,45,25,High,"Broadcom; NVIDIA; TSMC; Arista Networks; NextEra Energy",Neutral,Strong,AI model development and inference scale reinforces chip and power demand,2026-04-27
Advanced foundry capacity investment,TSMC,Data Center Expansion,35,20,High,"ASML; Applied Materials; NVIDIA; AMD",Positive,Moderate,Advanced node capacity supports AI accelerator supply growth,2026-04-27
Nuclear power demand from data centers,Constellation Energy,Power Agreement,5,15,High,"Constellation Energy; data center operators",Positive,Moderate,Firm clean power becomes strategic bottleneck for AI data centers,2026-04-27
"""

@st.cache_data
def load_data():
    return (
        pd.read_csv(StringIO(COMPANIES_CSV)),
        pd.read_csv(StringIO(ETFS_CSV)),
        pd.read_csv(StringIO(CAPEX_CSV))
    )

companies, etfs, capex = load_data()

st.title("⚡ AI Infrastructure Intelligence Dashboard")
st.caption("Track the AI infrastructure value chain, ETF exposure, and capex signals.")

tabs = st.tabs(["Executive View", "Infrastructure Tracker", "ETF Exposure Analyzer", "AI Capex Monitor", "Methodology"])

with tabs[0]:
    st.subheader("Executive View")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Companies Tracked", len(companies))
    c2.metric("ETFs Tracked", len(etfs))
    c3.metric("Capex Events", len(capex))
    c4.metric("Avg Company AI Score", round(companies["AI Exposure Score"].mean(), 1))
    st.subheader("🔥 Highest AI Exposure Companies")
    st.dataframe(companies.sort_values("AI Exposure Score", ascending=False), use_container_width=True, hide_index=True)
    st.subheader("📊 ETF AI Exposure Snapshot")
    st.dataframe(etfs.sort_values("AI Exposure Score", ascending=False), use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("Infrastructure Tracker")
    sector_filter = st.multiselect("Sector", sorted(companies["Sector"].unique()), default=sorted(companies["Sector"].unique()))
    min_score = st.slider("Minimum AI Exposure Score", 0, 100, 0)
    filtered = companies[(companies["Sector"].isin(sector_filter)) & (companies["AI Exposure Score"] >= min_score)]
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.bar_chart(filtered.sort_values("AI Exposure Score", ascending=False).set_index("Company")["AI Exposure Score"])

with tabs[2]:
    st.subheader("ETF Exposure Analyzer")
    selected_etf = st.selectbox("Select ETF", etfs["Ticker"].tolist())
    row = etfs[etfs["Ticker"] == selected_etf].iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AI Exposure Score", int(row["AI Exposure Score"]))
    c2.metric("Semiconductor Exposure", f'{row["Semiconductor Exposure (%)"]}%')
    c3.metric("Data Center Exposure", f'{row["Data Center Exposure (%)"]}%')
    c4.metric("Energy Exposure", f'{row["Energy Exposure (%)"]}%')
    st.markdown(f"### {row['ETF Name']} ({row['Ticker']})")
    st.write(f"**Role:** {row['Suggested Role']}")
    st.write(f"**Strengths:** {row['Strengths']}")
    st.write(f"**Weaknesses:** {row['Weaknesses']}")
    st.write(f"**Top Holdings:** {row['Top Holdings']}")
    st.dataframe(etfs, use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("AI Capex Monitor")
    st.dataframe(capex.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)
    st.bar_chart(capex.groupby("Company")["Capex Amount ($B)"].sum().sort_values(ascending=False))

with tabs[4]:
    st.subheader("Methodology")
    st.markdown("""
This MVP uses a rules-based scoring framework.

**AI Exposure Score** estimates how directly a company or ETF participates in the AI infrastructure value chain.

**Signal strength** reflects whether a development may change future demand for chips, energy, data centers, networking, or cooling.
""")
    st.warning("This app is for research and education only. It is not personal financial advice.")
