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
        if not feedback.strip():
            st.warning("Please enter some feedback before submitting.")
        else:
            # Define file path
            data_dir = "data"
            csv_path = os.path.join(data_dir, "feedback.csv")
    
            # Make sure data directory exists
            try:
                os.makedirs(data_dir, exist_ok=True)
    
                # Build entry
                new_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "name": name.strip() if name else "Anonymous",
                    "feedback": feedback.replace("\n", " ")
                }
    
                # Append to CSV
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
                else:
                    df = pd.DataFrame([new_entry])
    
                df.to_csv(csv_path, index=False)
                st.success("Thanks for your feedback! It has been recorded.")
            except Exception as e:
                st.error(f"An error occurred while saving your feedback: {e}")

# Hide Streamlit footer
st.markdown(
    "<style>.css-1lsmgbg.e1fqkh3o3 {visibility: hidden;} </style>",
    unsafe_allow_html=True
)
