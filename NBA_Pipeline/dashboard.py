import streamlit as st
import pandas as pd
from etl_pipeline import run_etl
import plotly.graph_objects as go

st.title("NBA Analytics Dashboard")

# Single Player Section
st.header("🔍 Player Search")

player_name = st.text_input("Enter Player Name")

if player_name:

    key = run_etl(player_name)
    games = pd.read_csv(f"data/lake/{key}_games.csv")
    summary = pd.read_csv(f"data/lake/{key}_summary.csv")

# Display Dashboard
    st.subheader("📊 Summary")
    st.dataframe(summary.reset_index(drop=True))
    st.subheader("📈 Rolling Avg Points")
    st.line_chart(games.sort_values("GAME_DATE")["rolling_5_avg_pts"])
    st.subheader("📋 Game Log")
    st.dataframe(games)

st.divider()

# Player Comparison
st.header("⚔️ Player Comparison")

col1, col2 = st.columns(2)
player_a = col1.text_input("Player A")
player_b = col2.text_input("Player B")

if st.button("Compare Players"):
    if not player_a or not player_b:
        st.error("Enter both players")
        st.stop()
    key_a = run_etl(player_a)
    key_b = run_etl(player_b)
    a = pd.read_csv(f"data/lake/{key_a}_summary.csv").iloc[0]
    b = pd.read_csv(f"data/lake/{key_b}_summary.csv").iloc[0]

    comparison = pd.DataFrame({
        "Stat": [
            "Avg Points",
            "Avg Rebounds",
            "Avg Assists",
            "Career High",
            "Career Low",
            "Consistency"
        ],
        player_a: [
            round(a["avg_pts"], 2),
            round(a["avg_reb"], 2),
            round(a["avg_ast"], 2),
            round(a["career_high"], 2),
            round(a["career_low"], 2),
            round(a["consistency"], 2)
        ],
        player_b: [
            round(b["avg_pts"], 2),
            round(b["avg_reb"], 2),
            round(b["avg_ast"], 2),
            round(b["career_high"], 2),
            round(b["career_low"], 2),
            round(b["consistency"], 2)
        ]
    })

# Display Dashboard For Comparison
    st.subheader("📊 Player Comparison")
    st.dataframe(comparison.reset_index(drop=True))
    st.subheader("📈 Visual Comparison")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=player_a,
        x=comparison["Stat"],
        y=comparison[player_a]
    ))
    fig.add_trace(go.Bar(
        name=player_b,
        x=comparison["Stat"],
        y=comparison[player_b]
    ))
    fig.update_layout(
        barmode="group",
        title="Player Comparison",
        xaxis_title="Stats",
        yaxis_title="Value"
    )
    st.plotly_chart(fig, use_container_width=True)

# Created By Michael
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; padding: 20px;'>"
    "Created by Michael"
    "</div>",
    unsafe_allow_html=True
)