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

# --- 2. NUCLEAR CSS (Sidebar Fix) ---
st.markdown("""
    <style>
    /* 1. GLOBAL RESET */
    @import url('https://fonts.cdnfonts.com/css/segoe-ui-4');
    * { font-family: 'Segoe UI', sans-serif !important; }
    
    /* 2. FORCE DARK THEME (The Fix for White Sidebar) */
    .stApp { background-color: #000000 !important; }
    
    /* Target EVERY possible sidebar container */
    section[data-testid="stSidebar"], 
    div[data-testid="stSidebar"],
    div[data-testid="stSidebarNav"] {
        background-color: #050505 !important;
        border-right: 1px solid #222 !important;
    }
    
    /* 3. FIX THE UPLOADER BOX (White Box Fix) */
    [data-testid="stFileUploader"] {
        background-color: #111111 !important;
        border: 1px dashed #444 !important;
        padding: 15px !important;
        border-radius: 0px !important;
    }
    [data-testid="stFileUploader"] section {
        background-color: #111111 !important;
    }
    [data-testid="stFileUploader"] div, 
    [data-testid="stFileUploader"] span, 
    [data-testid="stFileUploader"] small {
        color: #AAAAAA !important; /* Force text visible */
    }
    
    /* 4. BUTTONS */
    /* Browse Files - Red */
    [data-testid="stFileUploader"] button {
        background-color: #AD1212 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
    }
    /* Download Log - Black w/ Red Border */
    [data-testid="stDownloadButton"] button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid #AD1212 !important;
    }
    /* Terminate - Grey */
    div.stButton > button {
        background-color: #111111 !important;
        color: #888888 !important;
        border: 1px solid #333 !important;
    }

    /* 5. INPUT BOX */
    div[data-testid="stChatInput"] {
        background-color: #000000 !important;
        border: 2px solid #AD1212 !important;
    }
    div[data-testid="stChatInput"] textarea {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        caret-color: #AD1212 !important;
    }
    
    /* 6. VISIBILITY FIXES */
    h1, h2, h3 { color: #FFFFFF !important; }
    p, span, div, label { color: #CCCCCC !important; }
    
    /* Hide Header/Toolbar Artifacts */
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    
    /* Chat Bubbles */
    div[data-testid="stChatMessage"] {
        background-color: #0E0E0E !important;
        border: 1px solid #222;
        border-left: 3px solid #AD1212 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC ---
@st.cache_data
def load_structure():
    try:
        return pd.read_csv("table.tsv", sep="\t")
    except:
        return pd.DataFrame()

schema_df = load_structure()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <h1 style='font-size: 3rem; margin:0; line-height:1; color:white !important;'>QR<span style='color:#AD1212;'>_</span></h1>
        <p style='font-size: 0.75rem; letter-spacing: 2px; color: #CCCCCC !important; margin-top: 5px;'>STRATEGY OPERATING SYSTEM</p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("<p style='color:#AD1212 !important; font-size:0.75rem; font-weight:bold;'>01 // DATA INGESTION</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Data", type=["csv", "tsv"], label_visibility="collapsed")
    
    if uploaded_file:
        st.markdown("<div style='color:#4CAF50 !important; font-size:0.75rem; margin-top:5px;'>✓ DATASET MOUNTED</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    st.markdown("<p style='color:#AD1212 !important; font-size:0.75rem; font-weight:bold;'>02 // SYSTEM LOGS</p>", unsafe_allow_html=True)
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        report_text = f"QR_ STRATEGY LOG\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for m in st.session_state.messages:
            report_text += f"[{m['role'].upper()}]\n{m['content']}\n\n"
        st.download_button("DOWNLOAD LOG", report_text, file_name="QR_Log.txt")
    else:
        st.markdown("<p style='color:#666666 !important; font-size:0.75rem;'>NO TELEMETRY AVAILABLE</p>", unsafe_allow_html=True)

    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    if st.button("TERMINATE SESSION"):
        st.session_state.messages = []
        st.rerun()

# --- 5. MAIN INTERFACE ---
st.markdown("""
    <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;'>
        <div>
            <h1 style='font-size: 2.8rem; margin:0; color:white !important;'>QR<span style='color:#AD1212;'>_</span> STRATEGY</h1>
        </div>
        <div style='border:1px solid #AD1212; padding:5px 10px; border-radius:4px;'>
            <span style='color: #AD1212 !important; font-size: 0.7rem; font-weight: bold;'>SENIOR DIRECTOR ACTIVE</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Zero State
if len(st.session_state.messages) == 0:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    card_style = "background:#0E0E0E; padding:20px; border:1px solid #222; border-radius:4px;"
    head_style = "color:#AD1212 !important; font-weight:bold; font-size:0.9rem; margin-bottom:5px;"
    text_style = "color:#CCCCCC !important; font-size:0.8rem;"
    
    with c1:
        st.markdown(f"<div style='{card_style}'><div style='{head_style}'>GROWTH</div><div style='{text_style}'>Identify white-space opportunities.</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='{card_style}'><div style='{head_style}'>RISK</div><div style='{text_style}'>Evaluate stakeholder sentiment.</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div style='{card_style}'><div style='{head_style}'>INTEL</div><div style='{text_style}'>Competitor analysis vs QR value.</div></div>", unsafe_allow_html=True)

for message in st.session_state.messages:
    if message["role"] == "user":
        avatar = "👤"
    else:
        avatar = "🔴" 
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# --- 6. AI ENGINE (DIRECT CONNECTION) ---
if prompt := st.chat_input("INITIALIZE STRATEGIC QUERY..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # --- DIRECT CONNECTION (No Loops) ---
        # Using the standard stable model
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
        # Show the ACTUAL error to help debug
        full_response = f"**SYSTEM ERROR**: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()
