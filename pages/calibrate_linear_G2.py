import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score
except ImportError:
    st.error("Please install scikit-learn: pip install scikit-learn")
    st.stop()
import io

# Set page config
st.set_page_config(page_title="DTIMS Data Calibration", layout="wide")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ff7f0e;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .parameter-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .results-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">DTIMS Data Calibration Tool</div>', unsafe_allow_html=True)

def parse_dtims_csv(file):
    """Parse the DTIMS CSV file and extract data"""
    try:
        # Read the file content
        content = file.read().decode('utf-8')
        lines = content.strip().split('\n')
        
        # Extract header information
        range_files = lines[0].split(',')[1:]  # Skip first empty cell
        raw_files = lines[1].split(',')[1:]   # Skip first empty cell
        
        # Read the data part (skip first 2 header lines)
        data_lines = lines[2:]
        
        # Parse data into DataFrame
        data_rows = []
        for line in data_lines:
            values = line.split(',')
            if len(values) >= 6:  # Ensure we have all columns
                data_rows.append([float(v) if v else 0 for v in values])
        
        # Create DataFrame
        columns = ['Time'] + [f'File_{i+1}' for i in range(len(raw_files))]
        df = pd.DataFrame(data_rows, columns=columns)
        
        return df, raw_files, range_files
    
    except Exception as e:
        st.error(f"Error parsing CSV file: {str(e)}")
        return None, None, None

def find_max_drift_time(df, column):
    """Find the drift time with maximum intensity for a given column"""
    if column in df.columns:
        max_idx = df[column].idxmax()
        return df.loc[max_idx, 'Time'], df.loc[max_idx, column]
    return None, None

def calculate_ccs(drift_time, t0, td, charge=1):
    """
    Calculate CCS using the provided equation
    CCS = (charge * td) / (drift_time - t0)
    """
    if drift_time <= t0:
        return np.nan
    return (charge * td) / (drift_time - t0)

# Initialize session state
if 'data_uploaded' not in st.session_state:
    st.session_state.data_uploaded = False
if 'parameters_set' not in st.session_state:
    st.session_state.parameters_set = False

# File upload section
st.markdown('<div class="section-header">📁 Data Upload</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload DTIMS CSV file", type=['csv'])

if uploaded_file is not None:
    df, raw_files, range_files = parse_dtims_csv(uploaded_file)
    
    if df is not None:
        st.session_state.data_uploaded = True
        st.session_state.df = df
        st.session_state.raw_files = raw_files
        st.session_state.range_files = range_files
        
        st.success(f"File uploaded successfully! Found {len(raw_files)} raw files.")
        
        # Display basic info about the data
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Number of Files", len(raw_files))
        with col2:
            st.metric("Number of Data Points", len(df))
        with col3:
            st.metric("Time Range", f"{df['Time'].min():.2f} - {df['Time'].max():.2f}")

# Parameter input section
if st.session_state.data_uploaded:
    st.markdown('<div class="section-header">⚙️ Experimental Parameters</div>', unsafe_allow_html=True)
    
    # Global parameters
    st.markdown("### Global Experimental Conditions")
    col1, col2 = st.columns(2)
    
    with col1:
        pressure = st.number_input("Pressure (mbar)", value=3.0, format="%.3f")
        temperature = st.number_input("Temperature (K)", value=298.0, format="%.1f")
        pusher_time = st.number_input("Pusher Time (µs)", value=100.0, format="%.1f")
    
    with col2:
        transfer_dc_entrance = st.number_input("Transfer DC Entrance (V)", value=0.0, format="%.1f")
        helium_exit_dc = st.number_input("Helium Exit DC (V)", value=0.0, format="%.1f")
    
    # File-specific parameters
    st.markdown("### File-Specific Parameters")
    st.markdown('<div class="parameter-box">', unsafe_allow_html=True)
    
    # Create input fields for each file
    file_params = {}
    
    for i, raw_file in enumerate(st.session_state.raw_files):
        st.markdown(f"**File {i+1}: {raw_file}**")
        col1, col2 = st.columns(2)
        
        with col1:
            helium_cell_dc = st.number_input(
                f"Helium Cell DC (V)", 
                key=f"helium_dc_{i}",
                value=0.0,
                format="%.1f"
            )
        
        with col2:
            bias = st.number_input(
                f"Bias (V)", 
                key=f"bias_{i}",
                value=0.0,
                format="%.1f"
            )
        
        file_params[f'File_{i+1}'] = {
            'helium_cell_dc': helium_cell_dc,
            'bias': bias,
            'raw_file': raw_file
        }
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Process data button
    if st.button("🔬 Process Data and Calculate Calibration", type="primary"):
        # Find maximum drift times and intensities
        results_data = []
        
        for file_col, params in file_params.items():
            max_drift, max_intensity = find_max_drift_time(st.session_state.df, file_col)
            
            if max_drift is not None:
                # Calculate true voltage
                true_voltage = (params['helium_cell_dc'] + params['bias'] - 
                              transfer_dc_entrance - helium_exit_dc)
                voltage_inverse = 1 / true_voltage if true_voltage != 0 else np.nan
                
                results_data.append({
                    'File': params['raw_file'],
                    'Column': file_col,
                    'Helium_Cell_DC': params['helium_cell_dc'],
                    'Bias': params['bias'],
                    'Max_Drift_Time': max_drift,
                    'Max_Intensity': max_intensity,
                    'True_Voltage': true_voltage,
                    'Voltage_Inverse': voltage_inverse
                })
        
        results_df = pd.DataFrame(results_data)
        
        # Filter out invalid data
        valid_data = results_df.dropna(subset=['Voltage_Inverse', 'Max_Drift_Time'])
        
        if len(valid_data) >= 2:
            # Perform linear regression
            X = valid_data['Voltage_Inverse'].values.reshape(-1, 1)
            y = valid_data['Max_Drift_Time'].values
            
            reg = LinearRegression()
            reg.fit(X, y)
            
            y_pred = reg.predict(X)
            r2 = r2_score(y, y_pred)
            
            gradient = reg.coef_[0]  # td
            intercept = reg.intercept_  # t0
            
            # Store calibration results
            st.session_state.calibration_results = {
                'gradient': gradient,
                'intercept': intercept,
                'r2': r2,
                'results_df': results_df,
                'valid_data': valid_data
            }
            
            # Display results
            st.markdown('<div class="section-header">📊 Calibration Results</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Gradient (td)", f"{gradient:.6f}")
            with col2:
                st.metric("Intercept (t0)", f"{intercept:.6f}")
            with col3:
                st.metric("R² Value", f"{r2:.6f}")
            
            # Create calibration plot
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot data points
            ax.scatter(valid_data['Voltage_Inverse'], valid_data['Max_Drift_Time'], 
                      color='blue', s=100, alpha=0.7, label='Data Points')
            
            # Plot regression line
            x_line = np.linspace(valid_data['Voltage_Inverse'].min(), 
                               valid_data['Voltage_Inverse'].max(), 100)
            y_line = gradient * x_line + intercept
            ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Fit: y = {gradient:.6f}x + {intercept:.6f}')
            
            ax.set_xlabel('1/Voltage (V⁻¹)')
            ax.set_ylabel('Drift Time (ms)')
            ax.set_title(f'DTIMS Calibration Plot (R² = {r2:.6f})')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            st.pyplot(fig)
            
            # Display detailed results table
            st.markdown("### Detailed Results")
            st.dataframe(results_df, use_container_width=True)
            
            # Calculate CCS values
            st.markdown('<div class="section-header">🧮 CCS Calculations</div>', unsafe_allow_html=True)
            
            # CCS calculation parameters
            col1, col2 = st.columns(2)
            with col1:
                charge_state = st.number_input("Charge State", value=1, min_value=1)
            with col2:
                ccs_std_dev = st.number_input("CCS Standard Deviation", value=0.1, format="%.3f")
            
            # Calculate CCS for each drift time
            ccs_data = []
            for _, row in results_df.iterrows():
                if not pd.isna(row['Max_Drift_Time']):
                    ccs_value = calculate_ccs(row['Max_Drift_Time'], intercept, gradient, charge_state)
                    ccs_data.append({
                        'Charge': charge_state,
                        'Drift': row['Max_Drift_Time'],
                        'CCS': ccs_value,
                        'CCS_Std_Dev': ccs_std_dev,
                        'Intensity': row['Max_Intensity']
                    })
            
            ccs_df = pd.DataFrame(ccs_data)
            
            if not ccs_df.empty:
                st.markdown("### Calculated CCS Values")
                st.dataframe(ccs_df, use_container_width=True)
                
                # Create download button for CCS data
                csv_buffer = io.StringIO()
                ccs_df.to_csv(csv_buffer, index=False)
                csv_string = csv_buffer.getvalue()
                
                st.download_button(
                    label="📥 Download Calibrated Data (CSV)",
                    data=csv_string,
                    file_name="dtims_calibrated_data.csv",
                    mime="text/csv"
                )
                
                # Summary statistics
                st.markdown("### Summary Statistics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Average CCS", f"{ccs_df['CCS'].mean():.2f}")
                with col2:
                    st.metric("CCS Range", f"{ccs_df['CCS'].max() - ccs_df['CCS'].min():.2f}")
                with col3:
                    st.metric("Total Data Points", len(ccs_df))
        
        else:
            st.error("Not enough valid data points for calibration. Need at least 2 data points.")

# Information section
st.markdown('<div class="section-header">ℹ️ Information</div>', unsafe_allow_html=True)

with st.expander("How to use this tool"):
    st.markdown("""
    1. **Upload your DTIMS CSV file** - The file should contain time series data with multiple columns for different experimental conditions
    2. **Set global parameters** - Enter the experimental conditions (pressure, temperature, pusher time, etc.)
    3. **Set file-specific parameters** - For each raw file, enter the Helium Cell DC and Bias values
    4. **Process the data** - The tool will:
       - Find the drift time with maximum intensity for each file
       - Calculate the true voltage: (Helium Cell DC + Bias) - (Transfer DC Entrance + Helium Exit DC)
       - Plot drift time vs. 1/voltage and fit a linear regression
       - Calculate CCS values using the equation: CCS = (charge × td) / (drift_time - t0)
       - Generate a downloadable CSV with calibrated data
    """)

with st.expander("About the calculations"):
    st.markdown("""
    **True Voltage Calculation:**
    ```
    True Voltage = (Helium Cell DC + Bias) - (Transfer DC Entrance + Helium Exit DC)
    ```
    
    **CCS Calculation:**
    ```
    CCS = (charge × td) / (drift_time - t0)
    ```
    
    Where:
    - `td` = gradient from the linear fit of drift time vs. 1/voltage
    - `t0` = intercept from the linear fit
    - `charge` = charge state of the ion (typically 1)
    - `drift_time` = measured drift time at maximum intensity
    """)
