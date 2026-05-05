import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(layout="wide")

st.title("📊 Stock Screener Dashboard")

# =========================
# LOAD DATA (SAFE)
# =========================
file_path = "latest_results.csv"

if not os.path.exists(file_path):
    st.warning("⚠️ Data not available yet. Please wait for GitHub Actions run.")
    st.stop()

df = pd.read_csv(file_path)

if df.empty:
    st.warning("No data available")
    st.stop()

# =========================
# SIDEBAR FILTER (DRILL DOWN)
# =========================
st.sidebar.header("🔍 Filters")

sector_list = sorted(df['sector'].dropna().unique())

selected_sector = st.sidebar.selectbox(
    "Select Sector",
    ["All"] + sector_list
)

# Apply filter
if selected_sector != "All":
    filtered_df = df[df['sector'] == selected_sector]
else:
    filtered_df = df.copy()

# =========================
# SECTOR HEATMAP
# =========================
sector_df = filtered_df.groupby("sector").agg(
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
    filtered_df,
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

st.dataframe(
    filtered_df.sort_values(by="return", ascending=False),
    use_container_width=True
)
