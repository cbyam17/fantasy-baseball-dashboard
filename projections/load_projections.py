from dotenv import load_dotenv
import os
import pandas as pd
import mysql.connector

load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


def load(csv_file, table, column_mapping):
    df = pd.read_csv(csv_file)
    print(f"CSV loaded: {csv_file} — shape {df.shape}")

    df = df[list(column_mapping.keys())]
    df.rename(columns=column_mapping, inplace=True)
    df = df.where(pd.notnull(df), None)

    conn = get_connection()
    cursor = conn.cursor()

    print(f"Truncating {table}...")
    cursor.execute(f"TRUNCATE TABLE {table}")
    conn.commit()

    columns = ", ".join([f"`{col}`" for col in df.columns])
    placeholders = ", ".join(["%s"] * len(df.columns))
    insert_sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    data = df.values.tolist()
    batch_size = 1000
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        cursor.executemany(insert_sql, batch)
        conn.commit()
        print(f"  Inserted rows {i} to {i + len(batch)}")

    cursor.close()
    conn.close()
    print(f"Done: {table}")


HITTER_MAPPING = {
    "#": "ID",
    "Name": "NAME",
    "Team": "TEAM",
    "Y!": "POS",
    "R": "R",
    "H": "H",
    "HR": "HR",
    "RBI": "RBI",
    "SB": "SB",
    "SO": "K",
    "AVG": "AVG",
    "OPS": "OPS",
}

PITCHER_MAPPING = {
    "#": "ID",
    "Name": "NAME",
    "Team": "TEAM",
    "Y!": "POS",
    "QS": "QS",
    "W": "W",
    "L": "L",
    "SV": "SV",
    "HLD": "HLD",
    "ERA": "ERA",
    "WHIP": "WHIP",
    "K": "K",
}

load("projections/hitter_projections.csv", "hitter_projections", HITTER_MAPPING)
load("projections/pitcher_projections.csv", "pitcher_projections", PITCHER_MAPPING)

print("✅ All projections loaded.")
