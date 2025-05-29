import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64
import requests
from io import StringIO 

# Page config for professional look
st.set_page_config(
    page_title="Home",
    page_icon="🧪",
    layout="wide"
)

# Clean, minimal CSS styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    /* Clean font styling */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Clean title styling */
    .main-title {
        color: #1f2937;
        font-size: 2.5rem;
        font-weight: 600;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #6b7280;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Simple button styling */
    .stButton > button {
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: background-color 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #2563eb;
    }
    
    /* Clean input styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 6px;
        border: 1px solid #d1d5db;
        font-family: 'Inter', sans-serif;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 1px #3b82f6;
    }
    
    /* Section headers */
    .section-header {
        color: #1f2937;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
    }
    
    /* Info box styling */
    .info-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .warning-box {
        background-color: #fffbeb;
        border: 1px solid #fed7aa;
        border-left: 4px solid #f59e0b;
        border-radius: 6px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Clean table styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Hide default Streamlit elements */
    .css-1d391kg {padding-top: 1rem;}
    .css-hi6a2p {padding: 0 1rem;}
    .css-1lsmgbg.e1fqkh3o3 {display: none;}
    header[data-testid="stHeader"] {display: none;}
    .stDeployButton {display: none;}
    </style>
    """, unsafe_allow_html=True
)

# Main layout containers
header = st.container()
body = st.container()
guide = st.container()
feedback_section = st.container()

with header:
    st.markdown('<h1 class="main-title">Barran Group CCS Logging and Processing Tools</h1>', unsafe_allow_html=True)
    st.markdown("---")

with body:
    st.markdown("""
    <div class="info-box">
        <p><strong>Welcome!</strong> This site hosts tools for logging protein CCS values and processing IM-MS data.</p>
        <p>Please use the tools in the sidebar and provide feedback below!</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="warning-box">
        <strong>⚠️ Work in Progress</strong><br>
        Please sanity check all results before use.
    </div>
    """, unsafe_allow_html=True)

with guide:
    st.markdown('<h2 class="section-header">📋 Site Guide</h2>', unsafe_allow_html=True)
    st.write("Use the table below to find the pages you need:")

    # Define your guide table data
    guide_data = {
        "Page Name": [
            "app",
            "ccs logging",
            "view data",
            "calibrate",
            "get input files",
            "process output files",
            "process and plot IMS",
            "fit major peaks"
        ],
        "Description": [
            "Home page and feedback.",
            "Log protein CCS values from papers.",
            "View logged CCS values (and leaderboard!)",
            "Process calibrant data and export to IMSCal reference file and/or csv.",
            "Generate IMSCal input files from ATDs and masses.",
            "Process IMSCal output files to get arrival time ⇒ CCS conversions for your proteins.",
            "Use arrival time ⇒ CCS conversions from 'process output files' to process and plot IMS data.",
            "Fits major peaks in your data according to inputted parameters."
        ]
    }
    
    guide_df = pd.DataFrame(guide_data)
    st.dataframe(guide_df, use_container_width=True, hide_index=True)

with feedback_section:
    st.markdown("---")
    st.markdown('<h2 class="section-header">💬 User Feedback</h2>', unsafe_allow_html=True)

    name = st.text_input("Name:", max_chars=50, placeholder="Your name (optional)")
    feedback = st.text_area("Share your feedback or suggestions:", height=120, placeholder="Enter your feedback here...")
    
    submit = st.button("Submit Feedback")

    if submit:
        if not feedback.strip():
            st.warning("Please enter some feedback before submitting.")
        else:
            try:
                # Load GitHub credentials
                GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
                GITHUB_REPO = st.secrets["REPO_NAME"]

                # Constants
                CSV_PATH = "data/feedback.csv"
                API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{CSV_PATH}"

                # Create entry
                new_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "name": name.strip() if name else "Anonymous",
                    "feedback": feedback.replace("\n", " ")
                }

                # Get current CSV content from GitHub
                headers = {
                    "Authorization": f"token {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github+json"
                }

                response = requests.get(API_URL, headers=headers)
                if response.status_code == 200:
                    content_json = response.json()
                    sha = content_json["sha"]
                    decoded_content = base64.b64decode(content_json["content"]).decode("utf-8")
                    df = pd.read_csv(StringIO(decoded_content))
                    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
                elif response.status_code == 404:
                    sha = None
                    df = pd.DataFrame([new_entry])
                else:
                    raise Exception(f"GitHub API error: {response.status_code}, {response.text}")

                # Encode and push new content
                updated_csv = df.to_csv(index=False)
                encoded_content = base64.b64encode(updated_csv.encode()).decode()

                payload = {
                    "message": "Added user feedback",
                    "content": encoded_content
                }
                if sha:
                    payload["sha"] = sha

                put_response = requests.put(API_URL, headers=headers, json=payload)
                if put_response.status_code in [200, 201]:
                    st.success("Thanks! Your feedback has been saved.")
                else:
                    raise Exception(f"GitHub update error: {put_response.status_code}, {put_response.text}")

            except Exception as e:
                st.error(f"Error saving feedback: {e}")
