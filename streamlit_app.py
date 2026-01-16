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

# --- 2. CSS OVERRIDES (THE FINAL POLISH) ---
st.markdown("""
    <style>
    /* 1. GLOBAL RESET */
    @import url('https://fonts.cdnfonts.com/css/segoe-ui-4');
    * { font-family: 'Segoe UI', sans-serif !important; }
    
    /* 2. FORCE DARK BACKGROUNDS */
    .stApp { background-color: #000000 !important; }
    
    /* 3. SIDEBAR BUTTONS (CRITICAL FIXES) */
    
    /* File Uploader Button - Force Red */
    [data-testid="stFileUploader"] button {
        background-color: #AD1212 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 0px !important;
        text-transform: uppercase !important;
        font-weight: 700 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stFileUploader"] button:hover {
        background-color: #FF0000 !important;
        box-shadow: 0 0 10px rgba(173, 18, 18, 0.5) !important;
    }
    
    /* Download Button - Force Black with Red Border */
    [data-testid="stDownloadButton"] button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid #AD1212 !important;
        border-radius: 0px !important;
        text-transform: uppercase !important;
        font-weight: 700 !important;
        width: 100% !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        background-color: #AD1212 !important;
        color: #FFFFFF !important;
    }
    
    /* Terminate Button - Dark Grey */
    div.stButton > button {
        background-color: #111111 !important;
        color: #888888 !important;
        border: 1px solid #333 !important;
        border-radius: 0px !important;
        width: 100%;
        text-transform: uppercase;
    }
    div.stButton > button:hover {
        border-color: #AD1212 !important;
        color: #AD1212 !important;
    }

    /* 4. TEXT VISIBILITY & CONTRAST */
    h1, h2, h3 { color: #FFFFFF !important; }
    p, span, div, label { color: #CCCCCC !important; }
    
    /* Fix Uploader Text Visibility */
    [data-testid="stFileUploader"] div { color: #AAAAAA !important; }
    [data-testid="stFileUploader"] small { color: #888888 !important; }

    /* 5. INPUT BOX & BOTTOM BAR */
    div[data-testid="stChatInput"] {
        background-color: #000000 !important;
        border: 2px solid #AD1212 !important;
        border-radius: 0px !important;
    }
    div[data-testid="stChatInput"] textarea {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        caret-color: #AD1212 !important;
    }
    div[data-testid="stChatInput"] textarea::placeholder {
        color: #AAAAAA !important;
    }
    div[data-testid="stBottom"] { background-color: #000000 !important; border-top: 1px solid #222; }
    div[data-testid="stBottom"] > div { background-color: #000000 !important; }

    /* 6. HIDE JUNK */
    [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
    
    /* 7. CHAT BUBBLES */
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

# --- 6. AI ENGINE (MODEL HUNTER) ---
if prompt := st.chat_input("INITIALIZE STRATEGIC QUERY..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # --- ROBUST MODEL SELECTION ---
        # Tries multiple model names until one works.
        model = None
        # List of models to try in order of preference
        models_to_try = [
            "gemini-1.5-flash",          # Standard
            "gemini-1.5-flash-latest",   # Latest alias
            "gemini-1.5-flash-001",      # Specific version
            "gemini-1.5-flash-002",      # Newer specific version
            "gemini-2.0-flash-exp",      # Experimental 2.0
            "gemini-pro"                 # Fallback
        ]
        
        full_response = "Error: No models available."
        
        # Try generating with each model until success
        for model_name in models_to_try:
            try:
                temp_model = genai.GenerativeModel(model_name)
                
                client_context = ""
                if uploaded_file:
                    df = pd.read_csv(uploaded_file)
                    client_context = f"\n\n[CLIENT DATA]:\n{df.to_string()}"

                system_prompt = f"""
                You are the Quick Release (QR_) Senior Account Strategy Director.
                Reference: {schema_df.to_string()}
                Context: {client_context}
                """
                
                response = temp_model.generate_content(f"{system_prompt}\n\nQUERY: {st.session_state.messages[-1]['content']}")
                full_response = response.text
                break # If successful, stop the loop
            except Exception:
                continue # If failed, try the next model

    except Exception as e:
        full_response = f"**SYSTEM ALERT**: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()
