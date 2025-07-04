import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import io
import zipfile
import streamlit as st

# === PAGE CONFIGURATION ===
st.set_page_config(
    page_title="Calibrate",
    page_icon="📏",
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

st.markdown('<div class="main-header"><h1>Process Calibrant Data</h1><p>Fit ATDs of calibrants and generate reference files for IMSCal</p></div>', unsafe_allow_html=True)

st.markdown("""
<div class="info-card">
    <p>Use this page to fit the ATDs of your calibrants and generate a reference file for IMSCal and/or a csv file of calibrant measured and literature arrival times. This is designed for use with denatured calibrants, so the fitting only allows for a single peak for each ATD - consider another tool if your ATDs are not gaussian-y.</p>
    <p>To start, make a folder for each calibrant you used. You should name these folders according to the table below (or they won't match the bush database file). Within each folder, make a text file for each charge state (called e.g. '1.txt', '2.txt' etc.) and paste the corresponding ATD from MassLynx into each file. Remember to have the x-axis set to ms not bins! Zip these folders together and upload it below.</p>
</div>
""", unsafe_allow_html=True)

# Corrected structure for table display
data = {
    'Protein': [
        'Denatured Myoglobin',
        'Denatured Cytochrome C',
        'Polyalanine Peptide of Length X',
        'Denatured Ubiquitin'
    ],
    'Folder Name': [
        'myoglobin',
        'cytochrome c',
        'polyalanineX',
        'ubiquitin'
    ]
}

df = pd.DataFrame(data)

st.markdown('<h3 class="section-header">Calibrant Folder Naming Convention</h3>', unsafe_allow_html=True)
st.table(df)
st.markdown('</div>', unsafe_allow_html=True)

# Function to handle ZIP file upload and extract folder names
def handle_zip_upload(uploaded_file):
    temp_dir = '/tmp/extracted_zip/'
    os.makedirs(temp_dir, exist_ok=True)

    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    folders = [f for f in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, f))]
    if not folders:
        st.error("No folders found in the ZIP file.")
    return folders, temp_dir

with st.expander("Help it isn't working :("):
    st.write("The script is only looking inside the first layer of the zipped folder for protein names - if you saved the protein folders inside another folder before zipping then the script can't see them.")
    st.write("Check if the sample data (on Ana's github) works - if it doesn't, then Ana has broken the website.")

# Read the bush.csv file from the same folder as calibrant.py
def read_bush_csv():
    calibrant_file_path = os.path.join(os.path.dirname(__file__), '../data/bush.csv')
    if os.path.exists(calibrant_file_path):
        bush_df = pd.read_csv(calibrant_file_path)
    else:
        st.error(f"'{calibrant_file_path}' not found. Make sure 'bush.csv' is in the same directory as the script.")
        bush_df = pd.DataFrame()  # Empty DataFrame if the file isn't found
    return bush_df

# Gaussian fit function
def gaussian(x, amp, mean, stddev):
    return amp * np.exp(-((x - mean) ** 2) / (2 * stddev ** 2))

# R² Calculation
def r_squared(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - (ss_res / ss_tot)

# Fit Gaussian and retry with different initial guesses
def fit_gaussian_with_retries(drift_time, intensity, n_attempts=10):
    best_r2 = -np.inf
    best_params = None
    best_fitted_values = None

    for _ in range(n_attempts):
        initial_guess = [
            np.random.uniform(0.8 * max(intensity), 1.2 * max(intensity)),
            np.random.uniform(np.min(drift_time), np.max(drift_time)),
            np.random.uniform(0.1 * np.std(drift_time), 2 * np.std(drift_time))
        ]

        try:
            params, _ = curve_fit(gaussian, drift_time, intensity, p0=initial_guess)
            fitted_values = gaussian(drift_time, *params)
            r2 = r_squared(intensity, fitted_values)

            if r2 > best_r2:
                best_r2 = r2
                best_params = params
                best_fitted_values = fitted_values
        except RuntimeError:
            continue

    return best_params, best_r2, best_fitted_values

# Function to process each folder and extract data from .txt files
def process_folder_data(folder_name, base_path, bush_df, calibrant_type):
    folder_path = os.path.join(base_path, folder_name)
    results = []
    plots = []
    skipped_entries = []

    # Determine the column for the selected calibrant type
    calibrant_column = 'CCS_he' if calibrant_type == 'Helium' else 'CCS_n2'

    # Iterate through each file in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt') and filename[0].isdigit():  # Only process .txt files
            file_path = os.path.join(folder_path, filename)

            data = np.loadtxt(file_path)
            drift_time = data[:, 0]
            intensity = data[:, 1]

            # Perform Gaussian fit
            params, r2, fitted_values = fit_gaussian_with_retries(drift_time, intensity)
            if params is not None:
                amp, apex, stddev = params
                charge_state = filename.split('.')[0]
                
                # Look up the calibrant data from bush.csv based on protein and charge state
                calibrant_row = bush_df[(bush_df['protein'] == folder_name) & (bush_df['charge'] == int(charge_state))]
                
                if not calibrant_row.empty:
                    calibrant_value = calibrant_row[calibrant_column].values[0]
                    mass = calibrant_row['mass'].values[0]
                    
                    # Only add to results if calibrant_value is not None/NaN
                    if pd.notna(calibrant_value) and calibrant_value is not None:
                        results.append([folder_name, mass, charge_state, apex, r2, calibrant_value])
                        plots.append((drift_time, intensity, fitted_values, filename, apex, r2))
                    else:
                        skipped_entries.append(f"{folder_name} charge {charge_state} - no {calibrant_type.lower()} CCS value available")
                else:
                    skipped_entries.append(f"{folder_name} charge {charge_state} - not found in database")
            else:
                skipped_entries.append(f"{folder_name} charge {filename.split('.')[0]} - Gaussian fit failed")

    # Convert results to DataFrame
    results_df = pd.DataFrame(results, columns=['protein', 'mass', 'charge state', 'drift time', 'r2', 'calibrant_value'])

    return results_df, plots, skipped_entries

# Function to display the data and plots
def display_results(results_df, plots, skipped_entries):
    if not results_df.empty:
        st.markdown('<h3 class="section-header">Gaussian Fit Results</h3>', unsafe_allow_html=True)
        st.dataframe(results_df)
        st.markdown('</div>', unsafe_allow_html=True)

        # Plot all the fits
        n_plots = len(plots)
        if n_plots > 0:
            n_cols = 3
            n_rows = (n_plots + n_cols - 1) // n_cols

            plt.figure(figsize=(12, 4 * n_rows))
            for i, (drift_time, intensity, fitted_values, filename, apex, r2) in enumerate(plots):
                plt.subplot(n_rows, n_cols, i + 1)
                plt.plot(drift_time, intensity, 'b.', label='Raw Data', markersize=3)
                plt.plot(drift_time, fitted_values, 'r-', label='Gaussian Fit', linewidth=1)
                plt.title(f'{filename}\nApex: {apex:.2f}, R²: {r2:.3f}')
                plt.xlabel('Drift Time')
                plt.ylabel('Intensity')
                plt.legend()
                plt.grid()

            plt.tight_layout()
            st.pyplot(plt)
    else:
        st.markdown('<div class="warning-card">No valid calibrant data found that matches the database.</div>', unsafe_allow_html=True)

    # Show skipped entries if any
    if skipped_entries:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header">⚠️ Skipped Entries</h3>', unsafe_allow_html=True)
        st.markdown('<div class="warning-card">', unsafe_allow_html=True)
        st.write("The following entries were skipped:")
        for entry in skipped_entries:
            st.write(f"• {entry}")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Function to create .dat file from results
def generate_dat_file(results_df, velocity, voltage, pressure, length):
    if results_df.empty:
        return None
        
    dat_content = f"# length {length}\n# velocity {velocity}\n# voltage {voltage}\n# pressure {pressure}\n"

    # Create .dat content
    for _, row in results_df.iterrows():
        protein = row['protein']
        charge_state = row['charge state']
        mass = row['mass']
        calibrant_value = row['calibrant_value'] * 100  # Convert to Ų
        drift_time = row['drift time']
        dat_content += f"{protein}_{charge_state} {mass} {charge_state} {calibrant_value} {drift_time}\n"
    
    return dat_content

def calibrate_page():
    # Step 1: Upload ZIP file
    st.markdown('<h3 class="section-header">📁 Upload Calibrant Data</h3>', unsafe_allow_html=True)
    uploaded_zip_file = st.file_uploader("Upload a ZIP file containing your calibrant folders", type="zip")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_zip_file is not None:
        # Extract the folders from the ZIP file
        folders, temp_dir = handle_zip_upload(uploaded_zip_file)

        # Step 2: Read bush.csv for calibrant data
        bush_df = read_bush_csv()

        if bush_df.empty:
            st.markdown('<div class="error-card">Cannot proceed without the Bush calibrant database.</div>', unsafe_allow_html=True)
            return

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header">⚗️ Calibration Parameters</h3>', unsafe_allow_html=True)
        st.markdown('Most of the time you should calibrate with calibrant values obtained for the same drift gas as you used in your experiment, but sometimes you might not so the option is here.')
        
        # Step 3: Dropdown for selecting calibrant type (He or N2)
        calibrant_type = st.selectbox("Which values from the Bush database would you like to calibrate with?", options=["Helium", "Nitrogen"])

        col1, col2 = st.columns(2)
        with col1:
            # Step 4: Get user inputs for parameters
            velocity = st.number_input("Enter wave velocity (m/s), multiplied by 0.75 if this is Cyclic data", min_value=0.0, value=281.0)
            voltage = st.number_input("Enter wave height (V)", min_value=0.0, value=20.0)
        with col2:
            pressure = st.number_input("Enter IMS pressure", min_value=0.0, value=1.63)
            length = st.number_input("Enter drift cell length (0.25m for Synapt, 0.98m for Cyclic)", min_value=0.0, value=0.980)

        # Step 4.5: Ask for data type
        data_type = st.radio("Is this Cyclic or Synapt data?", options=["Cyclic", "Synapt"])
        inject_time = 0.0
        if data_type.lower() == "cyclic":
            inject_time = st.number_input("Enter inject time (ms)", min_value=0.0, value=0.0)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Step 5: Process all folders and files
        all_results_df = pd.DataFrame(columns=['protein', 'mass', 'charge state', 'drift time', 'r2', 'calibrant_value'])
        all_plots = []
        all_skipped = []

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header">🔬 Processing Results</h3>', unsafe_allow_html=True)
        
        for folder in folders:
            st.write(f"Processing folder: **{folder}**")
            results_df, plots, skipped_entries = process_folder_data(folder, temp_dir, bush_df, calibrant_type)
            all_results_df = pd.concat([all_results_df, results_df], ignore_index=True)
            all_plots.extend(plots)
            all_skipped.extend(skipped_entries)

        st.markdown('</div>', unsafe_allow_html=True)

        # Step 6: Display results
        display_results(all_results_df, all_plots, all_skipped)

        # Only show download options if we have valid results
        if not all_results_df.empty:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-header">📥 Download Results</h3>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Step 7: CSV download
                csv_buffer = io.StringIO()
                all_results_df.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="📊 Download Results (CSV)",
                    data=csv_buffer.getvalue(),
                    file_name="combined_gaussian_fit_results.csv",
                    mime="text/csv"
                )

            with col2:
                # Step 8: Prepare adjusted drift times for .dat file if cyclic
                if data_type.lower() == "cyclic":
                    adjusted_df = all_results_df.copy()
                    adjusted_df['drift time'] = adjusted_df['drift time'] - inject_time
                else:
                    adjusted_df = all_results_df

                # Step 9: .dat file download
                dat_file_content = generate_dat_file(adjusted_df, velocity, voltage, pressure, length)
                if dat_file_content:
                    st.download_button(
                        label="📋 Download .dat File",
                        data=dat_file_content,
                        file_name="calibration_data.dat",
                        mime="text/plain"
                    )
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-card">No valid results to download. Please check your data and database matching.</div>', unsafe_allow_html=True)

calibrate_page()
