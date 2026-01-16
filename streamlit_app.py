import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# --- 1. BRANDING & THEME ---
QR_RED = "#AD1212"
BLACK = "#000000"
DARK_GREY = "#111111"
WHITE = "#FFFFFF"

st.set_page_config(page_title="QR_ Strategy Hub", layout="wide")

# Advanced Responsive CSS
st.markdown(f"""
    <style>
    /* Import Segoe UI */
    @import url('https://fonts.cdnfonts.com/css/segoe-ui-4');
    
    /* Global Styles */
    html, body, [class*="st-"] {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        color: {WHITE} !important;
    }}
    
    .stApp {{
        background-color: {BLACK};
    }}

    /* Responsive Container */
    [data-testid="block-container"] {{
        padding-top: 2rem;
        max-width: 1200px; /* Limits width on huge monitors for readability */
        margin: auto;
    }}

    /* Sidebar - Responsive Width */
    section[data-testid="stSidebar"] {{
        background-color: {DARK_GREY} !important;
        border-right: 1px solid #222;
        min-width: 250px !important;
        max-width: 350px !important;
    }}

    /* QR_ Branding Style */
    .qr-logo {{
        font-size: 2.2rem;
        font-weight: 800;
        color: {WHITE};
        letter-spacing: -1px;
        margin-bottom: 0px;
    }}
    .red-underscore {{
        color: {QR_RED} !important;
    }}

    /* AI Status Badge */
    .status-badge {{
        background-color: transparent;
        border: 1px solid {QR_RED};
        color: {QR_RED} !important;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 30px;
        text-transform: uppercase;
    }}

    /* Clean File Uploader (No Artifacts) */
    div[data-testid="stFileUploader"] {{
        background-color: #000 !important;
        border: 1px solid #333 !important;
        border-radius: 4px;
    }}
    div[data-testid="stFileUploader"] section {{
        padding: 0px !important;
    }}
    /* Hide the "drag and drop" text to keep it clean on small screens */
    div[data-testid="stFileUploaderText"] {{
        display: none;
    }}

    /* Chat Input - Responsive & Centered */
    div[data-testid="stChatInput"] {{
        border: 1px solid #333 !important;
        background-color: #080808 !important;
        border-radius: 8px !important;
        margin-bottom: 20px;
    }}
    
    /* Chat Bubbles */
    div[data-testid="stChatMessage"] {{
        background-color: #080808 !important;
        border: 1px solid #1a1a1a;
        border-left: 2px solid {QR_RED} !important;
        border-radius: 0px 8px 8px 0px;
        margin-bottom: 15px;
    }}

    /* Standardized Buttons */
    .stButton>button {{
        background-color: {QR_RED};
        color: {WHITE} !important;
        border-radius: 2px;
        border: none;
        width: 100%;
        font-size: 0.8rem;
        font-weight: bold;
        height: 40px;
    }}
    
    /* Download Button Styling */
    div.stDownloadButton > button {{
        background-color: transparent !important;
        border: 1px solid {QR_RED} !important;
        color: {WHITE} !important;
        height: 40px;
    }}

    /* Hide Streamlit fluff */
    #MainMenu, footer, header, [data-testid="stHeader"] {{visibility: hidden;}}
    img {{ display: none !important; }} /* Force hide any broken image artifacts */
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADING ---
@st.cache_data
def load_structure():
    try:
        return pd.read_csv("table.tsv", sep="\t")
    except:
        return pd.DataFrame()

schema_df = load_structure()

# --- 3. SIDEBAR (The Control Panel) ---
with st.sidebar:
    # Text-based Logo (Replaces broken image)
    st.markdown(f'<p class="qr-logo">QR<span class="red-underscore">_</span></p>', unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:0.8rem; color:#666; margin-bottom:20px;'>STRATEGY HUB</p>", unsafe_allow_html=True)
    
    st.write("---")
    
    # Client Data Section
    st.markdown("### 📂 DATA IMPORT")
    uploaded_file = st.file_uploader("Upload CSV/TSV", type=["csv", "tsv"], label_visibility="collapsed")
    
    st.write("---")
    
    # Export Section
    st.markdown("### 📥 EXPORT")
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        report_content = f"QR_ STRATEGY REPORT\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for m in st.session_state.messages:
            report_content += f"[{m['role'].upper()}]: {m['content']}\n\n"
        
        st.download_button(label="DOWNLOAD SESSION (.TXT)", data=report_content, 
                           file_name=f"QR_Report_{datetime.now().strftime('%H%M')}.txt")
    else:
        st.caption("No active session to export.")

    # Reset at bottom
    st.write("")
    if st.button("RESET SYSTEM"):
        st.session_state.messages = []
        st.rerun()

# --- 4. MAIN INTERFACE ---
st.markdown(f'<h1><span style="color:white;">QR</span><span class="red-underscore">_</span> Account Strategy Assistant</h1>', unsafe_allow_html=True)
st.markdown('<div class="status-badge">SENIOR STRATEGY DIRECTOR ACTIVE</div>', unsafe_allow_html=True)

# Initialize/Display Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. AI LOGIC (Locked API Key) ---
if prompt := st.chat_input("Enter strategic query..."):
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
        
        Use clear headings and bullet points for all strategic advice.
        """

        response = model.generate_content(f"{system_prompt}\n\nUser: {prompt}")
        full_response = response.text

    except Exception as e:
        full_response = f"⚠️ **System Error:** {str(e)}"

    with st.chat_message("assistant"):
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
