import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="MLB Analytics MVP", layout="wide")

st.title("MLB Analytics MVP Dashboard")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Standings")
    season = st.number_input("Season", min_value=1900, max_value=2100, value=2024)
    if st.button("Load Standings"):
        try:
            r = requests.get(f"{API_URL}/standings", params={"season": season})
            r.raise_for_status()
            st.json(r.json())
        except Exception as e:
            st.error(f"Failed to load standings: {e}")

with col2:
    st.subheader("Leaders")
    category = st.selectbox("Category", [
        "homeRuns", "avg", "rbi", "era", "strikeOuts"
    ])
    limit = st.slider("Limit", 1, 50, 10)
    if st.button("Load Leaders"):
        try:
            r = requests.get(f"{API_URL}/leaders/{category}", params={"limit": limit})
            r.raise_for_status()
            st.json(r.json())
        except Exception as e:
            st.error(f"Failed to load leaders: {e}")
