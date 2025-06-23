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

def calculate_ccs_mason_schamp(drift_time, voltage, temperature, pressure, mass_analyte, charge=1, length=25.05):
    """
    Calculate CCS using the Mason-Schamp equation
    
    Parameters:
    - drift_time: drift time in ms
    - voltage: voltage in V
    - temperature: temperature in K
    - pressure: pressure in mbar
    - mass_analyte: mass of analyte in Da
    - charge: charge state
    - length: drift tube length in cm (default 25.05 cm for Synapt)
    
    Returns:
    - CCS in Å²
    """
    # Constants
    k_B = 1.380649e-23  # Boltzmann constant (J/K)
    e = 1.602176634e-19  # Elementary charge (C)
    N_A = 6.02214076e23  # Avogadro's number
    mass_He = 4.002602  # Mass of Helium in Da
    
    # Convert units
    drift_time_s = drift_time * 1e-3  # ms to s
    length_m = length * 1e-2  # cm to m
    pressure_Pa = pressure * 100  # mbar to Pa
    
    # Calculate reduced mass (in kg)
    mass_analyte_kg = mass_analyte * 1.66054e-27  # Da to kg
    mass_He_kg = mass_He * 1.66054e-27  # Da to kg
    reduced_mass = (mass_analyte_kg * mass_He_kg) / (mass_analyte_kg + mass_He_kg)
    
    # Calculate mobility
    mobility = length_m / (voltage * drift_time_s)  # m²/(V·s)
    
    # Calculate number density of buffer gas
    n_gas = pressure_Pa / (k_B * temperature)  # molecules/m³
    
    # Mason-Schamp equation
    # CCS = (3 * e * charge) / (16 * N_0) * sqrt(2π / (μ * k_B * T)) * (1 / K_0)
    # Where K_0 is the mobility
    
    ccs_m2 = (3 * e * charge) / (16 * n_gas) * np.sqrt(2 * np.pi / (reduced_mass * k_B * temperature)) * (1 / mobility)
    
    # Convert to Å²
    ccs_angstrom2 = ccs_m2 * 1e20
    
    return ccs_angstrom2

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
    
    # Analyte mass input - separate and prominent
    st.markdown("### Analyte Information")
    st.markdown('<div class="parameter-box">', unsafe_allow_html=True)
    mass_analyte = st.number_input(
        "**Analyte Mass (Da)**", 
        value=0.0, 
        min_value=0.0,
        format="%.4f", 
        help="Enter the mass of your analyte in Daltons (Da). This is required for CCS calculations using the Mason-Schamp equation."
    )
    
    if mass_analyte <= 0:
        st.warning("⚠️ Please enter a valid analyte mass (> 0 Da) to proceed with CCS calculations.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Process data button - only enable if mass is entered
    process_disabled = mass_analyte <= 0
    
    if process_disabled:
        st.info("👆 Please enter the analyte mass above to enable data processing.")
    
    if st.button("🔬 Process Data and Calculate Calibration", type="primary", disabled=process_disabled):
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
            
            # Calculate CCS values for ALL drift times and voltages
            st.markdown('<div class="section-header">🧮 CCS Calculations (All Data Points)</div>', unsafe_allow_html=True)
            
            # CCS calculation parameters
            col1, col2 = st.columns(2)
            with col1:
                charge_state = st.number_input("Charge State", value=1, min_value=1)
            with col2:
                st.info(f"Using Mason-Schamp equation with drift tube length: 25.05 cm")
            
            # Calculate CCS for ALL drift times across all files and voltages
            all_ccs_data = []
            
            for file_col, params in file_params.items():
                # Get all non-zero drift times and intensities for this file
                file_data = st.session_state.df[st.session_state.df[file_col] > 0].copy()
                
                if not file_data.empty:
                    true_voltage = (params['helium_cell_dc'] + params['bias'] - 
                                  transfer_dc_entrance - helium_exit_dc)
                    
                    for _, row in file_data.iterrows():
                        drift_time = row['Time']
                        intensity = row[file_col]
                        
                        # Calculate CCS using Mason-Schamp equation
                        ccs_value = calculate_ccs_mason_schamp(
                            drift_time=drift_time,
                            voltage=abs(true_voltage),  # Use absolute value
                            temperature=temperature,
                            pressure=pressure,
                            mass_analyte=mass_analyte,
                            charge=charge_state
                        )
                        
                        all_ccs_data.append({
                            'Charge': charge_state,
                            'Drift': drift_time,
                            'CCS': ccs_value,
                            'True_Voltage': true_voltage,
                            'Intensity': intensity,
                            'File': params['raw_file']
                        })
            
            # Create comprehensive CCS DataFrame
            comprehensive_ccs_df = pd.DataFrame(all_ccs_data)
            
            if not comprehensive_ccs_df.empty:
                # Remove any invalid CCS values (NaN or infinite)
                comprehensive_ccs_df = comprehensive_ccs_df.dropna(subset=['CCS'])
                comprehensive_ccs_df = comprehensive_ccs_df[np.isfinite(comprehensive_ccs_df['CCS'])]
                
                st.markdown("### Complete CCS Dataset")
                st.dataframe(comprehensive_ccs_df, use_container_width=True)
                
                # Create output DataFrame with the specified columns
                output_df = comprehensive_ccs_df[['Charge', 'Drift', 'CCS', 'True_Voltage', 'Intensity']].copy()
                
                # Create download button for comprehensive CCS data
                csv_buffer = io.StringIO()
                output_df.to_csv(csv_buffer, index=False)
                csv_string = csv_buffer.getvalue()
                
                st.download_button(
                    label="📥 Download Complete Calibrated Data (CSV)",
                    data=csv_string,
                    file_name="dtims_complete_calibrated_data.csv",
                    mime="text/csv"
                )
                
                # Summary statistics
                st.markdown("### Summary Statistics")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Data Points", len(output_df))
                with col2:
                    st.metric("Average CCS (Å²)", f"{output_df['CCS'].mean():.2f}")
                with col3:
                    st.metric("CCS Range (Å²)", f"{output_df['CCS'].max() - output_df['CCS'].min():.2f}")
                with col4:
                    st.metric("Voltage Range (V)", f"{abs(output_df['True_Voltage'].max() - output_df['True_Voltage'].min()):.1f}")
                
                # Create CCS distribution plot
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
                
                # CCS histogram
                ax1.hist(output_df['CCS'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
                ax1.set_xlabel('CCS (Å²)')
                ax1.set_ylabel('Frequency')
                ax1.set_title('CCS Distribution')
                ax1.grid(True, alpha=0.3)
                
                # CCS vs Drift Time scatter plot
                scatter = ax2.scatter(output_df['Drift'], output_df['CCS'], 
                                    c=output_df['True_Voltage'], cmap='viridis', 
                                    alpha=0.6, s=20)
                ax2.set_xlabel('Drift Time (ms)')
                ax2.set_ylabel('CCS (Å²)')
                ax2.set_title('CCS vs Drift Time (colored by Voltage)')
                ax2.grid(True, alpha=0.3)
                
                # Add colorbar
                cbar = plt.colorbar(scatter, ax=ax2)
                cbar.set_label('True Voltage (V)')
                
                plt.tight_layout()
                st.pyplot(fig)
                
                # Show file-wise summary
                st.markdown("### File-wise Summary")
                file_summary = comprehensive_ccs_df.groupby('File').agg({
                    'CCS': ['count', 'mean', 'std', 'min', 'max'],
                    'True_Voltage': 'first',
                    'Intensity': 'sum'
                }).round(2)
                
                # Flatten column names
                file_summary.columns = ['Data_Points', 'Mean_CCS', 'Std_CCS', 'Min_CCS', 'Max_CCS', 'True_Voltage', 'Total_Intensity']
                st.dataframe(file_summary, use_container_width=True)
        
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
       - Find the drift time with maximum intensity for each file (for calibration plot)
       - Calculate the true voltage: (Helium Cell DC + Bias) - (Transfer DC Entrance + Helium Exit DC)
       - Plot drift time vs. 1/voltage and fit a linear regression for calibration verification
       - Calculate CCS for ALL drift times using the Mason-Schamp equation
       - Generate a downloadable CSV with complete calibrated data (Charge, Drift, CCS, True_Voltage, Intensity)
    """)

with st.expander("About the calculations"):
    st.markdown("""
    **True Voltage Calculation:**
    ```
    True Voltage = (Helium Cell DC + Bias) - (Transfer DC Entrance + Helium Exit DC)
    ```
    
    **Mason-Schamp CCS Calculation:**
    ```
    CCS = (3 × e × z) / (16 × N₀) × √(2π / (μ × k_B × T)) × (1 / K₀)
    ```
    
    Where:
    - `e` = elementary charge (1.602 × 10⁻¹⁹ C)
    - `z` = charge state
    - `N₀` = number density of buffer gas
    - `μ` = reduced mass of analyte-buffer gas system
    - `k_B` = Boltzmann constant (1.381 × 10⁻²³ J/K)
    - `T` = temperature (K)
    - `K₀` = mobility = L/(V×t_d)
    - `L` = drift tube length (25.05 cm for Synapt)
    
    **Reduced Mass Calculation:**
    ```
    μ = (m_analyte × m_He) / (m_analyte + m_He)
    ```
    
    Where m_He = 4.002602 Da
    """)
