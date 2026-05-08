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

# Load hitter and pitcher names from CSV files
def get_hitters_wmm():
    df = pd.read_csv("players/hitters_wmm.csv")
    hitters = df["NAME"].dropna().tolist()
    return hitters

def get_hitters_lfl():
    df = pd.read_csv("players/hitters_lfl.csv")
    hitters = df["NAME"].dropna().tolist()
    return hitters

def get_pitchers_wmm():
    df = pd.read_csv("players/pitchers_wmm.csv")
    pitchers = df["NAME"].dropna().tolist()
    return pitchers

def get_pitchers_lfl():
    df = pd.read_csv("players/pitchers_lfl.csv")
    pitchers = df["NAME"].dropna().tolist()
    return pitchers
    
# Load all hitter z-scores from MySQL
def load_hitter_zscores():
    conn = get_connection()
    query = "SELECT NAME, TEAM, POS, ZSCORE_R, ZSCORE_HR, ZSCORE_H, ZSCORE_RBI, ZSCORE_SB, ZSCORE_K, ZSCORE_AVG, ZSCORE_OPS, ZSCORE_WMM, ZSCORE_LFL FROM hitter_zscore_view"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Load WMM hitter z-scores from MySQL
def load_hitter_zscores_wmm():
    hitters_wmm = get_hitters_wmm()
    placeholders = ", ".join(["%s"] * len(hitters_wmm))
    conn = get_connection()
    query = f"SELECT NAME, TEAM, POS, ZSCORE_R, ZSCORE_HR, ZSCORE_H, ZSCORE_RBI, ZSCORE_SB, ZSCORE_K, ZSCORE_AVG, ZSCORE_OPS, ZSCORE_WMM FROM hitter_zscore_view WHERE NAME IN ({placeholders})"
    df = pd.read_sql(query, conn, params=hitters_wmm)
    conn.close()
    return df

# Load LFL hitter z-scores from MySQL
def load_hitter_zscores_lfl():
    hitters_lfl = get_hitters_lfl()
    placeholders = ", ".join(["%s"] * len(hitters_lfl))
    conn = get_connection()
    query = f"SELECT NAME, TEAM, POS, ZSCORE_R, ZSCORE_HR, ZSCORE_H, ZSCORE_RBI, ZSCORE_SB, ZSCORE_K, ZSCORE_AVG, ZSCORE_OPS, ZSCORE_LFL FROM hitter_zscore_view WHERE NAME IN ({placeholders})"
    df = pd.read_sql(query, conn, params=hitters_lfl)
    conn.close()
    return df
    
# Load all pitcher z-scores from MySQL
def load_pitcher_zscores():
    conn = get_connection()
    query = "SELECT NAME, TEAM, POS, ZSCORE_W, ZSCORE_L, ZSCORE_QS, ZSCORE_K, ZSCORE_ERA, ZSCORE_WHIP, ZSCORE_SV, ZSCORE_SVHLD,ZSCORE_WMM, ZSCORE_LFL FROM pitcher_zscore_view"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Load WMM pitcher z-scores from MySQL
def load_pitcher_zscores_wmm():
    pitchers_wmm = get_pitchers_wmm()
    placeholders = ", ".join(["%s"] * len(pitchers_wmm))
    conn = get_connection()
    query = f"SELECT NAME, TEAM, POS, ZSCORE_W, ZSCORE_L, ZSCORE_QS, ZSCORE_K, ZSCORE_ERA, ZSCORE_WHIP, ZSCORE_SVHLD, ZSCORE_WMM FROM pitcher_zscore_view WHERE NAME IN ({placeholders})"
    df = pd.read_sql(query, conn, params=pitchers_wmm)
    conn.close()
    return df

# Load LFL pitcher z-scores from MySQL
def load_pitcher_zscores_lfl():
    pitchers_lfl = get_pitchers_lfl()
    placeholders = ", ".join(["%s"] * len(pitchers_lfl))
    conn = get_connection()
    query = f"SELECT NAME, TEAM, POS, ZSCORE_W, ZSCORE_QS, ZSCORE_K, ZSCORE_ERA, ZSCORE_WHIP, ZSCORE_SV, ZSCORE_LFL FROM pitcher_zscore_view WHERE NAME IN ({placeholders})"
    df = pd.read_sql(query, conn, params=pitchers_lfl)
    conn.close()
    return df

# Configure Dashboard
st.title("Fantasy Baseball Dashboard")
positions_h = ["All", "DH", "1B", "2B", "3B", "OF", "SS"]
positions_p = ["All", "SP", "RP"]
st.set_page_config(layout="wide")

# Load all z-scores for hitters and pitchers
df_hitter_zscores = load_hitter_zscores()
df_hitter_zscores_wmm = load_hitter_zscores_wmm()
df_hitter_zscores_lfl = load_hitter_zscores_lfl()
df_pitcher_zscores = load_pitcher_zscores()
df_pitcher_zscores_wmm = load_pitcher_zscores_wmm()
df_pitcher_zscores_lfl = load_pitcher_zscores_lfl()

# WMM Hitters Table
st.subheader("Walter Matthau Memorial Hitters")
position_filter_wmm = st.selectbox("Select Position WMM", positions_h)
if position_filter_wmm != "All":
    df_hitter_zscores_wmm = df_hitter_zscores_wmm[df_hitter_zscores_wmm["POS"].str.contains(position_filter_wmm, na=False)]
st.dataframe(df_hitter_zscores_wmm, width='stretch')

# LFL Hitters Table
st.subheader("Lion's Field Legends Hitters")
position_filter_lfl = st.selectbox("Select Position LFL", positions_h)
if position_filter_lfl != "All":
    df_hitter_zscores_lfl = df_hitter_zscores_lfl[df_hitter_zscores_lfl["POS"].str.contains(position_filter_lfl, na=False)]
st.dataframe(df_hitter_zscores_lfl, width='stretch')

# WMM pitchers Table
st.subheader("Walter Matthau Memorial Pitchers")
position_filter_wmm = st.selectbox("Select Position WMM", positions_p)
if position_filter_wmm != "All":
    df_pitcher_zscores_wmm = df_pitcher_zscores_wmm[df_pitcher_zscores_wmm["POS"].str.contains(position_filter_wmm, na=False)]
st.dataframe(df_pitcher_zscores_wmm, width='stretch')

# LFL pitchers Table
st.subheader("Lion's Field Legends Pitchers")
position_filter_lfl = st.selectbox("Select Position LFL", positions_p)
if position_filter_lfl != "All":
    df_pitcher_zscores_lfl = df_pitcher_zscores_lfl[df_pitcher_zscores_lfl["POS"].str.contains(position_filter_lfl, na=False)]
st.dataframe(df_pitcher_zscores_lfl, width='stretch')

# Player Comparison Section
st.subheader("Hitters Comparison")

# Define filters
player_filter_hitter = st.multiselect(
    "Search and select hitters:",
    options=sorted(df_hitter_zscores["NAME"].dropna().unique()),
)
score_columns = st.multiselect(
    "Select hitter columns for custom score",
    options=[col for col in df_hitter_zscores.columns if col.startswith("ZSCORE_")],
    default=[]
)

# Filter hitters based on selection
if player_filter_hitter:
    df_hitter_filtered = df_hitter_zscores[df_hitter_zscores["NAME"].isin(player_filter_hitter)]
else:
    df_hitter_filtered = df_hitter_zscores

# Calculate custom score if columns are selected
if score_columns:
    df_hitter_filtered["ZSCORE_CUSTOM"] = df_hitter_filtered[score_columns].sum(axis=1).round(1)
if "ZSCORE_CUSTOM" in df_hitter_filtered.columns:
    df_hitter_filtered = df_hitter_filtered.sort_values("ZSCORE_CUSTOM", ascending=False)

# generate hitter table
st.dataframe(df_hitter_filtered, width='stretch')

# Pitchers section
st.subheader("Pitchers Comparison")

# Define filters
player_filter_pitcher = st.multiselect(
    "Search and select pitchers:",
    options=sorted(df_pitcher_zscores["NAME"].dropna().unique()),
)
score_columns = st.multiselect(
    "Select pitcher columns for custom score",
    options=[col for col in df_pitcher_zscores.columns if col.startswith("ZSCORE_")],
    default=[]
)

# Filter pitchers based on selection
if player_filter_pitcher:
    df_pitcher_filtered = df_pitcher_zscores[df_pitcher_zscores["NAME"].isin(player_filter_pitcher)]
else:
    df_pitcher_filtered = df_pitcher_zscores

# Calculate custom score if columns are selected
if score_columns:
    df_pitcher_filtered["ZSCORE_CUSTOM"] = df_pitcher_filtered[score_columns].sum(axis=1).round(1)
if "ZSCORE_CUSTOM" in df_pitcher_filtered.columns:
    df_pitcher_filtered = df_pitcher_filtered.sort_values("ZSCORE_CUSTOM", ascending=False)

# generate pitcher table
st.dataframe(df_pitcher_filtered, width='stretch')