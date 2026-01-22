import streamlit as st
import pandas as pd
import google.generativeai as genai
import sqlite3
import time
import plotly.express as px
import os
import pypdf
from datetime import datetime

# --- 1. CONFIG & SYSTEM SETUP ---
st.set_page_config(
    page_title="QR_ ACCOUNTS OS",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. VISUAL CORE (CSS) ---
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=JetBrains+Mono:wght@400&display=swap');
        
        @font-face { font-family: 'Dolce Vita'; src: url('Dolce Vita.ttf') format('truetype'); font-weight: normal; }
        @font-face { font-family: 'Dolce Vita Bold'; src: url('Dolce Vita Heavy Bold.ttf') format('truetype'); font-weight: bold; }

        :root {
            --bg-color: #1a1a1a;
            --sidebar-bg: #000000;
            --accent-red: #D31515;
            --accent-green: #4CAF50;
            --text-white: #FFFFFF;
            --font-display: 'Dolce Vita Bold', 'Roboto', sans-serif;
            --font-body: 'Roboto', sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }

        /* GLOBAL RESETS */
        * { border-radius: 0px !important; }
        .stApp { background-color: var(--bg-color); font-family: var(--font-body); }
        .block-container { padding-top: 2rem !important; padding-bottom: 8rem !important; }
        
        /* HIDE STREAMLIT HEADER STRIP (The White Bar) */
        header[data-testid="stHeader"] {
            display: none !important;
        }
        
        h1, h2, h3 { font-family: var(--font-display) !important; letter-spacing: 2px !important; text-transform: uppercase !important; }
        p, div, span, li { font-family: var(--font-body); color: var(--text-white); }

        /* SIDEBAR LOGO ADJUSTMENT */
        [data-testid="stSidebar"] { background-color: var(--sidebar-bg); border-right: 1px solid #333; }
        section[data-testid="stSidebar"] > div { padding-top: 0rem !important; }
        
        /* ADJUSTED MARGIN: Moves logo slightly down from the extreme top */
        [data-testid="stSidebar"] img { 
            margin-top: -50px !important; 
            margin-bottom: 20px !important; 
        }

        /* FILE UPLOADER */
        [data-testid="stFileUploader"] { background-color: #0A0A0A; border: 1px solid #333; padding: 15px; }
        [data-testid="stFileUploader"] div, [data-testid="stFileUploader"] p, [data-testid="stFileUploader"] small { color: #FFFFFF !important; font-family: var(--font-body) !important; }
        [data-testid="stFileUploader"] button { background-color: var(--accent-red) !important; color: white !important; border: none; font-family: var(--font-display); }

        /* BUTTONS */
        div.stButton > button { 
            background-color: #000000 !important; color: var(--accent-red) !important; 
            border: 1px solid var(--accent-red) !important; font-family: var(--font-display) !important; 
            text-transform: uppercase; width: 100%; transition: all 0.2s ease;
        }
        div.stButton > button:hover { box-shadow: 0 0 15px rgba(211, 21, 21, 0.4); color: white !important; background-color: var(--accent-red) !important; }

        /* METRIC CARDS */
        .metric-card { background: #000000; border: 1px solid #333; padding: 20px; height: 100%; margin-bottom: 20px; }
        .metric-label { font-family: var(--font-body); font-size: 0.75rem; color: #888; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px; }
        .metric-value { font-family: var(--font-display); font-size: 1.5rem; color: white; letter-spacing: 1px; }

        /* CHAT INPUT */
        div[data-testid="stChatInput"] { background-color: var(--bg-color) !important; padding-bottom: 1.5rem !important; }
        div[data-testid="stChatInput"] textarea { background-color: #0A0A0A !important; color: white !important; border: 1px solid #333 !important; }
        div[data-testid="stChatInput"] textarea:focus { border-color: var(--accent-red) !important; box-shadow: 0 0 10px rgba(211, 21, 21, 0.2) !important; }

        /* TABS */
        button[data-baseweb="tab"] { font-family: var(--font-display) !important; letter-spacing: 1px; }
        
        .active-session-text { color: var(--accent-red); font-family: var(--font-mono); font-size: 0.8rem; letter-spacing: 1px; animation: pulse-red 2s infinite; }
        @keyframes pulse-red { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BACKEND LOGIC (PERSISTENT KNOWLEDGE BASE) ---

STORAGE_DIR = "knowledge_base"

def init_storage():
    """Ensures the local storage folder exists."""
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)

def save_uploaded_file(uploaded_file):
    """Saves a file permanently to the disk."""
    try:
        file_path = os.path.join(STORAGE_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    except Exception as e:
        return None

class KnowledgeEngine:
    """Reads ALL files in the knowledge_base folder to build a mega-context."""
    
    def get_all_context(self):
        context = ""
        files = [f for f in os.listdir(STORAGE_DIR) if os.path.isfile(os.path.join(STORAGE_DIR, f))]
        
        if not files:
            return "NO KNOWLEDGE BASE FILES FOUND. PLEASE UPLOAD DATA."
        
        context += f"/// SYSTEM KNOWLEDGE BASE ({len(files)} FILES LOADED) ///\n\n"
        
        for filename in files:
            file_path = os.path.join(STORAGE_DIR, filename)
            context += f"=== SOURCE FILE: {filename} ===\n"
            
            try:
                # PROCESS PDF
                if filename.endswith(".pdf"):
                    reader = pypdf.PdfReader(file_path)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    context += f"{text[:10000]} ... [TRUNCATED IF TOO LONG]\n\n"
                
                # PROCESS CSV/TSV
                elif filename.endswith(".csv") or filename.endswith(".tsv"):
                    sep = '\t' if filename.endswith('.tsv') else ','
                    df = pd.read_csv(file_path, sep=sep)
                    context += df.to_string(index=False) + "\n\n"
                    
            except Exception as e:
                context += f"[ERROR READING FILE: {str(e)}]\n\n"
                
        return context

class AIEngine:
    def __init__(self):
        try:
            self.api_key = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.active = True
        except: self.active = False

    def stream_response(self, user_query, db_context):
        if not self.active: yield "SYSTEM ERROR: API KEY MISSING."; return
        
        system_prompt = f"""
        ROLE: You are QR_ ACCOUNTS OS, an elite Strategy Operating System.
        TASK: Answer queries based STRICTLY on the knowledge base provided below.
        
        [KNOWLEDGE BASE]
        {db_context}
        """
        
        try:
            response = self.model.generate_content(f"{system_prompt}\n\nUSER QUERY: {user_query}", stream=True)
            for chunk in response: yield chunk.text
        except Exception as e: yield f"API ERROR: {str(e)}"

    def generate_one_pager(self, db_context):
        if not self.active: return "SYSTEM ERROR: API KEY MISSING."
        
        prompt = f"""
        ROLE: Senior Strategy Director.
        TASK: Create a consolidated "Executive 1-Pager" based on ALL the data provided below.
        
        FORMAT:
        1. **Executive Summary** (3-4 sentences high level)
        2. **Key Account Risks** (Bullet points)
        3. **Strategic Opportunities** (Bullet points)
        4. **Financial Health / Metrics** (If available in data)
        5. **Next 90 Days** (Action plan)
        
        [DATA SOURCE]
        {db_context}
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e: return f"GENERATION ERROR: {str(e)}"

# --- 4. FRONTEND COMPONENTS ---

def render_sidebar(knowledge_engine):
    with st.sidebar:
        # LOGO
        script_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [os.path.join(script_dir, "logo.png"), "logo.png"]
        logo_path = next((p for p in possible_paths if os.path.exists(p)), None)
        if logo_path: st.image(logo_path, use_container_width=True)
        else: st.markdown("<h1 style='color:white;'>QR_</h1>", unsafe_allow_html=True)
            
        st.markdown("""
            <div style='font-family: "Dolce Vita Bold", sans-serif; color:white; font-size:0.8rem; margin-top:20px;'>ACCOUNTS OS v5.1</div>
            <div style='border-top: 1px solid #333; margin-bottom: 20px;'></div>
        """, unsafe_allow_html=True)

        # UPLOAD
        st.markdown("<div style='color:white; font-family:var(--font-display); font-size:0.8rem; margin-bottom:5px;'>INGEST KNOWLEDGE</div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload", type=['csv', 'tsv', 'pdf'], label_visibility="collapsed")
        
        if uploaded_file:
            save_path = save_uploaded_file(uploaded_file)
            if save_path:
                st.toast(f"SAVED TO CORE: {uploaded_file.name}", icon="💾")
                time.sleep(1) # Give it a sec
                st.rerun() # Refresh so the new file is read into context

        # FILE LIST
        st.markdown("<br><div style='color:white; font-family:var(--font-display); font-size:0.8rem; margin-bottom:5px;'>ACTIVE DATASETS</div>", unsafe_allow_html=True)
        files = os.listdir(STORAGE_DIR)
        if files:
            for f in files:
                st.markdown(f"<div style='color:#888; font-size:0.8rem; border-left:2px solid #D31515; padding-left:10px; margin-bottom:5px;'>{f}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#444; font-size:0.8rem;'>Memory Empty</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("WIPE MEMORY"):
            for f in files:
                os.remove(os.path.join(STORAGE_DIR, f))
            st.rerun()

def render_metrics():
    # Count files
    file_count = len(os.listdir(STORAGE_DIR))
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">System Status</div><div class="metric-value" style="color:#4CAF50;">ONLINE</div><div class="metric-desc">Neural Engine Active</div></div>""", unsafe_allow_html=True)
    with c2:
        color = "#4CAF50" if file_count > 0 else "#D31515"
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Knowledge Base</div><div class="metric-value" style="color:{color};">{file_count} FILES</div><div class="metric-desc">Vectors Loaded</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Personality</div><div class="metric-value" style="color:#4CAF50;">DIRECTOR</div><div class="metric-desc">Strategic Mode</div></div>""", unsafe_allow_html=True)

# --- 5. MAIN EXECUTION ---

def main():
    init_storage()
    inject_custom_css()
    
    knowledge_engine = KnowledgeEngine()
    ai_engine = AIEngine()
    
    if "messages" not in st.session_state: st.session_state.messages = []

    render_sidebar(knowledge_engine)

    # TABS
    tab1, tab2, tab3 = st.tabs(["// ACCOUNTS_CHAT", "// EXEC_1_PAGER", "// DATA_RECON"])

    # --- TAB 1: CHAT ---
    with tab1:
        st.markdown(f"<div style='margin-bottom:20px;'><span class='active-session-text'>// ACTIVE SESSION: {datetime.now().strftime('%H:%M')}</span></div>", unsafe_allow_html=True)
        render_metrics()
        
        # Display Messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🔴"):
                st.markdown(message["content"])

        if prompt := st.chat_input("QUERY THE KNOWLEDGE BASE..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"): st.markdown(prompt)

            with st.chat_message("assistant", avatar="🔴"):
                response_placeholder = st.empty()
                full_response = ""
                # Get fresh context from disk
                context = knowledge_engine.get_all_context()
                
                try:
                    for chunk in ai_engine.stream_response(prompt, context):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                        time.sleep(0.01)
                    response_placeholder.markdown(full_response)
                except Exception as e:
                    response_placeholder.markdown(f"**ERROR:** {str(e)}")
            st.session_state.messages.append({"role": "assistant", "content": full_response})

    # --- TAB 2: EXEC 1 PAGER ---
    with tab2:
        st.markdown("### // EXECUTIVE ONE-PAGER GENERATOR")
        st.markdown("Generates a consolidated strategic view based on **all** currently uploaded files.")
        
        if st.button("GENERATE 1-PAGER"):
            with st.spinner("SYNTHESIZING KNOWLEDGE BASE..."):
                context = knowledge_engine.get_all_context()
                summary = ai_engine.generate_one_pager(context)
                st.markdown("---")
                st.markdown(summary)
        else:
            st.info("Click generate to fuse all uploaded data into a single strategic document.")

    # --- TAB 3: DATA RECON ---
    with tab3:
        st.markdown("### // RAW DATA INSPECTION")
        files = os.listdir(STORAGE_DIR)
        if files:
            selected_file = st.selectbox("SELECT FILE TO INSPECT", files)
            file_path = os.path.join(STORAGE_DIR, selected_file)
            
            if selected_file.endswith(".csv") or selected_file.endswith(".tsv"):
                sep = '\t' if selected_file.endswith('.tsv') else ','
                df = pd.read_csv(file_path, sep=sep)
                st.dataframe(df, use_container_width=True)
            elif selected_file.endswith(".pdf"):
                st.warning("PDF PREVIEW NOT SUPPORTED. TEXT CONTENT IS INDEXED IN BACKEND.")
        else:
            st.info("NO DATA LOADED.")

if __name__ == "__main__":
    main()