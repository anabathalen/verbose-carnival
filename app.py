import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64
import requests

# Page config for professional look
st.set_page_config(
    page_title="Barran Group CCS Tools",
    page_icon="🧪",
    layout="wide"
)

# Custom CSS to clean default Streamlit styling
st.markdown(
    """
    <style>
    .css-1d391kg {padding-top: 1rem;}  /* Reduce top padding */
    .css-hi6a2p {padding: 0 1rem;}    /* Reduce side padding */
    .stButton>button {background-color: #4CAF50; color: white;} /* Green submit button */
    .stTextArea>div>div>textarea {font-family: 'Arial'; font-size: 16px;} /* Text area styling */
    </style>
    """, unsafe_allow_html=True
)

# Main layout containers
header = st.container()
body = st.container()
feedback_section = st.container()

with header:
    st.title("Barran Group CCS Logging & Calibration Tools")
    st.markdown("---")

with body:
    st.write("Welcome! This site hosts tools for logging protein CCS values and processing IM-MS data.")
    st.write("Feel free to explore the tools in the sidebar and provide feedback below!")
    st.info("⚠️ This is a work in progress. Please sanity check all results before use.")

with feedback_section:
    st.markdown("---")
    st.header("User Feedback")

    name = st.text_input("Your name (optional):", max_chars=50)
    feedback = st.text_area("Share your feedback or suggestions:", height=150)
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
                    df = pd.read_csv(pd.compat.StringIO(decoded_content))
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
                    "message": "Add user feedback",
                    "content": encoded_content
                }
                if sha:
                    payload["sha"] = sha

                put_response = requests.put(API_URL, headers=headers, json=payload)
                if put_response.status_code in [200, 201]:
                    st.success("Thanks! Your feedback has been saved to GitHub.")
                else:
                    raise Exception(f"GitHub update error: {put_response.status_code}, {put_response.text}")

            except Exception as e:
                st.error(f"Error saving feedback: {e}")

# Hide Streamlit footer
st.markdown(
    "<style>.css-1lsmgbg.e1fqkh3o3 {visibility: hidden;} </style>",
    unsafe_allow_html=True
)

