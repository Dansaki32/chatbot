import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# --- 1. BRANDING & THEME ---
QR_RED = "#AD1212"
BLACK = "#000000"
DARK_GREY = "#0A0A0A"
WHITE = "#FFFFFF"

st.set_page_config(page_title="QR_ Strategy Hub", layout="wide")

# --- 2. AGGRESSIVE CSS OVERRIDES ---
st.markdown(f"""
    <style>
    /* Force Segoe UI everywhere */
    @import url('https://fonts.cdnfonts.com/css/segoe-ui-4');
    * {{ font-family: 'Segoe UI', sans-serif !important; }}
    
    /* Global Background */
    .stApp {{ background-color: {BLACK}; color: {WHITE}; }}

    /* REMOVE ALL STREAMLIT ARTIFACTS */
    [data-testid="stHeader"], [data-testid="stSidebarNav"], footer, header {{ visibility: hidden !important; display: none !important; }}
    .st-emotion-cache-6qob1r {{ display: none !important; }} /* Hides the 'keyboard_double' artifact */

    /* SIDEBAR STYLING */
    section[data-testid="stSidebar"] {{
        background-color: {DARK_GREY} !important;
        border-right: 1px solid #222;
        padding-top: 0px !important;
    }}
    
    /* QR_ LOGO BRANDING */
    .qr-logo {{
        font-size: 2.5rem;
        font-weight: 800;
        color: {WHITE};
        letter-spacing: -2px;
        margin-bottom: 0px;
        padding-top: 20px;
    }}
    .red-u {{ color: {QR_RED} !important; }}

    /* FILE UPLOADER FIX (Force Black) */
    div[data-testid="stFileUploader"] {{
        background-color: {BLACK} !important;
        border: 1px solid #333 !important;
        border-radius: 4px;
    }}
    div[data-testid="stFileUploader"] section {{
        background-color: {BLACK} !important;
        color: {WHITE} !important;
    }}
    /* Hide the 'Drag and drop' text to save space and avoid white text issues */
    div[data-testid="stFileUploaderText"] {{ display: none !important; }}
    /* Style the Browse Button */
    button[data-testid="baseButton-secondary"] {{
        background-color: #111 !important;
        border: 1px solid {QR_RED} !important;
        color: {WHITE} !important;
        text-transform: uppercase;
        font-size: 0.7rem !important;
    }}

    /* CHAT INPUT FIX (Force Black + Red Border) */
    div[data-testid="stChatInput"] {{
        background-color: {BLACK} !important;
        border: 1.5px solid {QR_RED} !important;
        border-radius: 8px !important;
    }}
    div[data-testid="stChatInput"] textarea {{
        background-color: transparent !important;
        color: {WHITE} !important;
    }}

    /* CHAT BUBBLES */
    div[data-testid="stChatMessage"] {{
        background-color: #050505 !important;
        border: 1px solid #111;
        border-left: 3px solid {QR_RED} !important;
        border-radius: 0px 8px 8px 0px;
        margin-bottom: 20px;
    }}

    /* STATUS BADGE */
    .status-badge {{
        border: 1px solid {QR_RED};
        color: {QR_RED} !important;
        padding: 4px 10px;
        font-size: 0.7rem;
        font-weight: 800;
        display: inline-block;
        margin-bottom: 40px;
    }}

    /* BUTTONS */
    .stButton>button {{
        background-color: {QR_RED};
        color: {WHITE} !important;
        border: none;
        font-weight: 700;
        width: 100%;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA LOADING ---
@st.cache_data
def load_structure():
    try:
        return pd.read_csv("table.tsv", sep="\t")
    except:
        return pd.DataFrame()

schema_df = load_structure()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<p class="qr-logo">QR<span class="red-u">_</span></p>', unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:0.7rem; color:#444; letter-spacing:1px; margin-top:-10px;'>STRATEGY HUB</p>", unsafe_allow_html=True)
    
    st.write("---")
    
    st.markdown("<p style='font-weight:700; color:#AD1212; font-size:0.8rem;'>01. DATA ASSETS</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload CSV/TSV", type=["csv", "tsv"], label_visibility="collapsed")
    
    st.write("---")
    
    st.markdown("<p style='font-weight:700; color:#AD1212; font-size:0.8rem;'>02. REPORTING</p>", unsafe_allow_html=True)
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        report_content = f"QR_ STRATEGY REPORT\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for m in st.session_state.messages:
            report_content += f"[{m['role'].upper()}]: {m['content']}\n\n"
        st.download_button(label="EXPORT SESSION (.TXT)", data=report_content, 
                           file_name=f"QR_Report_{datetime.now().strftime('%H%M')}.txt")
    else:
        st.caption("No active session.")

    st.write("")
    if st.button("TERMINATE SESSION"):
        st.session_state.messages = []
        st.rerun()

# --- 5. MAIN INTERFACE ---
st.markdown(f'<h1>QR<span class="red-u">_</span> Strategy Assistant</h1>', unsafe_allow_html=True)
st.markdown('<div class="status-badge">SENIOR STRATEGY DIRECTOR ACTIVE</div>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. AI LOGIC ---
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
        Tone: Senior, Analytical, Action-Oriented.
        Reference Structure: {schema_df.to_string()}
        {client_data}
        """
        response = model.generate_content(f"{system_prompt}\n\nUser: {prompt}")
        full_response = response.text

    except Exception as e:
        full_response = f"⚠️ **System Error:** {str(e)}"

    with st.chat_message("assistant"):
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
