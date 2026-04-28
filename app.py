
import streamlit as st
import pandas as pd
import urllib.parse, urllib.request, xml.etree.ElementTree as ET

st.set_page_config(page_title="AI Portfolio Decision Engine + Live Signals", page_icon="⚡", layout="wide")

LAYERS = ["Energy","Data Centers","Compute","Data/Models","Platforms/Apps","Crypto AI Pivot","Diversification"]
BASE_IMPORTANCE = {"Energy":92,"Data Centers":90,"Compute":98,"Data/Models":78,"Platforms/Apps":75,"Crypto AI Pivot":58,"Diversification":30}

SIGNAL_QUERIES = {
    "Energy":["AI data center power demand", "AI data center nuclear power deal", "hyperscaler power purchase agreement data center"],
    "Data Centers":["AI data center expansion", "hyperscale data center AI", "AI data center cooling power"],
    "Compute":["NVIDIA AI chip demand", "AI GPU supply shortage", "TSMC AI chips capex"],
    "Data/Models":["OpenAI Anthropic Google DeepMind model", "AI model training compute demand", "enterprise AI data platform"],
    "Platforms/Apps":["Microsoft Copilot AI revenue", "Amazon AWS AI demand", "Google Cloud AI demand"],
    "Crypto AI Pivot":["bitcoin miner AI data center pivot", "crypto miner AI HPC hosting", "IREN AI cloud data center"]
}

def classify_text(company, ticker=""):
    text=f"{company} {ticker}".lower()
    maps={
        "Energy":["constellation","nextera","duke","southern","vistra","ge vernova","cameco","uranium","woodside","bhp","freeport","southern copper","power","nuclear","electricity","grid"],
        "Data Centers":["equinix","digital realty","coreweave","vertiv","schneider","eaton","super micro","dell","data center","datacenter","cooling"],
        "Compute":["nvidia","amd","broadcom","asml","tsmc","taiwan semiconductor","intel","qualcomm","micron","marvell","applied materials","lam research","gpu","chip","semiconductor"],
        "Data/Models":["snowflake","palantir","databricks","meta","alphabet","google","mongodb","elastic","cloudflare","openai","anthropic","deepmind","foundation model","model training"],
        "Platforms/Apps":["microsoft","amazon","apple","salesforce","adobe","servicenow","oracle","ibm","tesla","shopify","intuit","sap","accenture","copilot","aws","azure","cloud"],
        "Crypto AI Pivot":["coinbase","microstrategy","strategy","bitmine","iren","hut 8","cleanspark","riot","marathon","mara","cipher","bitcoin","block","galaxy","mining","miner","crypto"]
    }
    for layer, words in maps.items():
        if any(w in text for w in words): return layer
    return "Diversification"

def score_headline(title):
    t=title.lower(); score=20
    high=["capex","data center","datacenter","power","nuclear","gpu","chip","semiconductor","supply","shortage","contract","deal","partnership","expansion","demand","electricity","grid","cloud"]
    huge=["billion","$","megawatt","mw","gigawatt","gw","multi-year","nvidia","tsmc","microsoft","amazon","alphabet","constellation","coreweave","hyperscaler"]
    bearish=["delay","cancel","slowdown","shortfall","restriction","export control","constraint","overcapacity"]
    for w in high:
        if w in t: score += 5
    for w in huge:
        if w in t: score += 8
    for w in bearish:
        if w in t: score += 6
    return min(score,100)

def sentiment(title):
    t=title.lower()
    if any(w in t for w in ["delay","cancel","slowdown","restriction","shortfall","shortage","constraint"]): return "Bearish / constraint"
    if any(w in t for w in ["deal","expansion","demand","growth","partnership","contract","investment","capex","buildout"]): return "Bullish"
    return "Neutral"

def market_read(layer):
    return {
        "Energy":"AI demand may be moving from compute scarcity to power scarcity.",
        "Data Centers":"Physical infrastructure and cooling capacity may be becoming more valuable.",
        "Compute":"Chip and accelerator demand remains the core near-term AI capex driver.",
        "Data/Models":"Model scaling and enterprise data demand may support the data/model layer.",
        "Platforms/Apps":"Platform winners may convert AI spend into user-facing revenue.",
        "Crypto AI Pivot":"Crypto miners may gain AI/HPC optionality where power and sites are valuable.",
    }.get(layer,"General AI ecosystem signal.")

@st.cache_data(ttl=1800)
def fetch_news(query, max_items=4):
    url="https://news.google.com/rss/search?q="+urllib.parse.quote_plus(query)+"&hl=en-AU&gl=AU&ceid=AU:en"
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        xml=urllib.request.urlopen(req,timeout=8).read()
        root=ET.fromstring(xml); ch=root.find("channel")
        rows=[]
        if ch is None: return []
        for item in ch.findall("item")[:max_items]:
            title=item.findtext("title",default="")
            source_el=item.find("source")
            rows.append({"Title":title,"Source":source_el.text if source_el is not None else "","Published":item.findtext("pubDate",default=""),"Link":item.findtext("link",default=""),"Query":query})
        return rows
    except Exception:
        return []

def fetch_live_signals():
    rows=[]
    for default_layer, qs in SIGNAL_QUERIES.items():
        for q in qs:
            for item in fetch_news(q,3):
                layer=classify_text(item["Title"])
                if layer=="Diversification": layer=default_layer
                rows.append({**item,"AI Layer":layer,"Signal Score":score_headline(item["Title"]),"Sentiment":sentiment(item["Title"]),"Market Read":market_read(layer)})
    if not rows: return pd.DataFrame(columns=["AI Layer","Signal Score","Sentiment","Title","Source","Published","Query","Market Read","Link"])
    return pd.DataFrame(rows).drop_duplicates("Title").sort_values("Signal Score",ascending=False)

def live_boosts(signals):
    boosts={l:0 for l in LAYERS}
    if signals.empty: return boosts
    for layer in LAYERS:
        d=signals[signals["AI Layer"]==layer]
        if not d.empty:
            boosts[layer]=min(round(d["Signal Score"].mean()/10 + len(d[d["Signal Score"]>=70])*3,1),25)
    return boosts

def layer_score(layer, boosts): return min(BASE_IMPORTANCE.get(layer,30)+boosts.get(layer,0),100)

def calc_exposures(holdings, boosts):
    h=holdings.copy(); h["Weight"]=pd.to_numeric(h["Weight"],errors="coerce").fillna(0)
    h["AI Layer"]=h.apply(lambda r: classify_text(str(r["Company"]),str(r["Holding Ticker"])),axis=1)
    h["Layer Score"]=h["AI Layer"].apply(lambda x: layer_score(x, boosts))
    h["Weighted AI Score"]=h["Weight"]*h["Layer Score"]/100
    exp=h.pivot_table(index="ETF",columns="AI Layer",values="Weight",aggfunc="sum",fill_value=0).reset_index()
    for l in LAYERS:
        if l not in exp.columns: exp[l]=0.0
    scores=h.groupby("ETF")["Weighted AI Score"].sum().reset_index().rename(columns={"Weighted AI Score":"AI Exposure Score"})
    totals=h.groupby("ETF")["Weight"].sum().reset_index().rename(columns={"Weight":"Mapped Holdings Weight"})
    out=exp.merge(scores,on="ETF",how="left").merge(totals,on="ETF",how="left")
    out["AI Exposure Score"]=out["AI Exposure Score"].round(1)
    return h,out[["ETF"]+LAYERS+["AI Exposure Score","Mapped Holdings Weight"]]

def portfolio_profile(weights, etf_exp):
    total=sum(weights.values()) or 100; out={l:0 for l in LAYERS+["AI Exposure Score"]}
    for etf,w in weights.items():
        row=etf_exp[etf_exp["ETF"]==etf]
        if row.empty: continue
        row=row.iloc[0]
        for l in out: out[l]+=w/total*float(row[l])
    return {k:round(v,1) for k,v in out.items()}

def overlap_engine(mapped, weights):
    h=mapped.copy(); total=sum(weights.values()) or 100
    h["Portfolio ETF Weight"]=h["ETF"].map(weights).fillna(0)
    h["Portfolio Exposure"]=h["Portfolio ETF Weight"]/total*h["Weight"]
    g=h.groupby(["Holding Ticker","Company"],as_index=False).agg(Portfolio_Exposure=("Portfolio Exposure","sum"),ETF_Count=("ETF","nunique"),ETFs=("ETF",lambda x:", ".join(sorted(set(x)))))
    g["AI Layer"]=g.apply(lambda r: classify_text(str(r["Company"]),str(r["Holding Ticker"])),axis=1)
    g["Overlap Flag"]=g["ETF_Count"].apply(lambda x:"High overlap" if x>=3 else ("Moderate overlap" if x==2 else "Single ETF"))
    return g.sort_values("Portfolio_Exposure",ascending=False)

def company_importance(company,ticker,layer,boosts):
    name=f"{company} {ticker}".lower(); base=BASE_IMPORTANCE.get(layer,30)+boosts.get(layer,0)
    b={"nvidia":25,"tsmc":24,"asml":23,"broadcom":20,"microsoft":19,"amazon":17,"alphabet":17,"constellation":18,"nextera":15,"equinix":16,"digital realty":15,"vertiv":20,"cameco":13,"ge vernova":14,"palantir":12,"snowflake":10,"meta":12,"iren":8,"hut 8":7,"cleanspark":7,"riot":7,"marathon":7,"mara":7}
    boost=max([v for k,v in b.items() if k in name] or [0])
    return min(round(base+boost,1),100)

def company_gap(overlap, boosts, mapped):
    critical=pd.DataFrame([
        ["NVDA","NVIDIA","Compute"],["TSM","TSMC","Compute"],["ASML","ASML","Compute"],["AVGO","Broadcom","Compute"],["AMD","AMD","Compute"],["AMAT","Applied Materials","Compute"],
        ["MSFT","Microsoft","Platforms/Apps"],["AMZN","Amazon","Platforms/Apps"],["GOOGL","Alphabet","Data/Models"],["META","Meta Platforms","Data/Models"],["PLTR","Palantir Technologies","Data/Models"],["SNOW","Snowflake","Data/Models"],
        ["CEG","Constellation Energy","Energy"],["NEE","NextEra Energy","Energy"],["GEV","GE Vernova","Energy"],["CCO","Cameco Corporation","Energy"],
        ["VRT","Vertiv","Data Centers"],["EQIX","Equinix","Data Centers"],["DLR","Digital Realty","Data Centers"],["ETN","Eaton","Data Centers"],
        ["IREN","IREN Ltd","Crypto AI Pivot"],["HUT","Hut 8 Corp","Crypto AI Pivot"],["CLSK","CleanSpark","Crypto AI Pivot"],["RIOT","Riot Platforms","Crypto AI Pivot"],["MARA","MARA Holdings","Crypto AI Pivot"]
    ],columns=["Holding Ticker","Company","AI Layer"])
    gap=critical.merge(overlap[["Holding Ticker","Company","Portfolio_Exposure","ETF_Count","ETFs"]],on=["Holding Ticker","Company"],how="left")
    gap[["Portfolio_Exposure","ETF_Count"]]=gap[["Portfolio_Exposure","ETF_Count"]].fillna(0); gap["ETFs"]=gap["ETFs"].fillna("None")
    gap["Dynamic Importance Score"]=gap.apply(lambda r: company_importance(r["Company"],r["Holding Ticker"],r["AI Layer"],boosts),axis=1)
    gap["Gap Score"]=(gap["Dynamic Importance Score"]-gap["Portfolio_Exposure"]*10).clip(lower=0).round(1)
    def sig(r):
        e=r["Portfolio_Exposure"]; imp=r["Dynamic Importance Score"]
        if e>=8: return "🔴 LIMIT — high concentration"
        if e>=5 and imp>=90: return "🟠 HOLD / WATCH — important but already meaningful"
        if e<1 and imp>=85: return "🟢 ADD — critical gap"
        if e<3 and imp>=75: return "🟡 BUILD — underweight"
        if r["AI Layer"]=="Crypto AI Pivot" and e<3: return "🟣 OPTIONALITY — small satellite only"
        return "⚖️ OK / monitor"
    gap["Company-Level Buy Signal"]=gap.apply(sig,axis=1)
    def route(r):
        m=mapped[(mapped["Holding Ticker"]==r["Holding Ticker"]) | (mapped["Company"]==r["Company"])].sort_values("Weight",ascending=False)
        return "No mapped ETF" if m.empty else ", ".join([f"{x['ETF']} ({x['Weight']:.1f}%)" for _,x in m.head(3).iterrows()])
    gap["ETF Route"]=gap.apply(route,axis=1)
    return gap.sort_values(["Gap Score","Dynamic Importance Score"],ascending=False)

def warnings(overlap):
    out=[]
    if overlap.empty: return out
    top=overlap.iloc[0]
    if top["Portfolio_Exposure"]>=8: out.append(f"High single-company concentration: {top['Company']} is {top['Portfolio_Exposure']:.1f}% of mapped portfolio exposure.")
    nv=overlap[overlap["Holding Ticker"].str.upper()=="NVDA"]
    if not nv.empty and nv.iloc[0]["Portfolio_Exposure"]>=5: out.append(f"NVIDIA stack risk: NVDA appears across {int(nv.iloc[0]['ETF_Count'])} ETFs and contributes {nv.iloc[0]['Portfolio_Exposure']:.1f}% of mapped portfolio exposure.")
    crypto=overlap[overlap["AI Layer"]=="Crypto AI Pivot"]["Portfolio_Exposure"].sum()
    if crypto>=2: out.append(f"Crypto AI pivot exposure: crypto miners/platforms contribute {crypto:.1f}% of mapped portfolio exposure.")
    compute=overlap[overlap["AI Layer"]=="Compute"]["Portfolio_Exposure"].sum(); energy=overlap[overlap["AI Layer"]=="Energy"]["Portfolio_Exposure"].sum()
    if compute>energy*3 and compute>5: out.append("Compute-heavy imbalance: compute exposure is much larger than energy exposure.")
    return out

holdings0=pd.DataFrame([
['IVV','MSFT','Microsoft',7.0],['IVV','NVDA','NVIDIA',6.5],['IVV','AAPL','Apple',6.0],['IVV','AMZN','Amazon',4.0],['IVV','GOOGL','Alphabet',3.5],['IVV','META','Meta Platforms',2.5],['IVV','AVGO','Broadcom',2.0],['IVV','TSLA','Tesla',1.5],['IVV','JPM','JPMorgan Chase',1.3],['IVV','XOM','Exxon Mobil',1.2],
['VEU','ASML','ASML',1.5],['VEU','TSM','TSMC',1.4],['VEU','SAP','SAP',1.0],['VEU','NESN','Nestle',1.0],['VEU','NOVO','Novo Nordisk',0.9],['VEU','TM','Toyota Motor',0.8],['VEU','SHEL','Shell',0.7],['VEU','AZN','AstraZeneca',0.7],['VEU','TCEHY','Tencent',0.7],['VEU','BHP','BHP Group',0.6],
['NDQ','NVDA','NVIDIA',8.5],['NDQ','MSFT','Microsoft',7.8],['NDQ','AAPL','Apple',7.5],['NDQ','AMZN','Amazon',5.5],['NDQ','AVGO','Broadcom',4.8],['NDQ','META','Meta Platforms',4.6],['NDQ','GOOGL','Alphabet',4.5],['NDQ','TSLA','Tesla',3.0],['NDQ','COST','Costco',2.5],['NDQ','NFLX','Netflix',2.3],
['VHY','BHP','BHP Group',10.3],['VHY','CBA','Commonwealth Bank of Australia',9.8],['VHY','NAB','National Australia Bank',6.8],['VHY','WDS','Woodside Energy',6.7],['VHY','WBC','Westpac Banking',6.0],['VHY','ANZ','ANZ Group',5.5],['VHY','MQG','Macquarie Group',3.5],['VHY','RIO','Rio Tinto',3.2],['VHY','TLS','Telstra',2.8],['VHY','WOW','Woolworths',2.5],
['AINF','GEV','GE Vernova',5.9],['AINF','CCO','Cameco Corporation',5.4],['AINF','SCCO','Southern Copper',5.4],['AINF','FCX','Freeport-McMoRan',5.0],['AINF','VRT','Vertiv',4.8],['AINF','ETN','Eaton',4.5],['AINF','EQIX','Equinix',4.0],['AINF','DLR','Digital Realty',3.8],['AINF','CEG','Constellation Energy',3.6],['AINF','NEE','NextEra Energy',3.3],
['SEMI','NVDA','NVIDIA',12.0],['SEMI','TSM','TSMC',10.0],['SEMI','ASML','ASML',9.0],['SEMI','AVGO','Broadcom',8.0],['SEMI','AMD','AMD',6.0],['SEMI','AMAT','Applied Materials',5.0],['SEMI','LRCX','Lam Research',4.5],['SEMI','MU','Micron Technology',4.0],['SEMI','QCOM','Qualcomm',3.5],['SEMI','INTC','Intel',3.0],
['CRYP','BMNR','BitMine Immersion Technologies',10.4],['CRYP','MSTR','Strategy Inc',9.8],['CRYP','IREN','IREN Ltd',9.7],['CRYP','HUT','Hut 8 Corp',5.1],['CRYP','COIN','Coinbase Global',5.0],['CRYP','CLSK','CleanSpark',4.5],['CRYP','RIOT','Riot Platforms',4.0],['CRYP','MARA','MARA Holdings',4.0],['CRYP','CIFR','Cipher Mining',3.6],['CRYP','GLXY','Galaxy Digital',3.2],
['GXAI','NVDA','NVIDIA',8.0],['GXAI','MSFT','Microsoft',7.0],['GXAI','GOOGL','Alphabet',6.0],['GXAI','META','Meta Platforms',5.0],['GXAI','PLTR','Palantir Technologies',4.5],['GXAI','SNOW','Snowflake',4.0],['GXAI','ADBE','Adobe',3.5],['GXAI','NOW','ServiceNow',3.0],['GXAI','CRM','Salesforce',3.0],['GXAI','AMZN','Amazon',3.0]
],columns=['ETF','Holding Ticker','Company','Weight'])

st.title('⚡ AI Portfolio Decision Engine + Live Signals')
st.caption('Live AI signals → dynamic importance → holdings overlap → company gaps → next-buy actions.')

tabs=st.tabs(['Live AI Signal Engine','Decision Engine','Dynamic Importance Ranking','Company Gap Engine','Overlap Engine','ETF Optimizer','Holdings Engine','Upload Official Holdings','Methodology'])

with tabs[7]:
    st.subheader('Upload Official Holdings')
    uploaded=st.file_uploader('Upload CSV with columns: ETF, Holding Ticker, Company, Weight', type=['csv'])
    st.download_button('Download starter holdings template', holdings0.to_csv(index=False).encode(), 'holdings_template.csv', 'text/csv')

if 'uploaded' in locals() and uploaded:
    try:
        holdings=pd.read_csv(uploaded)
        if not {'ETF','Holding Ticker','Company','Weight'}.issubset(holdings.columns):
            st.error('CSV must include ETF, Holding Ticker, Company, Weight'); holdings=holdings0.copy()
    except Exception as e:
        st.error(f'Could not read upload: {e}'); holdings=holdings0.copy()
else:
    holdings=holdings0.copy()

with st.sidebar:
    st.header('Portfolio Inputs')
    defaults={'IVV':22.0,'VEU':22.0,'NDQ':22.0,'VHY':24.0,'AINF':4.0,'SEMI':4.0,'CRYP':2.0,'GXAI':0.0}
    weights={}
    for etf in sorted(holdings['ETF'].unique()):
        weights[etf]=st.number_input(f'{etf} weight %',0.0,100.0,float(defaults.get(etf,0.0)),1.0,key=f'w_{etf}')
    contribution=st.number_input('Next contribution amount ($)',0,100000,3000,500)
    target_mode=st.selectbox('Target mode',['Balanced AI Growth','AI Infrastructure Tilt','Semiconductor Heavy','Crypto AI Pivot'])
    use_live=st.toggle('Use live signals in ranking', value=True)

signals=fetch_live_signals() if use_live else pd.DataFrame(columns=['AI Layer','Signal Score','Sentiment','Title','Source','Published','Query','Market Read','Link'])
boosts=live_boosts(signals) if use_live else {l:0 for l in LAYERS}
mapped, etf_exp=calc_exposures(holdings,boosts)
profile=portfolio_profile(weights,etf_exp)
overlap=overlap_engine(mapped,weights)
gap=company_gap(overlap,boosts,mapped)

targets={
'Balanced AI Growth': {'Energy':5,'Data Centers':5,'Compute':12,'Data/Models':8,'Platforms/Apps':14,'Crypto AI Pivot':1},
'AI Infrastructure Tilt': {'Energy':8,'Data Centers':8,'Compute':15,'Data/Models':4,'Platforms/Apps':8,'Crypto AI Pivot':1},
'Semiconductor Heavy': {'Energy':2,'Data Centers':2,'Compute':25,'Data/Models':3,'Platforms/Apps':8,'Crypto AI Pivot':1},
'Crypto AI Pivot': {'Energy':3,'Data Centers':4,'Compute':10,'Data/Models':4,'Platforms/Apps':8,'Crypto AI Pivot':5}}
target=targets[target_mode]

def decision_plan():
    act=gap[gap['Company-Level Buy Signal'].str.contains('ADD|BUILD|OPTIONALITY',regex=True)].head(5).copy()
    if act.empty: return act
    score=act['Gap Score'].clip(lower=0)
    act['Suggested $']=(score/score.sum()*contribution).round(0) if score.sum()>0 else 0
    act.insert(0,'Priority', range(1,len(act)+1))
    return act[['Priority','Company-Level Buy Signal','Company','AI Layer','Dynamic Importance Score','Portfolio_Exposure','ETF Route','Suggested $']]

plan=decision_plan()

with tabs[0]:
    st.subheader('Live AI Signal Engine')
    if not use_live: st.info('Live signals disabled in sidebar.')
    elif signals.empty: st.warning('No live signals could be fetched. Base model is still active.')
    else:
        c=st.columns(4); c[0].metric('Signals fetched',len(signals)); c[1].metric('Avg signal score',round(signals['Signal Score'].mean(),1)); c[2].metric('Strong signals',len(signals[signals['Signal Score']>=70])); c[3].metric('Layers active',signals['AI Layer'].nunique())
        st.markdown('### Layer Boosts Applied')
        st.dataframe(pd.DataFrame([{'AI Layer':k,'Live Importance Boost':v} for k,v in boosts.items()]).sort_values('Live Importance Boost',ascending=False), use_container_width=True, hide_index=True)
        st.markdown('### What Actually Matters')
        st.dataframe(signals.head(15)[['AI Layer','Signal Score','Sentiment','Title','Source','Published','Market Read','Link']], use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader('Full Decision Engine')
    c=st.columns(4); c[0].metric('Portfolio AI Score',profile['AI Exposure Score']); c[1].metric('Compute',profile['Compute']); c[2].metric('Energy',profile['Energy']); c[3].metric('Data Centers',profile['Data Centers'])
    c2=st.columns(4); c2[0].metric('Data/Models',profile['Data/Models']); c2[1].metric('Platforms/Apps',profile['Platforms/Apps']); c2[2].metric('Crypto AI Pivot',profile['Crypto AI Pivot']); c2[3].metric('Diversification',profile['Diversification'])
    st.markdown('### Key Warnings')
    ws=warnings(overlap)
    if ws:
        for w in ws: st.warning(w)
    else: st.success('No major concentration warnings detected.')
    st.markdown('### Recommended Next-Buy Action Plan')
    st.dataframe(plan,use_container_width=True,hide_index=True)
    if not plan.empty:
        r=plan.iloc[0]; st.success(f"Top action: {r['Company-Level Buy Signal']} — {r['Company']} via {r['ETF Route']}")

with tabs[2]:
    st.subheader('Dynamic Importance Ranking')
    st.dataframe(gap[['Holding Ticker','Company','AI Layer','Dynamic Importance Score','Portfolio_Exposure','ETF_Count','ETFs','Company-Level Buy Signal']], use_container_width=True, hide_index=True)
    st.bar_chart(gap.head(15).set_index('Company')[['Dynamic Importance Score','Portfolio_Exposure']])

with tabs[3]:
    st.subheader('Company Gap Engine')
    st.dataframe(gap[['Holding Ticker','Company','AI Layer','Dynamic Importance Score','Portfolio_Exposure','Gap Score','Company-Level Buy Signal','ETF Route']], use_container_width=True, hide_index=True)
    st.bar_chart(gap.head(15).set_index('Company')['Gap Score'])

with tabs[4]:
    st.subheader('Overlap Engine')
    st.dataframe(overlap[['Holding Ticker','Company','AI Layer','Portfolio_Exposure','ETF_Count','ETFs','Overlap Flag']], use_container_width=True, hide_index=True)
    st.bar_chart(overlap.head(10).set_index('Company')['Portfolio_Exposure'])

with tabs[5]:
    st.subheader('ETF Optimizer')
    gapdf=pd.DataFrame([{'Layer':k,'Current':profile[k],'Target':v,'Gap':round(v-profile[k],1)} for k,v in target.items()])
    st.dataframe(gapdf,use_container_width=True,hide_index=True)
    ranked=etf_exp.copy()
    def etf_score(row):
        s=0
        for l,t in target.items(): s+=max(t-profile.get(l,0),0)*row[l]
        return round(s+row['AI Exposure Score']*2,1)
    ranked['Optimizer Score']=ranked.apply(etf_score,axis=1)
    ranked=ranked.sort_values('Optimizer Score',ascending=False)
    st.dataframe(ranked[['ETF','AI Exposure Score','Energy','Data Centers','Compute','Data/Models','Platforms/Apps','Crypto AI Pivot','Optimizer Score']], use_container_width=True, hide_index=True)
    top3=ranked.head(3).copy(); pos=top3['Optimizer Score'].clip(lower=0); top3['Suggested $']=(pos/pos.sum()*contribution).round(0) if pos.sum()>0 else 0
    st.dataframe(top3[['ETF','Optimizer Score','Suggested $']], use_container_width=True, hide_index=True)

with tabs[6]:
    st.subheader('Holdings Engine')
    st.dataframe(mapped.sort_values(['ETF','Weight'],ascending=[True,False]), use_container_width=True, hide_index=True)
    st.markdown('### ETF Exposure Table')
    st.dataframe(etf_exp.sort_values('AI Exposure Score',ascending=False), use_container_width=True, hide_index=True)

with tabs[8]:
    st.subheader('Methodology')
    st.markdown("""
The live signal engine fetches recent Google News RSS headlines for AI infrastructure themes, classifies them by AI layer, scores their strength, and applies a temporary importance boost to affected layers.

This affects dynamic company importance, company gaps, and the decision plan. Treat live signals as triage, not truth. Upload official holdings for best accuracy.

CRYP is treated as **Crypto AI Pivot** exposure because some crypto miners have power access, data-center sites, cooling infrastructure and high-density compute operating experience that may create AI/HPC optionality.

This is for research and education only. It is not personal financial advice.
""")
