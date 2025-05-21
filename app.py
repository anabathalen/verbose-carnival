import streamlit as st
import pandas as pd
import os

from pages.data_visualisation import show_data_visualisation_page
from pages.welcome_page import show_welcome_page

# This is the home page content
st.title("Welcome to My Multi-Page Streamlit App")

st.write("This is the main page. Use the menu on the left to navigate to other pages.")
