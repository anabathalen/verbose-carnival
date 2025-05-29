import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64
import requests
from io import StringIO
import hashlib

# Page config for professional look
st.set_page_config(
    page_title="Barran Group CCS Tools",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# Enhanced CSS styling matching modern Streamlit designs
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styling */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Hide default Streamlit elements */
    .css-1d391kg {padding-top: 1rem;}
    .css-hi6a2p {padding: 0 1rem;}
    .css-1lsmgbg.e1fqkh3o3 {display: none;}
    header[data-testid="stHeader"] {display: none;}
    .stDeployButton {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Login container */
    .login-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 3rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        max-width: 400px;
        margin: 4rem auto;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Main content container */
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Title styling */
    .main-title {
        color: #1a202c;
        font-size: 2.8rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .login-title {
        color: #1a202c;
        font-size: 2.2rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .subtitle {
        color: #4a5568;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Welcome user styling */
    .welcome-user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        text-align: center;
        font-weight: 500;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Logout button styling */
    .logout-btn {
        background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%) !important;
        box-shadow: 0 4px 15px rgba(245, 101, 101, 0.3) !important;
    }
    
    .logout-btn:hover {
        box-shadow: 0 6px 20px rgba(245, 101, 101, 0.4) !important;
    }
    
    /* Input styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        font-family: 'Inter', sans-serif;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
        background: rgba(255, 255, 255, 0.8);
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        background: white;
    }
    
    /* Section headers */
    .section-header {
        color: #1a202c;
        font-size: 1.8rem;
        font-weight: 600;
        margin: 2rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(135deg, #e6fffa 0%, #b2f5ea 100%);
        border: 1px solid #81e6d9;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 15px rgba(129, 230, 217, 0.2);
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fffbeb 0%, #fef5e7 100%);
        border: 1px solid #f6ad55;
        border-left: 4px solid #ed8936;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 15px rgba(246, 173, 85, 0.2);
    }
    
    .success-box {
        background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
        border: 1px solid #68d391;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 15px rgba(104, 211, 145, 0.2);
    }
    
    .error-box {
        background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
        border: 1px solid #fc8181;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 15px rgba(252, 129, 129, 0.2);
    }
    
    /* Table styling */
    .stDataFrame {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Custom divider */
    .custom-divider {
        height: 2px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 2px;
        margin: 2rem 0;
    }
    
    /* Animated elements */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.2rem;
        }
        
        .login-container,
        .main-container {
            margin: 1rem;
            padding: 1.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True
)

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_credentials(username, password):
    """Verify user credentials against stored secrets"""
    try:
        # Get credentials from secrets
        users = st.secrets.get("users", {})
        
        if username in users:
            stored_hash = users[username]
            input_hash = hash_password(password)
            return stored_hash == input_hash
        
        return False
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False

def login_form():
    """Display login form"""
    st.markdown('<div class="login-container fade-in">', unsafe_allow_html=True)
    
    st.markdown('<h1 class="login-title">🧪 Barran Group Login</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Access CCS Logging and Processing Tools</p>', unsafe_allow_html=True)
    
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if not username or not password:
                st.markdown(
                    '<div class="error-box">⚠️ Please enter both username and password.</div>',
                    unsafe_allow_html=True
                )
            elif verify_credentials(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("Login successful! Redirecting...")
                st.rerun()
            else:
                st.markdown(
                    '<div class="error-box">❌ Invalid username or password. Please try again.</div>',
                    unsafe_allow_html=True
                )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Instructions for setup
    with st.expander("🔧 Setup Instructions (Admin Only)", expanded=False):
        st.markdown("""
        **To configure user accounts:**
        
        1. Add user credentials to your Streamlit secrets in the following format:
        
        ```toml
        [users]
        username1 = "hashed_password_1"
        username2 = "hashed_password_2"
        ```
        
        2. To generate password hashes, use this Python code:
        
        ```python
        import hashlib
        password = "your_password_here"
        hashed = hashlib.sha256(password.encode()).hexdigest()
        print(hashed)
        ```
        
        3. Add the hashed password (not the plain text) to your secrets.
        """)

def main_app():
    """Display main application after authentication"""
    
    # Header with logout
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<h1 class="main-title">Barran Group CCS Tools</h1>', unsafe_allow_html=True)
    with col2:
        if st.button("Logout", key="logout", help="Click to logout"):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.rerun()
    
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    
    # Welcome message
    st.markdown(f'''
    <div class="welcome-user fade-in">
        👋 Welcome back, <strong>{st.session_state.username}</strong>!
    </div>
    ''', unsafe_allow_html=True)
    
    # Main content container
    st.markdown('<div class="main-container fade-in">', unsafe_allow_html=True)
    
    # Welcome section
    st.markdown("""
    <div class="info-box">
        <p><strong>🎉 Welcome!</strong> This site hosts tools for logging protein CCS values and processing IM-MS data.</p>
        <p>Navigate using the sidebar to access different tools and features!</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="warning-box">
        <strong>⚠️ Work in Progress</strong><br>
        Please sanity check all results before use. Report any issues through the feedback form below.
    </div>
    """, unsafe_allow_html=True)
    
    # Site guide
    st.markdown('<h2 class="section-header">📋 Site Guide</h2>', unsafe_allow_html=True)
    st.write("Use the table below to find the pages you need:")

    # Guide table data
    guide_data = {
        "Page Name": [
            "🏠 Home",
            "📝 CCS Logging",
            "👁️ View Data",
            "⚖️ Calibrate",
            "📄 Get Input Files",
            "🔄 Process Output Files",
            "📊 Process and Plot IMS",
            "🎯 Fit Major Peaks"
        ],
        "Description": [
            "Home page, login, and feedback system.",
            "Log protein CCS values from research papers.",
            "View logged CCS values and user leaderboard.",
            "Process calibrant data and export to IMSCal reference files.",
            "Generate IMSCal input files from ATDs and masses.",
            "Process IMSCal output files to get arrival time ⇒ CCS conversions.",
            "Use arrival time ⇒ CCS conversions to process and plot IMS data.",
            "Fit major peaks in your data according to specified parameters."
        ],
        "Status": [
            "✅ Active",
            "✅ Active", 
            "✅ Active",
            "✅ Active",
            "✅ Active",
            "✅ Active",
            "✅ Active",
            "🔧 Beta"
        ]
    }
    
    guide_df = pd.DataFrame(guide_data)
    st.dataframe(
        guide_df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Page Name": st.column_config.TextColumn("Page Name", width="medium"),
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Status": st.column_config.TextColumn("Status", width="small")
        }
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Feedback section
    feedback_section()

def feedback_section():
    """User feedback section"""
    st.markdown('<div class="main-container fade-in">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-header">💬 User Feedback</h2>', unsafe_allow_html=True)

    name = st.text_input(
        "Name:", 
        max_chars=50, 
        placeholder="Your name (optional)",
        value=st.session_state.username if st.session_state.username else ""
    )
    feedback = st.text_area(
        "Share your feedback or suggestions:", 
        height=120, 
        placeholder="Enter your feedback here..."
    )
    
    submit = st.button("Submit Feedback", type="primary")

    if submit:
        if not feedback.strip():
            st.markdown(
                '<div class="warning-box">⚠️ Please enter some feedback before submitting.</div>',
                unsafe_allow_html=True
            )
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
                    "feedback": feedback.replace("\n", " "),
                    "user": st.session_state.username
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
                    "message": f"Added feedback from {st.session_state.username}",
                    "content": encoded_content
                }
                if sha:
                    payload["sha"] = sha

                put_response = requests.put(API_URL, headers=headers, json=payload)
                if put_response.status_code in [200, 201]:
                    st.markdown(
                        '<div class="success-box">🎉 Thanks! Your feedback has been saved successfully.</div>',
                        unsafe_allow_html=True
                    )
                else:
                    raise Exception(f"GitHub update error: {put_response.status_code}, {put_response.text}")

            except Exception as e:
                st.markdown(
                    f'<div class="error-box">❌ Error saving feedback: {str(e)}</div>',
                    unsafe_allow_html=True
                )
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main application logic
def main():
    if not st.session_state.authenticated:
        login_form()
    else:
        main_app()

if __name__ == "__main__":
    main()
