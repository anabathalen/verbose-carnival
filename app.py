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
    st.session_state.page = "Data Visualisation"

# Page title - moved outside of any function
page_title = "Native IM-MS Data Processing Tools"
st.header(page_title)

# Sidebar navigation - moved outside of functions to ensure it always shows
with st.sidebar:
    st.header("Navigation")
    selected_page = st.radio(
        "Select Page", 
        ["Data Visualisation"],
        key="page_selection"  # Unique key for the radio button
    )
    
    # Update session state with the selected page
    st.session_state.page = selected_page

# Display the selected page based on session state
if st.session_state.page == "Data Visualisation":
    show_data_visualisation_page()
