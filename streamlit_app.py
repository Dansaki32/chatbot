import streamlit as st
import pandas as pd
import google.generativeai as genai
import sqlite3
import time
import plotly.express as px
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
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');

        :root {
            --bg-color: #262626;
            --accent-black: #000000;
            --text-white: #FFFFFF;
            --text-gray: #CCCCCC;
            --highlight-red: #D31515;
            --highlight-green: #4CAF50;
            --input-bg: #333333;
        }

        .stApp { background-color: var(--bg-color); color: var(--text-white); font-family: 'Inter', sans-serif; }
        h1, h2, h3, h4, h5, h6 { color: var(--text-white) !important; font-family: 'Inter', sans-serif; letter-spacing: -0.5px; }
        p, div, span { color: var(--text-white); }
        [data-testid="stSidebar"] { background-color: var(--accent-black); border-right: 1px solid #111; }
        
        /* FILE UPLOADER */
        [data-testid="stFileUploader"] { padding: 1rem; background: var(--accent-black); border: 1px solid #444; border-radius: 4px; }
        [data-testid="stFileUploader"] div { color: var(--text-gray) !important; }
        [data-testid="stFileUploader"] button { background-color: var(--highlight-red) !important; color: white !important; border: none; font-weight: bold; }

        /* SIDEBAR BUTTONS */
        [data-testid="stSidebar"] .stButton button {
            color: var(--highlight-red) !important;
            border-color: #333 !important;
            background-color: transparent !important;
            font-weight: bold !important;
            transition: all 0.3s ease;
        }
        [data-testid="stSidebar"] .stButton button:hover {
            border-color: var(--highlight-red) !important;
            box-shadow: 0 0 10px rgba(211, 21, 21, 0.2);
        }

        /* INPUT & CHAT */
        .stChatInput { background: transparent; padding-bottom: 2rem; }
        .stChatInput textarea { background-color: var(--input-bg) !important; color: #FFFFFF !important; border: 1px solid #555 !important; border-radius: 8px !important; font-family: 'Inter', sans-serif !important; }
        .stChatInput textarea:focus { border-color: var(--highlight-red) !important; box-shadow: 0 0 0 1px var(--highlight-red) !important; }
        
        [data-testid="stChatMessage"] { background-color: transparent; border-bottom: 1px solid #333; }
        [data-testid="stChatMessage"] .st-emotion-cache-1p1m4ay { background-color: var(--highlight-red); }

        /* CARDS */
        .metric-card { background: var(--accent-black); border: 1px solid #333; padding: 20px; border-radius: 6px; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .metric-value { font-size: 2rem; font-weight: 700; color: var(--text-white); }
        .metric-label { font-size: 0.85rem; color: var(--text-gray); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; font-weight: 600; }
        .metric-desc { font-size: 0.8rem; color: #888; }

        /* TABS */
        button[data-baseweb="tab"] { background-color: transparent !important; color: var(--text-gray) !important; }
        button[data-baseweb="tab"][aria-selected="true"] { color: var(--text-white) !important; border-bottom-color: var(--highlight-red) !important; }

        #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. BACKEND LOGIC ---

class DataEngine:
    def __init__(self, db_name='strategy_core.db'):
        self.db_name = db_name

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def log_upload(self, filename, status, row_count):
        with self.get_connection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS upload_log
                            (timestamp TEXT, filename TEXT, status TEXT, row_count INTEGER)''')
            conn.execute("INSERT INTO upload_log VALUES (?, ?, ?, ?)",
                         (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), filename, status, row_count))

    def ingest_data(self, df, filename):
        table_name = "data_" + filename.split('.')[0].replace(" ", "_").lower()
        with self.get_connection() as conn:
            df.to_sql(table_name, conn, if_exists='replace', index=False)
        return table_name

    def get_schema_context(self):
        context_str = ""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = cursor.fetchall()
            
            for t in tables:
                table = t[0]
                try:
                    df_sample = pd.read_sql(f"SELECT * FROM {table} LIMIT 1", conn)
                    cols = ", ".join(df_sample.columns)
                    context_str += f"- TABLE: {table} | COLUMNS: {cols}\n"
                except:
                    continue
        return context_str if context_str else "NO DATASETS LOADED."

class AIEngine:
    def __init__(self):
        try:
            self.api_key = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.active = True
        except:
            self.active = False

    def validate_data(self, df_head):
        if not self.active: return "UNKNOWN (API OFF)"
        prompt = f"Analyze this data schema: {df_head}. Task: Return 1-sentence summary."
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return "VALIDATION ERROR"

    def stream_response(self, user_query, history, db_context):
        if not self.active:
            yield "SYSTEM ERROR: API KEY MISSING."
            return

        system_prompt = f"""
        ROLE: You are QR_ ACCOUNTS OS, an elite Account Strategy Operating System.
        TONE: Professional, concise, data-driven.
        CONTEXT: The user has access to the following secure databases:
        {db_context}
        """
        full_query = f"{system_prompt}\n\nUSER QUERY: {user_query}"
        
        try:
            response = self.model.generate_content(full_query, stream=True)
            for chunk in response:
                yield chunk.text
        except Exception as e:
            yield f"API ERROR: {str(e)}"

# --- 4. FRONTEND COMPONENTS ---

def render_sidebar(data_engine, ai_engine):
    with st.sidebar:
        # --- LOGO SECTION (UPDATED FOR logo.png) ---
        possible_paths = [
            "assessts/logo.png",                  # 1. Your requested file in your folder
            "logo.png",                           # 2. Root fallback
            "assessts/QR_logo, long, white.png",  # 3. Screenshot file fallback
            "assets/logo.png"                     # 4. Standard folder fallback
        ]
        
        logo_path = None
        for p in possible_paths:
            if os.path.exists(p):
                logo_path = p
                break
        
        if logo_path:
            st.image(logo_path, use_container_width=True)
        else:
            # Fallback Text if image fails to load
            st.markdown("""
                <h1 style='color:white; font-size:3rem; margin:0; line-height:0.8;'>QR<span style='color:#D31515;'>_</span></h1>
            """, unsafe_allow_html=True)
            
        st.markdown("""
            <div style='font-family: "JetBrains Mono"; font-size: 0.7rem; color: #CCCCCC; letter-spacing: 2px; margin-top: 10px; margin-bottom: 20px;'>ACCOUNTS OS v3.5</div>
            <div style='border-top: 1px solid #333; margin-bottom: 20px;'></div>
        """, unsafe_allow_html=True)

        # Upload
        st.markdown("<div style='color:#D31515; font-weight:bold; font-size:0.8rem; margin-bottom:10px;'>01 // DATA INGESTION</div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("DROP FILE", type=['csv', 'tsv'], label_visibility="collapsed")
        
        if uploaded_file:
            if "last_upload" not in st.session_state or st.session_state.last_upload != uploaded_file.name:
                sep = '\t' if uploaded_file.name.endswith('.tsv') else ','
                df = pd.read_csv(uploaded_file, sep=sep)
                
                validation_msg = ai_engine.validate_data(df.head(3).to_string())
                data_engine.ingest_data(df, uploaded_file.name)
                
                st.session_state.last_upload = uploaded_file.name
                st.session_state.active_df = df
                st.toast(f"SYSTEM: {uploaded_file.name} INGESTED", icon="💾")
                st.success(f"TYPE: {validation_msg}")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Controls
        st.markdown("<div style='color:#D31515; font-weight:bold; font-size:0.8rem; margin-bottom:10px;'>02 // SYSTEM CONTROLS</div>", unsafe_allow_html=True)
        if st.button("CLEAR SESSION CACHE"):
            st.session_state.messages = []
            st.rerun()

def render_zero_state():
    status_text = "ONLINE"
    context_text = "READY" if "active_df" in st.session_state else "WAITING"
    status_color = "#4CAF50"
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">System Status</div>
            <div class="metric-value" style="color:{status_color};">ONLINE</div>
            <div class="metric-desc">All neural modules active.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Data Context</div>
            <div class="metric-value" style="color:{status_color};">{context_text}</div>
            <div class="metric-desc">{'Local vectors loaded.' if context_text == 'READY' else 'Awaiting vector inputs.'}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Personality Type</div>
            <div class="metric-value" style="color:{status_color};">SENIOR DIRECTOR</div>
            <div class="metric-desc">Active.</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br><br><div style='text-align:center; color:#CCC; font-family:JetBrains Mono;'>INITIALIZE QUERY SEQUENCE BELOW...</div>", unsafe_allow_html=True)

# --- 5. MAIN EXECUTION ---

def main():
    inject_custom_css()
    
    data_engine = DataEngine()
    ai_engine = AIEngine()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Auto-Load
    if "local_loaded" not in st.session_state:
        local_file = "table.tsv"
        if os.path.exists(local_file):
            try:
                df_local = pd.read_csv(local_file, sep='\t')
                data_engine.ingest_data(df_local, local_file)
                st.session_state.active_df = df_local
                st.session_state.local_loaded = True
                st.toast(f"AUTO-MOUNT: {local_file} DETECTED & LOADED", icon="📂")
            except Exception as e:
                st.toast(f"AUTO-MOUNT ERROR: {e}", icon="⚠️")
        else:
            st.session_state.local_loaded = False

    render_sidebar(data_engine, ai_engine)

    tab1, tab2 = st.tabs(["// ACCOUNTS_CHAT", "// DATA_RECON"])

    with tab1:
        st.markdown("""
            <div style='display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px;'>
                <div>
                    <span style='color:#D31515; font-weight:bold; font-family:JetBrains Mono;'>// ACTIVE SESSION</span>
                </div>
                <div style='font-family:JetBrains Mono; font-size:0.8rem; color:#CCC;'>
                    {timestamp}
                </div>
            </div>
        """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")), unsafe_allow_html=True)

        if not st.session_state.messages:
            render_zero_state()

        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🔴"):
                st.markdown(message["content"])

        if prompt := st.chat_input("ENTER STRATEGIC QUERY..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar="🔴"):
                response_placeholder = st.empty()
                full_response = ""
                db_context = data_engine.get_schema_context()
                
                try:
                    for chunk in ai_engine.stream_response(prompt, st.session_state.messages, db_context):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                        time.sleep(0.01)
                    
                    response_placeholder.markdown(full_response)
                except Exception as e:
                    response_placeholder.markdown(f"**SYSTEM FAILURE:** {str(e)}")
                    full_response = f"Error: {str(e)}"
                
            st.session_state.messages.append({"role": "assistant", "content": full_response})

    with tab2:
        if "active_df" in st.session_state:
            df = st.session_state.active_df
            st.markdown("### DATA RECONNAISSANCE")
            
            num_cols = df.select_dtypes(include=['float64', 'int64']).columns
            
            if len(num_cols) > 0:
                c1, c2 = st.columns(2)
                with c1:
                    fig = px.bar(df, x=df.columns[0], y=num_cols[0], template="plotly_dark")
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E0E0E0")
                    fig.update_traces(marker_color='#D31515')
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    st.dataframe(df, use_container_width=True)
            else:
                st.dataframe(df, use_container_width=True)
        else:
            st.info("NO DATA LOADED.")

if __name__ == "__main__":
    main()