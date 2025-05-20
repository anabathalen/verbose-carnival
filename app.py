import streamlit as st
import pandas as pd
import os

from pages.data_visualisation import show_data_visualisation_page

st.set_page_config(
  page_title = "Native IM-MS Data Processing Tools",
  layout = "wide",
  initial_sidebar_state = "expanded"
)

def main():
  
  st.header("Native IM-MS Data Processing Tools")

  with st.sidebar:
      st.header("Natvigation")
      page = st.radio("Select Page", "Data Visualisation")
      st.session_state.page = page
    
  if st.session_state.page == "Data Visualisation":
      show_data_visualisation_page()

if __name__ == "__main__":
    if "page" not in st.session_state:
        st.session_state.page = "Data Visualisation"
    main()
