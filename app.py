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
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS styling matching CCS logging page
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 600;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    .section-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    .section-header {
        color: #667eea;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1rem;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
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
    
    .warning-card {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-left-color: #f59e0b;
        border-left: 4px solid #f59e0b;
        border: 1px solid #fed7aa;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-radius: 10px;
    }
    
    .guide-section {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #cbd5e1;
        margin: 1rem 0;
    }
    
    .feedback-section {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin: 2rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    /* Enhanced Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 500;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Form Input Styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 1px solid #d1d5db;
        font-family: 'Inter', sans-serif;
        padding: 0.5rem;
        transition: border-color 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }
    
    /* Table Styling */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Success/Error message styling */
    .success-message {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border-left: 4px solid #22c55e;
        border: 1px solid #bbf7d0;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .error-message {
        background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
        border-left: 4px solid #ef4444;
        border: 1px solid #fca5a5;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .warning-message {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-left: 4px solid #f59e0b;
        border: 1px solid #fed7aa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    /* Hide default elements */
    header[data-testid="stHeader"] {display: none;}
    .stDeployButton {display: none;}
    .css-1lsmgbg.e1fqkh3o3 {display: none;}
    .css-1d391kg {padding-top: 1rem;}
    .css-hi6a2p {padding: 0 1rem;}
</style>
""", unsafe_allow_html=True)

# Main layout containers
header = st.container()
body = st.container()
guide = st.container()
feedback_section = st.container()

with header:
    st.markdown("""
    <div class="main-header">
        <h1>!!NAME!! CCS Logging and Processing Tools</h1>
        <p>Advanced tools for protein CCS analysis and IM-MS data processing</p>
    </div>
    """, unsafe_allow_html=True)

with body:
    st.markdown("""
    <div class="info-card">
        <p><strong>Welcome!</strong> This site hosts tools for logging protein CCS values and processing IM-MS data. Some stuff about why we are doing this (expanding on beveridge paper, deveoping compendium of protein CCS values hoping to understand how structure links to CCS more closely.) Building on McLean/Bush - but protein data is harder, is it native?</p>
        <p>Please use the tools in the sidebar and provide feedback below!</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="warning-card">
        <strong>⚠️ Work in Progress</strong><br>
        Please sanity check all results before use.
    </div>
    """, unsafe_allow_html=True)

with guide:
    st.markdown("""
    <div class="section-card">
        <h2 class="section-header">📋 Site Guide</h2>
        <p>Use the table below to find the pages you need:</p>
    """, unsafe_allow_html=True)

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
    
    st.markdown("</div>", unsafe_allow_html=True)

with feedback_section:
    st.markdown("""
    <div class="feedback-section">
        <h2 class="section-header">💬 User Feedback</h2>
    """, unsafe_allow_html=True)

    name = st.text_input("Name:", max_chars=50, placeholder="Your name (optional)")
    feedback = st.text_area("Share your feedback or suggestions:", height=120, placeholder="Enter your feedback here...")
    
    submit = st.button("Submit Feedback")

    if submit:
        if not feedback.strip():
            st.markdown("""
            <div class="warning-message">
                <strong>⚠️ Please enter some feedback before submitting.</strong>
            </div>
            """, unsafe_allow_html=True)
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
                    st.markdown("""
                    <div class="success-message">
                        <strong>✅ Thanks! Your feedback has been saved.</strong>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    raise Exception(f"GitHub update error: {put_response.status_code}, {put_response.text}")

            except Exception as e:
                st.markdown(f"""
                <div class="error-message">
                    <strong>❌ Error saving feedback:</strong> {e}
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
