import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(
    page_title="QR_ Strategy OS",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. THE "ULTRA-PROFESSIONAL" CSS ENGINE ---
st.markdown("""
    <style>
    /* 1. CORE TYPOGRAPHY & RESET */
    @import url('https://fonts.cdnfonts.com/css/segoe-ui-4');
    
    * {
        font-family: 'Segoe UI', sans-serif !important;
        box-sizing: border-box;
    }
    
    /* 2. GLOBAL THEME - PURE OLED BLACK */
    .stApp {
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }
    
    /* 3. ARTIFACT REMOVAL (The "keyboard_double" & Header Fix) */
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; } /* Hides 'Manage App' */
    header { visibility: hidden !important; }
    footer { visibility: hidden !important; }
    
    /* 4. SIDEBAR - THE CONTROL PANEL */
    section[data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #1A1A1A;
        width: 320px !important;
    }
    
    /* Force ALL sidebar text to be visible */
    section[data-testid="stSidebar"] * {
        color: #E0E0E0 !important;
    }
    
    /* 5. THE BOTTOM BAR FIX (Removes the white background) */
    [data-testid="stBottom"] {
        background-color: #000000 !important;
        border-top: 1px solid #1A1A1A;
        padding-bottom: 20px;
    }
    .stChatFloatingInputContainer {
        background-color: #000000 !important;
    }

    /* 6. INPUT BOX - COMMAND LINE STYLE */
    div[data-testid="stChatInput"] {
        background-color: #000000 !important;
        border: 1px solid #AD1212 !important;
        border-radius: 0px !important; /* Sharp edges */
        padding: 2px !important;
    }
    div[data-testid="stChatInput"] textarea {
        color: #FFFFFF !important;
        background-color: transparent !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.5px;
    }
    div[data-testid="stChatInput"] ::placeholder {
        color: #666 !important;
        text-transform: uppercase;
        font-size: 0.8rem;
    }

    /* 7. FILE UPLOADER - VISIBLE & CLEAN */
    div[data-testid="stFileUploader"] {
        background-color: #0A0A0A !important;
        border: 1px dashed #333 !important;
        border-radius: 0px;
        padding: 15px;
    }
    div[data-testid="stFileUploader"] section {
        background-color: transparent !important;
    }
    /* The 'Browse files' button */
    button[data-testid="baseButton-secondary"] {
        background-color: transparent !important;
        border: 1px solid #AD1212 !important;
        color: #FFFFFF !important;
        width: 100%;
        border-radius: 0px !important;
        text-transform: uppercase;
        font-weight: 600;
        font-size: 0.7rem !important;
        transition: all 0.2s;
    }
    button[data-testid="baseButton-secondary"]:hover {
        background-color: #AD1212 !important;
        color: white !important;
    }
    /* Hide the drag/drop icon/text to keep it minimal */
    [data-testid="stFileUploader"] .st-emotion-cache-1fttcpj { display: none !important; }
    [data-testid="stFileUploader"] small { display: none !important; }

    /* 8. CHAT BUBBLES - PROFESSIONAL */
    div[data-testid="stChatMessage"] {
        background-color: #080808 !important;
        border: 1px solid #1A1A1A;
        border-left: 3px solid #AD1212 !important;
        border-radius: 0px;
        padding: 20px;
        margin-bottom: 15px;
    }
    
    /* 9. HEADERS & BRANDING */
    .qr-header {
        font-size: 3.5rem;
        font-weight: 800;
        color: #FFFFFF;
        line-height: 1;
        letter-spacing: -2px;
        margin-bottom: 5px;
    }
    .qr-accent { color: #AD1212; }
    
    .sidebar-label {
        font-size: 0.7rem;
        font-weight: 700;
        color: #AD1212 !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 10px;
        display: block;
        margin-top: 20px;
    }

    /* 10. BUTTONS */
    div.stButton > button {
        background-color: #111 !important;
        border: 1px solid #333 !important;
        color: #888 !important;
        border-radius: 0px;
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 1px;
        width: 100%;
    }
    div.stButton > button:hover {
        border-color: #AD1212 !important;
        color: #AD1212 !important;
    }
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

# --- 4. SIDEBAR LAYOUT (PRECISE ALIGNMENT) ---
with st.sidebar:
    # 4.1 Logo
    st.markdown('<div class="qr-header">QR<span class="qr-accent">_</span></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 0.7rem; color: #666; letter-spacing: 2px; margin-bottom: 30px;">STRATEGY OPERATING SYSTEM</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 4.2 Data Module
    st.markdown('<span class="sidebar-label">01 // DATA INGESTION</span>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Client Data", type=["csv", "tsv"], label_visibility="collapsed")
    
    if uploaded_file:
        st.markdown('<div style="color:#4CAF50; font-size:0.7rem; margin-top:5px;">● DATASET MOUNTED</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 4.3 Export Module
    st.markdown('<span class="sidebar-label">02 // SYSTEM LOGS</span>', unsafe_allow_html=True)
    
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        report_text = f"QR_ STRATEGY LOG\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for m in st.session_state.messages:
            report_text += f"[{m['role'].upper()}]\n{m['content']}\n\n"
            
        st.download_button(
            label="DOWNLOAD SESSION LOG",
            data=report_text,
            file_name=f"QR_Log_{datetime.now().strftime('%H%M')}.txt",
            mime="text/plain"
        )
    else:
        st.markdown('<div style="font-size:0.7rem; color:#444;">NO ACTIVE TELEMETRY</div>', unsafe_allow_html=True)

    # 4.4 Footer
    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    if st.button("TERMINATE SESSION"):
        st.session_state.messages = []
        st.rerun()

# --- 5. MAIN INTERFACE ---
# Title
st.markdown('<div class="qr-header" style="font-size: 2.5rem;">QR<span class="qr-accent">_</span> STRATEGY</div>', unsafe_allow_html=True)
st.markdown('<div style="font-size: 0.8rem; color: #AD1212; letter-spacing: 1px; margin-bottom: 40px; font-weight:bold;">● SENIOR DIRECTOR PERSONA ONLINE</div>', unsafe_allow_html=True)

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. AI ENGINE ---
if prompt := st.chat_input("INITIALIZE STRATEGIC QUERY..."):
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
        
        Style Guide:
        - Use Markdown Headers (###)
        - Professional, Executive Tone
        - Bullet points for clarity
        """
        
        response = model.generate_content(f"{system_prompt}\n\nQUERY: {prompt}")
        full_response = response.text

    except Exception as e:
        full_response = f"SYSTEM ERROR: {str(e)}"

    with st.chat_message("assistant"):
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
