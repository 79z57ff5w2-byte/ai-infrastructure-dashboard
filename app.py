
import streamlit as st
import pandas as pd

st.set_page_config(page_title='AI ETF Optimizer + Overlap Engine', page_icon='⚡', layout='wide')

LAYERS = ['Energy','Data Centers','Compute','Data/Models','Platforms/Apps','Crypto AI Pivot','Diversification']

def classify_holding(company, ticker):
    text = f'{company} {ticker}'.lower()
    keyword_map = {
        'Energy': ['constellation','nextera','duke','southern','vistra','ge vernova','cameco','uranium','woodside','bhp','freeport','southern copper'],
        'Data Centers': ['equinix','digital realty','iron mountain','coreweave','vertiv','schneider','eaton','super micro','dell'],
        'Compute': ['nvidia','amd','broadcom','asml','tsmc','taiwan semiconductor','intel','qualcomm','micron','marvell','applied materials','lam research'],
        'Data/Models': ['snowflake','palantir','databricks','meta','alphabet','google','mongodb','elastic','cloudflare'],
        'Platforms/Apps': ['microsoft','amazon','apple','salesforce','adobe','servicenow','oracle','ibm','tesla','shopify','intuit','sap','accenture'],
        'Crypto AI Pivot': ['coinbase','microstrategy','strategy','bitmine','iren','hut 8','cleanspark','riot','marathon','mara','cipher','bitcoin','block','galaxy','mining','miner']
    }
    for layer, keywords in keyword_map.items():
        if any(k in text for k in keywords):
            return layer
    return 'Diversification'

def layer_score(layer):
    return {
        'Energy': 85,
        'Data Centers': 88,
        'Compute': 95,
        'Data/Models': 75,
        'Platforms/Apps': 70,
        'Crypto AI Pivot': 55,
        'Diversification': 25
    }.get(layer, 25)

def calculate_holdings_exposures(holdings):
    h = holdings.copy()
    h['Weight'] = pd.to_numeric(h['Weight'], errors='coerce').fillna(0)
    h['AI Layer'] = h.apply(lambda r: classify_holding(str(r['Company']), str(r['Holding Ticker'])), axis=1)
    h['Layer Score'] = h['AI Layer'].apply(layer_score)
    h['Weighted AI Score'] = h['Weight'] * h['Layer Score'] / 100

    exposures = h.pivot_table(index='ETF', columns='AI Layer', values='Weight', aggfunc='sum', fill_value=0).reset_index()
    for layer in LAYERS:
        if layer not in exposures.columns:
            exposures[layer] = 0.0

    scores = h.groupby('ETF')['Weighted AI Score'].sum().reset_index().rename(columns={'Weighted AI Score':'AI Exposure Score'})
    total = h.groupby('ETF')['Weight'].sum().reset_index().rename(columns={'Weight':'Mapped Holdings Weight'})
    result = exposures.merge(scores, on='ETF', how='left').merge(total, on='ETF', how='left')
    result['AI Exposure Score'] = result['AI Exposure Score'].round(1)
    return h, result[['ETF'] + LAYERS + ['AI Exposure Score','Mapped Holdings Weight']]

def portfolio_exposure(weights, etf_exposures):
    total = sum(weights.values())
    out = {layer: 0 for layer in LAYERS + ['AI Exposure Score']}
    if total == 0:
        return out
    for etf, weight in weights.items():
        row = etf_exposures[etf_exposures['ETF'] == etf]
        if row.empty:
            continue
        row = row.iloc[0]
        for layer in LAYERS + ['AI Exposure Score']:
            out[layer] += (weight / total) * float(row[layer])
    return {k: round(v, 1) for k, v in out.items()}

def optimizer_score(row, current, target):
    score = 0
    for layer, target_value in target.items():
        gap = max(target_value - current.get(layer, 0), 0)
        score += gap * row[layer]
    score += row['AI Exposure Score'] * 2
    return round(score, 1)

def calculate_overlap(holdings, weights):
    h = holdings.copy()
    h['Weight'] = pd.to_numeric(h['Weight'], errors='coerce').fillna(0)
    total = sum(weights.values()) or 100
    h['Portfolio ETF Weight'] = h['ETF'].map(weights).fillna(0)
    h['Portfolio Contribution %'] = (h['Portfolio ETF Weight'] / total) * h['Weight']
    grouped = h.groupby(['Holding Ticker','Company'], as_index=False).agg(
        Total_Portfolio_Exposure=('Portfolio Contribution %','sum'),
        ETF_Count=('ETF','nunique'),
        ETFs=('ETF', lambda x: ', '.join(sorted(set(x)))),
        Max_Single_ETF_Holding=('Weight','max')
    )
    grouped['AI Layer'] = grouped.apply(lambda r: classify_holding(str(r['Company']), str(r['Holding Ticker'])), axis=1)
    grouped['Overlap Flag'] = grouped.apply(lambda r: 'High overlap' if r['ETF_Count'] >= 3 else ('Moderate overlap' if r['ETF_Count'] == 2 else 'Single ETF'), axis=1)
    return grouped.sort_values('Total_Portfolio_Exposure', ascending=False)

def concentration_warnings(overlap):
    warnings = []
    if overlap.empty:
        return warnings
    top = overlap.iloc[0]
    if top['Total_Portfolio_Exposure'] >= 8:
        warnings.append(f"High single-company concentration: {top['Company']} is {top['Total_Portfolio_Exposure']:.1f}% of mapped portfolio exposure.")
    nvda = overlap[overlap['Holding Ticker'].str.upper() == 'NVDA']
    if not nvda.empty and nvda.iloc[0]['Total_Portfolio_Exposure'] >= 5:
        warnings.append(f"NVIDIA stack risk: NVDA appears across {int(nvda.iloc[0]['ETF_Count'])} ETFs and contributes {nvda.iloc[0]['Total_Portfolio_Exposure']:.1f}% of mapped portfolio exposure.")
    crypto = overlap[overlap['AI Layer'] == 'Crypto AI Pivot']['Total_Portfolio_Exposure'].sum()
    if crypto >= 2:
        warnings.append(f"Crypto AI pivot exposure: crypto miners/platforms contribute {crypto:.1f}% of mapped portfolio exposure. This is high-upside but higher-risk optionality.")
    compute = overlap[overlap['AI Layer'] == 'Compute']['Total_Portfolio_Exposure'].sum()
    energy = overlap[overlap['AI Layer'] == 'Energy']['Total_Portfolio_Exposure'].sum()
    if compute > energy * 3 and compute > 5:
        warnings.append('Compute-heavy imbalance: compute exposure is much larger than energy exposure, which may miss the AI power bottleneck thesis.')
    return warnings

starter_holdings = pd.DataFrame([
    ['IVV','MSFT','Microsoft',7.0], ['IVV','NVDA','NVIDIA',6.5], ['IVV','AAPL','Apple',6.0], ['IVV','AMZN','Amazon',4.0], ['IVV','GOOGL','Alphabet',3.5], ['IVV','META','Meta Platforms',2.5], ['IVV','AVGO','Broadcom',2.0], ['IVV','TSLA','Tesla',1.5], ['IVV','JPM','JPMorgan Chase',1.3], ['IVV','XOM','Exxon Mobil',1.2],
    ['VEU','ASML','ASML',1.5], ['VEU','TSM','Taiwan Semiconductor Manufacturing',1.4], ['VEU','SAP','SAP',1.0], ['VEU','NESN','Nestle',1.0], ['VEU','NOVO','Novo Nordisk',0.9], ['VEU','TM','Toyota Motor',0.8], ['VEU','SHEL','Shell',0.7], ['VEU','AZN','AstraZeneca',0.7], ['VEU','TCEHY','Tencent',0.7], ['VEU','BHP','BHP Group',0.6],
    ['NDQ','NVDA','NVIDIA',8.5], ['NDQ','MSFT','Microsoft',7.8], ['NDQ','AAPL','Apple',7.5], ['NDQ','AMZN','Amazon',5.5], ['NDQ','AVGO','Broadcom',4.8], ['NDQ','META','Meta Platforms',4.6], ['NDQ','GOOGL','Alphabet',4.5], ['NDQ','TSLA','Tesla',3.0], ['NDQ','COST','Costco',2.5], ['NDQ','NFLX','Netflix',2.3],
    ['VHY','BHP','BHP Group',10.3], ['VHY','CBA','Commonwealth Bank of Australia',9.8], ['VHY','NAB','National Australia Bank',6.8], ['VHY','WDS','Woodside Energy',6.7], ['VHY','WBC','Westpac Banking',6.0], ['VHY','ANZ','ANZ Group',5.5], ['VHY','MQG','Macquarie Group',3.5], ['VHY','RIO','Rio Tinto',3.2], ['VHY','TLS','Telstra',2.8], ['VHY','WOW','Woolworths',2.5],
    ['AINF','GEV','GE Vernova',5.9], ['AINF','CCO','Cameco Corporation',5.4], ['AINF','SCCO','Southern Copper',5.4], ['AINF','FCX','Freeport-McMoRan',5.0], ['AINF','VRT','Vertiv',4.8], ['AINF','ETN','Eaton',4.5], ['AINF','EQIX','Equinix',4.0], ['AINF','DLR','Digital Realty',3.8], ['AINF','CEG','Constellation Energy',3.6], ['AINF','NEE','NextEra Energy',3.3],
    ['SEMI','NVDA','NVIDIA',12.0], ['SEMI','TSM','Taiwan Semiconductor Manufacturing',10.0], ['SEMI','ASML','ASML',9.0], ['SEMI','AVGO','Broadcom',8.0], ['SEMI','AMD','AMD',6.0], ['SEMI','AMAT','Applied Materials',5.0], ['SEMI','LRCX','Lam Research',4.5], ['SEMI','MU','Micron Technology',4.0], ['SEMI','QCOM','Qualcomm',3.5], ['SEMI','INTC','Intel',3.0],
    ['CRYP','BMNR','BitMine Immersion Technologies',10.4], ['CRYP','MSTR','Strategy Inc',9.8], ['CRYP','IREN','IREN Ltd',9.7], ['CRYP','HUT','Hut 8 Corp',5.1], ['CRYP','COIN','Coinbase Global',5.0], ['CRYP','CLSK','CleanSpark',4.5], ['CRYP','RIOT','Riot Platforms',4.0], ['CRYP','MARA','MARA Holdings',4.0], ['CRYP','CIFR','Cipher Mining',3.6], ['CRYP','GLXY','Galaxy Digital',3.2],
    ['GXAI','NVDA','NVIDIA',8.0], ['GXAI','MSFT','Microsoft',7.0], ['GXAI','GOOGL','Alphabet',6.0], ['GXAI','META','Meta Platforms',5.0], ['GXAI','PLTR','Palantir Technologies',4.5], ['GXAI','SNOW','Snowflake',4.0], ['GXAI','ADBE','Adobe',3.5], ['GXAI','NOW','ServiceNow',3.0], ['GXAI','CRM','Salesforce',3.0], ['GXAI','AMZN','Amazon',3.0]
], columns=['ETF','Holding Ticker','Company','Weight'])

st.title('⚡ AI ETF Holdings Optimizer + Overlap Engine')
st.caption('Holdings-driven ETF exposure, hidden overlap detection, and CRYP AI-pivot optionality.')

tabs = st.tabs(['ETF Optimizer','Overlap Engine','Holdings Engine','ETF Exposure Table','Upload Official Holdings','Methodology'])

with tabs[4]:
    st.subheader('Upload Official Holdings')
    uploaded = st.file_uploader('Upload a CSV with columns: ETF, Holding Ticker, Company, Weight', type=['csv'])
    st.download_button('Download starter holdings template', starter_holdings.to_csv(index=False).encode('utf-8'), file_name='holdings_template.csv', mime='text/csv')

if 'uploaded' in locals() and uploaded:
    try:
        holdings = pd.read_csv(uploaded)
        required_cols = {'ETF','Holding Ticker','Company','Weight'}
        if not required_cols.issubset(set(holdings.columns)):
            st.error('CSV must include columns: ETF, Holding Ticker, Company, Weight')
            holdings = starter_holdings.copy()
        else:
            st.success('Official holdings uploaded successfully. The optimizer is using your uploaded data.')
    except Exception as e:
        st.error(f'Could not read uploaded file: {e}')
        holdings = starter_holdings.copy()
else:
    holdings = starter_holdings.copy()

mapped_holdings, etf_exposures = calculate_holdings_exposures(holdings)

default_weights = {'IVV':22.0,'VEU':22.0,'NDQ':22.0,'VHY':24.0,'AINF':4.0,'SEMI':4.0,'CRYP':2.0,'GXAI':0.0}

with tabs[0]:
    st.subheader('ETF Optimizer')
    available_etfs = sorted(etf_exposures['ETF'].unique().tolist())
    weights = {}
    cols = st.columns(4)
    for i, etf in enumerate(available_etfs):
        with cols[i % 4]:
            weights[etf] = st.number_input(f'{etf} weight %', min_value=0.0, max_value=100.0, value=float(default_weights.get(etf, 0.0)), step=1.0, key=f'opt_{etf}')
    current = portfolio_exposure(weights, etf_exposures)
    st.markdown('### Current Portfolio Exposure')
    c = st.columns(4)
    c[0].metric('AI Exposure Score', current['AI Exposure Score'])
    c[1].metric('Energy', current['Energy'])
    c[2].metric('Data Centers', current['Data Centers'])
    c[3].metric('Compute', current['Compute'])
    c2 = st.columns(4)
    c2[0].metric('Data/Models', current['Data/Models'])
    c2[1].metric('Platforms/Apps', current['Platforms/Apps'])
    c2[2].metric('Crypto AI Pivot', current['Crypto AI Pivot'])
    c2[3].metric('Diversification', current['Diversification'])
    mode = st.selectbox('Choose optimizer mode', ['Balanced AI Growth','AI Infrastructure Tilt','Semiconductor Heavy','Crypto AI Pivot','Custom'])
    presets = {
        'Balanced AI Growth': {'Energy':5,'Data Centers':5,'Compute':12,'Data/Models':8,'Platforms/Apps':14,'Crypto AI Pivot':1},
        'AI Infrastructure Tilt': {'Energy':8,'Data Centers':8,'Compute':15,'Data/Models':4,'Platforms/Apps':8,'Crypto AI Pivot':1},
        'Semiconductor Heavy': {'Energy':2,'Data Centers':2,'Compute':25,'Data/Models':3,'Platforms/Apps':8,'Crypto AI Pivot':1},
        'Crypto AI Pivot': {'Energy':3,'Data Centers':4,'Compute':10,'Data/Models':4,'Platforms/Apps':8,'Crypto AI Pivot':5},
        'Custom': {'Energy':5,'Data Centers':5,'Compute':12,'Data/Models':8,'Platforms/Apps':14,'Crypto AI Pivot':1}
    }
    target = presets[mode].copy()
    if mode == 'Custom':
        cols = st.columns(3)
        for i, layer in enumerate(target.keys()):
            with cols[i % 3]:
                target[layer] = st.slider(f'Target {layer}', 0, 30, target[layer])
    gaps = {layer: round(target[layer] - current.get(layer, 0), 1) for layer in target}
    st.dataframe(pd.DataFrame([{'Layer':k,'Current':current[k],'Target':v,'Gap':gaps[k]} for k,v in target.items()]), use_container_width=True, hide_index=True)
    ranked = etf_exposures.copy()
    ranked['Optimizer Score'] = ranked.apply(lambda row: optimizer_score(row, current, target), axis=1)
    ranked = ranked.sort_values('Optimizer Score', ascending=False)
    st.markdown('### Suggested Buy Priority')
    st.dataframe(ranked[['ETF','AI Exposure Score','Energy','Data Centers','Compute','Data/Models','Platforms/Apps','Crypto AI Pivot','Optimizer Score']], use_container_width=True, hide_index=True)
    contribution = st.number_input('Next contribution amount ($)', min_value=0, value=3000, step=500)
    top3 = ranked.head(3).copy()
    positive = top3['Optimizer Score'].clip(lower=0)
    top3['Suggested $'] = (positive / positive.sum() * contribution).round(0) if positive.sum() > 0 else 0
    st.markdown('### No-Sell Allocation Plan')
    st.dataframe(top3[['ETF','Optimizer Score','Suggested $']], use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader('Overlap Engine')
    st.write('Shows hidden company-level concentration across ETFs based on your portfolio weights.')
    available_etfs = sorted(etf_exposures['ETF'].unique().tolist())
    overlap_weights = {}
    cols = st.columns(4)
    for i, etf in enumerate(available_etfs):
        with cols[i % 4]:
            overlap_weights[etf] = st.number_input(f'{etf} weight %', min_value=0.0, max_value=100.0, value=float(default_weights.get(etf, 0.0)), step=1.0, key=f'overlap_{etf}')
    overlap = calculate_overlap(mapped_holdings, overlap_weights)
    st.markdown('### Hidden Concentration Warnings')
    warnings = concentration_warnings(overlap)
    if warnings:
        for warning in warnings:
            st.warning(warning)
    else:
        st.success('No major concentration warnings detected in mapped holdings.')
    st.markdown('### Top Company Exposures Across Portfolio')
    st.dataframe(overlap[['Holding Ticker','Company','AI Layer','Total_Portfolio_Exposure','ETF_Count','ETFs','Overlap Flag']], use_container_width=True, hide_index=True)
    st.markdown('### Top 10 Company Exposures')
    st.bar_chart(overlap.head(10).set_index('Company')['Total_Portfolio_Exposure'])
    st.markdown('### Layer-Level Contribution from Overlapped Holdings')
    layer_overlap = overlap.groupby('AI Layer', as_index=False)['Total_Portfolio_Exposure'].sum().sort_values('Total_Portfolio_Exposure', ascending=False)
    st.dataframe(layer_overlap, use_container_width=True, hide_index=True)
    st.bar_chart(layer_overlap.set_index('AI Layer')['Total_Portfolio_Exposure'])
    st.markdown('### CRYP / Crypto Miner AI Pivot Lens')
    st.info('CRYP is treated as Crypto AI Pivot exposure because some crypto miners have power access, data-center sites, cooling infrastructure, and operating experience that may be repurposed toward AI/HPC workloads.')
    st.dataframe(mapped_holdings[mapped_holdings['ETF'] == 'CRYP'][['ETF','Holding Ticker','Company','Weight','AI Layer','Layer Score']], use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader('Holdings Engine')
    etf_filter = st.multiselect('ETF filter', sorted(mapped_holdings['ETF'].unique()), default=sorted(mapped_holdings['ETF'].unique()))
    layer_filter = st.multiselect('AI layer filter', sorted(mapped_holdings['AI Layer'].unique()), default=sorted(mapped_holdings['AI Layer'].unique()))
    view = mapped_holdings[mapped_holdings['ETF'].isin(etf_filter) & mapped_holdings['AI Layer'].isin(layer_filter)].sort_values(['ETF','Weight'], ascending=[True,False])
    st.dataframe(view, use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader('ETF Exposure Table')
    st.dataframe(etf_exposures.sort_values('AI Exposure Score', ascending=False), use_container_width=True, hide_index=True)
    st.bar_chart(etf_exposures.set_index('ETF')[LAYERS])

with tabs[5]:
    st.subheader('Methodology')
    st.markdown('''
### What the Overlap Engine does

The overlap engine calculates company-level exposure across all ETFs using:

**Portfolio ETF weight × holding weight inside each ETF**

It then adds up the same company across all ETFs.

### Why CRYP has a separate AI-pivot layer

CRYP is not treated as classic AI exposure. It is treated as **Crypto AI Pivot** exposure because some crypto miners may have:

- power access
- data-center sites
- cooling infrastructure
- operational experience running high-density compute
- optionality to shift toward AI/HPC hosting

This is higher-risk optionality, not the same as NVIDIA/TSMC-style core AI exposure.

### Important

The bundled holdings are starter rows and should be replaced with official full holdings where possible. This app is for research and education only. It is not personal financial advice.
''')
