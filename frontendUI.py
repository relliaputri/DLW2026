import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import json

# ==============================================================================
# [Connection 1] Import backend logic module
# ==============================================================================
try:
    import logic
    LOGIC_AVAILABLE = True
except ImportError:
    LOGIC_AVAILABLE = False

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(page_title="AxonAI", layout="wide", initial_sidebar_state="expanded")

# Initialize Chat Visibility State
if "chat_expanded" not in st.session_state:
    st.session_state.chat_expanded = True

# Initialize Goal Mode states (will be populated dynamically from data)
if "goal_modes" not in st.session_state:
    st.session_state.goal_modes = {}
if "course_deadlines" not in st.session_state:
    st.session_state.course_deadlines = {}
if "settings_ai_model" not in st.session_state:
    st.session_state.settings_ai_model = "gpt-4o-mini"
if "settings_ai_temp" not in st.session_state:
    st.session_state.settings_ai_temp = 0.7
if "settings_decay_constant" not in st.session_state:
    st.session_state.settings_decay_constant = 0.15
if "settings_notif_weekly" not in st.session_state:
    st.session_state.settings_notif_weekly = True
if "settings_notif_remind" not in st.session_state:
    st.session_state.settings_notif_remind = False

def toggle_chat():
    st.session_state.chat_expanded = not st.session_state.chat_expanded

def ensure_goal_modes(course_data):
    """Ensure goal_modes has entries for all courses in the loaded data."""
    for course_name in course_data:
        if course_name not in st.session_state.goal_modes:
            st.session_state.goal_modes[course_name] = False
        if course_name not in st.session_state.course_deadlines:
            st.session_state.course_deadlines[course_name] = datetime.now() + timedelta(days=14)

st.markdown(f"""
    <style>
    /* Main Background */
    .stApp {{ background-color: #0B0E14; color: #FFFFFF; }}
    
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    .stAppDeployButton {{display:none;}}
    #MainMenu {{visibility: hidden;}}
    
    button[data-testid="sidebar-toggle"] {{
        background-color: #FDE047 !important;
        border-radius: 50% !important;
        left: 10px !important;
        top: 10px !important;
        z-index: 1001 !important;
    }}

    .custom-header {{
        position: fixed; top: 0; left: 0; width: 100%; height: 50px;
        background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(253, 224, 71, 0.5);
        box-shadow: 0px 4px 20px rgba(253, 224, 71, 0.2);
        z-index: 999; display: flex; align-items: center; justify-content: center;
    }}
    .header-title {{
        color: #FDE047 !important; font-family: 'Inter', sans-serif;
        font-weight: 800; letter-spacing: 2px; font-size: 20px;
        text-shadow: 0px 0px 8px rgba(253, 224, 71, 0.4);
    }}

    .goal-tag {{
        background-color: #FDE047; color: #000000 !important;
        padding: 4px 12px; border-radius: 4px; font-weight: 800;
        font-size: 12px; display: inline-block; margin-bottom: 15px;
    }}

    .main-content {{ padding-top: 60px; }}
    h1, h2, h3, p, span, label {{ color: #FFFFFF !important; font-family: 'Inter', sans-serif; }}
    .stMarkdown p, .stCaption {{ color: #CBD5E1 !important; }}
    
    [data-testid="stSidebar"] {{ background-color: #111827 !important; border-right: 2px solid #1E293B; }}
    
    div[data-testid="stMetric"] {{ 
        background-color: #1E293B; border: 2px solid #FDE047;
        padding: 20px; border-radius: 12px;
    }}
    
    .stButton>button {{ 
        background-color: #3b82f6; color: #FFFFFF !important;
        font-weight: 500; border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.2); width: 100%; padding: 8px;
    }}
    
    .tag-container {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }}
    .topic-tag {{
        padding: 6px 14px; border-radius: 20px;
        background-color: rgba(37, 99, 235, 0.5); color: #FFFFFF !important;
        font-size: 14px; font-weight: 500; transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.2); cursor: pointer;
        display: inline-block; margin: 4px;
    }}
    .topic-tag:hover {{ background-color: rgba(96, 165, 250, 0.7) !important; border-color: #60a5fa; }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.urgent-marker) {{
        background-color: rgba(239, 68, 68, 0.15) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 12px !important;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.polish-marker) {{
        background-color: rgba(253, 224, 71, 0.1) !important;
        border: 1px solid rgba(253, 224, 71, 0.2) !important;
        border-radius: 12px !important;
    }}

    .trend-tag-final {{
        display: inline-flex; align-items: center; justify-content: center;
        padding: 4px 12px; border-radius: 20px; font-size: 13px;
        font-weight: 700; gap: 6px; min-width: 100px; margin-top: 5px;
        color: #FFFFFF !important;
        transition: all 0.2s ease;
    }}
    .trend-regressing {{
        background-color: rgba(248, 113, 113, 0.25) !important;
        border: 1px solid rgba(248, 113, 113, 0.6) !important;
        box-shadow: 0 0 8px rgba(248, 113, 113, 0.3);
    }}
    .trend-regressing:hover {{
        background-color: rgba(248, 113, 113, 0.55) !important;
        box-shadow: 0 0 14px rgba(248, 113, 113, 0.5);
    }}
    .trend-regressing .trend-arrow {{ color: #fca5a5; }}
    .trend-stagnant {{
        background-color: rgba(253, 224, 71, 0.2) !important;
        border: 1px solid rgba(253, 224, 71, 0.5) !important;
        box-shadow: 0 0 8px rgba(253, 224, 71, 0.25);
    }}
    .trend-stagnant:hover {{
        background-color: rgba(253, 224, 71, 0.45) !important;
        box-shadow: 0 0 14px rgba(253, 224, 71, 0.45);
    }}
    .trend-stagnant .trend-arrow {{ color: #fde68a; }}
    .trend-improving {{
        background-color: rgba(74, 222, 128, 0.2) !important;
        border: 1px solid rgba(74, 222, 128, 0.5) !important;
        box-shadow: 0 0 8px rgba(74, 222, 128, 0.25);
    }}
    .trend-improving:hover {{
        background-color: rgba(74, 222, 128, 0.45) !important;
        box-shadow: 0 0 14px rgba(74, 222, 128, 0.45);
    }}
    .trend-improving .trend-arrow {{ color: #86efac; }}

    .thin-divider {{ border-top: 1px solid rgba(255,255,255,0.1); margin: 15px 0; }}

    div[data-testid="stVerticalBlock"] > div:has(div.card-click) {{ transition: transform 0.2s ease-in-out; }}
    div[data-testid="stVerticalBlock"] > div:has(div.card-click):hover {{ transform: scale(1.02); cursor: pointer; }}

    [data-testid="column"]:nth-child(2) {{
        background: rgba(17, 24, 39, 0.7) !important;
        backdrop-filter: blur(10px) !important;
        border-left: 1px solid rgba(253, 224, 71, 0.5) !important;
        box-shadow: -4px 0px 20px rgba(253, 224, 71, 0.2) !important;
        padding: 0px !important;
        border-radius: 0px !important;
    }}

    .chat-header {{
        background: rgba(17, 24, 39, 0.7);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(253, 224, 71, 0.5);
        box-shadow: 0px 4px 20px rgba(253, 224, 71, 0.2);
        padding: 12px 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    .chat-header-title {{
        color: #FDE047 !important;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        letter-spacing: 2px;
        font-size: 16px;
        text-shadow: 0px 0px 8px rgba(253, 224, 71, 0.4);
    }}
    .chat-body {{
        padding: 16px;
    }}

    .right-chat-container {{
        position: fixed; right: 0; top: 50px; height: 100vh;
        background-color: rgba(17, 24, 39, 0.7);
        border-left: 1px solid rgba(253, 224, 71, 0.5);
        box-shadow: -4px 0px 20px rgba(253, 224, 71, 0.2);
        z-index: 1000; transition: width 0.3s ease;
        width: {"350px" if st.session_state.chat_expanded else "60px"};
    }}

    div[data-testid="stProgress"] {{ width: 100% !important; }}
    div[data-testid="stProgress"] > div > div > div > div {{
        background-color: #22c55e !important; height: 40px !important;
    }}
    
    /* FILE UPLOADER - Dark Theme Fix */
    [data-testid="stFileUploader"] {{
        background-color: transparent !important;
    }}
    [data-testid="stFileUploader"] section {{
        background-color: rgba(30, 41, 59, 0.8) !important;
        border: 1px dashed rgba(253, 224, 71, 0.4) !important;
        border-radius: 10px !important;
        padding: 16px !important;
    }}
    [data-testid="stFileUploader"] section > div {{
        color: #CBD5E1 !important;
    }}
    [data-testid="stFileUploader"] small {{
        color: #94a3b8 !important;
    }}
    [data-testid="stFileUploader"] button {{
        background-color: #FDE047 !important;
        color: #000000 !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
    }}
    [data-testid="stFileUploaderDeleteBtn"] {{
        color: #EF4444 !important;
    }}

    /* Date input — dark style */
    [data-testid="stDateInput"] input {{
        background-color: rgba(17, 24, 39, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        color: #FFFFFF !important;
    }}

    /* Expander — override all borders to yellow */
    [data-testid="stExpander"] {{
        border: 1px solid rgba(253, 224, 71, 0.15) !important;
    }}
    [data-testid="stExpander"] details {{
        border: none !important;
    }}
    [data-testid="stExpander"] details summary {{
        border: none !important;
        border-bottom: 2px solid rgba(253, 224, 71, 0.15) !important;
    }}
    [data-testid="stExpander"] details[open] summary {{
        border-bottom: 2px solid rgba(253, 224, 71, 0.3) !important;
    }}
    [data-testid="stExpander"] details summary:hover {{
        border-bottom: 2px solid rgba(253, 224, 71, 0.3) !important;
    }}
    [data-testid="stExpander"] details summary::before,
    [data-testid="stExpander"] details summary::after {{
        background: none !important;
        border: none !important;
    }}
    [data-testid="stExpander"] summary *,
    [data-testid="stExpander"] summary > div {{
        border: none !important;
        border-top: none !important;
        border-bottom: none !important;
    }}

    /* Goal Mode Toggle — bigger + glowing */
    [data-testid="stToggle"] {{
        transform: scale(1.3);
        transform-origin: left center;
        margin: 8px 0;
    }}
    [data-testid="stToggle"] label > div:first-child {{
        filter: drop-shadow(0 0 6px rgba(253, 224, 71, 0.5));
    }}
    [data-testid="stToggle"] label > div:first-child > div {{
        background-color: rgba(253, 224, 71, 0.8) !important;
        box-shadow: 0 0 12px rgba(253, 224, 71, 0.5);
    }}
    /* Uploaded file name text */
    [data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] p {{
        color: #CBD5E1 !important;
    }}
    
    .diag-box {{
        background-color: rgba(255,255,255,0.03); padding: 12px 16px;
        border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 10px;
    }}
    .diag-label {{ font-size: 12px; color: #FDE047 !important; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }}
    .diag-value {{ font-size: 22px; font-weight: 700; color: #FFFFFF !important; }}
    .diag-category {{ font-weight: 700; font-size: 16px; }}
    .diag-category.cat-careless {{ color: #F97316 !important; }}
    .diag-category.cat-weakness {{ color: #EF4444 !important; }}
    .diag-category.cat-normal {{ color: #FFFFFF !important; }}
    
    /* AI Chat Message Readability */
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] ol,
    [data-testid="stChatMessage"] ul,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] strong {{
        color: #FFFFFF !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
    }}
    .diag-sub {{ font-size: 12px; color: #94a3b8 !important; }}
    </style>
    
    <div class="custom-header">
        <div class="header-title">🎓 AxonAI</div>
    </div>
    """, unsafe_allow_html=True)


# --- 2. DEFAULT DATA (fallback when no CSV is uploaded) ---
DEFAULT_COURSE_DATA = {
    "Calculus II": {
        "topics": ["Limits", "Derivatives", "Integrals", "Series", "Polar Coordinates", "Vector Functions", "Taylor Series"],
        "mastery": [0.92, 0.88, 0.85, 0.40, 0.70, 0.65, 0.38],
        "trend_label": ["Improving", "Improving", "Stagnant", "Regressing", "Stagnant", "Improving", "Regressing"],
        "avg_time": [15, 45, 120, 300, 80, 95, 350],
        "e_r": [0.08, 0.12, 0.15, 0.60, 0.30, 0.35, 0.62],
        "r_t": [0.8, 0.9, 1.1, 1.5, 1.0, 0.95, 1.6],
        "category": ["Normal/Mastered"]*5 + ["Normal/Mastered"]*2,
        "priority": [0.15, 0.18, 0.25, 0.72, 0.35, 0.38, 0.75],
        "weekly_acc_weeks": [[1, 2]]*7,
        "weekly_acc_rates": [[50, 60]]*7
    },
    "Physics I": {
        "topics": ["Kinematics", "Dynamics", "Work & Energy", "Momentum", "Rotational Motion", "Gravity", "Oscillations"],
        "mastery": [0.45, 0.50, 0.42, 0.80, 0.30, 0.85, 0.40],
        "trend_label": ["Improving", "Stagnant", "Regressing", "Improving", "Regressing", "Improving", "Stagnant"],
        "avg_time": [10, 80, 75, 90, 280, 60, 110],
        "e_r": [0.55, 0.50, 0.58, 0.20, 0.70, 0.15, 0.60],
        "r_t": [0.9, 1.0, 1.2, 0.8, 1.4, 0.7, 1.1],
        "category": ["Normal/Mastered"]*7,
        "priority": [0.48, 0.45, 0.55, 0.20, 0.68, 0.15, 0.52],
        "weekly_acc_weeks": [[1, 2]]*7,
        "weekly_acc_rates": [[50, 60]]*7
    }
}

# --- 3. STATE MANAGEMENT ---
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "selected_course" not in st.session_state:
    st.session_state.selected_course = None
if "deep_dive_topic" not in st.session_state:
    st.session_state.deep_dive_topic = None
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! Upload a CSV to get started, or explore the default data. Ready to analyze?"}]
if "raw_data" not in st.session_state:
    st.session_state.raw_data = None
if "course_data" not in st.session_state:
    st.session_state.course_data = DEFAULT_COURSE_DATA
if "dashboard_metrics" not in st.session_state:
    st.session_state.dashboard_metrics = None
if "course_deadlines" not in st.session_state:
    st.session_state.course_deadlines = {}


# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("""<div style="text-align: center; padding: 10px 0 15px 0; border-bottom: 1px solid rgba(253, 224, 71, 0.3); margin-bottom: 15px;">
        <span style="color: #FDE047; font-family: 'Inter', sans-serif; font-weight: 800; letter-spacing: 2px; font-size: 26px; text-shadow: 0px 0px 12px rgba(253, 224, 71, 0.5);">🎓 AxonAI</span>
    </div>""", unsafe_allow_html=True)

    # ==============================================================================
    # [Connection 2] Data Upload UI & Backend Connection
    # ==============================================================================
    st.markdown("### 📁 Data Upload")
    uploaded_file = st.file_uploader("Upload Student Activity (CSV)", type=['csv'])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state.raw_data = df
            if LOGIC_AVAILABLE:
                st.session_state.course_data = logic.process_student_dataframe(df)
                st.session_state.dashboard_metrics = logic.compute_dashboard_metrics(df, st.session_state.course_data)
                st.success("✅ Data synced with neural core!")
            else:
                st.warning("Backend logic module missing. Using default data.", icon="⚠️")
        except Exception as e:
            st.error(f"Error parsing file: {e}")

    st.markdown("---")
    if st.button("🏠 Dashboard"):
        st.session_state.page = "Dashboard"
        st.session_state.selected_course = None
        st.session_state.deep_dive_topic = None
    if st.button("📖 My Courses"):
        st.session_state.page = "Courses"
        st.session_state.selected_course = None
        st.session_state.deep_dive_topic = None
    if st.button("⚙️ Settings"):
        st.session_state.page = "Settings"
    st.markdown("---")

    # Goal Mode Logic (Sidebar)
    st.subheader("🎯 Course Goal Mode")
    # Ensure goal modes are synced with current course data
    ensure_goal_modes(st.session_state.course_data)

    if st.session_state.selected_course and st.session_state.selected_course in st.session_state.course_data:
        current_course = st.session_state.selected_course
        st.session_state.goal_modes[current_course] = st.toggle(
            f"Intense Focus: {current_course}",
            value=st.session_state.goal_modes.get(current_course, False)
        )
    else:
        st.caption("Select a course to enable Goal Mode.")

    st.markdown("---")
    st.write("🔥 **14 Day Streak** *(Beta)*")
    st.write("🏆 **8 Badges Earned** *(Beta)*")

# Active course data reference
COURSE_DATA = st.session_state.course_data
ensure_goal_modes(COURSE_DATA)

# --- Helper: Trend tag rendering ---
def get_trend_parts(trend_text):
    if trend_text == "Improving":
        return "trend-improving", "↑"
    elif trend_text == "Stagnant":
        return "trend-stagnant", "→"
    else:
        return "trend-regressing", "↓"


# --- 5. LAYOUT ---
st.markdown("<div class='main-content'>", unsafe_allow_html=True)

if st.session_state.chat_expanded:
    col_content, col_agent = st.columns([2.2, 1], gap="medium")
else:
    col_content, col_agent = st.columns([15, 1], gap="small")


# ==================================================================================
# PAGE: DASHBOARD
# ==================================================================================
if st.session_state.page == "Dashboard":
    with col_content:
        st.title("Student Command Center")

        # --- Live metrics from backend ---
        dm = st.session_state.dashboard_metrics
        if dm:
            m1, m2, m3 = st.columns(3)
            mastery_d = f"{'+' if dm['mastery_delta'] > 0 else ''}{dm['mastery_delta']}%"
            velocity_d = f"{'+' if dm['velocity_delta'] > 0 else ''}{dm['velocity_delta']}%"
            careless_d = f"{'+' if dm['careless_delta'] > 0 else ''}{dm['careless_delta']}%"
            m1.metric("Overall Mastery", f"{dm['overall_mastery']}%", mastery_d)
            m2.metric("Study Velocity", f"{dm['study_velocity']} h/day", velocity_d)
            m3.metric("Careless Rate", f"{dm['careless_rate']}%", careless_d, delta_color="inverse")
        else:
            m1, m2, m3 = st.columns(3)
            m1.metric("Overall Mastery", "—")
            m2.metric("Study Velocity", "—")
            m3.metric("Careless Rate", "—")
            st.info("Upload a CSV in the sidebar to see live metrics.")

        st.markdown("---")

        st.subheader("📅 Unified Study Plan (Goal Mode Active)")
        active_goals = [c for c, active in st.session_state.goal_modes.items() if active]
        if active_goals:
            # Generate tasks from highest-priority topics in active goal courses
            plan_items = []
            for cname in active_goals:
                cinfo = COURSE_DATA.get(cname, {})
                if not cinfo.get("topics"):
                    continue
                # Pick top 2 priority topics
                paired = list(zip(cinfo["topics"], cinfo["priority"]))
                paired.sort(key=lambda x: x[1], reverse=True)
                for topic, pri in paired[:2]:
                    plan_items.append({"Course": cname, "Task": f"Review: {topic}", "Priority": pri})
            if plan_items:
                for i, item in enumerate(plan_items):
                    st.checkbox(
                        f"**{item['Course']}**: {item['Task']} (Pri: {int(item['Priority']*100)})",
                        key=f"dash_plan_{i}"
                    )
            else:
                st.info("No tasks available for courses in Goal Mode.")
        else:
            st.info("Activate 'Goal Mode' in the sidebar for a specific course to see your study plan.")

        st.subheader("📈 Progress Tracking")
        if dm and dm.get("weekly_progress"):
            fig = go.Figure()

            # Per-course mastery lines
            course_colors = ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6']
            weeks = dm.get("weeks", [])
            cwm = dm.get("course_weekly_mastery", {})
            for i, (course_name, mastery_vals) in enumerate(cwm.items()):
                color = course_colors[i % len(course_colors)]
                fig.add_trace(go.Scatter(
                    x=weeks, y=mastery_vals, mode='lines+markers',
                    name=course_name,
                    line=dict(color=color, width=1.5, dash='dot'),
                    marker=dict(size=5),
                    hovertemplate=f"{course_name}<br>Week %{{x}}<br>Mastery: %{{y:.1f}}%<extra></extra>"
                ))

            # Overall mastery (yellow, thicker, area fill)
            wp = dm["weekly_progress"]
            overall_weeks = [p["week"] for p in wp]
            overall_mastery = [p["mastery"] for p in wp]
            fig.add_trace(go.Scatter(
                x=overall_weeks, y=overall_mastery, mode='lines+markers',
                name='Overall Mastery',
                fill='tozeroy', fillcolor='rgba(253, 224, 71, 0.1)',
                line=dict(color='#FDE047', width=3),
                marker=dict(size=7),
                hovertemplate="Overall<br>Week %{x}<br>Mastery: %{y:.1f}%<extra></extra>"
            ))

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font_color="white",
                xaxis_title="Week", yaxis_title="Mastery (%)",
                yaxis=dict(range=[0, 105]),
                xaxis=dict(dtick=1),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white"))
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=days, y=[55, 57, 56, 60, 65, 68, 72], mode='lines+markers',
                name='Calculus', line=dict(color='#3B82F6', width=1.5, dash='dot'), marker=dict(size=5)))
            fig.add_trace(go.Scatter(x=days, y=[62, 63, 64, 66, 70, 71, 76], mode='lines+markers',
                name='Linear Algebra', line=dict(color='#EF4444', width=1.5, dash='dot'), marker=dict(size=5)))
            fig.add_trace(go.Scatter(x=days, y=[64, 66, 63, 69, 74, 76, 80], mode='lines+markers',
                name='Statistics', line=dict(color='#10B981', width=1.5, dash='dot'), marker=dict(size=5)))
            fig.add_trace(go.Scatter(x=days, y=[60, 62, 61, 65, 70, 72, 76], mode='lines+markers',
                name='Overall Mastery', fill='tozeroy', fillcolor='rgba(253, 224, 71, 0.1)',
                line=dict(color='#FDE047', width=3), marker=dict(size=7)))
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font_color="white", xaxis_title="Day", yaxis_title="Mastery (%)",
                yaxis=dict(range=[0, 105]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white"))
            )
            st.plotly_chart(fig, use_container_width=True)


# ==================================================================================
# PAGE: COURSES
# ==================================================================================
elif st.session_state.page == "Courses":
    with col_content:

        # ==================================================================
        # SUB-PAGE: DEEP DIVE (backed by real data)
        # ==================================================================
        if st.session_state.deep_dive_topic:
            topic_name = st.session_state.deep_dive_topic
            course_name = st.session_state.selected_course

            if st.button("← Back to Analytics"):
                st.session_state.deep_dive_topic = None
                st.rerun()

            st.title(f"🔍 Deep Dive: {topic_name}")
            st.markdown(f"Neural breakdown for **{topic_name}** in **{course_name}**.")

            # --- Fetch deep dive data from backend ---
            deep_data = None
            if LOGIC_AVAILABLE and st.session_state.raw_data is not None:
                deep_data = logic.get_deep_dive_data(
                    st.session_state.raw_data, course_name, topic_name
                )

            if deep_data:
                # ---- TOP DIAGNOSTIC CARDS ----
                current_mastery_pct = round(deep_data['current_mastery'] * 100, 1)
                accuracy_pct = round((1.0 - deep_data['e_r']) * 100, 1)

                # SVG circle params
                circ_r = 40
                circ_c = 2 * 3.14159 * circ_r
                filled = (current_mastery_pct / 100) * circ_c
                gap = circ_c - filled

                d1, d2, d3, d4 = st.columns(4)
                with d1:
                    st.markdown(f"""<div class='diag-box' style='text-align: center; padding: 16px 12px;'>
                        <div class='diag-label'>Current Mastery</div>
                        <svg width="110" height="110" viewBox="0 0 100 100" style="margin: 8px auto; display: block;">
                            <circle cx="50" cy="50" r="{circ_r}" fill="none" stroke="rgba(253, 224, 71, 0.1)" stroke-width="8"/>
                            <circle cx="50" cy="50" r="{circ_r}" fill="none" stroke="#FDE047" stroke-width="8"
                                stroke-dasharray="{filled:.1f} {gap:.1f}"
                                stroke-dashoffset="{circ_c * 0.25:.1f}"
                                stroke-linecap="round"
                                style="filter: drop-shadow(0 0 6px rgba(253, 224, 71, 0.5));"/>
                            <text x="50" y="50" text-anchor="middle" dominant-baseline="central" fill="#FDE047" font-size="18" font-weight="800" font-family="Inter, sans-serif" style="filter: drop-shadow(0 0 4px rgba(253, 224, 71, 0.4));">{current_mastery_pct}%</text>
                        </svg>
                    </div>""", unsafe_allow_html=True)
                with d2:
                    cls, arrow = get_trend_parts(deep_data['trend_label'])
                    slope_val = deep_data.get('avg_slope', 0.0)
                    slope_pct = round(slope_val, 2)
                    slope_sign = "+" if slope_pct > 0 else ""
                    st.markdown(f"""<div class='diag-box'>
                        <div class='diag-label'>Trend</div>
                        <div class='diag-value'><span class='trend-tag-final {cls}'>{arrow} {deep_data['trend_label']}</span></div>
                        <div class='diag-sub' style='margin-top: 10px;'>Avg Slope: {slope_sign}{slope_pct}%/week</div>
                    </div>""", unsafe_allow_html=True)
                with d3:
                    st.markdown(f"""<div class='diag-box'>
                        <div class='diag-label'>Accuracy</div>
                        <div class='diag-value'>{accuracy_pct}%</div>
                        <div class='diag-sub'>Time Ratio: {deep_data['r_t']:.2f}</div>
                    </div>""", unsafe_allow_html=True)
                with d4:
                    cat_cls = "cat-careless" if deep_data['category'] == "Careless Mistake" else (
                        "cat-weakness" if deep_data['category'] == "Genuine Weakness" else "cat-normal"
                    )
                    st.markdown(f"""<div class='diag-box'>
                        <div class='diag-label'>Diagnosis</div>
                        <div class='diag-value'><span class='diag-category {cat_cls}'>{deep_data['category']}</span></div>
                    </div>""", unsafe_allow_html=True)

                # ---- CHART 1: Mastery vs Accuracy over weeks ----
                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader("🧠 Mastery & Accuracy Over Time (Weekly)")

                mastery_weeks = [p[0] for p in deep_data['mastery_per_week']]
                mastery_vals = [p[1] for p in deep_data['mastery_per_week']]
                acc_weeks = [p[0] for p in deep_data['accuracy_per_week']]
                acc_vals = [p[1] for p in deep_data['accuracy_per_week']]

                fig_neural = go.Figure()
                fig_neural.add_trace(go.Scatter(
                    x=mastery_weeks, y=mastery_vals, mode='lines+markers',
                    name='Mastery (%)', line=dict(color='#2563EB', width=2),
                    marker=dict(size=7),
                    hovertemplate="Week %{x}<br>Mastery: %{y:.1f}%<extra></extra>"
                ))
                fig_neural.add_trace(go.Scatter(
                    x=acc_weeks, y=acc_vals, mode='markers+lines',
                    name='Weekly Accuracy (%)',
                    line=dict(color='#FDE047', width=1, dash='dot'),
                    marker=dict(color='#FDE047', size=9, symbol='diamond'),
                    hovertemplate="Week %{x}<br>Accuracy: %{y:.1f}%<extra></extra>"
                ))
                # Highlight current week (most recent) with larger glowing markers
                fig_neural.add_trace(go.Scatter(
                    x=[mastery_weeks[-1]], y=[mastery_vals[-1]], mode='markers',
                    name=f'Current Week ({mastery_weeks[-1]})',
                    marker=dict(color='#FFFFFF', size=14, symbol='circle',
                                line=dict(color='#2563EB', width=3)),
                    hovertemplate=f"Week {mastery_weeks[-1]} (Current)<br>Mastery: {mastery_vals[-1]:.1f}%<extra></extra>",
                    showlegend=True
                ))
                fig_neural.add_trace(go.Scatter(
                    x=[acc_weeks[-1]], y=[acc_vals[-1]], mode='markers',
                    name='',
                    marker=dict(color='#FFFFFF', size=14, symbol='diamond',
                                line=dict(color='#FDE047', width=3)),
                    hovertemplate=f"Week {acc_weeks[-1]} (Current)<br>Accuracy: {acc_vals[-1]:.1f}%<extra></extra>",
                    showlegend=False
                ))
                fig_neural.add_hline(y=75, line_dash="dash", line_color="#EF4444", opacity=0.5,
                                     annotation_text="75% Proficiency Threshold",
                                     annotation_position="top left",
                                     annotation_font_color="#EF4444")
                fig_neural.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(17, 24, 39, 0.5)',
                    font_color="white", xaxis_title="Week", yaxis_title="Percentage (%)",
                    yaxis=dict(range=[0, 105]),
                    xaxis=dict(dtick=1),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white"))
                )
                st.plotly_chart(fig_neural, use_container_width=True)

                # ---- CHART 2: Forward Decay Projection ----
                st.markdown("#### 📉 Forgetting Curve Projection")
                st.markdown("<p style='color: #94a3b8 !important; font-size: 13px; margin-top: -10px; margin-bottom: 15px;'>Projected mastery decay if no further review is done.</p>", unsafe_allow_html=True)

                decay_weeks = [p[0] for p in deep_data['decay_curve']]
                decay_vals = [p[1] for p in deep_data['decay_curve']]

                fig_decay = go.Figure()
                fig_decay.add_trace(go.Scatter(
                    x=decay_weeks, y=decay_vals, mode='lines+markers',
                    name='Projected Mastery',
                    fill='tozeroy', fillcolor='rgba(239, 68, 68, 0.1)',
                    line=dict(color='#EF4444', width=2),
                    marker=dict(size=6),
                    hovertemplate="Week +%{x}<br>Mastery: %{y:.1f}%<extra></extra>"
                ))
                fig_decay.add_hline(y=75, line_dash="dash", line_color="#FDE047", opacity=0.5,
                                    annotation_text="Proficiency Threshold",
                                    annotation_position="top left",
                                    annotation_font_color="#FDE047")
                fig_decay.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(17, 24, 39, 0.5)',
                    font_color="white", xaxis_title="Weeks From Now (No Review)",
                    yaxis_title="Projected Mastery (%)", yaxis=dict(range=[0, 105]),
                    xaxis=dict(dtick=1),
                    margin=dict(t=10)
                )
                st.plotly_chart(fig_decay, use_container_width=True)


            else:
                # Fallback: no raw data or topic not found
                st.warning("Deep dive analytics require raw CSV data. Please upload a dataset in the sidebar.")

                # Show basic info from course_data if available
                course_info = COURSE_DATA.get(course_name, {})
                if topic_name in course_info.get("topics", []):
                    idx = course_info["topics"].index(topic_name)
                    current_mastery_pct = round(course_info["mastery"][idx] * 100, 1)
                    trend = course_info["trend_label"][idx]
                    cls, arrow = get_trend_parts(trend)
                    st.write("📊 **Mastery Level (from summary data)**")
                    p_col1, p_col2, p_col3 = st.columns([0.15, 0.1, 0.75], gap="small")
                    with p_col1:
                        st.progress(course_info["mastery"][idx])
                    with p_col2:
                        st.write(f"**{current_mastery_pct}%**")
                    with p_col3:
                        st.markdown(f"<div class='trend-tag-final {cls}' style='margin-top: -5px;'><span class='trend-arrow'>{arrow}</span> {trend}</div>", unsafe_allow_html=True)

            # --- Description Box (always shown) ---
            st.subheader("Description")
            with st.container(border=True):
                st.markdown("""
                #### **Mastery Level**
                Mastery measures your high-retention knowledge, calculated using a **Time-Decayed Weighted Average**. By incorporating the Ebbinghaus Forgetting Curve, we apply a decay weight $w_i = e^{-\\lambda \\Delta t_i}$ based on the time since your last review.
                
                $$Mastery = \\frac{\\sum (w_i \\cdot C_i)}{\\sum w_i}$$
                
                *Older scores lose weight exponentially. If study activity remains stagnant for too long, the Mastery level will drop sharply, reflecting neural decay.*

                #### **Accuracy Level**
                Accuracy represents your **overall lifetime performance** on a topic — the simple mean of all correct answers across every question ever attempted.
                
                $$Accuracy = \\frac{\\text{Total Correct}}{\\text{Total Attempted}} \\times 100\\%$$
                
                Unlike Mastery, Accuracy does not apply time decay — it weights all attempts equally regardless of when they occurred.

                #### **Trend (Trajectory)**
                The trend is determined by computing the **average slope** of weekly accuracy over time:
                
                $$\\text{Avg Slope} = \\frac{1}{N}\\sum_{i=1}^{N} \\frac{Acc_{w_i} - Acc_{w_{i-1}}}{w_i - w_{i-1}}$$
                
                Where $Acc_{w_i}$ is the accuracy (0–1) at week $w_i$, and $N$ is the number of consecutive week pairs.
                
                * **Improving:** Slope $> 0.3$ %/week (accuracy rising week-over-week)
                * **Stagnant:** Slope $\\approx 0$ (no significant change)
                * **Regressing:** Slope $< -0.3$ %/week (accuracy declining week-over-week)
                
                #### **Forgetting Curve Projection**
                The forward projection shows what happens to your mastery if you stop reviewing. It uses the same exponential decay model $M(t) = M_0 \\cdot e^{-\\lambda t}$ to project mastery loss over the coming weeks.
                """)

        # ==================================================================
        # SUB-PAGE: COURSE LIST
        # ==================================================================
        elif st.session_state.selected_course is None:
            st.title("My Courses")
            st.markdown("Select a course card to see **Deep Data Analytics**.")

            cols = st.columns(min(len(COURSE_DATA), 3))
            for idx, (c_name, c_info) in enumerate(COURSE_DATA.items()):
                with cols[idx % len(cols)]:
                    with st.container(border=True):
                        st.markdown("<div class='card-click'></div>", unsafe_allow_html=True)
                        st.subheader(f"📚 {c_name}")
                        topics_preview = ', '.join(c_info['topics'][:3]) if c_info['topics'] else "N/A"
                        st.write(f"Topics: {topics_preview}...")

                        overall_prog = np.mean(c_info['mastery']) if c_info['mastery'] else 0.0
                        overall_prog = min(max(float(overall_prog), 0.0), 1.0)
                        st.progress(overall_prog)
                        st.caption(f"Avg Mastery: {round(overall_prog*100, 1)}%")

                        if st.button(f"Open Analytics", key=f"nav_{c_name}"):
                            st.session_state.selected_course = c_name
                            st.rerun()

        # ==================================================================
        # SUB-PAGE: COURSE ANALYTICS
        # ==================================================================
        else:
            course_name = st.session_state.selected_course
            if course_name not in COURSE_DATA:
                st.error(f"Course '{course_name}' not found in loaded data.")
                if st.button("← Back to Courses"):
                    st.session_state.selected_course = None
                    st.rerun()
            else:
                course_info = COURSE_DATA[course_name]
                if st.button("← Back to Courses"):
                    st.session_state.selected_course = None
                    st.rerun()

                st.title(f"📊 {course_name} Analytics")

                # Build topic_df early so Goal Mode and all sections can use it
                mastery_100 = [m * 100 for m in course_info["mastery"]]
                accuracy_100 = [round((1.0 - er) * 100, 1) for er in course_info["e_r"]]
                topic_df = pd.DataFrame({
                    "Topic": course_info["topics"],
                    "Mastery": mastery_100,
                    "Accuracy": accuracy_100,
                    "Trend": course_info["trend_label"],
                    "Avg Time (s)": course_info["avg_time"],
                    "Priority": course_info["priority"],
                    "Time Ratio": course_info["r_t"],
                    "Category": course_info["category"]
                })

                # Goal Mode Section — Adaptive Exam Scheduler
                if st.session_state.goal_modes.get(course_name, False):
                    st.markdown("<div class='goal-tag'>GOAL: EXAM</div>", unsafe_allow_html=True)
                    st.markdown("### 📝 Adaptive Exam Prep")

                    # User config: exam date + daily hours
                    col1, col2 = st.columns(2)
                    with col1:
                        default_date = st.session_state.course_deadlines.get(course_name, datetime.now() + timedelta(days=14))
                        default_date_val = default_date.date() if isinstance(default_date, datetime) else default_date
                        exam_date = st.date_input("Target Exam Date", value=default_date_val, key=f"date_{course_name}")
                    with col2:
                        daily_hours = st.slider("Daily Study Hours", min_value=1.0, max_value=8.0, value=2.0, step=0.5, key=f"hours_{course_name}")

                    days_left = (exam_date - datetime.now().date()).days

                    if days_left <= 0:
                        st.error("Exam date must be in the future!")
                    else:
                        cache_key = f"goal_plan_{course_name}"

                        # Generate button
                        if st.button("🚀 Generate Adaptive Schedule"):
                            with st.spinner("🤖 AI is analyzing your behavioral patterns & neuro-decay..."):
                                if LOGIC_AVAILABLE and hasattr(logic, 'get_goal_mode_schedule'):
                                    raw_json = logic.get_goal_mode_schedule(course_name, topic_df, days_left, daily_hours)
                                    try:
                                        schedule_data = json.loads(raw_json)
                                        st.session_state[cache_key] = schedule_data
                                        st.session_state.course_deadlines[course_name] = datetime.combine(exam_date, datetime.min.time())
                                    except Exception as e:
                                        st.error(f"Failed to parse AI response: {e}")
                                else:
                                    st.warning("Backend logic module missing.")

                        # Render cached schedule
                        if cache_key in st.session_state:
                            schedule_data = st.session_state[cache_key]

                            # Adaptation message
                            if "adaptation_message" in schedule_data:
                                st.info(schedule_data["adaptation_message"])

                            # Task checklist
                            if "tasks" in schedule_data and schedule_data["tasks"]:
                                h_col1, h_col2, h_col3 = st.columns([0.1, 0.6, 0.3])
                                h_col2.caption("TASK"); h_col3.caption("EST. TIME & DAY")
                                for i, t in enumerate(schedule_data["tasks"]):
                                    r_col1, r_col2, r_col3 = st.columns([0.1, 0.6, 0.3])
                                    with r_col1: st.checkbox("", key=f"check_goal_{course_name}_{i}")
                                    with r_col2: st.markdown(f"**{t.get('action', 'Review')}** \n*{t.get('topic', 'General')}*")
                                    with r_col3: st.markdown(f"📅 {t.get('date', 'N/A')} <br>⏱️ {t.get('duration_hours', 0)}h", unsafe_allow_html=True)
                            else:
                                st.caption("No tasks generated. Try regenerating.")

                            # AI explanation expander
                            if "explanation" in schedule_data and schedule_data["explanation"]:
                                with st.expander("🤖 AI's Logic Behind This Plan"):
                                    st.markdown(schedule_data["explanation"])

                    st.markdown("<div class='thin-divider'></div>", unsafe_allow_html=True)
                    st.error(f"⚠️ Exam countdown: {max(0, days_left)} days remaining ({exam_date.strftime('%b %d')})")

                st.subheader("📚 Course Curriculum")
                tag_html = "<div class='tag-container'>"
                for topic in course_info["topics"]:
                    tag_html += f"<div class='topic-tag'>{topic}</div>"
                tag_html += "</div>"
                st.markdown(tag_html, unsafe_allow_html=True)

                st.subheader("1. Topic-Level Mastery")

                fig_topics = px.bar(topic_df, x="Mastery", y="Topic", orientation='h',
                                    color="Mastery", color_continuous_scale='Sunset',
                                    hover_data={"Mastery": True, "Topic": True, "Trend": True})
                fig_topics.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                         font_color="white", xaxis=dict(range=[0, 100]))
                st.plotly_chart(fig_topics, use_container_width=True)

                st.subheader("2. Performance Diagnostic (Gap vs. Careless)")

                # Diagnostic legend
                st.markdown("""
                    <div style="background-color: rgba(255,255,255,0.03); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 25px;">
                        <div style="display: flex; justify-content: space-between; gap: 20px; margin-bottom: 15px;">
                            <div style="flex: 1;">
                                <h5 style="margin: 0 0 8px 0; color: #FDE047; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Core Metrics</h5>
                                <p style="font-size: 13px; color: #CBD5E1; line-height: 1.6;">
                                    <strong>Accuracy:</strong> Percentage of total possible points earned.<br>
                                    <strong>Avg. Time Ratio:</strong> Individual time relative to peer average.
                                </p>
                            </div>
                            <div style="flex: 1; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;">
                                <h5 style="margin: 0 0 8px 0; color: #FDE047; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Benchmarks</h5>
                                <p style="font-size: 13px; color: #CBD5E1; line-height: 1.6;">
                                    <strong>70% Accuracy:</strong> Target proficiency threshold.<br>
                                    <strong>1.0 Time Ratio:</strong> Efficiency parity with peers.
                                </p>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                    <div style="display: flex; gap: 20px; margin-bottom: 15px; font-size: 13px;">
                        <div style="display: flex; align-items: center; gap: 8px;"><div style="width: 12px; height: 12px; background-color: #FF7369; border-radius: 50%;"></div><span style="color: #CBD5E1;">= Genuine Weakness (slow + wrong)</span></div>
                        <div style="display: flex; align-items: center; gap: 8px;"><div style="width: 12px; height: 12px; background-color: #4CAF50; border-radius: 50%;"></div><span style="color: #CBD5E1;">= Expert</span></div>
                        <div style="display: flex; align-items: center; gap: 8px;"><div style="width: 12px; height: 12px; background-color: #FFD54F; border-radius: 50%;"></div><span style="color: #CBD5E1;">= Careless (fast + wrong)</span></div>
                        <div style="display: flex; align-items: center; gap: 8px;"><div style="width: 12px; height: 12px; background-color: #529CCA; border-radius: 50%;"></div><span style="color: #CBD5E1;">= Good</span></div>
                    </div>
                """, unsafe_allow_html=True)

                chart_range = max(abs(1 - topic_df["Time Ratio"].min()), abs(topic_df["Time Ratio"].max() - 1)) * 1.2
                if chart_range == 0:
                    chart_range = 0.5
                lower_x, upper_x = 1 - chart_range, 1 + chart_range

                fig_diag = px.scatter(topic_df, x="Time Ratio", y="Accuracy", text="Topic",
                                      color="Accuracy", size=[20]*len(topic_df),
                                      color_continuous_scale='RdYlGn',
                                      labels={"Accuracy": "Accuracy (%)", "Time Ratio": "Average Time Ratio"},
                                      hover_data=["Trend"])
                fig_diag.update_layout(shapes=[
                    dict(type="rect", x0=1, y0=0, x1=upper_x, y1=70, fillcolor="#FF7369", opacity=0.2, layer="below", line_width=0),
                    dict(type="rect", x0=lower_x, y0=0, x1=1, y1=70, fillcolor="#FFD54F", opacity=0.2, layer="below", line_width=0),
                    dict(type="rect", x0=1, y0=70, x1=upper_x, y1=100, fillcolor="#529CCA", opacity=0.2, layer="below", line_width=0),
                    dict(type="rect", x0=lower_x, y0=70, x1=1, y1=100, fillcolor="#4CAF50", opacity=0.2, layer="below", line_width=0)
                ])
                fig_diag.add_hline(y=70, line_dash="dash", line_color="white", opacity=0.3)
                fig_diag.add_vline(x=1, line_dash="dash", line_color="white", opacity=0.3)
                fig_diag.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                       font_color="white", yaxis=dict(range=[0, 100]),
                                       xaxis=dict(range=[lower_x, upper_x]))
                st.plotly_chart(fig_diag, use_container_width=True)

                st.markdown("---")
                ins_col1, ins_spacer, ins_col2 = st.columns([0.47, 0.06, 0.47])
                
                with ins_col1:
                    st.subheader("💡 AI Explanations")

                    # [THEIRS] Collapsible priority formula explanation (updated to 70/10/20)
                    with st.expander("ⓘ How is Priority Calculated?", expanded=False):
                        st.markdown("""
Priority ranks which topics need your attention most (0 = low, 1 = urgent).

$$Priority = \\alpha \\cdot (1 - Mastery) + \\beta \\cdot P_{weakness} + \\gamma \\cdot P_{trend}$$

Where $\\alpha = 0.7$, $\\beta = 0.1$, $\\gamma = 0.2$:

- $(1 - Mastery)$: Lower mastery → higher priority. Mastery uses **Ebbinghaus time-decay**, so inactive topics naturally rise in urgency.
- $P_{weakness}$: Penalty of **1.0** if accuracy < 70%, else **0**. Flags topics where you're consistently getting answers wrong.
- $P_{trend}$: **0.75** if regressing, **0.50** if stagnant, **0.25** if improving. Declining trends get escalated.

Topics are sorted by this score — the highest becomes your most urgent task.
                        """)

                    # [THEIRS] AI Explanation with caching + spinner
                    plan_cache_key = f"ai_plan_{course_name}"
                    if plan_cache_key not in st.session_state:
                        with st.spinner("🤖 AI is analyzing your neural data and generating a plan..."):
                            if LOGIC_AVAILABLE and hasattr(logic, 'get_explanation_feedback'):
                                st.session_state[plan_cache_key] = logic.get_explanation_feedback(course_name, topic_df)
                            else:
                                st.session_state[plan_cache_key] = "⚠️ Backend logic module disconnected. Cannot generate AI plan."

                    # Styled GPT output — use container so markdown renders properly
                    with st.container(border=True):
                        st.markdown(st.session_state[plan_cache_key])

                    st.markdown("### ✅ Mastered")
                    completed_df = topic_df[topic_df["Mastery"] >= 75].sort_values("Mastery", ascending=False)
                    if not completed_df.empty:
                        for _, row in completed_df.iterrows():
                            c_col1, c_col2 = st.columns([0.6, 0.4])
                            with c_col1:
                                if st.button(f"✓ {row['Topic']}", key=f"comp_btn_{row['Topic']}"):
                                    st.session_state.deep_dive_topic = row['Topic']
                                    st.rerun()
                            with c_col2:
                                cls, arrow = get_trend_parts(row['Trend'])
                                st.markdown(f"<div class='trend-tag-final {cls}'><span class='trend-arrow'>{arrow}</span> {row['Trend']}</div>", unsafe_allow_html=True)
                    else:
                        st.caption("No topics fully mastered yet.")

                with ins_col2:
                    st.subheader("📝 What's Next")
                    topic_df_sorted = topic_df.sort_values("Priority", ascending=False)

                    urgent_df = topic_df_sorted[topic_df_sorted["Priority"] >= 0.6]
                    steady_df = topic_df_sorted[(topic_df_sorted["Priority"] >= 0.3) & (topic_df_sorted["Priority"] < 0.6)]
                    maintenance_df = topic_df_sorted[topic_df_sorted["Priority"] < 0.3]

                    def render_block(df_block, title, marker_class):
                        if df_block.empty:
                            return
                        with st.container(border=True):
                            st.markdown(f'<div class="{marker_class}" style="display:none"></div>', unsafe_allow_html=True)
                            st.markdown(f"**{title}**")
                            for _, row in df_block.iterrows():
                                r_col1, r_col2 = st.columns([0.6, 0.4])
                                with r_col1:
                                    pri_score = int(row['Priority'] * 100)
                                    if st.button(f"{row['Topic']} (Pri: {pri_score})", key=f"next_btn_{row['Topic']}"):
                                        st.session_state.deep_dive_topic = row['Topic']
                                        st.rerun()
                                with r_col2:
                                    cls, arrow = get_trend_parts(row['Trend'])
                                    st.markdown(f"<div class='trend-tag-final {cls}'><span class='trend-arrow'>{arrow}</span> {row['Trend']}</div>", unsafe_allow_html=True)

                    render_block(urgent_df, "IMMEDIATE ATTENTION (High Pri)", "urgent-marker")
                    render_block(steady_df, "POLISH REQUIRED (Med Pri)", "polish-marker")
                    render_block(maintenance_df, "MAINTENANCE (Low Pri)", "polish-marker")


# ==================================================================================
# PAGE: SETTINGS
# ==================================================================================
elif st.session_state.page == "Settings":
    with col_content:
        st.title("⚙️ Settings")

        # --- Student Profile ---
        st.subheader("👤 Student Profile")
        with st.container(border=True):
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                st.text_input("Name", value="Alex Chen", disabled=True)
                st.text_input("Student ID", value="AX-2026-0471", disabled=True)
            with p_col2:
                st.text_input("Email", value="alex.chen@university.edu", disabled=True)
                st.text_input("Institution", value="National University", disabled=True)

        st.markdown("---")

        # --- AI Agent Settings ---
        st.subheader("🤖 AI Agent Configuration")
        with st.container(border=True):
            ai_col1, ai_col2 = st.columns(2)
            with ai_col1:
                model_options = ["gpt-4o-mini", "gpt-4o"]
                model_idx = model_options.index(st.session_state.settings_ai_model)
                new_model = st.selectbox("AI Model", model_options, index=model_idx)
                st.session_state.settings_ai_model = new_model
            with ai_col2:
                new_temp = st.slider("Temperature (Creativity)", min_value=0.0, max_value=1.0,
                                     value=st.session_state.settings_ai_temp, step=0.1)
                st.session_state.settings_ai_temp = new_temp
            st.caption("💡 Lower temperature = more precise answers. Higher = more creative responses.")

        st.markdown("---")

        # --- Mastery Model ---
        st.subheader("🧠 Mastery Model (Ebbinghaus Decay)")
        with st.container(border=True):
            new_decay = st.slider("Decay Constant (λ)", min_value=0.05, max_value=0.50,
                                  value=st.session_state.settings_decay_constant, step=0.01,
                                  help="Controls how quickly mastery decays over time. Higher = faster forgetting.")
            st.session_state.settings_decay_constant = new_decay

            # Live preview
            preview_weeks = np.arange(0, 13, 1)
            preview_mastery = [100 * np.exp(-new_decay * w) for w in preview_weeks]
            fig_decay = go.Figure()
            fig_decay.add_trace(go.Scatter(x=preview_weeks.tolist(), y=preview_mastery, mode='lines+markers',
                                           line=dict(color='#FDE047', width=2), marker=dict(size=5),
                                           name='Projected Decay'))
            fig_decay.add_hline(y=75, line_dash="dash", line_color="#EF4444", opacity=0.5,
                               annotation_text="75% Mastery Threshold")
            fig_decay.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                    font_color="white", height=250,
                                    xaxis_title="Weeks Since Last Practice", yaxis_title="Mastery (%)",
                                    yaxis=dict(range=[0, 105]), margin=dict(t=20, b=40))
            st.plotly_chart(fig_decay, use_container_width=True)
            st.caption(f"At λ = {new_decay:.2f}, mastery drops below 75% after ~{max(1, round(np.log(100/75) / new_decay, 1))} weeks of inactivity.")

        st.markdown("---")

        # --- Notification Preferences ---
        st.subheader("🔔 Notification Preferences")
        with st.container(border=True):
            st.session_state.settings_notif_weekly = st.toggle(
                "📧 Email weekly progress reports", value=st.session_state.settings_notif_weekly)
            st.session_state.settings_notif_remind = st.toggle(
                "⏰ Remind me to study (daily nudge)", value=st.session_state.settings_notif_remind)
            st.caption("Notifications are not yet active in this beta version.")

        st.markdown("---")

        # --- Data Management ---
        st.subheader("🗄️ Data Management")
        with st.container(border=True):
            dm_col1, dm_col2 = st.columns(2)
            with dm_col1:
                if st.button("🗑️ Clear Cached Data"):
                    for key in list(st.session_state.keys()):
                        if key.startswith("ai_plan_") or key.startswith("goal_plan_"):
                            del st.session_state[key]
                    st.toast("✅ Cached AI plans cleared!")
            with dm_col2:
                if st.button("📄 Export Report as PDF"):
                    st.toast("🚧 PDF export coming soon!")

        st.markdown("---")

        # --- About ---
        st.subheader("ℹ️ About AxonAI")
        with st.container(border=True):
            st.markdown("""
**AxonAI v1.0** — Intelligent Study Analytics Platform

Built with **Streamlit** + **OpenAI GPT-4o** + **Ebbinghaus Forgetting Curve**

Core algorithms: Time-decayed mastery modeling, four-quadrant diagnostic classification, 
adaptive priority scoring, and LLM-powered explainable study planning.

*Developed for NTU Deep Learning Week (DLW) Hackathon 2026*
            """)

# ==================================================================================
# AI AGENT PANEL
# ==================================================================================
with col_agent:
    if st.session_state.chat_expanded:
        st.markdown("""<div class='chat-header'>
            <span class='chat-header-title'>🤖 AI Study Agent</span>
        </div>""", unsafe_allow_html=True)
        st.markdown("<div class='chat-body'>", unsafe_allow_html=True)
        if st.button("➡️ Minimize"):
            toggle_chat()
            st.rerun()
        chat_container = st.container(height=480)
        with chat_container:
            for msg in st.session_state.messages:
                st.chat_message(msg["role"]).write(msg["content"])
        if prompt := st.chat_input("Ask about your progress..."):
            st.session_state.messages.append({"role": "user", "content": prompt})

            with chat_container:
                st.chat_message("user").write(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("🧠 Accessing neural context..."):
                        if LOGIC_AVAILABLE and hasattr(logic, 'get_ai_feedback'):
                            # Get current course + cached explanation plan + goal plan for context injection
                            current_course = st.session_state.selected_course
                            current_plan = ""
                            if current_course:
                                current_plan = st.session_state.get(f"ai_plan_{current_course}", "")

                            # Get goal mode schedule if active
                            current_goal_plan = ""
                            if current_course and f"goal_plan_{current_course}" in st.session_state:
                                current_goal_plan = json.dumps(st.session_state[f"goal_plan_{current_course}"])

                            ai_response = logic.get_ai_feedback(
                                prompt, COURSE_DATA, st.session_state.messages,
                                current_course=current_course,
                                current_plan=current_plan,
                                current_goal_plan=current_goal_plan
                            )
                        else:
                            ai_response = "Backend AI integration unavailable. Please check your OpenAI API key configuration."

                        st.write(ai_response)

            st.session_state.messages.append({"role": "assistant", "content": ai_response})
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        if st.button("⬅️ AI"):
            toggle_chat()
            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)