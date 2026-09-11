import streamlit as st
import pandas as pd
import sqlite3

st.title("Remote Jobs Dashboard")
con = sqlite3.connect("jobs.db")
cur = con.cursor()
query = "SELECT * FROM jobs"
df = pd.read_sql_query(query, con)
st.dataframe(df, width="content", height="content")
