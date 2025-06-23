import streamlit as st

# === PAGE CONFIGURATION ===
st.set_page_config(
    page_title="Calibrate DTIMS Data Acquired on Synapt",
    page_icon="📌",
    layout="wide",
    initial_sidebar_state="expanded")

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
</style>
""", unsafe_allow_html=True)

def main():

  st.markdown("""
    <div class="main-header">
        <h1>Calibrate DTIMS Data Acquired on Synapt</h1>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
