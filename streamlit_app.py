import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# --- 1. BRANDING & THEME CONFIG ---
QR_RED = "#AD1212"
QR_GLOW = "rgba(173, 18, 18, 0.15)"
BLACK = "#000000"
SIDEBAR_BG = "#0A0A0A"
CARD_BG = "#0D0D0D"
WHITE = "#FFFFFF"

st.set_page_config(page_title="QR_ Strategy Hub", layout="wide", initial_sidebar_state="expanded")

# --- 2. THE ULTIMATE POLISH CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.cdnfonts.com/css/segoe-ui-4');
    
    /* Global Reset */
    * {{
        font-family: 'Segoe UI', sans-serif !important;
    }}
    
    .stApp {{
        background-color: {BLACK};
        color: {WHITE};
    }}

    /* Sidebar - Executive Dark */
    section[data-testid="stSidebar"] {{
        background-color: {SIDEBAR_BG} !important;
        border-right: 1px solid #1A1A1A;
        padding-top: 1rem;
    }}
    
    /* QR_ Logo Styling */
    .qr-logo-container {{
        padding: 10px 0px;
        margin-bottom: 20px;
    }}
    .qr-logo-text {{
        font-size: 2.4rem;
        font-weight: 800;
        color: {WHITE};
        letter-spacing: -1.5px;
        margin: 0;
    }}
    .red-u {{ 
        color: {QR_RED} !important;
        text-shadow: 0 0 10px {QR_RED};
    }}

    /* Main Header Hierarchy */
    h1 {{
        font-weight: 800 !important;
        font-size: 2.8rem !important;
        letter-spacing: -1.5px !important;
        margin-bottom: 5px !important;
    }}
    
    /* Status Badge - Refined */
    .status-badge {{
        display: inline-flex;
        align-items: center;
        border: 1px solid {QR_RED};
        background: rgba(173, 18, 18, 0.05);
        color: {QR_RED} !important;
        padding: 4px 12px;
        border-radius: 2px;
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 1px;
        margin-bottom: 40px;
    }}

    /* Chat Input - Bespoke Design */
    div[data-testid="stChatInput"] {{
        border: 1px solid {QR_RED} !important;
        background-color: {BLACK} !important;
        border-radius: 4px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }}
    div[data-testid="stChatInput"] textarea {{
        color: {WHITE} !important;
        background-color: transparent !important;
        font-size: 1rem !important;
    }}

    /* Chat Messages - Premium Card Style */
    div[data-testid="stChatMessage"] {{
        background-color: {CARD_BG} !important;
        border: 1px solid #1A1A1A !important;
        border-left: 2px solid {QR_RED} !important;
        border-radius: 4px;
        padding: 25px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }}
    
    /* Markdown Styling for AI responses */
    .stMarkdown h3 {{
        color: {QR_RED} !important;
        font-size: 1.2rem !important;
        border-bottom: 1px solid #1A1A1A;
        padding-bottom: 5px;
        margin-top: 20px;
    }}
    .stMarkdown strong {{ color: {QR_RED}; }}

    /* File Uploader - Integrated */
    div[data-testid="stFileUploader"] {{
        background-color: #050505 !important;
        border: 1px dashed #333 !important;
        padding: 15px;
    }}
    button[data-testid="baseButton-secondary"] {{
        background-color: transparent !important;
        border: 1px solid {QR_RED} !important;
        color: {WHITE} !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.7rem !important;
    }}
    button[data-testid="baseButton-secondary"]:hover {{
        background-color: {QR_RED} !important;
    }}

    /* Custom Buttons */
    .stButton>button {{
        background-color: {QR_RED};
        color: {WHITE} !important;
        border-radius: 2px;
        border: none;
        font-weight: 700;
        letter-spacing: 0.5px;
        transition: all 0.2s ease;
    }}
    .stButton>button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 12px {QR_GLOW};
    }}

    /* Hide Default UI */
    [data-testid="stHeader"], [data-testid="stSidebarNav"], footer {{display: none !important;}}
    </style>
    """, unsafe_allow_html=True)

# --- 3. CORE LOGIC & DATA ---
@st.cache_data
def load_structure():
    try:
        return pd.read_csv("table.tsv", sep="\t")
    except:
        return pd.DataFrame()

schema_df = load_structure()

# --- 4. SIDEBAR (The Executive Console) ---
with st.sidebar:
    st.markdown(f'<div class="qr-logo-container"><p class="qr-logo-text">QR<span class="red-u">_</span></p></div>', unsafe_allow_html=True)
    
    st.markdown("<p style='font-size:0.7rem; color:#444; font-weight:700; letter-spacing:2px;'>ACCOUNT MANAGEMENT SYSTEM</p>", unsafe_allow_html=True)
    
    st.write("---")
    
    # Data Import
    st.markdown("### 01. DATA ASSETS")
    uploaded_file = st.file_uploader("Upload Client Intelligence", type=["csv", "tsv"], label_visibility="collapsed")
    if uploaded_file:
        st.success("Intelligence Loaded")
    
    st.write("---")
    
    # Export Actions
    st.markdown("### 02. REPORTING")
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        report_content = f"QR_ STRATEGY EXECUTIVE SUMMARY\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n" + "="*40 + "\n\n"
        for m in st.session_state.messages:
            report_content += f"[{m['role'].upper()}]:\n{m['content']}\n\n"
        
        st.download_button(label="EXPORT STRATEGY REPORT", data=report_content, 
                           file_name=f"QR_Strategy_Report_{datetime.now().strftime('%H%M')}.txt")
    else:
        st.caption("Awaiting session data...")

    # Reset
    st.write("")
    if st.button("TERMINATE SESSION"):
        st.session_state.messages = []
        st.rerun()

# --- 5. MAIN INTERFACE ---
st.markdown(f'<h1>QR<span class="red-u">_</span> Strategy Assistant</h1>', unsafe_allow_html=True)
st.markdown('<div class="status-badge">● SENIOR STRATEGY DIRECTOR ACTIVE</div>', unsafe_allow_html=True)

# Initialize/Display Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Container for chat for better spacing on large screens
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- 6. AI STRATEGY ENGINE ---
if prompt := st.chat_input("Enter strategic inquiry..."):
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
        You are the Quick Release (QR_) Senior Account Strategy Director. 
        Tone: Senior, Analytical, Direct, and Action-Oriented.
        Reference Structure: {schema_df.to_string()}
        {client_data}
        
        Formatting: Use Markdown headers (###) for sections. Use bold text for key insights.
        """
        
        response = model.generate_content(f"{system_prompt}\n\nUser: {prompt}")
        full_response = response.text

    except Exception as e:
        full_response = f"⚠️ **System Integrity Error:** {str(e)}"

    with st.chat_message("assistant"):
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
