import streamlit as st
import pandas as pd
import re
import requests
from datetime import datetime
from github import Github, GithubException
from io import StringIO

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

    # Main content
    # Step 1: DOI Verification
    st.markdown("---")
    st.markdown('<h2 class="section-header">Step 1: DOI Verification</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <strong>ℹ️ Instructions</strong><br>
        Enter the DOI of your paper to check if it already exists in our database and retrieve publication details automatically.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    with col1:
        doi = st.text_input(
            "📝 Enter DOI", 
            placeholder="e.g., 10.1021/acs.jproteome.2023.example",
            help="Digital Object Identifier"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        check_button = st.button("🔍 Verify DOI", use_container_width=True)

    if check_button and doi:
        if not validate_doi(doi):
            st.markdown("""
            <div class="error-card">
                <strong>❌ Invalid DOI Format</strong><br>
                Please enter a valid DOI starting with '10.' followed by publisher and article identifiers.
            </div>
            """, unsafe_allow_html=True)
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
                    st.session_state.protein_data = []

    st.markdown('</div>', unsafe_allow_html=True)

    # Step 2: Protein Data Entry
    if st.session_state.get('show_full_form', False):
        st.markdown("---")
        st.markdown('<h2 class="section-header">Step 2: Protein Data Entry</h2>', unsafe_allow_html=True)
        
        with st.form("protein_form", clear_on_submit=False):
            st.markdown("---")
            st.markdown("#### ⚙️ General Information")
            
            col1, col2 = st.columns(2)
            with col1:
                user_name = st.selectbox("Your Name", [
                    "Select your name...",
                    "Ana", "Perdi", "Tom", "Hari", "Wei", "Jason", "Charlie"
                ], help="Select your name from the dropdown")
            
            with col2:
                protein_name = st.text_input(
                    "Protein Name", 
                    placeholder="e.g., Cytochrome C, Ubiquitin",
                    help="Enter the name of the protein or ion studied"
                )
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### 👩‍🔬 Experimental Setup")
            
            col1, col2 = st.columns(2)
            with col1:
                instrument = st.selectbox("Instrument Used", [
                    "Select instrument...",
                    "Waters Synapt", "Waters Cyclic", "Waters Vion", 
                    "Agilent 6560", "Bruker timsTOF", "Other"
                ])
                if instrument == "Other":
                    instrument = st.text_input("Specify Instrument")
                
                drift_gas = st.selectbox("Drift Gas", [
                    "Select drift gas...",
                    "Nitrogen", "Helium", "Argon", "Other"
                ])
                if drift_gas == "Other":
                    drift_gas = st.text_input("Specify Drift Gas")
            
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
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### 🏷️ Protein Identifiers (Optional)")
            
            col1, col2 = st.columns(2)
            with col1:
                uniprot_id = st.text_input("UniProt ID", placeholder="e.g., P12345")
                sequence_mass_value = st.number_input("Sequence Mass or Best Approximation (Da)", min_value=0.0, value=0.0, format="%.2f")
                protein_sequence = st.text_area("Protein Sequence", placeholder="Enter amino acid sequence...")
            
            with col2:
                pdb_id = st.text_input("PDB ID", placeholder="e.g., 1ABC")
                measured_mass_value = st.number_input("Measured Mass (Da)", min_value=0.0, value=0.0, format="%.2f")
                additional_notes = st.text_area("Additional Notes", placeholder="Sample preparation, instrument settings, etc.")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### 🔬 Measurement Details")
            
            col1, col2 = st.columns(2)
            with col1:
                native_measurement = st.radio("Native measurement?", ["Yes", "No"])
                subunit_count = st.number_input("Number of Subunits", min_value=1, step=1)
            
            with col2:
                oligomer_type = ""
                if subunit_count > 1:
                    oligomer_type = st.radio("Oligomer Type", [
                        "Not applicable", "Homo-oligomer", "Hetero-oligomer"
                    ])
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### 📊 CCS Values")
            
            if ionization_mode not in ["Select mode...", ""]:
                num_ccs_values = st.number_input("Number of charge states", min_value=1, step=1)
                
                ccs_data = []
                st.markdown("**Enter charge states and corresponding CCS values:**")
                
                for i in range(int(num_ccs_values)):
                    col1, col2 = st.columns(2)
                    with col1:
                        charge_state = st.number_input(f"Charge State {i+1}", min_value=1, step=1, key=f"charge_{i}")
                    with col2:
                        ccs_value = st.number_input(f"CCS Value {i+1} (Ų)", min_value=0.0, format="%.2f", key=f"ccs_{i}")
                    ccs_data.append((charge_state, ccs_value))
            else:
                st.info("⚠️ Please select ionization mode to enter CCS values")
                ccs_data = []
            st.markdown('</div>', unsafe_allow_html=True)

            # Submit button
            submit_protein = st.form_submit_button("➕ Add Protein Data", use_container_width=True)

            if submit_protein:
                # Validation
                errors = []
                if user_name == "Select your name...":
                    errors.append("Please select your name")
                if not protein_name.strip():
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
                    errors.append("Please enter at least one CCS value")

                if errors:
                    for error in errors:
                        st.markdown(f"""
                        <div class="error-card">
                            <strong>❌ {error}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    protein_entry = {
                        "user_name": user_name,
                        "protein_name": protein_name,
                        "instrument": instrument,
                        "ims_type": ims_type,
                        "drift_gas": drift_gas,
                        "ionization_mode": ionization_mode,
                        "uniprot": uniprot_id if uniprot_id else None,
                        "pdb": pdb_id if pdb_id else None,
                        "sequence": protein_sequence if protein_sequence else None,
                        "sequence_mass": sequence_mass_value if sequence_mass_value > 0 else None,
                        "measured_mass": measured_mass_value if measured_mass_value > 0 else None,
                        "native_measurement": native_measurement,
                        "subunit_count": subunit_count,
                        "oligomer_type": oligomer_type if oligomer_type and oligomer_type != "Not applicable" else None,
                        "ccs_data": ccs_data,
                        "additional_notes": additional_notes
                    }
                    
                    if 'protein_data' not in st.session_state:
                        st.session_state.protein_data = []
                    st.session_state.protein_data.append(protein_entry)
                    
                    st.markdown("""
                    <div class="success-card">
                        <strong>✅ Protein data added successfully!</strong><br>
                        You can add more proteins or proceed to review and submit.
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Step 3: Review and Submit
        if st.session_state.get('protein_data', []):
            st.markdown("---")
            st.markdown('<h2 class="section-header">📋 Step 3: Review & Submit</h2>', unsafe_allow_html=True)
            
            # Initialize selection list
            if 'selected_proteins' not in st.session_state:
                st.session_state.selected_proteins = [True] * len(st.session_state.protein_data)
            else:
                diff = len(st.session_state.protein_data) - len(st.session_state.selected_proteins)
                if diff > 0:
                    st.session_state.selected_proteins.extend([True] * diff)
                elif diff < 0:
                    st.session_state.selected_proteins = st.session_state.selected_proteins[:len(st.session_state.protein_data)]

            st.markdown(f"**Review your {len(st.session_state.protein_data)} protein entries:**")
            
            # Select/Deselect all buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Select All"):
                    st.session_state.selected_proteins = [True] * len(st.session_state.protein_data)
                    st.experimental_rerun()
            with col2:
                if st.button("❌ Deselect All"):
                    st.session_state.selected_proteins = [False] * len(st.session_state.protein_data)
                    st.experimental_rerun()
            
            for i, protein in enumerate(st.session_state.protein_data):
                with st.expander(f"🧬 Protein {i+1}: {protein['protein_name']}", expanded=False):
                    col1, col2 = st.columns([5, 1])
                    
                    with col1:
                        st.markdown('<div class="protein-card">', unsafe_allow_html=True)
                        
                        # Basic info
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown(f"**👤 User:** {protein['user_name']}")
                            st.markdown(f"**⚗️ Instrument:** {protein['instrument']}")
                            st.markdown(f"**🔬 IMS Type:** {protein['ims_type']}")
                            st.markdown(f"**💨 Drift Gas:** {protein['drift_gas']}")
                        with col_b:
                            st.markdown(f"**⚡ Mode:** {protein['ionization_mode']}")
                            st.markdown(f"**🧪 Native?:** {protein['native_measurement']}")
                            st.markdown(f"**🔗 Subunits:** {protein['subunit_count']}")
                            if protein['oligomer_type']:
                                st.markdown(f"**Protein Type:** {protein['oligomer_type']}")
                        
                        # CCS values with badges
                        st.markdown("**📊 CCS Values:**")
                        ccs_badges = ""
                        for charge, ccs in protein['ccs_data']:
                            ccs_badges += f'<span class="metric-badge">+{charge}: {ccs} Ų</span>'
                        st.markdown(ccs_badges, unsafe_allow_html=True)
                        
                        if protein['additional_notes']:
                            st.markdown(f"**📝 Notes:** {protein['additional_notes']}")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("### ")
                        st.session_state.selected_proteins[i] = st.checkbox(
                            "Include",
                            value=st.session_state.selected_proteins[i],
                            key=f"protein_select_{i}"
                        )
            
            # Summary and submit
            selected_count = sum(st.session_state.selected_proteins)
            st.markdown(f"**📊 Summary: {selected_count} of {len(st.session_state.protein_data)} proteins selected for submission**")
            
            if selected_count > 0:
                st.markdown("""
                <div class="info-card">
                    <strong>🚀 Ready to Submit</strong><br>
                    Your selected protein data will be added to the CCS database and made available to the research community.
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    if st.button("🎯 Submit Selected Data to Database", use_container_width=True):
                        # Filter selected proteins
                        selected_proteins = [
                            protein for i, protein in enumerate(st.session_state.protein_data) 
                            if st.session_state.selected_proteins[i]
                        ]
                        
                        if selected_proteins:
                            with st.spinner("Submitting data to GitHub..."):
                                try:
                                    # Convert to DataFrame
                                    new_df = convert_protein_data_to_dataframe(
                                        selected_proteins, 
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
                                                st.markdown(f"""
                                                <div class="success-card">
                                                    <strong>🎉 Success!</strong><br>
                                                    {message}<br>
                                                    Successfully submitted {len(selected_proteins)} protein entries with {sum(len(p['ccs_data']) for p in selected_proteins)} CCS measurements.
                                                </div>
                                                """, unsafe_allow_html=True)
                                                
                                                # Clear session state
                                                for key in ['protein_data', 'selected_proteins', 'show_full_form', 'paper_details', 'new_doi']:
                                                    if key in st.session_state:
                                                        del st.session_state[key]
                                                
                                                # Clear cache to refresh data
                                                st.cache_data.clear()
                                                
                                                st.balloons()
                                                
                                                if st.button("🔄 Start New Entry"):
                                                    st.experimental_rerun()
                                            
                                            else:
                                                st.markdown(f"""
                                                <div class="error-card">
                                                    <strong>❌ Submission Failed</strong><br>
                                                    {message}
                                                </div>
                                                """, unsafe_allow_html=True)
                                        else:
                                            st.error("Could not access GitHub repository")
                                    else:
                                        st.error("GitHub authentication failed")
                                        
                                except Exception as e:
                                    st.markdown(f"""
                                    <div class="error-card">
                                        <strong>❌ Unexpected Error</strong><br>
                                        An error occurred during submission: {str(e)}
                                    </div>
                                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("🗑️ Clear All Data"):
                        # Clear session state
                        for key in ['protein_data', 'selected_proteins', 'show_full_form', 'paper_details', 'new_doi']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.experimental_rerun()
            
            else:
                st.markdown("""
                <div class="warning-card">
                    <strong>⚠️ No Proteins Selected</strong><br>
                    Please select at least one protein entry to submit to the database.
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# === RUN APPLICATION ===
if __name__ == "__main__":
    show_data_entry_page()

