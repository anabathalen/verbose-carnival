import streamlit as st
import zipfile
import tempfile
import os
import pandas as pd
from io import BytesIO

# === PAGE CONFIGURATION ===
st.set_page_config(
    page_title="Calibrate ATDs",
    page_icon="⚖️",
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
    <h1>Calibrate Drift Files</h1>
    <p>Match calibration data with raw drift intensities to create calibrated datasets</p>
</div>
""", unsafe_allow_html=True)

# Information card explaining the process
st.markdown("""
<div class="info-card">
    <p>This step combines your raw drift time data with the calibration information from the previous step. 
    The process matches drift times from your calibration data with the corresponding intensities from your raw files.</p>
    
    <p><strong>What you'll need:</strong></p>
    <ul>
        <li>ZIP file containing raw drift files (X.txt format where X is the charge state)</li>
        <li>CSV files from the 'Process Output Files' step</li>
        <li>Information about your instrument type (Synapt or Cyclic)</li>
    </ul>
</div>
""", unsafe_allow_html=True)

def calibrate_drift_files_page():
    # Progress indicator
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <span class="progress-step completed">1</span>
        <span class="progress-step active">2</span>
        <span class="progress-step">3</span>
        <br>
        <small style="color: #64748b;">Process Outputs → <strong>Calibrate Drift</strong> → Plot Data</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Step 1: Upload drift files
    st.markdown("""
    <div class="section-card">
        <div class="section-header">📁 Step 1: Upload Raw Drift Files</div>
    </div>
    """, unsafe_allow_html=True)
    
    drift_zip = st.file_uploader(
        "Upload zipped folder of raw drift files", 
        type="zip",
        help="ZIP file should contain folders with X.txt files (where X is the charge state number)"
    )

    if drift_zip:
        st.markdown("""
        <div class="status-card success-card">
            <strong>✅ Drift files uploaded successfully!</strong>
        </div>
        """, unsafe_allow_html=True)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save the uploaded zipped drift files temporarily
            drift_zip_path = os.path.join(tmpdir, "drift.zip")
            with open(drift_zip_path, "wb") as f:
                f.write(drift_zip.getvalue())

            # Extract the drift files
            with zipfile.ZipFile(drift_zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)

            # Step 2: Instrument configuration
            st.markdown("""
            <div class="section-card">
                <div class="section-header">⚙️ Step 2: Instrument Configuration</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Instrument type selection with enhanced styling
            data_type = st.radio(
                "Select your instrument type:",
                ["Synapt", "Cyclic"],
                help="This affects how drift times are processed"
            )
            
            # Conditional input for Cyclic instruments
            inject_time = None
            if data_type == "Cyclic":
                st.markdown("""
                <div class="form-section">
                    <h4 style="color: #667eea; margin-top: 0;">Cyclic Instrument Settings</h4>
                    <p style="color: #64748b; margin-bottom: 1rem;">
                        For Cyclic instruments, specify the injection time to subtract from drift times.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                inject_time = st.number_input(
                    "Enter the injection time (ms)", 
                    min_value=0.0, 
                    value=0.0, 
                    step=0.1,
                    help="This value will be subtracted from all drift times"
                )
                
                if inject_time > 0:
                    st.markdown(f"""
                    <div class="status-card info-card">
                        <strong>ℹ️ Injection Time Set:</strong> {inject_time} ms will be subtracted from drift times
                    </div>
                    """, unsafe_allow_html=True)

            # Step 3: Upload calibration files
            st.markdown("""
            <div class="section-card">
                <div class="section-header">📊 Step 3: Upload Calibration Data</div>
            </div>
            """, unsafe_allow_html=True)
            
            cal_csvs = st.file_uploader(
                "Upload the CSV files from the 'Process Output Files' page", 
                type="csv", 
                accept_multiple_files=True,
                help="Select all CSV files generated in the previous step"
            )

            # Check if both drift zip and calibration CSVs are uploaded
            if cal_csvs:
                st.markdown(f"""
                <div class="status-card success-card">
                    <strong>✅ Calibration files loaded!</strong><br>
                    Found <span class="metric-badge">{len(cal_csvs)} files</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Processing section
                st.markdown("""
                <div class="section-card">
                    <div class="section-header">🔄 Processing Data</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Load the calibration data into a dictionary
                calibration_lookup = {}
                total_cal_points = 0
                
                for file in cal_csvs:
                    protein_name = file.name.replace(".csv", "")
                    df = pd.read_csv(file)
                    
                    for _, row in df.iterrows():
                        key = (protein_name, int(row["Z"]))
                        if key not in calibration_lookup:
                            calibration_lookup[key] = []
                        calibration_lookup[key].append({
                            "Drift": row["Drift"],
                            "CCS": row["CCS"],
                            "CCS Std.Dev.": row["CCS Std.Dev."]
                        })
                        total_cal_points += 1

                st.markdown(f"""
                <div class="protein-card">
                    <h4 style="color: #667eea; margin: 0 0 0.5rem 0;">📋 Calibration Summary</h4>
                    <p style="margin: 0; color: #64748b;">
                        <span class="metric-badge">{len(calibration_lookup)} protein-charge combinations</span>
                        <span class="metric-badge">{total_cal_points} calibration points</span>
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # Prepare to save the output dataframes
                output_buffers = {}
                processed_files = 0
                matched_points = 0

                # Process each drift file
                for root, _, files in os.walk(tmpdir):
                    for file in files:
                        if file.endswith(".txt") and file.split(".")[0].isdigit():
                            charge_state = int(file.split(".")[0])
                            protein_name = os.path.basename(root)
                            key = (protein_name, charge_state)
                            cal_data = calibration_lookup.get(key)

                            # Skip if no calibration data is found
                            if not cal_data:
                                continue

                            # Read the raw drift data
                            file_path = os.path.join(root, file)
                            try:
                                raw_df = pd.read_csv(file_path, sep="\t", header=None, names=["Drift", "Intensity"])
                                processed_files += 1
                            except Exception as e:
                                st.error(f"Failed to read file {file}: {e}")
                                continue

                            # Adjust drift time for Cyclic data
                            if data_type == "Cyclic" and inject_time is not None:
                                raw_df["Drift"] = raw_df["Drift"] - inject_time
                            
                            # Convert from ms to s for matching with calibration data
                            raw_df["Drift"] = raw_df["Drift"] / 1000.0

                            # Match calibration drift times to intensities
                            out_rows = []
                            for entry in cal_data:
                                drift_val = entry["Drift"]
                                # Find the row in raw_df with the closest drift time
                                closest_idx = (raw_df["Drift"] - drift_val).abs().idxmin()
                                matched_intensity = raw_df.loc[closest_idx, "Intensity"]

                                out_rows.append({
                                    "Charge": charge_state,
                                    "Drift": drift_val,
                                    "CCS": entry["CCS"],
                                    "CCS Std.Dev.": entry["CCS Std.Dev."],
                                    "Intensity": matched_intensity
                                })
                                matched_points += 1

                            # Create the dataframe for the matched data
                            out_df = pd.DataFrame(out_rows)

                            # Save each protein's data
                            out_key = f"{protein_name}.csv"
                            if out_key not in output_buffers:
                                output_buffers[out_key] = []
                            output_buffers[out_key].append(out_df)

                # Results section
                if output_buffers:
                    st.markdown(f"""
                    <div class="status-card success-card">
                        <strong>🎉 Processing Complete!</strong><br>
                        Processed <span class="metric-badge">{processed_files} files</span>
                        with <span class="metric-badge">{matched_points} matched data points</span>
                        for <span class="metric-badge">{len(output_buffers)} proteins</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Download section
                    st.markdown("""
                    <div class="section-card">
                        <div class="section-header">📥 Download Results</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show protein breakdown
                    for filename, dfs in output_buffers.items():
                        protein_name = filename.replace('.csv', '')
                        total_points = sum(len(df) for df in dfs)
                        
                        st.markdown(f"""
                        <div class="protein-card">
                            <h4 style="color: #667eea; margin: 0 0 0.5rem 0;">🧬 {protein_name}</h4>
                            <p style="margin: 0; color: #64748b;">
                                <span class="metric-badge">{total_points} calibrated points</span>
                                <span class="metric-badge">{len(dfs)} charge states</span>
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Create ZIP download
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zip_out:
                        for filename, dfs in output_buffers.items():
                            combined = pd.concat(dfs, ignore_index=True)
                            csv_bytes = combined.to_csv(index=False).encode("utf-8")
                            zip_out.writestr(filename, csv_bytes)

                    zip_buffer.seek(0)
                    st.download_button(
                        label="📦 Download Calibrated Drift Data (ZIP)",
                        data=zip_buffer,
                        file_name="calibrated_drift_data.zip",
                        mime="application/zip"
                    )
                    
                    # Next steps
                    st.markdown("""
                    <div class="info-card">
                        <h4 style="color: #667eea; margin-top: 0;">🎯 Next Steps</h4>
                        <p>Your calibrated drift data is ready! Each CSV file contains:</p>
                        <ul>
                            <li><strong>Charge:</strong> Charge state</li>
                            <li><strong>Drift:</strong> Drift time (seconds)</li>
                            <li><strong>CCS:</strong> Collision cross-section</li>
                            <li><strong>CCS Std.Dev.:</strong> Standard deviation</li>
                            <li><strong>Intensity:</strong> Matched intensity values</li>
                        </ul>
                        <p><strong>Ready to visualize?</strong> Go to 'Process and Plot Data' to create plots and analyze your results.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                else:
                    st.markdown("""
                    <div class="status-card warning-card">
                        <strong>⚠️ No Matching Data Found</strong><br>
                        No matching calibration or intensity data was found. Please check:
                        <ul style="margin: 0.5rem 0 0 1rem;">
                            <li>Protein names match between drift files and calibration CSVs</li>
                            <li>Charge state files (X.txt) exist in the drift data</li>
                            <li>File formats are correct</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Debug information
                    st.markdown("""
                    <div class="info-card">
                        <h4 style="color: #667eea; margin-top: 0;">🔍 Debugging Information</h4>
                        <p><strong>Expected file structure:</strong></p>
                        <pre style="background: #f1f5f9; padding: 1rem; border-radius: 6px; font-size: 0.9rem;">
drift_files.zip/
├── Protein1/
│   ├── 2.txt  (charge state 2)
│   ├── 3.txt  (charge state 3)
│   └── ...
├── Protein2/
│   └── ...
└── ...</pre>
                        <p><strong>Calibration files should be named:</strong> Protein1.csv, Protein2.csv, etc.</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="status-card info-card">
                    <strong>📋 Waiting for calibration files...</strong><br>
                    Please upload the CSV files from the 'Process Output Files' step to continue.
                </div>
                """, unsafe_allow_html=True)

calibrate_drift_files_page()
