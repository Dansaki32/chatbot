import streamlit as st
import pandas as pd
import google.generativeai as genai
from google.cloud import storage
from google.oauth2 import service_account
import io
import json
import time
import pypdf
import os  # <--- FIXED: ADDED MISSING IMPORT
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

        /* --- GLOBAL BUTTON STYLING (FIXES WHITE BUTTONS) --- */
        /* Targets ALL buttons (Sidebar + Main Page) */
        div.stButton > button { 
            background-color: #000000 !important; 
            color: #AAAAAA !important; 
            border: 1px solid #333 !important; 
            font-family: var(--font-display) !important; 
            text-transform: uppercase; 
            font-size: 0.8rem !important; /* Slightly larger for main page readability */
            transition: all 0.2s ease;
        }
        
        /* Hover State */
        div.stButton > button:hover { 
            border-color: var(--accent-red) !important; 
            color: #FFFFFF !important; 
            box-shadow: 0 0 8px rgba(211, 21, 21, 0.4);
        }

        /* Primary/Active Buttons (Red Filled) */
        div.stButton > button[kind="primary"] {
            background-color: var(--accent-red) !important;
            color: #FFFFFF !important;
            border: 1px solid var(--accent-red) !important;
        }

        /* Specific fix for Sidebar Micro-Buttons to keep them small */
        [data-testid="stSidebar"] div[data-testid="column"] button {
            font-size: 0.6rem !important; 
            padding: 0px !important;
            min-height: 24px !important; 
            height: 24px !important; 
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

# --- 3. BACKEND LOGIC (GOOGLE CLOUD STORAGE) ---

# !!! CHANGE THIS TO YOUR BUCKET NAME !!!
BUCKET_NAME = "qr-accounts-os-memory" 
METADATA_BLOB = "metadata.json"

def get_gcs_client():
    """Authenticates using Streamlit Secrets."""
    try:
        if "gcp_service_account" not in st.secrets:
            return None
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        return storage.Client(credentials=creds, project=creds.project_id)
    except Exception as e:
        return None

def load_metadata(bucket):
    blob = bucket.blob(METADATA_BLOB)
    if blob.exists():
        data = blob.download_as_text()
        return json.loads(data)
    return {}

def save_metadata(bucket, data):
    blob = bucket.blob(METADATA_BLOB)
    blob.upload_from_string(json.dumps(data), content_type="application/json")

def save_uploaded_file(uploaded_file):
    client = get_gcs_client()
    if not client: return False
    try:
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(uploaded_file.name)
        uploaded_file.seek(0)
        blob.upload_from_file(uploaded_file)
        
        # Default to Active
        meta = load_metadata(bucket)
        meta[uploaded_file.name] = True
        save_metadata(bucket, meta)
        return True
    except: return False

def delete_file(filename):
    client = get_gcs_client()
    if not client: return False
    try:
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        if blob.exists(): blob.delete()
        
        meta = load_metadata(bucket)
        if filename in meta:
            del meta[filename]
            save_metadata(bucket, meta)
        return True
    except: return False

def set_file_status(filename, status):
    client = get_gcs_client()
    if not client: return
    bucket = client.bucket(BUCKET_NAME)
    meta = load_metadata(bucket)
    meta[filename] = status
    save_metadata(bucket, meta)

class KnowledgeEngine:
    def get_all_context(self):
        client = get_gcs_client()
        if not client: return "ERROR: NO CLOUD CONNECTION. CHECK SECRETS."
        
        bucket = client.bucket(BUCKET_NAME)
        blobs = list(bucket.list_blobs())
        meta = load_metadata(bucket)
        
        files = [b.name for b in blobs if b.name != METADATA_BLOB]
        active_files = [f for f in files if meta.get(f, True)]
        
        if not active_files: return "NO ACTIVE DATA IN CLOUD."
        
        context = f"/// CLOUD KNOWLEDGE BASE ({len(active_files)} FILES) ///\n\n"
        
        for filename in active_files:
            blob = bucket.blob(filename)
            context += f"=== FILE: {filename} ===\n"
            try:
                content_bytes = blob.download_as_bytes()
                if filename.endswith(".pdf"):
                    pdf_file = io.BytesIO(content_bytes)
                    reader = pypdf.PdfReader(pdf_file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    context += f"{text[:15000]} ... [TRUNCATED]\n\n"
                elif filename.endswith(".csv") or filename.endswith(".tsv"):
                    csv_str = content_bytes.decode("utf-8")
                    sep = '\t' if filename.endswith('.tsv') else ','
                    df = pd.read_csv(io.StringIO(csv_str), sep=sep)
                    context += df.to_string(index=False) + "\n\n"
            except Exception as e:
                context += f"[READ ERROR: {str(e)}]\n\n"
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
            if "429" in str(e): yield "⚠️ SYSTEM OVERLOAD (429): Rate limit exceeded."
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
            if "429" in str(e): return "⚠️ SYSTEM OVERLOAD (429)."
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
            <div style='font-family: "Dolce Vita Bold", sans-serif; color:white; font-size:0.8rem; margin-top:20px;'>ACCOUNTS OS v6.2 CLOUD</div>
            <div style='border-top: 1px solid #333; margin-bottom: 20px;'></div>
        """, unsafe_allow_html=True)

        # UPLOAD
        st.markdown("<div style='color:white; font-family:var(--font-display); font-size:0.8rem; margin-bottom:5px;'>INGEST KNOWLEDGE</div>", unsafe_allow_html=True)
        if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
        uploaded_file = st.file_uploader("Upload", type=['csv', 'tsv', 'pdf'], label_visibility="collapsed", key=f"uploader_{st.session_state.uploader_key}")
        
        if uploaded_file:
            success = save_uploaded_file(uploaded_file)
            if success:
                st.toast(f"UPLOADED: {uploaded_file.name}", icon="☁️")
                st.session_state.uploader_key += 1
                time.sleep(1)
                st.rerun()
            else:
                st.error("Upload Failed: Check Credentials.")

        # CLOUD DATASETS LIST
        st.markdown("<br><div style='color:white; font-family:var(--font-display); font-size:0.8rem; margin-bottom:10px;'>CLOUD DATASETS</div>", unsafe_allow_html=True)
        
        client = get_gcs_client()
        if client:
            bucket = client.bucket(BUCKET_NAME)
            try:
                blobs = list(bucket.list_blobs())
                meta = load_metadata(bucket)
                files = [b.name for b in blobs if b.name != METADATA_BLOB]
            except: files = []

            if files:
                for f in files:
                    is_active = meta.get(f, True)
                    
                    status_icon = "🟢" if is_active else "⚫"
                    opacity = "1.0" if is_active else "0.5"
                    st.markdown(f"""
                    <div style="font-size:0.8rem; color:white; opacity:{opacity}; margin-bottom:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                        {status_icon} {f}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 3-BUTTON ROW
                    c1, c2, c3 = st.columns([1, 1, 1.5])
                    with c1:
                        if st.button("ON", key=f"on_{f}", type="primary" if is_active else "secondary"):
                            set_file_status(f, True)
                            st.rerun()
                    with c2:
                        if st.button("OFF", key=f"off_{f}", type="primary" if not is_active else "secondary"):
                            set_file_status(f, False)
                            st.rerun()
                    with c3:
                        if st.button("REMOVE", key=f"del_{f}", type="secondary"):
                            delete_file(f)
                            st.rerun()
                    
                    st.markdown("<div style='margin-bottom:15px; border-bottom:1px solid #222;'></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:#444; font-size:0.8rem;'>Cloud Storage Empty</div>", unsafe_allow_html=True)
        else:
            st.error("No Cloud Connection.")

        # WIPE MEMORY
        st.markdown("<br><br>", unsafe_allow_html=True)
        if "wipe_confirm" not in st.session_state: st.session_state.wipe_confirm = False
        
        if not st.session_state.wipe_confirm:
            if st.button("WIPE CLOUD MEMORY"):
                st.session_state.wipe_confirm = True
                st.rerun()
        else:
            st.markdown("<div style='color:#D31515; font-size:0.8rem; text-align:center; margin-bottom:5px;'>⚠️ DELETE ALL CLOUD DATA?</div>", unsafe_allow_html=True)
            c_yes, c_no = st.columns(2)
            with c_yes:
                if st.button("YES", type="primary"):
                    client = get_gcs_client()
                    bucket = client.bucket(BUCKET_NAME)
                    for blob in bucket.list_blobs(): blob.delete()
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
    client = get_gcs_client()
    active_count = 0
    if client:
        try:
            bucket = client.bucket(BUCKET_NAME)
            blobs = list(bucket.list_blobs())
            meta = load_metadata(bucket)
            files = [b.name for b in blobs if b.name != METADATA_BLOB]
            active_count = sum(1 for f in files if meta.get(f, True))
        except: pass
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="metric-card"><div class="metric-label">System Status</div><div class="metric-value" style="color:#4CAF50;">ONLINE</div><div class="metric-desc">Neural Engine Active</div></div>""", unsafe_allow_html=True)
    with c2: 
        color = "#4CAF50" if active_count > 0 else "#D31515"
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Cloud Knowledge</div><div class="metric-value" style="color:{color};">{active_count} ACTIVE</div><div class="metric-desc">Vectors Loaded</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="metric-card"><div class="metric-label">Personality</div><div class="metric-value" style="color:#4CAF50;">DIRECTOR</div><div class="metric-desc">Strategic Mode</div></div>""", unsafe_allow_html=True)

# --- 5. MAIN EXECUTION ---

def main():
    inject_custom_css()
    if "messages" not in st.session_state: st.session_state.messages = []
    
    knowledge_engine = KnowledgeEngine()
    ai_engine = AIEngine()

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
        st.info("Cloud data inspection is currently minimized for performance.")

if __name__ == "__main__":
    main()