import streamlit as st
import pandas as pd
import re
import requests
from datetime import datetime
from github import Github, GithubException
from io import StringIO

# Page config
st.set_page_config(
    page_title="CCS Data Entry",
    page_icon="📝",
    layout="wide"
)

# Clean CSS styling to match home page
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
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        color: white;
        font-size: 2.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    /* Section headers */
    .section-header {
        color: #1f2937;
        font-size: 1.3rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
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
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {
        border-radius: 6px;
        border: 1px solid #d1d5db;
        font-family: 'Inter', sans-serif;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 1px #3b82f6;
    }
    
    /* Info boxes */
    .info-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .success-box {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 4px solid #22c55e;
        border-radius: 6px;
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
    
    .error-box {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        border-left: 4px solid #ef4444;
        border-radius: 6px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Form styling */
    .stForm {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 500;
        color: #1f2937;
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

# --- Helper Functions ---

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
        _ = g.get_user().login  # Test auth
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
    from io import StringIO
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

# --- Main Page ---

def show_data_entry_page():
    st.markdown('<h1 class="main-title">📝 Collision Cross Section Data Entry</h1>', unsafe_allow_html=True)

    @st.cache_data(ttl=600)
    def load_existing_data():
        g = authenticate_github()
        if g:
            repo = get_repository(g, st.secrets["REPO_NAME"])
            if repo:
                return get_existing_data_from_github(repo, st.secrets["CSV_PATH"])
        return pd.DataFrame()

    existing_data = load_existing_data()

    # DOI input and check
    with st.expander("📄 DOI Verification", expanded=True):
        st.markdown("Check if this paper already exists in our database")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            doi = st.text_input("Enter DOI", placeholder="e.g., 10.1021/example", key="doi_input")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
            check_button = st.button("Check DOI", use_container_width=True)

        if check_button and doi:
            if not validate_doi(doi):
                st.markdown("""
                <div class="error-box">
                    <strong>❌ Invalid DOI Format</strong><br>
                    Please enter a valid DOI (e.g., 10.1021/example)
                </div>
                """, unsafe_allow_html=True)
            else:
                paper_details = get_paper_details(doi)
                if check_doi_exists(existing_data, doi):
                    st.markdown(f"""
                    <div class="warning-box">
                        <strong>⚠️ Paper Already Exists</strong><br>
                        This paper (DOI: {doi}) is already in the database.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    paper_entries = existing_data[existing_data['doi'] == doi]
                    st.write(f"Found {len(paper_entries)} entries from this paper:")
                    st.dataframe(paper_entries, use_container_width=True)
                    st.session_state.show_full_form = False
                else:
                    st.markdown(f"""
                    <div class="success-box">
                        <strong>✅ Paper Not Found</strong><br>
                        This paper (DOI: {doi}) is not in the database. You can proceed with data entry.
                    </div>
                    """, unsafe_allow_html=True)
                    st.session_state.new_doi = doi
                    st.session_state.show_full_form = True
                    st.session_state.paper_details = paper_details
                    st.session_state.protein_data = []

    # Show protein data form
    if st.session_state.get('show_full_form', False):
        st.markdown('<h2 class="section-header">🧬 Protein Data Entry</h2>', unsafe_allow_html=True)
        st.markdown(f"**Paper:** {st.session_state.paper_details['paper_title']}")
        st.markdown("---")

        with st.form("protein_form", clear_on_submit=False):
            # User selection dropdown
            col1, col2 = st.columns([1, 1])
            with col1:
                user_name = st.selectbox("Your Name", [
                    "Select your name...",
                    "Ana",
                    "Perdi", 
                    "Tom",
                    "Hari",
                    "Wei",
                    "Jason",
                    "Charlie"
                ], key="user_name")
            
            with col2:
                protein_name = st.text_input("Protein/Ion Name", placeholder="e.g., Cytochrome C", key="protein_name")

            # Instrument details
            col1, col2 = st.columns([1, 1])
            with col1:
                instrument = st.selectbox("Instrument Used", [
                    "Select instrument...",
                    "Waters Synapt", 
                    "Waters Cyclic", 
                    "Waters Vion", 
                    "Agilent 6560", 
                    "Bruker timsTOF", 
                    "Other"
                ], key="instrument")
                
                if instrument == "Other":
                    instrument = st.text_input("Specify Instrument", key="instrument_other")
            
            with col2:
                ims_type = st.selectbox("IMS Type", [
                    "Select IMS type...",
                    "TWIMS", 
                    "DTIMS", 
                    "CYCLIC", 
                    "TIMS", 
                    "FAIMS", 
                    "Other"
                ], key="ims_type")
                
                if ims_type == "Other":
                    ims_type = st.text_input("Specify IMS Type", key="ims_type_other")

            # Gas and mode
            col1, col2 = st.columns([1, 1])
            with col1:
                drift_gas = st.selectbox("Drift Gas", [
                    "Select drift gas...",
                    "Nitrogen", 
                    "Helium", 
                    "Argon", 
                    "Other"
                ], key="drift_gas")
                
                if drift_gas == "Other":
                    drift_gas = st.text_input("Specify Drift Gas", key="drift_gas_other")
            
            with col2:
                ionization_mode = st.selectbox("Ionization Mode", [
                    "Select mode...",
                    "Positive",
                    "Negative"
                ], key="ionization_mode")

            # Protein identifiers section
            st.markdown("#### 🏷️ Optional Protein Identifiers")
            st.markdown("*Leave blank if not available*")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                uniprot_id = st.text_input("Uniprot ID", placeholder="e.g., P12345", key="uniprot_id")
                sequence_mass_value = st.number_input("Sequence Mass (Da)", min_value=0.0, value=0.0, format="%.2f", key="sequence_mass_value")
            
            with col2:
                pdb_id = st.text_input("PDB ID", placeholder="e.g., 1ABC", key="pdb_id")
                measured_mass_value = st.number_input("Measured Mass (Da)", min_value=0.0, value=0.0, format="%.2f", key="measured_mass_value")

            protein_sequence = st.text_area("Protein Sequence", placeholder="Enter amino acid sequence...", key="protein_sequence")

            # Measurement details
            st.markdown("#### ⚗️ Measurement Details")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                native_measurement = st.radio("Native measurement?", ["Yes", "No"], key="native_measurement")
                subunit_count = st.number_input("Number of Subunits", min_value=1, step=1, key="subunit_count")
            
            with col2:
                oligomer_type = ""
                if subunit_count > 1:
                    oligomer_type = st.radio("Oligomer Type", [
                        "Not applicable",
                        "Homo-oligomer", 
                        "Hetero-oligomer"
                    ], key="oligomer_type")

            # CCS Values section
            st.markdown("#### 📊 CCS Values")
            
            if ionization_mode not in ["Select mode...", ""]:
                num_ccs_values = st.number_input("Number of charge states", min_value=1, step=1, key="num_ccs_values")
                
                ccs_data = []
                for i in range(int(num_ccs_values)):
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        charge_state = st.number_input(f"Charge State {i+1}", min_value=1, step=1, key=f"charge_{i}")
                    with col2:
                        ccs_value = st.number_input(f"CCS Value {i+1} (Å²)", min_value=0.0, format="%.2f", key=f"ccs_{i}")
                    ccs_data.append((charge_state, ccs_value))
            else:
                st.info("Please select ionization mode to enter CCS values")
                ccs_data = []

            additional_notes = st.text_area("Additional Notes", placeholder="Sample preparation, instrument settings, etc.", key="additional_notes")

            # Validation and submit
            submit_protein = st.form_submit_button("Add Protein Data", use_container_width=True)

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
                        st.error(f"❌ {error}")
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
                    
                    st.success("✅ Protein data added successfully!")

        # Show entered data review
        if st.session_state.get('protein_data', []):
            st.markdown('<h2 class="section-header">📋 Review Entered Data</h2>', unsafe_allow_html=True)
        
            # Initialize selection list if it doesn't exist
            if 'selected_proteins' not in st.session_state:
                st.session_state.selected_proteins = [True] * len(st.session_state.protein_data)

            # Ensure selected_proteins is correctly initialized and sized
            if "selected_proteins" not in st.session_state:
                st.session_state.selected_proteins = [True] * len(st.session_state.protein_data)
            else:
                # Extend or truncate to match protein_data length
                diff = len(st.session_state.protein_data) - len(st.session_state.selected_proteins)
                if diff > 0:
                    st.session_state.selected_proteins.extend([True] * diff)
                elif diff < 0:
                    st.session_state.selected_proteins = st.session_state.selected_proteins[:len(st.session_state.protein_data)]

        
            for i, protein in enumerate(st.session_state.protein_data):
                with st.expander(f"Protein {i+1}: {protein['protein_name']}", expanded=False):
                    row = st.columns([5, 1])  # Wide column for data, narrow column for checkbox
                    with row[0]:
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            st.markdown(f"**User:** {protein['user_name']}")
                            st.markdown(f"**Instrument:** {protein['instrument']}")
                            st.markdown(f"**IMS Type:** {protein['ims_type']}")
                            st.markdown(f"**Drift Gas:** {protein['drift_gas']}")
                            st.markdown(f"**Mode:** {protein['ionization_mode']}")
                        with col2:
                            st.markdown(f"**Native:** {protein['native_measurement']}")
                            st.markdown(f"**Subunits:** {protein['subunit_count']}")
                            if protein['oligomer_type']:
                                st.markdown(f"**Oligomer:** {protein['oligomer_type']}")
                        
                        st.markdown("**CCS Values:**")
                        for charge, ccs in protein['ccs_data']:
                            st.markdown(f"- Charge {charge}: {ccs} Å²")
                        
                        if protein['additional_notes']:
                            st.markdown(f"**Notes:** {protein['additional_notes']}")
                    
                    with row[1]:
                        st.markdown("### ")
                        st.session_state.selected_proteins[i] = st.checkbox(
                            "✅ Keep",
                            value=st.session_state.selected_proteins[i],
                            key=f"select_protein_{i}",
                            help="Uncheck to exclude this protein from submission"
                        )

        
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("➕ Add Another Protein", use_container_width=True):
                    pass  # Keep form open for new entry
        
            with col2:
                if st.button("🗑️ Clear All Data", use_container_width=True):
                    st.session_state.protein_data = []
                    st.session_state.selected_proteins = []
                    st.rerun()
        
            with col3:
                submit_all = st.button("✅ Submit All Data", use_container_width=True)
        
            if submit_all:
                with st.spinner("Submitting data to GitHub..."):
                    selected_proteins = [
                        protein for protein, selected in zip(st.session_state.protein_data, st.session_state.selected_proteins) if selected
                    ]
        
                    if not selected_proteins:
                        st.warning("⚠️ Please select at least one protein to submit.")
                    else:
                        all_proteins = []
                        for protein in selected_proteins:
                            combined = {
                                **st.session_state.paper_details,
                                **protein,
                                "submission_timestamp": datetime.now().isoformat()
                            }
                            all_proteins.append(combined)
        
                        new_df = pd.DataFrame(all_proteins)
        
                        # Merge with existing data
                        if not existing_data.empty:
                            combined_df = pd.concat([existing_data, new_df], ignore_index=True)
                            combined_df.sort_values("submission_timestamp", ascending=False, inplace=True)
                            combined_df.drop_duplicates(subset=["protein_name", "doi"], keep="first", inplace=True)
                        else:
                            combined_df = new_df
        
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
                                    st.session_state.selected_proteins = []
                                    st.session_state.show_full_form = False
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                        else:
                            st.error("❌ GitHub authentication failed. Cannot save data.")


# Run app
if __name__ == "__main__":
    if "show_full_form" not in st.session_state:
        st.session_state.show_full_form = False
    if "protein_data" not in st.session_state:
        st.session_state.protein_data = []
    show_data_entry_page()

