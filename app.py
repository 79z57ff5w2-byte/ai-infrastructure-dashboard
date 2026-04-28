
import streamlit as st
import pandas as pd
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import random
import datetime as dt
import yfinance as yf

st.set_page_config(page_title="AI Portfolio Engine v8", layout="wide")

# ============================================================
# AI industry layers from user's diagram
# ============================================================

AI_LAYERS = [
    "Energy & Power Infrastructure",
    "Data Centers & Physical Infrastructure",
    "Compute Hardware & Semiconductors",
    "Data & Input Layer",
    "AI Models & Foundation Layer",
    "Platforms & AI Deployment Layer",
    "Applications End User Layer",
    "Crypto AI Pivot",
    "Diversification"
]

# ============================================================
# ETF holdings sample universe
# Includes companies from the diagram + user's ETFs including VHY
# ============================================================

HOLDINGS_DATA = [
    # IVV
    ["IVV","MSFT","Microsoft",7.0],
    ["IVV","NVDA","NVIDIA",6.5],
    ["IVV","AAPL","Apple",6.0],
    ["IVV","AMZN","Amazon",4.0],
    ["IVV","GOOGL","Alphabet",3.5],
    ["IVV","META","Meta Platforms",2.5],
    ["IVV","AVGO","Broadcom",2.0],
    ["IVV","TSLA","Tesla",1.5],
    ["IVV","CRM","Salesforce",0.8],
    ["IVV","ADBE","Adobe",0.7],
    ["IVV","ORCL","Oracle",0.7],
    ["IVV","IBM","IBM",0.4],
    ["IVV","INTC","Intel",0.4],
    ["IVV","AMD","AMD",0.3],

    # NDQ
    ["NDQ","NVDA","NVIDIA",8.5],
    ["NDQ","MSFT","Microsoft",7.8],
    ["NDQ","AAPL","Apple",7.5],
    ["NDQ","AMZN","Amazon",5.5],
    ["NDQ","AVGO","Broadcom",4.8],
    ["NDQ","META","Meta Platforms",4.6],
    ["NDQ","GOOGL","Alphabet",4.5],
    ["NDQ","TSLA","Tesla",3.0],
    ["NDQ","ADBE","Adobe",2.0],
    ["NDQ","AMD","AMD",1.5],
    ["NDQ","INTC","Intel",1.0],
    ["NDQ","CRM","Salesforce",1.0],

    # VEU
    ["VEU","TSM","TSMC",1.4],
    ["VEU","ASML","ASML",1.5],
    ["VEU","SAP","SAP",1.0],
    ["VEU","BABA","Alibaba",0.8],
    ["VEU","TCEHY","Tencent",0.7],
    ["VEU","BHP","BHP Group",0.6],
    ["VEU","SHEL","Shell",0.7],
    ["VEU","TM","Toyota",0.8],

    # VHY
    ["VHY","BHP","BHP Group",10.3],
    ["VHY","CBA","Commonwealth Bank",9.8],
    ["VHY","WDS","Woodside Energy",6.7],
    ["VHY","RIO","Rio Tinto",3.2],
    ["VHY","TLS","Telstra",2.8],
    ["VHY","WOW","Woolworths",2.5],

    # AINF
    ["AINF","NEE","NextEra Energy",3.3],
    ["AINF","CEG","Constellation Energy",3.6],
    ["AINF","DUK","Duke Energy",3.0],
    ["AINF","SO","Southern Company",2.8],
    ["AINF","VST","Vistra Corp",3.0],
    ["AINF","GEV","GE Vernova",5.9],
    ["AINF","CCO","Cameco",5.4],
    ["AINF","VRT","Vertiv",4.8],
    ["AINF","ETN","Eaton",4.5],
    ["AINF","EQIX","Equinix",4.0],
    ["AINF","DLR","Digital Realty",3.8],
    ["AINF","FCX","Freeport-McMoRan",5.0],
    ["AINF","SCCO","Southern Copper",5.4],

    # SEMI
    ["SEMI","NVDA","NVIDIA",12.0],
    ["SEMI","TSM","TSMC",10.0],
    ["SEMI","ASML","ASML",9.0],
    ["SEMI","AVGO","Broadcom",8.0],
    ["SEMI","AMD","AMD",6.0],
    ["SEMI","INTC","Intel",3.0],
    ["SEMI","AMAT","Applied Materials",5.0],
    ["SEMI","LRCX","Lam Research",4.5],
    ["SEMI","QCOM","Qualcomm",3.5],
    ["SEMI","MU","Micron",4.0],

    # CRYP
    ["CRYP","COIN","Coinbase",5.0],
    ["CRYP","IREN","IREN Ltd",9.7],
    ["CRYP","HUT","Hut 8 Corp",5.1],
    ["CRYP","CLSK","CleanSpark",4.5],
    ["CRYP","RIOT","Riot Platforms",4.0],
    ["CRYP","MARA","MARA Holdings",4.0],
    ["CRYP","CIFR","Cipher Mining",3.6],
    ["CRYP","GLXY","Galaxy Digital",3.2],
    ["CRYP","MSTR","Strategy Inc",9.8],
    ["CRYP","BMNR","BitMine Immersion Technologies",10.4],

    # GXAI
    ["GXAI","NVDA","NVIDIA",8.0],
    ["GXAI","MSFT","Microsoft",7.0],
    ["GXAI","GOOGL","Alphabet",6.0],
    ["GXAI","META","Meta Platforms",5.0],
    ["GXAI","PLTR","Palantir",4.5],
    ["GXAI","SNOW","Snowflake",4.0],
    ["GXAI","ADBE","Adobe",3.5],
    ["GXAI","NOW","ServiceNow",3.0],
    ["GXAI","CRM","Salesforce",3.0],
    ["GXAI","AMZN","Amazon",3.0],
]

STATIC_HOLDINGS_DF = pd.DataFrame(HOLDINGS_DATA, columns=["ETF","Ticker","Company","Weight"])

DEFAULT_WEIGHTS = {
    "IVV":22.0,
    "VEU":22.0,
    "NDQ":22.0,
    "VHY":24.0,
    "AINF":4.0,
    "SEMI":4.0,
    "CRYP":2.0,
    "GXAI":0.0,
}

# ============================================================
# Target AI universe from diagram
# ============================================================

TARGET_UNIVERSE = [
    # 1. Energy & Power Infrastructure
    ["NEE","NextEra Energy","Energy & Power Infrastructure",92],
    ["CEG","Constellation Energy","Energy & Power Infrastructure",96],
    ["DUK","Duke Energy","Energy & Power Infrastructure",82],
    ["SO","Southern Company","Energy & Power Infrastructure",80],
    ["VST","Vistra Corp","Energy & Power Infrastructure",86],
    ["GEV","GE Vernova","Energy & Power Infrastructure",84],
    ["CCO","Cameco","Energy & Power Infrastructure",82],

    # 2. Data Centers & Physical Infrastructure
    ["EQIX","Equinix","Data Centers & Physical Infrastructure",90],
    ["DLR","Digital Realty","Data Centers & Physical Infrastructure",88],
    ["AMZN","Amazon Web Services","Data Centers & Physical Infrastructure",86],
    ["MSFT","Microsoft Azure","Data Centers & Physical Infrastructure",86],
    ["GOOGL","Google Cloud","Data Centers & Physical Infrastructure",84],
    ["VRT","Vertiv","Data Centers & Physical Infrastructure",92],
    ["ETN","Eaton","Data Centers & Physical Infrastructure",86],

    # 3. Compute Hardware & Semiconductors
    ["NVDA","NVIDIA","Compute Hardware & Semiconductors",100],
    ["AMD","AMD","Compute Hardware & Semiconductors",84],
    ["INTC","Intel","Compute Hardware & Semiconductors",72],
    ["TSM","TSMC","Compute Hardware & Semiconductors",96],
    ["AVGO","Broadcom","Compute Hardware & Semiconductors",88],
    ["ASML","ASML","Compute Hardware & Semiconductors",94],
    ["AMAT","Applied Materials","Compute Hardware & Semiconductors",78],

    # 4. Data & Input Layer
    ["SNOW","Snowflake","Data & Input Layer",76],
    ["DBX","Databricks","Data & Input Layer",76],
    ["PLTR","Palantir","Data & Input Layer",78],
    ["GOOGL","Alphabet","Data & Input Layer",84],
    ["META","Meta Platforms","Data & Input Layer",82],

    # 5. AI Models & Foundation Layer
    ["OPENAI","OpenAI","AI Models & Foundation Layer",96],
    ["ANTH","Anthropic","AI Models & Foundation Layer",90],
    ["GOOGL","Google DeepMind","AI Models & Foundation Layer",88],
    ["META","Meta Platforms","AI Models & Foundation Layer",84],
    ["XAI","xAI","AI Models & Foundation Layer",72],

    # 6. Platforms & AI Deployment Layer
    ["MSFT","Microsoft","Platforms & AI Deployment Layer",92],
    ["AMZN","Amazon Web Services","Platforms & AI Deployment Layer",88],
    ["GOOGL","Alphabet / Google Cloud","Platforms & AI Deployment Layer",86],
    ["IBM","IBM","Platforms & AI Deployment Layer",70],
    ["ORCL","Oracle","Platforms & AI Deployment Layer",78],

    # 7. Applications End User Layer
    ["MSFT","Microsoft Copilot","Applications End User Layer",88],
    ["ADBE","Adobe","Applications End User Layer",80],
    ["CRM","Salesforce","Applications End User Layer",78],
    ["TSLA","Tesla","Applications End User Layer",76],
    ["NOW","ServiceNow","Applications End User Layer",78],

    # Crypto AI Pivot
    ["IREN","IREN Ltd","Crypto AI Pivot",62],
    ["HUT","Hut 8 Corp","Crypto AI Pivot",58],
    ["CLSK","CleanSpark","Crypto AI Pivot",56],
    ["RIOT","Riot Platforms","Crypto AI Pivot",55],
    ["MARA","MARA Holdings","Crypto AI Pivot",55],
    ["COIN","Coinbase","Crypto AI Pivot",50],
]

target_df = pd.DataFrame(TARGET_UNIVERSE, columns=["Ticker","Company","Layer","Base Importance"])

# Dedup target by ticker/layer/company combo but keep multiple layer uses for hyperscalers
target_df = target_df.drop_duplicates()

# ============================================================
# Presets and signal queries
# ============================================================

LAYER_PRESETS = {
    "Balanced AI Growth": {
        "Energy & Power Infrastructure": 1.00,
        "Data Centers & Physical Infrastructure": 1.00,
        "Compute Hardware & Semiconductors": 1.00,
        "Data & Input Layer": 0.85,
        "AI Models & Foundation Layer": 0.80,
        "Platforms & AI Deployment Layer": 0.85,
        "Applications End User Layer": 0.75,
        "Crypto AI Pivot": 0.45,
        "Diversification": 0.30,
    },
    "AI Infrastructure / Power Bottleneck": {
        "Energy & Power Infrastructure": 1.35,
        "Data Centers & Physical Infrastructure": 1.25,
        "Compute Hardware & Semiconductors": 0.85,
        "Data & Input Layer": 0.70,
        "AI Models & Foundation Layer": 0.65,
        "Platforms & AI Deployment Layer": 0.75,
        "Applications End User Layer": 0.65,
        "Crypto AI Pivot": 0.55,
        "Diversification": 0.25,
    },
    "Semiconductor Heavy": {
        "Energy & Power Infrastructure": 0.85,
        "Data Centers & Physical Infrastructure": 0.90,
        "Compute Hardware & Semiconductors": 1.35,
        "Data & Input Layer": 0.70,
        "AI Models & Foundation Layer": 0.70,
        "Platforms & AI Deployment Layer": 0.75,
        "Applications End User Layer": 0.65,
        "Crypto AI Pivot": 0.40,
        "Diversification": 0.25,
    },
    "Full AI Stack / Flywheel": {
        "Energy & Power Infrastructure": 1.10,
        "Data Centers & Physical Infrastructure": 1.10,
        "Compute Hardware & Semiconductors": 1.10,
        "Data & Input Layer": 1.00,
        "AI Models & Foundation Layer": 0.95,
        "Platforms & AI Deployment Layer": 1.00,
        "Applications End User Layer": 0.95,
        "Crypto AI Pivot": 0.50,
        "Diversification": 0.25,
    },
    "Crypto AI Pivot Optionality": {
        "Energy & Power Infrastructure": 1.00,
        "Data Centers & Physical Infrastructure": 1.05,
        "Compute Hardware & Semiconductors": 0.90,
        "Data & Input Layer": 0.70,
        "AI Models & Foundation Layer": 0.65,
        "Platforms & AI Deployment Layer": 0.75,
        "Applications End User Layer": 0.65,
        "Crypto AI Pivot": 1.20,
        "Diversification": 0.25,
    },
}

SIGNAL_QUERIES = {
    "Energy & Power Infrastructure": [
        "AI data center power demand",
        "AI data center nuclear power deal",
        "hyperscaler power purchase agreement data center",
        "AI electricity grid bottleneck"
    ],
    "Data Centers & Physical Infrastructure": [
        "AI data center expansion",
        "hyperscale data center AI",
        "data center capacity AI cloud",
        "AI data center cooling power"
    ],
    "Compute Hardware & Semiconductors": [
        "NVIDIA AI chip demand",
        "AI GPU supply shortage",
        "TSMC AI chips capex",
        "AI semiconductor capex"
    ],
    "Data & Input Layer": [
        "enterprise AI data platform demand",
        "Snowflake Palantir AI data platform",
        "AI model training data demand"
    ],
    "AI Models & Foundation Layer": [
        "OpenAI Anthropic Google DeepMind model",
        "foundation model training compute demand",
        "AI model scaling frontier model"
    ],
    "Platforms & AI Deployment Layer": [
        "Microsoft Copilot AI revenue",
        "Amazon AWS AI demand",
        "Google Cloud AI demand",
        "enterprise AI adoption"
    ],
    "Applications End User Layer": [
        "Adobe AI revenue",
        "Salesforce AI agents revenue",
        "ServiceNow AI demand",
        "Tesla AI software"
    ],
    "Crypto AI Pivot": [
        "bitcoin miner AI data center pivot",
        "crypto miner AI HPC hosting",
        "IREN AI cloud data center",
        "Hut 8 AI data center"
    ]
}

# ============================================================
# Core helpers
# ============================================================

def classify_layer(company, ticker):
    text = f"{company} {ticker}".lower()
    layer_keywords = {
        "Energy & Power Infrastructure": ["nextera", "constellation", "duke", "southern company", "vistra", "ge vernova", "cameco", "woodside", "bhp", "power", "nuclear", "energy", "grid"],
        "Data Centers & Physical Infrastructure": ["equinix", "digital realty", "aws", "azure", "google cloud", "vertiv", "eaton", "data center", "datacenter", "cooling"],
        "Compute Hardware & Semiconductors": ["nvidia", "amd", "intel", "tsmc", "broadcom", "asml", "applied materials", "gpu", "semiconductor", "chip"],
        "Data & Input Layer": ["snowflake", "databricks", "palantir", "alphabet", "google", "meta", "data"],
        "AI Models & Foundation Layer": ["openai", "anthropic", "deepmind", "xai", "foundation model"],
        "Platforms & AI Deployment Layer": ["microsoft", "amazon", "aws", "google cloud", "ibm", "oracle", "azure", "cloud"],
        "Applications End User Layer": ["copilot", "adobe", "salesforce", "tesla", "servicenow"],
        "Crypto AI Pivot": ["coinbase", "iren", "hut 8", "cleanspark", "riot", "mara", "marathon", "cipher", "galaxy", "strategy", "bitmine", "crypto", "bitcoin"],
    }
    for layer, keywords in layer_keywords.items():
        if any(k in text for k in keywords):
            return layer
    return "Diversification"



def get_weights(key_prefix):
    etfs = sorted(df["ETF"].unique())
    weights = {}
    cols = st.columns(4)
    for i, etf in enumerate(etfs):
        with cols[i % 4]:
            weights[etf] = st.number_input(
                label=f"{etf} %",
                min_value=0.0,
                max_value=100.0,
                value=float(DEFAULT_WEIGHTS.get(etf, 0.0)),
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

def current_company_exposure(norm):
    work = calc_lookthrough(norm)
    current = (
        work.groupby("Ticker", as_index=False)
        .agg(
            Exposure=("Exposure","sum"),
            ETF_Count=("ETF","nunique"),
            ETFs=("ETF", lambda x: ", ".join(sorted(set(x))))
        )
    )
    return current, work

def merged_target_exposure(norm):
    current, work = current_company_exposure(norm)
    merged = target_df.merge(current, on="Ticker", how="left").fillna({"Exposure":0, "ETF_Count":0, "ETFs":"None"})
    return merged, work


# ============================================================
# ETF Holdings Ingestion
# ============================================================

REQUIRED_HOLDINGS_COLUMNS = ["ETF", "Ticker", "Company", "Weight"]

def standardise_holdings_columns(uploaded_df):
    work = uploaded_df.copy()
    work.columns = [str(c).strip() for c in work.columns]

    lower_map = {c.lower(): c for c in work.columns}

    aliases = {
        "ETF": ["etf", "fund", "fund ticker", "fund_ticker", "fund code"],
        "Ticker": ["ticker", "holding ticker", "symbol", "asx code", "identifier", "holding_ticker"],
        "Company": ["company", "name", "holding name", "security name", "issuer", "description"],
        "Weight": ["weight", "weight (%)", "% weight", "portfolio weight", "fund weight", "market value weight"]
    }

    rename_map = {}
    for target, options in aliases.items():
        for opt in options:
            if opt in lower_map:
                rename_map[lower_map[opt]] = target
                break

    work = work.rename(columns=rename_map)

    return work

def clean_uploaded_holdings(uploaded_df, assigned_etf=""):
    work = standardise_holdings_columns(uploaded_df)

    if "ETF" not in work.columns and assigned_etf:
        work["ETF"] = assigned_etf

    missing = [c for c in REQUIRED_HOLDINGS_COLUMNS if c not in work.columns]
    if missing:
        return None, missing

    work = work[REQUIRED_HOLDINGS_COLUMNS].copy()
    work["ETF"] = work["ETF"].astype(str).str.upper().str.strip()
    work["Ticker"] = work["Ticker"].astype(str).str.upper().str.strip()
    work["Company"] = work["Company"].astype(str).str.strip()
    work["Weight"] = (
        work["Weight"].astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", "", regex=False)
    )
    work["Weight"] = pd.to_numeric(work["Weight"], errors="coerce")
    work = work.dropna(subset=["ETF", "Ticker", "Company", "Weight"])

    work["Layer"] = work.apply(lambda r: classify_layer(r["Company"], r["Ticker"]), axis=1)

    return work, []

def holdings_summary(active_df):
    if active_df is None or active_df.empty:
        return pd.DataFrame([{"Metric": "Rows", "Value": 0}])

    rows = [
        {"Metric": "Rows", "Value": len(active_df)},
        {"Metric": "ETFs", "Value": active_df["ETF"].nunique() if "ETF" in active_df.columns else 0},
        {"Metric": "Companies", "Value": active_df["Ticker"].nunique() if "Ticker" in active_df.columns else 0},
        {"Metric": "Total mapped weight", "Value": round(pd.to_numeric(active_df["Weight"], errors="coerce").fillna(0).sum(), 2) if "Weight" in active_df.columns else 0},
    ]

    if "ETF" in active_df.columns:
        rows.append({"Metric": "ETF list", "Value": ", ".join(sorted(active_df["ETF"].dropna().astype(str).unique()))})

    return pd.DataFrame(rows)

# Initialise dynamic holdings data
if "active_holdings_df" not in st.session_state:
    tmp = STATIC_HOLDINGS_DF.copy()
    tmp["Layer"] = tmp.apply(lambda r: classify_layer(r["Company"], r["Ticker"]), axis=1)
    st.session_state["active_holdings_df"] = tmp
    st.session_state["holdings_source"] = "Built-in sample holdings"

df = st.session_state["active_holdings_df"]

# ============================================================
# Live signal helpers
# ============================================================

def classify_signal_layer(text):
    t = text.lower()
    if any(k in t for k in ["power", "electricity", "grid", "nuclear", "energy", "constellation", "nextera"]):
        return "Energy & Power Infrastructure"
    if any(k in t for k in ["data center", "datacenter", "cooling", "hpc", "equinix", "vertiv", "digital realty"]):
        return "Data Centers & Physical Infrastructure"
    if any(k in t for k in ["nvidia", "gpu", "chip", "semiconductor", "tsmc", "asml", "broadcom"]):
        return "Compute Hardware & Semiconductors"
    if any(k in t for k in ["snowflake", "palantir", "databricks", "data platform"]):
        return "Data & Input Layer"
    if any(k in t for k in ["openai", "anthropic", "deepmind", "model", "llm"]):
        return "AI Models & Foundation Layer"
    if any(k in t for k in ["microsoft", "copilot", "aws", "amazon", "google cloud", "enterprise ai", "cloud", "oracle"]):
        return "Platforms & AI Deployment Layer"
    if any(k in t for k in ["adobe", "salesforce", "servicenow", "tesla ai"]):
        return "Applications End User Layer"
    if any(k in t for k in ["bitcoin miner", "crypto miner", "iren", "hut 8", "cleanspark", "riot", "mara"]):
        return "Crypto AI Pivot"
    return "General"

def signal_category(title):
    text = title.lower()
    structural = ["billion", "$", "capex", "multi-year", "contract", "deal", "agreement", "partnership", "power purchase", "ppa", "nuclear", "megawatt", "mw", "gigawatt", "gw", "data center", "datacenter", "expansion", "capacity", "facility", "buildout"]
    tactical = ["earnings", "guidance", "revenue", "sales", "forecast", "quarter", "demand", "launch", "product", "upgrade", "downgrade"]
    noise = ["could", "may", "might", "opinion", "top", "best", "why", "how", "stock to watch", "rumor", "rumour"]
    s = sum(1 for k in structural if k in text)
    t = sum(1 for k in tactical if k in text)
    n = sum(1 for k in noise if k in text)
    if s >= 2 or (s >= 1 and t >= 1):
        return "Structural"
    if t >= 1 and n <= 1:
        return "Tactical"
    return "Noise"

def score_signal(title):
    text = title.lower()
    score = 25
    boosts = ["billion", "$", "capex", "data center", "datacenter", "power", "nuclear", "gpu", "chip", "semiconductor", "contract", "deal", "agreement", "partnership", "expansion", "capacity", "shortage", "supply", "demand"]
    strong = ["multi-year", "gigawatt", "gw", "megawatt", "mw", "nvidia", "tsmc", "microsoft", "amazon", "google", "constellation", "coreweave", "hyperscaler"]
    for w in boosts:
        if w in text:
            score += 5
    for w in strong:
        if w in text:
            score += 8
    cat = signal_category(title)
    if cat == "Structural":
        score += 20
    elif cat == "Tactical":
        score += 5
    else:
        score -= 20
    return max(min(score, 100), 0)

def market_read(layer, category):
    if category == "Noise":
        return "Likely noise — do not act unless confirmed."
    reads = {
        "Energy & Power Infrastructure": "Power and grid constraints may be becoming more important to AI buildout.",
        "Data Centers & Physical Infrastructure": "Physical AI infrastructure and cooling capacity may be gaining importance.",
        "Compute Hardware & Semiconductors": "GPU/chip demand remains central to AI capex.",
        "Data & Input Layer": "Data platforms may gain value as AI workloads scale.",
        "AI Models & Foundation Layer": "Foundation model scaling remains strategically important.",
        "Platforms & AI Deployment Layer": "Cloud/platform players may be converting AI capex into revenue.",
        "Applications End User Layer": "Application companies may capture value from AI adoption.",
        "Crypto AI Pivot": "Crypto miners may gain AI/HPC optionality through power and sites.",
        "General": "General AI signal — monitor but do not overweight."
    }
    return reads.get(layer, "General signal.")

@st.cache_data(ttl=1800)
def fetch_google_news_rss(query, max_items=4):
    encoded = urllib.parse.quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-AU&gl=AU&ceid=AU:en"
    rows = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        channel = root.find("channel")
        if channel is None:
            return []
        for item in channel.findall("item")[:max_items]:
            title = item.findtext("title", default="")
            link = item.findtext("link", default="")
            published = item.findtext("pubDate", default="")
            source = ""
            source_el = item.find("source")
            if source_el is not None and source_el.text:
                source = source_el.text
            if title:
                rows.append({"Query": query, "Title": title, "Source": source, "Published": published, "Link": link})
    except Exception:
        return []
    return rows

def fetch_live_signals():
    rows = []
    for default_layer, queries in SIGNAL_QUERIES.items():
        for q in queries[:2]:
            for item in fetch_google_news_rss(q, max_items=3):
                layer = classify_signal_layer(item["Title"])
                if layer == "General":
                    layer = default_layer
                category = signal_category(item["Title"])
                score = score_signal(item["Title"])
                rows.append({
                    "AI Layer": layer,
                    "Signal Category": category,
                    "Signal Score": score,
                    "Title": item["Title"],
                    "Source": item["Source"],
                    "Published": item["Published"],
                    "Market Read": market_read(layer, category),
                    "Link": item["Link"]
                })
    if not rows:
        return pd.DataFrame(columns=["AI Layer","Signal Category","Signal Score","Title","Source","Published","Market Read","Link"])
    return pd.DataFrame(rows).drop_duplicates(subset=["Title"]).sort_values(["Signal Category","Signal Score"], ascending=[True, False])

def calculate_live_boosts(signals, include_tactical=True):
    boosts = {layer: 0.0 for layer in AI_LAYERS if layer != "Diversification"}
    if signals.empty:
        return boosts
    usable = signals[signals["Signal Category"] == "Structural"].copy()
    if include_tactical:
        usable = pd.concat([usable, signals[signals["Signal Category"] == "Tactical"]])
    for layer in boosts:
        layer_df = usable[usable["AI Layer"] == layer]
        if layer_df.empty:
            continue
        structural_count = len(layer_df[layer_df["Signal Category"] == "Structural"])
        tactical_count = len(layer_df[layer_df["Signal Category"] == "Tactical"])
        avg_score = layer_df["Signal Score"].mean()
        boosts[layer] = min(round((avg_score / 100) * 0.20 + structural_count * 0.08 + tactical_count * 0.03, 2), 0.45)
    return boosts

# ============================================================
# Dynamic ranking and signals
# ============================================================

def importance_multiplier(layer, preset_name, live_boosts=None):
    base = LAYER_PRESETS[preset_name].get(layer, 0.50)
    if live_boosts:
        base += live_boosts.get(layer, 0.0)
    return base

def dynamic_gap_score(row, preset_name, live_boosts=None):
    exposure = row["Exposure"]
    base = row["Base Importance"]
    multiplier = importance_multiplier(row["Layer"], preset_name, live_boosts)
    dynamic_importance = base * multiplier
    exposure_penalty = exposure * 14
    concentration_penalty = max(exposure - 5, 0) * 20
    score = dynamic_importance - exposure_penalty - concentration_penalty
    return max(round(score, 1), 0)

def build_dynamic_ranking(norm, preset_name, live_boosts=None):
    merged, work = merged_target_exposure(norm)
    merged["Layer Multiplier"] = merged["Layer"].apply(lambda c: importance_multiplier(c, preset_name, live_boosts))
    merged["Dynamic Importance"] = (merged["Base Importance"] * merged["Layer Multiplier"]).round(1)
    merged["Gap Score"] = merged.apply(lambda r: dynamic_gap_score(r, preset_name, live_boosts), axis=1)

    def signal(row):
        exposure = row["Exposure"]
        score = row["Gap Score"]
        layer = row["Layer"]
        if exposure > 6:
            return "LIMIT"
        if score >= 95 and exposure < 1:
            return "STRONG BUY"
        if score >= 75:
            return "BUY"
        if score >= 55:
            return "ADD"
        if layer == "Crypto AI Pivot" and score >= 35:
            return "OPTIONALITY"
        return "HOLD"

    merged["Signal"] = merged.apply(signal, axis=1)

    def reason(row):
        if row["Signal"] == "LIMIT":
            return f"High current exposure at {row['Exposure']:.2f}%"
        if row["Signal"] in ["STRONG BUY", "BUY"]:
            return f"High dynamic importance ({row['Dynamic Importance']:.1f}) and low exposure ({row['Exposure']:.2f}%)"
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
        return "No mapped ETF route in sample data / private company"
    return ", ".join([f"{r['ETF']} ({r['Weight']:.1f}%)" for _, r in matches.head(3).iterrows()])

# ============================================================
# Backtest and signal validation
# ============================================================

BASE_RETURNS = {
    "IVV": 0.008, "VEU": 0.006, "NDQ": 0.011, "VHY": 0.005,
    "AINF": 0.012, "SEMI": 0.014, "CRYP": 0.018, "GXAI": 0.013
}
VOL = {
    "IVV": 0.035, "VEU": 0.030, "NDQ": 0.055, "VHY": 0.025,
    "AINF": 0.060, "SEMI": 0.075, "CRYP": 0.140, "GXAI": 0.070
}

LAYER_TO_ETF_TILT = {
    "Energy & Power Infrastructure": ["AINF", "VHY"],
    "Data Centers & Physical Infrastructure": ["AINF"],
    "Compute Hardware & Semiconductors": ["SEMI", "NDQ"],
    "Data & Input Layer": ["GXAI", "NDQ"],
    "AI Models & Foundation Layer": ["GXAI", "NDQ"],
    "Platforms & AI Deployment Layer": ["NDQ", "IVV"],
    "Applications End User Layer": ["NDQ", "IVV"],
    "Crypto AI Pivot": ["CRYP"],
}

def normalize_weights(weights):
    total = sum(weights.values())
    if total == 0:
        return {k: 0 for k in weights}
    return {k: v / total for k, v in weights.items()}

def signal_tilt_weights(base_weights, live_boosts, tilt_strength=1.0):
    adjusted = dict(base_weights)
    for layer, boost in live_boosts.items():
        etfs = LAYER_TO_ETF_TILT.get(layer, [])
        for etf in etfs:
            if etf in adjusted:
                adjusted[etf] += boost * 10 * tilt_strength
    return normalize_weights(adjusted)

def simulate_returns(months, seed, ai_cycle_strength, volatility_multiplier):
    random.seed(seed)
    rows = []
    for month in range(1, months + 1):
        regime_boost = 0.0
        if month > months * 0.35:
            regime_boost = 0.004 * ai_cycle_strength
        if month > months * 0.65:
            regime_boost = 0.006 * ai_cycle_strength
        for etf in BASE_RETURNS:
            noise = random.gauss(0, VOL[etf] * volatility_multiplier)
            ai_extra = regime_boost if etf in ["AINF", "SEMI", "GXAI", "NDQ"] else 0
            crypto_extra = regime_boost * 1.2 if etf == "CRYP" else 0
            rows.append({"Month": month, "ETF": etf, "Return": BASE_RETURNS[etf] + ai_extra + crypto_extra + noise})
    return pd.DataFrame(rows)

def run_backtest(start_value, monthly_contribution, months, baseline_weights, signal_weights, seed, ai_cycle_strength, volatility_multiplier):
    returns = simulate_returns(months, seed, ai_cycle_strength, volatility_multiplier)
    baseline_value = start_value
    signal_value = start_value
    rows = []
    for month in range(1, months + 1):
        month_returns = returns[returns["Month"] == month].set_index("ETF")["Return"].to_dict()
        baseline_r = sum(baseline_weights.get(etf, 0) * month_returns.get(etf, 0) for etf in BASE_RETURNS)
        signal_r = sum(signal_weights.get(etf, 0) * month_returns.get(etf, 0) for etf in BASE_RETURNS)
        baseline_value = baseline_value * (1 + baseline_r) + monthly_contribution
        signal_value = signal_value * (1 + signal_r) + monthly_contribution
        rows.append({"Month": month, "Strategy": "Baseline", "Portfolio Value": baseline_value, "Return": baseline_r})
        rows.append({"Month": month, "Strategy": "Signal Tilt", "Portfolio Value": signal_value, "Return": signal_r})
    return pd.DataFrame(rows)

def max_drawdown(vals):
    peak = vals.cummax()
    dd = (vals - peak) / peak
    return dd.min()

def run_monte_carlo(start_value, monthly_contribution, months, baseline_weights, signal_weights, ai_cycle_strength, volatility_multiplier, runs, seed):
    rows = []
    for i in range(runs):
        bt = run_backtest(start_value, monthly_contribution, months, baseline_weights, signal_weights, seed + i, ai_cycle_strength, volatility_multiplier)
        b = bt[bt["Strategy"] == "Baseline"].sort_values("Month")
        s = bt[bt["Strategy"] == "Signal Tilt"].sort_values("Month")
        b_final = b["Portfolio Value"].iloc[-1]
        s_final = s["Portfolio Value"].iloc[-1]
        rows.append({
            "Run": i + 1,
            "Seed": seed + i,
            "Baseline Final": b_final,
            "Signal Tilt Final": s_final,
            "Outperformance $": s_final - b_final,
            "Outperformance %": ((s_final / b_final) - 1) * 100 if b_final else 0,
            "Baseline Max DD %": max_drawdown(b["Portfolio Value"]) * 100,
            "Signal Max DD %": max_drawdown(s["Portfolio Value"]) * 100,
        })
    return pd.DataFrame(rows)

def validate_signals(signals):
    if signals.empty:
        return pd.DataFrame(), pd.DataFrame()
    validation = signals.copy()
    validation["Validation Label"] = validation["Signal Category"].map({
        "Structural": "High quality",
        "Tactical": "Watchlist",
        "Noise": "Ignore"
    }).fillna("Unknown")
    validation["Actionability Score"] = pd.to_numeric(validation["Signal Score"], errors="coerce").fillna(0).astype(float)
    noise_mask = validation["Signal Category"] == "Noise"
    tactical_mask = validation["Signal Category"] == "Tactical"
    validation.loc[noise_mask, "Actionability Score"] = validation.loc[noise_mask, "Actionability Score"] * 0.3
    validation.loc[tactical_mask, "Actionability Score"] = validation.loc[tactical_mask, "Actionability Score"] * 0.7
    validation["Actionability Score"] = validation["Actionability Score"].round(1)
    summary = (
        validation.groupby(["AI Layer", "Validation Label"], as_index=False)
        .agg(
            Count=("Title","count"),
            Avg_Actionability=("Actionability Score","mean"),
            Avg_Raw_Score=("Signal Score","mean")
        )
    )
    summary["Avg_Actionability"] = summary["Avg_Actionability"].round(1)
    summary["Avg_Raw_Score"] = summary["Avg_Raw_Score"].round(1)
    return validation.sort_values("Actionability Score", ascending=False), summary.sort_values("Avg_Actionability", ascending=False)


# ============================================================
# Real market signal performance tracker
# ============================================================

YAHOO_TICKER_MAP = {
    "NVDA": "NVDA", "MSFT": "MSFT", "GOOGL": "GOOGL", "AMZN": "AMZN", "META": "META",
    "TSM": "TSM", "ASML": "ASML", "AVGO": "AVGO", "AMD": "AMD", "INTC": "INTC",
    "CEG": "CEG", "NEE": "NEE", "GEV": "GEV", "CCO": "CCJ", "DUK": "DUK", "SO": "SO", "VST": "VST",
    "EQIX": "EQIX", "DLR": "DLR", "VRT": "VRT", "ETN": "ETN",
    "PLTR": "PLTR", "SNOW": "SNOW", "ADBE": "ADBE", "CRM": "CRM", "NOW": "NOW",
    "TSLA": "TSLA", "ORCL": "ORCL", "IBM": "IBM",
    "COIN": "COIN", "IREN": "IREN", "HUT": "HUT", "CLSK": "CLSK", "RIOT": "RIOT", "MARA": "MARA",
    "CIFR": "CIFR", "MSTR": "MSTR", "BMNR": "BMNR",
}

if "signal_history" not in st.session_state:
    st.session_state.signal_history = pd.DataFrame(columns=[
        "Signal ID", "Date Logged", "Ticker", "Yahoo Ticker", "Company", "Layer", "Signal",
        "Gap Score", "Entry Price", "Price 7D", "Return 7D %", "Price 30D", "Return 30D %",
        "Price 90D", "Return 90D %", "Status"
    ])

def resolve_yahoo_ticker(ticker):
    return YAHOO_TICKER_MAP.get(str(ticker), str(ticker))

@st.cache_data(ttl=3600)
def get_price_on_or_after(yahoo_ticker, target_date, lookahead_days=7):
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
        close = data["Close"].dropna()
        if close.empty:
            return None
        return float(close.iloc[0])
    except Exception:
        return None

@st.cache_data(ttl=3600)
def get_latest_price(yahoo_ticker):
    try:
        data = yf.download(yahoo_ticker, period="5d", progress=False, auto_adjust=True)
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
    try:
        if pd.isna(entry_price) or pd.isna(exit_price) or float(entry_price) == 0:
            return None
        return round(((float(exit_price) / float(entry_price)) - 1) * 100, 2)
    except Exception:
        return None

def log_ranking_signals_to_tracker(ranking_df):
    today = dt.date.today()
    history = st.session_state.signal_history.copy()
    actionable = ranking_df[ranking_df["Signal"].isin(["STRONG BUY", "BUY", "ADD", "OPTIONALITY"])].copy()
    new_rows = []

    for _, row in actionable.iterrows():
        ticker = str(row["Ticker"])
        yahoo_ticker = resolve_yahoo_ticker(ticker)
        entry_price = get_price_on_or_after(yahoo_ticker, today)
        signal_id = f"{today}_{ticker}_{row['Signal']}_{len(history) + len(new_rows) + 1}"

        new_rows.append({
            "Signal ID": signal_id,
            "Date Logged": today.isoformat(),
            "Ticker": ticker,
            "Yahoo Ticker": yahoo_ticker,
            "Company": row.get("Company", ""),
            "Layer": row.get("Layer", ""),
            "Signal": row.get("Signal", ""),
            "Gap Score": row.get("Gap Score", 0),
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
        st.session_state.signal_history = pd.concat([history, pd.DataFrame(new_rows)], ignore_index=True)

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

        if (today - logged).days >= 7 and pd.isna(row["Price 7D"]):
            price_7d = get_price_on_or_after(yahoo_ticker, logged + dt.timedelta(days=7))
            history.at[idx, "Price 7D"] = price_7d
            history.at[idx, "Return 7D %"] = calculate_return(entry, price_7d)

        if (today - logged).days >= 30 and pd.isna(row["Price 30D"]):
            price_30d = get_price_on_or_after(yahoo_ticker, logged + dt.timedelta(days=30))
            history.at[idx, "Price 30D"] = price_30d
            history.at[idx, "Return 30D %"] = calculate_return(entry, price_30d)

        if (today - logged).days >= 90 and pd.isna(row["Price 90D"]):
            price_90d = get_price_on_or_after(yahoo_ticker, logged + dt.timedelta(days=90))
            history.at[idx, "Price 90D"] = price_90d
            history.at[idx, "Return 90D %"] = calculate_return(entry, price_90d)

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

def layer_performance_summary(history, horizon="30D"):
    col = f"Return {horizon} %"
    if history.empty or col not in history.columns:
        return pd.DataFrame()
    valid = history[pd.notna(history[col])].copy()
    if valid.empty:
        return pd.DataFrame()
    out = valid.groupby("Layer", as_index=False).agg(
        Signals=("Ticker", "count"),
        Avg_Return=(col, "mean"),
        Median_Return=(col, "median"),
        Win_Rate=(col, lambda x: (x > 0).mean() * 100)
    )
    out["Avg_Return"] = out["Avg_Return"].round(2)
    out["Median_Return"] = out["Median_Return"].round(2)
    out["Win_Rate"] = out["Win_Rate"].round(1)
    return out.sort_values("Avg_Return", ascending=False)


# ============================================================
# AI Wealth Radar Daily helper
# ============================================================

def build_daily_radar(signals, live_boosts, ranking):
    output = {}

    if signals is None or signals.empty:
        output["key_signals"] = pd.DataFrame()
    else:
        structural = signals[signals["Signal Category"] == "Structural"].copy()
        output["key_signals"] = structural.sort_values("Signal Score", ascending=False).head(5)

    boosts_df = pd.DataFrame([
        {"Layer": k, "Boost": v}
        for k, v in live_boosts.items()
    ]).sort_values("Boost", ascending=False)

    output["layer_shifts"] = boosts_df

    if ranking is None or ranking.empty:
        output["opportunities"] = pd.DataFrame()
        output["risks"] = pd.DataFrame()
    else:
        ranked = ranking.copy()
        if "ETF Route" not in ranked.columns:
            ranked["ETF Route"] = ranked["Ticker"].apply(suggest_etf_route)
        output["opportunities"] = ranked[ranked["Signal"].isin(["STRONG BUY", "BUY"])].head(5)
        output["watchlist"] = ranked[ranked["Signal"].isin(["ADD", "OPTIONALITY"])].head(5)
        output["risks"] = ranked[ranked["Signal"] == "LIMIT"].head(5)

    return output


# ============================================================
# ETF Translation + Upgrade Engine
# ============================================================

def best_etf_for_company_dynamic(ticker, norm=None):
    matches = df[df["Ticker"] == ticker].copy()

    if matches.empty:
        return "No mapped ETF route"

    if norm is None:
        matches["ETF Weight"] = 0
    else:
        matches["ETF Weight"] = matches["ETF"].map(norm).fillna(0)

    # Higher ETF holding weight is good.
    # If user already owns the ETF, route is more practical.
    matches["Route Score"] = matches["Weight"] * (1 + matches["ETF Weight"])

    ranked = matches.sort_values("Route Score", ascending=False)
    top = ranked.iloc[0]

    return f"{top['ETF']} ({top['Weight']:.1f}% holding)"

def all_etf_routes_for_company(ticker):
    matches = df[df["Ticker"] == ticker].copy()

    if matches.empty:
        return "No mapped ETF route"

    matches = matches.sort_values("Weight", ascending=False)
    return ", ".join([f"{r['ETF']} ({r['Weight']:.1f}%)" for _, r in matches.iterrows()])

def aggregate_etf_demand_from_ranking(ranking, norm=None):
    if ranking is None or ranking.empty:
        return pd.DataFrame(columns=["ETF", "Demand Score", "Signal Count", "Top Drivers"])

    actionable = ranking[ranking["Signal"].isin(["STRONG BUY", "BUY", "ADD", "OPTIONALITY"])].copy()

    rows = []

    for _, row in actionable.iterrows():
        ticker = row["Ticker"]
        gap_score = float(row.get("Gap Score", 0))
        signal = row.get("Signal", "")

        matches = df[df["Ticker"] == ticker].copy()

        if matches.empty:
            continue

        for _, m in matches.iterrows():
            etf = m["ETF"]
            holding_weight = float(m["Weight"])

            owned_weight = 0
            if norm is not None:
                owned_weight = float(norm.get(etf, 0))

            # Demand score blends signal strength, ETF holding concentration,
            # and current ownership practicality.
            demand_score = gap_score * holding_weight * (1 + owned_weight)

            rows.append({
                "ETF": etf,
                "Ticker": ticker,
                "Company": row.get("Company", ticker),
                "Signal": signal,
                "Layer": row.get("Layer", ""),
                "Gap Score": gap_score,
                "Holding Weight": holding_weight,
                "Portfolio ETF Weight": round(owned_weight * 100, 2),
                "Demand Score": demand_score
            })

    if not rows:
        return pd.DataFrame(columns=["ETF", "Demand Score", "Signal Count", "Top Drivers"])

    detail = pd.DataFrame(rows)

    summary = (
        detail.groupby("ETF", as_index=False)
        .agg(
            Demand_Score=("Demand Score", "sum"),
            Signal_Count=("Ticker", "nunique"),
            Top_Drivers=("Company", lambda x: ", ".join(list(dict.fromkeys(x))[:5]))
        )
        .sort_values("Demand_Score", ascending=False)
    )

    summary = summary.rename(columns={
        "Demand_Score": "Demand Score",
        "Signal_Count": "Signal Count",
        "Top_Drivers": "Top Drivers"
    })

    summary["Demand Score"] = summary["Demand Score"].round(1)

    return summary

def etf_translation_table(ranking, norm=None):
    if ranking is None or ranking.empty:
        return pd.DataFrame()

    out = ranking.copy()
    out["Best ETF Route"] = out["Ticker"].apply(lambda t: best_etf_for_company_dynamic(t, norm))
    out["All ETF Routes"] = out["Ticker"].apply(all_etf_routes_for_company)
    return out

def detect_unmapped_companies_from_ranking(ranking):
    if ranking is None or ranking.empty:
        return pd.DataFrame()

    mapped = set(df["Ticker"].dropna().astype(str).unique())
    out = ranking[~ranking["Ticker"].astype(str).isin(mapped)].copy()

    if out.empty:
        return pd.DataFrame(columns=["Ticker", "Company", "Layer", "Signal", "Gap Score", "Suggested Action"])

    out["Suggested Action"] = "Research ETF coverage / consider whether existing ETFs capture this indirectly"
    return out[["Ticker", "Company", "Layer", "Signal", "Gap Score", "Suggested Action"]]

def detect_possible_new_companies_from_signals(signals):
    # Simple MVP: detects uppercase ticker-like words in headlines not already mapped.
    # This is intentionally conservative and should be treated as a watchlist, not proof.
    if signals is None or signals.empty:
        return pd.DataFrame(columns=["Candidate", "Mentions", "Example Headline"])

    known = set(df["Ticker"].dropna().astype(str).str.upper().unique())
    ignore = set([
        "AI", "AUS", "USA", "CEO", "CFO", "GPU", "CPU", "HPC", "LLM", "ETF",
        "AWS", "API", "IPO", "SEC", "USD", "MW", "GW", "EV", "IT"
    ])

    candidates = {}

    for _, row in signals.iterrows():
        title = str(row.get("Title", ""))
        words = title.replace(",", " ").replace(".", " ").replace(":", " ").replace("-", " ").split()

        for word in words:
            cleaned = "".join(ch for ch in word if ch.isalnum()).upper()
            if 2 <= len(cleaned) <= 6 and cleaned.isalpha():
                if cleaned not in known and cleaned not in ignore:
                    if cleaned not in candidates:
                        candidates[cleaned] = {"Mentions": 0, "Example Headline": title}
                    candidates[cleaned]["Mentions"] += 1

    if not candidates:
        return pd.DataFrame(columns=["Candidate", "Mentions", "Example Headline"])

    result = pd.DataFrame([
        {"Candidate": k, "Mentions": v["Mentions"], "Example Headline": v["Example Headline"]}
        for k, v in candidates.items()
    ])

    return result.sort_values("Mentions", ascending=False).head(25)

def etf_upgrade_recommendations(ranking, signals):
    unmapped = detect_unmapped_companies_from_ranking(ranking)
    emerging = detect_possible_new_companies_from_signals(signals)

    recommendations = []

    if not unmapped.empty:
        recommendations.append({
            "Upgrade Area": "Company coverage gap",
            "Finding": f"{len(unmapped)} high-priority companies are not mapped to current ETF holdings.",
            "Action": "Research whether current ETFs hold them; if not, look for ASX ETFs with exposure."
        })

    if emerging is not None and not emerging.empty:
        recommendations.append({
            "Upgrade Area": "Emerging company watchlist",
            "Finding": f"{len(emerging)} ticker-like candidates appeared in live signals.",
            "Action": "Review candidates manually before adding to universe."
        })

    if ranking is not None and not ranking.empty:
        layer_gaps = (
            ranking[ranking["Signal"].isin(["STRONG BUY", "BUY"])]
            .groupby("Layer", as_index=False)
            .agg(Count=("Ticker", "count"), Avg_Gap=("Gap Score", "mean"))
            .sort_values(["Count", "Avg_Gap"], ascending=False)
        )

        if not layer_gaps.empty:
            top_layer = layer_gaps.iloc[0]["Layer"]
            recommendations.append({
                "Upgrade Area": "ETF suitability",
                "Finding": f"Strongest gaps cluster in: {top_layer}.",
                "Action": "Check whether your current ETFs are the best route for this layer or whether a more targeted ETF exists."
            })

    if not recommendations:
        return pd.DataFrame([{
            "Upgrade Area": "No major gap",
            "Finding": "Current ETF universe covers mapped signals reasonably well.",
            "Action": "Continue monitoring."
        }])

    return pd.DataFrame(recommendations)

# ============================================================
# App
# ============================================================

st.title("⚡ AI Portfolio Engine v8")
st.caption("Full 7-layer AI stack + VHY + backtest + signal validation")

tabs = st.tabs([
    "AI Wealth Radar (Daily)",
    "Holdings Ingestion",
    "Live Signal Engine",
    "Signal Validation",
    "Portfolio",
    "Overlap",
    "Gap Engine",
    "Dynamic Ranking",
    "Weighted Buy Signals",
    "ETF Translation & Upgrade",
    "Backtest",
    "Signal Performance Tracker"
])

with st.sidebar:
    st.header("Signal Settings")
    use_live_signals = st.toggle("Use live signals", value=True)
    include_tactical = st.toggle("Include tactical signals", value=True)
    st.caption("Structural signals carry the most weight. Tactical signals are optional.")

signals = fetch_live_signals() if use_live_signals else pd.DataFrame(columns=["AI Layer","Signal Category","Signal Score","Title","Source","Published","Market Read","Link"])
live_boosts = calculate_live_boosts(signals, include_tactical=include_tactical) if use_live_signals else {layer: 0.0 for layer in AI_LAYERS if layer != "Diversification"}


# Holdings Ingestion
with tabs[1]:
    st.subheader("ETF Holdings Ingestion")
    st.write("Upload real ETF holdings to replace the built-in sample data across the full engine.")

    st.info(
        "Accepted columns: ETF, Ticker, Company, Weight. "
        "Common provider column names like Symbol, Holding Name, Security Name, Weight (%) will be standardised where possible."
    )

    uploaded_files = st.file_uploader(
        "Upload one or more ETF holdings files",
        type=["csv"],
        accept_multiple_files=True,
        key="holdings_ingestion_files"
    )

    assigned_etf = st.text_input(
        "Optional: assign ETF ticker if uploaded file does not include ETF column",
        value="",
        key="assigned_etf_ingestion"
    ).strip().upper()

    if uploaded_files:
        frames = []
        errors = []

        for uploaded_file in uploaded_files:
            try:
                raw = pd.read_csv(uploaded_file)
                cleaned, missing = clean_uploaded_holdings(raw, assigned_etf=assigned_etf)

                if cleaned is None:
                    errors.append(f"{uploaded_file.name}: missing columns {missing}")
                else:
                    frames.append(cleaned)

            except Exception as e:
                errors.append(f"{uploaded_file.name}: {e}")

        if errors:
            st.error("Some files could not be loaded:")
            for err in errors:
                st.write(f"- {err}")

        if frames:
            combined = pd.concat(frames, ignore_index=True)
            st.session_state["active_holdings_df"] = combined
            st.session_state["holdings_source"] = "Uploaded ETF holdings"
            st.success("Uploaded holdings are now active across the full app.")
            st.rerun()

    active_df = st.session_state["active_holdings_df"]

    st.markdown("### Active Holdings Source")
    st.write(f"**Source:** {st.session_state.get('holdings_source', 'Unknown')}")

    st.markdown("### Active Holdings Summary")
    st.dataframe(holdings_summary(active_df), use_container_width=True, hide_index=True)

    st.markdown("### Active Holdings Preview")
    st.dataframe(active_df.head(200), use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Revert to built-in sample holdings"):
            tmp = STATIC_HOLDINGS_DF.copy()
            tmp["Layer"] = tmp.apply(lambda r: classify_layer(r["Company"], r["Ticker"]), axis=1)
            st.session_state["active_holdings_df"] = tmp
            st.session_state["holdings_source"] = "Built-in sample holdings"
            st.success("Reverted to built-in sample holdings.")
            st.rerun()

    with c2:
        csv_data = active_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download active holdings CSV",
            data=csv_data,
            file_name="active_holdings.csv",
            mime="text/csv"
        )


# Live signals
with tabs[2]:
    st.subheader("Live AI Signal Engine")
    if not use_live_signals:
        st.info("Live signals are disabled.")
    elif signals.empty:
        st.warning("No live signals could be fetched. The app is running on base importance only.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Signals fetched", len(signals))
        c2.metric("Structural", len(signals[signals["Signal Category"] == "Structural"]))
        c3.metric("Tactical", len(signals[signals["Signal Category"] == "Tactical"]))
        c4.metric("Noise", len(signals[signals["Signal Category"] == "Noise"]))

        st.markdown("### Live Layer Boosts")
        boost_df = pd.DataFrame([{"AI Layer": k, "Live Boost": v} for k, v in live_boosts.items()])
        st.dataframe(boost_df.sort_values("Live Boost", ascending=False), use_container_width=True, hide_index=True)

        for cat in ["Structural","Tactical","Noise"]:
            st.markdown(f"### {cat} Signals")
            view = signals[signals["Signal Category"] == cat].sort_values("Signal Score", ascending=False)
            st.dataframe(view[["AI Layer","Signal Score","Title","Source","Published","Market Read","Link"]], use_container_width=True, hide_index=True)

# Signal validation
with tabs[3]:
    st.subheader("Signal Validation Layer")
    st.write("Validates signal quality by separating high-quality structural signals from tactical/watchlist items and noise.")
    validated, validation_summary = validate_signals(signals)

    if validated.empty:
        st.warning("No signals available to validate.")
    else:
        st.markdown("### Validation Summary")
        st.dataframe(validation_summary, use_container_width=True, hide_index=True)

        st.markdown("### Validated Signals")
        st.dataframe(
            validated[["Validation Label","Actionability Score","AI Layer","Signal Category","Signal Score","Title","Source","Market Read","Link"]],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### Actionability by Layer")
        layer_action = validation_summary.groupby("AI Layer", as_index=False)["Avg_Actionability"].mean()
        st.bar_chart(layer_action.set_index("AI Layer")["Avg_Actionability"])

# Portfolio
with tabs[4]:
    st.subheader("Portfolio")
    norm = get_weights("portfolio")
    work = calc_lookthrough(norm)

    company = work.groupby(["Ticker","Company","Layer"], as_index=False)["Exposure"].sum().sort_values("Exposure", ascending=False)
    layer = work.groupby("Layer", as_index=False)["Exposure"].sum().sort_values("Exposure", ascending=False)

    st.markdown("### Company Look-through Exposure")
    st.dataframe(company, use_container_width=True, hide_index=True)

    st.markdown("### Layer Exposure")
    st.dataframe(layer, use_container_width=True, hide_index=True)
    st.bar_chart(layer.set_index("Layer")["Exposure"])

# Overlap
with tabs[5]:
    st.subheader("Overlap Engine")
    norm = get_weights("overlap")
    current, work = current_company_exposure(norm)

    overlap = (
        work.groupby(["Ticker","Company","Layer"], as_index=False)
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
with tabs[6]:
    st.subheader("Company Gap Engine")
    norm = get_weights("gap")
    merged, work = merged_target_exposure(norm)

    st.markdown("### Missing AI Exposure")
    gaps = merged[merged["Exposure"] == 0].sort_values("Layer")
    st.dataframe(gaps, use_container_width=True, hide_index=True)

    st.markdown("### Underweight Exposure (<1%)")
    under = merged[(merged["Exposure"] > 0) & (merged["Exposure"] < 1)].sort_values("Exposure")
    st.dataframe(under, use_container_width=True, hide_index=True)

    st.markdown("### Full 7-Layer Target Universe")
    st.dataframe(merged.sort_values(["Layer","Base Importance"], ascending=[True, False]), use_container_width=True, hide_index=True)

# Dynamic Ranking
with tabs[7]:
    st.subheader("Dynamic AI Importance Ranking")
    preset = st.selectbox("Choose AI thesis preset", list(LAYER_PRESETS.keys()), key="ranking_preset")
    norm = get_weights("ranking")
    ranking = build_dynamic_ranking(norm, preset, live_boosts=live_boosts)
    ranking["ETF Route"] = ranking["Ticker"].apply(lambda t: best_etf_for_company_dynamic(t, norm))

    st.dataframe(
        ranking[["Signal","Ticker","Company","Layer","Base Importance","Layer Multiplier","Dynamic Importance","Exposure","Gap Score","ETF Route","Reason"]],
        use_container_width=True,
        hide_index=True
    )
    top = ranking.sort_values("Gap Score", ascending=False).head(15)
    st.bar_chart(top.set_index("Company")["Gap Score"])

# Weighted Buy Signals
with tabs[8]:
    st.subheader("Weighted Buy Signals")
    preset = st.selectbox("Choose signal preset", list(LAYER_PRESETS.keys()), key="signals_preset")
    contribution = st.number_input("Next contribution amount ($)", min_value=0, value=3000, step=500)
    norm = get_weights("signals")
    ranking = build_dynamic_ranking(norm, preset, live_boosts=live_boosts)
    ranking["ETF Route"] = ranking["Ticker"].apply(lambda t: best_etf_for_company_dynamic(t, norm))
    actionable = ranking[ranking["Signal"].isin(["STRONG BUY","BUY","ADD","OPTIONALITY"])].copy()

    if actionable.empty:
        st.success("No high-priority additions detected.")
    else:
        top_actions = actionable.head(5).copy()
        score_sum = top_actions["Gap Score"].sum()
        top_actions["Suggested $"] = (top_actions["Gap Score"] / score_sum * contribution).round(0) if score_sum > 0 else 0
        st.dataframe(top_actions[["Signal","Ticker","Company","Layer","Exposure","Gap Score","ETF Route","Suggested $","Reason"]], use_container_width=True, hide_index=True)

        if st.button("Log these signals to performance tracker"):
            log_ranking_signals_to_tracker(top_actions)
            st.success("Signals logged to the performance tracker with real entry prices where available.")

    st.markdown("### Limit / Avoid Adding")
    limits = ranking[ranking["Signal"] == "LIMIT"]
    if limits.empty:
        st.success("No major concentration limits detected.")
    else:
        st.dataframe(limits[["Ticker","Company","Layer","Exposure","Reason"]], use_container_width=True, hide_index=True)


# ETF Translation & Upgrade Engine
with tabs[9]:
    st.subheader("ETF Translation & Upgrade Engine")
    st.write("Converts company-level signals into ETF-level actions and flags missing coverage.")

    preset = st.selectbox(
        "Choose ETF translation preset",
        list(LAYER_PRESETS.keys()),
        key="etf_translation_preset"
    )

    norm = get_weights("etf_translation")
    ranking = build_dynamic_ranking(norm, preset, live_boosts=live_boosts)

    translated = etf_translation_table(ranking, norm)
    etf_demand = aggregate_etf_demand_from_ranking(ranking, norm)
    unmapped = detect_unmapped_companies_from_ranking(ranking)
    emerging = detect_possible_new_companies_from_signals(signals)
    upgrades = etf_upgrade_recommendations(ranking, signals)

    st.markdown("### Company Signal → ETF Route")
    st.write("This ensures a company-level STRONG BUY / BUY signal gets translated into the ETF you can actually buy.")
    if translated.empty:
        st.info("No ranking data available.")
    else:
        st.dataframe(
            translated[[
                "Signal", "Ticker", "Company", "Layer", "Exposure", "Gap Score",
                "Best ETF Route", "All ETF Routes", "Reason"
            ]],
            use_container_width=True,
            hide_index=True
        )

    st.markdown("### ETF Demand Engine")
    st.write("Aggregates all actionable company signals into ETF-level demand.")
    if etf_demand.empty:
        st.info("No actionable ETF demand detected.")
    else:
        st.dataframe(etf_demand, use_container_width=True, hide_index=True)
        st.bar_chart(etf_demand.set_index("ETF")["Demand Score"])

    st.markdown("### ETF Upgrade Recommendations")
    st.write("Flags when current ETFs may not capture emerging or high-priority AI exposure.")
    st.dataframe(upgrades, use_container_width=True, hide_index=True)

    st.markdown("### Missing Mapped Coverage")
    if unmapped.empty:
        st.success("All ranked companies are mapped to current ETF holding data or are not currently actionable.")
    else:
        st.warning("Some ranked companies do not have a mapped ETF route in your current holdings dataset.")
        st.dataframe(unmapped, use_container_width=True, hide_index=True)

    st.markdown("### Emerging Company Watchlist From Live Signals")
    st.caption("Conservative ticker-like extraction from headlines. Treat as a prompt for manual research, not proof.")
    if emerging.empty:
        st.success("No new ticker-like candidates detected in live signal headlines.")
    else:
        st.dataframe(emerging, use_container_width=True, hide_index=True)

    st.markdown("### Practical ETF-Only Rule")
    st.info(
        "Do not act on a company signal unless this tab shows a clear ETF route or flags it as a deliberate ETF coverage gap to research."
    )


# Backtest
with tabs[10]:
    st.subheader("Backtest + Monte Carlo Layer")
    st.write("Tests a signal-tilted portfolio against your baseline using synthetic scenario paths.")

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        start_value = st.number_input("Starting portfolio value ($)", min_value=0, value=110000, step=5000)
    with b2:
        monthly_contribution = st.number_input("Monthly contribution ($)", min_value=0, value=2000, step=500)
    with b3:
        months = st.slider("Months", 12, 120, 60)
    with b4:
        seed = st.number_input("Scenario seed", min_value=1, value=7, step=1)

    s1, s2, s3 = st.columns(3)
    with s1:
        ai_cycle_strength = st.slider("AI cycle strength", 0.0, 3.0, 1.0, 0.1)
    with s2:
        volatility_multiplier = st.slider("Volatility multiplier", 0.25, 3.0, 1.0, 0.05)
    with s3:
        monte_carlo_runs = st.slider("Monte Carlo runs", 10, 500, 100, 10)

    st.markdown("### Baseline Weights")
    baseline_raw = {}
    cols = st.columns(4)
    for i, etf in enumerate(BASE_RETURNS.keys()):
        with cols[i % 4]:
            baseline_raw[etf] = st.number_input(f"Baseline {etf} %", min_value=0.0, max_value=100.0, value=float(DEFAULT_WEIGHTS.get(etf,0.0)), step=1.0, key=f"bt_base_{etf}")
    baseline_weights = normalize_weights(baseline_raw)

    tilt_strength = st.slider("Signal tilt strength", 0.0, 3.0, 1.0, 0.1)
    signal_weights = signal_tilt_weights(baseline_raw, live_boosts, tilt_strength=tilt_strength)

    st.markdown("### Signal Tilt Weights")
    tilt_df = pd.DataFrame([{"ETF": k, "Signal Tilt Weight %": round(v * 100, 2)} for k, v in signal_weights.items()])
    st.dataframe(tilt_df, use_container_width=True, hide_index=True)

    bt = run_backtest(start_value, monthly_contribution, months, baseline_weights, signal_weights, int(seed), ai_cycle_strength, volatility_multiplier)
    st.line_chart(bt.pivot(index="Month", columns="Strategy", values="Portfolio Value"))

    final = bt.groupby("Strategy").tail(1)[["Strategy","Portfolio Value"]].copy()
    final["Portfolio Value"] = final["Portfolio Value"].round(0)
    st.dataframe(final, use_container_width=True, hide_index=True)

    mc = run_monte_carlo(start_value, monthly_contribution, months, baseline_weights, signal_weights, ai_cycle_strength, volatility_multiplier, monte_carlo_runs, int(seed))
    win_rate = (mc["Outperformance $"] > 0).mean() * 100
    avg_out = mc["Outperformance $"].mean()
    med_out = mc["Outperformance $"].median()
    p10 = mc["Outperformance $"].quantile(0.10)
    p90 = mc["Outperformance $"].quantile(0.90)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Win rate", f"{win_rate:.1f}%")
    m2.metric("Avg outperformance", f"${avg_out:,.0f}")
    m3.metric("Median outperformance", f"${med_out:,.0f}")
    m4.metric("10th percentile", f"${p10:,.0f}")

    st.metric("90th percentile", f"${p90:,.0f}")

    st.markdown("### Monte Carlo Detail")
    st.dataframe(mc.round(1), use_container_width=True, hide_index=True)

    st.caption("Synthetic scenario test only. This does not predict future returns.")


# Signal Performance Tracker
with tabs[11]:
    st.subheader("Signal Performance Tracker")
    st.write("Tracks actual forward performance of logged buy signals using yfinance prices.")

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
        st.info("No signals logged yet. Go to Weighted Buy Signals and click the log button.")
    else:
        st.markdown("### Signal History")
        st.dataframe(history, use_container_width=True, hide_index=True)

        st.markdown("### Overall Performance")
        summary = performance_summary(history)
        if summary.empty:
            st.warning("Signals are logged, but not enough time has passed to calculate 7D / 30D / 90D returns.")
        else:
            st.dataframe(summary, use_container_width=True, hide_index=True)

        st.markdown("### Performance by Layer")
        horizon = st.selectbox("Layer performance horizon", ["7D", "30D", "90D"], index=1)
        layer_perf = layer_performance_summary(history, horizon=horizon)
        if layer_perf.empty:
            st.info(f"No {horizon} layer performance yet.")
        else:
            st.dataframe(layer_perf, use_container_width=True, hide_index=True)
            st.bar_chart(layer_perf.set_index("Layer")["Avg_Return"])

        st.markdown("### Performance by Signal Type")
        col = f"Return {horizon} %"
        valid = history[pd.notna(history[col])].copy()
        if valid.empty:
            st.info(f"No {horizon} signal performance yet.")
        else:
            signal_perf = valid.groupby("Signal", as_index=False).agg(
                Count=("Ticker", "count"),
                Avg_Return=(col, "mean"),
                Win_Rate=(col, lambda x: (x > 0).mean() * 100)
            )
            signal_perf["Avg_Return"] = signal_perf["Avg_Return"].round(2)
            signal_perf["Win_Rate"] = signal_perf["Win_Rate"].round(1)
            st.dataframe(signal_perf, use_container_width=True, hide_index=True)

        st.markdown("### Ticker Mapping")
        mapping_df = pd.DataFrame([
            {"Internal Ticker": k, "Yahoo Finance Ticker": v}
            for k, v in YAHOO_TICKER_MAP.items()
        ])
        st.dataframe(mapping_df, use_container_width=True, hide_index=True)
