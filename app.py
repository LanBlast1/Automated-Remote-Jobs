import streamlit as st
import pandas as pd
import sqlite3

st.title("Remote Jobs Dashboard")

con = sqlite3.connect("jobs.db")
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