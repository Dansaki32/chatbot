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
        /* 1. LOAD ROBOTO FROM GOOGLE (Body Text) */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=JetBrains+Mono:wght@400&display=swap');

        /* 2. LOAD LOCAL CUSTOM FONTS (DOLCE VITA) */
        @font-face {
            font-family: 'Dolce Vita';
            src: url('Dolce Vita.ttf') format('truetype');
            font-weight: normal;
        }
        @font-face {
            font-family: 'Dolce Vita Light';
            src: url('Dolce Vita Light.ttf') format('truetype');
            font-weight: 300;
        }
        @font-face {
            font-family: 'Dolce Vita Bold';
            src: url('Dolce Vita Heavy Bold.ttf') format('truetype');
            font-weight: bold;
        }

        /* 3. ROOT VARIABLES */
        :root {
            --bg-color: #1a1a1a;
            --sidebar-bg: #000000;
            --accent-red: #D31515;
            --accent-green: #4CAF50;
            --text-white: #FFFFFF;
            --text-gray: #B0B0B0;
            
            /* Font Mappings */
            --font-display: 'Dolce Vita Bold', 'Roboto', sans-serif;
            --font-subdisplay: 'Dolce Vita', 'Roboto', sans-serif;
            --font-body: 'Roboto', sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }

        /* 4. GLOBAL RESETS */
        .stApp { 
            background-color: var(--bg-color); 
            font-family: var(--font-body);
        }
        
        h1, h2, h3 { 
            font-family: var(--font-display) !important; 
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        
        p, div, span, li { 
            font-family: var(--font-body); 
            color: var(--text-white);
        }

        /* 5. SIDEBAR POLISH */
        [data-testid="stSidebar"] { 
            background-color: var(--sidebar-bg); 
            border-right: 1px solid #333; 
        }

        /* FILE UPLOADER - DARK MODE FIX */
        [data-testid="stFileUploader"] {
            background-color: #111111;
            border: 1px dashed #444;
            padding: 15px;
            border-radius: 5px;
        }
        [data-testid="stFileUploader"] section {
            background-color: #111111 !important;
        }
        /* Target the dropzone text - Force White/Light Grey */
        [data-testid="stFileUploader"] div {
            color: #E0E0E0 !important; /* Made brighter for visibility */
            font-family: var(--font-body);
        }
        [data-testid="stFileUploader"] button { 
            background-color: var(--accent-red) !important; 
            color: white !important; 
            border: none; 
            font-family: var(--font-display);
            letter-spacing: 1px;
        }

        /* SIDEBAR BUTTONS (CLEAR CACHE) */
        [data-testid="stSidebar"] .stButton button {
            background-color: #000000 !important; /* Black Background */
            color: var(--accent-red) !important;   /* Red Text */
            border: 1px solid var(--accent-red) !important; /* Red Border */
            font-family: var(--font-display) !important;
            letter-spacing: 1px;
            transition: all 0.3s ease;
            text-transform: uppercase;
        }
        [data-testid="stSidebar"] .stButton button:hover {
            background-color: var(--accent-red) !important; /* Red Fill on Hover */
            color: #FFFFFF !important; /* White Text on Hover */
            box-shadow: 0 0 10px rgba(211, 21, 21, 0.4);
        }

        /* 6. METRIC CARDS */
        .metric-card { 
            background: #000000; 
            border: 1px solid #222; 
            padding: 25px; 
            border-radius: 4px; 
            height: 100%; 
            transition: all 0.3s ease;
        }
        .metric-card:hover {
            border-color: var(--accent-red);
            box-shadow: 0 0 15px rgba(211, 21, 21, 0.1);
        }
        .metric-label { 
            font-family: var(--font-subdisplay);
            font-size: 0.8rem; 
            color: var(--text-gray); 
            letter-spacing: 2px; 
            margin-bottom: 8px; 
        }
        .metric-value { 
            font-family: var(--font-display);
            font-size: 1.2rem; 
            color: var(--text-white); 
        }
        .metric-desc { 
            font-family: var(--font-body);
            font-size: 0.8rem; 
            color: #666; 
            margin-top: 5px;
        }

        /* 7. CHAT INPUT FIX - FORCE DARK BACKGROUND */
        /* This targets the container */
        div[data-testid="stChatInput"] {
            background-color: transparent !important;
        }
        
        /* This targets the actual typing area */
        div[data-testid="stChatInput"] textarea { 
            background-color: #333333 !important; /* Dark Grey Background */
            color: #FFFFFF !important;            /* White Text */
            caret-color: #D31515 !important;      /* Red Cursor */
            border: 1px solid #555 !important; 
            font-family: var(--font-body) !important;
        }
        
        /* Focus state */
        div[data-testid="stChatInput"] textarea:focus {
            border-color: var(--accent-red) !important;
            background-color: #333333 !important; /* Ensure it stays dark on focus */
            color: #FFFFFF !important;
            box-shadow: 0 0 0 1px var(--accent-red) !important;
        }
        
        /* Placeholder Text */
        div[data-testid="stChatInput"] textarea::placeholder {
            color: #888888 !important;
        }

        /* 8. PULSING ANIMATION FOR "ACTIVE SESSION" */
        @keyframes pulse-red {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .active-session-text {
            color: var(--accent-red);
            font-family: var(--font-mono);
            font-size: 0.8rem;
            animation: pulse-red 2s infinite;
        }
        
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
        # --- LOGO & HEADER ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Priority search for logo
        possible_paths = [
            os.path.join(script_dir, "logo.png"),              
            os.path.join(script_dir, "assets", "logo.png"),    
            "logo.png"                                         
        ]
        
        logo_path = None
        for p in possible_paths:
            if os.path.exists(p):
                logo_path = p
                break
        
        if logo_path:
            st.image(logo_path, use_container_width=True)
        else:
            st.markdown("<h1 style='color:white;'>QR_</h1>", unsafe_allow_html=True)
            
        # Updated Subtitle
        st.markdown("""
            <div style='font-family: "Dolce Vita Light", sans-serif; font-size: 0.75rem; color: #888; letter-spacing: 3px; margin-top: 10px; margin-bottom: 20px; text-transform: uppercase;'>
                Accounts OS v3.9
            </div>
            <div style='border-top: 1px solid #333; margin-bottom: 25px;'></div>
        """, unsafe_allow_html=True)

        # Upload Section
        # CHANGED: Font color to WHITE as requested
        st.markdown("""
            <div style='font-family: "Dolce Vita Bold", sans-serif; color:#FFFFFF; font-size:0.85rem; margin-bottom:10px; letter-spacing: 1px;'>
                01 // DATA INGESTION
            </div>
        """, unsafe_allow_html=True)
        
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
        
        # Controls Section
        # CHANGED: Font color to WHITE as requested
        st.markdown("""
            <div style='font-family: "Dolce Vita Bold", sans-serif; color:#FFFFFF; font-size:0.85rem; margin-bottom:10px; letter-spacing: 1px;'>
                02 // SYSTEM CONTROLS
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("CLEAR SESSION CACHE"):
            st.session_state.messages = []
            st.rerun()

def render_zero_state():
    # Dynamic Status
    status_text = "ONLINE"
    context_text = "READY" if "active_df" in st.session_state else "WAITING"
    
    # Colors
    green = "#4CAF50"
    red = "#D31515"
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">System Status</div>
            <div class="metric-value" style="color:{green};">{status_text}</div>
            <div class="metric-desc">All neural modules active.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        # Context is green if ready, red if waiting
        ctx_color = green if context_text == "READY" else red
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Data Context</div>
            <div class="metric-value" style="color:{ctx_color};">{context_text}</div>
            <div class="metric-desc">{'Local vectors loaded.' if context_text == 'READY' else 'Awaiting vector inputs.'}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Personality Type</div>
            <div class="metric-value" style="color:{green};">SENIOR DIRECTOR</div>
            <div class="metric-desc">Active Strategy Mode.</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br><br><div style='text-align:center; color:#555; font-family:JetBrains Mono; font-size: 0.8rem;'>INITIALIZE QUERY SEQUENCE BELOW...</div>", unsafe_allow_html=True)

# --- 5. MAIN EXECUTION ---

def main():
    inject_custom_css()
    
    data_engine = DataEngine()
    ai_engine = AIEngine()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Auto-Load Logic
    if "local_loaded" not in st.session_state:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        local_file = os.path.join(script_dir, "table.tsv")
        
        if os.path.exists(local_file):
            try:
                df_local = pd.read_csv(local_file, sep='\t')
                data_engine.ingest_data(df_local, "table.tsv")
                st.session_state.active_df = df_local
                st.session_state.local_loaded = True
                st.toast(f"AUTO-MOUNT: table.tsv DETECTED & LOADED", icon="📂")
            except Exception as e:
                st.toast(f"AUTO-MOUNT ERROR: {e}", icon="⚠️")
        else:
            st.session_state.local_loaded = False

    render_sidebar(data_engine, ai_engine)

    tab1, tab2 = st.tabs(["// ACCOUNTS_CHAT", "// DATA_RECON"])

    with tab1:
        # Header with pulsing active session
        st.markdown("""
            <div style='display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px;'>
                <div>
                    <span class='active-session-text'>// ACTIVE SESSION</span>
                </div>
                <div style='font-family: "JetBrains Mono"; font-size:0.7rem; color:#555;'>
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
                    fig.update_layout(
                        paper_bgcolor="#1a1a1a", 
                        plot_bgcolor="#1a1a1a", 
                        font_color="#E0E0E0",
                        font_family="Roboto"
                    )
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