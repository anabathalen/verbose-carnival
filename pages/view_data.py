import pandas as pd
import streamlit as st
import plotly.express as px
from github import Github
from io import StringIO

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

st.title("📊 View All Protein CCS Data")
st.markdown("This page loads the current dataset and lets you explore and plot CCS information interactively.")

if df is not None and not df.empty:
    st.subheader("🧬 Raw Data Table")
    st.dataframe(df)

    # === Flatten ccs_data ===
    flat_rows = []
    for _, row in df.iterrows():
        ccs_list = row.get("ccs_data", [])
        if isinstance(ccs_list, str):
            try:
                # In case ccs_data is stored as a stringified list of tuples
                ccs_list = eval(ccs_list)
            except:
                continue
        for charge, ccs in ccs_list:
            flat_row = row.drop(labels=["ccs_data"]).to_dict()
            flat_row["charge"] = charge
            flat_row["ccs"] = ccs
            flat_rows.append(flat_row)

    flat_df = pd.DataFrame(flat_rows)

    st.subheader("📈 Customisable CCS Plot")

    # Optional filters by categorical columns
    categorical_columns = flat_df.select_dtypes(include=["object", "category"]).columns.tolist()
    filter_column = st.selectbox("Filter by category", options=["None"] + categorical_columns)
    if filter_column != "None":
        filter_options = flat_df[filter_column].dropna().unique().tolist()
        selected_values = st.multiselect(f"Select {filter_column} values to include", filter_options, default=filter_options)
        flat_df = flat_df[flat_df[filter_column].isin(selected_values)]

    # Axis and color selection
    numeric_columns = flat_df.select_dtypes(include=["float64", "int64"]).columns.tolist()
    all_columns = flat_df.columns.tolist()

    x_axis = st.selectbox("Select X-axis", options=numeric_columns, index=numeric_columns.index("charge") if "charge" in numeric_columns else 0)
    y_axis = st.selectbox("Select Y-axis", options=numeric_columns, index=numeric_columns.index("ccs") if "ccs" in numeric_columns else 1)
    color_by = st.selectbox("Color by (categorical)", options=[None] + categorical_columns)

    # Plot
    fig = px.scatter(
        flat_df,
        x=x_axis,
        y=y_axis,
        color=color_by if color_by else None,
        hover_data=all_columns,
        title=f"{y_axis} vs {x_axis}",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Download PNG
    st.download_button(
        label="📸 Download Plot as PNG",
        data=fig.to_image(format="png"),
        file_name="ccs_plot.png",
        mime="image/png"
    )
else:
    st.warning("No data found in the GitHub CSV.")

