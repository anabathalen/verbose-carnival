import os
import io
import zipfile
import numpy as np
import pandas as pd
import streamlit as st
from pathlib import Path
from tempfile import TemporaryDirectory

# === PAGE CONFIGURATION ===
st.set_page_config(
    page_title="Get Inputs",
    page_icon="➡️",
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

st.markdown('<div class="main-header"><h1>Get IMSCal Input Files</h1><p>Generate input files for IMSCal calibration from your sample data</p></div>', unsafe_allow_html=True)

st.markdown("""
<div class="info-card">
    <p>To use IMSCal, you need a reference file and an input file. The reference file is your calibrant information (if you haven't got this yet, go to 'calibrate'), and the input file is your data to be calibrated. Just as for the calibration, make a folder per sample and within that make a text file for each charge state (called e.g. '1.txt', '2.txt' etc.). Paste the corresponding ATD from MassLynx into each one. Zip the folders together and upload it here.</p>
    <p><strong>Note:</strong> This step is not doing any fitting! All it does is generates an input for IMSCal, which will then convert ATDs to CCSDs.</p>
</div>
""", unsafe_allow_html=True)

def handle_zip_upload(uploaded_file):
    temp_dir = '/tmp/samples_extracted/'
    
    if os.path.exists(temp_dir):
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

    os.makedirs(temp_dir, exist_ok=True)

    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    folders = [f for f in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, f))]
    if not folders:
        st.markdown('<div class="error-card">No folders found in the ZIP file.</div>', unsafe_allow_html=True)
        return [], temp_dir
    return folders, temp_dir


def process_sample_folder(folder_name, folder_path, mass, drift_mode, inject_time=None):
    sample_output = io.BytesIO()
    dat_files = {}
    processed_files = []
    failed_files = []

    output_folder = os.path.join(folder_path, folder_name)
    os.makedirs(output_folder, exist_ok=True)

    sample_folder_path = os.path.join(folder_path, folder_name)
    
    if not os.path.exists(sample_folder_path):
        return output_folder, processed_files, failed_files

    for filename in os.listdir(sample_folder_path):
        if filename.endswith('.txt') and filename[0].isdigit():
            file_path = os.path.join(sample_folder_path, filename)
            
            try:
                data = np.loadtxt(file_path)
                
                # Handle case where file might have different structure
                if data.ndim == 1:
                    st.warning(f"File {filename} in {folder_name} appears to have only one column. Expected two columns (drift_time, intensity).")
                    failed_files.append(f"{filename} - insufficient data columns")
                    continue
                
                if data.shape[1] < 2:
                    st.warning(f"File {filename} in {folder_name} has fewer than 2 columns. Expected (drift_time, intensity).")
                    failed_files.append(f"{filename} - insufficient data columns")
                    continue

                drift_time = data[:, 0]
                intensity = data[:, 1]

                if drift_mode == "Cyclic" and inject_time is not None:
                    drift_time = drift_time - inject_time

                drift_time = np.maximum(drift_time, 0)  # avoid negative times

                index = np.arange(len(drift_time))
                df = pd.DataFrame({
                    "index": index,
                    "mass": mass,
                    "charge": filename[:-4],
                    "intensity": intensity,
                    "drift_time": drift_time
                })

                dat_filename = f"input_{os.path.splitext(filename)[0]}.dat"
                dat_path = os.path.join(output_folder, dat_filename)
                df.to_csv(dat_path, sep=' ', index=False, header=False)
                processed_files.append(filename)
                
            except Exception as e:
                st.warning(f"Error processing file {filename} in {folder_name}: {str(e)}")
                failed_files.append(f"{filename} - {str(e)}")
    
    return output_folder, processed_files, failed_files

def generate_output_zip(sample_folders_paths):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for sample_folder in sample_folders_paths:
            for root, _, files in os.walk(sample_folder):
                for file in files:
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, os.path.dirname(sample_folder))
                    zipf.write(full_path, arcname=relative_path)
    return zip_buffer

# Main Streamlit app
def generate_input_dat_files_app():
    
    # Step 1: Upload ZIP file
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-header">📁 Upload Sample Data</h3>', unsafe_allow_html=True)
    uploaded_zip_file = st.file_uploader("Upload ZIP containing sample protein folders", type="zip")
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_zip_file is not None:
        sample_folders, base_path = handle_zip_upload(uploaded_zip_file)
        
        if not sample_folders:
            return

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header">⚙️ Instrument Settings</h3>', unsafe_allow_html=True)
        
        drift_mode = st.radio("Which instrument did you use?", options=["Cyclic", "Synapt"])
        inject_time = None
        if drift_mode == "Cyclic":
            inject_time = st.number_input("Enter inject time to subtract (ms)", min_value=0.0, value=12.0)
        
        st.markdown('</div>', unsafe_allow_html=True)

        all_sample_paths = []

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header">🧬 Sample Information</h3>', unsafe_allow_html=True)
        st.write("Enter the molecular mass (Da) for each sample protein:")

        with st.form("sample_mass_form"):
            sample_mass_map = {}
            
            # Create columns for better layout
            if len(sample_folders) > 1:
                cols = st.columns(min(3, len(sample_folders)))
                for i, sample in enumerate(sample_folders):
                    with cols[i % len(cols)]:
                        st.markdown(f'<div class="protein-card">', unsafe_allow_html=True)
                        st.markdown(f'<strong>{sample}</strong>')
                        mass = st.number_input(f"Mass (Da)", min_value=0.0, key=sample, label_visibility="collapsed")
                        sample_mass_map[sample] = mass
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                for sample in sample_folders:
                    st.markdown(f'<div class="protein-card">', unsafe_allow_html=True)
                    mass = st.number_input(f"Mass of '{sample}' (Da)", min_value=0.0, key=sample)
                    sample_mass_map[sample] = mass
                    st.markdown('</div>', unsafe_allow_html=True)
            
            submitted = st.form_submit_button("🔬 Generate .dat Files")

        st.markdown('</div>', unsafe_allow_html=True)

        if submitted:
            # Validate that masses are provided
            missing_masses = [sample for sample, mass in sample_mass_map.items() if mass == 0.0]
            if missing_masses:
                st.markdown('<div class="warning-card">', unsafe_allow_html=True)
                st.write("⚠️ Please provide masses for the following samples:")
                for sample in missing_masses:
                    st.write(f"• {sample}")
                st.markdown('</div>', unsafe_allow_html=True)
                return

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-header">🔄 Processing Status</h3>', unsafe_allow_html=True)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            all_processed_files = {}
            all_failed_files = {}
            
            with TemporaryDirectory() as tmp_output_dir:
                for i, sample in enumerate(sample_folders):
                    status_text.text(f"Processing {sample}...")
                    progress_bar.progress((i + 1) / len(sample_folders))
                    
                    sample_path, processed_files, failed_files = process_sample_folder(
                        folder_name=sample,
                        folder_path=base_path,
                        mass=sample_mass_map[sample],
                        drift_mode=drift_mode,
                        inject_time=inject_time
                    )
                    all_sample_paths.append(sample_path)
                    all_processed_files[sample] = processed_files
                    all_failed_files[sample] = failed_files

                # Show processing results
                st.markdown('<div class="success-card">', unsafe_allow_html=True)
                st.write("✅ **Processing Complete!**")
                
                total_processed = sum(len(files) for files in all_processed_files.values())
                total_failed = sum(len(files) for files in all_failed_files.values())
                
                st.write(f"• Successfully processed: **{total_processed}** files")
                if total_failed > 0:
                    st.write(f"• Failed to process: **{total_failed}** files")
                st.markdown('</div>', unsafe_allow_html=True)

                # Show detailed results
                with st.expander("📊 Detailed Processing Results"):
                    for sample in sample_folders:
                        st.write(f"**{sample}:**")
                        if all_processed_files[sample]:
                            st.write(f"  ✅ Processed: {', '.join(all_processed_files[sample])}")
                        if all_failed_files[sample]:
                            st.write(f"  ❌ Failed: {', '.join(all_failed_files[sample])}")

                if total_processed > 0:
                    zip_buffer = generate_output_zip(all_sample_paths)

                    st.markdown('<div class="section-card">', unsafe_allow_html=True)
                    st.markdown('<h3 class="section-header">📥 Download Results</h3>', unsafe_allow_html=True)
                    
                    st.download_button(
                        label="📦 Download All .dat Files (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name="sample_dat_files.zip",
                        mime="application/zip"
                    )
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-card">No files were successfully processed. Please check your data format and try again.</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

generate_input_dat_files_app()
