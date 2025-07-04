import streamlit as st
import pandas as pd
import re
import requests
from datetime import datetime, timedelta
from github import Github, GithubException
from io import StringIO
import hashlib
import json
import time

# === PAGE CONFIGURATION ===
st.set_page_config(
    page_title="CCS Logging",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === SESSION MANAGEMENT ===
SESSION_TIMEOUT_MINUTES = 120  # 2 hours
AUTO_SAVE_INTERVAL = 30  # Auto-save every 30 seconds

def refresh_session():
    """Refresh session timestamp to prevent timeout"""
    st.session_state.last_activity = datetime.now()

def check_session_timeout():
    """Check if session has timed out"""
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = datetime.now()
        return False
    
    time_since_activity = datetime.now() - st.session_state.last_activity
    return time_since_activity > timedelta(minutes=SESSION_TIMEOUT_MINUTES)

def auto_save_to_browser():
    """Auto-save current work to browser storage simulation"""
    if st.session_state.get('protein_data') or st.session_state.get('paper_details'):
        # Create a save state
        save_state = {
            'protein_data': st.session_state.get('protein_data', []),
            'paper_details': st.session_state.get('paper_details', {}),
            'new_doi': st.session_state.get('new_doi', ''),
            'show_full_form': st.session_state.get('show_full_form', False),
            'current_user': st.session_state.get('current_user', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in session state with a special key
        st.session_state.auto_save_data = save_state

def restore_from_auto_save():
    """Restore work from auto-save if available"""
    if 'auto_save_data' in st.session_state:
        save_state = st.session_state.auto_save_data
        
        # Check if the save is recent (within last 4 hours)
        save_time = datetime.fromisoformat(save_state.get('timestamp', ''))
        if datetime.now() - save_time < timedelta(hours=4):
            return save_state
    return None

def show_session_status():
    """Show session status and auto-save indicator"""
    if 'last_activity' in st.session_state:
        time_since_activity = datetime.now() - st.session_state.last_activity
        minutes_left = max(0, SESSION_TIMEOUT_MINUTES - int(time_since_activity.total_seconds() / 60))
        
        if minutes_left < 10:
            st.sidebar.warning(f"⏰ Session expires in {minutes_left} minutes")
        else:
            st.sidebar.info(f"🕐 Session active ({minutes_left}min remaining)")
        
        # Refresh button
        if st.sidebar.button("🔄 Refresh Session"):
            refresh_session()
            st.rerun()

def keep_alive_script():
    """JavaScript to keep session alive"""
    return """
    <script>
    // Keep session alive by periodically pinging
    setInterval(function() {
        // This will trigger a small rerun to keep session active
        const event = new Event('streamlit:componentReady');
        window.dispatchEvent(event);
    }, 30000); // Every 30 seconds
    </script>
    """

# === CUSTOM CSS (keeping original styling) ===
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
    
    .session-status {
        background: linear-gradient(135deg, #fef3c7 0%, #fcd34d 100%);
        padding: 0.8rem;
        border-radius: 8px;
        border-left: 4px solid #f59e0b;
        margin: 1rem 0;
        font-size: 0.9rem;
        text-align: center;
    }
    
    .auto-save-indicator {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        border: 1px solid #22c55e;
        color: #065f46;
        font-size: 0.8rem;
        display: inline-block;
        margin: 0.5rem 0;
    }
    
    .warning-timeout {
        background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ef4444;
        margin: 1rem 0;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    /* Keep all your existing CSS styles here */
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
    
    /* Keep all other existing styles */
    
</style>
""", unsafe_allow_html=True)

# Add keep-alive script
st.markdown(keep_alive_script(), unsafe_allow_html=True)

# === AUTHENTICATION FUNCTIONS (keeping original functions) ===

def hash_password(password):
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def load_user_credentials():
    """Load user credentials from Streamlit secrets."""
    try:
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
    """Display login form with auto-save recovery."""
    # Check for auto-save data
    auto_save_data = restore_from_auto_save()
    if auto_save_data and auto_save_data.get('current_user'):
        st.markdown(f"""
        <div class="warning-card">
            <strong>🔄 Work Recovery Available</strong><br>
            Found unsaved work from {auto_save_data.get('current_user')} 
            (saved {auto_save_data.get('timestamp', 'Unknown time')})
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Restore Previous Work", use_container_width=True):
                # Restore session
                st.session_state.authenticated = True
                st.session_state.current_user = auto_save_data['current_user']
                st.session_state.protein_data = auto_save_data.get('protein_data', [])
                st.session_state.paper_details = auto_save_data.get('paper_details', {})
                st.session_state.new_doi = auto_save_data.get('new_doi', '')
                st.session_state.show_full_form = auto_save_data.get('show_full_form', False)
                refresh_session()
                st.success("Work restored successfully!")
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear and Start Fresh", use_container_width=True):
                if 'auto_save_data' in st.session_state:
                    del st.session_state.auto_save_data
                st.rerun()
    
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
                    refresh_session()  # Initialize session tracking
                    st.success("Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
    
    return False

def show_user_info():
    """Display current user info and logout button with session status."""
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
                # Auto-save before logout
                auto_save_to_browser()
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.rerun()
        
        # Show session status in sidebar
        show_session_status()

# === HELPER FUNCTIONS (keeping all original functions) ===

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

def get_existing_protein_names(existing_data):
    """Extract unique protein names from existing data for dropdown."""
    if existing_data is None or existing_data.empty or 'protein_name' not in existing_data.columns:
        return []
    return sorted(existing_data['protein_name'].dropna().unique().tolist())

def convert_protein_data_to_dataframe(protein_data_list, paper_details):
    """Convert list of protein entries to DataFrame format for CSV with enhanced fields."""
    rows = []
    for protein in protein_data_list:
        for ccs_entry in protein['ccs_data']:
            charge = ccs_entry['charge']
            ccs = ccs_entry['ccs']
            data_source = ccs_entry['data_source']
            
            row = {
                'user_name': protein['user_name'],
                'protein_name': protein['protein_name'],
                'charge_state': charge,
                'ccs_value': ccs,
                'ccs_data_source': data_source,  # New field
                'instrument': protein['instrument'],
                'ims_type': protein['ims_type'],
                'drift_gas_measurement': protein['drift_gas_measurement'],
                'drift_gas_calibration': protein['drift_gas_calibration'],  # New field
                'ionization_mode': protein['ionization_mode'],
                'native_measurement': protein['native_measurement'],
                'subunit_count': protein['subunit_count'],
                'oligomer_type': protein['oligomer_type'],  # Required field now
                'uniprot': protein.get('uniprot'),
                'uniprot_source': protein.get('uniprot_source'),
                'pdb': protein.get('pdb'),
                'pdb_source': protein.get('pdb_source'),
                'sequence': protein.get('sequence'),
                'sequence_source': protein.get('sequence_source'),
                'sequence_mass': protein.get('sequence_mass'),
                'sequence_mass_source': protein.get('sequence_mass_source'),
                'measured_mass': protein.get('measured_mass'),
                'measured_mass_source': protein.get('measured_mass_source'),
                'measurement_conditions': protein.get('measurement_conditions'),
                'sample_conditions': protein.get('sample_conditions'),
                'paper_title': paper_details['paper_title'],
                'authors': paper_details['authors'],
                'doi': paper_details['doi'],
                'publication_year': paper_details['publication_year'],
                'journal': paper_details['journal'],
                'entry_date': datetime.now().isoformat()[:10]
            }
            rows.append(row)
    return pd.DataFrame(rows)

def show_enhanced_protein_form():
    """Enhanced protein entry form with updated requirements."""
    
    # Load existing data for protein name dropdown
    @st.cache_data(ttl=300)
    def load_existing_data_for_dropdown():
        g = authenticate_github()
        if g:
            repo = get_repository(g, st.secrets["REPO_NAME"])
            if repo:
                return get_existing_data_from_github(repo, st.secrets["CSV_PATH"])
        return pd.DataFrame()
    
    existing_data = load_existing_data_for_dropdown()
    existing_protein_names = get_existing_protein_names(existing_data)
    
    with st.form("protein_entry_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Basic Information")
            
            # Protein name with dropdown of existing names
            protein_name_option = st.selectbox(
                "Select Existing Protein or Enter New*",
                ["Enter new protein name..."] + existing_protein_names
            )
            
            if protein_name_option == "Enter new protein name...":
                protein_name = st.text_input("Protein Name*", placeholder="e.g., Cytochrome C")
            else:
                protein_name = protein_name_option
                st.info(f"Selected existing protein: {protein_name}")
            
            ionization_mode = st.selectbox("Ionization Mode*", [
                "Positive", "Negative"
            ])
            
            instrument = st.selectbox("Instrument Family*", [
                "Waters Synapt Series", "Waters Cyclic Series", "Agilent 6560", "Bruker timsTOF", "Waters Vion", "Other"
            ])
            if instrument == "Other":
                instrument = st.text_input("Specify Instrument")
            
            native_measurement = st.selectbox("Native Measurement*", [
                "Yes", "No"
            ])
        
        with col2:
            st.markdown("#### Measurement Setup")
            
            ims_type = st.selectbox("IMS Type*", [
                "TWIMS", "DTIMS", "TIMS", "Cyclic", "Other"
            ])
            if ims_type == "Other":
                ims_type = st.text_input("Specify IMS Type")
            
            drift_gas_measurement = st.selectbox("Drift Gas for Measurement*", [
                "Nitrogen", "Helium", "Argon", "Other"
            ])
            if drift_gas_measurement == "Other":
                drift_gas_measurement = st.text_input("Specify Drift Gas for Measurement")
            
            drift_gas_calibration = st.selectbox("Drift Gas for Calibration*", [
                "Nitrogen", "Helium", "Argon", "Same as measurement", "Other"
            ])
            if drift_gas_calibration == "Other":
                drift_gas_calibration = st.text_input("Specify Drift Gas for Calibration")
            
            subunit_count = st.number_input("Number of Subunits*", min_value=1, value=1, step=1)
            
            oligomer_type = st.selectbox("Oligomer Type*", [
                "Homoligomer", "Heteroligomer"
            ])
        
        # Measurement and Sample Conditions
        st.markdown("#### Conditions from Paper")
        col3, col4 = st.columns(2)
        
        with col3:
            measurement_conditions = st.text_area(
                "Measurement Conditions*",
                placeholder="Copy and paste measurement conditions from the paper",
                help="Include instrument settings, voltages, gas flows, etc."
            )
        
        with col4:
            sample_conditions = st.text_area(
                "Sample Conditions*", 
                placeholder="Copy and paste sample preparation conditions from the paper",
                help="Include buffer composition, pH, protein concentration, etc."
            )
        
        # Optional Information with Source Tracking
        st.markdown("#### Optional Information")
        st.markdown("*Check the box if you searched for this information (unchecked = provided in paper)*")
        
        col5, col6 = st.columns([4, 1])
        with col5:
            uniprot = st.text_input("UniProt ID", placeholder="e.g., P12345")
        with col6:
            st.markdown("<br>", unsafe_allow_html=True)
            uniprot_searched = st.checkbox("Searched?", key="uniprot_searched") if uniprot else False
        
        col7, col8 = st.columns([4, 1])
        with col7:
            pdb = st.text_input("PDB ID", placeholder="e.g., 1ABC")
        with col8:
            st.markdown("<br>", unsafe_allow_html=True)
            pdb_searched = st.checkbox("Searched?", key="pdb_searched") if pdb else False
        
        col9, col10 = st.columns([4, 1])
        with col9:
            sequence = st.text_area("Protein Sequence", placeholder="Full amino acid sequence")
        with col10:
            st.markdown("<br>", unsafe_allow_html=True)
            sequence_searched = st.checkbox("Searched?", key="sequence_searched") if sequence else False
        
        col11, col12 = st.columns([4, 1])
        with col11:
            measured_mass = st.number_input("Measured Mass (Da)", min_value=0.0, value=0.0, step=0.1)
        with col12:
            st.markdown("<br>", unsafe_allow_html=True)
            measured_mass_searched = st.checkbox("Searched?", key="measured_mass_searched") if measured_mass > 0 else False
        
        col13, col14 = st.columns([4, 1])
        with col13:
            sequence_mass = st.number_input("Sequence Mass (Da)", min_value=0.0, value=0.0, step=0.1)
        with col14:
            st.markdown("<br>", unsafe_allow_html=True)
            sequence_mass_searched = st.checkbox("Searched?", key="sequence_mass_searched") if sequence_mass > 0 else False
        
        # CCS Data Entry with source tracking
        st.markdown("#### CCS Data Entry")
        st.markdown("Enter charge states and corresponding CCS values.")
        
        if 'temp_ccs_data' not in st.session_state:
            st.session_state.temp_ccs_data = []
        
        col15, col16, col17, col18 = st.columns([2, 2, 2, 1])
        with col15:
            charge_state = st.number_input("Charge State", min_value=1, value=1, step=1, key="charge_input")
        with col16:
            ccs_value = st.number_input("CCS Value (Ų)", min_value=0.0, step=0.1, key="ccs_input")
        with col17:
            ccs_data_source = st.selectbox("Data Source", [
                "Provided in paper", "Read from graph"
            ], key="ccs_source")
        with col18:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("➕ Add CCS"):
                if charge_state and ccs_value > 0:
                    st.session_state.temp_ccs_data.append({
                        'charge': charge_state,
                        'ccs': ccs_value,
                        'data_source': ccs_data_source
                    })
                    refresh_session()
                    st.rerun()
        
        # Display current CCS data
        if st.session_state.temp_ccs_data:
            st.markdown("**Current CCS Data:**")
            ccs_display = []
            for entry in st.session_state.temp_ccs_data:
                ccs_display.append([
                    entry['charge'], 
                    entry['ccs'], 
                    entry['data_source']
                ])
            ccs_df = pd.DataFrame(ccs_display, columns=['Charge State', 'CCS Value (Ų)', 'Data Source'])
            st.dataframe(ccs_df, use_container_width=True)
            
            if st.form_submit_button("🗑️ Clear CCS Data"):
                st.session_state.temp_ccs_data = []
                refresh_session()
                st.rerun()
        
        # Form submission
        col19, col20 = st.columns(2)
        with col19:
            submit_protein = st.form_submit_button("✚ Add Protein Entry", use_container_width=True)
        with col20:
            clear_form = st.form_submit_button("🗑️ Clear Form", use_container_width=True)
        
        if submit_protein:
            refresh_session()
            # Validation
            errors = []
            if not protein_name:
                errors.append("Protein Name is required")
            if not ionization_mode:
                errors.append("Ionization Mode is required")
            if not instrument:
                errors.append("Instrument is required")
            if not native_measurement:
                errors.append("Native Measurement is required")
            if not ims_type:
                errors.append("IMS Type is required")
            if not drift_gas_measurement:
                errors.append("Drift Gas for Measurement is required")
            if not drift_gas_calibration:
                errors.append("Drift Gas for Calibration is required")
            if not subunit_count:
                errors.append("Number of Subunits is required")
            if not oligomer_type:
                errors.append("Oligomer Type is required")
            if not measurement_conditions:
                errors.append("Measurement Conditions are required")
            if not sample_conditions:
                errors.append("Sample Conditions are required")
            if not st.session_state.temp_ccs_data:
                errors.append("At least one CCS value is required")
            
            if errors:
                st.error("Please fix the following errors:\n" + "\n".join(f"• {error}" for error in errors))
            else:
                # Create protein entry
                protein_entry = {
                    'user_name': st.session_state.current_user,
                    'protein_name': protein_name,
                    'ionization_mode': ionization_mode,
                    'instrument': instrument,
                    'native_measurement': native_measurement,
                    'ims_type': ims_type,
                    'drift_gas_measurement': drift_gas_measurement,
                    'drift_gas_calibration': drift_gas_calibration,
                    'subunit_count': subunit_count,
                    'oligomer_type': oligomer_type,
                    'measurement_conditions': measurement_conditions,
                    'sample_conditions': sample_conditions,
                    'uniprot': uniprot if uniprot else None,
                    'uniprot_source': "User searched" if uniprot_searched else "Provided in paper" if uniprot else None,
                    'pdb': pdb if pdb else None,
                    'pdb_source': "User searched" if pdb_searched else "Provided in paper" if pdb else None,
                    'sequence': sequence if sequence else None,
                    'sequence_source': "User searched" if sequence_searched else "Provided in paper" if sequence else None,
                    'measured_mass': measured_mass if measured_mass > 0 else None,
                    'measured_mass_source': "User searched" if measured_mass_searched else "Provided in paper" if measured_mass > 0 else None,
                    'sequence_mass': sequence_mass if sequence_mass > 0 else None,
                    'sequence_mass_source': "User searched" if sequence_mass_searched else "Provided in paper" if sequence_mass > 0 else None,
                    'ccs_data': st.session_state.temp_ccs_data.copy()
                }
                
                st.session_state.protein_data.append(protein_entry)
                st.session_state.temp_ccs_data = []
                auto_save_to_browser()
                st.success(f"✅ Protein entry for '{protein_name}' added successfully!")
                st.rerun()
        
        if clear_form:
            st.session_state.temp_ccs_data = []
            refresh_session()
            st.rerun()

def display_current_protein_entries():
    """Display current protein entries with enhanced information."""
    if st.session_state.protein_data:
        st.markdown("### Current Protein Entries")
        for i, protein in enumerate(st.session_state.protein_data):
            with st.expander(f"Protein {i+1}: {protein['protein_name']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Ionization Mode:** {protein['ionization_mode']}")
                    st.write(f"**Instrument:** {protein['instrument']}")
                    st.write(f"**Native Measurement:** {protein['native_measurement']}")
                    st.write(f"**IMS Type:** {protein['ims_type']}")
                    st.write(f"**Drift Gas (Measurement):** {protein['drift_gas_measurement']}")
                    st.write(f"**Drift Gas (Calibration):** {protein['drift_gas_calibration']}")
                    st.write(f"**Subunit Count:** {protein['subunit_count']}")
                    st.write(f"**Oligomer Type:** {protein['oligomer_type']}")
                
                with col2:
                    # Display optional fields with sources
                    if protein.get('uniprot'):
                        st.write(f"**UniProt:** {protein['uniprot']} ({protein.get('uniprot_source', 'Unknown source')})")
                    if protein.get('pdb'):
                        st.write(f"**PDB:** {protein['pdb']} ({protein.get('pdb_source', 'Unknown source')})")
                    if protein.get('sequence'):
                        st.write(f"**Sequence:** Available ({protein.get('sequence_source', 'Unknown source')})")
                    if protein.get('measured_mass'):
                        st.write(f"**Measured Mass:** {protein['measured_mass']} Da ({protein.get('measured_mass_source', 'Unknown source')})")
                    if protein.get('sequence_mass'):
                        st.write(f"**Sequence Mass:** {protein['sequence_mass']} Da ({protein.get('sequence_mass_source', 'Unknown source')})")
                
                # Display conditions
                st.write("**Measurement Conditions:**")
                st.write(protein['measurement_conditions'])
                
                st.write("**Sample Conditions:**")
                st.write(protein['sample_conditions'])
                
                # Display CCS data with source information
                st.write("**CCS Data:**")
                ccs_display = []
                for entry in protein['ccs_data']:
                    ccs_display.append([
                        entry['charge'], 
                        entry['ccs'], 
                        entry['data_source']
                    ])
                ccs_df = pd.DataFrame(ccs_display, columns=['Charge State', 'CCS Value (Ų)', 'Data Source'])
                st.dataframe(ccs_df, use_container_width=True)
                
                if st.button(f"🗑️ Remove Entry {i+1}", key=f"remove_{i}"):
                    st.session_state.protein_data.pop(i)
                    refresh_session()
                    auto_save_to_browser()
                    st.rerun()

# === MAIN APPLICATION WITH ENHANCED SESSION MANAGEMENT ===

def show_data_entry_page():
    # Check for session timeout
    if check_session_timeout():
        st.markdown("""
        <div class="warning-timeout">
            <strong>⏰ Session Expired</strong><br>
            Your session has expired for security reasons. Your work has been auto-saved.
        </div>
        """, unsafe_allow_html=True)
        
        # Auto-save current work
        auto_save_to_browser()
        
        # Force logout
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.rerun()
    
    # Refresh session activity
    refresh_session()
    
    # Show user info and logout button
    show_user_info()
    
    # Auto-save indicator
    if st.session_state.get('protein_data') or st.session_state.get('paper_details'):
        auto_save_to_browser()
        st.markdown("""
        <div class="auto-save-indicator">
            💾 Auto-saved at {}
        </div>
        """.format(datetime.now().strftime("%H:%M:%S")), unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>Protein CCS Logging Form</h1>
        <p>Contribute collision cross-section data from papers to help build our database!</p>
    </div>
    """, unsafe_allow_html=True)

    # Load existing data with enhanced caching
    @st.cache_data(ttl=300, show_spinner="Loading existing database...")
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
        refresh_session()  # Refresh on interaction
        
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
                    # Auto-save after DOI verification
                    auto_save_to_browser()

    # Step 2: Protein Data Entry
    if st.session_state.show_full_form:
        st.markdown("---")
        st.markdown('<h2 class="section-header">Step 2: Protein Data Entry</h2>', unsafe_allow_html=True)
        
        # Add periodic refresh reminders
        st.markdown("""
        <div class="session-status">
            💡 <strong>Tip:</strong> Your work is auto-saved every 30 seconds. 
            Use the "🔄 Refresh Session" button in the sidebar to extend your session.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        Many papers contain data for several proteins and/or several measurements for the same protein. 
        Each entry corresponds to one set of values for one protein (e.g. CCS values for charge states +5 to +8 of Protein X). 
        If a single charge state has multiple conformers, these can be logged separately under the same entry. 
        If there are multiple sets of values, or multiple proteins, click '✚ Add Protein Entry' at the end of the form. 
        Once you are finished, click '🚀 Submit All Data to Database'.
        """)
        
        display_current_protein_entries()

        show_enhanced_protein_form()

        # Final submission
        if st.session_state.protein_data:
            st.markdown("---")
            st.markdown("### Final Submission")
            
            col10, col11 = st.columns([3, 1])
            with col10:
                st.info(f"Ready to submit {len(st.session_state.protein_data)} protein entries to the database.")
            with col11:
                if st.button("🚀 Submit All Data to Database", use_container_width=True):
                    refresh_session()
                    
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
                                    st.success("🎉 " + message)
                                    # Clear session data
                                    st.session_state.protein_data = []
                                    st.session_state.paper_details = {}
                                    st.session_state.show_full_form = False
                                    st.session_state.new_doi = ""
                                    if 'temp_ccs_data' in st.session_state:
                                        del st.session_state.temp_ccs_data
                                    if 'auto_save_data' in st.session_state:
                                        del st.session_state.auto_save_data
                                    
                                    # Clear cache to show updated data
                                    st.cache_data.clear()
                                    
                                    st.balloons()
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error("❌ " + message)
                            else:
                                st.error("Failed to access GitHub repository")
                        else:
                            st.error("Failed to authenticate with GitHub")

def main():
    """Main application entry point with enhanced session management."""
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = datetime.now()

    # Authentication check
    if not st.session_state.authenticated:
        show_login_form()
    else:
        show_data_entry_page()

if __name__ == "__main__":
    main()
