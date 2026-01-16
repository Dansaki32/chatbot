import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# --- 1. BRANDING & THEME ---
QR_RED = "#AD1212"
QR_DARK_RED = "#9E0B2E"
BLACK = "#000000"
DARK_GREY = "#141414"
WHITE = "#FFFFFF"

st.set_page_config(page_title="QR Strategy Hub", layout="wide")

# Advanced CSS for a High-End Look
st.markdown(f"""
    <style>
    /* Force Segoe UI everywhere */
    @import url('https://fonts.cdnfonts.com/css/segoe-ui-4');
    * {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }}
    
    .stApp {{
        background-color: {BLACK};
        color: {WHITE};
    }}

    /* Sidebar - Clean & Minimal */
    section[data-testid="stSidebar"] {{
        background-color: {DARK_GREY} !important;
        border-right: 1px solid #333;
        padding-top: 2rem;
    }}
    
    /* Title Styling */
    h1 {{
        font-weight: 800 !important;
        font-size: 2.5rem !important;
        letter-spacing: -1px;
    }}

    /* AI Status Badge */
    .status-badge {{
        background-color: #1a1a1a;
        border: 1px solid {QR_RED};
        color: {QR_RED};
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 20px;
    }}

    /* CLEAN FILE UPLOADER */
    div[data-testid="stFileUploader"] {{
        background-color: #000 !important;
        border: 1px solid #333 !important;
        border-radius: 8px;
        padding: 10px;
    }}
    div[data-testid="stFileUploader"] section {{
        background-color: transparent !important;
    }}
    /* The 'Browse Files' button inside */
    button[data-testid="baseButton-secondary"] {{
        background-color: {QR_RED} !important;
        color: white !important;
        border: none !important;
        font-size: 0.8rem !important;
    }}

    /* CHAT INPUT - Floating Red Accent */
    div[data-testid="stChatInput"] {{
        border: 1px solid #333 !important;
        background-color: #0a0a0a !important;
        border-radius: 15px !important;
        box-shadow: 0px 0px 15px rgba(173, 18, 18, 0.1);
    }}
    
    /* CHAT BUBBLES */
    div[data-testid="stChatMessage"] {{
        background-color: #0a0a0a !important;
        border: 1px solid #1a1a1a;
        border-left: 3px solid {QR_RED} !important;
        margin-bottom: 20px;
        padding: 20px;
    }}

    /* BUTTONS */
    .stButton>button {{
        background-color: {QR_RED};
        color: {WHITE};
        border-radius: 6px;
        font-weight: 600;
        border: none;
    }}
    
    /* DOWNLOAD BUTTON */
    div.stDownloadButton > button {{
        background-color: transparent !important;
        border: 1px solid {QR_RED} !important;
        color: {QR_RED} !important;
        font-size: 0.8rem !important;
    }}
    div.stDownloadButton > button:hover {{
        background-color: {QR_RED} !important;
        color: white !important;
    }}
    
    /* Hide Streamlit elements */
    #MainMenu, footer, header {{visibility: hidden;}}
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

# --- 3. SIDEBAR (The Control Panel) ---
with st.sidebar:
    # Reliable Logo Source (Fallback to Text if image fails)
    logo_url = "https://www.quickrelease.co.uk/hubfs/QR_Logo_Red_RGB.png"
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="{logo_url}" width="150" onerror="this.style.display='none'">
            <h2 style="color:{QR_RED}; font-weight:900; margin-top:10px;">QR STRATEGY</h2>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    
    # Client Data Section
    st.markdown("### 📂 CLIENT DATA")
    uploaded_file = st.file_uploader("Upload CSV/TSV", type=["csv", "tsv"], label_visibility="collapsed")
    
    st.write("---")
    
    # Export Section
    st.markdown("### 📥 REPORTING")
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        report_content = f"QUICK RELEASE STRATEGY REPORT\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for m in st.session_state.messages:
            report_content += f"[{m['role'].upper()}]: {m['content']}\n\n"
        
        st.download_button(label="EXPORT SESSION AS .TXT", data=report_content, 
                           file_name=f"QR_Report_{datetime.now().strftime('%H%M')}.txt")
    else:
        st.caption("No active session to export.")

    # Reset at bottom
    st.write("")
    if st.button("RESET SYSTEM"):
        st.session_state.messages = []
        st.rerun()

# --- 4. MAIN INTERFACE ---
st.markdown(f"<h1><span style='color:{QR_RED};'>QR</span> Account Strategy Assistant</h1>", unsafe_allow_html=True)
st.markdown('<div class="status-badge">● SENIOR STRATEGY DIRECTOR ACTIVE</div>', unsafe_allow_html=True)

# Initialize/Display Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. AI LOGIC (Locked API Key) ---
if prompt := st.chat_input("Ask a strategic question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        client_data = ""
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            client_data = f"\n\nACTUAL CLIENT DATA:\n{df.to_string()}"

        system_prompt = f"""
        You are the Quick Release Senior Account Strategy Director. 
        Tone: Senior, Insightful, Direct. Use business terminology.
        Reference Structure: {schema_df.to_string()}
        {client_data}
        
        Always format responses with bold subheaders and bullet points.
        """

        response = model.generate_content(f"{system_prompt}\n\nUser: {prompt}")
        full_response = response.text

    except Exception as e:
        full_response = f"⚠️ **System Error:** {str(e)}"

    with st.chat_message("assistant"):
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
