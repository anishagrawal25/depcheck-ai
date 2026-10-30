import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="depcheck-ai", layout="wide")
st.title("depcheck-ai")

code = st.text_area("Enter Python code to scan", height=200)

if st.button("Scan"):
    if not code.strip():
        st.warning("Please enter some Python code to scan.")
    else:
        try:
            response = requests.post(f"{API_URL}/scan", json={"code": code}, timeout=10)
            if response.status_code == 200:
                st.subheader("Raw JSON Output")
                st.json(response.json())
            else:
                st.error(f"Error {response.status_code}: {response.text}")
        except requests.RequestException as e:
            st.error(f"Failed to connect to API: {e}")
