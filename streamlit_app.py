import streamlit as st
import pandas as pd
import google.generativeai as genai
import sqlite3
import time
import plotly.express as px
import os
import pypdf
import json
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
        header[data-testid="stHeader"] { display: none !important; }
        
        h1, h2, h3 { font-family: var(--font-display) !important; letter-spacing: 2px !important; text-transform: uppercase !important; }
        p, div, span, li { font-family: var(--font-body); color: var(--text-white); }

        /* SIDEBAR */
        [data-testid="stSidebar"] { background-color: var(--sidebar-bg); border-right: 1px solid #333; }
        section[data-testid="stSidebar"] > div { padding-top: 0rem !important; }
        [data-testid="stSidebar"] img { margin-top: -50px !important; margin-bottom: 20px !important; }

        /* FILE UPLOADER */
        [data-testid="stFileUploader"] { background-color: #0A0A0A; border: 1px solid #333; padding: 15px; }
        [data-testid="stFileUploader"] div, [data-testid="stFileUploader"] p, [data-testid="stFileUploader"] small { color: #FFFFFF !important; font-family: var(--font-body) !important; }
        [data-testid="stFileUploader"] button { background-color: var(--accent-red) !important; color: white !important; border: none; font-family: var(--font-display); }

        /* --- MICRO BUTTONS FOR SIDEBAR FILES --- */
        /* Target the small columns in sidebar specifically */
        [data-testid="stSidebar"] div[data-testid="column"] button {
            font-size: 0.6rem !important;
            padding: 0px 5px !important;
            min-height: 20px !important;
            height: 24px !important;
            line-height: 1 !important;
            margin-top: 0px !important;
            width: 100%;
        }

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

# --- 3. BACKEND LOGIC ---

STORAGE_DIR = "knowledge_base"
METADATA_FILE = os.path.join(STORAGE_DIR, "metadata.json")

def init_storage():
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)
    if not os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'w') as f: json.dump({}, f)

def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f: return json.load(f)
    return {}

def save_metadata(data):
    with open(METADATA_FILE, 'w') as f: json.dump(data, f)

def save_uploaded_file(uploaded_file):
    try:
        file_path = os.path.join(STORAGE_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        meta = load_metadata()
        meta[uploaded_file.name] = True # Default to Active
        save_metadata(meta)
        return file_path
    except Exception as e: return None

def delete_file(filename):
    try:
        os.remove(os.path.join(STORAGE_DIR, filename))
        meta = load_metadata()
        if filename in meta:
            del meta[filename]
            save_metadata(meta)
        return True
    except: return False

def set_file_status(filename, status):
    meta = load_metadata()
    meta[filename] = status
    save_metadata(meta)

class KnowledgeEngine:
    def get_all_context(self):
        context = ""
        meta = load_metadata()
        if not os.path.exists(STORAGE_DIR): return "NO DATA."
        files = [f for f in os.listdir(STORAGE_DIR) if os.path.isfile(os.path.join(STORAGE_DIR, f)) and f != "metadata.json"]
        
        # Filter Active
        active_files = [f for f in files if meta.get(f, True)]
        
        if not active_files: return "NO ACTIVE DATA. PLEASE UPLOAD OR ACTIVATE FILES."
        
        context += f"/// SYSTEM KNOWLEDGE BASE ({len(active_files)} ACTIVE FILES) ///\n\n"
        for filename in active_files:
            file_path = os.path.join(STORAGE_DIR, filename)
            context += f"=== SOURCE FILE: {filename} ===\n"
            try:
                if filename.endswith(".pdf"):
                    reader = pypdf.PdfReader(file_path)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    context += f"{text[:15000]} ... [TRUNCATED]\n\n"
                elif filename.endswith(".csv") or filename.endswith(".tsv"):
                    sep = '\t' if filename.endswith('.tsv') else ','
                    df = pd.read_csv(file_path, sep=sep)
                    context += df.to_string(index=False) + "\n\n"
            except Exception as e: context += f"[ERROR READING FILE: {str(e)}]\n\n"
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
        TASK: Answer based STRICTLY on the knowledge base.
        [KNOWLEDGE BASE]
        {db_context}
        """
        try:
            response = self.model.generate_content(f"{system_prompt}\n\nUSER QUERY: {user_query}", stream=True)
            for chunk in response: yield chunk.text
        except Exception as e: 
            if "429" in str(e): yield "⚠️ SYSTEM OVERLOAD (429): API Rate limit exceeded. Please wait a moment."
            else: yield f"API ERROR: {str(e)}"

    def generate_one_pager(self, db_context):
        if not self.active: return "SYSTEM ERROR: API KEY MISSING."
        prompt = f"""
        ROLE: Strategy Director.
        TASK: Consolidated Executive 1-Pager based on ALL data below.
        FORMAT: 1. Summary, 2. Risks, 3. Opportunities, 4. Metrics, 5. Action Plan.
        [DATA]
        {db_context}
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e): return "⚠️ SYSTEM OVERLOAD (429): API Rate limit exceeded. Please wait a moment."
            return f"GENERATION ERROR: {str(e)}"

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
            <div style='font-family: "Dolce Vita Bold", sans-serif; color:white; font-size:0.8rem; margin-top:20px;'>ACCOUNTS OS v5.6</div>
            <div style='border-top: 1px solid #333; margin-bottom: 20px;'></div>
        """, unsafe_allow_html=True)

        # UPLOAD
        st.markdown("<div style='color:white; font-family:var(--font-display); font-size:0.8rem; margin-bottom:5px;'>INGEST KNOWLEDGE</div>", unsafe_allow_html=True)
        if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
        uploaded_file = st.file_uploader("Upload", type=['csv', 'tsv', 'pdf'], label_visibility="collapsed", key=f"uploader_{st.session_state.uploader_key}")
        
        if uploaded_file:
            save_path = save_uploaded_file(uploaded_file)
            if save_path:
                st.toast(f"SAVED: {uploaded_file.name}", icon="💾")
                st.session_state.uploader_key += 1
                time.sleep(1)
                st.rerun()

        # ACTIVE DATASETS LIST
        st.markdown("<br><div style='color:white; font-family:var(--font-display); font-size:0.8rem; margin-bottom:10px;'>ACTIVE DATASETS</div>", unsafe_allow_html=True)
        
        files = [f for f in os.listdir(STORAGE_DIR) if os.path.isfile(os.path.join(STORAGE_DIR, f)) and f != "metadata.json"]
        meta = load_metadata()
        
        if files:
            for f in files:
                is_active = meta.get(f, True)
                
                # VISUAL FEEDBACK ON FILENAME
                name_color = "#4CAF50" if is_active else "#666"
                status_icon = "🟢" if is_active else "⚫"
                st.markdown(f"""
                <div style="font-size:0.75rem; color:{name_color}; margin-bottom:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                    {status_icon} {f}
                </div>
                """, unsafe_allow_html=True)
                
                # CONTROL BUTTONS
                # We use 'primary' type for the active state to make it filled/bright
                c1, c2, c3 = st.columns([1, 1, 1.2])
                
                with c1:
                    # ON Button (Red if active, grey if not)
                    if st.button("ON", key=f"on_{f}", type="primary" if is_active else "secondary"):
                        set_file_status(f, True)
                        st.rerun()
                with c2:
                    # OFF Button (Red if inactive, grey if active)
                    if st.button("OFF", key=f"off_{f}", type="primary" if not is_active else "secondary"):
                        set_file_status(f, False)
                        st.rerun()
                with c3:
                    # REMOVE Button (Always secondary/grey until hovered)
                    if st.button("REMOVE", key=f"del_{f}", type="secondary"):
                        delete_file(f)
                        st.rerun()
                
                st.markdown("<div style='margin-bottom:10px; border-bottom:1px solid #222;'></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#444; font-size:0.8rem; font-style:italic;'>Memory Empty</div>", unsafe_allow_html=True)

        # WIPE MEMORY
        st.markdown("<br><br>", unsafe_allow_html=True)
        if "wipe_confirm" not in st.session_state: st.session_state.wipe_confirm = False
        
        if not st.session_state.wipe_confirm:
            # WIDE button for WIPE
            if st.button("WIPE MEMORY"):
                st.session_state.wipe_confirm = True
                st.rerun()
        else:
            st.markdown("<div style='color:#D31515; font-size:0.8rem; text-align:center; margin-bottom:5px;'>⚠️ CONFIRM WIPE?</div>", unsafe_allow_html=True)
            c_yes, c_no = st.columns(2)
            with c_yes:
                if st.button("YES", type="primary"):
                    for f in os.listdir(STORAGE_DIR): os.remove(os.path.join(STORAGE_DIR, f))
                    st.session_state.wipe_confirm = False
                    st.rerun()
            with c_no:
                if st.button("NO", type="secondary"):
                    st.session_state.wipe_confirm = False
                    st.rerun()
        
        st.markdown("<div style='margin-bottom:5px;'></div>", unsafe_allow_html=True)
        if st.button("CLEAR CHAT"):
            st.session_state.messages = []
            st.rerun()

def render_metrics():
    files = [f for f in os.listdir(STORAGE_DIR) if f != "metadata.json"]
    meta = load_metadata()
    active_count = sum(1 for f in files if meta.get(f, True))
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="metric-card"><div class="metric-label">System Status</div><div class="metric-value" style="color:#4CAF50;">ONLINE</div><div class="metric-desc">Neural Engine Active</div></div>""", unsafe_allow_html=True)
    with c2: 
        color = "#4CAF50" if active_count > 0 else "#D31515"
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Knowledge Base</div><div class="metric-value" style="color:{color};">{active_count} ACTIVE</div><div class="metric-desc">Vectors Loaded</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="metric-card"><div class="metric-label">Personality</div><div class="metric-value" style="color:#4CAF50;">DIRECTOR</div><div class="metric-desc">Strategic Mode</div></div>""", unsafe_allow_html=True)

# --- 5. MAIN EXECUTION ---

def main():
    init_storage()
    inject_custom_css()
    
    knowledge_engine = KnowledgeEngine()
    ai_engine = AIEngine()
    
    if "messages" not in st.session_state: st.session_state.messages = []

    render_sidebar(knowledge_engine)

    tab1, tab2, tab3 = st.tabs(["// ACCOUNTS_CHAT", "// EXEC_1_PAGER", "// DATA_RECON"])

    with tab1:
        st.markdown(f"<div style='margin-bottom:20px;'><span class='active-session-text'>// ACTIVE SESSION: {datetime.now().strftime('%H:%M')}</span></div>", unsafe_allow_html=True)
        render_metrics()
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🔴"):
                st.markdown(message["content"])

        if prompt := st.chat_input("QUERY THE KNOWLEDGE BASE..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"): st.markdown(prompt)

            with st.chat_message("assistant", avatar="🔴"):
                response_placeholder = st.empty()
                full_response = ""
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

    with tab2:
        st.markdown("### // EXECUTIVE ONE-PAGER GENERATOR")
        if st.button("GENERATE 1-PAGER"):
            with st.spinner("SYNTHESIZING KNOWLEDGE BASE..."):
                context = knowledge_engine.get_all_context()
                summary = ai_engine.generate_one_pager(context)
                st.markdown("---")
                st.markdown(summary)

    with tab3:
        st.markdown("### // RAW DATA INSPECTION")
        files = [f for f in os.listdir(STORAGE_DIR) if f != "metadata.json"]
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