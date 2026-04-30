from dotenv import load_dotenv
import os
import pandas as pd
import mysql.connector

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

# =========================
# 2. LOAD CSV INTO DATAFRAME
# =========================
csv_file = "projections/pitcher_projections.csv"

df = pd.read_csv(csv_file)

print("CSV Loaded. Shape:", df.shape)


# =========================
# 3. SOURCE → TARGET MAPPING
# (based on mapping file)
# =========================
column_mapping = {
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

# Keep only mapped columns
df = df[list(column_mapping.keys())]

# Rename columns to match MySQL table
df.rename(columns=column_mapping, inplace=True)


# =========================
# 4. HANDLE NaN VALUES
# =========================
df = df.where(pd.notnull(df), None)


# =========================
# 5. INSERT INTO MYSQL
# =========================
conn = get_connection()
cursor = conn.cursor()

# Build dynamic insert query
columns = ", ".join([f"`{col}`" for col in df.columns])
placeholders = ", ".join(["%s"] * len(df.columns))

insert_sql = f"""
INSERT INTO pitcher_projections ({columns})
VALUES ({placeholders})
"""

print("Starting insert...")

batch_size = 1000
data = df.values.tolist()

for i in range(0, len(data), batch_size):
    batch = data[i:i + batch_size]
    cursor.executemany(insert_sql, batch)
    conn.commit()
    print(f"Inserted rows {i} to {i + len(batch)}")

cursor.close()
conn.close()

print("✅ Data load complete!")