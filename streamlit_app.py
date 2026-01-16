import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import time

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="QR_ Strategy OS",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS THEME LOCK (Black & Red) ---
st.markdown("""
    <style>
    /* GLOBAL RESET */
    @import url('https://fonts.cdnfonts.com/css/segoe-ui-4');
    * { font-family: 'Segoe UI', sans-serif !important; }
    
    /* FORCE DARK THEME */
    html, body, .stApp {
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }
    
    /* SIDEBAR FIX */
    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #222 !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background-color: #050505 !important;
    }
    
    /* FILE UPLOADER */
    [data-testid="stFileUploader"] {
        background-color: #111111 !important;
        border: 1px dashed #444 !important;
        padding: 15px !important;
        border-radius: 0px !important;
    }
    [data-testid="stFileUploader"] div, 
    [data-testid="stFileUploader"] span, 
    [data-testid="stFileUploader"] small {
        color: #AAAAAA !important;
    }
    
    /* BUTTONS */
    [data-testid="stFileUploader"] button {
        background-color: #AD1212 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
    }
    [data-testid="stDownloadButton"] button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid #AD1212 !important;
        width: 100%;
    }
    div.stButton > button {
        background-color: #111111 !important;
        color: #888888 !important;
        border: 1px solid #333 !important;
        width: 100%;
    }

    /* CHAT INPUT */
    div[data-testid="stChatInput"] {
        background-color: #000000 !important;
        border: 2px solid #AD1212 !important;
    }
    div[data-testid="stChatInput"] textarea {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        caret-color: #AD1212 !important;
    }
    div[data-testid="stChatInput"] textarea::placeholder {
        color: #666 !important;
    }
    
    /* UI CLEANUP */
    h1, h2, h3 { color: #FFFFFF !important; }
    p, span, div, label { color: #CCCCCC !important; }
    [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
    
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

# --- 6. AI ENGINE (GEMINI 2.5 FLASH w/ RETRY) ---
if prompt := st.chat_input("INITIALIZE STRATEGIC QUERY..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # TARGETING GEMINI 2.5 FLASH
        model = genai.GenerativeModel('gemini-2.5-flash')

        client_context = ""
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            client_context = f"\n\n[CLIENT DATA]:\n{df.to_string()}"

        system_prompt = f"""
        You are the Quick Release (QR_) Senior Account Strategy Director.
        Reference: {schema_df.to_string()}
        Context: {client_context}
        """
        
        # RETRY LOOP FOR 429 ERRORS
        max_retries = 3
        full_response = ""
        
        for attempt in range(max_retries):
            try:
                response = model.generate_content(f"{system_prompt}\n\nQUERY: {st.session_state.messages[-1]['content']}")
                full_response = response.text
                break # Success! Exit loop.
            except Exception as e:
                error_str = str(e)
                if "429" in error_str and attempt < max_retries - 1:
                    # If quota exceeded, wait and retry
                    time.sleep(2) # Wait 2 seconds
                    continue
                else:
                    # If it's not 429, or we ran out of retries, show error
                    full_response = f"**SYSTEM ALERT**: {error_str}"
                    break

    except Exception as e:
        full_response = f"**CRITICAL FAILURE**: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()
