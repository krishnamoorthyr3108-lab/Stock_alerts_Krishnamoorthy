import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(layout="wide")

st.title("📊 Stock Screener Dashboard")

# =========================
# LOAD DATA
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
# SIDEBAR FILTERS
# =========================
st.sidebar.header("🔍 Filters")

sector_list = sorted(df['sector'].dropna().unique())

selected_sector = st.sidebar.selectbox(
    "Select Sector",
    ["All"] + sector_list
)

min_return = st.sidebar.slider("Min Return %", 0, 20, 5)
min_volume = st.sidebar.slider("Min Avg Volume", 0, 1000000, 50000)

# Apply filters
filtered_df = df.copy()

if selected_sector != "All":
    filtered_df = filtered_df[filtered_df['sector'] == selected_sector]

filtered_df = filtered_df[
    (filtered_df['return'] >= min_return) &
    (filtered_df['avg_vol'] >= min_volume)
]

# =========================
# SECTOR LEADERBOARD
# =========================
st.subheader("🏆 Sector Leaderboard")

sector_summary = df.groupby("sector").agg(
    stock_count=("symbol", "count"),
    avg_return=("return", "mean")
).reset_index()

sector_summary = sector_summary.sort_values(by="avg_return", ascending=False)

col1, col2 = st.columns([2, 3])

with col1:
    st.dataframe(
        sector_summary,
        use_container_width=True
    )

with col2:
    fig_leader = px.bar(
        sector_summary,
        x="avg_return",
        y="sector",
        orientation="h",
        color="avg_return",
        color_continuous_scale="RdYlGn",
        title="Sector Strength Ranking"
    )
    st.plotly_chart(fig_leader, use_container_width=True)

# =========================
# TOP MOVERS
# =========================
st.subheader("🚀 Top Movers")

top_n = st.slider("Top N Stocks", 5, 50, 10)

top_movers = filtered_df.sort_values(by="return", ascending=False).head(top_n)

st.dataframe(
    top_movers,
    use_container_width=True
)

# =========================
# SECTOR HEATMAP
# =========================
st.subheader("🔥 Sector Heatmap")

sector_df = filtered_df.groupby("sector").agg(
    stock_count=("symbol", "count"),
    avg_return=("return", "mean")
).reset_index()

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
# FULL TABLE
# =========================
st.subheader("📋 Stock Table")

st.dataframe(
    filtered_df.sort_values(by="return", ascending=False),
    use_container_width=True
)
