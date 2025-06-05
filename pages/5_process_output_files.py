import streamlit as st
import zipfile
import tempfile
import os
import pandas as pd
from io import BytesIO, StringIO

# === PAGE CONFIGURATION ===
st.set_page_config(
    page_title="Process Outputs",
    page_icon=" ⬅️",
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

# Main header with gradient styling
st.markdown("""
<div class="main-header">
    <h1>Process Output Files</h1>
    <p>Get a CCS value for Every Timepoint for Every Charge State of Every Protein</p>
</div>
""", unsafe_allow_html=True)

# Information card explaining the process
st.markdown("""
<div class="info-card">
    <p>This step is about finishing off the calibration. For many (most) purposes, it is useless and annoying that I have separated out this final part of the calibration from the generation of the full calibrated dataset, but for situations where you have done multiple experiments on the same protein (e.g. activated ion mobility), it is useful to only have to calibrate once.</p>
    
    <p>Here you are generating CCS values for every timepoint in the ATD for all the charge states of the proteins in your folders - if, for example, you have run Protein X at 5 different collision voltages, you only need to calibrate at one collision voltage.</p>
    
    <p><strong>Note:</strong> Once you have completed this step, go to 'Process and Plot Data' to finish the job. Again, no fitting is being done here.</p>
</div>
""", unsafe_allow_html=True)

def process_outputs_page():
    # File upload section with enhanced styling
    st.markdown("""
    <div class="section-card">
        <div class="section-header">📁 Upload Your Data</div>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_zip = st.file_uploader(
        "Upload a zipped folder containing your output files", 
        type="zip",
        help="Select a ZIP file containing folders with output_X.dat files"
    )
    
    if uploaded_zip:
        # Processing status
        st.markdown("""
        <div class="status-card info-card">
            <strong>🔄 Processing uploaded file...</strong>
        </div>
        """, unsafe_allow_html=True)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "uploaded.zip")
            with open(zip_path, "wb") as f:
                f.write(uploaded_zip.getvalue())
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            
            protein_data = {}
            files_processed = 0
            
            # Process files
            for root, dirs, files in os.walk(tmpdir):
                for file in files:
                    if file.startswith("output_") and file.endswith(".dat"):
                        file_path = os.path.join(root, file)
                        # Infer protein name from the first folder in the relative path
                        rel_path = os.path.relpath(file_path, tmpdir)
                        parts = rel_path.split(os.sep)
                        if len(parts) < 2:
                            continue
                        protein_name = parts[0]
                        
                        with open(file_path, 'r') as f:
                            lines = f.readlines()
                        
                        try:
                            cal_index = next(i for i, line in enumerate(lines) if line.strip() == "[CALIBRATED DATA]")
                            data_lines = lines[cal_index + 1:]
                        except StopIteration:
                            continue
                        
                        try:
                            df = pd.read_csv(StringIO(''.join(data_lines)))
                            df = df[['Z', 'Drift', 'CCS', 'CCS Std.Dev.']]
                            
                            if protein_name not in protein_data:
                                protein_data[protein_name] = []
                            protein_data[protein_name].append(df)
                            files_processed += 1
                        except Exception:
                            continue
            
            # Display results
            if protein_data:
                st.markdown(f"""
                <div class="status-card success-card">
                    <strong>✅ Processing Complete!</strong><br>
                    Found data for <span class="metric-badge">{len(protein_data)} proteins</span> 
                    from <span class="metric-badge">{files_processed} files</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Downloads section
                st.markdown("""
                <div class="section-card">
                    <div class="section-header">📥 Download Processed Data</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Create columns for organized download layout
                col1, col2 = st.columns(2)
                
                for i, (protein_name, dfs) in enumerate(protein_data.items()):
                    combined_df = pd.concat(dfs, ignore_index=True)
                    
                    # Show protein info card
                    st.markdown(f"""
                    <div class="protein-card">
                        <h4 style="color: #667eea; margin: 0 0 0.5rem 0;">🧬 {protein_name}</h4>
                        <p style="margin: 0; color: #64748b;">
                            <span class="metric-badge">{len(combined_df)} data points</span>
                            <span class="metric-badge">{len(dfs)} files combined</span>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Prepare download
                    buffer = BytesIO()
                    combined_df.to_csv(buffer, index=False)
                    buffer.seek(0)
                    
                    # Download button
                    st.download_button(
                        label=f"📊 Download {protein_name}.csv",
                        data=buffer,
                        file_name=f"{protein_name}.csv",
                        mime="text/csv",
                        key=f"download_{protein_name}"
                    )
                
                # Summary information
                st.markdown("""
                <div class="info-card">
                    <h4 style="color: #667eea; margin-top: 0;">📋 Next Steps</h4>
                    <p>Your processed data is now ready for download. Each CSV file contains:</p>
                    <ul>
                        <li><strong>Z:</strong> Charge state</li>
                        <li><strong>Drift:</strong> Drift time</li>
                        <li><strong>CCS:</strong> Collision cross-section value</li>
                        <li><strong>CCS Std.Dev.:</strong> Standard deviation</li>
                    </ul>
                    <p><strong>Ready to continue?</strong> Go to 'Process and Plot Data' to finish your analysis.</p>
                </div>
                """, unsafe_allow_html=True)
                
            else:
                st.markdown("""
                <div class="status-card warning-card">
                    <strong>⚠️ No Valid Data Found</strong><br>
                    No valid output_X.dat files were found in the uploaded ZIP file. 
                    Please ensure your ZIP contains folders with properly formatted output files.
                </div>
                """, unsafe_allow_html=True)
                
                # Help section
                st.markdown("""
                <div class="info-card">
                    <h4 style="color: #667eea; margin-top: 0;">📖 Expected File Structure</h4>
                    <p>Your ZIP file should contain:</p>
                    <pre style="background: #f1f5f9; padding: 1rem; border-radius: 6px; font-size: 0.9rem;">
your_data.zip/
├── Protein1/
│   ├── output_1.dat
│   ├── output_2.dat
│   └── ...
├── Protein2/
│   ├── output_1.dat
│   └── ...
└── ...</pre>
                    <p>Each output_X.dat file should contain a <code>[CALIBRATED DATA]</code> section.</p>
                </div>
                """, unsafe_allow_html=True)

process_outputs_page()
