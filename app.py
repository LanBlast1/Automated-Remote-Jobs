import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path


# Local database used for personal job tracking
LOCAL_DB = Path("jobs.db")

# Sanitized database used for public demo
DEMO_DB = Path("showcase.db")

# Choose local DB if it exists, otherwise use demo DB
if LOCAL_DB.exists():
    DB_PATH = LOCAL_DB
elif DEMO_DB.exists():
    DB_PATH = DEMO_DB
else:
    st.error("No database found. Run main.py locally or commit showcase.db for the demo.")
    st.stop()

st.title("Remote Jobs Dashboard")
con = sqlite3.connect(str(DB_PATH))
query = "SELECT * FROM jobs ORDER BY scraped_at DESC"
df = pd.read_sql_query(query, con)
con.close()

st.sidebar.header("Filters")
tag_filter = st.sidebar.text_input("Tag contains", "").strip()

filtered = df.copy()

if tag_filter:
    filtered = filtered[
        filtered["tags"]
        .fillna("")
        .str.contains(tag_filter, case=False, regex=False)
    ]

st.dataframe(filtered, use_container_width=True)
st.caption(f"Showing {len(filtered)} of {len(df)} rows")