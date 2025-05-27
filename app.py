import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64
import requests
from io import StringIO 

# Page config for professional look
st.set_page_config(
    page_title="Barran Group CCS Tools",
    page_icon="🧪",
    layout="wide"
)

# Enhanced CSS with modern design and animations
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', sans-serif;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        margin: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Header Styles */
    .hero-title {
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
        animation: fadeInUp 1s ease-out;
    }
    
    .hero-subtitle {
        text-align: center;
        color: #64748b;
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 2rem;
        animation: fadeInUp 1s ease-out 0.2s both;
    }
    
    /* Card Styles */
    .feature-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.5);
        transition: all 0.3s ease;
        animation: fadeInUp 1s ease-out 0.4s both;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
    }
    
    .warning-card {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #f59e0b;
        animation: fadeInUp 1s ease-out 0.6s both;
    }
    
    /* Table Styles */
    .guide-table {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        animation: fadeInUp 1s ease-out 0.8s both;
    }
    
    .stTable > div {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
        background: linear-gradient(135deg, #059669, #047857);
    }
    
    /* Input Styles */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        font-family: 'Inter', sans-serif;
        font-size: 16px;
        padding: 12px;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        outline: none;
    }
    
    /* Section Headers */
    .section-header {
        color: #1f2937;
        font-size: 2rem;
        font-weight: 600;
        margin: 2rem 0 1rem 0;
        position: relative;
        animation: fadeInUp 1s ease-out;
    }
    
    .section-header::after {
        content: '';
        position: absolute;
        bottom: -8px;
        left: 0;
        width: 60px;
        height: 3px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 2px;
    }
    
    /* Animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* Success/Warning Messages */
    .stSuccess {
        background: linear-gradient(135deg, #d1fae5, #a7f3d0);
        border-left: 4px solid #10b981;
        border-radius: 12px;
        animation: fadeInUp 0.5s ease-out;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #fef3c7, #fde68a);
        border-left: 4px solid #f59e0b;
        border-radius: 12px;
        animation: fadeInUp 0.5s ease-out;
    }
    
    .stError {
        background: linear-gradient(135deg, #fee2e2, #fecaca);
        border-left: 4px solid #ef4444;
        border-radius: 12px;
        animation: fadeInUp 0.5s ease-out;
    }
    
    /* Hide Streamlit elements */
    .css-1d391kg {padding-top: 0;}
    .css-hi6a2p {padding: 0;}
    .css-1lsmgbg.e1fqkh3o3 {display: none;}
    header[data-testid="stHeader"] {display: none;}
    .stDeployButton {display: none;}
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2.5rem;
        }
        .feature-card {
            padding: 1.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True
)

# Main layout containers
header = st.container()
body = st.container()
guide = st.container()
feedback_section = st.container()

with header:
    st.markdown('<h1 class="hero-title">🧪 Barran Group CCS Tools</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Advanced Logging & Calibration Tools for IM-MS Data Processing</p>', unsafe_allow_html=True)

with body:
    st.markdown("""
    <div class="feature-card">
        <h3 style="color: #1f2937; margin-bottom: 1rem;">Welcome to the Future of CCS Analysis</h3>
        <p style="color: #64748b; font-size: 1.1rem; line-height: 1.6;">
            This comprehensive platform hosts cutting-edge tools for logging protein CCS values and processing IM-MS data. 
            Streamline your workflow with our intuitive interface and powerful analytics capabilities.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="warning-card">
        <strong>⚠️ Beta Release Notice</strong><br>
        This platform is continuously evolving. Please validate all results before publication or critical use.
    </div>
    """, unsafe_allow_html=True)

with guide:
    st.markdown('<h2 class="section-header">📋 Navigation Guide</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <p style="color: #64748b; margin-bottom: 1.5rem;">
            Explore our comprehensive suite of tools using the sidebar navigation. Each page is designed for specific workflows:
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Define your guide table data with enhanced descriptions
    guide_data = {
        "🔧 Page": [
            "🏠 Home",
            "📝 CCS Logging",
            "📊 View Data",
            "⚙️ Calibrate",
            "📁 Get Input Files",
            "🔄 Process Output Files",
            "📈 Process & Plot IMS",
            "🎯 Fit Major Peaks"
        ],
        "📖 Description": [
            "Central hub with navigation guide and feedback system",
            "Log and catalog protein CCS values from literature sources",
            "Browse logged CCS database with interactive leaderboard",
            "Process calibrant data and export to IMSCal formats",
            "Generate IMSCal input files from ATD and mass data",
            "Convert IMSCal outputs to arrival time ⇒ CCS calibrations",
            "Apply calibrations to process and visualize IMS datasets",
            "Advanced peak fitting with customizable parameters"
        ],
        "🎯 Use Case": [
            "Start here for overview and feedback",
            "Literature data entry and management",
            "Data exploration and validation",
            "Instrument calibration workflows",
            "Data preparation and formatting",
            "Calibration curve generation",
            "Data analysis and visualization",
            "Quantitative peak analysis"
        ]
    }
    
    guide_df = pd.DataFrame(guide_data)
    
    # Display the enhanced guide table
    st.markdown('<div class="guide-table">', unsafe_allow_html=True)
    st.dataframe(
        guide_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "🔧 Page": st.column_config.TextColumn(width="medium"),
            "📖 Description": st.column_config.TextColumn(width="large"),
            "🎯 Use Case": st.column_config.TextColumn(width="medium")
        }
    )
    st.markdown('</div>', unsafe_allow_html=True)

with feedback_section:
    st.markdown('<h2 class="section-header">💬 Your Feedback Matters</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <p style="color: #64748b; margin-bottom: 1.5rem;">
            Help us improve! Share your experience, suggest features, or report issues. Your input drives our development roadmap.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Create columns for better layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        name = st.text_input("👤 Your Name (Optional):", max_chars=50, placeholder="Enter your name...")
    
    with col2:
        feedback = st.text_area(
            "💭 Share Your Thoughts:", 
            height=120, 
            placeholder="Tell us about your experience, suggest improvements, or report any issues..."
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Center the submit button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        submit = st.button("🚀 Submit Feedback", use_container_width=True)

    if submit:
        if not feedback.strip():
            st.warning("💡 Please share some feedback before submitting!")
        else:
            with st.spinner("Sending your feedback..."):
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
                        "name": name.strip() if name else "Anonymous User",
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
                        st.success("🎉 Thank you! Your feedback has been successfully saved and will help improve our platform.")
                        st.balloons()
                    else:
                        raise Exception(f"GitHub update error: {put_response.status_code}, {put_response.text}")

                except Exception as e:
                    st.error(f"❌ Oops! There was an issue saving your feedback: {e}")
                    st.info("💡 Please try again in a moment or contact our support team.")
