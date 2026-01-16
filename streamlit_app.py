import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="QR_ Strategy Hub",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. THE DESIGN ENGINE (CSS) ---
st.markdown("""
    <style>
    /* IMPORT FONT */
    @import url('https://fonts.cdnfonts.com/css/segoe-ui-4');

    /* GLOBAL RESET - FORCE BLACK BACKGROUND EVERYWHERE */
    html, body, [class*="st-"] {
        font-family: 'Segoe UI', sans-serif !important;
        color: #FFFFFF !important;
    }
    .stApp {
        background-color: #000000 !important;
    }

    /* --- KILL THE WHITE BAR AT THE BOTTOM --- */
    /* This targets the sticky footer container that holds the chat input */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stBottom"] {
        background-color: #000000 !important;
        border-top: 1px solid #1A1A1A;
    }
    .stChatFloatingInputContainer {
        background-color: #000000 !important;
    }

    /* --- SIDEBAR ALIGNMENT & DESIGN --- */
    section[data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #AD1212; /* Red border to separate sidebar */
        width: 320px !important;
        padding-top: 2rem !important;
    }
    /* Fix alignment of sidebar elements */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* --- QR_ BRANDING --- */
    .qr-logo {
        font-size: 2.8rem;
        font-weight: 800;
        color: #FFFFFF;
        line-height: 1;
        letter-spacing: -2px;
        margin-bottom: 0px;
    }
    .qr-logo span { color: #AD1212; }
    
    .qr-sub {
        font-size: 0.7rem;
        color: #888;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 40px;
        display: block;
    }

    /* --- FILE UPLOADER (TOTAL FIX) --- */
    div[data-testid="stFileUploader"] {
        background-color: #000000 !important;
        border: 1px solid #333 !important;
        border-radius: 4px;
        padding: 10px;
        margin-bottom: 20px;
    }
    div[data-testid="stFileUploader"] section {
        background-color: #000000 !important;
    }
    /* Hide the 'Drag and drop' text and icon */
    [data-testid="stFileUploader"] .st-emotion-cache-1fttcpj { display: none !important; }
    [data-testid="stFileUploader"] span { display: none !important; }
    [data-testid="stFileUploader"] small { display: none !important; }
    
    /* STYLE THE BROWSE BUTTON */
    button[data-testid="baseButton-secondary"] {
        background-color: #000000 !important;
        border: 1px solid #AD1212 !important;
        color: #FFFFFF !important;
        width: 100%;
        border-radius: 0px !important;
        text-transform: uppercase;
        font-size: 0.75rem !important;
        letter-spacing: 1px;
        padding: 0.5rem 0;
    }
    button[data-testid="baseButton-secondary"]:hover {
        background-color: #AD1212 !important;
        color: #FFFFFF !important;
        border-color: #AD1212 !important;
    }

    /* --- CHAT INPUT (BLACK & RED) --- */
    div[data-testid="stChatInput"] {
        background-color: #000000 !important;
        border: 1px solid #AD1212 !important;
        border-radius: 0px !important; /* Sharp corners */
    }
    div[data-testid="stChatInput"] textarea {
        color: #FFFFFF !important;
        background-color: transparent !important;
    }

    /* --- CHAT MESSAGES --- */
    div[data-testid="stChatMessage"] {
        background-color: #0A0A0A !important;
        border: none;
        border-left: 2px solid #AD1212 !important;
        padding: 1.5rem;
    }

    /* --- BUTTONS (TERMINATE) --- */
    div.stButton > button {
        background-color: #111 !important;
        border: 1px solid #333 !important;
        color: #666 !important;
        border-radius: 0px;
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 1px;
    }
    div.stButton > button:hover {
        border-color: #AD1212 !important;
        color: #AD1212 !important;
    }
    
    /* HIDE STREAMLIT UI CRUFT */
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stHeader"] {display: none !important;}
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
    st.markdown('<div class="qr-logo">QR<span>_</span></div>', unsafe_allow_html=True)
    st.markdown('<span class="qr-sub">STRATEGY OPERATING SYSTEM</span>', unsafe_allow_html=True)
    
    st.markdown("<p style='color:#AD1212; font-weight:bold; font-size:0.8rem; margin-bottom:5px;'>01 // DATA INGESTION</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Client Data", type=["csv", "tsv"], label_visibility="collapsed")
    if uploaded_file:
        st.success("DATA MOUNTED")

    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True) # Spacer

    st.markdown("<p style='color:#AD1212; font-weight:bold; font-size:0.8rem; margin-bottom:5px;'>02 // OUTPUTS</p>", unsafe_allow_html=True)
    
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        report_text = f"QR_ STRATEGY LOG\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for m in st.session_state.messages:
            report_text += f"[{m['role'].upper()}]\n{m['content']}\n\n"
        
        st.download_button(
            label="DOWNLOAD LOG",
            data=report_text,
            file_name=f"QR_Log_{datetime.now().strftime('%H%M')}.txt",
            mime="text/plain"
        )
    else:
        st.markdown("<span style='color:#444; font-size:0.75rem;'>Awaiting Session Data...</span>", unsafe_allow_html=True)

    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True) # Spacer
    
    if st.button("TERMINATE SESSION"):
        st.session_state.messages = []
        st.rerun()

# --- 5. MAIN PAGE ---
st.markdown('# QR<span>_</span> Strategy Assistant', unsafe_allow_html=True)
st.markdown('<div style="color:#AD1212; font-weight:bold; font-size:0.75rem; margin-bottom:40px; letter-spacing:1px;">● SENIOR DIRECTOR PERSONA ONLINE</div>', unsafe_allow_html=True)

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. LOGIC ---
if prompt := st.chat_input("INITIALIZE QUERY..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        client_context = ""
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            client_context = f"\n\n[CLIENT DATA]:\n{df.to_string()}"

        system_prompt = f"""
        You are the Quick Release (QR_) Senior Account Strategy Director.
        Reference: {schema_df.to_string()}
        Context: {client_context}
        """
        
        response = model.generate_content(f"{system_prompt}\n\nQUERY: {prompt}")
        full_response = response.text

    except Exception as e:
        full_response = f"SYSTEM ERROR: {str(e)}"

    with st.chat_message("assistant"):
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
