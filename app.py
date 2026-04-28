
import streamlit as st
import pandas as pd
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

st.set_page_config(page_title="AI Portfolio Engine v7", layout="wide")

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
    ["AINF","GEV","GE Vernova",5.9],
    ["AINF","CCO","Cameco",5.4],
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

SIGNAL_QUERIES = {
    "Energy": [
        "AI data center power demand",
        "AI data center nuclear power deal",
        "hyperscaler power purchase agreement data center",
        "AI electricity grid bottleneck"
    ],
    "Data Centers": [
        "AI data center expansion",
        "hyperscale data center AI",
        "data center capacity AI cloud",
        "AI data center cooling power"
    ],
    "Compute": [
        "NVIDIA AI chip demand",
        "AI GPU supply shortage",
        "TSMC AI chips capex",
        "AI semiconductor capex"
    ],
    "Data/Models": [
        "OpenAI Anthropic Google DeepMind model",
        "enterprise AI data platform demand",
        "AI model training compute demand",
        "foundation model training data AI"
    ],
    "Platforms": [
        "Microsoft Copilot AI revenue",
        "Amazon AWS AI demand",
        "Google Cloud AI demand",
        "enterprise AI adoption"
    ],
    "Crypto AI Pivot": [
        "bitcoin miner AI data center pivot",
        "crypto miner AI HPC hosting",
        "IREN AI cloud data center",
        "Hut 8 AI data center"
    ]
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

def classify_signal_layer(text):
    t = text.lower()
    if any(k in t for k in ["power", "electricity", "grid", "nuclear", "energy", "constellation", "nextera"]):
        return "Energy"
    if any(k in t for k in ["data center", "datacenter", "cooling", "hpc", "equinix", "vertiv", "digital realty"]):
        return "Data Centers"
    if any(k in t for k in ["nvidia", "gpu", "chip", "semiconductor", "tsmc", "asml", "broadcom"]):
        return "Compute"
    if any(k in t for k in ["openai", "anthropic", "deepmind", "model", "llm", "palantir", "snowflake"]):
        return "Data/Models"
    if any(k in t for k in ["microsoft", "copilot", "aws", "amazon", "google cloud", "enterprise ai", "cloud"]):
        return "Platforms"
    if any(k in t for k in ["bitcoin miner", "crypto miner", "iren", "hut 8", "cleanspark", "riot", "mara"]):
        return "Crypto AI Pivot"
    return "General"

def signal_category(title):
    text = title.lower()

    structural_keywords = [
        "billion", "$", "capex", "capital expenditure", "multi-year", "contract",
        "deal", "agreement", "partnership", "power purchase", "ppa", "nuclear",
        "megawatt", "mw", "gigawatt", "gw", "data center", "datacenter",
        "expansion", "capacity", "facility", "buildout"
    ]

    tactical_keywords = [
        "earnings", "guidance", "revenue", "sales", "forecast", "quarter",
        "demand", "launch", "product", "upgrade", "downgrade"
    ]

    noise_keywords = [
        "could", "may", "might", "opinion", "top", "best", "why", "how",
        "stock to watch", "rumor", "rumour"
    ]

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

def score_signal(title):
    text = title.lower()
    score = 25

    boost_words = [
        "billion", "$", "capex", "data center", "datacenter", "power", "nuclear",
        "gpu", "chip", "semiconductor", "contract", "deal", "agreement",
        "partnership", "expansion", "capacity", "shortage", "supply", "demand"
    ]

    strong_words = [
        "multi-year", "gigawatt", "gw", "megawatt", "mw", "nvidia", "tsmc",
        "microsoft", "amazon", "google", "constellation", "coreweave", "hyperscaler"
    ]

    for word in boost_words:
        if word in text:
            score += 5

    for word in strong_words:
        if word in text:
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
        return "Likely noise — do not act unless confirmed by stronger signals."
    reads = {
        "Energy": "Power and grid constraints may be becoming more important to AI buildout.",
        "Data Centers": "Physical AI infrastructure and cooling capacity may be gaining importance.",
        "Compute": "GPU/chip demand remains central to AI capex.",
        "Data/Models": "Model and data-platform demand may be strengthening.",
        "Platforms": "Cloud/platform players may be converting AI capex into revenue.",
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
                rows.append({
                    "Query": query,
                    "Title": title,
                    "Source": source,
                    "Published": published,
                    "Link": link
                })

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

    signals = pd.DataFrame(rows).drop_duplicates(subset=["Title"])
    return signals.sort_values(["Signal Category","Signal Score"], ascending=[True, False])

def calculate_live_boosts(signals, include_tactical=True):
    boosts = {layer: 0.0 for layer in ["Compute","Energy","Data Centers","Platforms","Data/Models","Crypto AI Pivot"]}

    if signals.empty:
        return boosts

    usable = signals[signals["Signal Category"] == "Structural"].copy()
    if include_tactical:
        usable = pd.concat([usable, signals[signals["Signal Category"] == "Tactical"]])

    for layer in boosts.keys():
        layer_df = usable[usable["AI Layer"] == layer]
        if layer_df.empty:
            continue

        structural_count = len(layer_df[layer_df["Signal Category"] == "Structural"])
        tactical_count = len(layer_df[layer_df["Signal Category"] == "Tactical"])
        avg_score = layer_df["Signal Score"].mean()

        boosts[layer] = min(round((avg_score / 100) * 0.20 + structural_count * 0.08 + tactical_count * 0.03, 2), 0.45)

    return boosts

def importance_multiplier(category, preset_name, live_boosts=None):
    base = LAYER_PRESETS[preset_name].get(category, 0.70)
    if live_boosts:
        base += live_boosts.get(category, 0.0)
    return base

def dynamic_gap_score(row, preset_name, live_boosts=None):
    exposure = row["Exposure"]
    base = row["Base Importance"]
    multiplier = importance_multiplier(row["Category"], preset_name, live_boosts)

    dynamic_importance = base * multiplier

    exposure_penalty = exposure * 14
    concentration_penalty = max(exposure - 5, 0) * 20

    score = dynamic_importance - exposure_penalty - concentration_penalty
    return max(round(score, 1), 0)

def build_dynamic_ranking(norm, preset_name, live_boosts=None):
    merged, work = get_current_exposure(norm)

    merged["Layer Multiplier"] = merged["Category"].apply(lambda c: importance_multiplier(c, preset_name, live_boosts))
    merged["Dynamic Importance"] = (merged["Base Importance"] * merged["Layer Multiplier"]).round(1)
    merged["Gap Score"] = merged.apply(lambda r: dynamic_gap_score(r, preset_name, live_boosts), axis=1)

    def signal(row):
        exposure = row["Exposure"]
        score = row["Gap Score"]
        category = row["Category"]

        if exposure > 6:
            return "LIMIT"
        if score >= 95 and exposure < 1:
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
st.title("⚡ AI Portfolio Engine v7")
st.caption("Live AI signal engine + dynamic importance ranking")

tabs = st.tabs([
    "Live Signal Engine",
    "Portfolio",
    "Overlap",
    "Gap Engine",
    "Dynamic Ranking",
    "Weighted Buy Signals"
])

with st.sidebar:
    st.header("Signal Settings")
    use_live_signals = st.toggle("Use live signals", value=True)
    include_tactical = st.toggle("Include tactical signals", value=True)
    st.caption("Structural signals carry the most weight. Tactical signals are optional.")

signals = fetch_live_signals() if use_live_signals else pd.DataFrame(columns=["AI Layer","Signal Category","Signal Score","Title","Source","Published","Market Read","Link"])
live_boosts = calculate_live_boosts(signals, include_tactical=include_tactical) if use_live_signals else {layer: 0.0 for layer in ["Compute","Energy","Data Centers","Platforms","Data/Models","Crypto AI Pivot"]}

# Live Signal Engine
with tabs[0]:
    st.subheader("Live AI Signal Engine")
    st.write("Fetches recent AI infrastructure headlines, filters noise, classifies by AI layer, and boosts dynamic importance.")

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
            st.dataframe(
                view[["AI Layer","Signal Score","Title","Source","Published","Market Read","Link"]],
                use_container_width=True,
                hide_index=True
            )

# Portfolio
with tabs[1]:
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
with tabs[2]:
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
with tabs[3]:
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
with tabs[4]:
    st.subheader("Dynamic AI Importance Ranking")
    st.write("Live signals adjust the layer multipliers if enabled.")

    preset = st.selectbox(
        "Choose AI cycle / thesis preset",
        list(LAYER_PRESETS.keys()),
        key="ranking_preset"
    )

    norm = get_weights("ranking")
    ranking = build_dynamic_ranking(norm, preset, live_boosts=live_boosts)
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
with tabs[5]:
    st.subheader("Weighted Buy Signals")
    st.write("This is the clean decision output: what to prioritise next, adjusted for your thesis, exposure, and live signals.")

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
    ranking = build_dynamic_ranking(norm, preset, live_boosts=live_boosts)
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
