import streamlit as st
import pandas as pd
import google.generativeai as genai
import sqlite3
import time
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- 1. CONFIG & SYSTEM SETUP ---
st.set_page_config(
    page_title="QR_ STRATEGY OS",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. THE VISUAL CORE (CSS) ---
def inject_custom_css():
    st.markdown("""
    <style>
        /* IMPORTS */
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');

        /* ROOT VARIABLES */
        :root {
            --bg-color: #050505;
            --card-bg: #0F0F0F;
            --border-color: #222;
            --accent-color: #D31515; /* The QR Red */
            --accent-glow: rgba(211, 21, 21, 0.2);
            --text-primary: #E0E0E0;
            --text-secondary: #888888;
        }

        /* GLOBAL RESET */
        .stApp {
            background-color: var(--bg-color);
            font-family: 'Inter', sans-serif;
        }
        
        h1, h2, h3 { font-family: 'Inter', sans-serif; letter-spacing: -0.5px; }
        code, .stCodeBlock, .mono-font { font-family: 'JetBrains Mono', monospace !important; }

        /* SIDEBAR STYLING */
        [data-testid="stSidebar"] {
            background-color: #000000;
            border-right: 1px solid var(--border-color);
        }
        
        /* FILE UPLOADER - THE "DROP ZONE" */
        [data-testid="stFileUploader"] {
            padding: 1rem;
            border: 1px dashed #333;
            background: #080808;
            transition: all 0.3s ease;
        }
        [data-testid="stFileUploader"]:hover {
            border-color: var(--accent-color);
            box-shadow: 0 0 10px var(--accent-glow);
        }
        [data-testid="stFileUploader"] section { background: transparent !important; }
        [data-testid="stFileUploader"] button {
            background-color: var(--accent-color) !important;
            color: white !important;
            border: none;
            text-transform: uppercase;
            font-weight: bold;
            letter-spacing: 1px;
            border-radius: 2px;
        }

        /* CHAT INPUT - THE "TERMINAL" */
        .stChatInput {
            border-top: 1px solid var(--border-color);
            background: #000;
            padding-bottom: 2rem;
        }
        .stChatInput textarea {
            background-color: #0A0A0A !important;
            color: #fff !important;
            border: 1px solid #333 !important;
            font-family: 'JetBrains Mono', monospace !important;
        }
        .stChatInput textarea:focus {
            border-color: var(--accent-color) !important;
            box-shadow: 0 0 10px var(--accent-glow) !important;
        }

        /* CHAT MESSAGES */
        [data-testid="stChatMessage"] {
            background-color: transparent;
            border-bottom: 1px solid #111;
        }
        [data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {
            color: var(--text-primary);
        }
        /* AI Avatar Glow */
        [data-testid="stChatMessage"] .st-emotion-cache-1p1m4ay {
            background-color: var(--accent-color);
            box-shadow: 0 0 15px var(--accent-color);
        }

        /* CUSTOM METRICS CARDS */
        .metric-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            padding: 20px;
            border-radius: 4px;
            height: 100%;
        }
        .metric-value { font-size: 2rem; font-weight: 700; color: #fff; }
        .metric-label { font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; }

        /* DATAFRAME STYLING */
        [data-testid="stDataFrame"] { border: 1px solid #222; }

        /* HIDE STREAMLIT CHROME */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. BACKEND LOGIC (Database & AI) ---

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
        # Sanitize table name
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
                # Get columns
                df_sample = pd.read_sql(f"SELECT * FROM {table} LIMIT 1", conn)
                cols = ", ".join(df_sample.columns)
                context_str += f"- TABLE: {table} | COLUMNS: {cols}\n"
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
        prompt = f"""
        Analyze this data schema for a Strategy Engine.
        Data: {df_head}
        Task: Return a 1-sentence summary of what this data represents.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return "VALIDATION ERROR"

    def stream_response(self, user_query, history, db_context):
        if not self.active:
            yield "SYSTEM ERROR: API KEY MISSING. PLEASE CONFIGURE SECRETS."
            return

        system_prompt = f"""
        ROLE: You are QR_OS, an elite Strategy Operating System for Quick Release.
        TONE: Professional, concise, data-driven, slightly futuristic. Use bullet points.
        CONTEXT: The user has access to the following secure databases:
        {db_context}
        
        INSTRUCTIONS:
        1. If the user asks about data, reference the specific table names available.
        2. If the user asks for strategy, provide high-level frameworks (Growth Vectors, Risk Matrices).
        3. Keep responses under 200 words unless asked for a deep dive.
        """
        
        # Build chat history for context
        history_formatted = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in history]
        
        # Add system prompt effectively by prepending or using system instruction if supported, 
        # here we just wrap the query for simplicity in this demo structure.
        full_query = f"{system_prompt}\n\nUSER QUERY: {user_query}"
        
        response = self.model.generate_content(full_query, stream=True)
        for chunk in response:
            yield chunk.text

# --- 4. FRONTEND COMPONENTS ---

def render_sidebar(data_engine, ai_engine):
    with st.sidebar:
        # Logo Area
        st.markdown("""
            <div style='margin-bottom: 20px;'>
                <h1 style='color:white; font-size:3rem; margin:0; line-height:0.8;'>QR<span style='color:#D31515;'>_</span></h1>
                <div style='font-family: "JetBrains Mono"; font-size: 0.7rem; color: #666; letter-spacing: 2px;'>STRATEGY OS v2.4</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        
        # Upload Section
        st.markdown("<div style='color:#D31515; font-weight:bold; font-size:0.8rem; margin-bottom:10px;'>01 // DATA INGESTION</div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("DROP FILE", type=['csv'], label_visibility="collapsed")
        
        if uploaded_file:
            if "last_upload" not in st.session_state or st.session_state.last_upload != uploaded_file.name:
                df = pd.read_csv(uploaded_file)
                # Quick Validation
                validation_msg = ai_engine.validate_data(df.head(3).to_string())
                # Ingest
                table_name = data_engine.ingest_data(df, uploaded_file.name)
                data_engine.log_upload(uploaded_file.name, "SUCCESS", len(df))
                
                st.session_state.last_upload = uploaded_file.name
                st.session_state.active_df = df # Store for viz
                st.toast(f"SYSTEM: {uploaded_file.name} INGESTED", icon="💾")
                st.success(f"TYPE: {validation_msg}")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Controls
        st.markdown("<div style='color:#D31515; font-weight:bold; font-size:0.8rem; margin-bottom:10px;'>02 // SYSTEM CONTROLS</div>", unsafe_allow_html=True)
        if st.button("CLEAR SESSION CACHE"):
            st.session_state.messages = []
            st.rerun()

        # Footer
        st.markdown("""
            <div style='position: fixed; bottom: 20px; font-size: 0.7rem; color: #444;'>
                SECURE CONNECTION<br>
                LATENCY: 12ms
            </div>
        """, unsafe_allow_html=True)

def render_zero_state():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">System Status</div>
            <div class="metric-value" style="color:#4CAF50;">ONLINE</div>
            <div style="margin-top:10px; font-size:0.8rem; color:#666;">All neural modules active.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Data Context</div>
            <div class="metric-value">READY</div>
            <div style="margin-top:10px; font-size:0.8rem; color:#666;">Awaiting vector inputs.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Security Level</div>
            <div class="metric-value" style="color:#D31515;">ALPHA</div>
            <div style="margin-top:10px; font-size:0.8rem; color:#666;">Senior Director authorization.</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br><br><div style='text-align:center; color:#444; font-family:JetBrains Mono;'>INITIALIZE QUERY SEQUENCE BELOW...</div>", unsafe_allow_html=True)

def render_viz_tab():
    if "active_df" in st.session_state:
        df = st.session_state.active_df
        st.markdown("### DATA RECONNAISSANCE")
        
        # Identify numeric columns for plotting
        num_cols = df.select_dtypes(include=['float64', 'int64']).columns
        
        if len(num_cols) > 0:
            c1, c2 = st.columns(2)
            with c1:
                # Custom Dark Theme Plot
                fig = px.bar(df, x=df.columns[0], y=num_cols[0], template="plotly_dark", title=f"{num_cols[0]} Analysis")
                fig.update_layout(paper_bgcolor="#0F0F0F", plot_bgcolor="#0F0F0F", font_color="#E0E0E0")
                fig.update_traces(marker_color='#D31515')
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.dataframe(df.head(10), use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
    else:
        st.info("NO DATA LOADED. UPLOAD A FILE TO INITIALIZE VISUALS.")

# --- 5. MAIN EXECUTION ---

def main():
    inject_custom_css()
    
    # Initialize Engines
    data_engine = DataEngine()
    ai_engine = AIEngine()
    
    # Session State Init
    if "messages" not in st.session_state:
        st.session_state.messages = []

    render_sidebar(data_engine, ai_engine)

    # Tabs for different views
    tab1, tab2 = st.tabs(["// STRATEGY_CHAT", "// DATA_RECON"])

    with tab1:
        # Header
        st.markdown("""
            <div style='display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1px solid #222; padding-bottom: 10px; margin-bottom: 20px;'>
                <div>
                    <span style='color:#D31515; font-weight:bold; font-family:JetBrains Mono;'>// ACTIVE SESSION</span>
                </div>
                <div style='font-family:JetBrains Mono; font-size:0.8rem; color:#666;'>
                    {timestamp}
                </div>
            </div>
        """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

        # Chat History
        if not st.session_state.messages:
            render_zero_state()

        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🔴"):
                st.markdown(message["content"])

        # Chat Input
        if prompt := st.chat_input("ENTER STRATEGIC QUERY..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

            # Generate AI response
            with st.chat_message("assistant", avatar="🔴"):
                response_placeholder = st.empty()
                full_response = ""
                
                # Get Context
                db_context = data_engine.get_schema_context()
                
                # Stream
                try:
                    for chunk in ai_engine.stream_response(prompt, st.session_state.messages, db_context):
                        full_response += chunk
                        # Typing effect with cursor
                        response_placeholder.markdown(full_response + "▌")
                        time.sleep(0.01) # Slight delay for effect
                    
                    response_placeholder.markdown(full_response)
                except Exception as e:
                    response_placeholder.markdown(f"**SYSTEM FAILURE:** {str(e)}")
                    full_response = f"Error: {str(e)}"
                
            st.session_state.messages.append({"role": "assistant", "content": full_response})

    with tab2:
        render_viz_tab()

if __name__ == "__main__":
    main()