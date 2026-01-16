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

# --- 2. NUCLEAR CSS OVERRIDES ---
st.markdown("""
    <style>
    /* 1. GLOBAL RESET & FONT */
    @import url('https://fonts.cdnfonts.com/css/segoe-ui-4');
    * { font-family: 'Segoe UI', sans-serif !important; }
    
    /* 2. FORCE DARK BACKGROUNDS (The Fix) */
    .stApp { background-color: #000000 !important; }
    
    /* 3. FIX THE BOTTOM WHITE BAR */
    div[data-testid="stBottom"] {
        background-color: #000000 !important;
        border-top: 1px solid #1A1A1A;
    }
    /* This targets the internal container of the bottom bar */
    div[data-testid="stBottom"] > div {
        background-color: #000000 !important;
    }

    /* 4. FIX THE CHAT INPUT (The Invisible Text Fix) */
    div[data-testid="stChatInput"] {
        background-color: #000000 !important;
        border: 2px solid #AD1212 !important;
        border-radius: 4px !important;
    }
    
    /* TARGET THE ACTUAL TYPING AREA */
    div[data-testid="stChatInput"] textarea {
        background-color: #000000 !important; /* Force Black Background */
        color: #FFFFFF !important; /* Force White Text */
        caret-color: #AD1212 !important; /* Red Cursor */
    }
    
    /* TARGET THE PLACEHOLDER TEXT */
    div[data-testid="stChatInput"] textarea::placeholder {
        color: #888888 !important;
    }

    /* 5. SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        background-color: #0A0A0A !important;
        border-right: 1px solid #222;
        width: 320px !important;
    }
    
    /* 6. FILE UPLOADER & BUTTONS (Fixing the White Buttons) */
    div[data-testid="stFileUploader"] {
        background-color: #111 !important;
        border: 1px dashed #444 !important;
        padding: 15px;
        border-radius: 0px;
    }
    div[data-testid="stFileUploader"] section { background-color: #111 !important; }
    
    /* BROWSE BUTTON - Force Red Outline */
    button[data-testid="baseButton-secondary"] {
        background-color: transparent !important;
        border: 1px solid #AD1212 !important;
        color: #AD1212 !important;
        font-weight: bold !important;
        transition: all 0.3s;
    }
    button[data-testid="baseButton-secondary"]:hover {
        background-color: #AD1212 !important;
        color: #FFFFFF !important;
    }
    
    /* TERMINATE BUTTON */
    div.stButton > button {
        background-color: #111 !important;
        color: #FFFFFF !important;
        border: 1px solid #333 !important;
    }

    /* 7. TEXT VISIBILITY FIXES */
    h1, h2, h3, p, span, div { color: #FFFFFF; } /* Default to white text */
    .stMarkdown p { color: #E0E0E0 !important; }
    
    /* 8. HIDE STREAMLIT UI */
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    div[data-testid="stFileUploader"] .st-emotion-cache-1fttcpj { display: none !important; }

    /* 9. CHAT BUBBLES */
    div[data-testid="stChatMessage"] {
        background-color: #0E0E0E !important;
        border: 1px solid #222;
        border-left: 3px solid #AD1212 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA & LOGIC ---
@st.cache_data
def load_structure():
    try:
        return pd.read_csv("table.tsv", sep="\t")
    except:
        return pd.DataFrame()

schema_df = load_structure()

# --- 4. SIDEBAR ---
with st.sidebar:
    # Header
    st.markdown("""
        <h1 style='font-size: 3rem; margin:0; line-height:1; color:white !important;'>QR<span style='color:#AD1212;'>_</span></h1>
        <p style='font-size: 0.7rem; letter-spacing: 2px; color: #888 !important; margin-top: 5px;'>STRATEGY OPERATING SYSTEM</p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Data
    st.markdown("<p style='color:#AD1212 !important; font-size:0.7rem; font-weight:bold;'>01 // DATA INGESTION</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Data", type=["csv", "tsv"], label_visibility="collapsed")
    if uploaded_file:
        st.success("DATASET MOUNTED")
    
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Export
    st.markdown("<p style='color:#AD1212 !important; font-size:0.7rem; font-weight:bold;'>02 // SYSTEM LOGS</p>", unsafe_allow_html=True)
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        report_text = f"QR_ STRATEGY LOG\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for m in st.session_state.messages:
            report_text += f"[{m['role'].upper()}]\n{m['content']}\n\n"
        st.download_button("DOWNLOAD LOG", report_text, file_name="QR_Log.txt")
    else:
        st.markdown("<p style='color:#444 !important; font-size:0.7rem;'>NO TELEMETRY AVAILABLE</p>", unsafe_allow_html=True)

    # Footer
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    if st.button("TERMINATE SESSION"):
        st.session_state.messages = []
        st.rerun()

# --- 5. MAIN INTERFACE ---
# Title Area
st.markdown("""
    <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;'>
        <div>
            <h1 style='font-size: 2.5rem; margin:0; color:white !important;'>QR<span style='color:#AD1212;'>_</span> STRATEGY</h1>
        </div>
        <div style='border:1px solid #AD1212; padding:5px 10px; border-radius:4px;'>
            <span style='color: #AD1212 !important; font-size: 0.7rem; font-weight: bold;'>SENIOR DIRECTOR ACTIVE</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Welcome Cards (Zero State)
if len(st.session_state.messages) == 0:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    card_style = "background:#0E0E0E; padding:20px; border:1px solid #222; border-radius:4px;"
    head_style = "color:#AD1212 !important; font-weight:bold; font-size:0.9rem; margin-bottom:5px;"
    text_style = "color:#888 !important; font-size:0.8rem;"
    
    with c1:
        st.markdown(f"<div style='{card_style}'><div style='{head_style}'>GROWTH</div><div style='{text_style}'>Identify white-space opportunities.</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='{card_style}'><div style='{head_style}'>RISK</div><div style='{text_style}'>Evaluate stakeholder sentiment.</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div style='{card_style}'><div style='{head_style}'>INTEL</div><div style='{text_style}'>Competitor analysis vs QR value.</div></div>", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. AI ENGINE ---
if prompt := st.chat_input("INITIALIZE STRATEGIC QUERY..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

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
