import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# --- 1. BRANDING & THEME ---
QR_RED = "#AD1212"
QR_DARK_RED = "#9E0B2E"
BLACK = "#000000"
DARK_GREY = "#111111"
WHITE = "#FFFFFF"

st.set_page_config(page_title="QR Strategy Assistant", layout="wide")

# Custom CSS for a Bespoke Corporate Look
st.markdown(f"""
    <style>
    /* Global Font & Background */
    html, body, [class*="st-"] {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }}
    .stApp {{
        background-color: {BLACK};
        color: {WHITE};
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: {DARK_GREY} !important;
        border-right: 2px solid {QR_RED};
    }}
    
    /* Header Styling */
    h1 {{
        font-weight: 700 !important;
        letter-spacing: -1px;
        margin-bottom: 0px !important;
    }}

    /* FIXING THE FILE UPLOADER (No more white box) */
    div[data-testid="stFileUploader"] {{
        background-color: {DARK_GREY};
        border: 1px dashed {QR_RED};
        border-radius: 8px;
        padding: 5px;
    }}
    div[data-testid="stFileUploader"] section {{
        background-color: {DARK_GREY} !important;
        color: {WHITE} !important;
    }}
    div[data-testid="stFileUploader"] label {{
        color: {WHITE} !important;
        font-size: 0.9rem !important;
    }}
    /* Style the 'Browse Files' button inside the uploader */
    button[data-testid="baseButton-secondary"] {{
        background-color: #222 !important;
        border: 1px solid {QR_RED} !important;
        color: {WHITE} !important;
    }}

    /* Chat Input Styling */
    div[data-testid="stChatInput"] {{
        border: 1px solid {QR_RED} !important;
        background-color: {DARK_GREY} !important;
        border-radius: 12px !important;
    }}
    
    /* Chat Message Bubbles */
    div[data-testid="stChatMessage"] {{
        background-color: #0c0c0c !important;
        border: 1px solid #222;
        border-left: 4px solid {QR_RED} !important;
        border-radius: 10px;
        margin-bottom: 15px;
    }}

    /* Buttons */
    .stButton>button {{
        background-color: {QR_RED};
        color: {WHITE};
        border: none;
        width: 100%;
        transition: 0.3s;
    }}
    .stButton>button:hover {{
        background-color: {QR_DARK_RED};
        border: none;
        color: {WHITE};
    }}
    
    /* Download Button Specifics */
    div.stDownloadButton > button {{
        background-color: transparent !important;
        border: 1px solid {QR_RED} !important;
        color: {WHITE} !important;
    }}
    div.stDownloadButton > button:hover {{
        background-color: {QR_RED} !important;
    }}
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

# --- 3. SIDEBAR LAYOUT ---
with st.sidebar:
    # Logo Area
    st.image("https://www.quickrelease.co.uk/hubfs/QR_Logo_Red_RGB.png", width=150)
    st.markdown(f"<h3 style='margin-top:0; color:{QR_RED};'>STRATEGY HUB</h3>", unsafe_allow_html=True)
    st.write("---")
    
    # Import Section
    st.markdown("📂 **Client Data**")
    uploaded_file = st.file_uploader("Upload CSV/TSV", type=["csv", "tsv"], label_visibility="collapsed")
    
    st.write("---")
    
    # Export Section
    st.markdown("📥 **Export Report**")
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        report_content = f"QUICK RELEASE STRATEGY REPORT\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for m in st.session_state.messages:
            report_content += f"[{m['role'].upper()}]: {m['content']}\n\n"
        
        st.download_button(label="Download Session (.txt)", data=report_content, 
                           file_name=f"QR_Report_{datetime.now().strftime('%H%M')}.txt")
    else:
        st.caption("Chat history will appear here for download.")

    # Reset Button at the bottom
    st.write("")
    if st.button("🗑️ Reset Session"):
        st.session_state.messages = []
        st.rerun()

# --- 4. MAIN CHAT INTERFACE ---
st.markdown(f"<h1><span style='color:{QR_RED};'>QR</span> Account Strategy Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#888; margin-bottom:30px;'>Senior Strategy Director Persona Active</p>", unsafe_allow_html=True)

# Initialize Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. AI LOGIC (Locked API Key) ---
if prompt := st.chat_input("Enter strategic query..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        # Pulls from Streamlit Cloud Secrets
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Context
        client_data = ""
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            client_data = f"\n\nACTUAL CLIENT DATA:\n{df.to_string()}"

        system_prompt = f"""
        You are the Quick Release Senior Account Strategy Director. 
        Tone: Professional, Data-Driven, Strategic.
        Reference Structure: {schema_df.to_string()}
        {client_data}
        
        Provide advice using clear headings and bullet points.
        """

        response = model.generate_content(f"{system_prompt}\n\nUser: {prompt}")
        full_response = response.text

    except Exception as e:
        full_response = f"⚠️ **Configuration Error:** {str(e)}"

    with st.chat_message("assistant"):
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
