import streamlit as st
import pandas as pd
from github import Github
from io import StringIO

st.title("📊 View All Protein CCS Data")

# --- Load GitHub secrets ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
CSV_PATH = st.secrets["CSV_PATH"]

# --- Authenticate with GitHub ---
@st.cache_data(ttl=300)
def load_csv_from_github():
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        file_content = repo.get_contents(CSV_PATH)
        csv_string = file_content.decoded_content.decode("utf-8")
        df = pd.read_csv(StringIO(csv_string))
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# --- Load and display the data ---
df = load_csv_from_github()

if df is not None:
    st.success("Data loaded successfully!")
    st.dataframe(df, use_container_width=True)
    # Optional download button
    csv = df.to_csv(index=False)
    st.download_button("📥 Download as CSV", csv, "protein_ccs_data.csv", "text/csv")
else:
    st.warning("No data found or failed to load.")
