import streamlit as st
import pandas as pd
import re
import requests
from datetime import datetime
from github import Github, GithubException
from io import StringIO
import hashlib

# === PAGE CONFIGURATION ===
st.set_page_config(
    page_title="CCS Logging",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === CUSTOM CSS ===
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
    
    .login-card {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        margin: 2rem auto;
        max-width: 400px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    
    .login-header {
        color: #667eea;
        font-size: 1.8rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    .user-info {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #22c55e;
        margin: 1rem 0;
        text-align: center;
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
    
    .status-card {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid;
    }
    
    .success-card {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border-left-color: #22c55e;
        border: 1px solid #bbf7d0;
    }
    
    .warning-card {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-left-color: #f59e0b;
        border: 1px solid #fed7aa;
    }
    
    .error-card {
        background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
        border-left-color: #ef4444;
        border: 1px solid #fca5a5;
    }
    
    .info-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-left-color: #667eea;
        border: 1px solid #cbd5e1;
        padding: 1.5rem;
        margin: 1.5rem 0;
    }
    
    .form-section {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin: 1rem 0;
    }
    
    .protein-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin: 0.5rem 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .metric-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
        display: inline-block;
        margin: 0.2rem;
    }
    
    .doi-input-section {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #cbd5e1;
        margin: 1rem 0;
    }
    
    .paper-info {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
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
    
    /* Logout button styling */
    .logout-btn {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.4rem 1rem;
        font-weight: 500;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .logout-btn:hover {
        background: linear-gradient(135deg, #b91c1c 0%, #991b1b 100%);
    }
    
    /* Form Input Styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #d1d5db;
        font-family: 'Inter', sans-serif;
        padding: 0.5rem;
        transition: border-color 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 8px;
        padding: 0.5rem;
        font-weight: 500;
        color: #1f2937;
    }
    
    /* Table Styling */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Progress Indicators */
    .progress-step {
        display: inline-block;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: #e2e8f0;
        color: #64748b;
        text-align: center;
        line-height: 30px;
        margin: 0 0.5rem;
        font-weight: 600;
    }
    
    .progress-step.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .progress-step.completed {
        background: #22c55e;
        color: white;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    /* Hide default elements */
    header[data-testid="stHeader"] {display: none;}
    .stDeployButton {display: none;}
    .css-1lsmgbg.e1fqkh3o3 {display: none;}
</style>
""", unsafe_allow_html=True)

# === AUTHENTICATION FUNCTIONS ===

def hash_password(password):
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def load_user_credentials():
    """Load user credentials from Streamlit secrets."""
    try:
        # Expected format in secrets:
        # [users]
        # usernames = ["user1", "user2", "user3"]
        # passwords = ["hash1", "hash2", "hash3"]  # Pre-hashed passwords
        usernames = st.secrets["users"]["usernames"]
        passwords = st.secrets["users"]["passwords"]
        
        if len(usernames) != len(passwords):
            st.error("Mismatch between usernames and passwords in secrets!")
            return {}
            
        return dict(zip(usernames, passwords))
    except Exception as e:
        st.error(f"Error loading user credentials: {e}")
        st.info("Please ensure your secrets.toml contains [users] section with 'usernames' and 'passwords' lists")
        return {}

def authenticate_user(username, password):
    """Authenticate user credentials."""
    credentials = load_user_credentials()
    if not credentials:
        return False
    
    hashed_password = hash_password(password)
    return credentials.get(username) == hashed_password

def show_login_form():
    """Display login form."""
    st.markdown("""
    <div class="main-header">
        <h1>🔐 CCS Database Login</h1>
        <p>Please log in to access the protein CCS logging system. If you don't have an account, email ana.bathalen@manchester.ac.uk to get one! You will be assigned a username and password.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="login-card">
        <div class="login-header">Sign In</div>
        <p style="color: #64748b; margin-bottom: 1.5rem;">Enter your credentials to continue</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get available usernames for dropdown
    credentials = load_user_credentials()
    available_usernames = list(credentials.keys()) if credentials else []
    
    if not available_usernames:
        st.error("No user accounts configured. Please contact your administrator.")
        return False
    
    with st.form("login_form"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.selectbox("Username", ["Select username..."] + available_usernames)
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            login_button = st.form_submit_button("🚀 Sign In", use_container_width=True)
            
            if login_button:
                if username == "Select username...":
                    st.error("Please select a username")
                elif not password:
                    st.error("Please enter your password")
                elif authenticate_user(username, password):
                    st.session_state.authenticated = True
                    st.session_state.current_user = username
                    st.success("Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
    
    return False

def show_user_info():
    """Display current user info and logout button."""
    if st.session_state.get('authenticated', False):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"""
            <div class="user-info">
                <strong>👤 Logged in as: {st.session_state.current_user}</strong>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("🚪 Logout"):
                st.session_state.authenticated = False
                st.session_state.current_user = None
                # Clear all other session state
                for key in list(st.session_state.keys()):
                    if key not in ['authenticated', 'current_user']:
                        del st.session_state[key]
                st.rerun()

# === HELPER FUNCTIONS ===

def validate_doi(doi):
    """Validate DOI format using regex."""
    doi_pattern = r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$'
    return re.match(doi_pattern, doi.strip(), re.IGNORECASE) is not None

def normalize_doi(doi):
    """Normalize DOI by stripping whitespace, lowercasing, and removing any prefix."""
    if not isinstance(doi, str):
        return ""
    doi = doi.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/"):
        if doi.startswith(prefix):
            doi = doi.replace(prefix, "")
    return doi

def check_doi_exists(existing_data, doi):
    """Check if normalized DOI already exists in the dataframe."""
    if existing_data is None or existing_data.empty or 'doi' not in existing_data.columns:
        return False
    normalized_doi = normalize_doi(str(doi))
    normalized_existing = set(normalize_doi(str(x)) for x in existing_data['doi'].dropna())
    return normalized_doi in normalized_existing

def get_paper_details(doi):
    """Fetch paper details from CrossRef API."""
    try:
        response = requests.get(f"https://api.crossref.org/works/{doi}")
        if response.status_code == 200:
            data = response.json()['message']
            title = data.get("title", ["No title"])[0]
            authors_list = data.get('author', [])
            authors = ', '.join([f"{a.get('given','')} {a.get('family','')}".strip() for a in authors_list])
            year = None
            if 'published-print' in data:
                year = data['published-print'].get("date-parts", [[None]])[0][0]
            elif 'published-online' in data:
                year = data['published-online'].get("date-parts", [[None]])[0][0]
            elif 'published' in data:
                year = data['published'].get("date-parts", [[None]])[0][0]
            journal = data.get("container-title", ["No journal"])[0]
            return {
                "paper_title": title,
                "authors": authors if authors else "Unknown Authors",
                "doi": doi,
                "publication_year": year if year else "Unknown Year",
                "journal": journal
            }
        else:
            return {
                "paper_title": "Unknown Paper Title",
                "authors": "Unknown Authors",
                "doi": doi,
                "publication_year": "Unknown Year",
                "journal": "Unknown Journal"
            }
    except Exception:
        return {
            "paper_title": "Unknown Paper Title",
            "authors": "Unknown Authors",
            "doi": doi,
            "publication_year": "Unknown Year",
            "journal": "Unknown Journal"
        }

def authenticate_github():
    """Authenticate GitHub using token from secrets."""
    try:
        token = st.secrets["GITHUB_TOKEN"]
        g = Github(token)
        _ = g.get_user().login
        return g
    except Exception as e:
        st.error(f"GitHub Authentication error: {e}")
        return None

def get_repository(g, repo_name):
    """Get a repository by name."""
    try:
        repo = g.get_repo(repo_name)
        return repo
    except GithubException as e:
        st.error(f"GitHub repo access error: {e}")
        return None

def get_existing_data_from_github(repo, path):
    try:
        file_content = repo.get_contents(path)
        csv_str = file_content.decoded_content.decode('utf-8')
        df = pd.read_csv(StringIO(csv_str))
        return df
    except Exception as e:
        st.warning(f"Could not load existing data from GitHub: {e}")
        return pd.DataFrame()

def update_csv_in_github(repo, path, df):
    """Update or create CSV file on GitHub."""
    try:
        file = repo.get_contents(path)
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        new_content = csv_buffer.getvalue()
        repo.update_file(path, f"Update CCS data {datetime.now().isoformat()}", new_content, file.sha)
        return True, "Data successfully updated in GitHub."
    except GithubException:
        try:
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            new_content = csv_buffer.getvalue()
            repo.create_file(path, f"Create CCS data {datetime.now().isoformat()}", new_content)
            return True, "Data file created successfully in GitHub."
        except Exception as e2:
            return False, f"Failed to update or create file in GitHub: {e2}"
    except Exception as e:
        return False, f"Unexpected error: {e}"

def convert_protein_data_to_dataframe(protein_data_list, paper_details):
    """Convert list of protein entries to DataFrame format for CSV."""
    rows = []
    for protein in protein_data_list:
        for charge, ccs in protein['ccs_data']:
            row = {
                'user_name': protein['user_name'],
                'protein_name': protein['protein_name'],
                'charge_state': charge,
                'ccs_value': ccs,
                'instrument': protein['instrument'],
                'ims_type': protein['ims_type'],
                'drift_gas': protein['drift_gas'],
                'ionization_mode': protein['ionization_mode'],
                'native_measurement': protein['native_measurement'],
                'subunit_count': protein['subunit_count'],
                'oligomer_type': protein.get('oligomer_type'),
                'uniprot': protein.get('uniprot'),
                'pdb': protein.get('pdb'),
                'sequence': protein.get('sequence'),
                'sequence_mass': protein.get('sequence_mass'),
                'measured_mass': protein.get('measured_mass'),
                'additional_notes': protein.get('additional_notes'),
                'paper_title': paper_details['paper_title'],
                'authors': paper_details['authors'],
                'doi': paper_details['doi'],
                'publication_year': paper_details['publication_year'],
                'journal': paper_details['journal'],
                'entry_date': datetime.now().isoformat()[:10]  # YYYY-MM-DD format
            }
            rows.append(row)
    return pd.DataFrame(rows)

# === MAIN APPLICATION ===

def show_data_entry_page():
    # Show user info and logout button
    show_user_info()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>Protein CCS Logging Form</h1>
        <p>Contribute collision cross-section data from papers to help build our database!</p>
    </div>
    """, unsafe_allow_html=True)

    # Load existing data
    @st.cache_data(ttl=600, show_spinner="Loading existing database...")
    def load_existing_data():
        g = authenticate_github()
        if g:
            repo = get_repository(g, st.secrets["REPO_NAME"])
            if repo:
                return get_existing_data_from_github(repo, st.secrets["CSV_PATH"])
        return pd.DataFrame()

    existing_data = load_existing_data()

    # Initialize session state variables
    if 'show_full_form' not in st.session_state:
        st.session_state.show_full_form = False
    if 'protein_data' not in st.session_state:
        st.session_state.protein_data = []
    if 'new_doi' not in st.session_state:
        st.session_state.new_doi = ""
    if 'paper_details' not in st.session_state:
        st.session_state.paper_details = {}

    # Main content
    # Step 1: DOI Verification
    st.markdown("---")
    st.markdown('<h2 class="section-header">Step 1: DOI Verification</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <strong>ℹ️ Instructions</strong><br>
        Enter the DOI of your paper to check if it already exists in our database.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    with col1:
        doi = st.text_input(
            "📝 Enter DOI", 
            placeholder="e.g., 10.1234/example",
            help="Digital Object Identifier",
            key="doi_input"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        check_button = st.button("🔍 Verify DOI", use_container_width=True)

    # DOI verification logic
    if check_button and doi:
        if not validate_doi(doi):
            st.markdown("""
            <div class="error-card">
                <strong>❌ Invalid DOI Format</strong><br>
                Please enter a valid DOI starting with '10.' followed by publisher and article identifiers.
            </div>
            """, unsafe_allow_html=True)
            st.session_state.show_full_form = False
        else:
            with st.spinner("Checking DOI and fetching paper details..."):
                paper_details = get_paper_details(doi)
                
                if check_doi_exists(existing_data, doi):
                    st.markdown(f"""
                    <div class="warning-card">
                        <strong>⚠️ Paper Already in Database</strong><br>
                        This paper (DOI: {doi}) already has entries in our database.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    paper_entries = existing_data[existing_data['doi'] == doi]
                    st.markdown(f"**Found {len(paper_entries)} existing entries:**")
                    st.dataframe(paper_entries, use_container_width=True)
                    st.session_state.show_full_form = False
                else:
                    st.markdown(f"""
                    <div class="success-card">
                        <strong>✅ New Paper Verified</strong><br>
                        Paper successfully verified and not found in database. You can proceed with data entry.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display paper details
                    st.markdown(f"""
                    <div class="paper-info">
                        <strong>📖 Paper Details</strong><br>
                        <strong>Title:</strong> {paper_details['paper_title']}<br>
                        <strong>Authors:</strong> {paper_details['authors']}<br>
                        <strong>Journal:</strong> {paper_details['journal']}<br>
                        <strong>Year:</strong> {paper_details['publication_year']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.session_state.new_doi = doi
                    st.session_state.show_full_form = True
                    st.session_state.paper_details = paper_details
                    # Don't reset protein_data here - let user continue adding

    # Step 2: Protein Data Entry
    if st.session_state.show_full_form:
        st.markdown("---")
        st.markdown('<h2 class="section-header">Step 2: Protein Data Entry</h2>', unsafe_allow_html=True)
        st.markdown("""
        Many papers contain data for several proteins and/or several measurements for the same protein. 
        Each entry corresponds to one set of values for one protein (e.g. CCS values for charge states +5 to +8 of Protein X). 
        If a single charge state has multiple conformers, these can be logged separately under the same entry. 
        If there are multiple sets of values, or multiple proteins, click '✚ Add Protein Entry' at the end of the form. 
        Once you are finished, click '🚀 Submit All Data to Database'.
        """)
        
        # Create form with unique key to prevent conflicts
        with st.form("protein_form", clear_on_submit=False):
            st.markdown("---")
            st.markdown("#### ⚙️ General Information")
            
            col1, col2 = st.columns(2)
            with col1:
                # Use current logged-in user as default
                current_user = st.session_state.get('current_user', '')
                credentials = load_user_credentials()
                available_usernames = list(credentials.keys()) if credentials else [current_user]
                
                # Set current user as default selection
                default_index = 0
                if current_user in available_usernames:
                    default_index = available_usernames.index(current_user)
                
                user_name = st.selectbox(
                    "Username", 
                    available_usernames,
                    index=default_index,
                    help="Select username for this entry"
                )
            
            with col2:
                protein_name = st.text_input(
                    "Protein Name", 
                    placeholder="e.g., Cytochrome C, Ubiquitin",
                    help="Enter the name of the protein or ion studied"
                )
            
            st.markdown("---")
            st.markdown("#### 👩‍🔬 Experimental Setup")
            
            col1, col2 = st.columns(2)
            with col1:
                instrument = st.selectbox("Instrument Family", [
                    "Select instrument...",
                    "Waters Synapt", "Waters Cyclic", "Waters Vion", 
                    "Agilent 6560", "Bruker timsTOF", "Other"
                ])
                if instrument == "Other":
                    instrument = st.text_input("Specify Instrument")
                
                drift_gas = st.selectbox("Drift Gas used for Measurement", [
                    "Select drift gas...",
                    "Nitrogen", "Helium", "Argon", "Other"
                ])
                if drift_gas == "Other":
                    drift_gas = st.text_input("Specify Drift Gas")
                
                drift_gas_calibration = st.selectbox("Drift Gas used for Calibration (if applicable)", [
                    "Select drift gas...",
                    "Nitrogen", "Helium", "Argon", "N/A","Other"
                ])
                if drift_gas_calibration == "Other":
                    drift_gas_calibration = st.text_input("Specify Calibration Drift Gas")
            
            with col2:
                ims_type = st.selectbox("IMS Type", [
                    "Select IMS type...",
                    "TWIMS", "DTIMS", "CYCLIC", "TIMS", "FAIMS", "Other"
                ])
                if ims_type == "Other":
                    ims_type = st.text_input("Specify IMS Type")
                
                ionization_mode = st.selectbox("Ionization Mode", [
                    "Select mode...", "Positive", "Negative"
                ])
                instrument_details = st.text_input("Instrument details as described in the paper:")
                
            st.markdown("---")
            st.markdown("#### 🏷️ Protein Identifiers")
            
            col1, col2 = st.columns(2)
            with col1:
                uniprot_id = st.text_input("UniProt ID", placeholder="e.g., P12345")
                uniprot_source = st.radio(
                    "UniProt ID source:",
                    ["Not provided", "Provided in paper", "User searched"],
                    horizontal=True
                )
                
                sequence_mass_value = st.number_input("Sequence Mass or Best Approximation (Da)", min_value=0.0, value=0.0, format="%.2f")
                sequence_mass_source = st.radio(
                    "Sequence Mass source:",
                    ["Not provided", "Provided in paper", "User calculated"],
                    horizontal=True
                )
                
                protein_sequence = st.text_area("Protein Sequence", placeholder="Enter amino acid sequence...")
                sequence_source = st.radio(
                    "Protein Sequence source:",
                    ["Not provided", "Provided in paper", "User searched"],
                    horizontal=True
                )
            
            with col2:
                pdb_id = st.text_input("PDB ID", placeholder="e.g., 1ABC")
                pdb_source = st.radio(
                    "PDB ID source:",
                    ["Not provided", "Provided in paper", "User searched"],
                    horizontal=True
                )
                
                measured_mass_value = st.number_input("Measured Mass (Da)", min_value=0.0, value=0.0, format="%.2f")
                measured_mass_source = st.radio(
                    "Measured Mass source:",
                    ["Not provided", "Provided in paper", "User calculated"],
                    horizontal=True
                )
                
                additional_notes = st.text_area("Additional Notes", placeholder="Sample preparation, instrument settings, etc.")
            
            st.markdown("---")
            st.markdown("#### 🔬 Measurement Details")
            
            col1, col2 = st.columns(2)
            with col1:
                native_measurement = st.radio("Native measurement?", ["Yes", "No"])
                subunit_count = st.number_input("Number of Subunits", min_value=1, step=1, value=1)
            
            with col2:
                oligomer_type = ""
                if subunit_count > 1:
                    oligomer_type = st.radio("Oligomer Type", [
                        "Not applicable", "Homo-oligomer", "Hetero-oligomer"
                    ])
            
            st.markdown("---")
            st.markdown("#### 📊 CCS Values")
            
            if ionization_mode not in ["Select mode...", ""]:
                num_ccs_values = st.number_input("Number of charge states", min_value=1, step=1, value=1)
                
                ccs_data = []
                ccs_data_sources = []
                st.markdown("**Enter charge states and corresponding CCS values:**")
                
                # CCS source selection helpers
                if int(num_ccs_values) > 1:
                    st.markdown("**Quick source selection:**")
                    col_btn1, col_btn2, col_spacer = st.columns([1, 1, 3])
                    with col_btn1:
                        all_from_paper = st.checkbox("All from Paper", key="all_paper")
                    with col_btn2:
                        all_from_graph = st.checkbox("All from Graph", key="all_graph")
                
                for i in range(int(num_ccs_values)):
                    st.markdown(f"**Charge State {i+1}:**")
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        charge_state = st.number_input(f"Charge", min_value=1, step=1, key=f"charge_{i}", value=i+1)
                    with col2:
                        ccs_value = st.number_input(f"CCS (Ų)", min_value=0.0, format="%.2f", key=f"ccs_{i}")
                    with col3:
                        col3a, col3b = st.columns(2)
                        with col3a:
                            # Use the "all" checkboxes to set defaults
                            default_paper = all_from_paper if int(num_ccs_values) > 1 else False
                            from_paper = st.checkbox("From paper", key=f"ccs_paper_{i}", value=default_paper)
                        with col3b:
                            default_graph = all_from_graph if int(num_ccs_values) > 1 else False
                            from_graph = st.checkbox("From graph", key=f"ccs_graph_{i}", value=default_graph)
                        
                        ccs_data_sources.append({
                            'from_paper': from_paper,
                            'from_graph': from_graph
                        })
                    
                    ccs_data.append((charge_state, ccs_value))
                
            else:
                st.info("⚠️ Please select ionization mode to enter CCS values")
                ccs_data = []
                ccs_data_sources = []
            
            # Form submission
            submit_button = st.form_submit_button("➕ Add Protein Entry", use_container_width=True)
            
            if submit_button:
                # Validation
                errors = []
                if not protein_name:
                    errors.append("Protein name is required")
                if instrument == "Select instrument...":
                    errors.append("Please select an instrument")
                if ims_type == "Select IMS type...":
                    errors.append("Please select IMS type")
                if drift_gas == "Select drift gas...":
                    errors.append("Please select drift gas")
                if ionization_mode == "Select mode...":
                    errors.append("Please select ionization mode")
                if not ccs_data or all(ccs == 0.0 for _, ccs in ccs_data):
                    errors.append("Please enter at least one valid CCS value")
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    # Create protein entry with source tracking fields
                    protein_entry = {
                        'user_name': user_name,
                        'protein_name': protein_name,
                        'instrument': instrument,
                        'ims_type': ims_type,
                        'drift_gas': drift_gas,
                        'drift_gas_calibration': drift_gas_calibration,
                        'ionization_mode': ionization_mode,
                        'instrument_details': instrument_details,
                        'native_measurement': native_measurement,
                        'subunit_count': subunit_count,
                        'oligomer_type': oligomer_type if subunit_count > 1 else "",
                        'uniprot': uniprot_id,
                        'uniprot_source': uniprot_source,
                        'pdb': pdb_id,
                        'pdb_source': pdb_source,
                        'sequence': protein_sequence,
                        'sequence_source': sequence_source,
                        'sequence_mass': sequence_mass_value if sequence_mass_value > 0 else None,
                        'sequence_mass_source': sequence_mass_source,
                        'measured_mass': measured_mass_value if measured_mass_value > 0 else None,
                        'measured_mass_source': measured_mass_source,
                        'additional_notes': additional_notes,
                        'ccs_data': [(int(charge), float(ccs)) for charge, ccs in ccs_data if ccs > 0],
                        'ccs_data_sources': [src for i, src in enumerate(ccs_data_sources) if ccs_data[i][1] > 0]
                    }
                    
                    # Add to session state
                    st.session_state.protein_data.append(protein_entry)
                    st.success(f"✅ Protein '{protein_name}' added successfully!")
                    st.rerun()
                    
        # Display added proteins
        if st.session_state.protein_data:
            st.markdown("---")
            st.markdown('<h3 class="section-header">📝 Added Protein Entries</h3>', unsafe_allow_html=True)
            
            for i, protein in enumerate(st.session_state.protein_data):
                with st.expander(f"🧬 {protein['protein_name']} ({len(protein['ccs_data'])} charge states)"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**User:** {protein['user_name']}")
                        st.write(f"**Instrument:** {protein['instrument']}")
                        st.write(f"**IMS Type:** {protein['ims_type']}")
                        st.write(f"**Drift Gas:** {protein['drift_gas']}")
                        st.write(f"**Drift Gas (Calibration):** {protein.get('drift_gas_calibration', 'N/A')}")
                        st.write(f"**Ionization Mode:** {protein['ionization_mode']}")
                        # Display source information
                        if protein.get('uniprot'):
                            st.write(f"**UniProt:** {protein['uniprot']} *({protein.get('uniprot_source', 'Unknown source')})*")
                        else:
                            st.write(f"**UniProt:** Not provided *({protein.get('uniprot_source', 'Not provided')})*")
                        if protein.get('pdb'):
                            st.write(f"**PDB:** {protein['pdb']} *({protein.get('pdb_source', 'Unknown source')})*")
                        else:
                            st.write(f"**PDB:** Not provided *({protein.get('pdb_source', 'Not provided')})*")
                    with col2:
                        st.write(f"**Native Measurement:** {protein['native_measurement']}")
                        st.write(f"**Subunit Count:** {protein['subunit_count']}")
                        if protein['oligomer_type']:
                            st.write(f"**Oligomer Type:** {protein['oligomer_type']}")
                        # Display mass source information
                        if protein.get('sequence_mass'):
                            st.write(f"**Sequence Mass:** {protein['sequence_mass']} Da *({protein.get('sequence_mass_source', 'Unknown source')})*")
                        else:
                            st.write(f"**Sequence Mass:** Not provided *({protein.get('sequence_mass_source', 'Not provided')})*")
                        if protein.get('measured_mass'):
                            st.write(f"**Measured Mass:** {protein['measured_mass']} Da *({protein.get('measured_mass_source', 'Unknown source')})*")
                        else:
                            st.write(f"**Measured Mass:** Not provided *({protein.get('measured_mass_source', 'Not provided')})*")
                        if protein.get('sequence'):
                            st.write(f"**Sequence:** Provided *({protein.get('sequence_source', 'Unknown source')})*")
                        else:
                            st.write(f"**Sequence:** Not provided *({protein.get('sequence_source', 'Not provided')})*")
                    
                    st.write("**CCS Values with Sources:**")
                    ccs_display_data = []
                    for j, (charge, ccs) in enumerate(protein['ccs_data']):
                        source_info = protein.get('ccs_data_sources', [{}])[j] if j < len(protein.get('ccs_data_sources', [])) else {}
                        sources = []
                        if source_info.get('from_paper', False):
                            sources.append("Paper")
                        if source_info.get('from_graph', False):
                            sources.append("Graph")
                        source_text = ", ".join(sources) if sources else "Not specified"
                        ccs_display_data.append([charge, ccs, source_text])
                    
                    ccs_df = pd.DataFrame(ccs_display_data, columns=['Charge State', 'CCS (Ų)', 'Source'])
                    st.dataframe(ccs_df, use_container_width=True)
                    
                    if st.button(f"🗑️ Remove {protein['protein_name']}", key=f"remove_{i}"):
                        st.session_state.protein_data.pop(i)
                        st.rerun()
                        
            # Submit all data
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 Submit All Data to Database", use_container_width=True, type="primary"):
                    if st.session_state.protein_data:
                        with st.spinner("Submitting data to GitHub..."):
                            # Convert to DataFrame
                            new_df = convert_protein_data_to_dataframe(
                                st.session_state.protein_data, 
                                st.session_state.paper_details
                            )
                            
                            # Combine with existing data
                            if not existing_data.empty:
                                combined_df = pd.concat([existing_data, new_df], ignore_index=True)
                            else:
                                combined_df = new_df
                            
                            # Submit to GitHub
                            g = authenticate_github()
                            if g:
                                repo = get_repository(g, st.secrets["REPO_NAME"])
                                if repo:
                                    success, message = update_csv_in_github(repo, st.secrets["CSV_PATH"], combined_df)
                                    if success:
                                        st.success(f"🎉 {message}")
                                        st.balloons()
                                        
                                        # Clear session state
                                        st.session_state.protein_data = []
                                        st.session_state.show_full_form = False
                                        st.session_state.new_doi = ""
                                        st.session_state.paper_details = {}
                                        
                                        # Clear cache to refresh data
                                        load_existing_data.clear()
                                        
                                        st.info("Form has been reset. You can now enter data for a new paper.")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                                else:
                                    st.error("❌ Could not access GitHub repository")
                            else:
                                st.error("❌ GitHub authentication failed")
                    else:
                        st.warning("⚠️ No protein data to submit")

def main():
    """Main application entry point."""
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None

    # Authentication check
    if not st.session_state.authenticated:
        show_login_form()
    else:
        show_data_entry_page()

if __name__ == "__main__":
    main()
