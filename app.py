import streamlit as st
import pandas as pd
import os

# This is the home page content
st.title("Welcome to My Multi-Page Streamlit App")

st.write("This is the main page. Use the menu on the left to navigate to other pages.")

st.write("Loaded secrets:")
st.write(st.secrets.keys())

# Optional: print the token length (not the token itself!)
if "GITHUB_TOKEN" in st.secrets:
    st.success(f"GITHUB_TOKEN loaded (length: {len(st.secrets['GITHUB_TOKEN'])})")
else:
    st.error("GITHUB_TOKEN is missing in secrets.")
