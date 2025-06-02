import streamlit as st
import zipfile
import tempfile
import os
import pandas as pd
from io import BytesIO

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
    <p>This is one of the tools I use to plot my data - I hope it is helpful to you!</p>
</div>
""", unsafe_allow_html=True)

# Header
    st.markdown("""
    <div class="main-header">
        <h1>Protein CCS Logging Form</h1>
        <p>Contribute collision cross-section data from papers to help build our database!</p>
    </div>
    """, unsafe_allow_html=True)

# Upload files
twim_extract_file = st.file_uploader("Upload the TWIM Extract CSV file", type="csv")
calibration_file = st.file_uploader("Upload the calibration CSV file", type="csv")
    
if twim_extract_file and calibration_file:
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

    st.write("Uploaded TWIM Extract Data:")
    st.dataframe(twim_df.head())

     # Read calibration data
    cal_df = pd.read_csv(calibration_file)
    st.write("Uploaded Calibration Data:")
    st.dataframe(cal_df.head())

    if 'Z' not in cal_df.columns:
        st.error("Calibration data must include a 'Z' column for charge state.")
        return

    data_type = st.radio("Is your data from a Synapt or Cyclic instrument?", ["Synapt", "Cyclic"])
    charge_state = st.number_input("Enter the charge state of the protein (Z)", min_value=1, max_value=100, step=1)
    inject_time = None

    if data_type == "Cyclic":
        inject_time = st.number_input("Enter the injection time (ms)", min_value=0.0, value=0.0, step=0.1)

    # Button to process data
    if st.button("Process Data"):
        if inject_time is not None and data_type == "Cyclic":
            twim_df["Drift Time"] = twim_df["Drift Time"] - inject_time

        cal_data = cal_df[cal_df["Z"] == charge_state]
        if cal_data.empty:
            st.error(f"No calibration data found for charge state {charge_state}")
            return

        if "Drift" not in cal_data.columns or "CCS" not in cal_data.columns:
            st.error("Calibration data must include 'Drift' and 'CCS' columns.")
            return

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

# If processed data exists, allow customization and visualization
if "calibrated_array" in st.session_state:
    calibrated_array = st.session_state["calibrated_array"]

    # Customization section
    st.header("📊 CIU Heatmap Customization")

    color_map = st.selectbox("Color Map", [
        "viridis", "plasma", "inferno", "cividis", "coolwarm", "magma", 
        "Blues", "Greens", "Purples", "Oranges", "Reds", "Greens_r", 
        "Purples_r", "Blues_r", "Oranges_r", "Reds_r", "Spectral"
    ])
    font_size = st.slider("Font Size", 8, 24, 12, 1)
    figure_size = st.slider("Figure Size (inches)", 1, 12, 10, 1)
    dpi = st.slider("Figure Resolution (DPI)", 100, 1000, 300, 50)

    x_min, x_max = st.slider("Crop Collision Voltage Range",
        float(calibrated_array[:, 2].min()),
        float(calibrated_array[:, 2].max()),
        (float(calibrated_array[:, 2].min()), float(calibrated_array[:, 2].max()))
    )
    y_min, y_max = st.slider("Crop CCS Range",
        float(calibrated_array[:, 0].min()),
        float(calibrated_array[:, 0].max()),
        (float(calibrated_array[:, 0].min()), float(calibrated_array[:, 0].max()))
    )

    # Create heatmap grid with CCS and Collision Voltage as axes
    grid_x = np.linspace(x_min, x_max, num=100)
    grid_y = np.linspace(y_min, y_max, num=100)

    # Create a meshgrid for the x and y axes
    X, Y = np.meshgrid(grid_x, grid_y)

    # Interpolate intensities over the meshgrid
    from scipy.interpolate import griddata
    Z = griddata(
        (calibrated_array[:, 2], calibrated_array[:, 0]),  # Points
        calibrated_array[:, 3],  # Intensity
        (X, Y),  # Grid
        method='cubic'  # Interpolation method
    )

    # Plot the heatmap
    fig, ax = plt.subplots(figsize=(figure_size, figure_size), dpi=dpi)
    c = ax.pcolormesh(X, Y, Z, cmap=color_map, shading='auto')

    # Customize the plot with labels and ticks
    ax.set_xlabel("Collision Voltage", fontsize=font_size)
    ax.set_ylabel("CCS", fontsize=font_size)
    ax.tick_params(labelsize=font_size)

    # Add a black line around the heatmap
    ax.spines['top'].set_color('black')
    ax.spines['right'].set_color('black')
    ax.spines['bottom'].set_color('black')
    ax.spines['left'].set_color('black')

    # Add dashed lines based on user input for x-values and y-values
    num_x_labels = st.slider("How many x-values to label (0-5)?", 0, 5, 0)
    x_values = []
    x_labels = []
    for i in range(num_x_labels):
        value = st.number_input(f"Enter x-value {i+1}", min_value=float(x_min), max_value=float(x_max))
        label = st.text_input(f"Enter label for x-value {i+1}")
        x_values.append(value)
        x_labels.append(label)

    num_y_labels = st.slider("How many y-values to label (0-5)?", 0, 5, 0)
    y_values = []
    y_labels = []
    for i in range(num_y_labels):
        value = st.number_input(f"Enter y-value {i+1}", min_value=float(y_min), max_value=float(y_max))
        label = st.text_input(f"Enter label for y-value {i+1}")
        y_values.append(value)
        y_labels.append(label)

    # Plot the dashed lines and labels based on user input
    for i in range(num_x_labels):
        ax.axvline(x=x_values[i], color='white', linestyle='--', linewidth=1)
        ax.text(x=x_values[i], y=y_max, s=x_labels[i], color='white', va='bottom', ha='center', fontsize=font_size)

    for i in range(num_y_labels):
        ax.axhline(y=y_values[i], color='white', linestyle='--', linewidth=1)
        ax.text(x=x_min, y=y_values[i], s=y_labels[i], color='white', va='center', ha='left', fontsize=font_size)

    plt.tight_layout()
    st.pyplot(fig)

    # Download buttons
    csv = pd.DataFrame(calibrated_array, columns=["CCS", "Drift Time", "Collision Voltage", "Intensity"]).to_csv(index=False).encode('utf-8')
    st.download_button("Download Calibrated CSV", data=csv, file_name="calibrated_twim_extract.csv", mime="text/csv")
    img = BytesIO()
    fig.savefig(img, format='png', bbox_inches="tight")
    img.seek(0)
    st.download_button("Download CIU Heatmap Image", data=img, file_name="ciu_heatmap.png", mime="image/png")
