import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from github import Github
from io import StringIO

# === PAGE CONFIGURATION ===
st.set_page_config(
    page_title="CCS Data Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === CUSTOM CSS ===
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    
    .section-header {
        color: #667eea;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
        margin: 2rem 0 1rem 0;
    }
    
    .leaderboard-item {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.3rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# === GITHUB DATA LOADING ===
@st.cache_data(ttl=300, show_spinner="Loading CCS data from GitHub...")
def load_csv_from_github():
    """Load CCS data from GitHub repository"""
    try:
        GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
        REPO_NAME = st.secrets["REPO_NAME"]
        CSV_PATH = st.secrets["CSV_PATH"]
        
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        file_content = repo.get_contents(CSV_PATH)
        csv_string = file_content.decoded_content.decode("utf-8")
        df = pd.read_csv(StringIO(csv_string))
        return df
    except Exception as e:
        st.error(f"❌ Error loading data from GitHub: {e}")
        return None

# === DATA PROCESSING ===
def flatten_ccs_data(df):
    """Flatten nested CCS data for plotting"""
    flat_rows = []
    for _, row in df.iterrows():
        ccs_list = row.get("ccs_data", [])
        if isinstance(ccs_list, str):
            try:
                ccs_list = eval(ccs_list)
            except:
                continue
        
        for charge, ccs in ccs_list:
            flat_row = row.drop(labels=["ccs_data"]).to_dict()
            flat_row["charge"] = charge
            flat_row["ccs"] = ccs
            flat_rows.append(flat_row)
    
    return pd.DataFrame(flat_rows)

# === MAIN PAGE ===
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>CCS Data Explorer</h1>
        <p>Interactive visualization of compiled protein collision cross-section data.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    df = load_csv_from_github()
    
    if df is None or df.empty:
        st.error("❌ No data available. Please check your GitHub configuration.")
        return
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Data Overview", "📈 Interactive Plots", "🏆 Leaderboard", "📊 Statistics"])
    
    with tab1:
        st.markdown('<h2 class="section-header">Raw Dataset</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input("🔍 Search proteins", placeholder="Enter protein name or keyword...")
        with col2:
            show_all = st.checkbox("Show all columns", value=False)
        
        # Filter data based on search
        display_df = df.copy()
        if search_term:
            mask = display_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
            display_df = display_df[mask]
        
        # Display filtered data
        if not show_all:
            # Show only key columns
            key_columns = ["protein_name", "user_name", "timestamp", "ccs_data"]
            available_columns = [col for col in key_columns if col in display_df.columns]
            display_df = display_df[available_columns]
        
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # Download option
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download filtered data as CSV",
            data=csv,
            file_name="ccs_data_filtered.csv",
            mime="text/csv"
        )
    
    with tab2:
        st.markdown('<h2 class="section-header">Interactive CCS Visualization</h2>', unsafe_allow_html=True)
        
        # Flatten the data for plotting
        flat_df = flatten_ccs_data(df)
        
        if flat_df.empty:
            st.warning("⚠️ No CCS data available for plotting.")
            return
        
        # Plot controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            categorical_columns = flat_df.select_dtypes(include=["object", "category"]).columns.tolist()
            filter_column = st.selectbox("🎯 Filter by category", options=["None"] + categorical_columns)
            
            if filter_column != "None":
                filter_options = flat_df[filter_column].dropna().unique().tolist()
                selected_values = st.multiselect(
                    f"Select {filter_column} values",
                    filter_options,
                    default=filter_options[:5] if len(filter_options) > 5 else filter_options
                )
                flat_df = flat_df[flat_df[filter_column].isin(selected_values)]
        
        with col2:
            numeric_columns = flat_df.select_dtypes(include=["float64", "int64"]).columns.tolist()
            x_axis = st.selectbox("📊 X-axis", options=numeric_columns, 
                                index=numeric_columns.index("charge") if "charge" in numeric_columns else 0)
            y_axis = st.selectbox("📊 Y-axis", options=numeric_columns,
                                index=numeric_columns.index("ccs") if "ccs" in numeric_columns else 1)
        
        with col3:
            color_by = st.selectbox("🎨 Color by", options=[None] + categorical_columns)
            plot_type = st.selectbox("📈 Plot type", options=["Scatter", "Box Plot", "Violin Plot"])
        
        # Create plot
        if plot_type == "Scatter":
            fig = px.scatter(
                flat_df, x=x_axis, y=y_axis, color=color_by,
                hover_data=flat_df.columns.tolist(),
                title=f"CCS Analysis: {y_axis} vs {x_axis}",
                template="plotly_white"
            )
        elif plot_type == "Box Plot":
            if color_by:
                fig = px.box(flat_df, x=color_by, y=y_axis, title=f"Distribution of {y_axis} by {color_by}")
            else:
                fig = px.box(flat_df, y=y_axis, title=f"Distribution of {y_axis}")
        else:  # Violin Plot
            if color_by:
                fig = px.violin(flat_df, x=color_by, y=y_axis, title=f"Distribution of {y_axis} by {color_by}")
            else:
                fig = px.violin(flat_df, y=y_axis, title=f"Distribution of {y_axis}")
        
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # Download plot
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📸 Download as PNG",
                data=fig.to_image(format="png"),
                file_name="ccs_analysis.png",
                mime="image/png"
            )
        with col2:
            st.download_button(
                label="📊 Download as HTML",
                data=fig.to_html(),
                file_name="ccs_analysis.html",
                mime="text/html"
            )
    
    with tab3:
        st.markdown('<h2 class="section-header">Research Contributions Leaderboard</h2>', unsafe_allow_html=True)
        
        # Calculate leaderboard data
        user_counts = df["user_name"].value_counts().reset_index()
        user_counts.columns = ["User", "Proteins Logged"]
        
        # Add ranking and medals
        user_counts["Rank"] = range(1, len(user_counts) + 1)
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        user_counts["Medal"] = user_counts["Rank"].map(lambda x: medals.get(x, ""))
        
        # Display top contributors
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Top Contributors")
            for i, row in user_counts.head(10).iterrows():
                medal = row["Medal"]
                user = row["User"]
                count = row["Proteins Logged"]
                
                if medal:
                    st.markdown(f"""
                    <div class="leaderboard-item">
                        <span style="font-weight: bold;">{medal} {user}</span>
                        <span style="color: #667eea; font-weight: bold;">{count} proteins</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.write(f"**{row['Rank']}.** {user} - {count} proteins")
        
        with col2:
            st.markdown("### Quick Stats")
            st.metric("Total Contributors", len(user_counts))
            st.metric("Average per User", f"{user_counts['Proteins Logged'].mean():.1f}")
            st.metric("Top Contributor", f"{user_counts.iloc[0]['Proteins Logged']} proteins")
    
    with tab4:
        st.markdown('<h2 class="section-header">Dataset Statistics</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### User Activity")
            user_activity = df["user_name"].value_counts()
            fig_users = px.bar(
                x=user_activity.values[:10],
                y=user_activity.index[:10],
                orientation='h',
                title="Top 10 Most Active Users",
                labels={'x': 'Proteins Logged', 'y': 'User'}
            )
            fig_users.update_layout(height=400)
            st.plotly_chart(fig_users, use_container_width=True)
        
        with col2:
            if "timestamp" in df.columns:
                st.markdown("### Submission Timeline")
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
                daily_counts = df.groupby(df["timestamp"].dt.date).size()
                
                fig_timeline = px.line(
                    x=daily_counts.index,
                    y=daily_counts.values,
                    title="Daily Submissions",
                    labels={'x': 'Date', 'y': 'Submissions'}
                )
                fig_timeline.update_layout(height=400)
                st.plotly_chart(fig_timeline, use_container_width=True)

if __name__ == "__main__":
    main()

