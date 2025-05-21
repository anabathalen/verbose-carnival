import streamlit as st
import pandas as pd
from github import Github
from io import StringIO
import plotly.express as px

st.title("📊 View All Protein CCS Data")

# --- Load GitHub secrets ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
CSV_PATH = st.secrets["CSV_PATH"]

# --- Authenticate with GitHub ---
@st.cache_data(ttl=300)
def load_csv_from_github():
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        file_content = repo.get_contents(CSV_PATH)
        csv_string = file_content.decoded_content.decode("utf-8")
        df = pd.read_csv(StringIO(csv_string))
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# --- Load and display the data ---
df = load_csv_from_github()

if df is not None:
    st.success("Data loaded successfully!")
    st.dataframe(df, use_container_width=True)
    # Optional download button
    csv = df.to_csv(index=False)
    st.download_button("📥 Download as CSV", csv, "protein_ccs_data.csv", "text/csv")
    
    st.markdown("---")
    st.header("📈 Customisable Data Plot")
    
    if df is not None and not df.empty:
        numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        all_columns = df.columns.tolist()
    
        x_axis = st.selectbox("Select X-axis", options=numeric_columns, index=0)
        y_axis = st.selectbox("Select Y-axis", options=numeric_columns, index=1 if len(numeric_columns) > 1 else 0)
        color_by = st.selectbox("Color by (categorical)", options=[None] + all_columns, index=0)
    
        if x_axis and y_axis:
            fig = px.scatter(
                df,
                x=x_axis,
                y=y_axis,
                color=color_by if color_by else None,
                hover_data=all_columns,
                title=f"{y_axis} vs {x_axis}",
            )
            st.plotly_chart(fig, use_container_width=True)
    
            # Optional: download plot as image
            st.download_button(
                label="📸 Download Plot as PNG",
                data=fig.to_image(format="png"),
                file_name="protein_ccs_plot.png",
                mime="image/png"
            )

else:
    st.warning("No data found or failed to load.")
