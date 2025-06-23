import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64
import requests
from io import StringIO 

# === PAGE CONFIGURATION ===
st.set_page_config(
    page_title="Calibrate DTIMS Data Acquired on Synapt",
    page_icon="📌",
    layout="wide",
    initial_sidebar_state="expanded")

  # === CUSTOM CSS ===
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
        .info-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-left-color: #667eea;
        border-left: 4px solid #667eea;
        border: 1px solid #cbd5e1;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

def main():

    st.markdown("""
    <div class="main-header">
        <h1>Calibrate DTIMS Data Acquired on Synapt</h1>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card">
        <p>Collect together your data (.raw files). The first thing you will need to do is use TWIMExtract to get ATDs for each charge state of the protein. To do this, create a range file for each charge state (detailed instructions can be found <a href="https://github.com/dpolasky/TWIMExtract" target="_blank">here</a>). Call your range files 'protein_X.txt' where protein is the name of the protein and X is the charge state. Use the navigation in TWIMExtract to select your .raw file, and extract using the range files you have created. Make sure 'Combine Ranges' = 'Yes'. This will generate a .csv file which will be used to generate calibrated data. Upload this file below.</p>
    </div>
    """, unsafe_allow_html=True)




if __name__ == "__main__":
    main()
