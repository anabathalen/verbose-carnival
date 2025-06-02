import streamlit as st
import zipfile
import tempfile
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from scipy.interpolate import griddata
from scipy.signal import savgol_filter
import matplotlib.colors as mcolors

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
    
    /* Hide default elements */
    header[data-testid="stHeader"] {display: none;}
    .stDeployButton {display: none;}
    .css-1lsmgbg.e1fqkh3o3 {display: none;}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>Plot aIMS/CIU Plot from TWIMExtract Data</h1>
    <p>Enhanced version with normalization, smoothing, and advanced colorbar customization</p>
</div>
""", unsafe_allow_html=True)

# File Upload Section
with st.container():
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-header">📁 File Upload</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        twim_extract_file = st.file_uploader("Upload the TWIM Extract CSV file", type="csv")
    with col2:
        calibration_file = st.file_uploader("Upload the calibration CSV file", type="csv")
    
    st.markdown('</div>', unsafe_allow_html=True)

if twim_extract_file and calibration_file:
    # Data Processing Section
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">⚙️ Data Configuration</h2>', unsafe_allow_html=True)
        
        # Read the first row to check for metadata
        first_row = twim_extract_file.readline().decode("utf-8")
        
        # Reset file pointer so pandas reads from the start again
        twim_extract_file.seek(0)
        
        # Conditional loading depending on metadata
        if first_row.startswith("#"):
            twim_df = pd.read_csv(twim_extract_file, header=2)
        else:
            twim_df = pd.read_csv(twim_extract_file)
        
        # Convert 'Drift Time' column to numeric, coercing errors
        twim_df.iloc[:, 0] = pd.to_numeric(twim_df.iloc[:, 0], errors='coerce')
        twim_df = twim_df.dropna(subset=[twim_df.columns[0]])  # Remove rows with NaN drift times
        
        # Rename columns: first one is 'Drift Time', the rest are assumed to be CV steps
        twim_df.columns = ['Drift Time'] + list(twim_df.columns[1:])

        with st.expander("View TWIM Extract Data Preview"):
            st.dataframe(twim_df.head())

        # Read calibration data
        cal_df = pd.read_csv(calibration_file)
        
        with st.expander("View Calibration Data Preview"):
            st.dataframe(cal_df.head())

        if 'Z' not in cal_df.columns:
            st.markdown('<div class="status-card error-card">❌ Calibration data must include a "Z" column for charge state.</div>', unsafe_allow_html=True)
            st.stop()

        col1, col2, col3 = st.columns(3)
        with col1:
            data_type = st.radio("Instrument Type", ["Synapt", "Cyclic"])
        with col2:
            charge_state = st.number_input("Charge State (Z)", min_value=1, max_value=100, step=1, value=1)
        with col3:
            inject_time = None
            if data_type == "Cyclic":
                inject_time = st.number_input("Injection Time (ms)", min_value=0.0, value=0.0, step=0.1)

        st.markdown('</div>', unsafe_allow_html=True)

    # Processing Section
    if st.button("🔄 Process Data", help="Click to calibrate and process your data"):
        with st.spinner("Processing data..."):
            if inject_time is not None and data_type == "Cyclic":
                twim_df["Drift Time"] = twim_df["Drift Time"] - inject_time

            cal_data = cal_df[cal_df["Z"] == charge_state]
            if cal_data.empty:
                st.markdown('<div class="status-card error-card">❌ No calibration data found for the specified charge state.</div>', unsafe_allow_html=True)
                st.stop()

            if "Drift" not in cal_data.columns or "CCS" not in cal_data.columns:
                st.markdown('<div class="status-card error-card">❌ Calibration data must include "Drift" and "CCS" columns.</div>', unsafe_allow_html=True)
                st.stop()

            cal_data["CCS Std.Dev."] = cal_data["CCS Std.Dev."].fillna(0)
            cal_data = cal_data[cal_data["CCS Std.Dev."] <= 0.1 * cal_data["CCS"]]
            cal_data["Drift (ms)"] = cal_data["Drift"] * 1000

            calibrated_data = []

            drift_times = twim_df["Drift Time"]
            collision_voltages = twim_df.columns[1:]

            for idx, drift_time in enumerate(drift_times):
                intensities = twim_df.iloc[idx, 1:].values
                if pd.isna(drift_time):
                    continue
                drift_time_rounded = round(drift_time, 4)
                closest_idx = (cal_data["Drift (ms)"] - drift_time_rounded).abs().idxmin()
                ccs_value = cal_data.loc[closest_idx, "CCS"]

                for col_idx, intensity in enumerate(intensities):
                    cv = collision_voltages[col_idx]
                    calibrated_data.append([ccs_value, drift_time, float(cv), intensity])

            # Convert calibrated data to NumPy array
            calibrated_array = np.array(calibrated_data)

            # Store the result in session state
            st.session_state["calibrated_array"] = calibrated_array
            
            st.markdown('<div class="status-card success-card">✅ Data processed successfully!</div>', unsafe_allow_html=True)

# If processed data exists, allow customization and visualization
if "calibrated_array" in st.session_state:
    calibrated_array = st.session_state["calibrated_array"]

    # Data Processing Options
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">🔧 Data Processing Options</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Normalization")
            normalize_data = st.checkbox("Normalize each collision voltage slice to maximum intensity of 1", 
                                       help="This will normalize each CV slice independently to its maximum value")
        
        with col2:
            st.subheader("Savitzky-Golay Smoothing")
            apply_smoothing = st.checkbox("Apply Savitzky-Golay smoothing", 
                                        help="Smooth the data to reduce noise")
            
            if apply_smoothing:
                window_length = st.slider("Window Length", 3, 51, 11, 2, 
                                        help="Must be odd number. Larger values = more smoothing")
                poly_order = st.slider("Polynomial Order", 1, min(6, window_length-1), 3, 
                                     help="Order of polynomial used for smoothing")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Visualization Customization
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">📊 CIU Heatmap Customization</h2>', unsafe_allow_html=True)

        # Basic plot settings
        st.subheader("🎨 Basic Plot Settings")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            color_map = st.selectbox("Color Map", [
                "viridis", "plasma", "inferno", "cividis", "coolwarm", "magma", 
                "Blues", "Greens", "Purples", "Oranges", "Reds", "Greens_r", 
                "Purples_r", "Blues_r", "Oranges_r", "Reds_r", "Spectral", "jet"
            ])
        
        with col2:
            font_size = st.slider("Font Size", 8, 24, 12, 1)
        
        with col3:
            figure_size = st.slider("Figure Size (inches)", 4, 16, 10, 1)
        
        with col4:
            dpi = st.slider("Resolution (DPI)", 100, 1000, 300, 50)

        # Advanced colorbar settings
        st.subheader("🌈 Advanced Colorbar Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            use_custom_colorbar = st.checkbox("Use custom colorbar settings", 
                                            help="Enable advanced colorbar customization")
            
            if use_custom_colorbar:
                vmin_percent = st.slider("Minimum intensity threshold (%)", 0, 50, 5, 1,
                                       help="Values below this % of max will be set to minimum color")
                vmax_percent = st.slider("Maximum intensity threshold (%)", 50, 100, 95, 1,
                                       help="Values above this % of max will be set to maximum color")
        
        with col2:
            show_colorbar = st.checkbox("Show colorbar", value=True)
            if show_colorbar:
                colorbar_shrink = st.slider("Colorbar size", 0.3, 1.0, 0.8, 0.05)
                colorbar_aspect = st.slider("Colorbar aspect ratio", 10, 50, 20, 5)

        # Axis range settings
        st.subheader("📏 Axis Range Settings")
        
        x_min_default, x_max_default = float(calibrated_array[:, 2].min()), float(calibrated_array[:, 2].max())
        y_min_default, y_max_default = float(calibrated_array[:, 0].min()), float(calibrated_array[:, 0].max())
        
        col1, col2 = st.columns(2)
        
        with col1:
            x_min, x_max = st.slider("Collision Voltage Range",
                x_min_default, x_max_default, (x_min_default, x_max_default),
                help="Crop the x-axis range")
        
        with col2:
            y_min, y_max = st.slider("CCS Range",
                y_min_default, y_max_default, (y_min_default, y_max_default),
                help="Crop the y-axis range")

        # Annotation settings
        st.subheader("📝 Annotations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            num_x_lines = st.slider("Number of vertical reference lines", 0, 5, 0)
            x_values, x_labels = [], []
            for i in range(num_x_lines):
                subcol1, subcol2 = st.columns(2)
                with subcol1:
                    value = st.number_input(f"X-value {i+1}", min_value=x_min, max_value=x_max, 
                                          value=(x_min + x_max)/2, key=f"x_val_{i}")
                with subcol2:
                    label = st.text_input(f"X-label {i+1}", value=f"Line {i+1}", key=f"x_label_{i}")
                x_values.append(value)
                x_labels.append(label)
        
        with col2:
            num_y_lines = st.slider("Number of horizontal reference lines", 0, 5, 0)
            y_values, y_labels = [], []
            for i in range(num_y_lines):
                subcol1, subcol2 = st.columns(2)
                with subcol1:
                    value = st.number_input(f"Y-value {i+1}", min_value=y_min, max_value=y_max, 
                                          value=(y_min + y_max)/2, key=f"y_val_{i}")
                with subcol2:
                    label = st.text_input(f"Y-label {i+1}", value=f"Line {i+1}", key=f"y_label_{i}")
                y_values.append(value)
                y_labels.append(label)

        st.markdown('</div>', unsafe_allow_html=True)

    # Generate Plot Button
    if st.button("🎨 Generate CIU Heatmap"):
        with st.spinner("Generating heatmap..."):
            # Filter data to the specified ranges
            mask = ((calibrated_array[:, 2] >= x_min) & (calibrated_array[:, 2] <= x_max) & 
                   (calibrated_array[:, 0] >= y_min) & (calibrated_array[:, 0] <= y_max))
            filtered_data = calibrated_array[mask]
            
            # Apply normalization if requested
            if normalize_data:
                df_temp = pd.DataFrame(filtered_data, columns=["CCS", "Drift Time", "Collision Voltage", "Intensity"])
                normalized_data = []
                for cv in df_temp["Collision Voltage"].unique():
                    cv_data = df_temp[df_temp["Collision Voltage"] == cv].copy()
                    max_intensity = cv_data["Intensity"].max()
                    if max_intensity > 0:
                        cv_data["Intensity"] = cv_data["Intensity"] / max_intensity
                    normalized_data.append(cv_data)
                df_normalized = pd.concat(normalized_data, ignore_index=True)
                filtered_data = df_normalized[["CCS", "Drift Time", "Collision Voltage", "Intensity"]].values

            # Create heatmap grid
            grid_resolution = 200
            grid_x = np.linspace(x_min, x_max, num=grid_resolution)
            grid_y = np.linspace(y_min, y_max, num=grid_resolution)
            X, Y = np.meshgrid(grid_x, grid_y)

            # Interpolate intensities over the meshgrid
            Z = griddata(
                (filtered_data[:, 2], filtered_data[:, 0]),  # Points (CV, CCS)
                filtered_data[:, 3],  # Intensity
                (X, Y),  # Grid
                method='cubic',
                fill_value=0
            )
            
            # Apply smoothing if requested
            if apply_smoothing:
                # Ensure window_length is odd and doesn't exceed array size
                effective_window = min(window_length, min(Z.shape) - 1)
                if effective_window % 2 == 0:
                    effective_window -= 1
                effective_window = max(3, effective_window)
                
                effective_poly_order = min(poly_order, effective_window - 1)
                
                # Apply 2D smoothing by smoothing along both axes
                Z_smooth = np.zeros_like(Z)
                for i in range(Z.shape[0]):
                    if not np.all(np.isnan(Z[i, :])):
                        valid_mask = ~np.isnan(Z[i, :])
                        if np.sum(valid_mask) >= effective_window:
                            Z_smooth[i, valid_mask] = savgol_filter(Z[i, valid_mask], effective_window, effective_poly_order)
                        else:
                            Z_smooth[i, :] = Z[i, :]
                    else:
                        Z_smooth[i, :] = Z[i, :]
                
                for j in range(Z.shape[1]):
                    if not np.all(np.isnan(Z_smooth[:, j])):
                        valid_mask = ~np.isnan(Z_smooth[:, j])
                        if np.sum(valid_mask) >= effective_window:
                            Z_smooth[valid_mask, j] = savgol_filter(Z_smooth[valid_mask, j], effective_window, effective_poly_order)
                
                Z = Z_smooth

            # Set up the plot
            fig, ax = plt.subplots(figsize=(figure_size, figure_size), dpi=dpi)
            
            # Handle custom colorbar settings
            if use_custom_colorbar:
                z_max = np.nanmax(Z)
                z_min = np.nanmin(Z)
                vmin = z_min + (vmin_percent / 100) * (z_max - z_min)
                vmax = z_min + (vmax_percent / 100) * (z_max - z_min)
            else:
                vmin, vmax = None, None

            # Create the heatmap
            c = ax.pcolormesh(X, Y, Z, cmap=color_map, shading='auto', vmin=vmin, vmax=vmax)

            # Customize the plot
            ax.set_xlabel("Collision Voltage", fontsize=font_size, fontweight='bold')
            ax.set_ylabel("CCS (Ų)", fontsize=font_size, fontweight='bold')
            ax.tick_params(labelsize=font_size-2)

            # Style the plot borders
            for spine in ax.spines.values():
                spine.set_color('black')
                spine.set_linewidth(1.5)

            # Add colorbar if requested
            if show_colorbar:
                cbar = plt.colorbar(c, ax=ax, shrink=colorbar_shrink, aspect=colorbar_aspect)
                intensity_label = "Normalized Intensity" if normalize_data else "Intensity"
                cbar.set_label(intensity_label, fontsize=font_size, fontweight='bold')
                cbar.ax.tick_params(labelsize=font_size-2)

            # Add reference lines and labels
            for i in range(num_x_lines):
                ax.axvline(x=x_values[i], color='white', linestyle='--', linewidth=2, alpha=0.8)
                ax.text(x_values[i], y_max * 0.98, x_labels[i], color='white', 
                       va='top', ha='center', fontsize=font_size-1, fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))

            for i in range(num_y_lines):
                ax.axhline(y=y_values[i], color='white', linestyle='--', linewidth=2, alpha=0.8)
                ax.text(x_min * 1.02, y_values[i], y_labels[i], color='white', 
                       va='center', ha='left', fontsize=font_size-1, fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))

            plt.tight_layout()
            
            # Display the plot
            st.pyplot(fig)
            
            # Store the figure and processed data for downloads
            st.session_state["current_figure"] = fig
            st.session_state["processed_data"] = filtered_data

    # Download Section
    if "current_figure" in st.session_state and "processed_data" in st.session_state:
        with st.container():
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<h2 class="section-header">💾 Download Options</h2>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Download CSV
                csv_data = pd.DataFrame(st.session_state["processed_data"], 
                                      columns=["CCS", "Drift Time", "Collision Voltage", "Intensity"])
                csv = csv_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📊 Download Processed CSV",
                    data=csv,
                    file_name="calibrated_twim_extract.csv",
                    mime="text/csv",
                    help="Download the processed and calibrated data"
                )
            
            with col2:
                # Download PNG
                img_png = BytesIO()
                st.session_state["current_figure"].savefig(img_png, format='png', bbox_inches="tight", dpi=dpi)
                img_png.seek(0)
                st.download_button(
                    "🖼️ Download PNG Image",
                    data=img_png,
                    file_name="ciu_heatmap.png",
                    mime="image/png",
                    help="Download high-quality PNG image"
                )
            
            with col3:
                # Download SVG for vector graphics
                img_svg = BytesIO()
                st.session_state["current_figure"].savefig(img_svg, format='svg', bbox_inches="tight")
                img_svg.seek(0)
                st.download_button(
                    "📈 Download SVG Image",
                    data=img_svg,
                    file_name="ciu_heatmap.svg",
                    mime="image/svg+xml",
                    help="Download scalable vector graphics"
                )
            
            st.markdown('</div>', unsafe_allow_html=True)

# Information Section
with st.container():
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("""
    ### 📖 How to Use This Tool
    
    1. **Upload Files**: Upload your TWIM Extract CSV and calibration CSV files
    2. **Configure Settings**: Select instrument type, charge state, and injection time (if applicable)
    3. **Process Data**: Click "Process Data" to calibrate your measurements
    4. **Customize Visualization**: Adjust plot settings, normalization, smoothing, and colorbar options
    5. **Generate Plot**: Create your CIU heatmap with all customizations applied
    6. **Download Results**: Save your processed data and publication-ready figures
    
    **New Features:**
    - **Normalization**: Normalize each collision voltage slice to maximum intensity of 1
    - **Savitzky-Golay Smoothing**: Reduce noise with customizable window and polynomial order
    - **Advanced Colorbar**: Custom thresholds and appearance settings
    - **Enhanced Styling**: Professional appearance with consistent formatting
    - **Multiple Export Formats**: PNG, SVG, and CSV downloads available
    """)
    st.markdown('</div>', unsafe_allow_html=True)
