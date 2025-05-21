import streamlit as st
import pandas as pd
import os

from pages.data_visualisation import show_data_visualisation_page
from pages.welcome_page import show_welcome_page

# Initialize session state if needed
if "page" not in st.session_state:
  st.session_state.page = "Welcome"

with st.sidebar:
  st.header("Navigation")
  selected_page = st.radio(
    "Select Page", 
    ["Welcome", "Data Visualisation"],
    key="page_selection",
    index = 0 if st.session_state.page == "Welcome" else 1
  )
