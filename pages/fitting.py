import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit
import io
import json

# Set page config
st.set_page_config(page_title="Gaussian Fitting", layout="wide")

def gaussian(x, amplitude, center, width):
    """Single Gaussian function"""
    return amplitude * np.exp(-(x - center)**2 / (2 * width**2))

def multi_gaussian(x, *params):
    """Multiple Gaussian function"""
    y = np.zeros_like(x)
    for i in range(0, len(params), 3):
        y += gaussian(x, params[i], params[i+1], params[i+2])
    return y

def interpolate_charge_state(df_charge, ccs_range):
    """Interpolate a charge state's data to a common CCS range"""
    if len(df_charge) < 2:
        return np.zeros_like(ccs_range)
    
    # Remove duplicates and sort by CCS
    df_charge = df_charge.drop_duplicates(subset=['CCS']).sort_values('CCS')
    
    # Create interpolation function
    interp_func = interp1d(
        df_charge['CCS'], 
        df_charge['Scaled Intensity'], 
        kind='linear', 
        bounds_error=False, 
        fill_value=0
    )
    
    return interp_func(ccs_range)

def create_summed_data(df):
    """Create summed data across all charge states"""
    # Get the full CCS range
    ccs_min = df['CCS'].min()
    ccs_max = df['CCS'].max()
    
    # Create a common CCS range with high resolution
    ccs_range = np.linspace(ccs_min, ccs_max, 1000)
    
    # Interpolate each charge state and sum
    summed_intensity = np.zeros_like(ccs_range)
    
    for charge in df['Charge'].unique():
        df_charge = df[df['Charge'] == charge]
        interpolated = interpolate_charge_state(df_charge, ccs_range)
        summed_intensity += interpolated
    
    # Create summed dataframe
    summed_df = pd.DataFrame({
        'CCS': ccs_range,
        'Scaled Intensity': summed_intensity
    })
    
    return summed_df

def auto_fit_gaussians(x, y, n_gaussians):
    """Automatically fit Gaussians to the data using local maxima"""
    try:
        from scipy.signal import find_peaks, peak_prominences
        
        # Smooth the data slightly to reduce noise in peak detection
        from scipy.ndimage import gaussian_filter1d
        y_smooth = gaussian_filter1d(y, sigma=1)
        
        # Find all local maxima with various criteria
        # Use multiple criteria to catch different types of peaks
        min_height = np.max(y) * 0.05  # 5% of max height
        min_distance = max(1, len(y) // 50)  # Minimum distance between peaks
        
        # Find peaks with prominence to avoid noise
        peaks, properties = find_peaks(
            y_smooth, 
            height=min_height,
            distance=min_distance,
            prominence=np.max(y) * 0.02  # 2% prominence
        )
        
        if len(peaks) == 0:
            # If no peaks found, try with lower thresholds
            peaks, _ = find_peaks(y_smooth, distance=min_distance)
        
        # Calculate peak prominences to rank them
        if len(peaks) > 0:
            prominences = peak_prominences(y_smooth, peaks)[0]
            # Sort peaks by prominence (more prominent = better peak)
            peak_ranking = np.argsort(prominences)[::-1]
            ranked_peaks = peaks[peak_ranking]
        else:
            ranked_peaks = []
        
        # Select the best peaks up to n_gaussians
        if len(ranked_peaks) >= n_gaussians:
            selected_peaks = ranked_peaks[:n_gaussians]
        else:
            # If we don't have enough peaks, add some at reasonable locations
            selected_peaks = list(ranked_peaks)
            
            # Find gaps in the data where we might place additional Gaussians
            if len(selected_peaks) > 0:
                # Sort selected peaks by position
                selected_peaks.sort()
                # Add peaks in the largest gaps
                while len(selected_peaks) < n_gaussians:
                    gaps = []
                    for i in range(len(selected_peaks) + 1):
                        if i == 0:
                            start_idx = 0
                        else:
                            start_idx = selected_peaks[i-1]
                        
                        if i == len(selected_peaks):
                            end_idx = len(x) - 1
                        else:
                            end_idx = selected_peaks[i]
                        
                        gap_size = end_idx - start_idx
                        gap_center = (start_idx + end_idx) // 2
                        gaps.append((gap_size, gap_center))
                    
                    # Add peak at the center of the largest gap
                    largest_gap = max(gaps, key=lambda x: x[0])
                    selected_peaks.append(largest_gap[1])
                    selected_peaks.sort()
            else:
                # No peaks found at all, distribute evenly
                selected_peaks = np.linspace(len(y)//10, len(y)-len(y)//10, n_gaussians, dtype=int)
        
        # Convert indices back to sorted order for parameter extraction
        selected_peaks = sorted(selected_peaks)
        
        # Initial parameters using the actual peak values
        initial_params = []
        for peak_idx in selected_peaks:
            # Use actual peak height as amplitude
            amplitude = y[peak_idx]
            center = x[peak_idx]
            
            # Estimate width based on peak shape
            # Look for half-maximum points around the peak
            half_max = amplitude / 2
            
            # Search left and right for half-maximum
            left_idx = peak_idx
            right_idx = peak_idx
            
            # Search left
            while left_idx > 0 and y[left_idx] > half_max:
                left_idx -= 1
            
            # Search right  
            while right_idx < len(y) - 1 and y[right_idx] > half_max:
                right_idx += 1
            
            # Calculate FWHM-based width
            if right_idx > left_idx:
                fwhm = x[right_idx] - x[left_idx]
                width = fwhm / (2 * np.sqrt(2 * np.log(2)))  # Convert FWHM to sigma
            else:
                # Fallback width
                width = (x.max() - x.min()) / (n_gaussians * 4)
            
            # Ensure reasonable width bounds
            min_width = (x.max() - x.min()) / 100
            max_width = (x.max() - x.min()) / 2
            width = np.clip(width, min_width, max_width)
            
            initial_params.extend([amplitude, center, width])
        
        # Fit the curve with the improved initial guesses
        popt, _ = curve_fit(
            multi_gaussian, 
            x, y, 
            p0=initial_params, 
            maxfev=10000,
            bounds=(
                # Lower bounds: [amp_min, center_min, width_min] for each Gaussian
                [0, x.min(), 0.1] * n_gaussians,
                # Upper bounds: [amp_max, center_max, width_max] for each Gaussian  
                [y.max() * 2, x.max(), (x.max() - x.min())] * n_gaussians
            )
        )
        
        return popt
        
    except Exception as e:
        # If fitting fails, return reasonable defaults based on data
        print(f"Auto-fitting failed: {e}, using defaults")
        x_range = x.max() - x.min()
        centers = np.linspace(x.min() + x_range/4, x.max() - x_range/4, n_gaussians)
        params = []
        for center in centers:
            # Use a reasonable amplitude based on data
            center_idx = np.argmin(np.abs(x - center))
            amplitude = y[center_idx] if center_idx < len(y) else y.max()/n_gaussians
            params.extend([amplitude, center, x_range/(n_gaussians*4)])
        return params

def save_fit_result(charge_state, params, n_gaussians, r_squared, rmse):
    """Save a fit result to the session state"""
    if 'all_fit_results' not in st.session_state:
        st.session_state.all_fit_results = {}
    
    st.session_state.all_fit_results[charge_state] = {
        'charge': charge_state,
        'n_gaussians': n_gaussians,
        'r_squared': r_squared,
        'rmse': rmse,
        'parameters': []
    }
    
    for i in range(n_gaussians):
        st.session_state.all_fit_results[charge_state]['parameters'].append({
            'gaussian': i+1,
            'amplitude': params[i*3],
            'center': params[i*3+1],
            'width': params[i*3+2]
        })

def main():
    st.title("🔍 Gaussian Fitting Tool")
    st.markdown("Fit Gaussian curves to your calibrated data with interactive controls")
    
    # File upload
    uploaded_file = st.file_uploader("Upload calibrated CSV file", type=['csv'])
    
    if uploaded_file is not None:
        try:
            # Load data
            df = pd.read_csv(uploaded_file)
            
            # Validate required columns
            required_cols = ['Charge', 'CCS', 'Scaled Intensity']
            if not all(col in df.columns for col in required_cols):
                st.error(f"Missing required columns. Need: {required_cols}")
                return
            
            # Sidebar controls
            st.sidebar.header("📊 Data Selection")
            
            # Show available charge states
            charges = sorted(df['Charge'].unique())
            st.sidebar.write(f"Available charges: {charges}")
            
            # Data selection mode
            mode = st.sidebar.radio(
                "Analysis Mode",
                ["Individual Charge State", "Summed Data"]
            )
            
            # Initialize all_fit_results if not exists
            if 'all_fit_results' not in st.session_state:
                st.session_state.all_fit_results = {}
            
            # Replace the sidebar multi-charge results section and export section with this:

    # In the sidebar (around line 280, replace the multi-charge results management section):
    if mode == "Individual Charge State":
        st.sidebar.header("🗂️ Sequential Fitting Workflow")
        
        # Progress indicator
        total_charges = len(charges)
        fitted_charges = len(st.session_state.all_fit_results)
        
        st.sidebar.progress(fitted_charges / total_charges)
        st.sidebar.write(f"Progress: {fitted_charges}/{total_charges} charge states fitted")
        
        # Show fitted and remaining charges
        fitted_list = list(st.session_state.all_fit_results.keys())
        remaining_list = [c for c in charges if c not in fitted_list]
        
        if fitted_list:
            st.sidebar.write("**✅ Fitted:**")
            for charge in sorted(fitted_list):
                result = st.session_state.all_fit_results[charge]
                st.sidebar.write(f"• Charge {charge}: {result['n_gaussians']}G (R²={result['r_squared']:.3f})")
        
        if remaining_list:
            st.sidebar.write("**⏳ Remaining:**")
            for charge in sorted(remaining_list):
                st.sidebar.write(f"• Charge {charge}")
        
        # Auto-select next unfitted charge
        if remaining_list and 'auto_select' not in st.session_state:
            st.session_state.auto_select = True
        
        if st.session_state.get('auto_select', False) and remaining_list:
            next_charge = min(remaining_list)
            if selected_charge != next_charge:
                st.rerun()
        
        # Quick navigation
        st.sidebar.write("**🎯 Quick Navigation:**")
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("⏮️ Previous"):
                current_idx = charges.index(selected_charge)
                if current_idx > 0:
                    st.session_state.selected_charge = charges[current_idx - 1]
                    st.rerun()
        
        with col2:
            if st.button("⏭️ Next"):
                current_idx = charges.index(selected_charge)
                if current_idx < len(charges) - 1:
                    st.session_state.selected_charge = charges[current_idx + 1]
                    st.rerun()
        
        # Management buttons
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🗑️ Clear All"):
                st.session_state.all_fit_results = {}
                st.sidebar.success("All results cleared!")
        
        with col2:
            if st.button("🔄 Reset Current"):
                if selected_charge in st.session_state.all_fit_results:
                    del st.session_state.all_fit_results[selected_charge]
                    st.sidebar.success(f"Charge {selected_charge} reset!")
    
    # Replace the charge selection with this (around line 320):
    if mode == "Individual Charge State":
        # Use session state for charge selection to enable navigation
        if 'selected_charge' not in st.session_state:
            remaining_charges = [c for c in charges if c not in st.session_state.all_fit_results]
            st.session_state.selected_charge = min(remaining_charges) if remaining_charges else charges[0]
        
        selected_charge = st.sidebar.selectbox(
            "Select Charge State", 
            charges,
            index=charges.index(st.session_state.selected_charge),
            key="charge_selector"
        )
        
        # Update session state when selection changes
        if selected_charge != st.session_state.selected_charge:
            st.session_state.selected_charge = selected_charge
        
        plot_data = df[df['Charge'] == selected_charge].copy()
        plot_data = plot_data.sort_values('CCS')
        data_label = f"Charge {selected_charge}"
        
        # Show fit status for current charge
        if selected_charge in st.session_state.all_fit_results:
            st.sidebar.success(f"✅ Charge {selected_charge} already fitted!")
            if st.sidebar.button("🔄 Load Saved Parameters"):
                saved_result = st.session_state.all_fit_results[selected_charge]
                loaded_params = []
                for param in saved_result['parameters']:
                    loaded_params.extend([param['amplitude'], param['center'], param['width']])
                st.session_state.fitted_params[data_label] = loaded_params
                n_gaussians = saved_result['n_gaussians']
        else:
            st.sidebar.info(f"⏳ Fit Charge {selected_charge}")
    
    # Replace the save button section (around line 600) with this enhanced version:
    with col2:
        # Fit statistics
        st.subheader("📈 Fit Statistics")
        
        # Calculate R-squared and RMSE
        y_data_interp = np.interp(x_fit, plot_data['CCS'], plot_data['Scaled Intensity'])
        ss_res = np.sum((y_data_interp - y_fit) ** 2)
        ss_tot = np.sum((y_data_interp - np.mean(y_data_interp)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        rmse = np.sqrt(np.mean((y_data_interp - y_fit)**2))
        
        st.metric("R²", f"{r_squared:.4f}")
        st.metric("RMSE", f"{rmse:.2f}")
        
        # Save/Update buttons for individual charge states
        if mode == "Individual Charge State":
            col_a, col_b = st.columns(2)
            
            with col_a:
                if selected_charge not in st.session_state.all_fit_results:
                    if st.button("💾 Save Fit", type="primary", use_container_width=True):
                        save_fit_result(selected_charge, params, n_gaussians, r_squared, rmse)
                        st.success(f"✅ Saved!")
                        # Auto-advance to next unfitted charge
                        remaining = [c for c in charges if c not in st.session_state.all_fit_results]
                        if remaining:
                            st.session_state.selected_charge = min(remaining)
                            st.rerun()
                else:
                    if st.button("🔄 Update Fit", type="secondary", use_container_width=True):
                        save_fit_result(selected_charge, params, n_gaussians, r_squared, rmse)
                        st.success(f"✅ Updated!")
            
            with col_b:
                if st.button("⏭️ Save & Next", use_container_width=True):
                    save_fit_result(selected_charge, params, n_gaussians, r_squared, rmse)
                    remaining = [c for c in charges if c not in st.session_state.all_fit_results]
                    if remaining:
                        st.session_state.selected_charge = min(remaining)
                        st.success("✅ Saved! Moving to next...")
                        st.rerun()
                    else:
                        st.success("🎉 All charges fitted!")
        
        # Parameter summary
        st.subheader("📋 Parameters")
        param_df = pd.DataFrame({
            'Gaussian': [i+1 for i in range(n_gaussians)],
            'Amplitude': [f"{params[i*3]:.3f}" for i in range(n_gaussians)],
            'Center': [f"{params[i*3+1]:.3f}" for i in range(n_gaussians)],
            'Width': [f"{params[i*3+2]:.3f}" for i in range(n_gaussians)]
        })
        st.dataframe(param_df, use_container_width=True)
    
    # Replace the entire export section with this comprehensive version:
    # Export section
    st.header("💾 Export Results")
    
    if mode == "Individual Charge State":
        # Show completion status
        total_charges = len(charges)
        fitted_charges = len(st.session_state.all_fit_results)
        
        if fitted_charges == total_charges:
            st.success(f"🎉 All {total_charges} charge states fitted! Ready for export.")
        else:
            st.info(f"📊 {fitted_charges}/{total_charges} charge states fitted.")
        
        # Export options
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Download all parameters as CSV
            if st.button("📋 All Parameters CSV", type="primary") and st.session_state.all_fit_results:
                # Create comprehensive parameters DataFrame
                param_rows = []
                for charge, result in st.session_state.all_fit_results.items():
                    for param in result['parameters']:
                        param_rows.append({
                            'Charge': charge,
                            'Gaussian': param['gaussian'],
                            'Amplitude': param['amplitude'],
                            'Center': param['center'],
                            'Width': param['width'],
                            'R_squared': result['r_squared'],
                            'RMSE': result['rmse'],
                            'Total_Gaussians': result['n_gaussians']
                        })
                
                param_df = pd.DataFrame(param_rows)
                csv_buffer = io.StringIO()
                param_df.to_csv(csv_buffer, index=False)
                
                st.download_button(
                    label="📥 Download Parameters CSV",
                    data=csv_buffer.getvalue(),
                    file_name="all_gaussian_parameters.csv",
                    mime="text/csv",
                    type="primary"
                )
        
        with col2:
            # Download summary statistics CSV
            if st.button("📊 Summary Stats CSV") and st.session_state.all_fit_results:
                summary_rows = []
                for charge, result in st.session_state.all_fit_results.items():
                    summary_rows.append({
                        'Charge': charge,
                        'N_Gaussians': result['n_gaussians'],
                        'R_squared': result['r_squared'],
                        'RMSE': result['rmse'],
                        'Peak_Centers': ', '.join([f"{p['center']:.3f}" for p in result['parameters']]),
                        'Peak_Amplitudes': ', '.join([f"{p['amplitude']:.3f}" for p in result['parameters']]),
                        'Peak_Widths': ', '.join([f"{p['width']:.3f}" for p in result['parameters']])
                    })
                
                summary_df = pd.DataFrame(summary_rows)
                csv_buffer = io.StringIO()
                summary_df.to_csv(csv_buffer, index=False)
                
                st.download_button(
                    label="📥 Download Summary CSV",
                    data=csv_buffer.getvalue(),
                    file_name="gaussian_fits_summary.csv",
                    mime="text/csv"
                )
        
        with col3:
            # Download all as JSON
            if st.button("📄 All Data JSON") and st.session_state.all_fit_results:
                all_results = {
                    'metadata': {
                        'total_charges': len(st.session_state.all_fit_results),
                        'charge_states': sorted(list(st.session_state.all_fit_results.keys())),
                        'export_timestamp': pd.Timestamp.now().isoformat()
                    },
                    'fits': st.session_state.all_fit_results
                }
                
                json_str = json.dumps(all_results, indent=2)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name="all_gaussian_fits.json",
                    mime="application/json"
                )
        
        with col4:
            # Download current charge fit data
            if st.button("📈 Current Fit Data"):
                fit_df = pd.DataFrame({
                    'CCS': x_fit,
                    'Total_Fit': y_fit,
                    'Charge': selected_charge
                })
                
                # Add individual Gaussians
                for i in range(n_gaussians):
                    fit_df[f'Gaussian_{i+1}'] = individual_gaussians[i]
                
                csv_buffer = io.StringIO()
                fit_df.to_csv(csv_buffer, index=False)
                
                st.download_button(
                    label="📥 Download Current CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"fit_data_charge_{selected_charge}.csv",
                    mime="text/csv"
                )
        
        # Show detailed results table
        if st.session_state.all_fit_results:
            st.subheader("📊 All Fitted Results")
            
            # Create expandable sections for each charge
            for charge in sorted(st.session_state.all_fit_results.keys()):
                result = st.session_state.all_fit_results[charge]
                
                with st.expander(f"Charge {charge} - {result['n_gaussians']} Gaussians (R² = {result['r_squared']:.4f})"):
                    cols = st.columns([1, 1, 1, 1])
                    cols[0].metric("R²", f"{result['r_squared']:.4f}")
                    cols[1].metric("RMSE", f"{result['rmse']:.3f}")
                    cols[2].metric("Gaussians", result['n_gaussians'])
                    cols[3].metric("Charge", charge)
                    
                    # Parameters table
                    param_data = []
                    for param in result['parameters']:
                        param_data.append({
                            'Gaussian': param['gaussian'],
                            'Amplitude': f"{param['amplitude']:.3f}",
                            'Center': f"{param['center']:.3f}",
                            'Width': f"{param['width']:.3f}"
                        })
                    
                    param_df = pd.DataFrame(param_data)
                    st.dataframe(param_df, use_container_width=True)
                
                else:  # Summed data mode
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Download summed fit parameters
                        if st.button("📊 Download Parameters"):
                            param_dict = {
                                'data_label': data_label,
                                'mode': 'summed',
                                'n_gaussians': n_gaussians,
                                'r_squared': r_squared,
                                'rmse': rmse,
                                'parameters': []
                            }
                            
                            for i in range(n_gaussians):
                                param_dict['parameters'].append({
                                    'gaussian': i+1,
                                    'amplitude': params[i*3],
                                    'center': params[i*3+1],
                                    'width': params[i*3+2]
                                })
                            
                            json_str = json.dumps(param_dict, indent=2)
                            st.download_button(
                                label="Download JSON",
                                data=json_str,
                                file_name="gaussian_fit_summed_data.json",
                                mime="application/json"
                            )
                    
                    with col2:
                        # Download summed fit data
                        if st.button("📈 Download Fit Data"):
                            fit_df = pd.DataFrame({
                                'CCS': x_fit,
                                'Fitted_Intensity': y_fit
                            })
                            
                            # Add individual Gaussians
                            for i in range(n_gaussians):
                                fit_df[f'Gaussian_{i+1}'] = individual_gaussians[i]
                            
                            csv_buffer = io.StringIO()
                            fit_df.to_csv(csv_buffer, index=False)
                            
                            st.download_button(
                                label="Download CSV",
                                data=csv_buffer.getvalue(),
                                file_name="fit_data_summed.csv",
                                mime="text/csv"
                            )
        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.error("Please ensure your CSV has the required columns: Charge, CCS, Scaled Intensity")
    
    else:
        st.info("👆 Please upload a CSV file to get started")
        st.markdown("""
        ### Required CSV Format:
        Your file should contain these columns:
        - **Charge**: Charge state values
        - **CCS**: Collision Cross Section values
        - **Scaled Intensity**: Intensity values
        
        ### Features:
        - 🔄 **Auto-fit**: Automatically detect peaks and fit Gaussians
        - 🎛️ **Manual Control**: Fine-tune parameters with interactive sliders
        - 🔒 **Fix Parameters**: Lock specific parameters during fitting
        - 📊 **Individual/Summed**: Analyze single charge states or summed data
        - 💾 **Multi-Export**: Save results in JSON, CSV, or combined formats
        """)

if __name__ == "__main__":
    main()
