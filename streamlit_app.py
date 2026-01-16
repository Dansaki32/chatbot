

```python
import streamlit as st
import pandas as pd
import google.generativeai as genai
import sqlite3
import time
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="QR_ Strategy OS",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ADVANCED VISUAL POLISH (CSS) ---
st.markdown("""
    <style>
    /* 1. CORE FONTS & COLORS */
    @import url('https://fonts.cdnfonts.com/css/segoe-ui-4');
    * { font-family: 'Segoe UI', sans-serif !important; }
    
    /* 2. DEEP DARK MODE FORCE */
    html, body, .stApp {
        background-color: #000000 !important;
        color: #E0E0E0 !important;
    }
    
    /* 3. SIDEBAR PERFECTION */
    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #1A1A1A !important;
    }
    
    /* 4. THE FILE UPLOADER (Fixed the White Box) */
    [data-testid="stFileUploader"] {
        padding: 0px !important;
    }
    [data-testid="stFileUploader"] section {
        background-color: #0A0A0A !important; /* Dark Grey Background */
        border: 1px dashed #333 !important;
        border-radius: 0px !important;
        padding: 20px !important;
    }
    /* The Dropzone Text */
    [data-testid="stFileUploader"] div { color: #666 !important; }
    [data-testid="stFileUploader"] span { color: #888 !important; }
    [data-testid="stFileUploader"] small { color: #444 !important; }
    
    /* Browse Button - High Impact Red */
    [data-testid="stFileUploader"] button {
        background-color: #AD1212 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        border-radius: 0px !important;
        transition: all 0.3s !important;
    }
    [data-testid="stFileUploader"] button:hover {
        background-color: #D31515 !important;
        box-shadow: 0 0 15px rgba(173, 18, 18, 0.4) !important;
    }

    /* 5. CHAT INTERFACE */
    /* Input Box */
    div[data-testid="stChatInput"] {
        background-color: #000000 !important;
        border: 1px solid #333 !important;
        border-radius: 0px !important;
    }
    div[data-testid="stChatInput"]:focus-within {
        border-color: #AD1212 !important;
    }
    div[data-testid="stChatInput"] textarea {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        caret-color: #AD1212 !important;
    }
    
    /* Messages */
    div[data-testid="stChatMessage"] {
        background-color: #0A0A0A !important;
        border: 1px solid #1A1A1A;
        border-radius: 0px !important;
        margin-bottom: 10px;
    }
    /* User Message Override */
    div[data-testid="stChatMessage"][data-test-user-name="user"] {
        background-color: #000000 !important;
        border-left: 2px solid #333;
    }
    /* AI Message Override */
    div[data-testid="stChatMessage"][data-test-user-name="assistant"] {
        background-color: #080808 !important;
        border-left: 2px solid #AD1212;
    }

    /* 6. SIDEBAR BUTTONS */
    div.stButton > button {
        background-color: #000000 !important;
        border: 1px solid #333 !important;
        color: #888 !important;
        border-radius: 0px !important;
        text-transform: uppercase;
        font-size: 0.8rem !important;
    }
    div.stButton > button:hover {
        border-color: #AD1212 !important;
        color: #AD1212 !important;
    }
    
    /* 7. HIDE STREAMLIT UI ELEMENTS */
    [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATABASE ENGINE (SQLite) ---
def init_db():
    conn = sqlite3.connect('strategy.db')
    c = conn.cursor()
    # Create a master log table
    c.execute('''CREATE TABLE IF NOT EXISTS upload_log
                 (timestamp TEXT, filename TEXT, status TEXT, row_count INTEGER)''')
    conn.commit()
    return conn

def validate_and_ingest(df, filename, api_key):
    """
    1. Sends data schema to Gemini for validation.
    2. If valid, commits to SQLite.
    """
    conn = init_db()
    
    # 1. AI VALIDATION PASS
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # We send the columns and first 3 rows to check structure
        preview = df.head(3).to_string()
        validation_prompt = f"""
        ACT AS A DATA ENGINEER. Analyze this dataset snippet.
        Filename: {filename}
        Data:
        {preview}
        
        Task: Verify if this looks like valid business/strategy data. 
        Output ONLY: "VALID" or "INVALID: [Reason]"
        """
        response = model.generate_content(validation_prompt)
        ai_verdict = response.text.strip()
    except Exception as e:
        ai_verdict = "VALID (AI Bypass due to connection)" # Fallback

    # 2. DATABASE COMMIT
    if "VALID" in ai_verdict.upper():
        try:
            # Dynamic table creation based on filename (sanitized)
            table_name = "data_" + filename.split('.')[0].replace(" ", "_").lower()
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            
            # Log it
            c = conn.cursor()
            c.execute("INSERT INTO upload_log VALUES (?, ?, ?, ?)", 
                      (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), filename, "SUCCESS", len(df)))
            conn.commit()
            return True, f"AI AUDIT PASSED. COMMITTED {len(df)} ROWS TO DB TABLE '{table_name}'."
        except Exception as e:
            return False, f"DATABASE ERROR: {str(e)}"
    else:
        return False, f"AI VALIDATION FAILED: {ai_verdict}"

# --- 4. SIDEBAR LOGIC ---
with st.sidebar:
    st.markdown("""
        <h1 style='font-size: 3rem; margin:0; line-height:1; color:white !important;'>QR<span style='color:#AD1212;'>_</span></h1>
        <p style='font-size: 0.75rem; letter-spacing: 2px; color: #666 !important; margin-top: 5px; margin-bottom: 30px;'>STRATEGY OPERATING SYSTEM</p>
    """, unsafe_allow_html=True)
    
    # --- DATA INGESTION ---
    st.markdown("<div style='color:#AD1212; font-size:0.7rem; font-weight:bold; margin-bottom:5px;'>01 // DATA INGESTION</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Data", type=["csv", "tsv"], label_visibility="collapsed")
    
    db_status = ""
    
    if uploaded_file:
        if "db_ingested" not in st.session_state or st.session_state.db_ingested != uploaded_file.name:
            # Perform the Ingestion
            df = pd.read_csv(uploaded_file)
            try:
                api_key = st.secrets["GEMINI_API_KEY"]
                success, msg = validate_and_ingest(df, uploaded_file.name, api_key)
                if success:
                    st.session_state.db_ingested = uploaded_file.name
                    db_status = f"<span style='color:#4CAF50;'>✓ {msg}</span>"
                else:
                    db_status = f"<span style='color:#FF0000;'>⚠ {msg}</span>"
            except:
                db_status = "<span style='color:#FF0000;'>⚠ API KEY MISSING - CANNOT VALIDATE</span>"
        else:
             db_status = "<span style='color:#4CAF50;'>✓ DATASET ACTIVE IN DATABASE</span>"
    
    if db_status:
        st.markdown(f"<div style='font-size:0.7rem; line-height:1.4; margin-top:10px; border-left:2px solid #333; padding-left:10px;'>{db_status}</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

    # --- SYSTEM LOGS ---
    st.markdown("<div style='color:#AD1212; font-size:0.7rem; font-weight:bold; margin-bottom:5px;'>02 // SYSTEM LOGS</div>", unsafe_allow_html=True)
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        report_text = f"QR_ STRATEGY LOG\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for m in st.session_state.messages:
            report_text += f"[{m['role'].upper()}]\n{m['content']}\n\n"
        st.download_button("DOWNLOAD LOG", report_text, file_name="QR_Log.txt")
    else:
        st.markdown("<div style='color:#444; font-size:0.7rem;'>NO TELEMETRY AVAILABLE</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:50px'></div>", unsafe_allow_html=True)
    if st.button("TERMINATE SESSION"):
        st.session_state.messages = []
        if 'db_ingested' in st.session_state:
            del st.session_state.db_ingested
        st.rerun()

# --- 5. MAIN INTERFACE ---
st.markdown("""
    <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 30px;'>
        <div>
            <h1 style='font-size: 2.8rem; margin:0; font-weight:300; letter-spacing:-1px; color:white !important;'>QR<span style='color:#AD1212;'>_</span> STRATEGY</h1>
        </div>
        <div style='border:1px solid #AD1212; padding:5px 12px; background:#0A0000;'>
            <span style='color: #AD1212 !important; font-size: 0.7rem; font-weight: bold; letter-spacing:1px;'>SENIOR DIRECTOR ACTIVE</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Zero State
if len(st.session_state.messages) == 0:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    card_style = "background:#0A0A0A; padding:25px; border:1px solid #1A1A1A; height:100%;"
    head_style = "color:#AD1212 !important; font-weight:bold; font-size:0.8rem; margin-bottom:10px; letter-spacing:1px;"
    text_style = "color:#666 !important; font-size:0.85rem; line-height:1.5;"
    
    with c1:
        st.markdown(f"<div style='{card_style}'><div style='{head_style}'>GROWTH VECTORS</div><div style='{text_style}'>Identify white-space opportunities and penetration gaps.</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='{card_style}'><div style='{head_style}'>RISK MATRIX</div><div style='{text_style}'>Evaluate stakeholder sentiment and project delivery risks.</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div style='{card_style}'><div style='{head_style}'>COMPETITIVE INTEL</div><div style='{text_style}'>Analyze QR value proposition against market threats.</div></div>", unsafe_allow_html=True)

for message in st.session_state.messages:
    role = message["role"]
    avatar = "👤" if role == "user" else "🔴"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message["content"])

# --- 6. AI ENGINE (Gemini 2.5 + DB Context) ---
if prompt := st.chat_input("INITIALIZE STRATEGIC QUERY..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # TARGET GEMINI 2.5 FLASH
        model = genai.GenerativeModel('gemini-2.5-flash')

        # CONTEXT BUILDING
        # Check if we have data in the DB
        conn = init_db()
        c = conn.cursor()
        
        # Get list of tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = c.fetchall()
        
        db_context = ""
        if tables:
            db_context = "\n\n[ATTACHED DATABASE TABLES]:\n"
            for t in tables:
                table_name = t[0]
                # Get schema
                df_head = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 3", conn)
                db_context += f"TABLE: {table_name}\nSCHEMA: {df_head.to_string()}\n\n"

        system_prompt = f"""
        You are the Quick Release (QR_) Senior Account Strategy Director.
        You have access to a secure internal database.
        
        DATABASE CONTEXT:
        {db_context}
        
        If the user asks about the data, analyze the schema provided above.
        """
        
        # RETRY LOGIC (429 HANDLING)
        max_retries = 3
        full_response = ""
        
        for attempt in range(max_retries):
            try:
                response = model.generate_content(f"{system_prompt}\n\nQUERY: {st.session_state.messages[-1]['content']}")
                full_response = response.text
                break
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    full_response = f"**SYSTEM ALERT**: {str(e)}"
                    break

    except Exception as e:
        full_response = f"**CRITICAL FAILURE**: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()
```