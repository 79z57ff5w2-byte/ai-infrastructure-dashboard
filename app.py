import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI Portfolio Allocation Engine", layout="wide")

# Sample holdings
data = [
    ["IVV","MSFT","Microsoft",7.0],
    ["IVV","NVDA","NVIDIA",6.5],
    ["NDQ","NVDA","NVIDIA",8.5],
    ["NDQ","MSFT","Microsoft",7.8],
    ["SEMI","NVDA","NVIDIA",12.0],
    ["AINF","CEG","Constellation Energy",3.6],
    ["CRYP","COIN","Coinbase",5.0],
]

df = pd.DataFrame(data, columns=["ETF","Ticker","Company","Weight"])

st.title("⚡ Portfolio Allocation Engine")

# Portfolio weights input
etfs = sorted(df["ETF"].unique())
weights = {}

st.subheader("Input Portfolio Weights")

cols = st.columns(len(etfs))

for i, etf in enumerate(etfs):
    weights[etf] = cols[i].number_input(etf, 0.0, 100.0, 10.0)

total = sum(weights.values())

if total != 100:
    st.warning(f"Total = {total}%. Will normalise.")

norm = {k: (v/total if total else 0) for k,v in weights.items()}

# Look-through exposure
df["ETF Weight"] = df["ETF"].map(norm)
df["Lookthrough"] = df["ETF Weight"] * df["Weight"]

result = df.groupby(["Ticker","Company"], as_index=False)["Lookthrough"].sum()
result = result.sort_values("Lookthrough", ascending=False)

st.subheader("Look-through Exposure")
st.dataframe(result)

st.bar_chart(result.set_index("Company"))
