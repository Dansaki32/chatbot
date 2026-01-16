import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="QR_ Strategy Hub",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={} # Hides the hamburger menu help items
)

# --- 2. THE "NUCLEAR" CSS OVERRIDE ---
# This CSS targets specific Streamlit internal classes to force the design.
st.markdown("""
    <style>
    /* 1. GLOBAL FONTS & RESET */
    @import url('https://fonts.cdnfonts.com/css/segoe-ui-4');
    
    html, body, [class*="st-"] {
        font-family: 'Segoe UI', sans-serif !important;
        color: #FFFFFF !important;
    }
    
    /* 2. BACKGROUNDS - PURE BLACK OLED THEME */
    .stApp {
        background-color: #000000 !important;
    }
    
    /* 3. SIDEBAR - DARK & SHARP */
    section[data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #1A1A1A;
        width: 300px !important;
    }
    
    /* 4. QR_ BRANDING LOGO */
    .qr-brand {
        font-size: 3rem;
        font-weight: 900;
        letter-spacing: -2px;
        color: #FFFFFF;
        line-height: 1;
        margin-bottom: 5px;
    }
    .qr-brand span {
        color: #AD1212;
    }
    .qr-subtitle {
        font-size: 0.75rem;
        color: #666;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 40px;
    }

    /* 5. INPUT BOX - THE FIX (NO MORE WHITE BAR) */
    div[data-testid="stChatInput"] {
        background-color: #000000 !important;
        border: 1px solid #AD1212 !important;
        border-radius: 8px !important;
        padding: 5px !important;
        margin-bottom: 20px;
    }
    div[data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #FFFFFF !important;
        caret-color: #AD1212;
    }
    /* Hide the default container background that causes the white strip */
    .stChatFloatingInputContainer {
        background-color: #000000 !important;
    }

    /* 6. FILE UPLOADER - THE FIX (NO MORE WHITE BUTTON) */
    div[data-testid="stFileUploader"] {
        background-color: #0A0A0A !important;
        border: 1px dashed #333 !important;
        border-radius: 6px;
        padding: 15px;
    }
    div[data-testid="stFileUploader"] section {
        background-color: transparent !important;
    }
    /* Target the 'Browse files' button specifically */
    button[data-testid="baseButton-secondary"] {
        background-color: transparent !important;
        border: 1px solid #AD1212 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 4px !important;
        transition: all 0.3s ease;
    }
    button[data-testid="baseButton-secondary"]:hover {
        background-color: #AD1212 !important;
        border-color: #AD1212 !important;
    }
    /* Hide the 'Drag and drop' text */
    .st-emotion-cache-1fttcpj { display: none; } 

    /* 7. CHAT BUBBLES - CARDS */
    div[data-testid="stChatMessage"] {
        background-color: #0A0A0A !important;
        border: 1px solid #1A1A1A;
        border-left: 3px solid #AD1212 !important;
        border-radius: 4px;
        padding: 20px;
        margin-bottom: 15px;
    }
    div[data-testid="stChatMessage"] p {
        font-size: 1rem;
        line-height: 1.6;
    }

    /* 8. BUTTONS (TERMINATE / RESET) */
    div.stButton > button {
        background-color: #111 !important;
        color: #AD1212 !important;
        border: 1px solid #333 !important;
        border-radius: 4px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.8rem;
        padding: 10px 0;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        border-color: #AD1212 !important;
        color: #FFFFFF !important;
        background-color: #AD1212 !important;
    }

    /* 9. HEADERS & TEXT */
    h1 { font-weight: 800 !important; letter-spacing: -1px; }
    h3 { color: #AD1212 !important; font-size: 1.1rem !important; margin-top: 20px !important; }
    
    /* 10. HIDE JUNK */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {display: none !important;} /* Hides Manage App */
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

# --- 4. SIDEBAR LAYOUT ---
with st.sidebar:
    # 4.1 Custom Logo Section
    st.markdown('<div class="qr-brand">QR<span>_</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="qr-subtitle">STRATEGY OPERATING SYSTEM</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 4.2 Data Section
    st.markdown("**DATA INGESTION**")
    uploaded_file = st.file_uploader("Client Data", type=["csv", "tsv"], label_visibility="collapsed")
    if uploaded_file:
        st.success("✓ Data Mounted")
    
    st.markdown("---")
    
    # 4.3 Export Section
    st.markdown("**OUTPUTS**")
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        # Generate clean text for export
        report_text = f"QR_ STRATEGY LOG\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for m in st.session_state.messages:
            report_text += f"[{m['role'].upper()}]\n{m['content']}\n\n"
            
        st.download_button(
            label="DOWNLOAD LOG (.TXT)",
            data=report_text,
            file_name=f"QR_Log_{datetime.now().strftime('%H%M')}.txt",
            mime="text/plain"
        )
    else:
        st.markdown("<span style='color:#444; font-size:0.8rem;'>No active session data.</span>", unsafe_allow_html=True)

    # 4.4 Footer Controls
    st.markdown("---")
    if st.button("TERMINATE SESSION"):
        st.session_state.messages = []
        st.rerun()

# --- 5. MAIN PAGE LAYOUT ---
# 5.1 Header
st.markdown('# QR<span>_</span> Strategy Assistant', unsafe_allow_html=True)
st.markdown('<div style="color:#AD1212; font-weight:bold; font-size:0.8rem; margin-bottom:30px;">● SENIOR DIRECTOR PERSONA ACTIVE</div>', unsafe_allow_html=True)

# 5.2 Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. INTELLIGENCE ENGINE ---
if prompt := st.chat_input("Input strategic query..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        # Secure API Key Retrieval
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Context Building
        client_context = ""
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            client_context = f"\n\n[ATTACHED CLIENT DATASET]:\n{df.to_string()}"

        # The "Brain"
        system_prompt = f"""
        You are the Quick Release (QR_) Senior Account Strategy Director.
        
        MANDATE:
        Provide high-level, actionable strategic advice based on the provided framework.
        
        FRAMEWORK:
        {schema_df.to_string()}
        
        CONTEXT:
        {client_context}
        
        FORMATTING RULES:
        1. Use Markdown headers (###) for structure.
        2. Use Bullet points for readability.
        3. Tone: Professional, Concise, Executive.
        """
        
        response = model.generate_content(f"{system_prompt}\n\nQUERY: {prompt}")
        full_response = response.text

    except Exception as e:
        full_response = f"**SYSTEM ALERT**: {str(e)}"

    with st.chat_message("assistant"):
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
