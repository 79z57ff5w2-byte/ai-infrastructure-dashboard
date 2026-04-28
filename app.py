
import streamlit as st
import pandas as pd
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import random

st.set_page_config(
    page_title="AI Portfolio Decision Engine + Adjustable Backtest",
    page_icon="⚡",
    layout="wide"
)

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

SIGNAL_QUERIES = {
    "Energy": ["AI data center power demand", "AI data center nuclear power deal"],
    "Data Centers": ["AI data center expansion", "hyperscale data center AI"],
    "Compute": ["NVIDIA AI chip demand", "AI GPU supply shortage"],
    "Data/Models": ["foundation model training data AI", "OpenAI Anthropic Google DeepMind model"],
    "Platforms/Apps": ["Microsoft Copilot AI revenue", "Amazon AWS AI demand"],
    "Crypto AI Pivot": ["bitcoin miner AI data center pivot", "crypto miner AI HPC hosting"]
}

def classify_holding(company, ticker):
    text = f"{company} {ticker}".lower()
    keyword_map = {
        "Energy": ["constellation", "nextera", "duke", "southern", "vistra", "ge vernova", "cameco", "uranium", "woodside", "bhp", "freeport", "southern copper", "power", "nuclear", "electricity", "grid", "energy"],
        "Data Centers": ["equinix", "digital realty", "iron mountain", "coreweave", "vertiv", "schneider", "eaton", "super micro", "dell", "data center", "datacenter", "cooling", "hpc"],
        "Compute": ["nvidia", "amd", "broadcom", "asml", "tsmc", "taiwan semiconductor", "intel", "qualcomm", "micron", "marvell", "applied materials", "lam research", "gpu", "chip", "semiconductor", "accelerator"],
        "Data/Models": ["snowflake", "palantir", "databricks", "meta", "alphabet", "google", "mongodb", "elastic", "cloudflare", "openai", "anthropic", "deepmind", "foundation model", "model training", "llm"],
        "Platforms/Apps": ["microsoft", "amazon", "apple", "salesforce", "adobe", "servicenow", "oracle", "ibm", "tesla", "shopify", "intuit", "sap", "accenture", "copilot", "aws", "azure", "cloud"],
        "Crypto AI Pivot": ["coinbase", "microstrategy", "strategy", "bitmine", "iren", "hut 8", "cleanspark", "riot", "marathon", "mara", "cipher", "bitcoin", "block", "galaxy", "mining", "miner", "crypto"],
    }
    for layer, keywords in keyword_map.items():
        if any(k in text for k in keywords):
            return layer
    return "Diversification"

def layer_score(layer):
    return LAYER_IMPORTANCE.get(layer, 30)

def signal_category(title, summary=""):
    text = f"{title} {summary}".lower()
    structural_keywords = ["multi-year", "billion", "$", "capex", "capital expenditure", "power purchase", "ppa", "nuclear", "grid", "megawatt", "gigawatt", "mw", "gw", "data center", "datacenter", "contract", "deal", "supply agreement", "partnership", "buildout", "expansion", "capacity", "plant", "facility"]
    tactical_keywords = ["earnings", "guidance", "forecast", "quarter", "sales", "revenue", "margin", "demand", "launch", "product", "analyst", "upgrade", "downgrade"]
    noise_keywords = ["could", "may", "might", "opinion", "rumor", "rumour", "hype", "says", "why", "how", "what", "top", "best", "stock to watch"]
    structural_hits = sum(1 for k in structural_keywords if k in text)
    tactical_hits = sum(1 for k in tactical_keywords if k in text)
    noise_hits = sum(1 for k in noise_keywords if k in text)
    if structural_hits >= 2:
        return "Structural"
    if structural_hits >= 1 and tactical_hits >= 1:
        return "Structural"
    if tactical_hits >= 1 and noise_hits <= 1:
        return "Tactical"
    return "Noise"

def raw_signal_score(title, summary=""):
    text = f"{title} {summary}".lower()
    score = 20
    high_keywords = ["capex", "capital expenditure", "data center", "datacenter", "power", "nuclear", "gpu", "chip", "semiconductor", "supply", "shortage", "contract", "deal", "partnership", "expansion", "demand", "electricity", "grid", "cloud", "ai infrastructure", "hpc"]
    very_high_keywords = ["billion", "$", "megawatt", "mw", "gigawatt", "gw", "multi-year", "nvidia", "tsmc", "microsoft", "amazon", "alphabet", "constellation", "coreweave", "hyperscaler"]
    bearish_keywords = ["delay", "cancel", "slowdown", "shortfall", "restriction", "export control", "supply constraint", "margin pressure", "overcapacity"]
    for word in high_keywords:
        if word in text:
            score += 5
    for word in very_high_keywords:
        if word in text:
            score += 8
    for word in bearish_keywords:
        if word in text:
            score += 6
    return min(score, 100)

def filtered_signal_score(title, summary=""):
    base = raw_signal_score(title, summary)
    category = signal_category(title, summary)
    if category == "Structural":
        return min(base + 20, 100)
    if category == "Tactical":
        return min(base + 5, 85)
    return max(base - 25, 0)

def signal_sentiment(title, summary=""):
    text = f"{title} {summary}".lower()
    bearish = ["delay", "cancel", "slowdown", "restriction", "export control", "shortfall", "power shortage", "constraint"]
    bullish = ["deal", "expansion", "demand", "growth", "partnership", "contract", "investment", "capex", "buildout", "agreement"]
    if any(w in text for w in bearish):
        return "Bearish / constraint"
    if any(w in text for w in bullish):
        return "Bullish"
    return "Neutral"

def signal_market_read(title, layer, category):
    if category == "Noise":
        return "Likely headline noise. Do not act unless confirmed by stronger signals."
    reads = {
        "Energy": "AI demand may be moving from compute scarcity to power scarcity.",
        "Data Centers": "Physical infrastructure and cooling capacity may be becoming more valuable.",
        "Compute": "Chip and accelerator demand remains the core near-term AI capex driver.",
        "Data/Models": "Model scaling and enterprise data demand may support the data/model layer.",
        "Platforms/Apps": "Platform winners may be converting infrastructure spend into user-facing revenue.",
        "Crypto AI Pivot": "Crypto miners may gain AI/HPC optionality where power and sites are valuable."
    }
    return reads.get(layer, "General AI ecosystem signal.")

@st.cache_data(ttl=1800)
def fetch_google_news_rss(query, max_items=5):
    encoded = urllib.parse.quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-AU&gl=AU&ceid=AU:en"
    items = []
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
            pub_date = item.findtext("pubDate", default="")
            source = ""
            source_el = item.find("source")
            if source_el is not None and source_el.text:
                source = source_el.text
            if title:
                items.append({"Query": query, "Title": title, "Source": source, "Published": pub_date, "Link": link})
    except Exception:
        return []
    return items

def fetch_live_signals():
    rows = []
    for layer, queries in SIGNAL_QUERIES.items():
        for query in queries:
            for item in fetch_google_news_rss(query, max_items=3):
                item_layer = classify_holding(item["Title"], "")
                if item_layer == "Diversification":
                    item_layer = layer
                category = signal_category(item["Title"])
                score = filtered_signal_score(item["Title"])
                rows.append({
                    "AI Layer": item_layer,
                    "Signal Category": category,
                    "Signal Score": score,
                    "Sentiment": signal_sentiment(item["Title"]),
                    "Title": item["Title"],
                    "Source": item["Source"],
                    "Published": item["Published"],
                    "Query": item["Query"],
                    "Market Read": signal_market_read(item["Title"], item_layer, category),
                    "Link": item["Link"]
                })
    if not rows:
        return pd.DataFrame(columns=["AI Layer", "Signal Category", "Signal Score", "Sentiment", "Title", "Source", "Published", "Query", "Market Read", "Link"])
    df = pd.DataFrame(rows).drop_duplicates(subset=["Title"])
    return df.sort_values(["Signal Category", "Signal Score"], ascending=[True, False])

def live_layer_boosts(signals, include_tactical=True):
    boosts = {layer: 0 for layer in LAYERS}
    if signals.empty:
        return boosts
    usable = signals[signals["Signal Category"] == "Structural"].copy()
    if include_tactical:
        usable = pd.concat([usable, signals[signals["Signal Category"] == "Tactical"]])
    for layer in LAYERS:
        layer_df = usable[usable["AI Layer"] == layer]
        if layer_df.empty:
            continue
        structural_count = len(layer_df[layer_df["Signal Category"] == "Structural"])
        tactical_count = len(layer_df[layer_df["Signal Category"] == "Tactical"])
        avg_score = layer_df["Signal Score"].mean()
        boosts[layer] = min(round((avg_score / 12) + structural_count * 5 + tactical_count * 2, 1), 30)
    return boosts

def calculate_holdings_exposures(holdings, signal_boosts=None):
    if signal_boosts is None:
        signal_boosts = {layer: 0 for layer in LAYERS}
    h = holdings.copy()
    h["Weight"] = pd.to_numeric(h["Weight"], errors="coerce").fillna(0)
    h["AI Layer"] = h.apply(lambda r: classify_holding(str(r["Company"]), str(r["Holding Ticker"])), axis=1)
    h["Layer Score"] = h["AI Layer"].apply(lambda layer: min(layer_score(layer) + signal_boosts.get(layer, 0), 100))
    h["Weighted AI Score"] = h["Weight"] * h["Layer Score"] / 100
    exposures = h.pivot_table(index="ETF", columns="AI Layer", values="Weight", aggfunc="sum", fill_value=0).reset_index()
    for layer in LAYERS:
        if layer not in exposures.columns:
            exposures[layer] = 0.0
    scores = h.groupby("ETF")["Weighted AI Score"].sum().reset_index().rename(columns={"Weighted AI Score": "AI Exposure Score"})
    total_weight = h.groupby("ETF")["Weight"].sum().reset_index().rename(columns={"Weight": "Mapped Holdings Weight"})
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
    grouped["AI Layer"] = grouped.apply(lambda r: classify_holding(str(r["Company"]), str(r["Holding Ticker"])), axis=1)
    grouped["Overlap Flag"] = grouped.apply(lambda r: "High overlap" if r["ETF_Count"] >= 3 else ("Moderate overlap" if r["ETF_Count"] == 2 else "Single ETF"), axis=1)
    return grouped.sort_values("Portfolio_Exposure", ascending=False)

def concentration_warnings(overlap_df):
    warnings = []
    if overlap_df.empty:
        return warnings
    top = overlap_df.iloc[0]
    if top["Portfolio_Exposure"] >= 8:
        warnings.append(f"High single-company concentration: {top['Company']} is {top['Portfolio_Exposure']:.1f}% of mapped portfolio exposure.")
    nvda = overlap_df[overlap_df["Holding Ticker"].str.upper() == "NVDA"]
    if not nvda.empty and nvda.iloc[0]["Portfolio_Exposure"] >= 5:
        warnings.append(f"NVIDIA stack risk: NVDA appears across {int(nvda.iloc[0]['ETF_Count'])} ETFs and contributes {nvda.iloc[0]['Portfolio_Exposure']:.1f}% of mapped portfolio exposure.")
    crypto = overlap_df[overlap_df["AI Layer"] == "Crypto AI Pivot"]["Portfolio_Exposure"].sum()
    if crypto >= 2:
        warnings.append(f"Crypto AI pivot exposure: crypto miners/platforms contribute {crypto:.1f}% of mapped portfolio exposure. This is high-upside but higher-risk optionality.")
    compute = overlap_df[overlap_df["AI Layer"] == "Compute"]["Portfolio_Exposure"].sum()
    energy = overlap_df[overlap_df["AI Layer"] == "Energy"]["Portfolio_Exposure"].sum()
    if compute > energy * 3 and compute > 5:
        warnings.append("Compute-heavy imbalance: compute exposure is much larger than energy exposure, which may miss the AI power bottleneck thesis.")
    return warnings

def company_importance_rank(company, ticker, layer, signal_boosts=None):
    if signal_boosts is None:
        signal_boosts = {layer: 0 for layer in LAYERS}
    name = f"{company} {ticker}".lower()
    base = LAYER_IMPORTANCE.get(layer, 30)
    live_boost = signal_boosts.get(layer, 0)
    boosts = {
        "nvidia": 25, "tsmc": 24, "asml": 23, "broadcom": 20,
        "microsoft": 19, "amazon": 17, "alphabet": 17, "constellation": 18,
        "nextera": 15, "equinix": 16, "digital realty": 15, "vertiv": 20,
        "cameco": 13, "ge vernova": 14, "palantir": 12, "snowflake": 10,
        "meta": 12, "coinbase": 8, "strategy": 7, "bitmine": 7, "iren": 8,
        "hut 8": 7, "cleanspark": 7, "riot": 7, "marathon": 7, "mara": 7
    }
    boost = 0
    for key, value in boosts.items():
        if key in name:
            boost = max(boost, value)
    return min(base + boost + live_boost, 100)

def build_company_gap_engine(overlap_df, signal_boosts=None):
    if signal_boosts is None:
        signal_boosts = {layer: 0 for layer in LAYERS}
    critical_companies = pd.DataFrame([
        ["NVDA", "NVIDIA", "Compute"], ["TSM", "TSMC", "Compute"], ["ASML", "ASML", "Compute"],
        ["AVGO", "Broadcom", "Compute"], ["AMD", "AMD", "Compute"], ["AMAT", "Applied Materials", "Compute"],
        ["MSFT", "Microsoft", "Platforms/Apps"], ["AMZN", "Amazon", "Platforms/Apps"],
        ["GOOGL", "Alphabet", "Data/Models"], ["META", "Meta Platforms", "Data/Models"],
        ["PLTR", "Palantir Technologies", "Data/Models"], ["SNOW", "Snowflake", "Data/Models"],
        ["CEG", "Constellation Energy", "Energy"], ["NEE", "NextEra Energy", "Energy"],
        ["GEV", "GE Vernova", "Energy"], ["CCO", "Cameco Corporation", "Energy"],
        ["VRT", "Vertiv", "Data Centers"], ["EQIX", "Equinix", "Data Centers"],
        ["DLR", "Digital Realty", "Data Centers"], ["ETN", "Eaton", "Data Centers"],
        ["IREN", "IREN Ltd", "Crypto AI Pivot"], ["HUT", "Hut 8 Corp", "Crypto AI Pivot"],
        ["CLSK", "CleanSpark", "Crypto AI Pivot"], ["RIOT", "Riot Platforms", "Crypto AI Pivot"],
        ["MARA", "MARA Holdings", "Crypto AI Pivot"],
    ], columns=["Holding Ticker", "Company", "AI Layer"])
    gap = critical_companies.merge(overlap_df[["Holding Ticker", "Company", "Portfolio_Exposure", "ETF_Count", "ETFs"]], on=["Holding Ticker", "Company"], how="left")
    gap["Portfolio_Exposure"] = gap["Portfolio_Exposure"].fillna(0)
    gap["ETF_Count"] = gap["ETF_Count"].fillna(0).astype(int)
    gap["ETFs"] = gap["ETFs"].fillna("None")
    gap["Dynamic Importance Score"] = gap.apply(lambda r: company_importance_rank(r["Company"], r["Holding Ticker"], r["AI Layer"], signal_boosts), axis=1)
    gap["Gap Score"] = gap.apply(lambda r: max(r["Dynamic Importance Score"] - (r["Portfolio_Exposure"] * 10), 0), axis=1).round(1)
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
    matches = mapped_holdings[(mapped_holdings["Holding Ticker"] == ticker) | (mapped_holdings["Company"] == company)].copy()
    if matches.empty:
        return "No mapped ETF in starter data"
    matches = matches.sort_values("Weight", ascending=False)
    return ", ".join([f"{r['ETF']} ({r['Weight']:.1f}%)" for _, r in matches.head(3).iterrows()])

def build_decision_plan(company_gap, mapped_holdings, contribution):
    actionable = company_gap[company_gap["Company-Level Buy Signal"].str.contains("ADD|BUILD|OPTIONALITY", regex=True)].copy()
    if actionable.empty:
        return pd.DataFrame(columns=["Priority", "Action", "Company", "AI Layer", "Reason", "ETF Route", "Suggested $"])
    actionable["ETF Route"] = actionable.apply(lambda r: suggest_etf_for_company(r, mapped_holdings), axis=1)
    top = actionable.head(5).copy()
    weights = top["Gap Score"].clip(lower=0)
    top["Suggested $"] = (weights / weights.sum() * contribution).round(0) if weights.sum() else 0
    top["Priority"] = range(1, len(top) + 1)
    top["Action"] = top["Company-Level Buy Signal"]
    top["Reason"] = top.apply(lambda r: f"{r['Company']} is in {r['AI Layer']} with importance {r['Dynamic Importance Score']} and current exposure {r['Portfolio_Exposure']:.1f}%", axis=1)
    return top[["Priority", "Action", "Company", "AI Layer", "Reason", "ETF Route", "Suggested $"]]

# Backtest
def normalize_weights(weights):
    total = sum(weights.values())
    if total == 0:
        return {k: 0 for k in weights}
    return {k: v / total * 100 for k, v in weights.items()}

def simulate_monthly_returns(months, ai_cycle_strength=1.0, volatility_multiplier=1.0, seed=7):
    random.seed(seed)
    base_monthly = {
        "IVV": 0.008, "VEU": 0.006, "NDQ": 0.011, "VHY": 0.005,
        "AINF": 0.012, "SEMI": 0.014, "CRYP": 0.018, "GXAI": 0.013
    }
    vol = {
        "IVV": 0.035, "VEU": 0.030, "NDQ": 0.055, "VHY": 0.025,
        "AINF": 0.060, "SEMI": 0.075, "CRYP": 0.140, "GXAI": 0.070
    }
    rows = []
    for month in range(1, months + 1):
        regime_boost = 0.0
        if month > months * 0.35:
            regime_boost = 0.004 * ai_cycle_strength
        if month > months * 0.65:
            regime_boost = 0.006 * ai_cycle_strength
        for etf in base_monthly:
            noise = random.gauss(0, vol[etf] * volatility_multiplier)
            infra_extra = regime_boost if etf in ["AINF", "SEMI", "GXAI", "NDQ"] else 0
            crypto_extra = regime_boost * 1.2 if etf == "CRYP" else 0
            rows.append({"Month": month, "ETF": etf, "Return": base_monthly[etf] + infra_extra + crypto_extra + noise})
    return pd.DataFrame(rows)

def run_backtest(start_value, monthly_contribution, months, baseline_weights, test_weights, ai_cycle_strength, volatility_multiplier, seed):
    returns = simulate_monthly_returns(months, ai_cycle_strength, volatility_multiplier, seed)
    baseline_weights = normalize_weights(baseline_weights)
    test_weights = normalize_weights(test_weights)
    baseline_value = start_value
    test_value = start_value
    rows = []
    for month in range(1, months + 1):
        month_returns = returns[returns["Month"] == month].set_index("ETF")["Return"].to_dict()
        baseline_r = sum((baseline_weights.get(etf, 0) / 100) * month_returns.get(etf, 0) for etf in baseline_weights)
        test_r = sum((test_weights.get(etf, 0) / 100) * month_returns.get(etf, 0) for etf in test_weights)
        baseline_value = baseline_value * (1 + baseline_r) + monthly_contribution
        test_value = test_value * (1 + test_r) + monthly_contribution
        rows.append({"Month": month, "Strategy": "Baseline", "Portfolio Value": baseline_value, "Monthly Return": baseline_r})
        rows.append({"Month": month, "Strategy": "Test Portfolio", "Portfolio Value": test_value, "Monthly Return": test_r})
    return pd.DataFrame(rows)

def max_drawdown(values):
    peak = values.cummax()
    drawdown = (values - peak) / peak
    return drawdown.min()

starter_holdings = pd.DataFrame([
    ["IVV", "MSFT", "Microsoft", 7.0], ["IVV", "NVDA", "NVIDIA", 6.5], ["IVV", "AAPL", "Apple", 6.0], ["IVV", "AMZN", "Amazon", 4.0], ["IVV", "GOOGL", "Alphabet", 3.5], ["IVV", "META", "Meta Platforms", 2.5], ["IVV", "AVGO", "Broadcom", 2.0], ["IVV", "TSLA", "Tesla", 1.5], ["IVV", "JPM", "JPMorgan Chase", 1.3], ["IVV", "XOM", "Exxon Mobil", 1.2],
    ["VEU", "ASML", "ASML", 1.5], ["VEU", "TSM", "TSMC", 1.4], ["VEU", "SAP", "SAP", 1.0], ["VEU", "NESN", "Nestle", 1.0], ["VEU", "NOVO", "Novo Nordisk", 0.9], ["VEU", "TM", "Toyota Motor", 0.8], ["VEU", "SHEL", "Shell", 0.7], ["VEU", "AZN", "AstraZeneca", 0.7], ["VEU", "TCEHY", "Tencent", 0.7], ["VEU", "BHP", "BHP Group", 0.6],
    ["NDQ", "NVDA", "NVIDIA", 8.5], ["NDQ", "MSFT", "Microsoft", 7.8], ["NDQ", "AAPL", "Apple", 7.5], ["NDQ", "AMZN", "Amazon", 5.5], ["NDQ", "AVGO", "Broadcom", 4.8], ["NDQ", "META", "Meta Platforms", 4.6], ["NDQ", "GOOGL", "Alphabet", 4.5], ["NDQ", "TSLA", "Tesla", 3.0], ["NDQ", "COST", "Costco", 2.5], ["NDQ", "NFLX", "Netflix", 2.3],
    ["VHY", "BHP", "BHP Group", 10.3], ["VHY", "CBA", "Commonwealth Bank of Australia", 9.8], ["VHY", "NAB", "National Australia Bank", 6.8], ["VHY", "WDS", "Woodside Energy", 6.7], ["VHY", "WBC", "Westpac Banking", 6.0], ["VHY", "ANZ", "ANZ Group", 5.5], ["VHY", "MQG", "Macquarie Group", 3.5], ["VHY", "RIO", "Rio Tinto", 3.2], ["VHY", "TLS", "Telstra", 2.8], ["VHY", "WOW", "Woolworths", 2.5],
    ["AINF", "GEV", "GE Vernova", 5.9], ["AINF", "CCO", "Cameco Corporation", 5.4], ["AINF", "SCCO", "Southern Copper", 5.4], ["AINF", "FCX", "Freeport-McMoRan", 5.0], ["AINF", "VRT", "Vertiv", 4.8], ["AINF", "ETN", "Eaton", 4.5], ["AINF", "EQIX", "Equinix", 4.0], ["AINF", "DLR", "Digital Realty", 3.8], ["AINF", "CEG", "Constellation Energy", 3.6], ["AINF", "NEE", "NextEra Energy", 3.3],
    ["SEMI", "NVDA", "NVIDIA", 12.0], ["SEMI", "TSM", "TSMC", 10.0], ["SEMI", "ASML", "ASML", 9.0], ["SEMI", "AVGO", "Broadcom", 8.0], ["SEMI", "AMD", "AMD", 6.0], ["SEMI", "AMAT", "Applied Materials", 5.0], ["SEMI", "LRCX", "Lam Research", 4.5], ["SEMI", "MU", "Micron Technology", 4.0], ["SEMI", "QCOM", "Qualcomm", 3.5], ["SEMI", "INTC", "Intel", 3.0],
    ["CRYP", "BMNR", "BitMine Immersion Technologies", 10.4], ["CRYP", "MSTR", "Strategy Inc", 9.8], ["CRYP", "IREN", "IREN Ltd", 9.7], ["CRYP", "HUT", "Hut 8 Corp", 5.1], ["CRYP", "COIN", "Coinbase Global", 5.0], ["CRYP", "CLSK", "CleanSpark", 4.5], ["CRYP", "RIOT", "Riot Platforms", 4.0], ["CRYP", "MARA", "MARA Holdings", 4.0], ["CRYP", "CIFR", "Cipher Mining", 3.6], ["CRYP", "GLXY", "Galaxy Digital", 3.2],
    ["GXAI", "NVDA", "NVIDIA", 8.0], ["GXAI", "MSFT", "Microsoft", 7.0], ["GXAI", "GOOGL", "Alphabet", 6.0], ["GXAI", "META", "Meta Platforms", 5.0], ["GXAI", "PLTR", "Palantir Technologies", 4.5], ["GXAI", "SNOW", "Snowflake", 4.0], ["GXAI", "ADBE", "Adobe", 3.5], ["GXAI", "NOW", "ServiceNow", 3.0], ["GXAI", "CRM", "Salesforce", 3.0], ["GXAI", "AMZN", "Amazon", 3.0],
], columns=["ETF", "Holding Ticker", "Company", "Weight"])

st.title("⚡ AI Portfolio Decision Engine")
st.caption("Now with adjustable backtest weights.")

tabs = st.tabs([
    "Signal Filtering Engine", "Decision Engine", "Backtest Engine",
    "Dynamic Importance Ranking", "Company Gap Engine", "Overlap Engine",
    "ETF Optimizer", "Holdings Engine", "Upload Official Holdings", "Methodology"
])

with tabs[8]:
    st.subheader("Upload Official Holdings")
    uploaded = st.file_uploader("Upload a CSV with columns: ETF, Holding Ticker, Company, Weight", type=["csv"])
    st.download_button("Download starter holdings template", starter_holdings.to_csv(index=False).encode("utf-8"), file_name="holdings_template.csv", mime="text/csv")

if "uploaded" in locals() and uploaded:
    try:
        holdings = pd.read_csv(uploaded)
        required_cols = {"ETF", "Holding Ticker", "Company", "Weight"}
        if not required_cols.issubset(set(holdings.columns)):
            st.error("CSV must include columns: ETF, Holding Ticker, Company, Weight")
            holdings = starter_holdings.copy()
        else:
            st.success("Official holdings uploaded successfully.")
    except Exception as e:
        st.error(f"Could not read uploaded file: {e}")
        holdings = starter_holdings.copy()
else:
    holdings = starter_holdings.copy()

with st.sidebar:
    st.header("Portfolio Inputs")
    default_weights = {"IVV": 22.0, "VEU": 22.0, "NDQ": 22.0, "VHY": 24.0, "AINF": 4.0, "SEMI": 4.0, "CRYP": 2.0, "GXAI": 0.0}
    weights = {}
    available_etfs = sorted(holdings["ETF"].unique().tolist())
    for etf in available_etfs:
        weights[etf] = st.number_input(f"{etf} weight %", min_value=0.0, max_value=100.0, value=float(default_weights.get(etf, 0.0)), step=1.0, key=f"shared_weight_{etf}")
    contribution = st.number_input("Next contribution amount ($)", min_value=0, value=3000, step=500)
    target_mode = st.selectbox("Target mode", ["Balanced AI Growth", "AI Infrastructure Tilt", "Semiconductor Heavy", "Crypto AI Pivot"])
    use_live_signals = st.toggle("Use live signals", value=True)
    include_tactical = st.toggle("Allow tactical signals into boosts", value=True)

signals = fetch_live_signals() if use_live_signals else pd.DataFrame(columns=["AI Layer", "Signal Category", "Signal Score", "Sentiment", "Title", "Source", "Published", "Query", "Market Read", "Link"])
signal_boosts = live_layer_boosts(signals, include_tactical=include_tactical) if use_live_signals else {layer: 0 for layer in LAYERS}
mapped_holdings, etf_exposures = calculate_holdings_exposures(holdings, signal_boosts=signal_boosts)

target_presets = {
    "Balanced AI Growth": {"Energy": 5, "Data Centers": 5, "Compute": 12, "Data/Models": 8, "Platforms/Apps": 14, "Crypto AI Pivot": 1},
    "AI Infrastructure Tilt": {"Energy": 8, "Data Centers": 8, "Compute": 15, "Data/Models": 4, "Platforms/Apps": 8, "Crypto AI Pivot": 1},
    "Semiconductor Heavy": {"Energy": 2, "Data Centers": 2, "Compute": 25, "Data/Models": 3, "Platforms/Apps": 8, "Crypto AI Pivot": 1},
    "Crypto AI Pivot": {"Energy": 3, "Data Centers": 4, "Compute": 10, "Data/Models": 4, "Platforms/Apps": 8, "Crypto AI Pivot": 5},
}
target = target_presets[target_mode]
current_profile = portfolio_exposure(weights, etf_exposures)
overlap = calculate_overlap(mapped_holdings, weights)
company_gap = build_company_gap_engine(overlap, signal_boosts=signal_boosts)
decision_plan = build_decision_plan(company_gap, mapped_holdings, contribution)

with tabs[0]:
    st.subheader("Signal Filtering Engine")
    if not use_live_signals:
        st.info("Live signals are disabled.")
    elif signals.empty:
        st.warning("No live signals could be fetched. Running base model.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Signals fetched", len(signals))
        c2.metric("Structural", len(signals[signals["Signal Category"] == "Structural"]))
        c3.metric("Tactical", len(signals[signals["Signal Category"] == "Tactical"]))
        c4.metric("Noise", len(signals[signals["Signal Category"] == "Noise"]))
        boost_df = pd.DataFrame([{"AI Layer": k, "Live Importance Boost": v} for k, v in signal_boosts.items()])
        st.markdown("### Live Importance Boosts")
        st.dataframe(boost_df.sort_values("Live Importance Boost", ascending=False), use_container_width=True, hide_index=True)
        for cat in ["Structural", "Tactical", "Noise"]:
            st.markdown(f"### {cat} Signals")
            df = signals[signals["Signal Category"] == cat].sort_values("Signal Score", ascending=False)
            st.dataframe(df[["AI Layer", "Signal Score", "Sentiment", "Title", "Source", "Published", "Market Read", "Link"]], use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("Full Decision Engine")
    cols = st.columns(4)
    cols[0].metric("Portfolio AI Score", current_profile["AI Exposure Score"])
    cols[1].metric("Compute", current_profile["Compute"])
    cols[2].metric("Energy", current_profile["Energy"])
    cols[3].metric("Data Centers", current_profile["Data Centers"])
    cols2 = st.columns(4)
    cols2[0].metric("Data/Models", current_profile["Data/Models"])
    cols2[1].metric("Platforms/Apps", current_profile["Platforms/Apps"])
    cols2[2].metric("Crypto AI Pivot", current_profile["Crypto AI Pivot"])
    cols2[3].metric("Diversification", current_profile["Diversification"])
    st.markdown("### Key Warnings")
    warnings = concentration_warnings(overlap)
    if warnings:
        for warning in warnings:
            st.warning(warning)
    else:
        st.success("No major concentration warnings detected.")
    st.markdown("### Recommended Next-Buy Action Plan")
    st.dataframe(decision_plan, use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("Adjustable Backtest Engine")
    st.write("Compare any baseline portfolio against any test portfolio using adjustable ETF weights.")

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        start_value = st.number_input("Starting portfolio value ($)", min_value=0, value=110000, step=5000)
    with b2:
        monthly_contribution = st.number_input("Monthly contribution ($)", min_value=0, value=2000, step=500)
    with b3:
        months = st.slider("Backtest length (months)", 12, 120, 60)
    with b4:
        random_seed = st.number_input("Scenario seed", min_value=1, value=7, step=1)

    s1, s2 = st.columns(2)
    with s1:
        ai_cycle_strength = st.slider("AI cycle strength", 0.0, 3.0, 1.0, 0.1)
    with s2:
        volatility_multiplier = st.slider("Volatility multiplier", 0.25, 3.0, 1.0, 0.05)

    st.markdown("### Baseline Portfolio Weights")
    baseline_defaults = {"IVV": 22, "VEU": 22, "NDQ": 22, "VHY": 24, "AINF": 4, "SEMI": 4, "CRYP": 2, "GXAI": 0}
    baseline_weights = {}
    cols = st.columns(4)
    for i, etf in enumerate(["IVV", "VEU", "NDQ", "VHY", "AINF", "SEMI", "CRYP", "GXAI"]):
        with cols[i % 4]:
            baseline_weights[etf] = st.number_input(f"Baseline {etf} %", min_value=0.0, max_value=100.0, value=float(baseline_defaults.get(etf, 0)), step=1.0, key=f"bt_base_{etf}")

    st.markdown("### Test Portfolio Weights")
    preset = st.selectbox("Load test preset", ["Custom / current", "AI Infrastructure Tilt", "Semiconductor Heavy", "Crypto AI Pivot", "Global Core + AINF"])
    presets = {
        "Custom / current": {"IVV": 22, "VEU": 22, "NDQ": 22, "VHY": 24, "AINF": 4, "SEMI": 4, "CRYP": 2, "GXAI": 0},
        "AI Infrastructure Tilt": {"IVV": 20, "VEU": 24, "NDQ": 18, "VHY": 20, "AINF": 10, "SEMI": 5, "CRYP": 2, "GXAI": 1},
        "Semiconductor Heavy": {"IVV": 20, "VEU": 22, "NDQ": 20, "VHY": 18, "AINF": 5, "SEMI": 12, "CRYP": 2, "GXAI": 1},
        "Crypto AI Pivot": {"IVV": 20, "VEU": 22, "NDQ": 20, "VHY": 20, "AINF": 6, "SEMI": 5, "CRYP": 5, "GXAI": 2},
        "Global Core + AINF": {"IVV": 20, "VEU": 35, "NDQ": 15, "VHY": 15, "AINF": 10, "SEMI": 3, "CRYP": 1, "GXAI": 1},
    }
    test_defaults = presets[preset]
    test_weights = {}
    cols = st.columns(4)
    for i, etf in enumerate(["IVV", "VEU", "NDQ", "VHY", "AINF", "SEMI", "CRYP", "GXAI"]):
        with cols[i % 4]:
            test_weights[etf] = st.number_input(f"Test {etf} %", min_value=0.0, max_value=100.0, value=float(test_defaults.get(etf, 0)), step=1.0, key=f"bt_test_{preset}_{etf}")

    baseline_total = sum(baseline_weights.values())
    test_total = sum(test_weights.values())
    if abs(baseline_total - 100) > 0.1:
        st.warning(f"Baseline weights total {baseline_total:.1f}%. They will be normalized.")
    if abs(test_total - 100) > 0.1:
        st.warning(f"Test weights total {test_total:.1f}%. They will be normalized.")

    bt = run_backtest(start_value, monthly_contribution, months, baseline_weights, test_weights, ai_cycle_strength, volatility_multiplier, int(random_seed))
    st.line_chart(bt.pivot(index="Month", columns="Strategy", values="Portfolio Value"))

    final = bt.groupby("Strategy").tail(1)[["Strategy", "Portfolio Value"]].copy()
    final["Portfolio Value"] = final["Portfolio Value"].round(0)
    # Add drawdown
    dd_rows = []
    for strategy in bt["Strategy"].unique():
        vals = bt[bt["Strategy"] == strategy].sort_values("Month")["Portfolio Value"]
        dd_rows.append({"Strategy": strategy, "Max Drawdown": round(max_drawdown(vals) * 100, 1)})
    dd_df = pd.DataFrame(dd_rows)
    final = final.merge(dd_df, on="Strategy", how="left")
    st.dataframe(final, use_container_width=True, hide_index=True)

    static_final = float(final[final["Strategy"] == "Baseline"]["Portfolio Value"].iloc[0])
    test_final = float(final[final["Strategy"] == "Test Portfolio"]["Portfolio Value"].iloc[0])
    delta = test_final - static_final
    if delta > 0:
        st.success(f"In this scenario, the test portfolio ends ${delta:,.0f} ahead.")
    else:
        st.warning(f"In this scenario, the test portfolio ends ${abs(delta):,.0f} behind.")

    st.caption("This is synthetic scenario testing, not true historical performance.")

with tabs[3]:
    st.subheader("Dynamic Importance Ranking")
    ranking = company_gap.sort_values("Dynamic Importance Score", ascending=False)
    st.dataframe(ranking[["Holding Ticker", "Company", "AI Layer", "Dynamic Importance Score", "Portfolio_Exposure", "ETF_Count", "ETFs", "Company-Level Buy Signal"]], use_container_width=True, hide_index=True)
    st.bar_chart(ranking.set_index("Company")[["Dynamic Importance Score", "Portfolio_Exposure"]].head(15))

with tabs[4]:
    st.subheader("Company Gap Engine")
    gap_view = company_gap.copy()
    gap_view["ETF Route"] = gap_view.apply(lambda r: suggest_etf_for_company(r, mapped_holdings), axis=1)
    st.dataframe(gap_view[["Holding Ticker", "Company", "AI Layer", "Dynamic Importance Score", "Portfolio_Exposure", "Gap Score", "Company-Level Buy Signal", "ETF Route"]], use_container_width=True, hide_index=True)
    st.bar_chart(gap_view.head(15).set_index("Company")["Gap Score"])

with tabs[5]:
    st.subheader("Overlap Engine")
    st.dataframe(overlap[["Holding Ticker", "Company", "AI Layer", "Portfolio_Exposure", "ETF_Count", "ETFs", "Overlap Flag"]], use_container_width=True, hide_index=True)
    st.bar_chart(overlap.head(10).set_index("Company")["Portfolio_Exposure"])

with tabs[6]:
    st.subheader("ETF Optimizer")
    gaps = {layer: round(target[layer] - current_profile.get(layer, 0), 1) for layer in target}
    st.dataframe(pd.DataFrame([{"Layer": k, "Current": current_profile[k], "Target": v, "Gap": gaps[k]} for k, v in target.items()]), use_container_width=True, hide_index=True)
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
    st.dataframe(ranked[["ETF", "AI Exposure Score", "Energy", "Data Centers", "Compute", "Data/Models", "Platforms/Apps", "Crypto AI Pivot", "Optimizer Score"]], use_container_width=True, hide_index=True)

with tabs[7]:
    st.subheader("Holdings Engine")
    etf_filter = st.multiselect("ETF filter", sorted(mapped_holdings["ETF"].unique()), default=sorted(mapped_holdings["ETF"].unique()))
    layer_filter = st.multiselect("AI layer filter", sorted(mapped_holdings["AI Layer"].unique()), default=sorted(mapped_holdings["AI Layer"].unique()))
    view = mapped_holdings[mapped_holdings["ETF"].isin(etf_filter) & mapped_holdings["AI Layer"].isin(layer_filter)].sort_values(["ETF", "Weight"], ascending=[True, False])
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.markdown("### ETF Exposure Table")
    st.dataframe(etf_exposures.sort_values("AI Exposure Score", ascending=False), use_container_width=True, hide_index=True)

with tabs[9]:
    st.subheader("Methodology")
    st.markdown("""
### Adjustable Backtest

The backtest now allows editable weights for both:

- Baseline portfolio
- Test portfolio

You can also adjust:

- AI cycle strength
- Volatility multiplier
- Backtest length
- Monthly contributions
- Starting value

This is still synthetic scenario testing, not true historical performance. It helps test whether portfolio logic is robust under different assumptions.

### Signal Filtering

Signals are classified as structural, tactical or noise. Structural signals are strongest and most relevant to the decision engine.

### Important

This app is for research and education only. It is not personal financial advice.
""")
