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
            
            # Show multi-charge results management for individual mode
            if mode == "Individual Charge State":
                st.sidebar.header("🗂️ Multi-Charge Results")
                
                # Show currently saved results
                if st.session_state.all_fit_results:
                    st.sidebar.write("**Saved Fits:**")
                    for charge, result in st.session_state.all_fit_results.items():
                        st.sidebar.write(f"• Charge {charge}: {result['n_gaussians']} Gaussians (R² = {result['r_squared']:.3f})")
                else:
                    st.sidebar.write("*No saved results yet*")
                
                # Clear all results button
                if st.sidebar.button("🗑️ Clear All Saved Results"):
                    st.session_state.all_fit_results = {}
                    st.sidebar.success("All results cleared!")
                
                # Export all saved results
                if st.session_state.all_fit_results:
                    st.sidebar.markdown("---")
                    st.sidebar.subheader("📥 Export All Results")
                    
                    # Create summary DataFrame for all results
                    summary_rows = []
                    for charge, result in st.session_state.all_fit_results.items():
                        for param in result['parameters']:
                            summary_rows.append({
                                'Charge': charge,
                                'Gaussian': param['gaussian'],
                                'Amplitude': param['amplitude'],
                                'Center': param['center'],
                                'Width': param['width'],
                                'R_squared': result['r_squared'],
                                'RMSE': result['rmse'],
                                'N_Gaussians': result['n_gaussians']
                            })
                    
                    summary_df = pd.DataFrame(summary_rows)
                    csv_buffer = io.StringIO()
                    summary_df.to_csv(csv_buffer, index=False)
                    
                    st.sidebar.download_button(
                        label="📋 Download All Results (CSV)",
                        data=csv_buffer.getvalue(),
                        file_name="all_gaussian_fits.csv",
                        mime="text/csv",
                        help="Download all saved fits as a single CSV file"
                    )
                
                st.sidebar.markdown("---")
            
            # Prepare data based on mode
            if mode == "Individual Charge State":
                selected_charge = st.sidebar.selectbox("Select Charge State", charges)
                plot_data = df[df['Charge'] == selected_charge].copy()
                plot_data = plot_data.sort_values('CCS')
                data_label = f"Charge {selected_charge}"
                
                # Check if this charge state has been fitted before
                if selected_charge in st.session_state.all_fit_results:
                    st.info(f"✅ Charge {selected_charge} has been fitted and saved. You can modify and re-save if needed.")
                
            else:
                plot_data = create_summed_data(df)
                data_label = "Summed Data"
            
            # Remove zero intensities for cleaner fitting
            plot_data = plot_data[plot_data['Scaled Intensity'] > 0]
            
            if len(plot_data) == 0:
                st.error("No data points with positive intensity found")
                return
            
            # Fitting controls
            st.sidebar.header("🎯 Fitting Controls")
            
            # Number of Gaussians
            n_gaussians = st.sidebar.number_input(
                "Number of Gaussians", 
                min_value=1, 
                max_value=10, 
                value=1
            )
            
            # Auto-fit button
            if st.sidebar.button("🔄 Auto-fit Gaussians"):
                x_data = plot_data['CCS'].values
                y_data = plot_data['Scaled Intensity'].values
                fitted_params = auto_fit_gaussians(x_data, y_data, n_gaussians)
                
                # Store fitted parameters in session state
                if 'fitted_params' not in st.session_state:
                    st.session_state.fitted_params = {}
                st.session_state.fitted_params[data_label] = fitted_params
                st.success("Auto-fitting completed!")
            
            # Initialize parameters if not exists
            if 'fitted_params' not in st.session_state:
                st.session_state.fitted_params = {}
            
            if data_label not in st.session_state.fitted_params:
                # Default parameters
                x_range = plot_data['CCS'].max() - plot_data['CCS'].min()
                centers = np.linspace(
                    plot_data['CCS'].min() + x_range/4, 
                    plot_data['CCS'].max() - x_range/4, 
                    n_gaussians
                )
                default_params = []
                for center in centers:
                    default_params.extend([
                        plot_data['Scaled Intensity'].max()/n_gaussians,  # amplitude
                        center,  # center
                        x_range/(n_gaussians*4)  # width
                    ])
                st.session_state.fitted_params[data_label] = default_params
            
            # Adjust parameters list if number of Gaussians changed
            current_params = st.session_state.fitted_params[data_label]
            if len(current_params) != n_gaussians * 3:
                x_range = plot_data['CCS'].max() - plot_data['CCS'].min()
                centers = np.linspace(
                    plot_data['CCS'].min() + x_range/4, 
                    plot_data['CCS'].max() - x_range/4, 
                    n_gaussians
                )
                new_params = []
                for i, center in enumerate(centers):
                    if i * 3 < len(current_params):
                        # Use existing parameters if available
                        new_params.extend(current_params[i*3:(i+1)*3])
                    else:
                        # Add default parameters for new Gaussians
                        new_params.extend([
                            plot_data['Scaled Intensity'].max()/n_gaussians,
                            center,
                            x_range/(n_gaussians*4)
                        ])
                st.session_state.fitted_params[data_label] = new_params[:n_gaussians*3]
            
            # Interactive parameter controls
            st.sidebar.header("🎛️ Gaussian Parameters")
            
            # Initialize fixed parameters if not exists
            if 'fixed_params' not in st.session_state:
                st.session_state.fixed_params = {}
            
            if data_label not in st.session_state.fixed_params:
                st.session_state.fixed_params[data_label] = [False] * (n_gaussians * 3)
            
            # Adjust fixed parameters list if number of Gaussians changed
            if len(st.session_state.fixed_params[data_label]) != n_gaussians * 3:
                st.session_state.fixed_params[data_label] = [False] * (n_gaussians * 3)
            
            # Constrained fitting button
            if st.sidebar.button("🔧 Fit with Fixed Parameters"):
                x_data = plot_data['CCS'].values
                y_data = plot_data['Scaled Intensity'].values
                current_params = st.session_state.fitted_params[data_label]
                fixed_flags = st.session_state.fixed_params[data_label]
                
                try:
                    # Create masks for free and fixed parameters
                    free_param_mask = [not fixed for fixed in fixed_flags]
                    free_params = [p for i, p in enumerate(current_params) if free_param_mask[i]]
                    
                    if len(free_params) > 0:  # Only fit if there are free parameters
                        def constrained_multi_gaussian(x, *free_params):
                            # Reconstruct full parameter list
                            full_params = []
                            free_idx = 0
                            
                            for i, is_fixed in enumerate(fixed_flags):
                                if is_fixed:
                                    full_params.append(current_params[i])
                                else:
                                    full_params.append(free_params[free_idx])
                                    free_idx += 1
                            
                            return multi_gaussian(x, *full_params)
                        
                        # Create bounds for free parameters only
                        free_bounds_lower = []
                        free_bounds_upper = []
                        
                        for i, is_fixed in enumerate(fixed_flags):
                            if not is_fixed:
                                param_type = i % 3  # 0=amplitude, 1=center, 2=width
                                if param_type == 0:  # amplitude
                                    free_bounds_lower.append(0)
                                    free_bounds_upper.append(y_data.max() * 2)
                                elif param_type == 1:  # center
                                    free_bounds_lower.append(x_data.min())
                                    free_bounds_upper.append(x_data.max())
                                else:  # width
                                    free_bounds_lower.append(0.1)
                                    free_bounds_upper.append((x_data.max() - x_data.min()))
                        
                        # Fit with constraints
                        popt_free, _ = curve_fit(
                            constrained_multi_gaussian,
                            x_data, y_data,
                            p0=free_params,
                            bounds=(free_bounds_lower, free_bounds_upper),
                            maxfev=10000
                        )
                        
                        # Reconstruct full parameter list
                        fitted_params = []
                        free_idx = 0
                        
                        for i, is_fixed in enumerate(fixed_flags):
                            if is_fixed:
                                fitted_params.append(current_params[i])
                            else:
                                fitted_params.append(popt_free[free_idx])
                                free_idx += 1
                        
                        st.session_state.fitted_params[data_label] = fitted_params
                        st.success("Constrained fitting completed!")
                    else:
                        st.warning("All parameters are fixed - nothing to fit!")
                        
                except Exception as e:
                    st.error(f"Constrained fitting failed: {str(e)}")
            
            params = []
            for i in range(n_gaussians):
                st.sidebar.subheader(f"Gaussian {i+1}")
                
                # Get current parameters
                current_params = st.session_state.fitted_params[data_label]
                fixed_flags = st.session_state.fixed_params[data_label]
                
                # Create columns for parameter and fix checkbox
                col1, col2 = st.sidebar.columns([3, 1])
                
                with col1:
                    amplitude = st.number_input(
                        f"Amplitude {i+1}",
                        min_value=0.0,
                        max_value=plot_data['Scaled Intensity'].max() * 2,
                        value=float(current_params[i*3]),
                        step=plot_data['Scaled Intensity'].max() / 100,
                        format="%.2f",
                        key=f"amp_{i}_{data_label}"
                    )
                
                with col2:
                    fix_amp = st.checkbox(
                        "Fix",
                        value=fixed_flags[i*3],
                        key=f"fix_amp_{i}_{data_label}"
                    )
                    st.session_state.fixed_params[data_label][i*3] = fix_amp
                
                col1, col2 = st.sidebar.columns([3, 1])
                
                with col1:
                    center = st.number_input(
                        f"Center {i+1}",
                        min_value=float(plot_data['CCS'].min()),
                        max_value=float(plot_data['CCS'].max()),
                        value=float(current_params[i*3+1]),
                        step=(plot_data['CCS'].max() - plot_data['CCS'].min()) / 1000,
                        format="%.3f",
                        key=f"center_{i}_{data_label}"
                    )
                
                with col2:
                    fix_center = st.checkbox(
                        "Fix",
                        value=fixed_flags[i*3+1],
                        key=f"fix_center_{i}_{data_label}"
                    )
                    st.session_state.fixed_params[data_label][i*3+1] = fix_center
                
                col1, col2 = st.sidebar.columns([3, 1])
                
                with col1:
                    width = st.number_input(
                        f"Width {i+1}",
                        min_value=0.1,
                        max_value=(plot_data['CCS'].max() - plot_data['CCS'].min()) / 2,
                        value=float(current_params[i*3+2]),
                        step=0.1,
                        format="%.3f",
                        key=f"width_{i}_{data_label}"
                    )
                
                with col2:
                    fix_width = st.checkbox(
                        "Fix",
                        value=fixed_flags[i*3+2],
                        key=f"fix_width_{i}_{data_label}"
                    )
                    st.session_state.fixed_params[data_label][i*3+2] = fix_width
                
                params.extend([amplitude, center, width])
            
            # Update session state
            st.session_state.fitted_params[data_label] = params
            
            # Create plot
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Generate fitted curve
                x_fit = np.linspace(plot_data['CCS'].min(), plot_data['CCS'].max(), 1000)
                y_fit = multi_gaussian(x_fit, *params)
                
                # Individual Gaussians
                individual_gaussians = []
                for i in range(n_gaussians):
                    y_individual = gaussian(x_fit, params[i*3], params[i*3+1], params[i*3+2])
                    individual_gaussians.append(y_individual)
                
                # Create plot
                fig = go.Figure()
                
                # Add original data
                fig.add_trace(go.Scatter(
                    x=plot_data['CCS'],
                    y=plot_data['Scaled Intensity'],
                    mode='markers',
                    name='Data',
                    marker=dict(color='blue', size=6)
                ))
                
                # Add individual Gaussians
                colors = px.colors.qualitative.Set1
                for i, y_individual in enumerate(individual_gaussians):
                    fig.add_trace(go.Scatter(
                        x=x_fit,
                        y=y_individual,
                        mode='lines',
                        name=f'Gaussian {i+1}',
                        line=dict(color=colors[i % len(colors)], dash='dash')
                    ))
                
                # Add fitted curve
                fig.add_trace(go.Scatter(
                    x=x_fit,
                    y=y_fit,
                    mode='lines',
                    name='Total Fit',
                    line=dict(color='red', width=3)
                ))
                
                fig.update_layout(
                    title=f'Gaussian Fitting - {data_label}',
                    xaxis_title='CCS (Å²)',
                    yaxis_title='Scaled Intensity',
                    height=600,
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Fit statistics
                st.subheader("📈 Fit Statistics")
                
                # Calculate R-squared
                y_data_interp = np.interp(x_fit, plot_data['CCS'], plot_data['Scaled Intensity'])
                ss_res = np.sum((y_data_interp - y_fit) ** 2)
                ss_tot = np.sum((y_data_interp - np.mean(y_data_interp)) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                rmse = np.sqrt(np.mean((y_data_interp - y_fit)**2))
                
                st.metric("R²", f"{r_squared:.4f}")
                st.metric("RMSE", f"{rmse:.2f}")
                
                # Save current fit button for individual charge states
                if mode == "Individual Charge State":
                    # Highlight the save button
                    if st.button("💾 Save Current Fit", type="primary"):
                        save_fit_result(selected_charge, params, n_gaussians, r_squared, rmse)
                        st.success(f"✅ Fit saved for Charge {selected_charge}!")
                        st.rerun()  # Refresh to update the sidebar
                
                # Parameter summary
                st.subheader("📋 Parameters")
                param_df = pd.DataFrame({
                    'Gaussian': [i+1 for i in range(n_gaussians)],
                    'Amplitude': [f"{params[i*3]:.2f}" for i in range(n_gaussians)],
                    'Center': [f"{params[i*3+1]:.3f}" for i in range(n_gaussians)],
                    'Width': [f"{params[i*3+2]:.3f}" for i in range(n_gaussians)]
                })
                st.dataframe(param_df, use_container_width=True)
            
            # Export section
            st.header("💾 Export Current Results")
            
            if mode == "Individual Charge State":
                col1, col2 = st.columns(2)
                
                with col1:
                    # Download current fit parameters as CSV
                    param_rows = []
                    for i in range(n_gaussians):
                        param_rows.append({
                            'Charge': selected_charge,
                            'Gaussian': i+1,
                            'Amplitude': params[i*3],
                            'Center': params[i*3+1],
                            'Width': params[i*3+2],
                            'R_squared': r_squared,
                            'RMSE': rmse,
                            'N_Gaussians': n_gaussians
                        })
                    
                    current_df = pd.DataFrame(param_rows)
                    csv_buffer = io.StringIO()
                    current_df.to_csv(csv_buffer, index=False)
                    
                    st.download_button(
                        label="📊 Download Current Parameters (CSV)",
                        data=csv_buffer.getvalue(),
                        file_name=f"gaussian_fit_charge_{selected_charge}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # Download current fit data
                    fit_df = pd.DataFrame({
                        'CCS': x_fit,
                        'Fitted_Intensity': y_fit,
                        'Charge': selected_charge
                    })
                    
                    # Add individual Gaussians
                    for i in range(n_gaussians):
                        fit_df[f'Gaussian_{i+1}'] = individual_gaussians[i]
                    
                    csv_buffer = io.StringIO()
                    fit_df.to_csv(csv_buffer, index=False)
                    
                    st.download_button(
                        label="📈 Download Fit Data (CSV)",
                        data=csv_buffer.getvalue(),
                        file_name=f"fit_data_charge_{selected_charge}.csv",
                        mime="text/csv"
                    )
                
                # Show saved results summary
                if st.session_state.all_fit_results:
                    st.subheader("📊 All Saved Results Summary")
                    summary_data = []
                    for charge, result in st.session_state.all_fit_results.items():
                        summary_data.append({
                            'Charge': charge,
                            'Gaussians': result['n_gaussians'],
                            'R²': f"{result['r_squared']:.4f}",
                            'RMSE': f"{result['rmse']:.2f}"
                        })
                    
                    summary_df = pd.DataFrame(summary_data)
                    st.dataframe(summary_df, use_container_width=True)
            
            else:  # Summed data mode
                col1, col2 = st.columns(2)
                
                with col1:
                    # Download summed fit parameters as CSV
                    param_rows = []
                    for i in range(n_gaussians):
                        param_rows.append({
                            'Mode': 'Summed',
                            'Gaussian': i+1,
                            'Amplitude': params[i*3],
                            'Center': params[i*3+1],
                            'Width': params[i*3+2],
                            'R_squared': r_squared,
                            'RMSE': rmse,
                            'N_Gaussians': n_gaussians
                        })
                    
                    summed_df = pd.DataFrame(param_rows)
                    csv_buffer = io.StringIO()
                    summed_df.to_csv(csv_buffer, index=False)
                    
                    st.download_button(
                        label="📊 Download Parameters (CSV)",
                        data=csv_buffer.getvalue(),
                        file_name="gaussian_fit_summed_data.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # Download summed fit data
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
                        label="📈 Download Fit Data (CSV)",
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
        ### 🎯 Workflow for Individual Charge States:
        1. **Upload your CSV** with columns: Charge, CCS, Scaled Intensity
        2. **Select "Individual Charge State"** mode
        3. **Choose a charge state** from the dropdown
        4. **Fit Gaussians** using auto-fit or manual parameter adjustment
        5. **Save the fit** using the "Save Current Fit" button
        6. **Repeat for other charge states** - switch charge states and repeat steps 4-5
        7. **Export all results** using the "Download All Results" button in the sidebar
        
        ### 📋 Required CSV Format:
        - **Charge**: Charge state values
        - **CCS**: Collision Cross Section values  
        - **Scaled Intensity**: Intensity values
        
        ### ✨ Features:
        - 🔄 **Auto-fit**: Automatically detect peaks and fit Gaussians
        - 🎛️ **Manual Control**: Fine-tune parameters with interactive sliders
        - 🔒 **Fix Parameters**: Lock specific parameters during fitting
        - 💾 **Save & Accumulate**: Save fits for each charge state individually
        - 📊 **Export All**: Download all saved results as a single CSV file
        """)
if __name__ == "__main__":
    main()
