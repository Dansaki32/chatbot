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
        
        :root {
            --bg-color: #1a1a1a;
            --sidebar-bg: #000000;
            --accent-red: #D31515;
            --accent-green: #4CAF50;
            --text-white: #FFFFFF;
            --font-display: 'Roboto', sans-serif;
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
        
        /* FILE UPLOADER */
        [data-testid="stFileUploader"] { background-color: #0A0A0A; border: 1px solid #333; padding: 15px; }
        [data-testid="stFileUploader"] div, [data-testid="stFileUploader"] p, [data-testid="stFileUploader"] small { color: #FFFFFF !important; }
        [data-testid="stFileUploader"] button { background-color: var(--accent-red) !important; color: white !important; }

        /* BUTTONS */
        div.stButton > button { 
            background-color: #000000 !important; 
            color: #AAAAAA !important; 
            border: 1px solid #333 !important; 
            text-transform: uppercase; 
            font-size: 0.8rem !important;
        }
        div.stButton > button:hover { border-color: var(--accent-red) !important; color: #FFFFFF !important; }

        /* METRIC CARDS */
        .metric-card { background: #000000; border: 1px solid #333; padding: 20px; margin-bottom: 20px; }
        .metric-label { font-size: 0.75rem; color: #888; letter-spacing: 2px; text-transform: uppercase; }
        .metric-value { font-size: 1.5rem; color: white; }

        .active-session-text { color: var(--accent-red); font-family: var(--font-mono); font-size: 0.8rem; animation: pulse-red 2s infinite; }
        @keyframes pulse-red { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BACKEND LOGIC (CLOUD + LOCAL) ---

BUCKET_NAME = "plenary-matrix-460717-u7" 
METADATA_BLOB = "metadata.json"

def get_gcs_client():
    try:
        if "gcp_service_account" not in st.secrets: return None
        creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        return storage.Client(credentials=creds, project=creds.project_id)
    except Exception: return None

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

def save_uploaded_file(uploaded_file):
    client = get_gcs_client()
    if not client: 
        st.error("GCS Client Connection Failed - Check Secrets")
        return False
    try:
        # FIXED: Using the BUCKET_NAME variable correctly
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(uploaded_file.name)
        
        # MEMORY PROTECTION: Chunked upload prevents PC crashes
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
        context = ""
        # 1. READ LOCAL 'table.tsv'
        script_dir = os.path.dirname(os.path.abspath(__file__))
        local_file = os.path.join(script_dir, "table.tsv")
        if os.path.exists(local_file):
            try:
                df_local = pd.read_csv(local_file, sep='\t')
                context += f"/// LOCAL SYSTEM DATA ///\n{df_local.to_string(index=False)}\n\n"
            except: pass

        # 2. READ GCS (With Memory Safeguards)
        client = get_gcs_client()
        if client:
            try:
                bucket = client.bucket(BUCKET_NAME)
                meta = load_metadata(bucket)
                blobs = list(bucket.list_blobs())
                active_files = [b for b in blobs if meta.get(b.name, True) and b.name != METADATA_BLOB]
                
                for blob in active_files:
                    content_bytes = blob.download_as_bytes()
                    if blob.name.endswith(".pdf"):
                        reader = pypdf.PdfReader(io.BytesIO(content_bytes))
                        text = "".join([p.extract_text() for p in reader.pages[:5]])
                        context += f"=== FILE: {blob.name} ===\n{text[:5000]}\n"
                    elif blob.name.endswith((".csv", ".tsv")):
                        sep = '\t' if blob.name.endswith('.tsv') else ','
                        df = pd.read_csv(io.BytesIO(content_bytes), sep=sep, nrows=100)
                        context += f"=== FILE: {blob.name} ===\n{df.to_string()}\n"
            except Exception as e:
                context += f"[CLOUD ERROR: {str(e)}]"
        return context
    
class AIEngine:
    def __init__(self):
        try:
            self.api_key = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            self.active = True
        except: self.active = False

    def stream_response(self, user_query, db_context):
        if not self.active: yield "SYSTEM ERROR: API KEY MISSING."; return
        system_prompt = f"ROLE: QR_ ACCOUNTS OS. KNOWLEDGE BASE: {db_context}"
        try:
            response = self.model.generate_content(f"{system_prompt}\n\nUSER: {user_query}", stream=True)
            for chunk in response: yield chunk.text
        except Exception as e: yield f"API ERROR: {str(e)}"

    def generate_one_pager(self, db_context):
        if not self.active: return "SYSTEM ERROR: API KEY MISSING."
        try:
            response = self.model.generate_content(f"Create a Strategy 1-Pager based on: {db_context}")
            return response.text
        except Exception as e: return f"ERROR: {str(e)}"

# --- 4. FRONTEND COMPONENTS ---

def render_sidebar(knowledge_engine):
    with st.sidebar:
        st.markdown("<h1 style='color:white;'>QR_</h1>", unsafe_allow_html=True)
        st.markdown("ACCOUNTS OS v6.3<br><hr>", unsafe_allow_html=True)

        # UPLOAD
        if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
        uploaded_file = st.file_uploader("INGEST KNOWLEDGE", type=['csv', 'tsv', 'pdf'], key=f"uploader_{st.session_state.uploader_key}")
        
        if uploaded_file:
            if save_uploaded_file(uploaded_file):
                st.toast(f"UPLOADED: {uploaded_file.name}")
                st.session_state.uploader_key += 1
                time.sleep(1)
                st.rerun()

        # CLOUD DATASETS
        st.markdown("### CLOUD DATASETS")
        client = get_gcs_client()
        if client:
            bucket = client.bucket(BUCKET_NAME)
            try:
                blobs = list(bucket.list_blobs())
                meta = load_metadata(bucket)
                files = [b.name for b in blobs if b.name != METADATA_BLOB]
                for f in files:
                    is_active = meta.get(f, True)
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"{'🟢' if is_active else '⚫'} {f}")
                    if col2.button("X", key=f"del_{f}"):
                        delete_file(f)
                        st.rerun()
            except: st.write("Empty Storage")
        
        if st.button("CLEAR CHAT"):
            st.session_state.messages = []
            st.rerun()

def render_metrics():
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown('<div class="metric-card"><div class="metric-label">System</div><div class="metric-value">ONLINE</div></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="metric-card"><div class="metric-label">Neural Engine</div><div class="metric-value">ACTIVE</div></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="metric-card"><div class="metric-label">Mode</div><div class="metric-value">DIRECTOR</div></div>', unsafe_allow_html=True)

# --- 5. MAIN EXECUTION ---

def main():
    inject_custom_css()
    if "messages" not in st.session_state: st.session_state.messages = []
    
    knowledge_engine = KnowledgeEngine()
    ai_engine = AIEngine()

    render_sidebar(knowledge_engine)

    tab1, tab2, tab3 = st.tabs(["// ACCOUNTS_CHAT", "// EXEC_1_PAGER", "// DATA_RECON"])

    with tab1:
        st.markdown(f"// ACTIVE SESSION: {datetime.now().strftime('%H:%M')}")
        render_metrics()
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]): st.markdown(message["content"])

        if prompt := st.chat_input("QUERY KNOWLEDGE BASE..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                resp_placeholder = st.empty()
                full_response = ""
                context = knowledge_engine.get_all_context()
                for chunk in ai_engine.stream_response(prompt, context):
                    full_response += chunk
                    resp_placeholder.markdown(full_response + "▌")
                resp_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

    with tab2:
        if st.button("GENERATE 1-PAGER"):
            with st.spinner("SYNTHESIZING..."):
                summary = ai_engine.generate_one_pager(knowledge_engine.get_all_context())
                st.markdown(summary)

if __name__ == "__main__":
    main()