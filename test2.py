import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(page_title="AxonAI", layout="wide", initial_sidebar_state="expanded")

# Initialize Chat Visibility State
if "chat_expanded" not in st.session_state:
    st.session_state.chat_expanded = True

# Initialize Goal Mode states per course
if "goal_modes" not in st.session_state:
    st.session_state.goal_modes = {"Calculus II": False, "Physics I": False}
if "course_deadlines" not in st.session_state:
    st.session_state.course_deadlines = {
        "Calculus II": datetime(2026, 3, 15),
        "Physics I": datetime(2026, 3, 20)
    }

def toggle_chat():
    st.session_state.chat_expanded = not st.session_state.chat_expanded

st.markdown(f"""
    <style>
    
    
    /* Main Background */
    .stApp {{ background-color: #0B0E14; color: #FFFFFF; }}
    
    /* HIDE DEFAULT HEADER BUT KEEP SIDEBAR TOGGLE VISIBLE */
    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}
    .stAppDeployButton {{display:none;}}
    #MainMenu {{visibility: hidden;}}
    
    /* ENSURE SIDEBAR TOGGLE IS ALWAYS VISIBLE AND YELLOW */
    button[data-testid="sidebar-toggle"] {{
        background-color: #FDE047 !important;
        border-radius: 50% !important;
        left: 10px !important;
        top: 10px !important;
        z-index: 1001 !important;
    }}
            
            

    /* CUSTOM YELLOW GLOWING HEADER */
    .custom-header {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 50px;
        background: rgba(17, 24, 39, 0.7); 
        backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(253, 224, 71, 0.5); 
        box-shadow: 0px 4px 20px rgba(253, 224, 71, 0.2); 
        z-index: 999;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .header-title {{
        color: #FDE047 !important; 
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        letter-spacing: 2px;
        font-size: 20px;
        text-shadow: 0px 0px 8px rgba(253, 224, 71, 0.4);
    }}

    /* GOAL TAG STYLING */
    .goal-tag {{
        background-color: #FDE047;
        color: #000000 !important;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: 800;
        font-size: 12px;
        display: inline-block;
        margin-bottom: 15px;
    }}

    .main-content {{ padding-top: 60px; }}

    h1, h2, h3, p, span, label {{ color: #FFFFFF !important; font-family: 'Inter', sans-serif; }}
    .stMarkdown p, .stCaption {{ color: #CBD5E1 !important; }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{ background-color: #111827 !important; border-right: 2px solid #1E293B; }}
    
    /* Metrics with Yellow Accent */
    div[data-testid="stMetric"] {{ 
        background-color: #1E293B; 
        border: 2px solid #FDE047; 
        padding: 20px; 
        border-radius: 12px; 
    }}
    
    /* REPLACED BUTTON STYLING: Less round, opaque, like reference */
    .stButton>button {{ 
        background-color: #3b82f6; 
        color: #FFFFFF !important; 
        font-weight: 500; 
        border-radius: 12px; 
        border: 1px solid rgba(255,255,255,0.2); 
        width: 100%; 
        padding: 8px;
    }}
    
    /* TAG STYLING */
    .tag-container {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }}
    .topic-tag {{
        padding: 6px 14px;
        border-radius: 20px;
        background-color: rgba(37, 99, 235, 0.5); 
        color: #FFFFFF !important;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.2);
        cursor: pointer;
        display: inline-block;
        margin: 4px;
    }}
    .topic-tag:hover {{ 
        background-color: rgba(96, 165, 250, 0.7) !important; 
        border-color: #60a5fa;
    }}

    /* CSS TARGETING FOR BUTTON BACKGROUND BLOCKS */
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

    /* TREND TAG STYLING - INCREASED OPACITY */
    .trend-tag-final {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 700;
        gap: 6px;
        min-width: 100px;
        margin-top: 5px;
        color: #FFFFFF !important;
    }}
    .trend-regressing {{ background-color: rgba(239, 68, 68, 0.45) !important; }}
    .trend-regressing .trend-arrow {{ color: #ff5f5f; }}
    
    .trend-stagnant {{ background-color: rgba(253, 224, 71, 0.45) !important; }}
    .trend-stagnant .trend-arrow {{ color: #fde047; }}
    
    .trend-improving {{ background-color: rgba(34, 197, 94, 0.45) !important; }}
    .trend-improving .trend-arrow {{ color: #4ade80; }}

    /* Divider */
    .thin-divider {{ border-top: 1px solid rgba(255,255,255,0.1); margin: 15px 0; }}

    /* Card Hover Effect */
    div[data-testid="stVerticalBlock"] > div:has(div.card-click) {{ transition: transform 0.2s ease-in-out; }}
    div[data-testid="stVerticalBlock"] > div:has(div.card-click):hover {{ transform: scale(1.02); cursor: pointer; }}

    /* RIGHT SIDE CHAT STYLING - UPDATED FOR 50% TRANSPARENCY & GLOW */
    [data-testid="column"]:nth-child(2) {{
        background: rgba(17, 24, 39, 0.5) !important; 
        backdrop-filter: blur(10px) !important;
        border-left: 1px solid rgba(253, 224, 71, 0.5) !important; 
        box-shadow: -4px 0px 20px rgba(253, 224, 71, 0.2) !important; 
        padding: 20px !important;
    }}

    .right-chat-container {{
        position: fixed;
        right: 0;
        top: 50px;
        height: 100vh;
        background-color: rgba(17, 24, 39, 0.5); 
        border-left: 1px solid rgba(253, 224, 71, 0.5); 
        box-shadow: -4px 0px 20px rgba(253, 224, 71, 0.2);
        z-index: 1000;
        transition: width 0.3s ease;
        padding: 20px;
        width: {"350px" if st.session_state.chat_expanded else "60px"};
    }}

    /* PROGRESS BAR: Thicker and Shorter in shape */
    div[data-testid="stProgress"] {{
        width: 100% !important;
    }}
    div[data-testid="stProgress"] > div > div > div > div {{
        background-color: #22c55e !important;
        height: 40px !important;
    }}
    </style>
    
    <div class="custom-header">
        <div class="header-title">🎓 AxonAI</div>
    </div>
    """, unsafe_allow_html=True)



# --- 2. DATA: TOPIC INVENTORY ---
COURSE_DATA = {
    "Calculus II": {
        "topics": ["Limits", "Derivatives", "Integrals", "Series", "Polar Coordinates", "Vector Functions", "Taylor Series"],
        "mastery": [92, 88, 85, 40, 70, 65, 38],
        "trends": ["Improving", "Improving", "Stagnant", "Regressing", "Stagnant", "Improving", "Regressing"],
        "avg_time": [15, 45, 120, 300, 80, 95, 350] 
    },
    "Physics I": {
        "topics": ["Kinematics", "Dynamics", "Work & Energy", "Momentum", "Rotational Motion", "Gravity", "Oscillations"],
        "mastery": [45, 50, 42, 80, 30, 85, 40],
        "trends": ["Improving", "Stagnant", "Regressing", "Improving", "Regressing", "Improving", "Stagnant"],
        "avg_time": [10, 80, 75, 90, 280, 60, 110]
    }
}

# --- 3. STATE MANAGEMENT ---
if "page" not in st.session_state: st.session_state.page = "Dashboard"
if "selected_course" not in st.session_state: st.session_state.selected_course = None
if "deep_dive_topic" not in st.session_state: st.session_state.deep_dive_topic = None
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! Diagnostic centers are now normalized. 1.0 is your average speed. Ready to analyze?"}]

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Settings & Status")
    st.markdown("---")
    if st.button("🏠 Dashboard"): 
        st.session_state.page = "Dashboard"
        st.session_state.selected_course = None
        st.session_state.deep_dive_topic = None
    if st.button("📖 My Courses"): 
        st.session_state.page = "Courses"
        st.session_state.selected_course = None
        st.session_state.deep_dive_topic = None
    if st.button("⚙️ Settings"): st.session_state.page = "Settings"
    st.markdown("---")
    
    # Goal Mode Logic (Sidebar)
    st.subheader("🎯 Course Goal Mode")
    if st.session_state.selected_course:
        current_course = st.session_state.selected_course
        st.session_state.goal_modes[current_course] = st.toggle(f"Intense Focus: {current_course}", value=st.session_state.goal_modes[current_course])
    else:
        st.caption("Select a course to enable Goal Mode.")

    st.markdown("---")
    st.write("🔥 **14 Day Streak**")
    st.write("🏆 **8 Badges Earned**")

# --- 5. LAYOUT ---
st.markdown("<div class='main-content'>", unsafe_allow_html=True) 

if st.session_state.chat_expanded:
    col_content, col_agent = st.columns([2.2, 1], gap="medium")
else:
    col_content, col_agent = st.columns([15, 1], gap="small")

# PAGE: DASHBOARD
if st.session_state.page == "Dashboard":
    with col_content:
        st.title("Student Command Center")
        m1, m2, m3 = st.columns(3)
        m1.metric("Overall Mastery", "78%", "+2%")
        m2.metric("Study Velocity", "1.2h/day", "-10%")
        m3.metric("Careless Rate", "15%", "-5%")
        st.markdown("---")
        
        st.subheader("📅 Unified Study Plan (Goal Mode Active)")
        active_goals = [c for c, active in st.session_state.goal_modes.items() if active]
        if active_goals:
            plan_data = [
                {"Date": "Mar 02", "Course": "Calculus II", "Task": "Integration Drill", "Status": True},
                {"Date": "Mar 03", "Course": "Physics I", "Task": "Momentum Lab", "Status": False},
                {"Date": "Mar 04", "Course": "AI Ethics", "Task": "Review Ch. 2", "Status": False},
            ]
            found_task = False
            for item in plan_data:
                if item['Course'] in active_goals:
                    st.checkbox(f"**{item['Date']}** | {item['Course']}: {item['Task']}", value=item['Status'], key=f"dash_{item['Task']}")
                    found_task = True
            if not found_task:
                st.info("No tasks scheduled for courses in Goal Mode.")
        else:
            st.info("Activate 'Goal Mode' in the sidebar for a specific course to see your study plan.")

        st.subheader("📈 Progress Tracking")
        chart_data = pd.DataFrame({"Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "Mastery": [60, 62, 61, 65, 70, 72, 78]})
        fig = px.area(chart_data, x="Day", y="Mastery", color_discrete_sequence=['#FDE047']) 
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)

# PAGE: COURSES
elif st.session_state.page == "Courses":
    with col_content:
        if st.session_state.deep_dive_topic:
            topic_name = st.session_state.deep_dive_topic
            if st.button("← Back to Analytics"):
                st.session_state.deep_dive_topic = None
                st.rerun()
            
            st.title(f"🔍 Deep Dive: {topic_name}")
            st.markdown(f"Neural breakdown for your last performance in **{st.session_state.selected_course}**.")
            
            st.subheader("🧠 Neural Retention & Decay Model (Weekly)")
            weeks = np.arange(0, 11, 1)
            mastery_vals = []
            current_m = 90
            for w in weeks:
                if w == 1: current_m = 92
                elif w == 5: current_m = 95
                else: current_m *= 0.96
                mastery_vals.append(current_m)
            
            accuracy_weeks = [1, 5]
            accuracy_vals = [85, 94]
            fig_neural = go.Figure()
            fig_neural.add_trace(go.Scatter(x=weeks, y=mastery_vals, mode='lines+markers', name='Mastery Level (%)', line=dict(color='#2563EB', dash='dot'), marker=dict(size=8), hovertemplate="Week: %{x}<br>Mastery: %{y:.1f}%<extra></extra>"))
            fig_neural.add_trace(go.Scatter(x=accuracy_weeks, y=accuracy_vals, mode='markers', name='Accuracy (Test Score)', marker=dict(color='#FDE047', size=12, symbol='diamond'), hovertemplate="Week: %{x}<br>Accuracy: %{y}%<extra></extra>"))
            fig_neural.add_shape(type="line", x0=0, y0=75, x1=10, y1=75, line=dict(color="#EF4444", width=2, dash="dash"))
            fig_neural.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(17, 24, 39, 0.5)', font_color="white", xaxis_title="Weeks Since Review", yaxis_title="Percentage (%)", yaxis=dict(range=[0, 105]), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white")))
            st.plotly_chart(fig_neural, use_container_width=True)

            # --- UPDATED MASTERY SECTION WITH TREND TAG ---
            current_mastery_pct = round(mastery_vals[0], 1)
            # Find the trend for the selected topic
            course_info = COURSE_DATA[st.session_state.selected_course]
            try:
                topic_idx = course_info["topics"].index(topic_name)
                txt = course_info["trends"][topic_idx]
            except:
                txt = "Stagnant"

            if txt == "Improving": cls, arrow = "trend-improving", "↑"
            elif txt == "Stagnant": cls, arrow = "trend-stagnant", "→"
            else: cls, arrow = "trend-regressing", "↓"

            st.write("📊 **Mastery Level**")
            p_col1, p_col2, p_col3 = st.columns([0.15, 0.1, 0.75], gap="small")
            with p_col1: st.progress(current_mastery_pct / 100)
            with p_col2: st.write(f"**{current_mastery_pct}%**")
            with p_col3: st.markdown(f"<div class='trend-tag-final {cls}' style='margin-top: -5px;'><span class='trend-arrow'>{arrow}</span> {txt}</div>", unsafe_allow_html=True)
            
            # --- START STRATEGIC DIAGNOSTICS DESCRIPTION BOX ---
            st.subheader("Description")
            with st.container(border=True):
                st.markdown("""
                #### **Mastery Level**
                Mastery measures your high-retention knowledge, calculated using a **Time-Decayed Weighted Average**. By incorporating the Ebbinghaus Forgetting Curve, we apply a decay weight $w_i = e^{-\lambda \\Delta t_i}$ based on the time since your last review.
                
                $$Mastery = \\frac{\\sum (w_i \\cdot C_i)}{\\sum w_i}$$
                
                *Older scores lose weight exponentially. If study activity remains stagnant for too long, the Mastery level will drop sharply, reflecting neural decay.*

                #### **Accuracy Level**
                Accuracy represents your raw test performance in any given assessment period. The **Slope** of these scores determines your current trajectory:
                
                * **Improving:** Slope $> 0.5$
                * **Stagnant:** Slope $\approx 0.5$
                * **Regressing:** Slope $< 0.5$
                """)
            # --- END STRATEGIC DIAGNOSTICS DESCRIPTION BOX ---
            
            st.info(f"💡 **AI Diagnostic:** {topic_name} moved to 'Immediate Attention'.")

        elif st.session_state.selected_course is None:
            st.title("My Courses")
            st.markdown("Select a course card to see **Deep Data Analytics**.")
            c1, c2 = st.columns(2)
            with c1:
                with st.container(border=True):
                    st.markdown("<div class='card-click'></div>", unsafe_allow_html=True)
                    st.subheader("📐 Calculus II")
                    st.write(f"Topics: {', '.join(COURSE_DATA['Calculus II']['topics'][:3])}...")
                    st.progress(0.78)
                    if st.button("Open Calculus Analytics", key="calc_nav"):
                        st.session_state.selected_course = "Calculus II"
                        st.rerun()
            with c2:
                with st.container(border=True):
                    st.markdown("<div class='card-click'></div>", unsafe_allow_html=True)
                    st.subheader("⚛️ Physics I")
                    st.write(f"Topics: {', '.join(COURSE_DATA['Physics I']['topics'][:3])}...")
                    st.progress(0.45)
                    st.warning("⚠️ High 'Knowledge Decay' detected")
                    if st.button("Open Physics Analytics", key="phys_nav"):
                        st.session_state.selected_course = "Physics I"
                        st.rerun()
        else:
            course_name = st.session_state.selected_course
            course_info = COURSE_DATA[course_name]
            if st.button("← Back to Courses"):
                st.session_state.selected_course = None
                st.rerun()

            st.title(f"📊 {course_name} Analytics")
            if st.session_state.goal_modes[course_name]:
                st.markdown("<div class='goal-tag'>GOAL: EXAM</div>", unsafe_allow_html=True)
                st.markdown("### 📝 Exam Prep Checklist")
                exam_tasks = [
                    {"topic": course_info["topics"][0], "act": "Past Paper Drill", "hours": "2.5h", "due": "Mar 08"},
                    {"topic": course_info["topics"][1], "act": "Blitz-Drill Retake", "hours": "1.0h", "due": "Mar 10"},
                    {"topic": course_info["topics"][2], "act": "Neural Review", "hours": "1.5h", "due": "Mar 12"}
                ]
                h_col1, h_col2, h_col3, h_col4 = st.columns([0.1, 0.4, 0.25, 0.25])
                h_col2.caption("TASK"); h_col3.caption("EST. TIME"); h_col4.caption("DUE DATE")
                for i, t in enumerate(exam_tasks):
                    r_col1, r_col2, r_col3, r_col4 = st.columns([0.1, 0.4, 0.25, 0.25])
                    with r_col1: st.checkbox("", key=f"check_{course_name}_{i}")
                    with r_col2: st.markdown(f"**{t['act']}** \n*{t['topic']}*")
                    with r_col3: st.markdown(f"⏱️ {t['hours']}")
                    with r_col4: st.markdown(f"📅 {t['due']}")
                st.markdown("<div class='thin-divider'></div>", unsafe_allow_html=True)
                deadline = st.session_state.course_deadlines[course_name]
                days_left = (deadline - datetime.now()).days
                st.error(f"⚠️ Exam countdown: {days_left} days remaining ({deadline.strftime('%b %d')})")
            
            st.subheader("📚 Course Curriculum")
            tag_html = "<div class='tag-container'>"
            for topic in course_info["topics"]:
                tag_html += f"<div class='topic-tag'>{topic}</div>"
            tag_html += "</div>"
            st.markdown(tag_html, unsafe_allow_html=True)
            
            st.subheader("1. Topic-Level Mastery")
            topic_df = pd.DataFrame({"Topic": course_info["topics"], "Mastery": course_info["mastery"], "Trend": course_info["trends"], "Avg Time (s)": course_info["avg_time"]})
            fig_topics = px.bar(topic_df, x="Mastery", y="Topic", orientation='h', color="Mastery", color_continuous_scale='Sunset', hover_data={"Mastery": True, "Topic": True, "Trend": True})
            fig_topics.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig_topics, use_container_width=True)

            st.subheader("2. Performance Diagnostic (Gap vs. Careless)")
            
            # --- START DIAGNOSTIC DESCRIPTION ---
            st.markdown("""
                <div style="background-color: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 25px;">
                    <div style="display: flex; justify-content: space-between; gap: 20px; margin-bottom: 15px;">
                        <div style="flex: 1;">
                            <h5 style="margin: 0 0 8px 0; color: #FDE047; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Core Metrics</h5>
                            <p style="font-size: 13px; color: #CBD5E1; line-height: 1.6;">
                                <strong>Accuracy:</strong> Percentage of total possible points earned within a specific topic.<br>
                                <strong>Avg. Time Ratio:</strong> Individual completion time relative to the global peer average.
                            </p>
                        </div>
                        <div style="flex: 1; border-left: 1px solid rgba(255, 255, 255, 0.1); padding-left: 20px;">
                            <h5 style="margin: 0 0 8px 0; color: #FDE047; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Benchmarks</h5>
                            <ul style="font-size: 13px; color: #CBD5E1; margin: 0; padding-left: 15px; line-height: 1.6;">
                                <li><strong>75% Accuracy:</strong> Target proficiency threshold for passing.</li>
                                <li><strong>1.0 Time Ratio:</strong> Efficiency parity with the average test-taker population.</li>
                            </ul>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("""
                <div style="display: flex; gap: 20px; margin-bottom: 15px; font-size: 13px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 12px; height: 12px; background-color: #FF7369; border-radius: 50%;"></div>
                        <span style="color: #CBD5E1;">= Skill Gap</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 12px; height: 12px; background-color: #4CAF50; border-radius: 50%;"></div>
                        <span style="color: #CBD5E1;">= Expert</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 12px; height: 12px; background-color: #FFD54F; border-radius: 50%;"></div>
                        <span style="color: #CBD5E1;">= Careless</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 12px; height: 12px; background-color: #529CCA; border-radius: 50%;"></div>
                        <span style="color: #CBD5E1;">= Good</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            # --- END DIAGNOSTIC DESCRIPTION ---

            mean_time = topic_df["Avg Time (s)"].mean()
            topic_df["Time Ratio"] = topic_df["Avg Time (s)"] / mean_time
            chart_range = max(abs(1 - topic_df["Time Ratio"].min()), abs(topic_df["Time Ratio"].max() - 1)) * 1.2
            lower_x, upper_x = 1 - chart_range, 1 + chart_range
            fig_diag = px.scatter(topic_df, x="Time Ratio", y="Mastery", text="Topic", color="Mastery", size=[20]*len(topic_df), color_continuous_scale='RdYlGn', labels={"Mastery": "Accuracy (%)", "Time Ratio": "Average Time Ratio"}, hover_data=["Trend"])
            fig_diag.update_layout(shapes=[dict(type="rect", x0=1, y0=0, x1=upper_x, y1=70, fillcolor="#FFD54F", opacity=0.2, layer="below", line_width=0), dict(type="rect", x0=lower_x, y0=0, x1=1, y1=70, fillcolor="#FF7369", opacity=0.2, layer="below", line_width=0), dict(type="rect", x0=1, y0=70, x1=upper_x, y1=100, fillcolor="#529CCA", opacity=0.2, layer="below", line_width=0), dict(type="rect", x0=lower_x, y0=70, x1=1, y1=100, fillcolor="#4CAF50", opacity=0.2, layer="below", line_width=0)])
            fig_diag.add_hline(y=70, line_dash="dash", line_color="white", opacity=0.3); fig_diag.add_vline(x=1, line_dash="dash", line_color="white", opacity=0.3)
            fig_diag.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", yaxis=dict(range=[0, 100]), xaxis=dict(range=[lower_x, upper_x]))
            st.plotly_chart(fig_diag, use_container_width=True)

            st.markdown("---")
            ins_col1, ins_col2 = st.columns(2)
            with ins_col1:
                st.subheader("💡 AI Suggestions")
                st.info(f"The Neural Net detected a recurring bottleneck in your retrieval speed.")
                st.markdown("### ✅ Mastered")
                # FILTER: ONLY SHOW > 75
                completed_df = topic_df[topic_df["Mastery"] >= 75].sort_values("Mastery", ascending=False)
                if not completed_df.empty:
                    for _, row in completed_df.iterrows():
                        c_col1, c_col2 = st.columns([0.6, 0.4])
                        with c_col1:
                            if st.button(f"✓ {row['Topic']}", key=f"comp_btn_{row['Topic']}"):
                                st.session_state.deep_dive_topic = row['Topic']; st.rerun()
                        with c_col2:
                            txt = row['Trend']
                            if txt == "Improving": cls, arrow = "trend-improving", "↑"
                            elif txt == "Stagnant": cls, arrow = "trend-stagnant", "→"
                            else: cls, arrow = "trend-regressing", "↓"
                            st.markdown(f"<div class='trend-tag-final {cls}'><span class='trend-arrow'>{arrow}</span> {txt}</div>", unsafe_allow_html=True)
                else: st.caption("No topics fully mastered yet.")
            
            with ins_col2:
                st.subheader("📝 What's next")
                urgent_df = topic_df[topic_df["Mastery"] < 50].sort_values("Mastery")
                steady_df = topic_df[(topic_df["Mastery"] >= 50) & (topic_df["Mastery"] < 75)].sort_values("Mastery")

                def render_block(df, title, marker_class):
                    if df.empty: return
                    # Use container with border and a hidden CSS 'marker' class to apply background
                    with st.container(border=True):
                        st.markdown(f'<div class="{marker_class}" style="display:none"></div>', unsafe_allow_html=True)
                        st.markdown(f"**{title}**")
                        for _, row in df.iterrows():
                            r_col1, r_col2 = st.columns([0.6, 0.4])
                            with r_col1:
                                if st.button(row['Topic'], key=f"next_btn_{row['Topic']}"):
                                    st.session_state.deep_dive_topic = row['Topic']; st.rerun()
                            with r_col2:
                                txt = row['Trend']
                                if txt == "Improving": cls, arrow = "trend-improving", "↑"
                                elif txt == "Stagnant": cls, arrow = "trend-stagnant", "→"
                                else: cls, arrow = "trend-regressing", "↓"
                                st.markdown(f"<div class='trend-tag-final {cls}'><span class='trend-arrow'>{arrow}</span> {txt}</div>", unsafe_allow_html=True)

                render_block(urgent_df, "IMMEDIATE ATTENTION", "urgent-marker")
                render_block(steady_df, "POLISH REQUIRED", "polish-marker")

# AI AGENT POP-UP
with col_agent:
    if st.session_state.chat_expanded:
        if st.button("➡️ Minimize AI"): toggle_chat(); st.rerun()
        st.subheader("🤖 AI Study Agent")
        chat_container = st.container(height=500)
        with chat_container:
            for msg in st.session_state.messages: st.chat_message(msg["role"]).write(msg["content"])
        if prompt := st.chat_input("Ask about your progress..."):
            st.session_state.messages.append({"role": "user", "content": prompt}); st.rerun()
    else:
        if st.button("⬅️ AI"): toggle_chat(); st.rerun()

st.markdown("</div>", unsafe_allow_html=True)