
import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI Industry End-to-End System View", page_icon="⚡", layout="wide")

def calculate_company_ai_score(row):
    score = 0
    layer = row.get("Layer", "")
    role = row.get("Role", "")
    bottleneck = row.get("Bottleneck Exposure", "")
    public_status = row.get("Public Status", "")

    layer_weights = {
        "1. Energy & Power Infrastructure": 30,
        "2. Data Centers & Physical Infrastructure": 32,
        "3. Compute Hardware & Semiconductors": 35,
        "4. Data & Input Layer": 24,
        "5. AI Models & Foundation Layer": 28,
        "6. Platforms & AI Deployment Layer": 30,
        "7. Applications & End User Layer": 22,
    }
    score += layer_weights.get(layer, 15)

    role_terms = {
        "Power": 25, "Grid": 20, "Storage": 18, "Data Center": 25, "Cloud": 22,
        "Compute": 30, "GPU": 30, "Accelerator": 30, "Foundry": 28,
        "Networking": 24, "Data": 20, "Warehouse": 20, "Governance": 16,
        "Foundation Model": 28, "Training": 26, "Deployment": 22,
        "Enterprise": 18, "Application": 16,
    }
    for term, points in role_terms.items():
        if term.lower() in role.lower():
            score += points

    if bottleneck == "High":
        score += 25
    elif bottleneck == "Medium":
        score += 12

    if public_status == "Public":
        score += 5
    elif public_status == "Private":
        score -= 5

    return min(max(score, 0), 100)

def investment_signal(score):
    if score >= 85:
        return "🔥 Critical AI Bottleneck"
    elif score >= 70:
        return "📈 High Strategic Exposure"
    elif score >= 50:
        return "⚖️ Meaningful Exposure"
    return "🔎 Watchlist"

def layer_thesis(layer):
    theses = {
        "1. Energy & Power Infrastructure": "AI demand ultimately becomes electricity demand. This layer tracks power providers and grid infrastructure that enable data center growth.",
        "2. Data Centers & Physical Infrastructure": "This layer provides the physical facilities where AI workloads run, including hyperscale cloud infrastructure and colocation assets.",
        "3. Compute Hardware & Semiconductors": "This is the core compute layer: GPUs, accelerators, foundries, CPUs, networking chips, and interconnects.",
        "4. Data & Input Layer": "AI systems depend on data pipelines, storage, warehousing, governance, and enterprise operational data.",
        "5. AI Models & Foundation Layer": "This layer builds and trains the foundation models that create intelligence and AI capability.",
        "6. Platforms & AI Deployment Layer": "This layer turns models into deployable services through cloud platforms, APIs, tools, SDKs, and enterprise integration.",
        "7. Applications & End User Layer": "This layer delivers AI-powered products to users and businesses, where visible customer value is captured.",
    }
    return theses.get(layer, "")

def calculate_etf_ai_score(row):
    score = (
        row["Energy Exposure (%)"] * 0.18 +
        row["Data Center Exposure (%)"] * 0.20 +
        row["Compute Exposure (%)"] * 0.25 +
        row["Data/Model Exposure (%)"] * 0.12 +
        row["Platform/Application Exposure (%)"] * 0.15 +
        row["Diversification Score"] * 0.10
    )
    if row["Core or Satellite"] == "Satellite":
        score += 20
    elif row["Core or Satellite"] == "Core / Satellite":
        score += 10
    return min(round(score, 1), 100)

def etf_gap_analysis(row):
    gaps = []
    if row["Energy Exposure (%)"] < 5: gaps.append("energy/power")
    if row["Data Center Exposure (%)"] < 5: gaps.append("data centers")
    if row["Compute Exposure (%)"] < 10: gaps.append("compute/semiconductors")
    if row["Data/Model Exposure (%)"] < 5: gaps.append("data/model layer")
    if row["Platform/Application Exposure (%)"] < 10: gaps.append("platforms/applications")
    return "Balanced end-to-end AI exposure" if not gaps else "Lower exposure to: " + ", ".join(gaps)

company_rows = [
    ["1. Energy & Power Infrastructure","NextEra Energy","NEE","Public","Power generation, renewables, grid-scale energy","High","Power generation for AI data centers"],
    ["1. Energy & Power Infrastructure","Constellation Energy","CEG","Public","Power generation, nuclear power","High","Firm clean power for hyperscale data centers"],
    ["1. Energy & Power Infrastructure","Duke Energy","DUK","Public","Power generation and grid transmission","Medium","Electric utility and grid support"],
    ["1. Energy & Power Infrastructure","Southern Company","SO","Public","Power generation, utility infrastructure","Medium","Power supply and regulated utility infrastructure"],
    ["1. Energy & Power Infrastructure","Vistra Corp","VST","Public","Power generation and energy storage","High","Dispatchable power and energy supply"],

    ["2. Data Centers & Physical Infrastructure","Equinix","EQIX","Public","Data Center colocation and interconnection","High","Colocation and data center REIT exposure"],
    ["2. Data Centers & Physical Infrastructure","Digital Realty","DLR","Public","Data Center REIT and hyperscale facilities","High","Large-scale data center capacity"],
    ["2. Data Centers & Physical Infrastructure","Amazon Web Services","AMZN","Public","Cloud infrastructure and hyperscale data centers","High","Hyperscale cloud infrastructure"],
    ["2. Data Centers & Physical Infrastructure","Microsoft Azure","MSFT","Public","Cloud infrastructure and AI data centers","High","AI cloud capacity and data center buildout"],
    ["2. Data Centers & Physical Infrastructure","Google Cloud","GOOGL","Public","Cloud infrastructure and AI data centers","High","Hyperscale AI infrastructure"],

    ["3. Compute Hardware & Semiconductors","NVIDIA","NVDA","Public","GPU accelerators and AI compute","High","GPUs and AI accelerators"],
    ["3. Compute Hardware & Semiconductors","AMD","AMD","Public","GPU accelerators, CPUs and AI compute","Medium","AI accelerators and processors"],
    ["3. Compute Hardware & Semiconductors","Intel","INTC","Public","CPUs, accelerators and foundry ambitions","Medium","Processors and foundry capacity"],
    ["3. Compute Hardware & Semiconductors","TSMC","TSM","Public","Foundry manufacturing for advanced AI chips","High","Chip manufacturing foundry"],
    ["3. Compute Hardware & Semiconductors","Broadcom","AVGO","Public","Networking chips, ASICs and interconnects","High","Networking chips and custom silicon"],

    ["4. Data & Input Layer","Snowflake","SNOW","Public","Data warehouse and data platform","Medium","Data storage and warehousing"],
    ["4. Data & Input Layer","Databricks","Private","Private","Data engineering, lakehouse and AI data platform","Medium","Data engineering and pipelines"],
    ["4. Data & Input Layer","Palantir Technologies","PLTR","Public","Enterprise data platforms and operational AI","Medium","Enterprise operational data platforms"],
    ["4. Data & Input Layer","Alphabet","GOOGL","Public","Data, search, cloud and AI infrastructure","High","Data scale and AI training data"],
    ["4. Data & Input Layer","Meta Platforms","META","Public","Social data, AI research and model training","Medium","Large-scale data and AI model training"],

    ["5. AI Models & Foundation Layer","OpenAI","Private","Private","Foundation Model development and inference","High","Foundation model development"],
    ["5. AI Models & Foundation Layer","Anthropic","Private","Private","Foundation Model development and safety","High","Foundation model training and safety"],
    ["5. AI Models & Foundation Layer","Google DeepMind","GOOGL","Public","Foundation Model research and training","High","AI research and foundation models"],
    ["5. AI Models & Foundation Layer","Meta Platforms","META","Public","Open-source foundation models and AI research","Medium","Model training and open-source model ecosystem"],
    ["5. AI Models & Foundation Layer","xAI","Private","Private","Foundation Model development and AI products","Medium","Foundation model development"],

    ["6. Platforms & AI Deployment Layer","Microsoft","MSFT","Public","Cloud, AI deployment, APIs and enterprise integration","High","Cloud AI services and APIs"],
    ["6. Platforms & AI Deployment Layer","Amazon Web Services","AMZN","Public","Cloud AI services and model deployment","High","Cloud AI deployment infrastructure"],
    ["6. Platforms & AI Deployment Layer","Alphabet / Google Cloud","GOOGL","Public","Cloud, AI tools and model deployment","High","Cloud AI services and model management"],
    ["6. Platforms & AI Deployment Layer","IBM","IBM","Public","Enterprise AI integration and hybrid cloud","Medium","Enterprise integration and security"],
    ["6. Platforms & AI Deployment Layer","Oracle","ORCL","Public","Cloud infrastructure and enterprise AI deployment","Medium","Cloud infrastructure and enterprise AI services"],

    ["7. Applications & End User Layer","Microsoft Copilot","MSFT","Public","Application AI, productivity and automation","Medium","Productivity and automation"],
    ["7. Applications & End User Layer","Adobe","ADBE","Public","Creative AI and content generation","Medium","Creative and content generation"],
    ["7. Applications & End User Layer","Salesforce","CRM","Public","CRM AI and customer experience automation","Medium","Customer experience and CRM"],
    ["7. Applications & End User Layer","Tesla","TSLA","Public","Autonomy, robotics and applied AI","Medium","AI-powered industry solution"],
    ["7. Applications & End User Layer","ServiceNow","NOW","Public","Enterprise workflow automation and AI agents","Medium","Enterprise workflow automation"],
]
companies = pd.DataFrame(company_rows, columns=["Layer","Company","Ticker","Public Status","Role","Bottleneck Exposure","Example Role"])
companies["AI Exposure Score"] = companies.apply(calculate_company_ai_score, axis=1)
companies["Signal"] = companies["AI Exposure Score"].apply(investment_signal)

etfs = pd.DataFrame([
    {"ETF Name":"Global X Artificial Intelligence Infrastructure ETF","Ticker":"AINF","Core or Satellite":"Satellite","Energy Exposure (%)":20,"Data Center Exposure (%)":20,"Compute Exposure (%)":25,"Data/Model Exposure (%)":5,"Platform/Application Exposure (%)":5,"Diversification Score":60,"Suggested Role":"Primary AI infrastructure satellite","Strengths":"Best fit for physical AI infrastructure, energy and data center bottlenecks","Weaknesses":"Less exposure to downstream software and application winners"},
    {"ETF Name":"Global X Semiconductor ETF","Ticker":"SEMI","Core or Satellite":"Satellite","Energy Exposure (%)":0,"Data Center Exposure (%)":0,"Compute Exposure (%)":70,"Data/Model Exposure (%)":0,"Platform/Application Exposure (%)":3,"Diversification Score":35,"Suggested Role":"Semiconductor satellite","Strengths":"Strong compute and chip supply-chain exposure","Weaknesses":"Minimal power, data center, platform and application exposure"},
    {"ETF Name":"BetaShares Nasdaq 100 ETF","Ticker":"NDQ","Core or Satellite":"Core / Satellite","Energy Exposure (%)":1,"Data Center Exposure (%)":2,"Compute Exposure (%)":22,"Data/Model Exposure (%)":15,"Platform/Application Exposure (%)":35,"Diversification Score":55,"Suggested Role":"Mega-cap AI platform and application exposure","Strengths":"Strong exposure to Microsoft, NVIDIA, Alphabet, Amazon, Meta and Broadcom","Weaknesses":"Low energy and physical infrastructure exposure"},
    {"ETF Name":"iShares S&P 500 ETF","Ticker":"IVV","Core or Satellite":"Core","Energy Exposure (%)":4,"Data Center Exposure (%)":3,"Compute Exposure (%)":12,"Data/Model Exposure (%)":12,"Platform/Application Exposure (%)":25,"Diversification Score":85,"Suggested Role":"Broad US core exposure","Strengths":"Captures many large AI winners while remaining diversified","Weaknesses":"Less targeted than thematic ETFs"},
    {"ETF Name":"Vanguard FTSE All-World ex-US ETF","Ticker":"VEU","Core or Satellite":"Core","Energy Exposure (%)":5,"Data Center Exposure (%)":1,"Compute Exposure (%)":8,"Data/Model Exposure (%)":2,"Platform/Application Exposure (%)":5,"Diversification Score":90,"Suggested Role":"Global diversification outside the US","Strengths":"Diversifies away from US concentration and includes some global AI suppliers","Weaknesses":"Low direct AI exposure"},
])
etfs["AI Exposure Score"] = etfs.apply(calculate_etf_ai_score, axis=1)
etfs["Gap Analysis"] = etfs.apply(etf_gap_analysis, axis=1)

capex = pd.DataFrame([
    {"Event":"Hyperscaler AI data center buildout","Company":"Microsoft","AI Layer Impact":"Data Centers, Compute, Energy, Platforms","Capex Amount ($B)":50,"Signal Strength":"Strong","Likely Beneficiaries":"NVIDIA, TSMC, Vertiv, Constellation Energy, Arista Networks"},
    {"Event":"Cloud AI infrastructure expansion","Company":"Amazon","AI Layer Impact":"Data Centers, Compute, Platforms","Capex Amount ($B)":60,"Signal Strength":"Strong","Likely Beneficiaries":"NVIDIA, Broadcom, TSMC, Vertiv, Digital Realty"},
    {"Event":"AI training and inference expansion","Company":"Alphabet","AI Layer Impact":"Compute, Models, Data Centers, Platforms","Capex Amount ($B)":45,"Signal Strength":"Strong","Likely Beneficiaries":"Broadcom, NVIDIA, TSMC, Arista Networks, NextEra Energy"},
    {"Event":"Advanced foundry capacity investment","Company":"TSMC","AI Layer Impact":"Compute Hardware & Semiconductors","Capex Amount ($B)":35,"Signal Strength":"Moderate","Likely Beneficiaries":"ASML, Applied Materials, NVIDIA, AMD"},
    {"Event":"Firm clean power demand from data centers","Company":"Constellation Energy","AI Layer Impact":"Energy & Power Infrastructure","Capex Amount ($B)":5,"Signal Strength":"Moderate","Likely Beneficiaries":"Constellation Energy, data center operators"},
])

st.title("⚡ The AI Industry: End-to-End System View")
st.caption("From energy to end users — top 5 companies across each AI value-chain layer.")

tabs = st.tabs(["System Overview","Layer Explorer","Company Tracker","ETF Exposure Analyzer","AI Capex Monitor","Methodology"])

with tabs[0]:
    st.subheader("Executive View")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("AI Layers", companies["Layer"].nunique())
    c2.metric("Companies Tracked", len(companies))
    c3.metric("ETFs Tracked", len(etfs))
    c4.metric("Avg AI Score", round(companies["AI Exposure Score"].mean(), 1))

    st.subheader("🧠 AI Flywheel")
    st.markdown("**More applications & users → more data generated → better models → more compute demand → more energy demand.**")
    st.write("This dashboard maps the top 5 companies positioned across each part of that flywheel.")

    st.subheader("🏗️ Top 5 Companies by Layer")
    for layer in companies["Layer"].unique():
        layer_df = companies[companies["Layer"] == layer].sort_values("AI Exposure Score", ascending=False)
        with st.expander(layer, expanded=True):
            st.caption(layer_thesis(layer))
            st.dataframe(layer_df[["Company","Ticker","Public Status","Role","Bottleneck Exposure","AI Exposure Score","Signal"]], use_container_width=True, hide_index=True)

    st.subheader("🔥 Highest Scoring Companies Across the Full AI Stack")
    st.dataframe(companies.sort_values("AI Exposure Score", ascending=False).head(15), use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("Layer Explorer")
    selected_layer = st.selectbox("Choose an AI value-chain layer", companies["Layer"].unique())
    layer_df = companies[companies["Layer"] == selected_layer].sort_values("AI Exposure Score", ascending=False)
    st.markdown(f"### {selected_layer}")
    st.write(layer_thesis(selected_layer))
    st.dataframe(layer_df[["Company","Ticker","Public Status","Role","Example Role","Bottleneck Exposure","AI Exposure Score","Signal"]], use_container_width=True, hide_index=True)
    st.subheader("Layer AI Exposure Scores")
    st.bar_chart(layer_df.set_index("Company")["AI Exposure Score"])

with tabs[2]:
    st.subheader("Company Tracker")
    selected_layers = st.multiselect("Filter by layer", companies["Layer"].unique(), default=list(companies["Layer"].unique()))
    selected_status = st.multiselect("Filter by public/private status", companies["Public Status"].unique(), default=list(companies["Public Status"].unique()))
    min_score = st.slider("Minimum AI Exposure Score", 0, 100, 0)
    filtered = companies[(companies["Layer"].isin(selected_layers)) & (companies["Public Status"].isin(selected_status)) & (companies["AI Exposure Score"] >= min_score)].sort_values("AI Exposure Score", ascending=False)
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.subheader("Scores by Company")
    st.bar_chart(filtered.set_index("Company")["AI Exposure Score"])

with tabs[3]:
    st.subheader("ETF Exposure Analyzer")
    selected = st.selectbox("Select ETF", etfs["Ticker"].tolist())
    row = etfs[etfs["Ticker"] == selected].iloc[0]
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("AI Exposure Score", row["AI Exposure Score"])
    c2.metric("Energy Exposure", f'{row["Energy Exposure (%)"]}%')
    c3.metric("Compute Exposure", f'{row["Compute Exposure (%)"]}%')
    c4.metric("Platform/App Exposure", f'{row["Platform/Application Exposure (%)"]}%')
    st.markdown(f"### {row['ETF Name']} ({row['Ticker']})")
    st.write(f"**Suggested Role:** {row['Suggested Role']}")
    st.write(f"**Strengths:** {row['Strengths']}")
    st.write(f"**Weaknesses:** {row['Weaknesses']}")
    st.write(f"**Gap Analysis:** {row['Gap Analysis']}")
    st.subheader("ETF Comparison")
    st.dataframe(etfs.sort_values("AI Exposure Score", ascending=False), use_container_width=True, hide_index=True)
    st.subheader("ETF End-to-End AI Exposure Comparison")
    chart_df = etfs.set_index("Ticker")[["Energy Exposure (%)","Data Center Exposure (%)","Compute Exposure (%)","Data/Model Exposure (%)","Platform/Application Exposure (%)"]]
    st.bar_chart(chart_df)

with tabs[4]:
    st.subheader("AI Capex Monitor")
    st.dataframe(capex, use_container_width=True, hide_index=True)
    st.subheader("Capex by Company")
    st.bar_chart(capex.set_index("Company")["Capex Amount ($B)"])

with tabs[5]:
    st.subheader("Methodology")
    st.markdown("""
This app maps the AI industry into seven layers:

1. Energy & Power Infrastructure  
2. Data Centers & Physical Infrastructure  
3. Compute Hardware & Semiconductors  
4. Data & Input Layer  
5. AI Models & Foundation Layer  
6. Platforms & AI Deployment Layer  
7. Applications & End User Layer  

### Company AI Exposure Score
Scores are based on:
- Which AI layer the company sits in
- Its role in the AI value chain
- Whether it sits near a bottleneck
- Whether it is publicly investable

### ETF AI Exposure Score
Scores are based on:
- Energy exposure
- Data center exposure
- Compute/semiconductor exposure
- Data/model exposure
- Platform/application exposure
- Diversification score

This is a research and education tool only. It is not personal financial advice.
""")
