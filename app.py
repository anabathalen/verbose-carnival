import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Page config for professional look
st.set_page_config(
    page_title="Home",
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
    .stTextArea>div>div>textarea {font-size: 16px;} /* Text area styling */
    </style>
    """, unsafe_allow_html=True
)

# Main layout containers
header = st.container()
body = st.container()
feedback_section = st.container()

with header:
    st.title("Barran Group CCS Logging & Calibration Tools 🧰")
    st.markdown(
        "---"
    )

with body:
    st.write(
        "Welcome! This site hosts tools for logging protein CCS values and processing IM-MS data."
    )
    st.write(
        "Please use the tools in the sidebar and provide feedback below!"
    )
    st.info(
        "⚠️ This is a work in progress. Please sanity check all results before use."
    )

with feedback_section:
    st.markdown("---")
    st.header("Feedback")
    name = st.text_input("Name:")
    feedback = st.text_area("Share your feedback or suggestions:", height=150)
    submit = st.button("Submit Feedback")

    if submit:
        # Ensure feedback.csv exists
        csv_path = "feedback.csv"
        new_entry = {
            "timestamp": datetime.now().isoformat(),
            "name": name.strip() if name else "Anonymous",
            "feedback": feedback.replace("\n", " ")
        }
        # Append to CSV
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            df = df.append(new_entry, ignore_index=True)
        else:
            df = pd.DataFrame([new_entry])
        df.to_csv(csv_path, index=False)

        st.success("Thanks for your feedback! It has been recorded.")

# Hide Streamlit footer
st.markdown(
    "<style>.css-1lsmgbg.e1fqkh3o3 {visibility: hidden;} </style>",
    unsafe_allow_html=True
)
