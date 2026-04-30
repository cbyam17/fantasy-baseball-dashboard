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
st.title("Playground Dashboard")
st.set_page_config(layout="wide")
df_hitter_zscores = load_hitter_zscores()
df_pitcher_zscores = load_pitcher_zscores()

# Hitters table
st.subheader("All Hitters")
score_columns = st.multiselect(
    "Select hitter columns for custom score",
    options=[col for col in df_hitter_zscores.columns if col.startswith("ZSCORE_")],
    default=[]
)
if score_columns:
    df_hitter_zscores["ZSCORE_CUSTOM"] = df_hitter_zscores[score_columns].sum(axis=1).round(1)
if "ZSCORE_CUSTOM" in df_hitter_zscores.columns:
    df_hitter_zscores = df_hitter_zscores.sort_values("ZSCORE_CUSTOM", ascending=False)
st.dataframe(df_hitter_zscores, width='stretch')

# Pitchers table
st.subheader("All Pitchers")
score_columns = st.multiselect(
    "Select pitcher columns for custom score",
    options=[col for col in df_pitcher_zscores.columns if col.startswith("ZSCORE_")],
    default=[]
)
if score_columns:
    df_pitcher_zscores["ZSCORE_CUSTOM"] = df_pitcher_zscores[score_columns].sum(axis=1).round(1)
if "ZSCORE_CUSTOM" in df_pitcher_zscores.columns:
    df_pitcher_zscores = df_pitcher_zscores.sort_values("ZSCORE_CUSTOM", ascending=False)
st.dataframe(df_pitcher_zscores, width='stretch')