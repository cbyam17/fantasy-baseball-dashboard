from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import mysql.connector
import os

#load environment variables from .env file
load_dotenv()

# Get MySQL connection
def get_connection():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")

    )
    return conn

# Load hitter z-scores from MySQL
def load_hitter_zscores():
    conn = get_connection()
    query = "SELECT NAME, TEAM, POS, ZSCORE_R, ZSCORE_HR, ZSCORE_H, ZSCORE_RBI, ZSCORE_SB, ZSCORE_K, ZSCORE_AVG, ZSCORE_OPS, ZSCORE_WMM, ZSCORE_LFL FROM hitter_zscore_view"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Load pitcher z-scores from MySQL
def load_pitcher_zscores():
    conn = get_connection()
    query = "SELECT NAME, TEAM, POS, ZSCORE_W, ZSCORE_L, ZSCORE_QS, ZSCORE_K, ZSCORE_ERA, ZSCORE_WHIP, ZSCORE_SV, ZSCORE_SVHLD,ZSCORE_WMM, ZSCORE_LFL FROM pitcher_zscore_view"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Configure dashboard
st.title("Player Comparison Dashboard")
st.set_page_config(layout="wide")
df_hitter_zscores = load_hitter_zscores()
df_pitcher_zscores = load_pitcher_zscores()

# Hitters section
st.subheader("Hitters")
player_filter = st.multiselect(
    "Search and select hitters:",
    options=sorted(df_hitter_zscores["NAME"].dropna().unique()),
)
if player_filter:
    df_filtered = df_hitter_zscores[df_hitter_zscores["NAME"].isin(player_filter)]
else:
    df_filtered = df_hitter_zscores
st.dataframe(df_filtered, width='stretch')

# Pitchers section
st.subheader("Pitchers")
player_filter = st.multiselect(
    "Search and select pitchers:",
    options=sorted(df_pitcher_zscores["NAME"].dropna().unique()),
)
if player_filter:
    df_filtered = df_pitcher_zscores[df_pitcher_zscores["NAME"].isin(player_filter)]
else:
    df_filtered = df_pitcher_zscores
st.dataframe(df_filtered, width='stretch')