import streamlit as st
import pandas as pd
import os

from pages.data_visualisation import show_data_visualisation_page

st.set_page_config(
  page_title = "Native IM-MS Data Processing Tools",
  layout = "wide",
  initial_sidebar_state = "expanded"
)

# Initialize session state if needed
if "page" not in st.session_state:
  st.session_state.page = "Welcome"

st.header("Native IM-MS Data Processing Tools")

with st.sidebar:
    st.header("Navigation")
    selected_page = st.radio(
      "Select Page", 
      ["Welcome", "Data Visualisation"],
      key="page_selection",
      index = 0 if st.session_state.page == "Welcome" else 1
    )
    
    # Update session state with the selected page
    st.session_state.page = selected_page

if st.session_state.page == "Welcome":
  show_welcome_page()
elif st.session_state.page == "Data Visualisation":
  show_data_visualisation_page()
