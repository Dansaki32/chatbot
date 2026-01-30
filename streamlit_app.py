import streamlit as st
import pandas as pd
import google.generativeai as genai
from google.cloud import storage
from google.oauth2 import service_account
import io
import json
import time
import pypdf
import os
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

        * { border-radius: 0px !important; }
        .stApp { background-color: var(--bg-color); font-family: var(--font-body); }
        header[data-testid="stHeader"] { display: none !important; }
        
        h1, h2, h3 { font-family: var(--font-display) !important; letter-spacing: 2px !important; text-transform: uppercase !important; }
        p, div, span, li { font-family: var(--font-body); color: var(--text-white); }

        [data-testid="stSidebar"] { background-color: var(--sidebar-bg); border-right: 1px solid #333; }
        [data-testid="stSidebar"] img { margin-top: -50px !important; margin-bottom: 20px !important; }

        .metric-card { background: #000000; border: 1px solid #333; padding: 20px; height: 100%; margin-bottom: 20px; }
        .metric-label { font-family: var(--font-body); font-size: 0.75rem; color: #888; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px; }
        .metric-value { font-family: var(--font-display); font-size: 1.5rem; color: white; letter-spacing: 1px; }

        div[data-testid="stChatInput"] textarea { background-color: #0A0A0A !important; color: white !important; border: 1px solid #333 !important; }

        .active-session-text { color: var(--accent-red); font-family: var(--font-mono); font-size: 0.8rem; animation: pulse-red 2s infinite; }
        @keyframes pulse-red { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BACKEND LOGIC ---

# FIXED: Name matched to your Google Cloud Console screenshot
BUCKET_NAME = "accounts_data_store" 
METADATA_BLOB = "metadata.json"

def get_gcs_client():
    try:
        if "gcp_service_account" not in st.secrets: return None
        creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        return storage.Client(credentials=creds, project=creds.project_id)
    except: return None

def load_metadata(bucket):
    try:
        blob = bucket.blob(METADATA_BLOB)
        if blob.exists():
            return json.loads(blob.download_as_text())
    except: pass
    return {}

def save_metadata(bucket, data):
    blob = bucket.blob(METADATA_BLOB)
    blob.upload_from_string(json.dumps(data), content_type="application/json")

# FIXED: Corrected function definition and bucket logic
def save_uploaded_file(uploaded_file):
    client = get_gcs_client()
    if not client: 
        st.error("GCS Client Connection Failed")
        return False
    try:
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(uploaded_file.name)
        
        # MEMORY PROTECTION: Prevents system crashes
        blob.chunk_size = 5 * 1024 * 1024 
        
        uploaded_file.seek(0)
        blob.upload_from_file(uploaded_file, content_type=uploaded_file.type)
        
        meta = load_metadata(bucket)
        meta[uploaded_file.name] = True
        save_metadata(bucket, meta)
        return True
    except Exception as e:
        st.error(f"Upload System Error: {str(e)}")
        return False

# --- 4. ENGINE CLASSES ---

class KnowledgeEngine:
    def get_all_context(self):
        context = ""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        local_file = os.path.join(script_dir, "table.tsv")
        if os.path.exists(local_file):
            try:
                df_local = pd.read_csv(local_file, sep='\t')
                context += f"/// LOCAL SYSTEM DATA ///\n{df_local.to_string(index=False)}\n\n"
            except: pass

        client = get_gcs_client()
        if client:
            try:
                bucket = client.bucket(BUCKET_NAME)
                meta = load_metadata(bucket)
                blobs = list(bucket.list_blobs())
                active_files = [b for b in blobs if meta.get(b.name, True) and b.name != METADATA_BLOB]
                
                for b in active_files:
                    bytes_data = b.download_as_bytes()
                    if b.name.endswith(".pdf"):
                        reader = pypdf.PdfReader(io.BytesIO(bytes_data))
                        text = "".join([p.extract_text() for p in reader.pages[:5]])
                        context += f"=== FILE: {b.name} ===\n{text[:5000]}\n"
                    elif b.name.endswith((".csv", ".tsv")):
                        sep = '\t' if b.name.endswith('.tsv') else ','
                        df = pd.read_csv(io.BytesIO(bytes_data), sep=sep, nrows=100)
                        context += f"=== FILE: {b.name} ===\n{df.to_string()}\n"
            except: pass
        return context

class AIEngine:
    def __init__(self):
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.active = True
        except: self.active = False

    def stream_response(self, query, context):
        if not self.active: yield "API KEY MISSING"; return
        prompt = f"ROLE: QR_ ACCOUNTS OS. CONTEXT: {context}\n\nUSER: {query}"
        try:
            response = self.model.generate_content(prompt, stream=True)
            for chunk in response: yield chunk.text
        except Exception as e: yield f"API ERROR: {str(e)}"

# --- 5. UI COMPONENTS ---

def render_sidebar(k_engine):
    with st.sidebar:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(script_dir, "logo.png")
        if os.path.exists(logo_path): st.image(logo_path, use_container_width=True)
        else: st.markdown("<h1>QR_</h1>", unsafe_allow_html=True)
        
        st.markdown("<div style='font-family:\"Dolce Vita Bold\"; color:white; font-size:0.8rem;'>ACCOUNTS OS v6.3</div><hr>", unsafe_allow_html=True)
        
        if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
        uploaded_file = st.file_uploader("INGEST KNOWLEDGE", type=['csv', 'tsv', 'pdf'], key=f"up_{st.session_state.uploader_key}")
        
        if uploaded_file:
            if save_uploaded_file(uploaded_file):
                st.toast(f"SUCCESS: {uploaded_file.name}")
                st.session_state.uploader_key += 1
                time.sleep(1)
                st.rerun()

        if st.button("CLEAR SESSION"):
            st.session_state.messages = []
            st.rerun()

def render_metrics():
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown('<div class="metric-card"><div class="metric-label">System</div><div class="metric-value">ONLINE</div></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="metric-card"><div class="metric-label">Neural Engine</div><div class="metric-value" style="color:#4CAF50">ACTIVE</div></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="metric-card"><div class="metric-label">Mode</div><div class="metric-value">DIRECTOR</div></div>', unsafe_allow_html=True)

def main():
    inject_custom_css()
    if "messages" not in st.session_state: st.session_state.messages = []
    
    k_engine = KnowledgeEngine()
    ai_engine = AIEngine()
    render_sidebar(k_engine)

    tab1, tab2, tab3 = st.tabs(["// ACCOUNTS_CHAT", "// EXEC_1_PAGER", "// DATA_RECON"])

    with tab1:
        st.markdown(f"<div class='active-session-text'>// ACTIVE SESSION: {datetime.now().strftime('%H:%M')}</div>", unsafe_allow_html=True)
        render_metrics()
        
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if prompt := st.chat_input("QUERY KNOWLEDGE BASE..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                placeholder = st.empty()
                full_resp = ""
                for chunk in ai_engine.stream_response(prompt, k_engine.get_all_context()):
                    full_resp += chunk
                    placeholder.markdown(full_resp + "▌")
                placeholder.markdown(full_resp)
            st.session_state.messages.append({"role": "assistant", "content": full_resp})

if __name__ == "__main__":
    main()