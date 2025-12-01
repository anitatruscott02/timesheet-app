"""
Execution Edge Timesheet Management System
Production-Ready with Beautiful UI - Light/Dark Mode Compatible
"""

import streamlit as st
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import pandas as pd
import hashlib
import datetime
from datetime import timedelta
import plotly.express as px
import plotly.graph_objects as go
import os
import pytz
from io import BytesIO

# ============== PAGE CONFIGURATION ==============
st.set_page_config(
    page_title="Execution Edge — Timesheet",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== COMPREHENSIVE CSS FOR BRANDING REMOVAL & BEAUTIFUL UI ==============
st.markdown("""
<style>
/* ========== COMPLETE STREAMLIT BRANDING REMOVAL ========== */
/* Remove all Streamlit UI elements */
#MainMenu {visibility: hidden !important; display: none !important;}
header {visibility: hidden !important; display: none !important;}
footer {visibility: hidden !important; display: none !important;}

/* Remove deploy button and badges */
.stDeployButton {display: none !important;}
button[kind="header"] {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}
[data-testid="stDecoration"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}

/* Remove GitHub and Streamlit links */
.viewerBadge_container__1QSob {display: none !important;}
.styles_viewerBadge__1yB5_ {display: none !important;}
.viewerBadge_link__1S137 {display: none !important;}
.viewerBadge_text__1JaDK {display: none !important;}

/* Remove all footer elements */
footer, .footer {display: none !important;}
.css-164nlkn, .css-1n76uvr {display: none !important;}

/* Remove "Made with Streamlit" */
a[href*="streamlit.io"] {display: none !important;}

/* Remove manage app button */
button[title*="manage app"] {display: none !important;}
button[title*="Manage app"] {display: none !important;}

/* Additional overlay removals */
.stApp > header {display: none !important;}
iframe[title="streamlit_option_menu.nav_item"] {border: none !important;}

/* ========== REMOVE BOTTOM RIGHT ICONS (GitHub, Streamlit, etc) ========== */
/* Remove all floating action buttons */
.stActionButton {display: none !important;}
button[kind="icon"] {display: none !important;}
button[kind="borderless"] {display: none !important;}

/* Remove GitHub icon */
svg[class*="github"] {display: none !important;}
a[aria-label*="GitHub"] {display: none !important;}
button[aria-label*="GitHub"] {display: none !important;}

/* Remove fork/edit buttons */
button[title*="Fork"] {display: none !important;}
button[title*="Edit"] {display: none !important;}
a[title*="Fork"] {display: none !important;}
a[title*="Edit"] {display: none !important;}

/* Remove bottom-right corner elements */
.styles_stActionButtonIcon__LySVS {display: none !important;}
.stApp > div > div > div > div > button {
    display: none !important;
}

/* Remove any fixed position buttons */
button[style*="position: fixed"] {display: none !important;}
div[style*="position: fixed"] > button {display: none !important;}

/* Remove Streamlit branding icons */
svg[class*="streamlit"] {display: none !important;}
img[alt*="Streamlit"] {display: none !important;}

/* Remove all floating elements in bottom corners */
div[data-testid="stBottom"] {display: none !important;}
.element-container:has(button[kind="icon"]) {display: none !important;}

/* Remove app menu and settings */
.stAppViewBlockContainer > div:last-child > div:last-child {display: none !important;}

/* Nuclear option for bottom-right icons */
.main > div:last-child > div:last-child > button,
.main > div:last-child > button,
div[style*="bottom: 1rem"][style*="right: 1rem"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* ========== BEAUTIFUL UI STYLES ========== */
/* Root variables for theme compatibility */
:root {
    --primary-color: #2E86DE;
    --secondary-color: #54A0FF;
    --success-color: #10AC84;
    --warning-color: #FFA502;
    --danger-color: #EE5A6F;
    --text-primary: inherit;
    --text-secondary: inherit;
    --bg-primary: transparent;
    --bg-secondary: rgba(128, 128, 128, 0.05);
    --border-color: rgba(128, 128, 128, 0.2);
    --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 20px rgba(0, 0, 0, 0.15);
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
}

/* Main app container */
.stApp {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
}

/* Adjust padding after header removal */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
}

/* ========== ENHANCED METRICS ========== */
[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

[data-testid="stMetricLabel"] {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    opacity: 0.8;
}

[data-testid="stMetricDelta"] {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
}

div[data-testid="metric-container"] {
    background: var(--bg-secondary);
    padding: 1.5rem;
    border-radius: var(--radius-md);
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

div[data-testid="metric-container"]:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-md);
    border-color: var(--primary-color);
}

/* ========== BEAUTIFUL BUTTONS ========== */
.stButton > button {
    border-radius: var(--radius-md) !important;
    font-weight: 600 !important;
    padding: 0.75rem 1.5rem !important;
    border: none !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-sm) !important;
}

.stButton > button:before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0));
    opacity: 0;
    transition: opacity 0.3s;
}

.stButton > button:hover:before {
    opacity: 1;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-md) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
}

.stButton > button[kind="secondary"] {
    background: var(--bg-secondary) !important;
    border: 2px solid var(--border-color) !important;
}

/* ========== ELEGANT TABS ========== */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: var(--bg-secondary);
    padding: 0.5rem;
    border-radius: var(--radius-md);
    border: 1px solid var(--border-color);
}

.stTabs [data-baseweb="tab"] {
    border-radius: var(--radius-sm) !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    border: none !important;
    background: transparent !important;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(128, 128, 128, 0.1) !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
    color: white !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ========== REFINED EXPANDERS ========== */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    font-size: 1.1rem !important;
    background: var(--bg-secondary) !important;
    border-radius: var(--radius-md) !important;
    padding: 1rem 1.25rem !important;
    border: 1px solid var(--border-color) !important;
    transition: all 0.3s ease !important;
}

.streamlit-expanderHeader:hover {
    background: rgba(128, 128, 128, 0.08) !important;
    border-color: var(--primary-color) !important;
}

details[open] > .streamlit-expanderHeader {
    border-bottom-left-radius: 0 !important;
    border-bottom-right-radius: 0 !important;
    border-color: var(--primary-color) !important;
}

.streamlit-expanderContent {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-color) !important;
    border-top: none !important;
    border-bottom-left-radius: var(--radius-md) !important;
    border-bottom-right-radius: var(--radius-md) !important;
    padding: 1.25rem !important;
}

/* ========== POLISHED DATA TABLES ========== */
.stDataFrame {
    border-radius: var(--radius-md) !important;
    overflow: hidden !important;
    border: 1px solid var(--border-color) !important;
    box-shadow: var(--shadow-sm) !important;
}

.stDataFrame [data-testid="stDataFrameResizable"] {
    border-radius: var(--radius-md) !important;
}

/* DataFrame headers */
.stDataFrame thead tr th {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
    color: white !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.5px !important;
    padding: 1rem !important;
}

/* DataFrame rows */
.stDataFrame tbody tr {
    transition: background-color 0.2s ease;
}

.stDataFrame tbody tr:hover {
    background-color: rgba(128, 128, 128, 0.05) !important;
}

/* ========== ELEGANT INPUT FIELDS ========== */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div,
.stTextArea > div > div > textarea,
.stDateInput > div > div > input {
    border-radius: var(--radius-sm) !important;
    border: 2px solid var(--border-color) !important;
    padding: 0.75rem !important;
    font-size: 1rem !important;
    transition: all 0.3s ease !important;
    background: var(--bg-secondary) !important;
}

.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stSelectbox > div > div:focus-within,
.stTextArea > div > div > textarea:focus,
.stDateInput > div > div > input:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 3px rgba(46, 134, 222, 0.1) !important;
}

/* Input labels */
.stTextInput > label,
.stNumberInput > label,
.stSelectbox > label,
.stTextArea > label,
.stDateInput > label {
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    margin-bottom: 0.5rem !important;
}

/* ========== BEAUTIFUL ALERTS ========== */
.stAlert {
    border-radius: var(--radius-md) !important;
    border: none !important;
    padding: 1rem 1.25rem !important;
    box-shadow: var(--shadow-sm) !important;
    font-weight: 500 !important;
}

div[data-baseweb="notification"] {
    border-radius: var(--radius-md) !important;
}

/* Success alerts */
.stSuccess {
    background: linear-gradient(135deg, rgba(16, 172, 132, 0.1), rgba(16, 172, 132, 0.05)) !important;
    border-left: 4px solid var(--success-color) !important;
}

/* Info alerts */
.stInfo {
    background: linear-gradient(135deg, rgba(46, 134, 222, 0.1), rgba(46, 134, 222, 0.05)) !important;
    border-left: 4px solid var(--primary-color) !important;
}

/* Warning alerts */
.stWarning {
    background: linear-gradient(135deg, rgba(255, 165, 2, 0.1), rgba(255, 165, 2, 0.05)) !important;
    border-left: 4px solid var(--warning-color) !important;
}

/* Error alerts */
.stError {
    background: linear-gradient(135deg, rgba(238, 90, 111, 0.1), rgba(238, 90, 111, 0.05)) !important;
    border-left: 4px solid var(--danger-color) !important;
}

/* ========== REFINED SIDEBAR ========== */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border-color) !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 2rem !important;
}

/* Sidebar radio buttons */
[data-testid="stSidebar"] .stRadio > div {
    gap: 0.5rem;
}

[data-testid="stSidebar"] .stRadio > div > label {
    background: rgba(128, 128, 128, 0.05) !important;
    padding: 0.75rem 1rem !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    border: 2px solid transparent !important;
}

[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: rgba(128, 128, 128, 0.1) !important;
    border-color: var(--primary-color) !important;
}

[data-testid="stSidebar"] .stRadio > div > label[data-baseweb="radio"] > div:first-child {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
}

/* ========== CUSTOM SCROLLBAR ========== */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
    border-radius: 5px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    border-radius: 5px;
    transition: background 0.3s ease;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--primary-color);
}

/* ========== PLOTLY CHARTS STYLING ========== */
.js-plotly-plot {
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-sm) !important;
    border: 1px solid var(--border-color) !important;
}

/* ========== CUSTOM CONTAINERS ========== */
.custom-card {
    background: var(--bg-secondary);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
    transition: all 0.3s ease;
}

.custom-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

/* ========== HEADERS & TYPOGRAPHY ========== */
h1, h2, h3, h4, h5, h6 {
    font-weight: 700 !important;
    letter-spacing: -0.5px !important;
}

h1 {
    font-size: 2.5rem !important;
    margin-bottom: 1rem !important;
}

h2 {
    font-size: 2rem !important;
    margin-bottom: 0.875rem !important;
}

h3 {
    font-size: 1.5rem !important;
    margin-bottom: 0.75rem !important;
}

/* ========== LOADING ANIMATION ========== */
.stSpinner > div {
    border-color: var(--primary-color) !important;
    border-right-color: transparent !important;
}

/* ========== RESPONSIVE DESIGN ========== */
@media (max-width: 768px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    [data-testid="metric-container"] {
        padding: 1rem;
    }
    
    .stButton > button {
        padding: 0.6rem 1rem !important;
        font-size: 0.9rem !important;
    }
}

/* ========== CHECKBOX & RADIO STYLING ========== */
.stCheckbox > label {
    font-weight: 500 !important;
    padding: 0.5rem !important;
    border-radius: var(--radius-sm) !important;
    transition: background 0.2s ease !important;
}

.stCheckbox > label:hover {
    background: rgba(128, 128, 128, 0.05) !important;
}

/* ========== DOWNLOAD BUTTON ========== */
.stDownloadButton > button {
    background: linear-gradient(135deg, var(--success-color), #0EE2A0) !important;
    color: white !important;
    font-weight: 600 !important;
}

/* ========== DIVIDERS ========== */
hr {
    margin: 2rem 0 !important;
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, var(--border-color), transparent) !important;
}

/* ========== TOOLTIPS ========== */
[data-testid="stTooltipIcon"] {
    color: var(--primary-color) !important;
}

/* ========== FILE UPLOADER ========== */
[data-testid="stFileUploader"] {
    border: 2px dashed var(--border-color) !important;
    border-radius: var(--radius-md) !important;
    padding: 2rem !important;
    transition: all 0.3s ease !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: var(--primary-color) !important;
    background: rgba(46, 134, 222, 0.02) !important;
}

/* ========== ANIMATIONS ========== */
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.element-container {
    animation: slideIn 0.3s ease-out;
}

/* ========== PRINT STYLES ========== */
@media print {
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    .stButton {
        display: none !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ============== TIMEZONE CONFIGURATION ==============
APP_TIMEZONE = pytz.timezone('Africa/Lagos')

def get_local_time():
    """Get current time in local timezone - WAT (UTC+1)"""
    utc_now = datetime.datetime.now(pytz.UTC)
    return utc_now.astimezone(APP_TIMEZONE)

def get_local_time_naive():
    """Get current local time as naive datetime for database storage"""
    local = get_local_time()
    return local.replace(tzinfo=None)

def format_datetime(dt):
    """Format datetime for display"""
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt
    if hasattr(dt, 'tzinfo') and dt.tzinfo is None:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    elif hasattr(dt, 'astimezone'):
        return dt.astimezone(APP_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)

# ============== DATABASE CONFIGURATION ==============
@st.cache_resource
def init_connection_pool():
    """Create a connection pool for PostgreSQL"""
    try:
        db_config = st.secrets["database"]
        return psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=db_config["host"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"],
            port=db_config.get("port", "5432"),
            sslmode="require"
        )
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        st.info("Please configure database credentials in .streamlit/secrets.toml")
        st.stop()

def get_connection():
    pool = init_connection_pool()
    return pool.getconn()

def release_connection(conn):
    pool = init_connection_pool()
    pool.putconn(conn)

def execute_query(query, params=None, fetch=True):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch:
                result = cur.fetchall()
                return result
            conn.commit()
            return cur.lastrowid if hasattr(cur, 'lastrowid') else None
    finally:
        release_connection(conn)

def execute_df(query, params=None):
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        release_connection(conn)

def init_database():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            # Users table
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                full_name VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL CHECK(role IN ('admin', 'manager', 'employee')),
                department VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER
            )''')
            
            # Clients table
            c.execute('''CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Projects table
            c.execute('''CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                client_id INTEGER NOT NULL REFERENCES clients(id),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                manager_id INTEGER REFERENCES users(id),
                start_date DATE,
                end_date DATE,
                status VARCHAR(20) DEFAULT 'active',
                budget_hours REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Project assignments
            c.execute('''CREATE TABLE IF NOT EXISTS project_assignments (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id),
                employee_id INTEGER NOT NULL REFERENCES users(id),
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(project_id, employee_id)
            )''')
            
            # Time entries
            c.execute('''CREATE TABLE IF NOT EXISTS time_entries (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER NOT NULL REFERENCES users(id),
                project_id INTEGER REFERENCES projects(id),
                entry_date DATE NOT NULL,
                hours REAL NOT NULL,
                minutes INTEGER DEFAULT 0,
                description TEXT,
                task_type VARCHAR(50),
                entry_type VARCHAR(50) DEFAULT 'project_work',
                entry_category VARCHAR(50),
                is_billable BOOLEAN DEFAULT TRUE,
                status VARCHAR(20) DEFAULT 'draft' CHECK(status IN ('draft', 'submitted', 'approved', 'rejected', 'recalled')),
                submitted_at TIMESTAMP,
                reviewed_by INTEGER REFERENCES users(id),
                reviewed_at TIMESTAMP,
                review_comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Add new columns if they don't exist
            try:
                c.execute("ALTER TABLE time_entries ADD COLUMN IF NOT EXISTS entry_type VARCHAR(50) DEFAULT 'project_work'")
                c.execute("ALTER TABLE time_entries ADD COLUMN IF NOT EXISTS entry_category VARCHAR(50)")
            except:
                pass
            
            # Recall requests
            c.execute('''CREATE TABLE IF NOT EXISTS recall_requests (
                id SERIAL PRIMARY KEY,
                time_entry_id INTEGER NOT NULL REFERENCES time_entries(id),
                employee_id INTEGER NOT NULL REFERENCES users(id),
                reason TEXT,
                status VARCHAR(20) DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_by INTEGER REFERENCES users(id),
                reviewed_at TIMESTAMP
            )''')
            
            # Audit logs
            c.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                action VARCHAR(100) NOT NULL,
                entity_type VARCHAR(50),
                entity_id INTEGER,
                details TEXT,
                ip_address VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # System settings
            c.execute('''CREATE TABLE IF NOT EXISTS settings (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Check if admin exists
            c.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
            if c.fetchone()[0] == 0:
                admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
                c.execute("""INSERT INTO users (username, password_hash, full_name, email, role, department) 
                             VALUES (%s, %s, %s, %s, %s, %s)""",
                          ("admin", admin_hash, "System Administrator", "admin@company.com", "admin", "IT"))
            
            # Insert default settings
            defaults = [
                ('recall_window_hours', '24'),
                ('overtime_threshold', '9'),
                ('work_week_start', 'Monday'),
                ('company_name', 'Execution Edge')
            ]
            for key, val in defaults:
                c.execute("""INSERT INTO settings (key, value) VALUES (%s, %s) 
                             ON CONFLICT (key) DO NOTHING""", (key, val))
            
            # Create EE Internal client if not exists
            c.execute("SELECT id FROM clients WHERE name = 'EE Internal'")
            if not c.fetchone():
                c.execute("INSERT INTO clients (name, description) VALUES ('EE Internal', 'Internal company activities')")
            
            conn.commit()
    finally:
        release_connection(conn)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    return hash_password(password) == password_hash

def log_audit(user_id, action, entity_type=None, entity_id=None, details=None):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            local_time = get_local_time_naive()
            c.execute("""INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, created_at) 
                         VALUES (%s, %s, %s, %s, %s, %s)""", (user_id, action, entity_type, entity_id, details, local_time))
            conn.commit()
    finally:
        release_connection(conn)

def get_setting(key):
    result = execute_query("SELECT value FROM settings WHERE key=%s", (key,))
    return result[0]['value'] if result else None

# ============== AUTHENTICATION ==============
def authenticate(username, password):
    result = execute_query(
        "SELECT id, password_hash, full_name, role, is_active FROM users WHERE username=%s", 
        (username,)
    )
    if result:
        user = result[0]
        if verify_password(password, user['password_hash']):
            if user['is_active']:
                return {"id": user['id'], "username": username, "full_name": user['full_name'], "role": user['role']}
            else:
                return {"error": "Account is deactivated"}
    return None


def login_page():
    # Get company name
    company_name = get_setting('company_name') or 'Execution Edge'
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px;">
            <h1 style="margin-bottom: 5px;">🧭 {company_name}</h1>
            <h3 style="font-weight: normal; opacity: 0.8;">Timesheet Management System</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        with st.container():
            username = st.text_input("👤 Username", placeholder="Enter username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🔐 Login", use_container_width=True, type="primary"):
                if username and password:
                    user = authenticate(username, password)
                    if user:
                        if "error" in user:
                            st.error(user["error"])
                        else:
                            st.session_state.user = user
                            st.session_state.logged_in = True
                            log_audit(user["id"], "LOGIN", "user", user["id"])
                            st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
                else:
                    st.warning("⚠️ Please enter username and password")
        
        st.markdown("---")
        st.caption("Default admin: admin / admin123")
        
        # Show current time
        st.caption(f"🕐 Server Time: {get_local_time().strftime('%Y-%m-%d %H:%M:%S')} (WAT)")

# ============== WORKHUB (EMPLOYEE PORTAL) ==============
def workhub_dashboard():
    user = st.session_state.user
    
    # Header
    st.markdown(f"""
    <div style="padding: 10px 0;">
        <h1>🧭 WorkHub</h1>
        <p style="font-size: 1.1em;">Welcome back, <strong>{user['full_name']}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show recall window info
    recall_window = int(get_setting('recall_window_hours') or 24)
    st.info(f"⏰ **Recall Window:** You can recall submitted entries within **{recall_window} hours** of submission.")
    
    tabs = st.tabs(["📝 Project Time", "🏢 EE Internal", "📊 My Dashboard", "🔄 Recall Requests", "📋 My History"])
    
    with tabs[0]:
        workhub_project_time_entry()
    with tabs[1]:
        workhub_ee_internal()
    with tabs[2]:
        workhub_analytics()
    with tabs[3]:
        workhub_recalls()
    with tabs[4]:
        workhub_history()

def workhub_project_time_entry():
    user = st.session_state.user
    
    st.subheader("📝 Log Project Time")
    
    projects_df = execute_df("""
        SELECT p.id, p.name as project_name, c.name as client_name, c.id as client_id
        FROM projects p
        JOIN clients c ON p.client_id = c.id
        JOIN project_assignments pa ON p.id = pa.project_id
        WHERE pa.employee_id = %s AND p.status = 'active' AND c.name != 'EE Internal'
    """, (user['id'],))
    
    if projects_df.empty:
        st.warning("⚠️ You have no projects assigned. Contact your manager.")
        return
    
    # Form layout
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📁 Project Details")
            clients = projects_df['client_name'].unique().tolist()
            selected_client = st.selectbox("Client", clients, key="proj_client")
            
            client_projects = projects_df[projects_df['client_name'] == selected_client]
            selected_project = st.selectbox("Project", client_projects['project_name'].tolist(), key="proj_project")
            
            project_id = int(client_projects[client_projects['project_name'] == selected_project]['id'].values[0])
            
            task_type = st.selectbox("Task Type", [
                "Development", "Design", "Meeting", "Documentation", 
                "Testing", "Support", "Research", "Other"
            ], key="proj_task")
        
        with col2:
            st.markdown("##### ⏱️ Time Details")
            entry_date = st.date_input("Date", datetime.date.today(), key="proj_date")
            
            hcol1, hcol2 = st.columns(2)
            with hcol1:
                hours = st.number_input("Hours", min_value=0, max_value=24, value=8, key="proj_hours")
            with hcol2:
                minutes = st.selectbox("Minutes", [0, 15, 30, 45], key="proj_mins")
            
            is_billable = st.checkbox("💰 Billable", value=True, key="proj_billable")
    
    st.markdown("##### 📝 Description")
    description = st.text_area("What did you work on?", placeholder="Describe your work...", key="proj_desc", height=100)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 Save Draft", use_container_width=True):
            save_time_entry(user['id'], project_id, entry_date, hours, minutes, description, task_type, is_billable, 'draft', 'project_work', None)
            st.success("✅ Draft saved!")
            st.rerun()
    
    with col2:
        if st.button("📤 Submit", use_container_width=True, type="primary"):
            save_time_entry(user['id'], project_id, entry_date, hours, minutes, description, task_type, is_billable, 'submitted', 'project_work', None)
            st.success("✅ Entry submitted for approval!")
            st.rerun()
    
    # Show today's entries
    st.markdown("---")
    st.markdown("##### 📋 Today's Entries")
    show_entries_table(user['id'], entry_date)

def workhub_ee_internal():
    user = st.session_state.user
    
    st.subheader("🏢 EE Internal Time")
    st.markdown("Log time for internal company activities like Leave, Training, or Other Absences.")
    
    # Category selection with visual cards
    st.markdown("##### Select Category")
    
    col1, col2, col3 = st.columns(3)
    
    # Initialize session state for category selection
    if 'ee_category' not in st.session_state:
        st.session_state.ee_category = None
    
    with col1:
        if st.button("🏖️ Leave", use_container_width=True, type="secondary" if st.session_state.ee_category != 'Leave' else "primary"):
            st.session_state.ee_category = 'Leave'
            st.rerun()
        st.caption("Annual leave, sick leave, personal time off")
    
    with col2:
        if st.button("📋 Other Absence", use_container_width=True, type="secondary" if st.session_state.ee_category != 'Other Absence' else "primary"):
            st.session_state.ee_category = 'Other Absence'
            st.rerun()
        st.caption("Jury duty, bereavement, appointments")
    
    with col3:
        if st.button("📚 Training", use_container_width=True, type="secondary" if st.session_state.ee_category != 'Training' else "primary"):
            st.session_state.ee_category = 'Training'
            st.rerun()
        st.caption("Courses, workshops, certifications")
    
    # Show form based on selected category
    if st.session_state.ee_category:
        st.markdown("---")
        st.markdown(f"##### 📝 {st.session_state.ee_category} Request")
        
        category = st.session_state.ee_category
        
        with st.container():
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📅 Date Range**")
                start_date = st.date_input("Start Date", datetime.date.today(), key="ee_start_date")
                end_date = st.date_input("End Date", datetime.date.today(), key="ee_end_date")
                
                # Calculate total days
                if end_date >= start_date:
                    total_days = (end_date - start_date).days + 1
                    st.info(f"📆 **Total Days:** {total_days} day(s)")
                else:
                    st.error("End date must be after start date")
                    total_days = 0
                
                if category == 'Leave':
                    leave_type = st.selectbox("Leave Type", [
                        "Annual Leave", "Sick Leave", "Personal Leave", 
                        "Maternity/Paternity Leave", "Unpaid Leave", "Compassionate Leave", "Other Leave"
                    ], key="ee_leave_type")
                    task_type = leave_type
                elif category == 'Other Absence':
                    absence_type = st.selectbox("Absence Type", [
                        "Jury Duty", "Bereavement", "Medical Appointment",
                        "Family Emergency", "Public Holiday", "Work From Home", "Other Absence"
                    ], key="ee_absence_type")
                    task_type = absence_type
                else:  # Training
                    training_type = st.selectbox("Training Type", [
                        "Internal Training", "External Course", "Conference",
                        "Workshop", "Certification", "Self-Study", "Onboarding", "Seminar"
                    ], key="ee_training_type")
                    task_type = training_type
            
            with col2:
                st.markdown("**⏱️ Hours Per Day**")
                hcol1, hcol2 = st.columns(2)
                with hcol1:
                    hours_per_day = st.number_input("Hours", min_value=0, max_value=24, value=8, key="ee_hours")
                with hcol2:
                    minutes_per_day = st.selectbox("Minutes", [0, 15, 30, 45], key="ee_mins")
                
                # Calculate total hours
                total_hours = (hours_per_day + minutes_per_day/60) * total_days if total_days > 0 else 0
                st.success(f"⏱️ **Total Hours:** {total_hours:.1f} hours")
                
                # Show info based on category
                if category == 'Leave':
                    st.warning("⚠️ Leave requests require manager approval.")
                elif category == 'Other Absence':
                    st.warning("⚠️ Please provide documentation if applicable.")
                else:
                    st.info("📌 Include training provider or course name in description.")
        
        st.markdown("##### 📝 Description / Reason")
        
        if category == 'Leave':
            description = st.text_area("Leave details", placeholder="Reason for leave request, any handover notes, emergency contact if needed...", key="ee_desc", height=120)
        elif category == 'Other Absence':
            description = st.text_area("Absence details", placeholder="Explain the absence reason, provide any relevant details...", key="ee_desc", height=120)
        else:
            description = st.text_area("Training details", placeholder="Course name, provider, learning objectives, how it benefits your role...", key="ee_desc", height=120)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("💾 Save Draft", use_container_width=True, key="ee_draft"):
                if total_days > 0:
                    save_ee_internal_entry(user['id'], start_date, end_date, hours_per_day, minutes_per_day, description, task_type, 'draft', category)
                    st.success("✅ Draft saved!")
                    st.rerun()
                else:
                    st.error("Invalid date range")
        
        with col2:
            if st.button("📤 Submit Request", use_container_width=True, type="primary", key="ee_submit"):
                if total_days > 0:
                    if not description:
                        st.error("Please provide a description/reason")
                    else:
                        save_ee_internal_entry(user['id'], start_date, end_date, hours_per_day, minutes_per_day, description, task_type, 'submitted', category)
                        st.success("✅ Request submitted for approval!")
                        st.rerun()
                else:
                    st.error("Invalid date range")
        
        # Show pending requests
        st.markdown("---")
        st.markdown("##### 📋 My EE Internal Requests")
        my_requests = execute_df("""
            SELECT te.id, te.entry_date as "Start Date", te.task_type as "Type",
                   te.entry_category as "Category", te.hours as "Hours/Day",
                   te.status as "Status", te.description as "Description",
                   te.review_comment as "Manager Comment"
            FROM time_entries te
            WHERE te.employee_id = %s AND te.entry_type = 'ee_internal'
            ORDER BY te.created_at DESC LIMIT 10
        """, (user['id'],))
        
        if not my_requests.empty:
            st.dataframe(my_requests, use_container_width=True, hide_index=True)
        else:
            st.info("No EE Internal requests yet")
    else:
        st.markdown("---")
        st.info("👆 Select a category above to submit an EE Internal request.")

def save_ee_internal_entry(employee_id, start_date, end_date, hours, minutes, description, task_type, status, entry_category):
    """Save EE Internal entry with date range support"""
    conn = get_connection()
    try:
        with conn.cursor() as c:
            local_time = get_local_time_naive()
            submitted_at = local_time if status == 'submitted' else None
            
            # Store the date range info in description
            date_range_info = f"[{start_date} to {end_date}] "
            full_description = date_range_info + (description or "")
            
            # Calculate total days
            total_days = (end_date - start_date).days + 1
            total_hours = hours * total_days + (minutes/60) * total_days
            
            c.execute("""INSERT INTO time_entries 
                        (employee_id, project_id, entry_date, hours, minutes, description, task_type, 
                         is_billable, status, submitted_at, created_at, updated_at, entry_type, entry_category)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                      (employee_id, None, start_date, total_hours, 0, full_description, task_type, 
                       False, status, submitted_at, local_time, local_time, 'ee_internal', entry_category))
            entry_id = c.fetchone()[0]
            conn.commit()
            log_audit(employee_id, f"EE_INTERNAL_{status.upper()}", "time_entry", entry_id, f"{entry_category}: {task_type}")
    finally:
        release_connection(conn)

def save_time_entry(employee_id, project_id, entry_date, hours, minutes, description, task_type, is_billable, status, entry_type, entry_category):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            local_time = get_local_time_naive()
            submitted_at = local_time if status == 'submitted' else None
            c.execute("""INSERT INTO time_entries (employee_id, project_id, entry_date, hours, minutes, description, task_type, is_billable, status, submitted_at, created_at, updated_at, entry_type, entry_category)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                      (employee_id, project_id, entry_date, hours, minutes, description, task_type, is_billable, status, submitted_at, local_time, local_time, entry_type, entry_category))
            entry_id = c.fetchone()[0]
            conn.commit()
            log_audit(employee_id, f"TIME_ENTRY_{status.upper()}", "time_entry", entry_id)
    finally:
        release_connection(conn)

def show_entries_table(employee_id, date=None):
    query = """
        SELECT te.id, 
               COALESCE(c.name, 'EE Internal') as "Client", 
               COALESCE(p.name, te.entry_category) as "Project/Category", 
               te.entry_date as "Date",
               te.hours as "Hours", te.minutes as "Mins", te.task_type as "Task",
               CASE WHEN te.is_billable THEN 'Yes' ELSE 'No' END as "Billable",
               te.status as "Status"
        FROM time_entries te
        LEFT JOIN projects p ON te.project_id = p.id
        LEFT JOIN clients c ON p.client_id = c.id
        WHERE te.employee_id = %s
    """
    params = [employee_id]
    if date:
        query += " AND te.entry_date = %s"
        params.append(date)
    query += " ORDER BY te.entry_date DESC, te.created_at DESC LIMIT 20"
    
    df = execute_df(query, tuple(params))
    
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("📭 No entries found")

def workhub_analytics():
    user = st.session_state.user
    
    st.subheader("📊 My Dashboard")
    
    today = datetime.date.today()
    week_start = today - timedelta(days=today.weekday())
    
    summary = execute_df("""
        SELECT 
            COALESCE(SUM(hours + minutes/60.0), 0) as total_hours,
            COALESCE(SUM(CASE WHEN is_billable THEN hours + minutes/60.0 ELSE 0 END), 0) as billable_hours,
            COUNT(*) as entry_count
        FROM time_entries
        WHERE employee_id = %s AND entry_date >= %s AND status != 'draft'
    """, (user['id'], week_start))
    
    col1, col2, col3, col4 = st.columns(4)
    total_h = float(summary['total_hours'].iloc[0] or 0)
    billable_h = float(summary['billable_hours'].iloc[0] or 0)
    
    col1.metric("📅 This Week", f"{total_h:.1f} hrs")
    col2.metric("💰 Billable", f"{billable_h:.1f} hrs")
    col3.metric("📈 Utilization", f"{(billable_h/total_h*100) if total_h > 0 else 0:.0f}%")
    col4.metric("📝 Entries", int(summary['entry_count'].iloc[0] or 0))
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Billable vs Non-Billable (30 Days)")
        pie_data = execute_df("""
            SELECT 
                CASE WHEN is_billable THEN 'Billable' ELSE 'Non-Billable' END as "Type",
                SUM(hours + minutes/60.0) as "Hours"
            FROM time_entries
            WHERE employee_id = %s AND entry_date >= CURRENT_DATE - INTERVAL '30 days' AND status != 'draft'
            GROUP BY is_billable
        """, (user['id'],))
        
        if not pie_data.empty:
            fig = px.pie(pie_data, values='Hours', names='Type', 
                        color_discrete_sequence=['#00CC96', '#EF553B'])
            fig.update_layout(margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")
    
    with col2:
        st.markdown("##### Daily Hours (14 Days)")
        daily_data = execute_df("""
            SELECT entry_date as "Date", SUM(hours + minutes/60.0) as "Hours"
            FROM time_entries
            WHERE employee_id = %s AND entry_date >= CURRENT_DATE - INTERVAL '14 days' AND status != 'draft'
            GROUP BY entry_date ORDER BY entry_date
        """, (user['id'],))
        
        if not daily_data.empty:
            fig = px.bar(daily_data, x='Date', y='Hours', color_discrete_sequence=['#636EFA'])
            fig.add_hline(y=8, line_dash="dash", line_color="red", annotation_text="Target (8h)")
            fig.update_layout(margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")

def workhub_recalls():
    user = st.session_state.user
    
    st.subheader("🔄 Recall Requests")
    
    recall_window = int(get_setting('recall_window_hours') or 24)
    cutoff = get_local_time() - timedelta(hours=recall_window)
    
    # Show recall window info prominently
    st.markdown(f"""
    <div style="padding: 15px; border-radius: 10px; border-left: 4px solid #1f77b4; margin-bottom: 20px;">
        <strong>⏰ Recall Window: {recall_window} hours</strong><br>
        <small>You can recall entries submitted after: {cutoff.strftime('%Y-%m-%d %H:%M:%S')}</small>
    </div>
    """, unsafe_allow_html=True)
    
    recallable = execute_df("""
        SELECT te.id, 
               COALESCE(c.name, 'EE Internal') as "Client", 
               COALESCE(p.name, te.entry_category) as "Project", 
               te.entry_date as "Date",
               te.hours as "Hours", te.status as "Status", te.submitted_at
        FROM time_entries te
        LEFT JOIN projects p ON te.project_id = p.id
        LEFT JOIN clients c ON p.client_id = c.id
        WHERE te.employee_id = %s AND te.status = 'submitted' AND te.submitted_at > %s
    """, (user['id'], cutoff))
    
    if not recallable.empty:
        st.markdown("##### ✅ Entries You Can Recall")
        for _, row in recallable.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.write(f"**{row['Date']}** | {row['Client']} - {row['Project']} | {row['Hours']}h")
                
                # Calculate time remaining
                if row['submitted_at']:
                    submitted_time = row['submitted_at']
                    if submitted_time.tzinfo is None:
                        submitted_time = pytz.utc.localize(submitted_time)
                    deadline = submitted_time + timedelta(hours=recall_window)
                    time_left = deadline - get_local_time()
                    hours_left = max(0, time_left.total_seconds() / 3600)
                    col2.caption(f"⏳ {hours_left:.1f}h left")
                
                if col3.button("🔄 Recall", key=f"recall_{row['id']}"):
                    conn = get_connection()
                    try:
                        with conn.cursor() as c:
                            c.execute("UPDATE time_entries SET status='recalled', updated_at=%s WHERE id=%s", (get_local_time(), row['id']))
                            conn.commit()
                    finally:
                        release_connection(conn)
                    log_audit(user['id'], "RECALL_ENTRY", "time_entry", row['id'])
                    st.success("✅ Entry recalled!")
                    st.rerun()
                st.markdown("---")
    else:
        st.info(f"📭 No entries eligible for recall. Entries must be submitted within the last {recall_window} hours.")
    
    # Show recall history
    st.markdown("##### 📜 My Recall History")
    history = execute_df("""
        SELECT te.entry_date as "Date", 
               COALESCE(p.name, te.entry_category) as "Project",
               te.hours as "Hours",
               te.status as "Current Status",
               te.updated_at as "Last Updated"
        FROM time_entries te
        LEFT JOIN projects p ON te.project_id = p.id
        WHERE te.employee_id = %s AND te.status = 'recalled'
        ORDER BY te.updated_at DESC LIMIT 10
    """, (user['id'],))
    
    if not history.empty:
        st.dataframe(history, use_container_width=True, hide_index=True)
    else:
        st.caption("No recalled entries")

def workhub_history():
    user = st.session_state.user
    st.subheader("📋 My Time Entry History")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        start_date = st.date_input("From", datetime.date.today() - timedelta(days=30), key="hist_start")
    with col2:
        end_date = st.date_input("To", datetime.date.today(), key="hist_end")
    with col3:
        status_filter = st.selectbox("Status", ["All", "draft", "submitted", "approved", "rejected", "recalled"], key="hist_status")
    
    query = """
        SELECT te.entry_date as "Date", 
               COALESCE(c.name, 'EE Internal') as "Client", 
               COALESCE(p.name, te.entry_category) as "Project",
               te.hours as "Hours", te.minutes as "Mins", te.task_type as "Task",
               CASE WHEN te.is_billable THEN 'Yes' ELSE 'No' END as "Billable",
               te.status as "Status", te.review_comment as "Comment"
        FROM time_entries te
        LEFT JOIN projects p ON te.project_id = p.id
        LEFT JOIN clients c ON p.client_id = c.id
        WHERE te.employee_id = %s AND te.entry_date BETWEEN %s AND %s
    """
    params = [user['id'], start_date, end_date]
    
    if status_filter != "All":
        query += " AND te.status = %s"
        params.append(status_filter)
    
    query += " ORDER BY te.entry_date DESC"
    
    df = execute_df(query, tuple(params))
    
    if not df.empty:
        # Summary stats
        total_hours = df['Hours'].sum() + df['Mins'].sum() / 60
        approved_df = df[df['Status'] == 'approved']
        approved_hours = approved_df['Hours'].sum() + approved_df['Mins'].sum() / 60 if not approved_df.empty else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Entries", len(df))
        col2.metric("Total Hours", f"{total_hours:.1f}")
        col3.metric("Approved Hours", f"{approved_hours:.1f}")
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        csv = df.to_csv(index=False)
        st.download_button("📥 Download CSV", csv, "my_timesheet.csv", "text/csv")
    else:
        st.info("📭 No entries found for selected period")

# ============== MANAGE360 (MANAGER PORTAL) ==============
def manage360_dashboard():
    user = st.session_state.user
    st.title("🧮 Manage360 - Manager Portal")
    st.markdown(f"Welcome, **{user['full_name']}**")
    
    tabs = st.tabs(["📋 Review Queue", "✅ Approvals", "👥 Team Overview", "📊 Analytics", "📁 Projects"])
    
    with tabs[0]:
        manage360_review_queue()
    with tabs[1]:
        manage360_approvals()
    with tabs[2]:
        manage360_team()
    with tabs[3]:
        manage360_analytics()
    with tabs[4]:
        manage360_projects()

def manage360_review_queue():
    user = st.session_state.user
    
    st.subheader("📋 Pending Reviews")
    
    # Tabs for different request types
    review_tabs = st.tabs(["📁 All Pending", "🏢 EE Internal Requests", "📝 Project Time"])
    
    with review_tabs[0]:
        show_all_pending_reviews(user)
    
    with review_tabs[1]:
        show_ee_internal_reviews(user)
    
    with review_tabs[2]:
        show_project_time_reviews(user)

def show_all_pending_reviews(user):
    """Show all pending reviews"""
    pending = execute_df("""
        SELECT te.id, u.full_name as "Employee", 
               COALESCE(c.name, 'EE Internal') as "Client", 
               COALESCE(p.name, te.entry_category) as "Project/Category",
               te.entry_date as "Date", te.hours as "Hours", te.minutes as "Mins",
               te.task_type as "Type", te.description as "Description",
               CASE WHEN te.is_billable THEN 'Yes' ELSE 'No' END as "Billable",
               te.submitted_at as "Submitted",
               te.entry_type as "Entry_Type",
               te.entry_category as "Category"
        FROM time_entries te
        JOIN users u ON te.employee_id = u.id
        LEFT JOIN projects p ON te.project_id = p.id
        LEFT JOIN clients c ON p.client_id = c.id
        WHERE te.status = 'submitted' 
        AND (p.manager_id = %s OR %s IN (SELECT id FROM users WHERE role IN ('manager', 'admin')))
        ORDER BY te.submitted_at ASC
    """, (user['id'], user['id']))
    
    if pending.empty:
        st.success("🎉 No pending reviews! All caught up.")
        return
    
    st.info(f"📬 **{len(pending)}** total entries awaiting review")
    
    for _, row in pending.iterrows():
        entry_type_icon = "🏢" if row['Entry_Type'] == 'ee_internal' else "📁"
        entry_label = f"{row['Category']}" if row['Entry_Type'] == 'ee_internal' else "Project Work"
        
        with st.expander(f"{entry_type_icon} {row['Employee']} | {row['Date']} | {row['Project/Category']} ({row['Hours']:.1f}h) - {entry_label}"):
            col1, col2 = st.columns(2)
            col1.write(f"**Client/Type:** {row['Client']}")
            col1.write(f"**Task:** {row['Type']}")
            col1.write(f"**Request Type:** {entry_label}")
            col2.write(f"**Billable:** {row['Billable']}")
            col2.write(f"**Submitted:** {row['Submitted']}")
            col2.write(f"**Total Hours:** {row['Hours']:.1f}h")
            
            st.write(f"**Description/Reason:** {row['Description'] or 'N/A'}")
            
            comment = st.text_input("Manager Comment", placeholder="Add approval/denial reason...", key=f"comment_{row['id']}")
            
            col1, col2, col3 = st.columns(3)
            if col1.button("✅ Approve", key=f"approve_{row['id']}", type="primary"):
                update_entry_status(row['id'], 'approved', user['id'], comment)
                st.success("✅ Approved!")
                st.rerun()
            if col2.button("❌ Deny", key=f"reject_{row['id']}"):
                if not comment:
                    st.error("Please provide a reason for denial")
                else:
                    update_entry_status(row['id'], 'rejected', user['id'], comment)
                    st.warning("❌ Denied")
                    st.rerun()

def show_ee_internal_reviews(user):
    """Show only EE Internal requests (Leave, Training, Absence)"""
    st.markdown("### 🏢 EE Internal Requests")
    st.markdown("Review and approve/deny Leave, Training, and Other Absence requests.")
    
    pending = execute_df("""
        SELECT te.id, u.full_name as "Employee", u.department as "Department",
               te.entry_category as "Category", te.task_type as "Request Type",
               te.entry_date as "Start Date", te.hours as "Total Hours",
               te.description as "Description/Reason",
               te.submitted_at as "Submitted"
        FROM time_entries te
        JOIN users u ON te.employee_id = u.id
        WHERE te.status = 'submitted' AND te.entry_type = 'ee_internal'
        ORDER BY te.submitted_at ASC
    """)
    
    if pending.empty:
        st.success("🎉 No pending EE Internal requests!")
        return
    
    # Summary cards
    leave_count = len(pending[pending['Category'] == 'Leave'])
    training_count = len(pending[pending['Category'] == 'Training'])
    absence_count = len(pending[pending['Category'] == 'Other Absence'])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🏖️ Leave Requests", leave_count)
    col2.metric("📚 Training Requests", training_count)
    col3.metric("📋 Other Absences", absence_count)
    
    st.markdown("---")
    
    for _, row in pending.iterrows():
        # Color code by category
        if row['Category'] == 'Leave':
            icon = "🏖️"
            color = "🟡"
        elif row['Category'] == 'Training':
            icon = "📚"
            color = "🔵"
        else:
            icon = "📋"
            color = "🟠"
        
        with st.expander(f"{icon} {row['Employee']} - {row['Request Type']} ({row['Total Hours']:.1f}h)"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**👤 Employee:** {row['Employee']}")
                st.write(f"**🏢 Department:** {row['Department']}")
                st.write(f"**📁 Category:** {row['Category']}")
                st.write(f"**📝 Type:** {row['Request Type']}")
            
            with col2:
                st.write(f"**📅 Start Date:** {row['Start Date']}")
                st.write(f"**⏱️ Total Hours:** {row['Total Hours']:.1f} hours")
                st.write(f"**📤 Submitted:** {row['Submitted']}")
            
            st.markdown("**📝 Description/Reason:**")
            st.info(row['Description/Reason'] or 'No description provided')
            
            st.markdown("---")
            comment = st.text_input("Manager Decision Comment", placeholder="Reason for approval/denial...", key=f"ee_comment_{row['id']}")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("✅ Approve Request", key=f"ee_approve_{row['id']}", type="primary", use_container_width=True):
                    update_entry_status(row['id'], 'approved', user['id'], comment or "Approved")
                    st.success(f"✅ {row['Request Type']} request approved!")
                    st.rerun()
            
            with col2:
                if st.button("❌ Deny Request", key=f"ee_reject_{row['id']}", use_container_width=True):
                    if not comment:
                        st.error("⚠️ Please provide a reason for denial")
                    else:
                        update_entry_status(row['id'], 'rejected', user['id'], comment)
                        st.warning(f"❌ {row['Request Type']} request denied")
                        st.rerun()

def show_project_time_reviews(user):
    """Show only project time entries"""
    st.markdown("### 📁 Project Time Entries")
    
    pending = execute_df("""
        SELECT te.id, u.full_name as "Employee", 
               c.name as "Client", p.name as "Project",
               te.entry_date as "Date", te.hours as "Hours", te.minutes as "Mins",
               te.task_type as "Task", te.description as "Description",
               CASE WHEN te.is_billable THEN 'Yes' ELSE 'No' END as "Billable",
               te.submitted_at as "Submitted"
        FROM time_entries te
        JOIN users u ON te.employee_id = u.id
        JOIN projects p ON te.project_id = p.id
        JOIN clients c ON p.client_id = c.id
        WHERE te.status = 'submitted' AND te.entry_type = 'project_work'
        AND (p.manager_id = %s OR %s IN (SELECT id FROM users WHERE role IN ('manager', 'admin')))
        ORDER BY te.submitted_at ASC
    """, (user['id'], user['id']))
    
    if pending.empty:
        st.success("🎉 No pending project time entries!")
        return
    
    st.info(f"📬 **{len(pending)}** project entries awaiting review")
    
    for _, row in pending.iterrows():
        with st.expander(f"📁 {row['Employee']} | {row['Date']} | {row['Project']} ({row['Hours']}h {row['Mins']}m)"):
            col1, col2 = st.columns(2)
            col1.write(f"**Client:** {row['Client']}")
            col1.write(f"**Project:** {row['Project']}")
            col1.write(f"**Task:** {row['Task']}")
            col2.write(f"**Billable:** {row['Billable']}")
            col2.write(f"**Submitted:** {row['Submitted']}")
            st.write(f"**Description:** {row['Description'] or 'N/A'}")
            
            comment = st.text_input("Comment", key=f"proj_comment_{row['id']}")
            
            col1, col2, col3 = st.columns(3)
            if col1.button("✅ Approve", key=f"proj_approve_{row['id']}", type="primary"):
                update_entry_status(row['id'], 'approved', user['id'], comment)
                st.success("✅ Approved!")
                st.rerun()
            if col2.button("❌ Reject", key=f"proj_reject_{row['id']}"):
                update_entry_status(row['id'], 'rejected', user['id'], comment)
                st.warning("❌ Rejected")
                st.rerun()

def update_entry_status(entry_id, status, reviewer_id, comment=None):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            local_time = get_local_time()
            c.execute("""UPDATE time_entries SET status=%s, reviewed_by=%s, reviewed_at=%s, review_comment=%s, updated_at=%s
                         WHERE id=%s""", (status, reviewer_id, local_time, comment, local_time, entry_id))
            conn.commit()
    finally:
        release_connection(conn)
    log_audit(reviewer_id, f"ENTRY_{status.upper()}", "time_entry", entry_id, comment)

def manage360_approvals():
    st.subheader("✅ Approval History")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "approved", "rejected"])
    with col2:
        start = st.date_input("From", datetime.date.today() - timedelta(days=30), key="appr_start")
    with col3:
        end = st.date_input("To", datetime.date.today(), key="appr_end")
    
    query = """
        SELECT te.id, u.full_name as "Employee", 
               COALESCE(p.name, te.entry_category) as "Project", 
               te.entry_date as "Date",
               te.hours as "Hours", te.status as "Status", r.full_name as "Reviewer",
               te.reviewed_at as "Reviewed", te.review_comment as "Comment"
        FROM time_entries te
        JOIN users u ON te.employee_id = u.id
        LEFT JOIN projects p ON te.project_id = p.id
        LEFT JOIN users r ON te.reviewed_by = r.id
        WHERE te.status IN ('approved', 'rejected') AND te.entry_date BETWEEN %s AND %s
    """
    params = [start, end]
    
    if status_filter != "All":
        query += " AND te.status = %s"
        params.append(status_filter)
    
    query += " ORDER BY te.reviewed_at DESC LIMIT 100"
    
    df = execute_df(query, tuple(params))
    
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("📭 No approval history found")

def manage360_team():
    st.subheader("👥 Team Overview")
    
    team = execute_df("""
        SELECT u.id, u.full_name as "Name", u.email as "Email", u.department as "Department",
               COUNT(DISTINCT pa.project_id) as "Projects",
               COALESCE(SUM(CASE WHEN te.entry_date >= CURRENT_DATE - INTERVAL '7 days' THEN te.hours ELSE 0 END), 0) as "Week_Hours"
        FROM users u
        LEFT JOIN project_assignments pa ON u.id = pa.employee_id
        LEFT JOIN time_entries te ON u.id = te.employee_id AND te.status != 'draft'
        WHERE u.role = 'employee' AND u.is_active = TRUE
        GROUP BY u.id, u.full_name, u.email, u.department
        ORDER BY u.full_name
    """)
    
    if not team.empty:
        st.dataframe(team, use_container_width=True, hide_index=True)
        
        overtime_threshold = float(get_setting('overtime_threshold') or 9)
        overtime = execute_df(f"""
            SELECT u.full_name as "Employee", te.entry_date as "Date", 
                   SUM(te.hours + te.minutes/60.0) as "Total_Hours"
            FROM time_entries te
            JOIN users u ON te.employee_id = u.id
            WHERE te.entry_date >= CURRENT_DATE - INTERVAL '7 days' AND te.status != 'draft'
            GROUP BY u.full_name, te.entry_date
            HAVING SUM(te.hours + te.minutes/60.0) > {overtime_threshold}
        """)
        
        if not overtime.empty:
            st.warning(f"⚠️ **Overtime Alerts** (>{overtime_threshold}h/day)")
            st.dataframe(overtime, use_container_width=True, hide_index=True)

def manage360_analytics():
    st.subheader("📊 Team Analytics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = execute_df("""
        SELECT 
            COUNT(DISTINCT employee_id) as employees,
            SUM(CASE WHEN status='submitted' THEN 1 ELSE 0 END) as pending,
            COALESCE(SUM(CASE WHEN is_billable AND status='approved' THEN hours ELSE 0 END), 0) as billable,
            COALESCE(SUM(CASE WHEN status='approved' THEN hours ELSE 0 END), 0) as total
        FROM time_entries
        WHERE entry_date >= CURRENT_DATE - INTERVAL '30 days'
    """)
    
    col1.metric("👥 Active Employees", int(metrics['employees'].iloc[0] or 0))
    col2.metric("📋 Pending Reviews", int(metrics['pending'].iloc[0] or 0))
    col3.metric("💰 Billable (30d)", f"{float(metrics['billable'].iloc[0] or 0):.0f}h")
    total_val = float(metrics['total'].iloc[0] or 0)
    billable_val = float(metrics['billable'].iloc[0] or 0)
    util = (billable_val / total_val * 100) if total_val > 0 else 0
    col4.metric("📈 Utilization", f"{util:.0f}%")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Top Projects (30 Days)")
        proj_data = execute_df("""
            SELECT p.name as "Project", SUM(te.hours) as "Hours"
            FROM time_entries te
            JOIN projects p ON te.project_id = p.id
            WHERE te.entry_date >= CURRENT_DATE - INTERVAL '30 days' AND te.status = 'approved'
            GROUP BY p.id, p.name ORDER BY "Hours" DESC LIMIT 10
        """)
        
        if not proj_data.empty:
            fig = px.bar(proj_data, x='Project', y='Hours', color_discrete_sequence=['#636EFA'])
            fig.update_layout(margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")
    
    with col2:
        st.markdown("##### Top Contributors (30 Days)")
        emp_data = execute_df("""
            SELECT u.full_name as "Employee", SUM(te.hours) as "Hours"
            FROM time_entries te
            JOIN users u ON te.employee_id = u.id
            WHERE te.entry_date >= CURRENT_DATE - INTERVAL '30 days' AND te.status = 'approved'
            GROUP BY u.id, u.full_name ORDER BY "Hours" DESC LIMIT 10
        """)
        
        if not emp_data.empty:
            fig = px.bar(emp_data, x='Employee', y='Hours', color_discrete_sequence=['#00CC96'])
            fig.update_layout(margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")

def manage360_projects():
    st.subheader("📁 Project Management")
    
    with st.expander("➕ Create New Project"):
        clients = execute_df("SELECT id, name FROM clients WHERE is_active=TRUE AND name != 'EE Internal'")
        managers = execute_df("SELECT id, full_name FROM users WHERE role IN ('manager', 'admin') AND is_active=TRUE")
        
        if clients.empty:
            st.warning("⚠️ Create a client first in TechCore")
        else:
            col1, col2 = st.columns(2)
            with col1:
                new_client = st.selectbox("Client", clients['name'].tolist(), key="new_proj_client")
                new_proj_name = st.text_input("Project Name", key="new_proj_name")
            with col2:
                new_manager = st.selectbox("Project Manager", managers['full_name'].tolist(), key="new_proj_mgr")
                new_proj_desc = st.text_input("Description", key="new_proj_desc")
            
            if st.button("Create Project", type="primary"):
                if new_proj_name:
                    client_id = int(clients[clients['name'] == new_client]['id'].values[0])
                    manager_id = int(managers[managers['full_name'] == new_manager]['id'].values[0])
                    conn = get_connection()
                    try:
                        with conn.cursor() as c:
                            c.execute("INSERT INTO projects (client_id, name, description, manager_id) VALUES (%s, %s, %s, %s) RETURNING id",
                                      (client_id, new_proj_name, new_proj_desc, manager_id))
                            proj_id = c.fetchone()[0]
                            conn.commit()
                    finally:
                        release_connection(conn)
                    log_audit(st.session_state.user['id'], "CREATE_PROJECT", "project", proj_id)
                    st.success("✅ Project created!")
                    st.rerun()
    
    projects = execute_df("""
        SELECT p.id, c.name as "Client", p.name as "Project", u.full_name as "Manager",
               p.status as "Status", COUNT(DISTINCT pa.employee_id) as "Team_Size",
               COALESCE(SUM(te.hours), 0) as "Total_Hours"
        FROM projects p
        JOIN clients c ON p.client_id = c.id
        LEFT JOIN users u ON p.manager_id = u.id
        LEFT JOIN project_assignments pa ON p.id = pa.project_id
        LEFT JOIN time_entries te ON p.id = te.project_id AND te.status = 'approved'
        WHERE c.name != 'EE Internal'
        GROUP BY p.id, c.name, p.name, u.full_name, p.status
        ORDER BY p.created_at DESC
    """)
    
    if not projects.empty:
        st.dataframe(projects, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("##### 👤 Assign Employee to Project")
        col1, col2, col3 = st.columns([2, 2, 1])
        
        employees = execute_df("SELECT id, full_name FROM users WHERE role='employee' AND is_active=TRUE")
        
        with col1:
            assign_proj = st.selectbox("Select Project", projects['Project'].tolist())
        with col2:
            if not employees.empty:
                assign_emp = st.selectbox("Select Employee", employees['full_name'].tolist())
            else:
                st.warning("No employees found")
                assign_emp = None
        with col3:
            st.write("")
            st.write("")
            if assign_emp and st.button("Assign", type="primary"):
                proj_id = int(projects[projects['Project'] == assign_proj]['id'].values[0])
                emp_id = int(employees[employees['full_name'] == assign_emp]['id'].values[0])
                conn = get_connection()
                try:
                    with conn.cursor() as c:
                        c.execute("INSERT INTO project_assignments (project_id, employee_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (proj_id, emp_id))
                        conn.commit()
                    st.success(f"✅ Assigned {assign_emp} to {assign_proj}")
                    st.rerun()
                except Exception as e:
                    st.warning(f"Could not assign: {e}")
                finally:
                    release_connection(conn)

# ============== TECHCORE (ADMIN PORTAL) ==============
def techcore_dashboard():
    user = st.session_state.user
    st.title("⚙️ TechCore - Admin Portal")
    st.markdown(f"Welcome, **{user['full_name']}**")
    
    tabs = st.tabs(["👥 Users", "🏢 Clients", "📁 Projects", "📊 Reports", "📤 Export Center", "⚙️ Settings", "📜 Audit Logs"])
    
    with tabs[0]:
        techcore_users()
    with tabs[1]:
        techcore_clients()
    with tabs[2]:
        techcore_projects_admin()
    with tabs[3]:
        techcore_reports()
    with tabs[4]:
        techcore_export_center()
    with tabs[5]:
        techcore_settings()
    with tabs[6]:
        techcore_audit()

def techcore_users():
    st.subheader("👥 User Management")
    
    with st.expander("➕ Add New User", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("Username", key="new_user")
            new_password = st.text_input("Password", type="password", key="new_pass")
            new_email = st.text_input("Email", key="new_email")
        with col2:
            new_fullname = st.text_input("Full Name", key="new_name")
            new_role = st.selectbox("Role", ["employee", "manager", "admin"], key="new_role")
            new_dept = st.text_input("Department", key="new_dept")
        
        if st.button("Create User", type="primary"):
            if new_username and new_password and new_fullname:
                conn = get_connection()
                try:
                    with conn.cursor() as c:
                        c.execute("""INSERT INTO users (username, password_hash, email, full_name, role, department, created_by)
                                     VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                                  (new_username, hash_password(new_password), new_email, new_fullname, 
                                   new_role, new_dept, st.session_state.user['id']))
                        user_id = c.fetchone()[0]
                        conn.commit()
                    log_audit(st.session_state.user['id'], "CREATE_USER", "user", user_id)
                    st.success(f"✅ User '{new_username}' created!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    release_connection(conn)
            else:
                st.warning("⚠️ Username, password, and full name are required")
    
    users = execute_df("""
        SELECT id, username as "Username", full_name as "Name", email as "Email", 
               role as "Role", department as "Department",
               CASE WHEN is_active THEN 'Active' ELSE 'Inactive' END as "Status",
               created_at as "Created"
        FROM users ORDER BY created_at DESC
    """)
    
    st.dataframe(users, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("##### ✏️ Edit User")
    col1, col2 = st.columns(2)
    
    with col1:
        edit_user = st.selectbox("Select User", users['Username'].tolist())
        user_id = int(users[users['Username'] == edit_user]['id'].values[0])
    with col2:
        action = st.selectbox("Action", ["Reset Password", "Toggle Active", "Change Role", "🗑️ Delete User"])
    
    if action == "Reset Password":
        new_pwd = st.text_input("New Password", type="password", key="reset_pwd")
        if st.button("Reset Password"):
            if new_pwd:
                conn = get_connection()
                try:
                    with conn.cursor() as c:
                        c.execute("UPDATE users SET password_hash=%s WHERE id=%s", (hash_password(new_pwd), user_id))
                        conn.commit()
                finally:
                    release_connection(conn)
                log_audit(st.session_state.user['id'], "RESET_PASSWORD", "user", user_id)
                st.success("✅ Password reset!")
    elif action == "Toggle Active":
        if st.button("Toggle Status"):
            conn = get_connection()
            try:
                with conn.cursor() as c:
                    c.execute("UPDATE users SET is_active = NOT is_active WHERE id=%s", (user_id,))
                    conn.commit()
            finally:
                release_connection(conn)
            log_audit(st.session_state.user['id'], "TOGGLE_USER_STATUS", "user", user_id)
            st.success("✅ Status toggled!")
            st.rerun()
    elif action == "Change Role":
        new_role = st.selectbox("New Role", ["employee", "manager", "admin"], key="change_role")
        if st.button("Update Role"):
            conn = get_connection()
            try:
                with conn.cursor() as c:
                    c.execute("UPDATE users SET role=%s WHERE id=%s", (new_role, user_id))
                    conn.commit()
            finally:
                release_connection(conn)
            log_audit(st.session_state.user['id'], "CHANGE_ROLE", "user", user_id, new_role)
            st.success("✅ Role updated!")
            st.rerun()
    elif action == "🗑️ Delete User":
        st.warning(f"⚠️ Permanently delete user: **{edit_user}**")
        if edit_user == "admin":
            st.error("❌ Cannot delete the main admin account!")
        else:
            confirm = st.text_input("Type username to confirm:", key="confirm_delete")
            if st.button("🗑️ Permanently Delete", type="primary"):
                if confirm == edit_user:
                    conn = get_connection()
                    try:
                        with conn.cursor() as c:
                            c.execute("DELETE FROM time_entries WHERE employee_id=%s", (user_id,))
                            c.execute("DELETE FROM project_assignments WHERE employee_id=%s", (user_id,))
                            c.execute("DELETE FROM recall_requests WHERE employee_id=%s", (user_id,))
                            c.execute("DELETE FROM users WHERE id=%s", (user_id,))
                            conn.commit()
                    finally:
                        release_connection(conn)
                    log_audit(st.session_state.user['id'], "DELETE_USER", "user", user_id, edit_user)
                    st.success(f"✅ User '{edit_user}' deleted!")
                    st.rerun()
                else:
                    st.error("Username doesn't match.")

def techcore_clients():
    st.subheader("🏢 Client Management")
    
    with st.expander("➕ Add New Client"):
        col1, col2 = st.columns(2)
        with col1:
            client_name = st.text_input("Client Name", key="client_name")
        with col2:
            client_desc = st.text_input("Description", key="client_desc")
        
        if st.button("Add Client"):
            if client_name:
                conn = get_connection()
                try:
                    with conn.cursor() as c:
                        c.execute("INSERT INTO clients (name, description) VALUES (%s, %s) RETURNING id", (client_name, client_desc))
                        client_id = c.fetchone()[0]
                        conn.commit()
                    log_audit(st.session_state.user['id'], "CREATE_CLIENT", "client", client_id)
                    st.success("✅ Client added!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    release_connection(conn)
    
    clients = execute_df("""
        SELECT c.id, c.name as "Client", c.description as "Description",
               CASE WHEN c.is_active THEN 'Active' ELSE 'Inactive' END as "Status",
               COUNT(DISTINCT p.id) as "Projects",
               COALESCE(SUM(te.hours), 0) as "Total_Hours"
        FROM clients c
        LEFT JOIN projects p ON c.id = p.client_id
        LEFT JOIN time_entries te ON p.id = te.project_id AND te.status = 'approved'
        GROUP BY c.id, c.name, c.description, c.is_active
        ORDER BY c.name
    """)
    
    st.dataframe(clients, use_container_width=True, hide_index=True)
    
    if not clients.empty:
        st.markdown("---")
        st.markdown("##### ✏️ Manage Client")
        col1, col2 = st.columns(2)
        
        with col1:
            selected_client = st.selectbox("Select Client", clients['Client'].tolist())
            client_id = int(clients[clients['Client'] == selected_client]['id'].values[0])
        with col2:
            client_action = st.selectbox("Action", ["Toggle Active", "🗑️ Delete Client"], key="client_action")
        
        if client_action == "Toggle Active":
            if st.button("Toggle Client Status"):
                conn = get_connection()
                try:
                    with conn.cursor() as c:
                        c.execute("UPDATE clients SET is_active = NOT is_active WHERE id=%s", (client_id,))
                        conn.commit()
                finally:
                    release_connection(conn)
                st.success("✅ Status toggled!")
                st.rerun()
        
        elif client_action == "🗑️ Delete Client":
            st.warning(f"⚠️ Permanently delete client: **{selected_client}**")
            confirm = st.text_input("Type client name to confirm:", key="confirm_delete_client")
            if st.button("🗑️ Permanently Delete Client", type="primary"):
                if confirm == selected_client:
                    conn = get_connection()
                    try:
                        with conn.cursor() as c:
                            c.execute("SELECT id FROM projects WHERE client_id=%s", (client_id,))
                            project_ids = [row[0] for row in c.fetchall()]
                            for pid in project_ids:
                                c.execute("DELETE FROM time_entries WHERE project_id=%s", (pid,))
                                c.execute("DELETE FROM project_assignments WHERE project_id=%s", (pid,))
                            c.execute("DELETE FROM projects WHERE client_id=%s", (client_id,))
                            c.execute("DELETE FROM clients WHERE id=%s", (client_id,))
                            conn.commit()
                    finally:
                        release_connection(conn)
                    log_audit(st.session_state.user['id'], "DELETE_CLIENT", "client", client_id)
                    st.success(f"✅ Client '{selected_client}' deleted!")
                    st.rerun()
                else:
                    st.error("Client name doesn't match.")

def techcore_projects_admin():
    st.subheader("📁 All Projects")
    
    projects = execute_df("""
        SELECT p.id, c.name as "Client", p.name as "Project", u.full_name as "Manager",
               p.status as "Status", p.created_at as "Created",
               COUNT(DISTINCT pa.employee_id) as "Team",
               COALESCE(SUM(te.hours), 0) as "Hours"
        FROM projects p
        JOIN clients c ON p.client_id = c.id
        LEFT JOIN users u ON p.manager_id = u.id
        LEFT JOIN project_assignments pa ON p.id = pa.project_id
        LEFT JOIN time_entries te ON p.id = te.project_id AND te.status = 'approved'
        GROUP BY p.id, c.name, p.name, u.full_name, p.status, p.created_at
        ORDER BY p.created_at DESC
    """)
    
    st.dataframe(projects, use_container_width=True, hide_index=True)
    
    if not projects.empty:
        st.markdown("---")
        st.markdown("##### ✏️ Manage Project")
        col1, col2 = st.columns(2)
        
        with col1:
            sel_proj = st.selectbox("Select Project", projects['Project'].tolist())
            proj_id = int(projects[projects['Project'] == sel_proj]['id'].values[0])
        with col2:
            proj_action = st.selectbox("Action", ["Update Status", "🗑️ Delete Project"], key="proj_action")
        
        if proj_action == "Update Status":
            new_status = st.selectbox("New Status", ["active", "on_hold", "completed", "cancelled"])
            if st.button("Update Status"):
                conn = get_connection()
                try:
                    with conn.cursor() as c:
                        c.execute("UPDATE projects SET status=%s WHERE id=%s", (new_status, proj_id))
                        conn.commit()
                finally:
                    release_connection(conn)
                st.success("✅ Status updated!")
                st.rerun()
        
        elif proj_action == "🗑️ Delete Project":
            st.warning(f"⚠️ Permanently delete project: **{sel_proj}**")
            confirm = st.text_input("Type project name to confirm:", key="confirm_delete_proj")
            if st.button("🗑️ Permanently Delete Project", type="primary"):
                if confirm == sel_proj:
                    conn = get_connection()
                    try:
                        with conn.cursor() as c:
                            c.execute("DELETE FROM time_entries WHERE project_id=%s", (proj_id,))
                            c.execute("DELETE FROM project_assignments WHERE project_id=%s", (proj_id,))
                            c.execute("DELETE FROM projects WHERE id=%s", (proj_id,))
                            conn.commit()
                    finally:
                        release_connection(conn)
                    log_audit(st.session_state.user['id'], "DELETE_PROJECT", "project", proj_id)
                    st.success(f"✅ Project '{sel_proj}' deleted!")
                    st.rerun()
                else:
                    st.error("Project name doesn't match.")

def techcore_reports():
    st.subheader("📊 System Reports")
    
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("From", datetime.date.today() - timedelta(days=30), key="rep_start")
    with col2:
        end = st.date_input("To", datetime.date.today(), key="rep_end")
    
    report_type = st.selectbox("Report Type", [
        "Employee Hours Summary",
        "Project Hours Summary", 
        "Client Hours Summary",
        "EE Internal Summary",
        "Utilization Report"
    ])
    
    if st.button("Generate Report", type="primary"):
        if report_type == "Employee Hours Summary":
            df = execute_df("""
                SELECT u.full_name as "Employee", u.department as "Department",
                       COALESCE(SUM(te.hours), 0) as "Total_Hours",
                       COALESCE(SUM(CASE WHEN te.is_billable THEN te.hours ELSE 0 END), 0) as "Billable_Hours",
                       COUNT(*) as "Entries"
                FROM time_entries te
                JOIN users u ON te.employee_id = u.id
                WHERE te.entry_date BETWEEN %s AND %s AND te.status = 'approved'
                GROUP BY u.id, u.full_name, u.department ORDER BY "Total_Hours" DESC
            """, (start, end))
        
        elif report_type == "Project Hours Summary":
            df = execute_df("""
                SELECT c.name as "Client", p.name as "Project", u.full_name as "Manager",
                       COALESCE(SUM(te.hours), 0) as "Total_Hours", COUNT(DISTINCT te.employee_id) as "Contributors"
                FROM time_entries te
                JOIN projects p ON te.project_id = p.id
                JOIN clients c ON p.client_id = c.id
                LEFT JOIN users u ON p.manager_id = u.id
                WHERE te.entry_date BETWEEN %s AND %s AND te.status = 'approved'
                GROUP BY p.id, c.name, p.name, u.full_name ORDER BY "Total_Hours" DESC
            """, (start, end))
        
        elif report_type == "Client Hours Summary":
            df = execute_df("""
                SELECT c.name as "Client", COUNT(DISTINCT p.id) as "Projects",
                       COALESCE(SUM(te.hours), 0) as "Total_Hours",
                       COALESCE(SUM(CASE WHEN te.is_billable THEN te.hours ELSE 0 END), 0) as "Billable_Hours"
                FROM time_entries te
                JOIN projects p ON te.project_id = p.id
                JOIN clients c ON p.client_id = c.id
                WHERE te.entry_date BETWEEN %s AND %s AND te.status = 'approved'
                GROUP BY c.id, c.name ORDER BY "Total_Hours" DESC
            """, (start, end))
        
        elif report_type == "EE Internal Summary":
            df = execute_df("""
                SELECT u.full_name as "Employee", te.entry_category as "Category",
                       te.task_type as "Type", COALESCE(SUM(te.hours), 0) as "Total_Hours",
                       COUNT(*) as "Entries"
                FROM time_entries te
                JOIN users u ON te.employee_id = u.id
                WHERE te.entry_date BETWEEN %s AND %s AND te.status = 'approved' AND te.entry_type = 'ee_internal'
                GROUP BY u.id, u.full_name, te.entry_category, te.task_type ORDER BY "Total_Hours" DESC
            """, (start, end))
        
        else:  # Utilization Report
            df = execute_df("""
                SELECT u.full_name as "Employee", u.department as "Department",
                       COALESCE(SUM(te.hours), 0) as "Total_Hours",
                       COALESCE(SUM(CASE WHEN te.is_billable THEN te.hours ELSE 0 END), 0) as "Billable",
                       ROUND(COALESCE(SUM(CASE WHEN te.is_billable THEN te.hours ELSE 0 END), 0) * 100.0 / 
                             NULLIF(SUM(te.hours), 0), 1) as "Utilization_Pct"
                FROM time_entries te
                JOIN users u ON te.employee_id = u.id
                WHERE te.entry_date BETWEEN %s AND %s AND te.status = 'approved'
                GROUP BY u.id, u.full_name, u.department ORDER BY "Utilization_Pct" DESC
            """, (start, end))
        
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False)
            st.download_button("📥 Download CSV", csv, f"{report_type.replace(' ', '_')}.csv", "text/csv")
        else:
            st.info("📭 No data found")

def techcore_export_center():
    st.subheader("📤 Export Center")
    
    col1, col2 = st.columns(2)
    with col1:
        export_start = st.date_input("From Date", datetime.date.today() - timedelta(days=30), key="export_start")
    with col2:
        export_end = st.date_input("To Date", datetime.date.today(), key="export_end")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📋 Time Entries")
        if st.button("📥 Export All Time Entries", use_container_width=True):
            df = execute_df("""
                SELECT te.id as "Entry_ID", u.full_name as "Employee", u.department as "Department",
                       COALESCE(c.name, 'EE Internal') as "Client", COALESCE(p.name, te.entry_category) as "Project",
                       te.entry_date as "Date", te.hours as "Hours", te.minutes as "Minutes",
                       te.task_type as "Task_Type", te.entry_type as "Entry_Type",
                       CASE WHEN te.is_billable THEN 'Yes' ELSE 'No' END as "Billable",
                       te.status as "Status", te.description as "Description",
                       te.submitted_at as "Submitted_At", r.full_name as "Reviewed_By"
                FROM time_entries te
                JOIN users u ON te.employee_id = u.id
                LEFT JOIN projects p ON te.project_id = p.id
                LEFT JOIN clients c ON p.client_id = c.id
                LEFT JOIN users r ON te.reviewed_by = r.id
                WHERE te.entry_date BETWEEN %s AND %s
                ORDER BY te.entry_date DESC
            """, (export_start, export_end))
            
            if not df.empty:
                csv = df.to_csv(index=False)
                timestamp = get_local_time().strftime('%Y%m%d_%H%M%S')
                st.download_button("⬇️ Download CSV", csv, f"time_entries_{timestamp}.csv", "text/csv", key="dl_entries")
                st.success(f"✅ {len(df)} entries ready!")
            else:
                st.warning("No data found")
        
        if st.button("📥 Export Approved Only", use_container_width=True):
            df = execute_df("""
                SELECT u.full_name as "Employee", COALESCE(c.name, 'EE Internal') as "Client",
                       COALESCE(p.name, te.entry_category) as "Project", te.entry_date as "Date",
                       te.hours as "Hours", te.task_type as "Task",
                       CASE WHEN te.is_billable THEN 'Yes' ELSE 'No' END as "Billable"
                FROM time_entries te
                JOIN users u ON te.employee_id = u.id
                LEFT JOIN projects p ON te.project_id = p.id
                LEFT JOIN clients c ON p.client_id = c.id
                WHERE te.entry_date BETWEEN %s AND %s AND te.status = 'approved'
                ORDER BY te.entry_date DESC
            """, (export_start, export_end))
            
            if not df.empty:
                csv = df.to_csv(index=False)
                timestamp = get_local_time().strftime('%Y%m%d_%H%M%S')
                st.download_button("⬇️ Download CSV", csv, f"approved_entries_{timestamp}.csv", "text/csv", key="dl_approved")
                st.success(f"✅ {len(df)} entries ready!")
            else:
                st.warning("No data found")
    
    with col2:
        st.markdown("##### 👥 Users & Projects")
        if st.button("📥 Export All Users", use_container_width=True):
            df = execute_df("""
                SELECT id as "ID", username as "Username", full_name as "Full_Name",
                       email as "Email", role as "Role", department as "Department",
                       CASE WHEN is_active THEN 'Active' ELSE 'Inactive' END as "Status"
                FROM users ORDER BY full_name
            """)
            if not df.empty:
                csv = df.to_csv(index=False)
                st.download_button("⬇️ Download CSV", csv, "users_list.csv", "text/csv", key="dl_users")
                st.success(f"✅ {len(df)} users ready!")
        
        if st.button("📥 Export Projects & Teams", use_container_width=True):
            df = execute_df("""
                SELECT c.name as "Client", p.name as "Project", p.status as "Status",
                       m.full_name as "Manager", u.full_name as "Team_Member"
                FROM projects p
                JOIN clients c ON p.client_id = c.id
                LEFT JOIN users m ON p.manager_id = m.id
                LEFT JOIN project_assignments pa ON p.id = pa.project_id
                LEFT JOIN users u ON pa.employee_id = u.id
                ORDER BY c.name, p.name
            """)
            if not df.empty:
                csv = df.to_csv(index=False)
                st.download_button("⬇️ Download CSV", csv, "projects_teams.csv", "text/csv", key="dl_projects")
                st.success(f"✅ {len(df)} records ready!")
    
    st.markdown("---")
    st.markdown("##### 📦 Full Database Backup")
    
    if st.button("📥 Export Complete Backup (Excel)", use_container_width=True, type="primary"):
        try:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                execute_df("SELECT * FROM users").to_excel(writer, sheet_name='Users', index=False)
                execute_df("SELECT * FROM clients").to_excel(writer, sheet_name='Clients', index=False)
                execute_df("SELECT * FROM projects").to_excel(writer, sheet_name='Projects', index=False)
                execute_df("SELECT * FROM project_assignments").to_excel(writer, sheet_name='Assignments', index=False)
                execute_df("SELECT * FROM time_entries").to_excel(writer, sheet_name='Time_Entries', index=False)
                execute_df("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 5000").to_excel(writer, sheet_name='Audit_Logs', index=False)
            output.seek(0)
            timestamp = get_local_time().strftime('%Y%m%d_%H%M%S')
            st.download_button("⬇️ Download Excel Backup", output, f"backup_{timestamp}.xlsx",
                              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_backup")
            st.success("✅ Backup ready!")
            log_audit(st.session_state.user['id'], "EXPORT_BACKUP", "system", None)
        except Exception as e:
            st.error(f"Error: {e}")
            st.info("Install openpyxl: pip install openpyxl")

def techcore_settings():
    st.subheader("⚙️ System Settings")
    
    settings_data = execute_query("SELECT key, value FROM settings")
    settings_dict = {s['key']: s['value'] for s in settings_data}
    
    col1, col2 = st.columns(2)
    
    with col1:
        company = st.text_input("Company Name", value=settings_dict.get('company_name', ''))
        recall_hrs = st.number_input("Recall Window (hours)", value=int(settings_dict.get('recall_window_hours', 24)), min_value=1, max_value=72)
    
    with col2:
        overtime = st.number_input("Overtime Threshold (hours/day)", value=float(settings_dict.get('overtime_threshold', 9)), min_value=1.0, max_value=24.0)
        week_start = st.selectbox("Work Week Starts", ["Monday", "Sunday"], 
                                  index=0 if settings_dict.get('work_week_start', 'Monday') == 'Monday' else 1)
    
    if st.button("💾 Save Settings", type="primary"):
        conn = get_connection()
        try:
            local_time = get_local_time()
            with conn.cursor() as c:
                c.execute("UPDATE settings SET value=%s, updated_at=%s WHERE key='company_name'", (company, local_time))
                c.execute("UPDATE settings SET value=%s, updated_at=%s WHERE key='recall_window_hours'", (str(recall_hrs), local_time))
                c.execute("UPDATE settings SET value=%s, updated_at=%s WHERE key='overtime_threshold'", (str(overtime), local_time))
                c.execute("UPDATE settings SET value=%s, updated_at=%s WHERE key='work_week_start'", (week_start, local_time))
                conn.commit()
        finally:
            release_connection(conn)
        log_audit(st.session_state.user['id'], "UPDATE_SETTINGS", "settings", None)
        st.success("✅ Settings saved!")
        st.rerun()
    
    st.markdown("---")
    st.markdown("##### 📊 Database Statistics")
    
    stats = {}
    for table in ['users', 'clients', 'projects', 'time_entries', 'audit_logs']:
        result = execute_query(f"SELECT COUNT(*) as count FROM {table}")
        stats[table] = result[0]['count'] if result else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Users", stats['users'])
    col2.metric("Clients", stats['clients'])
    col3.metric("Projects", stats['projects'])
    col4.metric("Time Entries", stats['time_entries'])
    col5.metric("Audit Logs", stats['audit_logs'])
    
    st.markdown("---")
    st.info(f"🕐 **Server Time:** {get_local_time().strftime('%Y-%m-%d %H:%M:%S')} (Africa/Lagos - WAT)")

def techcore_audit():
    st.subheader("📜 Audit Logs")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        start = st.date_input("From", datetime.date.today() - timedelta(days=7), key="audit_start")
    with col2:
        end = st.date_input("To", datetime.date.today(), key="audit_end")
    with col3:
        action_filter = st.text_input("Filter Action", placeholder="e.g., LOGIN")
    
    query = """
        SELECT al.id, u.username as "User", al.action as "Action", 
               al.entity_type as "Entity", al.entity_id as "Entity_ID",
               al.details as "Details", al.created_at as "Timestamp"
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        WHERE DATE(al.created_at) BETWEEN %s AND %s
    """
    params = [start, end]
    
    if action_filter:
        query += " AND al.action ILIKE %s"
        params.append(f"%{action_filter}%")
    
    query += " ORDER BY al.created_at DESC LIMIT 500"
    
    logs = execute_df(query, tuple(params))
    
    st.info(f"📋 Showing {len(logs)} records")
    st.dataframe(logs, use_container_width=True, hide_index=True)
    
    if not logs.empty:
        csv = logs.to_csv(index=False)
        st.download_button("📥 Download Audit Log", csv, "audit_log.csv", "text/csv")

# ============== MAIN APPLICATION ==============
def main():
    st.set_page_config(
        page_title="Execution Edge Timesheet",
        page_icon="🧭",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for dark/light mode compatibility
    st.markdown("""
    <style>
    /* Works in both dark and light mode */
    .stApp {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 500;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 1rem;
    }
    
    /* Data frames */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
    }
    
    /* Info/Warning/Error boxes */
    .stAlert {
        border-radius: 8px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        padding-top: 1rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize database
    init_database()
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if not st.session_state.logged_in:
        login_page()
        return
    
    user = st.session_state.user
    
    # Sidebar
    with st.sidebar:
        company_name = get_setting('company_name') or 'Execution Edge'
        st.markdown(f"### 🧭 {company_name}")
        st.markdown(f"**{user['full_name']}**")
        st.caption(f"Role: {user['role'].title()}")
        
        st.markdown("---")
        
        # Portal navigation
        if user['role'] == 'admin':
            portal = st.radio("📍 Portal", ["🧭 WorkHub", "🧮 Manage360", "⚙️ TechCore"], label_visibility="collapsed")
        elif user['role'] == 'manager':
            portal = st.radio("📍 Portal", ["🧭 WorkHub", "🧮 Manage360"], label_visibility="collapsed")
        else:
            portal = "🧭 WorkHub"
            st.info("📍 WorkHub")
        
        st.markdown("---")
        
        # Recall window info
        recall_window = get_setting('recall_window_hours') or '24'
        st.caption(f"⏰ Recall Window: {recall_window}h")
        st.caption(f"🕐 {get_local_time().strftime('%H:%M:%S')} WAT")
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            log_audit(user['id'], "LOGOUT", "user", user['id'])
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
    
    # Route to appropriate portal
    if "TechCore" in portal:
        techcore_dashboard()
    elif "Manage360" in portal:
        manage360_dashboard()
    else:
        workhub_dashboard()

if __name__ == "__main__":
    main()










