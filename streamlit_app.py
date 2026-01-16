import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# --- 1. BRANDING & COLORS ---
QR_RED_MAIN = "#AD1212"
QR_RED_DARK = "#9E0B2E"
QR_RED_LIGHT = "#D63030"
QR_WHITE = "#FFFFFF"

st.set_page_config(page_title="QR Account Strategy Bot", layout="wide")

# Custom CSS for Branding
st.markdown(f"""
    <style>
    .stApp {{ background-color: {QR_WHITE}; }}
    .stButton>button {{
        background-color: {QR_RED_MAIN};
        color: white;
        border-radius: 5px;
        border: none;
    }}
    .stButton>button:hover {{
        background-color: {QR_RED_LIGHT};
        border: none;
        color: white;
    }}
    h1, h2, h3 {{ color: {QR_RED_DARK}; }}
    .stChatFloatingInputContainer {{ background-color: {QR_WHITE}; }}
    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background-color: #f8f9fa;
        border-right: 2px solid {QR_RED_MAIN};
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

st.title("🔴 Quick Release Account Strategy Assistant")
st.subheader("Strategic Planning & Client Insights")

# --- 3. SIDEBAR CONFIG ---
with st.sidebar:
    st.image("https://www.quickrelease.co.uk/hubfs/QR_Logo_Red_RGB.png", width=200) # Placeholder for logo
    st.header("Configuration")
    google_api_key = st.text_input("Enter Gemini API Key", type="password")
    
    available_models = []
    if google_api_key:
        try:
            genai.configure(api_key=google_api_key)
            models = genai.list_models()
            available_models = [m.name.replace('models/', '') for m in models if 'generateContent' in m.supported_generation_methods]
        except: pass

    model_choice = st.selectbox("Select Model", available_models) if available_models else None
    
    st.write("---")
    uploaded_file = st.file_uploader("Upload Client Data (CSV/TSV)", type=["csv", "tsv"])
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 4. CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. STRATEGY LOGIC & CHAT ---
if prompt := st.chat_input("Ask a strategic question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if google_api_key and model_choice:
        try:
            client_data_context = ""
            if uploaded_file:
                df = pd.read_csv(uploaded_file)
                client_data_context = f"\n\nACTUAL CLIENT DATA:\n{df.to_string()}"

            # STEP 3: IMPROVED STRATEGY PERSONA
            system_instruction = f"""
            You are the Quick Release Senior Account Strategy Director. 
            Your goal is to help Account Managers build world-class account plans.
            
            STRUCTURE GUIDELINE:
            {schema_df.to_string()}
            
            {client_data_context}
            
            STRATEGIC RULES:
            1. Always provide actionable advice. Don't just explain 'what' to do, explain 'how' to win.
            2. If a client has 'Weak' relationship status, suggest specific stakeholder engagement tactics.
            3. If the user asks for a plan, use the Structure Guideline to ensure all required QR sections are covered.
            4. Use a professional, high-energy, and insightful tone.
            """
            
            model = genai.GenerativeModel(model_choice)
            response = model.generate_content(f"{system_instruction}\n\nUser: {prompt}")
            full_response = response.text
            
        except Exception as e:
            full_response = f"⚠️ Error: {str(e)}"
    else:
        full_response = "Please ensure your API Key is entered and a model is selected."

    with st.chat_message("assistant"):
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# --- 6. STEP 4: EXPORT FUNCTIONALITY ---
if st.session_state.messages:
    st.write("---")
    # Prepare the chat history for export
    report_text = f"QUICK RELEASE STRATEGY REPORT\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    for m in st.session_state.messages:
        report_text += f"{m['role'].upper()}: {m['content']}\n\n"
    
    st.download_button(
        label="📥 Download Strategy Report (.txt)",
        data=report_text,
        file_name=f"QR_Strategy_Report_{datetime.now().strftime('%d_%m_%Y')}.txt",
        mime="text/plain"
    )
