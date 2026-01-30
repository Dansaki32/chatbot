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

# --- 2. VISUAL CORE (CSS RESTORED) ---
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

        /* GLOBAL STYLING */
        * { border-radius: 0px !important; }
        .stApp { background-color: var(--bg-color); font-family: var(--font-body); }
        .block-container { padding-top: 2rem !important; padding-bottom: 8rem !important; }
        header[data-testid="stHeader"] { display: none !important; }
        
        h1, h2, h3 { font-family: var(--font-display) !important; letter-spacing: 2px !important; text-transform: uppercase !important; }
        p, div, span, li { font-family: var(--font-body); color: var(--text-white); }

        /* SIDEBAR BRANDING */
        [data-testid="stSidebar"] { background-color: var(--sidebar-bg); border-right: 1px solid #333; }
        section[data-testid="stSidebar"] > div { padding-top: 0rem !important; }

        /* METRIC CARDS */
        .metric-card { background: #000000; border: 1px solid #333; padding: 20px; height: 100%; margin-bottom: 20px; }
        .metric-label { font-family: var(--font-body); font-size: 0.75rem; color: #888; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px; }
        .metric-value { font-family: var(--font-display); font-size: 1.5rem; color: white; letter-spacing: 1px; }

        /* CHAT INPUT */
        div[data-testid="stChatInput"] { background-color: var(--bg-color) !important; padding-bottom: 1.5rem !important; }
        div[data-testid="stChatInput"] textarea { background-color: #0A0A0A !important; color: white !important; border: 1px solid #333 !important; }

        .active-session-text { color: var(--accent-red); font-family: var(--font-mono); font-size: 0.8rem; letter-spacing: 1px; animation: pulse-red 2s infinite; }
        @keyframes pulse-red { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BACKEND LOGIC ---

# FIXED: Bucket Name corrected based on Cloud Console
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
        if blob.exists(): return json.loads(blob.download_as_text())
    except: pass
    return {}

def save_metadata(bucket, data):
    blob = bucket.blob(METADATA_BLOB)
    blob.upload_from_string(json.dumps(data), content_type="application/json")

# FIXED: Corrected 'def' and typo in 'uploaded_file.seek'
def save_uploaded_file(uploaded_file):
    client = get_gcs_client()
    if not client: return False
    try:
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(uploaded_file.name)
        blob.chunk_size = 5 * 1024 * 1024 
        uploaded_file.seek(0)
        blob.upload_from_file(uploaded_file, content_type=uploaded_file.type)
        
        meta = load_metadata(bucket)
        meta[uploaded_file.name] = True
        save_metadata(bucket, meta)
        return True
    except: return False

def delete_file(filename):
    client = get_gcs_client()
    if client:
        try:
            bucket = client.bucket(BUCKET_NAME)
            bucket.blob(filename).delete()
            meta = load_metadata(bucket)
            if filename in meta:
                del meta[filename]
                save_metadata(bucket, meta)
            return True
        except: return False
    return False

# --- 4. ENGINE CLASSES ---

class KnowledgeEngine:
    def get_all_context(self):
        context = ""
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
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.active = True
        except: self.active = False

    def stream_response(self, query, context):
        if not self.active: yield "API KEY MISSING"; return
        prompt = f"ROLE: QR_ ACCOUNTS OS. CONTEXT: {context}\n\nUSER: {query}"
        try:
            response = self.model.generate_content(prompt, stream=True)
            for chunk in response: yield chunk.text
        except: yield "API ERROR"

# --- 5. UI COMPONENTS ---

def main():
    inject_custom_css()
    if "messages" not in st.session_state: st.session_state.messages = []
    
    k_engine = KnowledgeEngine()
    ai_engine = AIEngine()

    # Sidebar branding restoration
    with st.sidebar:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(script_dir, "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        else:
            st.markdown("<h1 style='color:white;'>QUICK RELEASE_</h1>", unsafe_allow_html=True)
        
        st.markdown("<div style='font-family:\"Dolce Vita Bold\"; color:white; font-size:0.8rem; margin-top:20px;'>ACCOUNTS OS v6.3</div><hr>", unsafe_allow_html=True)
        
        # File Ingest UI
        st.markdown("<div style='color:white; font-family:var(--font-display); font-size:0.8rem; margin-bottom:5px;'>INGEST KNOWLEDGE</div>", unsafe_allow_html=True)
        if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
        uploaded_file = st.file_uploader("Upload", type=['csv', 'tsv', 'pdf'], label_visibility="collapsed", key=f"up_{st.session_state.uploader_key}")
        
        if uploaded_file:
            if save_uploaded_file(uploaded_file):
                st.toast(f"SUCCESS: {uploaded_file.name}")
                st.session_state.uploader_key += 1
                time.sleep(1)
                st.rerun()

        if st.button("CLEAR SESSION"):
            st.session_state.messages = []
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["// ACCOUNTS_CHAT", "// EXEC_1_PAGER", "// DATA_RECON"])

    with tab1:
        st.markdown(f"<div class='active-session-text'>// ACTIVE SESSION: {datetime.now().strftime('%H:%M')}</div>", unsafe_allow_html=True)
        
        # Metrics
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown('<div class="metric-card"><div class="metric-label">SYSTEM</div><div class="metric-value">ONLINE</div></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="metric-card"><div class="metric-label">NEURAL ENGINE</div><div class="metric-value" style="color:#4CAF50">ACTIVE</div></div>', unsafe_allow_html=True)
        with c3: st.markdown('<div class="metric-card"><div class="metric-label">MODE</div><div class="metric-value">DIRECTOR</div></div>', unsafe_allow_html=True)
        
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

    with tab3:
        st.markdown("### // CLOUD KNOWLEDGE RECONCILIATION")
        client = get_gcs_client()
        if client:
            bucket = client.bucket(BUCKET_NAME)
            blobs = list(bucket.list_blobs())
            files = [b.name for b in blobs if b.name != METADATA_BLOB]
            if files:
                for f in files:
                    col1, col2 = st.columns([4, 1])
                    col1.write(f"📄 {f}")
                    if col2.button("DELETE", key=f"recon_del_{f}"):
                        delete_file(f)
                        st.rerun()
            else:
                st.info("Cloud Knowledge Base is currently empty.")

if __name__ == "__main__":
    main()