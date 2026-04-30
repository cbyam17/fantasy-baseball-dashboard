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

def get_pitchers_wmm():
    df = pd.read_csv("players/pitchers_wmm.csv")
    pitchers = df["NAME"].dropna().tolist()
    return pitchers

def get_pitchers_lfl():
    df = pd.read_csv("players/pitchers_lfl.csv")
    pitchers = df["NAME"].dropna().tolist()
    return pitchers
    
    
# Load pitcher z-scores from MySQL
def load_pitcher_zscores():
    conn = get_connection()
    query = "SELECT NAME, TEAM, POS, ZSCORE_W, ZSCORE_L, ZSCORE_QS, ZSCORE_K, ZSCORE_ERA, ZSCORE_WHIP, ZSCORE_SV, ZSCORE_SVHLD,ZSCORE_WMM, ZSCORE_LFL FROM pitcher_zscore_view"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Load pitcher z-scores WMM from MySQL
def load_pitcher_zscores_wmm():
    pitchers_wmm = get_pitchers_wmm()
    placeholders = ", ".join(["%s"] * len(pitchers_wmm))
    conn = get_connection()
    query = f"SELECT NAME, TEAM, POS, ZSCORE_W, ZSCORE_L, ZSCORE_QS, ZSCORE_K, ZSCORE_ERA, ZSCORE_WHIP, ZSCORE_SVHLD, ZSCORE_WMM FROM pitcher_zscore_view WHERE NAME IN ({placeholders})"
    df = pd.read_sql(query, conn, params=pitchers_wmm)
    conn.close()
    return df

# Load pitcher z-scores LFL from MySQL
def load_pitcher_zscores_lfl():
    pitchers_lfl = get_pitchers_lfl()
    placeholders = ", ".join(["%s"] * len(pitchers_lfl))
    conn = get_connection()
    query = f"SELECT NAME, TEAM, POS, ZSCORE_W, ZSCORE_QS, ZSCORE_K, ZSCORE_ERA, ZSCORE_WHIP, ZSCORE_SV, ZSCORE_LFL FROM pitcher_zscore_view WHERE NAME IN ({placeholders})"
    df = pd.read_sql(query, conn, params=pitchers_lfl)
    conn.close()
    return df

# Configure Dashboard
st.title("Pitchers ROS Z-SCORE Dashboard")
positions = ["All", "SP", "RP"]
st.set_page_config(layout="wide")
df_pitcher_zscores_wmm = load_pitcher_zscores_wmm()
df_pitcher_zscores_lfl = load_pitcher_zscores_lfl()

# WMM pitchers Table
st.subheader("Walter Matthau Memorial Pitchers")
position_filter_wmm = st.selectbox("Select Position WMM", positions)
if position_filter_wmm != "All":
    df_pitcher_zscores_wmm = df_pitcher_zscores_wmm[df_pitcher_zscores_wmm["POS"].str.contains(position_filter_wmm, na=False)]
st.dataframe(df_pitcher_zscores_wmm, width='stretch')

# LFL pitchers Table
st.subheader("Lion's Field Legends Pitchers")
position_filter_lfl = st.selectbox("Select Position LFL", positions)
if position_filter_lfl != "All":
    df_pitcher_zscores_lfl = df_pitcher_zscores_lfl[df_pitcher_zscores_lfl["POS"].str.contains(position_filter_lfl, na=False)]
st.dataframe(df_pitcher_zscores_lfl, width='stretch')