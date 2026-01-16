import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="QR_ Strategy OS",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ADVANCED CSS ENGINE ---
st.markdown("""
    <style>
    /* GLOBAL RESET */
    @import url('https://fonts.cdnfonts.com/css/segoe-ui-4');
    * { font-family: 'Segoe UI', sans-serif !important; }
    
    /* THEME COLORS */
    :root {
        --qr-red: #AD1212;
        --bg-black: #000000;
        --bg-panel: #0A0A0A;
        --text-white: #FFFFFF;
        --text-grey: #888888;
    }

    /* BACKGROUNDS */
    .stApp { background-color: var(--bg-black) !important; }
    
    /* ANIMATIONS */
    @keyframes pulse {
        0% { opacity: 1; box-shadow: 0 0 0 0 rgba(173, 18, 18, 0.7); }
        70% { opacity: 1; box-shadow: 0 0 0 6px rgba(173, 18, 18, 0); }
        100% { opacity: 1; box-shadow: 0 0 0 0 rgba(173, 18, 18, 0); }
    }
    .live-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: var(--qr-red);
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }

    /* SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-panel) !important;
        border-right: 1px solid #1A1A1A;
        width: 320px !important;
    }
    
    /* FILE UPLOADER - REDESIGNED */
    div[data-testid="stFileUploader"] {
        background-color: #000000 !important;
        border: 1px solid #333 !important;
        padding: 15px;
        border-radius: 0px;
    }
    div[data-testid="stFileUploader"] section { background-color: #000000 !important; }
    div[data-testid="stFileUploader"] .st-emotion-cache-1fttcpj { display: none !important; } /* Hide Drag/Drop Icon */
    
    /* BROWSE BUTTON */
    button[data-testid="baseButton-secondary"] {
        background-color: transparent !important;
        border: 1px solid var(--qr-red) !important;
        color: var(--qr-red) !important;
        width: 100%;
        border-radius: 0px !important;
        text-transform: uppercase;
        font-weight: 700;
        font-size: 0.75rem !important;
        transition: all 0.3s ease;
    }
    button[data-testid="baseButton-secondary"]:hover {
        background-color: var(--qr-red) !important;
        color: white !important;
    }

    /* INPUT BOX - COMMAND CENTER STYLE */
    div[data-testid="stChatInput"] {
        background-color: #000000 !important;
        border: 1px solid var(--qr-red) !important;
        border-radius: 0px !important;
        padding: 5px !important;
    }
    div[data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: white !important;
        font-size: 0.9rem !important;
    }
    
    /* BOTTOM BAR FIX (CRITICAL) */
    div[data-testid="stBottom"] { background-color: #000000 !important; border-top: 1px solid #1A1A1A; }
    
    /* CHAT BUBBLES */
    div[data-testid="stChatMessage"] {
        background-color: var(--bg-panel) !important;
        border: 1px solid #1A1A1A;
        border-left: 3px solid var(--qr-red) !important;
        padding: 20px;
    }

    /* WELCOME CARDS */
    .welcome-card {
        background-color: #0A0A0A;
        border: 1px solid #222;
        padding: 20px;
        border-radius: 4px;
        height: 100%;
    }
    .welcome-header { color: var(--qr-red); font-weight: bold; font-size: 0.9rem; margin-bottom: 10px; }
    .welcome-text { color: #888; font-size: 0.8rem; }

    /* UTILS */
    .footer-disclaimer {
        text-align: center;
        color: #333;
        font-size: 0.6rem;
        margin-top: 50px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* HIDE JUNK */
    [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC & DATA ---
@st.cache_data
def load_structure():
    try:
        return pd.read_csv("table.tsv", sep="\t")
    except:
        return pd.DataFrame()

schema_df = load_structure()

# --- 4. SIDEBAR ---
with st.sidebar:
    # BRANDING
    st.markdown("""
        <div style='margin-bottom: 30px;'>
            <h1 style='font-size: 3rem; margin:0; line-height:1; color:white;'>QR<span style='color:#AD1212;'>_</span></h1>
            <p style='font-size: 0.7rem; letter-spacing: 2px; color: #666; margin-top: 5px;'>STRATEGY OPERATING SYSTEM</p>
        </div>
    """, unsafe_allow_html=True)
    
    # DATA SECTION
    st.markdown("<p style='color:#AD1212; font-size:0.7rem; font-weight:bold; margin-bottom:5px;'>01 // DATA INGESTION</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Data", type=["csv", "tsv"], label_visibility="collapsed")
    if uploaded_file:
        st.markdown("<div style='background:#111; color:#4CAF50; padding:8px; font-size:0.7rem; border-left:2px solid #4CAF50; margin-top:10px;'>✓ DATASET MOUNTED</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

    # EXPORT SECTION
    st.markdown("<p style='color:#AD1212; font-size:0.7rem; font-weight:bold; margin-bottom:5px;'>02 // SYSTEM LOGS</p>", unsafe_allow_html=True)
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        report_text = f"QR_ STRATEGY LOG\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for m in st.session_state.messages:
            report_text += f"[{m['role'].upper()}]\n{m['content']}\n\n"
        st.download_button("DOWNLOAD LOG", report_text, file_name="QR_Log.txt")
    else:
        st.markdown("<p style='color:#444; font-size:0.7rem;'>NO TELEMETRY AVAILABLE</p>", unsafe_allow_html=True)

    # FOOTER
    st.markdown("<div style='height:50px'></div>", unsafe_allow_html=True)
    if st.button("TERMINATE SESSION"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("<div class='footer-disclaimer'>CONFIDENTIAL<br>INTERNAL USE ONLY</div>", unsafe_allow_html=True)

# --- 5. MAIN INTERFACE ---

# HEADER WITH PULSING STATUS
st.markdown("""
    <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;'>
        <div>
            <h1 style='font-size: 2.2rem; margin:0;'>QR<span style='color:#AD1212;'>_</span> STRATEGY</h1>
        </div>
        <div style='display: flex; align-items: center; background: #0A0A0A; padding: 8px 15px; border: 1px solid #222; border-radius: 4px;'>
            <span class='live-indicator'></span>
            <span style='color: #AD1212; font-size: 0.7rem; font-weight: bold; letter-spacing: 1px;'>SENIOR DIRECTOR ACTIVE</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# CHAT HISTORY
if "messages" not in st.session_state:
    st.session_state.messages = []

# ZERO STATE DASHBOARD (Only shows if no messages)
if len(st.session_state.messages) == 0:
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; margin-bottom: 20px;'>SUGGESTED STRATEGIC VECTORS:</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="welcome-card">
            <div class="welcome-header">ACCOUNT GROWTH</div>
            <div class="welcome-text">Analyze current penetration and identify white-space opportunities.</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="welcome-card">
            <div class="welcome-header">RISK ASSESSMENT</div>
            <div class="welcome-text">Evaluate stakeholder sentiment and project delivery risks.</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="welcome-card">
            <div class="welcome-header">COMPETITOR INTEL</div>
            <div class="welcome-text">Compare QR value proposition against known market threats.</div>
        </div>
        """, unsafe_allow_html=True)

# DISPLAY MESSAGES
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. AI ENGINE ---
if prompt := st.chat_input("INITIALIZE STRATEGIC QUERY..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun() # Rerun immediately to clear the zero-state dashboard

# Process Response (After Rerun)
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
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
        
        response = model.generate_content(f"{system_prompt}\n\nQUERY: {st.session_state.messages[-1]['content']}")
        full_response = response.text

    except Exception as e:
        full_response = f"SYSTEM ERROR: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()
