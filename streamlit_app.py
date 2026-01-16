import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# --- 1. BRANDING & THEME (Segoe UI / Black / Red) ---
QR_RED = "#AD1212"
QR_DARK_RED = "#9E0B2E"
BLACK = "#000000"
WHITE = "#FFFFFF"

st.set_page_config(page_title="QR Strategy Assistant", layout="wide")

# Custom CSS for the requested look
st.markdown(f"""
    <style>
    /* Main App Background and Font */
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI&display=swap');
    
    .stApp {{
        background-color: {BLACK};
        color: {WHITE};
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: #111111;
        border-right: 1px solid {QR_RED};
        color: {WHITE};
    }}

    /* Headers */
    h1, h2, h3, p, span, label {{
        color: {WHITE} !important;
        font-family: 'Segoe UI' !important;
    }}

    /* Input Box */
    .stChatFloatingInputContainer {{
        background-color: {BLACK};
    }}
    
    div[data-testid="stChatInput"] {{
        border: 1px solid {QR_RED} !important;
        border-radius: 10px;
    }}

    /* Buttons */
    .stButton>button {{
        background-color: {QR_RED};
        color: {WHITE};
        border-radius: 4px;
        border: none;
        width: 100%;
        font-weight: bold;
    }}
    .stButton>button:hover {{
        background-color: {QR_DARK_RED};
        color: {WHITE};
    }}

    /* File Uploader Design */
    div[data-testid="stFileUploader"] {{
        background-color: #1a1a1a;
        padding: 10px;
        border-radius: 5px;
        border: 1px dashed {QR_RED};
    }}

    /* Chat Bubbles */
    div[data-testid="stChatMessage"] {{
        background-color: #1a1a1a;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 3px solid {QR_RED};
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADING ---
@st.cache_data
def load_structure():
    try:
        return pd.read_csv("table.tsv", sep="\t")
    except:
        return pd.DataFrame()

schema_df = load_structure()

# --- 3. SIDEBAR (Locked Configuration) ---
with st.sidebar:
    st.image("https://www.quickrelease.co.uk/hubfs/QR_Logo_Red_RGB.png", width=180)
    st.markdown(f"<h2 style='color:{QR_RED};'>STRATEGY HUB</h2>", unsafe_allow_html=True)
    st.write("---")
    
    # Import Section
    st.subheader("📁 Client Data")
    uploaded_file = st.file_uploader("Upload CSV/TSV", type=["csv", "tsv"], label_visibility="collapsed")
    
    st.write("---")
    
    # Export Section (Better Design)
    st.subheader("📥 Export Report")
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        # Prepare text for export
        report_content = f"QUICK RELEASE STRATEGY REPORT\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n" + "="*30 + "\n\n"
        for m in st.session_state.messages:
            report_content += f"[{m['role'].upper()}]:\n{m['content']}\n\n"
        
        st.download_button(
            label="Download Session (.txt)",
            data=report_content,
            file_name=f"QR_Report_{datetime.now().strftime('%H%M')}.txt",
            mime="text/plain"
        )
    else:
        st.info("Start a chat to generate a report.")

    if st.button("🗑️ Reset Session"):
        st.session_state.messages = []
        st.rerun()

# --- 4. MAIN INTERFACE ---
st.markdown(f"<h1><span style='color:{QR_RED};'>QR</span> Account Strategy Assistant</h1>", unsafe_allow_html=True)

# Initialize Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. LOGIC (Using Hidden Secret) ---
if prompt := st.chat_input("Enter strategic query..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get API Key from Secrets
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # Hardcoded to the most stable model for speed
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Context Setup
        client_data = ""
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            client_data = f"\n\nACTUAL CLIENT DATA:\n{df.to_string()}"

        system_prompt = f"""
        You are the Quick Release Senior Account Strategy Director. 
        Tone: Professional, Insightful, Action-Oriented.
        Structure Reference: {schema_df.to_string()}
        {client_data}
        
        Use Segoe UI style formatting (clear headings, bullet points).
        """

        response = model.generate_content(f"{system_prompt}\n\nUser: {prompt}")
        full_response = response.text

    except KeyError:
        full_response = "⚠️ **Error:** API Key not found in Streamlit Secrets. Please add 'GEMINI_API_KEY' to your app settings."
    except Exception as e:
        full_response = f"⚠️ **Error:** {str(e)}"

    with st.chat_message("assistant"):
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
