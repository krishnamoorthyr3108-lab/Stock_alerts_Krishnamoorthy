import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📊 Stock Screener Dashboard")

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("latest_results.csv")

if df.empty:
    st.warning("No data available")
    st.stop()

# =========================
# SECTOR HEATMAP
# =========================
sector_df = df.groupby("sector").agg(
    stock_count=("symbol", "count"),
    avg_return=("return", "mean")
).reset_index()

st.subheader("🔥 Sector Heatmap")

fig = px.treemap(
    sector_df,
    path=["sector"],
    values="stock_count",
    color="avg_return",
    color_continuous_scale="RdYlGn",
    title="Sector Strength"
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# STOCK HEATMAP
# =========================
st.subheader("📈 Stock Heatmap")

fig2 = px.treemap(
    df,
    path=["sector", "symbol"],
    values="avg_vol",
    color="return",
    color_continuous_scale="RdYlGn",
    title="Stock Performance"
)

st.plotly_chart(fig2, use_container_width=True)

# =========================
# TABLE
# =========================
st.subheader("📋 Stock Table")

st.dataframe(df.sort_values(by="return", ascending=False))