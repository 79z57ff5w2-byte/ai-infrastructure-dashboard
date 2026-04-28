
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(
    page_title="AI Portfolio Decision Engine - Clean Ingestion",
    page_icon="⚡",
    layout="wide"
)

# ============================================================
# Provider pages
# ============================================================

PROVIDER_PAGES = {
    "IVV": "https://www.blackrock.com/au/products/275304/",
    "NDQ": "https://www.betashares.com.au/fund/nasdaq-100-etf/",
    "CRYP": "https://www.betashares.com.au/fund/crypto-innovators-etf/",
    "VHY": "https://www.vanguard.com.au/personal/invest-with-us/etf?portId=8210",
    "VEU": "https://investor.vanguard.com/investment-products/etfs/profile/veu",
    "AINF": "https://www.globalxetfs.com.au/funds/ainf/",
    "SEMI": "https://www.globalxetfs.com.au/funds/semi/",
    "GXAI": "https://www.globalxetfs.com.au/"
}

# ============================================================
# Starter holdings
# ============================================================

STARTER_HOLDINGS = pd.DataFrame([
    ["IVV", "MSFT", "Microsoft", 7.0],
    ["IVV", "NVDA", "NVIDIA", 6.5],
    ["IVV", "AAPL", "Apple", 6.0],
    ["IVV", "AMZN", "Amazon", 4.0],
    ["IVV", "GOOGL", "Alphabet", 3.5],
    ["IVV", "META", "Meta Platforms", 2.5],
    ["IVV", "AVGO", "Broadcom", 2.0],

    ["VEU", "ASML", "ASML", 1.5],
    ["VEU", "TSM", "TSMC", 1.4],
    ["VEU", "SAP", "SAP", 1.0],
    ["VEU", "BHP", "BHP Group", 0.6],

    ["NDQ", "NVDA", "NVIDIA", 8.5],
    ["NDQ", "MSFT", "Microsoft", 7.8],
    ["NDQ", "AAPL", "Apple", 7.5],
    ["NDQ", "AMZN", "Amazon", 5.5],
    ["NDQ", "AVGO", "Broadcom", 4.8],
    ["NDQ", "META", "Meta Platforms", 4.6],
    ["NDQ", "GOOGL", "Alphabet", 4.5],

    ["VHY", "BHP", "BHP Group", 10.3],
    ["VHY", "CBA", "Commonwealth Bank of Australia", 9.8],
    ["VHY", "WDS", "Woodside Energy", 6.7],

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

    ["CRYP", "BMNR", "BitMine Immersion Technologies", 10.4],
    ["CRYP", "MSTR", "Strategy Inc", 9.8],
    ["CRYP", "IREN", "IREN Ltd", 9.7],
    ["CRYP", "HUT", "Hut 8 Corp", 5.1],
    ["CRYP", "COIN", "Coinbase Global", 5.0],
    ["CRYP", "CLSK", "CleanSpark", 4.5],
    ["CRYP", "RIOT", "Riot Platforms", 4.0],
    ["CRYP", "MARA", "MARA Holdings", 4.0],

    ["GXAI", "NVDA", "NVIDIA", 8.0],
    ["GXAI", "MSFT", "Microsoft", 7.0],
    ["GXAI", "GOOGL", "Alphabet", 6.0],
    ["GXAI", "META", "Meta Platforms", 5.0],
    ["GXAI", "PLTR", "Palantir Technologies", 4.5],
    ["GXAI", "SNOW", "Snowflake", 4.0],
], columns=["ETF", "Holding Ticker", "Company", "Weight"])

REQUIRED_COLUMNS = ["ETF", "Holding Ticker", "Company", "Weight"]

# ============================================================
# Helpers
# ============================================================

def standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Attempts to standardise common provider/export column names."""
    df = df.copy()
    original_columns = list(df.columns)
    lower_map = {str(c).strip().lower(): c for c in df.columns}

    aliases = {
        "ETF": ["etf", "fund", "fund ticker", "fund_ticker"],
        "Holding Ticker": ["holding ticker", "ticker", "asx code", "symbol", "identifier", "holding_ticker"],
        "Company": ["company", "name", "holding name", "security name", "issuer", "description"],
        "Weight": ["weight", "weight (%)", "% weight", "portfolio weight", "market value weight", "fund weight"]
    }

    rename_map = {}
    for target, possible_names in aliases.items():
        for name in possible_names:
            if name in lower_map:
                rename_map[lower_map[name]] = target
                break

    df = df.rename(columns=rename_map)

    # If uploaded file does not contain ETF column, leave it missing so user can assign it manually.
    if "Weight" in df.columns:
        df["Weight"] = (
            df["Weight"]
            .astype(str)
            .str.replace("%", "", regex=False)
            .str.replace(",", "", regex=False)
        )
        df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce").fillna(0)

    return df

def validate_holdings(df: pd.DataFrame) -> tuple[bool, list[str]]:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    return len(missing) == 0, missing

def summarize_ingestion_result(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame([{"Metric": "Rows", "Value": 0}])

    summary = [
        {"Metric": "Rows", "Value": len(df)},
        {"Metric": "Columns", "Value": len(df.columns)}
    ]

    if "ETF" in df.columns:
        etfs = sorted(df["ETF"].dropna().astype(str).unique())
        summary.append({"Metric": "ETFs detected", "Value": len(etfs)})
        summary.append({"Metric": "ETF list", "Value": ", ".join(etfs)})

    if "Company" in df.columns:
        summary.append({"Metric": "Companies detected", "Value": df["Company"].nunique()})

    if "Weight" in df.columns:
        weights = pd.to_numeric(df["Weight"], errors="coerce").fillna(0)
        summary.append({"Metric": "Total mapped weight", "Value": round(weights.sum(), 2)})

    return pd.DataFrame(summary)

def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(uploaded_file)
    raise ValueError("Unsupported file type")

def build_template_file() -> bytes:
    output = BytesIO()
    STARTER_HOLDINGS.to_excel(output, index=False)
    return output.getvalue()

def classify_ai_layer(company: str, ticker: str) -> str:
    text = f"{company} {ticker}".lower()

    layer_keywords = {
        "Energy": ["constellation", "nextera", "ge vernova", "cameco", "woodside", "bhp", "freeport", "copper", "energy", "power", "nuclear"],
        "Data Centers": ["equinix", "digital realty", "vertiv", "eaton", "data center", "datacenter", "cooling"],
        "Compute": ["nvidia", "amd", "broadcom", "asml", "tsmc", "intel", "applied materials", "semiconductor", "gpu"],
        "Data/Models": ["palantir", "snowflake", "meta", "alphabet", "google", "databricks", "openai", "anthropic"],
        "Platforms/Apps": ["microsoft", "amazon", "apple", "salesforce", "adobe", "servicenow", "oracle", "tesla"],
        "Crypto AI Pivot": ["coinbase", "strategy", "bitmine", "iren", "hut 8", "cleanspark", "riot", "marathon", "mara", "crypto", "bitcoin"]
    }

    for layer, keywords in layer_keywords.items():
        if any(k in text for k in keywords):
            return layer

    return "Diversification"

def add_ai_layers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if {"Company", "Holding Ticker"}.issubset(df.columns):
        df["AI Layer"] = df.apply(
            lambda r: classify_ai_layer(str(r["Company"]), str(r["Holding Ticker"])),
            axis=1
        )
    return df

def calculate_etf_layer_exposure(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "AI Layer" not in df.columns or "Weight" not in df.columns:
        return pd.DataFrame()

    exposure = (
        df.pivot_table(
            index="ETF",
            columns="AI Layer",
            values="Weight",
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )

    return exposure

# ============================================================
# Session state
# ============================================================

if "holdings" not in st.session_state:
    st.session_state["holdings"] = add_ai_layers(STARTER_HOLDINGS)

if "holdings_source" not in st.session_state:
    st.session_state["holdings_source"] = "Starter sample holdings"

# ============================================================
# App
# ============================================================

st.title("⚡ AI Portfolio Decision Engine")
st.caption("Clean holdings ingestion module — stable upload, provider links, validation and AI layer mapping.")

tabs = st.tabs([
    "Holdings Ingestion",
    "Active Holdings",
    "ETF Exposure Summary",
    "Provider Pages",
    "Template / Instructions"
])

# ============================================================
# Holdings Ingestion
# ============================================================

with tabs[0]:
    st.subheader("Holdings Ingestion")

    st.info(
        "Upload CSV/XLS/XLSX files with these columns: ETF, Holding Ticker, Company, Weight. "
        "The app will also try to standardise common provider column names."
    )

    uploaded_files = st.file_uploader(
        "Upload one or more holdings files",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True
    )

    assigned_etf = st.text_input(
        "Optional: assign ETF ticker if the uploaded file does not contain an ETF column",
        value=""
    ).strip().upper()

    if uploaded_files:
        frames = []
        errors = []

        for uploaded_file in uploaded_files:
            try:
                raw_df = read_uploaded_file(uploaded_file)
                df = standardise_columns(raw_df)

                if "ETF" not in df.columns and assigned_etf:
                    df["ETF"] = assigned_etf

                valid, missing = validate_holdings(df)

                if not valid:
                    errors.append(f"{uploaded_file.name}: missing columns {missing}")
                    continue

                df = df[REQUIRED_COLUMNS].copy()
                df["ETF"] = df["ETF"].astype(str).str.upper().str.strip()
                df["Holding Ticker"] = df["Holding Ticker"].astype(str).str.upper().str.strip()
                df["Company"] = df["Company"].astype(str).str.strip()
                df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce").fillna(0)
                frames.append(df)

            except Exception as e:
                errors.append(f"{uploaded_file.name}: {e}")

        if errors:
            st.error("Some files could not be loaded:")
            for error in errors:
                st.write(f"- {error}")

        if frames:
            combined = pd.concat(frames, ignore_index=True)
            combined = add_ai_layers(combined)
            st.session_state["holdings"] = combined
            st.session_state["holdings_source"] = "Uploaded holdings files"
            st.success("Holdings loaded successfully.")

    active_holdings = st.session_state["holdings"]

    st.markdown("### Current Ingestion Summary")
    st.dataframe(
        summarize_ingestion_result(active_holdings),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Current Holdings Preview")
    st.dataframe(
        active_holdings.head(100),
        use_container_width=True,
        hide_index=True
    )

    if st.button("Clear uploaded holdings and revert to starter data"):
        st.session_state["holdings"] = add_ai_layers(STARTER_HOLDINGS)
        st.session_state["holdings_source"] = "Starter sample holdings"
        st.success("Reverted to starter holdings.")

# ============================================================
# Active Holdings
# ============================================================

with tabs[1]:
    st.subheader("Active Holdings")

    active_holdings = st.session_state["holdings"]

    st.write(f"**Source:** {st.session_state['holdings_source']}")

    st.dataframe(
        summarize_ingestion_result(active_holdings),
        use_container_width=True,
        hide_index=True
    )

    etf_filter = st.multiselect(
        "Filter by ETF",
        sorted(active_holdings["ETF"].dropna().astype(str).unique()),
        default=sorted(active_holdings["ETF"].dropna().astype(str).unique())
    )

    layer_filter = st.multiselect(
        "Filter by AI Layer",
        sorted(active_holdings["AI Layer"].dropna().astype(str).unique()),
        default=sorted(active_holdings["AI Layer"].dropna().astype(str).unique())
    )

    filtered = active_holdings[
        active_holdings["ETF"].isin(etf_filter)
        & active_holdings["AI Layer"].isin(layer_filter)
    ]

    st.dataframe(
        filtered.sort_values(["ETF", "Weight"], ascending=[True, False]),
        use_container_width=True,
        hide_index=True
    )

# ============================================================
# ETF Exposure Summary
# ============================================================

with tabs[2]:
    st.subheader("ETF Exposure Summary")

    active_holdings = st.session_state["holdings"]
    exposure = calculate_etf_layer_exposure(active_holdings)

    if exposure.empty:
        st.warning("No exposure summary available.")
    else:
        st.dataframe(exposure, use_container_width=True, hide_index=True)

        numeric_cols = [c for c in exposure.columns if c != "ETF"]
        if numeric_cols:
            st.bar_chart(exposure.set_index("ETF")[numeric_cols])

    st.caption(
        "This summary is holdings-derived. Accuracy improves as you upload complete official holdings files."
    )

# ============================================================
# Provider Pages
# ============================================================

with tabs[3]:
    st.subheader("Official Provider Pages")

    provider_df = pd.DataFrame(
        [{"ETF": etf, "Provider Page": url} for etf, url in PROVIDER_PAGES.items()]
    )

    st.dataframe(provider_df, use_container_width=True, hide_index=True)

    st.info(
        "Provider pages often change their download formats. Use these links to download official holdings, "
        "then upload the CSV/XLS/XLSX files in the Holdings Ingestion tab."
    )

# ============================================================
# Template / Instructions
# ============================================================

with tabs[4]:
    st.subheader("Template / Instructions")

    st.markdown("""
### Required columns

Your holdings file should include:

- **ETF**
- **Holding Ticker**
- **Company**
- **Weight**

### Accepted formats

- CSV
- XLS
- XLSX

### If the provider file does not include ETF

Enter the ETF ticker in the optional field on the ingestion tab before uploading.

### Why this clean module exists

This version avoids brittle auto-scraping. Provider sites change frequently, so the most stable workflow is:

1. Use the official provider page.
2. Download holdings.
3. Upload the file here.
4. Let the app standardise, validate and map AI layers.
""")

    st.download_button(
        label="Download holdings template",
        data=build_template_file(),
        file_name="holdings_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
