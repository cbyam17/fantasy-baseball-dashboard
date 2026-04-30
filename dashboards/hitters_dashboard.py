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

def get_hitters_wmm():
    df = pd.read_csv("players/hitters_wmm.csv")
    hitters = df["NAME"].dropna().tolist()
    return hitters

def get_hitters_lfl():
    df = pd.read_csv("players/hitters_lfl.csv")
    hitters = df["NAME"].dropna().tolist()
    return hitters
    
    
# Load hitter z-scores from MySQL
def load_hitter_zscores():
    conn = get_connection()
    query = "SELECT NAME, TEAM, POS, ZSCORE_R, ZSCORE_HR, ZSCORE_H, ZSCORE_RBI, ZSCORE_SB, ZSCORE_K, ZSCORE_AVG, ZSCORE_OPS, ZSCORE_WMM, ZSCORE_LFL FROM hitter_zscore_view"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Load hitter z-scores WMM from MySQL
def load_hitter_zscores_wmm():
    hitters_wmm = get_hitters_wmm()
    placeholders = ", ".join(["%s"] * len(hitters_wmm))
    conn = get_connection()
    query = f"SELECT NAME, TEAM, POS, ZSCORE_R, ZSCORE_HR, ZSCORE_H, ZSCORE_RBI, ZSCORE_SB, ZSCORE_K, ZSCORE_AVG, ZSCORE_OPS, ZSCORE_WMM FROM hitter_zscore_view WHERE NAME IN ({placeholders})"
    df = pd.read_sql(query, conn, params=hitters_wmm)
    conn.close()
    return df

# Load hitter z-scores LFL from MySQL
def load_hitter_zscores_lfl():
    hitters_lfl = get_hitters_lfl()
    placeholders = ", ".join(["%s"] * len(hitters_lfl))
    conn = get_connection()
    query = f"SELECT NAME, TEAM, POS, ZSCORE_R, ZSCORE_HR, ZSCORE_H, ZSCORE_RBI, ZSCORE_SB, ZSCORE_K, ZSCORE_AVG, ZSCORE_OPS, ZSCORE_LFL FROM hitter_zscore_view WHERE NAME IN ({placeholders})"
    df = pd.read_sql(query, conn, params=hitters_lfl)
    conn.close()
    return df

# Configure Dashboard
st.title("Hitters ROS Z-SCORE Dashboard")
positions = ["All", "DH", "1B", "2B", "3B", "OF", "SS"]
st.set_page_config(layout="wide")
df_hitter_zscores = load_hitter_zscores()
df_hitter_zscores_wmm = load_hitter_zscores_wmm()
df_hitter_zscores_lfl = load_hitter_zscores_lfl()

# All Hitters Table
st.subheader("All Hitters")
position_filter = st.selectbox("Select Position", positions)
if position_filter != "All":
    df_hitter_zscores = df_hitter_zscores[df_hitter_zscores["POS"].str.contains(position_filter, na=False)]
st.dataframe(df_hitter_zscores, width='stretch')

# WMM Hitters Table
st.subheader("Walter Matthau Memorial Hitters")
position_filter_wmm = st.selectbox("Select Position WMM", positions)
if position_filter_wmm != "All":
    df_hitter_zscores_wmm = df_hitter_zscores_wmm[df_hitter_zscores_wmm["POS"].str.contains(position_filter_wmm, na=False)]
st.dataframe(df_hitter_zscores_wmm, width='stretch')

# LFL Hitters Table
st.subheader("Lion's Field Legends Hitters")
position_filter_lfl = st.selectbox("Select Position LFL", positions)
if position_filter_lfl != "All":
    df_hitter_zscores_lfl = df_hitter_zscores_lfl[df_hitter_zscores_lfl["POS"].str.contains(position_filter_lfl, na=False)]
st.dataframe(df_hitter_zscores_lfl, width='stretch')

#Example chart
#st.bar_chart(df_hitter_zscores[["NAME", "ZSCORE_HR"]].set_index("NAME").head(20))