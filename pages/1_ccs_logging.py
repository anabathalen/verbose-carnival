import streamlit as st
import pandas as pd
import re
import requests
from datetime import datetime
from github import Github, GithubException
from io import StringIO

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
    """Check if normalized DOI already exists in the dataframe, with debug output."""
    if existing_data is None or existing_data.empty or 'doi' not in existing_data.columns:
        st.info("Existing data is empty or missing a DOI column.")
        return False

    normalized_doi = normalize_doi(str(doi))

    st.markdown("### 🔍 Debugging DOI Check")
    st.write("**Raw DOIs in database:**")
    st.write(existing_data['doi'])

    normalized_existing = set(normalize_doi(str(x)) for x in existing_data['doi'].dropna())
    st.write("**Normalized DOIs in database:**")
    st.write(list(normalized_existing))

    st.write("**Normalized input DOI:**", normalized_doi)

    exists = normalized_doi in normalized_existing
    st.write("**Match found?**", exists)

    return exists

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
    st.title("Collision Cross Section Data Entry")

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
    with st.expander("DOI Check", expanded=True):
        st.markdown("### Check if paper already exists in database")
        col1, col2 = st.columns([3, 1])
        with col1:
            doi = st.text_input("Enter DOI (e.g., 10.1021/example)", key="doi_input")
        with col2:
            check_button = st.button("Check DOI")

        if check_button and doi:
            if not validate_doi(doi):
                st.error("Invalid DOI format. Please enter a valid DOI (e.g., 10.1021/example)")
            else:
                paper_details = get_paper_details(doi)
                if check_doi_exists(existing_data, doi):
                    st.warning(f"This paper (DOI: {doi}) already exists in the database!")
                    paper_entries = existing_data[existing_data['doi'] == doi]
                    st.write(f"Found {len(paper_entries)} entries from this paper:")
                    st.dataframe(paper_entries)
                    st.session_state.show_full_form = False
                else:
                    st.success(f"This paper (DOI: {doi}) is not yet in the database. Please proceed with data entry.")
                    st.session_state.new_doi = doi
                    st.session_state.show_full_form = True
                    st.session_state.paper_details = paper_details
                    st.session_state.protein_data = []

    # Show protein data form
    if st.session_state.get('show_full_form', False):
        st.header(f"Log Protein Data for Paper: {st.session_state.paper_details['paper_title']}")

        with st.form("protein_form", clear_on_submit=False):
            protein_name = st.text_input("Protein/Ion Name", key="protein_name")
            instrument = st.selectbox("Instrument Used", ["Waters Synapt", "Waters Cyclic", "Waters Vion", "Agilent 6560", 
                                                        "Bruker timsTOF", "Other (enter)"], key="instrument")
            ims_type = st.selectbox("IMS Type", ["TWIMS", "DTIMS", "CYCLIC", "TIMS", "FAIMS", "Other (enter)"], key="ims_type")
            drift_gas = st.selectbox("Drift Gas", ["Nitrogen", "Helium", "Argon", "Other"], key="drift_gas")
            if drift_gas == "Other":
                drift_gas = st.text_input("Specify Drift Gas", key="drift_gas_other")

            st.markdown("#### Optional Protein Identifiers (Leave blank if not available)")
            uniprot_id = st.text_input("Uniprot Identifier", key="uniprot_id")
            pdb_id = st.text_input("PDB Identifier", key="pdb_id")
            protein_sequence = st.text_area("Protein Sequence", key="protein_sequence")
            sequence_mass_value = st.number_input("Sequence Mass (Da)", min_value=0.0, value=0.0, format="%.2f", key="sequence_mass_value")
            measured_mass_value = st.number_input("Measured Mass (Da)", min_value=0.0, value=0.0, format="%.2f", key="measured_mass_value")

            native_measurement = st.radio("Is this a native measurement?", ["Yes", "No"], key="native_measurement")
            subunit_count = st.number_input("Number of Non-Covalently Linked Subunits", min_value=1, step=1, key="subunit_count")

            oligomer_type = ""
            if subunit_count > 1:
                oligomer_type = st.radio("If this is an oligomer (subunit count > 1), is it a homo or hetero-oligomer?", 
                                        ["", "Homo-oligomer", "Hetero-oligomer"], key="oligomer_type")

            num_ccs_values = st.number_input("How many CCS values for this protein?", min_value=1, step=1, key="num_ccs_values")
            ccs_data = []
            for i in range(num_ccs_values):
                charge_state = st.number_input(f"Charge State {i+1}", min_value=1, step=1, key=f"charge_{i}")
                ccs_value = st.number_input(f"CCS Value for Charge State {i+1} (Å²)", min_value=0.0, format="%.2f", key=f"ccs_{i}")
                ccs_data.append((charge_state, ccs_value))

            additional_notes = st.text_area("Additional Notes (sample, instrument, etc.)", key="additional_notes")

            submit_protein = st.form_submit_button("Ready to Submit")

            if submit_protein:
                protein_entry = {
                    "protein_name": protein_name,
                    "instrument": instrument,
                    "ims_type": ims_type,
                    "drift_gas": drift_gas,
                    "uniprot": uniprot_id if uniprot_id else None,
                    "pdb": pdb_id if pdb_id else None,
                    "sequence": protein_sequence if protein_sequence else None,
                    "sequence_mass": sequence_mass_value if sequence_mass_value > 0 else None,
                    "measured_mass": measured_mass_value if measured_mass_value > 0 else None,
                    "native_measurement": native_measurement,
                    "subunit_count": subunit_count,
                    "oligomer_type": oligomer_type if oligomer_type else None,
                    "ccs_data": ccs_data,
                    "additional_notes": additional_notes
                }
                if 'protein_data' not in st.session_state:
                    st.session_state.protein_data = []
                st.session_state.protein_data.append(protein_entry)

                more_proteins = st.radio("Do you want to log another protein?", ["Yes", "No"], key=f"more_{len(st.session_state.protein_data)}")
                if more_proteins == "No":
                    st.session_state.show_full_form = False

        # Show entered data review
        if st.session_state.get('protein_data', []):
            st.subheader("Review Entered Data")
            for i, protein in enumerate(st.session_state.protein_data):
                st.markdown(f"### Protein {i+1}")
                st.markdown(f"**Protein Name:** {protein['protein_name']}")
                st.markdown(f"**Instrument:** {protein['instrument']}")
                st.markdown(f"**IMS Type:** {protein['ims_type']}")
                st.markdown(f"**Drift Gas:** {protein['drift_gas']}")
                st.markdown(f"**Native Measurement:** {protein['native_measurement']}")
                st.markdown(f"**Subunits:** {protein['subunit_count']}")
                st.markdown(f"**Oligomer Type:** {protein['oligomer_type']}")
                st.markdown("**CCS Values:**")
                for charge, ccs in protein['ccs_data']:
                    st.markdown(f"- Charge {charge}: {ccs} Å²")
                st.markdown(f"**Notes:** {protein['additional_notes']}")

            # Final submit button
            submit_all = st.button("Submit All Protein Data")

            if submit_all:
                all_proteins = []
                for protein in st.session_state.protein_data:
                    combined = {
                        **st.session_state.paper_details,
                        **protein,
                        "submission_timestamp": datetime.now().isoformat()
                    }
                    all_proteins.append(combined)

                new_df = pd.DataFrame(all_proteins)

                # Merge with existing data and remove duplicates by protein_name and doi (keep latest)
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
                            st.success(message)
                            # Clear session state to reset form
                            st.session_state.protein_data = []
                            st.session_state.show_full_form = False
                        else:
                            st.error(message)
                else:
                    st.error("GitHub authentication failed. Cannot save data.")

# Run app
if __name__ == "__main__":
    if "show_full_form" not in st.session_state:
        st.session_state.show_full_form = False
    if "protein_data" not in st.session_state:
        st.session_state.protein_data = []
    show_data_entry_page()

