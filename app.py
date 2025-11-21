"""
Execution Edge Timesheet Management System
Production-Ready with PostgreSQL for Multi-User Deployment
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

# ============== DATABASE CONFIGURATION ==============
# Set these in Streamlit Cloud Secrets or environment variables
# Create a .streamlit/secrets.toml file locally:
# [database]
# host = "your-host.supabase.co"
# database = "postgres"
# user = "postgres"
# password = "your-password"
# port = "5432"

@st.cache_resource
def init_connection_pool():
    """Create a connection pool for PostgreSQL"""
    try:
        # Try Streamlit secrets first
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
    """Get a connection from the pool"""
    pool = init_connection_pool()
    return pool.getconn()

def release_connection(conn):
    """Return connection to pool"""
    pool = init_connection_pool()
    pool.putconn(conn)

def execute_query(query, params=None, fetch=True):
    """Execute a query and return results"""
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
    """Execute query and return DataFrame"""
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        release_connection(conn)

def init_database():
    """Initialize database tables"""
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
                project_id INTEGER NOT NULL REFERENCES projects(id),
                entry_date DATE NOT NULL,
                hours REAL NOT NULL,
                minutes INTEGER DEFAULT 0,
                description TEXT,
                task_type VARCHAR(50),
                is_billable BOOLEAN DEFAULT TRUE,
                status VARCHAR(20) DEFAULT 'draft' CHECK(status IN ('draft', 'submitted', 'approved', 'rejected', 'recalled')),
                submitted_at TIMESTAMP,
                reviewed_by INTEGER REFERENCES users(id),
                reviewed_at TIMESTAMP,
                review_comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
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
            c.execute("""INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details) 
                         VALUES (%s, %s, %s, %s, %s)""", (user_id, action, entity_type, entity_id, details))
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
    st.markdown("""
    <style>
    .login-box {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"## 🧭 {get_setting('company_name') or 'Execution Edge'}")
        st.markdown("### Timesheet Management System")
        st.markdown("---")
        
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        
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
                    st.error("Invalid credentials")
            else:
                st.warning("Please enter username and password")
        
        st.markdown("---")
        st.caption("Default admin: admin / admin123")

# ============== WORKHUB (EMPLOYEE PORTAL) ==============
def workhub_dashboard():
    user = st.session_state.user
    st.title("🧭 WorkHub - Employee Portal")
    st.markdown(f"Welcome, **{user['full_name']}**")
    
    tabs = st.tabs(["📝 Time Entry", "📊 My Dashboard", "🔄 Recall Requests", "📋 My History"])
    
    with tabs[0]:
        workhub_time_entry()
    with tabs[1]:
        workhub_analytics()
    with tabs[2]:
        workhub_recalls()
    with tabs[3]:
        workhub_history()

def workhub_time_entry():
    user = st.session_state.user
    
    st.subheader("Log Time Entry")
    
    projects_df = execute_df("""
        SELECT p.id, p.name as project_name, c.name as client_name, c.id as client_id
        FROM projects p
        JOIN clients c ON p.client_id = c.id
        JOIN project_assignments pa ON p.id = pa.project_id
        WHERE pa.employee_id = %s AND p.status = 'active'
    """, (user['id'],))
    
    if projects_df.empty:
        st.warning("You have no projects assigned. Contact your manager.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        clients = projects_df['client_name'].unique().tolist()
        selected_client = st.selectbox("Client", clients)
        
        client_projects = projects_df[projects_df['client_name'] == selected_client]
        selected_project = st.selectbox("Project", client_projects['project_name'].tolist())
        
        project_id = int(client_projects[client_projects['project_name'] == selected_project]['id'].values[0])
    
    with col2:
        entry_date = st.date_input("Date", datetime.date.today())
        
        hcol1, hcol2 = st.columns(2)
        with hcol1:
            hours = st.number_input("Hours", min_value=0, max_value=24, value=8)
        with hcol2:
            minutes = st.selectbox("Minutes", [0, 15, 30, 45])
    
    task_type = st.selectbox("Task Type", ["Development", "Meeting", "Documentation", "Testing", "Support", "Training", "Other"])
    is_billable = st.checkbox("Billable", value=True)
    description = st.text_area("Description", placeholder="What did you work on?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Draft", use_container_width=True):
            save_time_entry(user['id'], project_id, entry_date, hours, minutes, description, task_type, is_billable, 'draft')
            st.success("Draft saved!")
            st.rerun()
    
    with col2:
        if st.button("📤 Submit", use_container_width=True, type="primary"):
            save_time_entry(user['id'], project_id, entry_date, hours, minutes, description, task_type, is_billable, 'submitted')
            st.success("Entry submitted for approval!")
            st.rerun()
    
    st.markdown("---")
    st.subheader("Today's Entries")
    show_entries_table(user['id'], entry_date)

def save_time_entry(employee_id, project_id, entry_date, hours, minutes, description, task_type, is_billable, status):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            submitted_at = datetime.datetime.now() if status == 'submitted' else None
            c.execute("""INSERT INTO time_entries (employee_id, project_id, entry_date, hours, minutes, description, task_type, is_billable, status, submitted_at)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                      (employee_id, project_id, entry_date, hours, minutes, description, task_type, is_billable, status, submitted_at))
            entry_id = c.fetchone()[0]
            conn.commit()
            log_audit(employee_id, f"TIME_ENTRY_{status.upper()}", "time_entry", entry_id)
    finally:
        release_connection(conn)

def show_entries_table(employee_id, date=None):
    query = """
        SELECT te.id, c.name as "Client", p.name as "Project", te.entry_date as "Date",
               te.hours as "Hours", te.minutes as "Mins", te.task_type as "Task",
               CASE WHEN te.is_billable THEN 'Yes' ELSE 'No' END as "Billable",
               te.status as "Status", te.description as "Description"
        FROM time_entries te
        JOIN projects p ON te.project_id = p.id
        JOIN clients c ON p.client_id = c.id
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
        st.info("No entries found")

def workhub_analytics():
    user = st.session_state.user
    
    st.subheader("My Analytics")
    
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
    
    col1, col2, col3 = st.columns(3)
    total_h = float(summary['total_hours'].iloc[0] or 0)
    billable_h = float(summary['billable_hours'].iloc[0] or 0)
    
    col1.metric("This Week Total", f"{total_h:.1f} hrs")
    col2.metric("Billable Hours", f"{billable_h:.1f} hrs")
    col3.metric("Utilization", f"{(billable_h/total_h*100) if total_h > 0 else 0:.0f}%")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pie_data = execute_df("""
            SELECT 
                CASE WHEN is_billable THEN 'Billable' ELSE 'Non-Billable' END as "Type",
                SUM(hours + minutes/60.0) as "Hours"
            FROM time_entries
            WHERE employee_id = %s AND entry_date >= CURRENT_DATE - INTERVAL '30 days' AND status != 'draft'
            GROUP BY is_billable
        """, (user['id'],))
        
        if not pie_data.empty:
            fig = px.pie(pie_data, values='Hours', names='Type', title='Last 30 Days - Billable vs Non-Billable')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        daily_data = execute_df("""
            SELECT entry_date as "Date", SUM(hours + minutes/60.0) as "Hours"
            FROM time_entries
            WHERE employee_id = %s AND entry_date >= CURRENT_DATE - INTERVAL '14 days' AND status != 'draft'
            GROUP BY entry_date ORDER BY entry_date
        """, (user['id'],))
        
        if not daily_data.empty:
            fig = px.bar(daily_data, x='Date', y='Hours', title='Last 14 Days - Daily Hours')
            fig.add_hline(y=8, line_dash="dash", line_color="red", annotation_text="Target")
            st.plotly_chart(fig, use_container_width=True)

def workhub_recalls():
    user = st.session_state.user
    
    st.subheader("Recall Requests")
    
    recall_window = int(get_setting('recall_window_hours') or 24)
    cutoff = datetime.datetime.now() - timedelta(hours=recall_window)
    
    recallable = execute_df("""
        SELECT te.id, c.name as "Client", p.name as "Project", te.entry_date as "Date",
               te.hours as "Hours", te.status as "Status", te.submitted_at
        FROM time_entries te
        JOIN projects p ON te.project_id = p.id
        JOIN clients c ON p.client_id = c.id
        WHERE te.employee_id = %s AND te.status = 'submitted' AND te.submitted_at > %s
    """, (user['id'], cutoff))
    
    if not recallable.empty:
        st.markdown("**Entries eligible for recall:**")
        for _, row in recallable.iterrows():
            col1, col2 = st.columns([4, 1])
            col1.write(f"{row['Date']} | {row['Client']} - {row['Project']} | {row['Hours']}h")
            if col2.button("🔄 Recall", key=f"recall_{row['id']}"):
                conn = get_connection()
                try:
                    with conn.cursor() as c:
                        c.execute("UPDATE time_entries SET status='recalled' WHERE id=%s", (row['id'],))
                        conn.commit()
                finally:
                    release_connection(conn)
                log_audit(user['id'], "RECALL_ENTRY", "time_entry", row['id'])
                st.success("Entry recalled!")
                st.rerun()
    else:
        st.info(f"No entries eligible for recall. Recall window is {recall_window} hours.")
    
    st.markdown("---")
    st.markdown("**My Recall Requests:**")
    requests = execute_df("""
        SELECT rr.id, te.entry_date, rr.reason, rr.status, rr.requested_at
        FROM recall_requests rr
        JOIN time_entries te ON rr.time_entry_id = te.id
        WHERE rr.employee_id = %s
        ORDER BY rr.requested_at DESC LIMIT 10
    """, (user['id'],))
    
    if not requests.empty:
        st.dataframe(requests, use_container_width=True, hide_index=True)
    else:
        st.info("No recall requests")

def workhub_history():
    user = st.session_state.user
    st.subheader("My Time Entry History")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", datetime.date.today() - timedelta(days=30), key="hist_start")
    with col2:
        end_date = st.date_input("To", datetime.date.today(), key="hist_end")
    
    df = execute_df("""
        SELECT te.entry_date as "Date", c.name as "Client", p.name as "Project",
               te.hours as "Hours", te.minutes as "Mins", te.task_type as "Task",
               CASE WHEN te.is_billable THEN 'Yes' ELSE 'No' END as "Billable",
               te.status as "Status", te.review_comment as "Comment"
        FROM time_entries te
        JOIN projects p ON te.project_id = p.id
        JOIN clients c ON p.client_id = c.id
        WHERE te.employee_id = %s AND te.entry_date BETWEEN %s AND %s
        ORDER BY te.entry_date DESC
    """, (user['id'], start_date, end_date))
    
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False)
        st.download_button("📥 Download CSV", csv, "my_timesheet.csv", "text/csv")
    else:
        st.info("No entries found for selected period")

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
    
    st.subheader("Pending Reviews")
    
    pending = execute_df("""
        SELECT te.id, u.full_name as "Employee", c.name as "Client", p.name as "Project",
               te.entry_date as "Date", te.hours as "Hours", te.minutes as "Mins",
               te.task_type as "Task", te.description as "Description",
               CASE WHEN te.is_billable THEN 'Yes' ELSE 'No' END as "Billable",
               te.submitted_at as "Submitted"
        FROM time_entries te
        JOIN users u ON te.employee_id = u.id
        JOIN projects p ON te.project_id = p.id
        JOIN clients c ON p.client_id = c.id
        WHERE te.status = 'submitted' 
        AND (p.manager_id = %s OR %s IN (SELECT id FROM users WHERE role IN ('manager', 'admin')))
        ORDER BY te.submitted_at ASC
    """, (user['id'], user['id']))
    
    if pending.empty:
        st.success("🎉 No pending reviews!")
        return
    
    st.info(f"**{len(pending)}** entries awaiting review")
    
    for _, row in pending.iterrows():
        with st.expander(f"📝 {row['Employee']} | {row['Date']} | {row['Project']} ({row['Hours']}h {row['Mins']}m)"):
            col1, col2 = st.columns(2)
            col1.write(f"**Client:** {row['Client']}")
            col1.write(f"**Task:** {row['Task']}")
            col2.write(f"**Billable:** {row['Billable']}")
            col2.write(f"**Submitted:** {row['Submitted']}")
            st.write(f"**Description:** {row['Description'] or 'N/A'}")
            
            comment = st.text_input("Comment (optional)", key=f"comment_{row['id']}")
            
            col1, col2, col3 = st.columns(3)
            if col1.button("✅ Approve", key=f"approve_{row['id']}", type="primary"):
                update_entry_status(row['id'], 'approved', user['id'], comment)
                st.success("Approved!")
                st.rerun()
            if col2.button("❌ Reject", key=f"reject_{row['id']}"):
                update_entry_status(row['id'], 'rejected', user['id'], comment)
                st.warning("Rejected")
                st.rerun()

def update_entry_status(entry_id, status, reviewer_id, comment=None):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("""UPDATE time_entries SET status=%s, reviewed_by=%s, reviewed_at=%s, review_comment=%s
                         WHERE id=%s""", (status, reviewer_id, datetime.datetime.now(), comment, entry_id))
            conn.commit()
    finally:
        release_connection(conn)
    log_audit(reviewer_id, f"ENTRY_{status.upper()}", "time_entry", entry_id, comment)

def manage360_approvals():
    st.subheader("Approval History")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "approved", "rejected"])
    with col2:
        start = st.date_input("From", datetime.date.today() - timedelta(days=30), key="appr_start")
    with col3:
        end = st.date_input("To", datetime.date.today(), key="appr_end")
    
    query = """
        SELECT te.id, u.full_name as "Employee", p.name as "Project", te.entry_date as "Date",
               te.hours as "Hours", te.status as "Status", r.full_name as "Reviewer",
               te.reviewed_at as "Reviewed", te.review_comment as "Comment"
        FROM time_entries te
        JOIN users u ON te.employee_id = u.id
        JOIN projects p ON te.project_id = p.id
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
        st.info("No approval history found")

def manage360_team():
    st.subheader("Team Overview")
    
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
            st.warning(f"⚠️ Overtime Alerts (>{overtime_threshold}h/day)")
            st.dataframe(overtime, use_container_width=True, hide_index=True)

def manage360_analytics():
    st.subheader("Team Analytics")
    
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
    
    col1.metric("Active Employees", int(metrics['employees'].iloc[0] or 0))
    col2.metric("Pending Reviews", int(metrics['pending'].iloc[0] or 0))
    col3.metric("Billable Hours (30d)", f"{float(metrics['billable'].iloc[0] or 0):.0f}h")
    total_val = float(metrics['total'].iloc[0] or 0)
    billable_val = float(metrics['billable'].iloc[0] or 0)
    util = (billable_val / total_val * 100) if total_val > 0 else 0
    col4.metric("Utilization", f"{util:.0f}%")
    
    col1, col2 = st.columns(2)
    
    with col1:
        proj_data = execute_df("""
            SELECT p.name as "Project", SUM(te.hours) as "Hours"
            FROM time_entries te
            JOIN projects p ON te.project_id = p.id
            WHERE te.entry_date >= CURRENT_DATE - INTERVAL '30 days' AND te.status = 'approved'
            GROUP BY p.id, p.name ORDER BY "Hours" DESC LIMIT 10
        """)
        
        if not proj_data.empty:
            fig = px.bar(proj_data, x='Project', y='Hours', title='Top Projects (30 Days)')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        emp_data = execute_df("""
            SELECT u.full_name as "Employee", SUM(te.hours) as "Hours"
            FROM time_entries te
            JOIN users u ON te.employee_id = u.id
            WHERE te.entry_date >= CURRENT_DATE - INTERVAL '30 days' AND te.status = 'approved'
            GROUP BY u.id, u.full_name ORDER BY "Hours" DESC LIMIT 10
        """)
        
        if not emp_data.empty:
            fig = px.bar(emp_data, x='Employee', y='Hours', title='Top Contributors (30 Days)')
            st.plotly_chart(fig, use_container_width=True)

def manage360_projects():
    st.subheader("Project Management")
    
    with st.expander("➕ Create New Project"):
        clients = execute_df("SELECT id, name FROM clients WHERE is_active=TRUE")
        managers = execute_df("SELECT id, full_name FROM users WHERE role IN ('manager', 'admin') AND is_active=TRUE")
        
        if clients.empty:
            st.warning("Create a client first in TechCore")
        else:
            col1, col2 = st.columns(2)
            with col1:
                new_client = st.selectbox("Client", clients['name'].tolist(), key="new_proj_client")
                new_proj_name = st.text_input("Project Name", key="new_proj_name")
            with col2:
                new_manager = st.selectbox("Project Manager", managers['full_name'].tolist(), key="new_proj_mgr")
                new_proj_desc = st.text_input("Description", key="new_proj_desc")
            
            if st.button("Create Project"):
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
                    st.success("Project created!")
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
        GROUP BY p.id, c.name, p.name, u.full_name, p.status
        ORDER BY p.created_at DESC
    """)
    
    if not projects.empty:
        st.dataframe(projects, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("**Assign Employee to Project**")
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
            if assign_emp and st.button("Assign"):
                proj_id = int(projects[projects['Project'] == assign_proj]['id'].values[0])
                emp_id = int(employees[employees['full_name'] == assign_emp]['id'].values[0])
                conn = get_connection()
                try:
                    with conn.cursor() as c:
                        c.execute("INSERT INTO project_assignments (project_id, employee_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (proj_id, emp_id))
                        conn.commit()
                    st.success(f"Assigned {assign_emp} to {assign_proj}")
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
    
    tabs = st.tabs(["👥 Users", "🏢 Clients", "📁 Projects", "📊 Reports", "⚙️ Settings", "📜 Audit Logs"])
    
    with tabs[0]:
        techcore_users()
    with tabs[1]:
        techcore_clients()
    with tabs[2]:
        techcore_projects_admin()
    with tabs[3]:
        techcore_reports()
    with tabs[4]:
        techcore_settings()
    with tabs[5]:
        techcore_audit()

def techcore_users():
    st.subheader("User Management")
    
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
                    st.success(f"User '{new_username}' created successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    release_connection(conn)
            else:
                st.warning("Username, password, and full name are required")
    
    users = execute_df("""
        SELECT id, username as "Username", full_name as "Name", email as "Email", 
               role as "Role", department as "Department",
               CASE WHEN is_active THEN 'Active' ELSE 'Inactive' END as "Status",
               created_at as "Created"
        FROM users ORDER BY created_at DESC
    """)
    
    st.dataframe(users, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("**Edit User**")
    col1, col2 = st.columns(2)
    
    with col1:
        edit_user = st.selectbox("Select User", users['Username'].tolist())
        user_id = int(users[users['Username'] == edit_user]['id'].values[0])
    with col2:
        action = st.selectbox("Action", ["Reset Password", "Toggle Active", "Change Role"])
    
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
                st.success("Password reset!")
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
            st.success("Status toggled!")
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
            st.success("Role updated!")
            st.rerun()

def techcore_clients():
    st.subheader("Client Management")
    
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
                    st.success("Client added!")
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

def techcore_projects_admin():
    st.subheader("All Projects")
    
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
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            sel_proj = st.selectbox("Select Project", projects['Project'].tolist())
        with col2:
            new_status = st.selectbox("New Status", ["active", "on_hold", "completed", "cancelled"])
        with col3:
            st.write("")
            st.write("")
            if st.button("Update Status"):
                proj_id = int(projects[projects['Project'] == sel_proj]['id'].values[0])
                conn = get_connection()
                try:
                    with conn.cursor() as c:
                        c.execute("UPDATE projects SET status=%s WHERE id=%s", (new_status, proj_id))
                        conn.commit()
                finally:
                    release_connection(conn)
                log_audit(st.session_state.user['id'], "UPDATE_PROJECT_STATUS", "project", proj_id, new_status)
                st.success("Status updated!")
                st.rerun()

def techcore_reports():
    st.subheader("System Reports")
    
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("From", datetime.date.today() - timedelta(days=30), key="rep_start")
    with col2:
        end = st.date_input("To", datetime.date.today(), key="rep_end")
    
    report_type = st.selectbox("Report Type", [
        "Employee Hours Summary",
        "Project Hours Summary", 
        "Client Hours Summary",
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
        
        else:
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
            st.info("No data found for selected criteria")

def techcore_settings():
    st.subheader("System Settings")
    
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
            with conn.cursor() as c:
                c.execute("UPDATE settings SET value=%s, updated_at=%s WHERE key='company_name'", (company, datetime.datetime.now()))
                c.execute("UPDATE settings SET value=%s, updated_at=%s WHERE key='recall_window_hours'", (str(recall_hrs), datetime.datetime.now()))
                c.execute("UPDATE settings SET value=%s, updated_at=%s WHERE key='overtime_threshold'", (str(overtime), datetime.datetime.now()))
                c.execute("UPDATE settings SET value=%s, updated_at=%s WHERE key='work_week_start'", (week_start, datetime.datetime.now()))
                conn.commit()
        finally:
            release_connection(conn)
        log_audit(st.session_state.user['id'], "UPDATE_SETTINGS", "settings", None)
        st.success("Settings saved!")
        st.rerun()
    
    st.markdown("---")
    st.subheader("Database Statistics")
    
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

def techcore_audit():
    st.subheader("Audit Logs")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        start = st.date_input("From", datetime.date.today() - timedelta(days=7), key="audit_start")
    with col2:
        end = st.date_input("To", datetime.date.today(), key="audit_end")
    with col3:
        action_filter = st.text_input("Filter by Action", placeholder="e.g., LOGIN")
    
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
    
    st.info(f"Showing {len(logs)} records")
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
    
    st.markdown("""
    <style>
    .stApp {background-color: #f8f9fa;}
    .stButton>button {border-radius: 8px;}
    div[data-testid="stMetricValue"] {font-size: 28px;}
    .stTabs [data-baseweb="tab-list"] {gap: 8px;}
    .stTabs [data-baseweb="tab"] {background-color: white; border-radius: 8px 8px 0 0;}
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
    
    with st.sidebar:
        st.markdown(f"### 🧭 {get_setting('company_name') or 'Execution Edge'}")
        st.markdown(f"**{user['full_name']}**")
        st.caption(f"Role: {user['role'].title()}")
        st.markdown("---")
        
        if user['role'] == 'admin':
            portal = st.radio("Portal", ["⚙️ TechCore", "🧮 Manage360", "🧭 WorkHub"])
        elif user['role'] == 'manager':
            portal = st.radio("Portal", ["🧮 Manage360", "🧭 WorkHub"])
        else:
            portal = "🧭 WorkHub"
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            log_audit(user['id'], "LOGOUT", "user", user['id'])
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
    
    if "TechCore" in portal:
        techcore_dashboard()
    elif "Manage360" in portal:
        manage360_dashboard()
    else:
        workhub_dashboard()

if __name__ == "__main__":
    main()