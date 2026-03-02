import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
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
    
    .stButton>button {{ background-color: #2563EB; color: #FFFFFF !important; font-weight: bold; border-radius: 8px; border: none; width: 100%; }}
    
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

    /* WHATS NEXT COLOR BLOCKS */
    .whats-next-block {{
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 10px;
    }}
    .bg-urgent-block {{ background-color: rgba(239, 68, 68, 0.3) !important; border: 1px solid rgba(239, 68, 68, 0.4); }}
    .bg-polish-block {{ background-color: rgba(253, 224, 71, 0.2) !important; border: 1px solid rgba(253, 224, 71, 0.3); }}
    .bg-stable-block {{ background-color: rgba(34, 197, 94, 0.2) !important; border: 1px solid rgba(34, 197, 94, 0.3); }}

    /* TREND TAG STYLING */
    .trend-tag-final {{
        padding: 8px 12px;
        border-radius: 30px;
        font-size: 13px;
        font-weight: 700;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
        min-width: 120px;
        margin-top: 5px;
    }}
    .trend-regressing {{ background-color: #ef4444; color: white !important; }}
    .trend-stagnant {{ background-color: #fde047; color: #000 !important; }}
    .trend-improving {{ background-color: #22c55e; color: white !important; }}

    /* Divider */
    .thin-divider {{ border-top: 1px solid rgba(255,255,255,0.1); margin: 15px 0; }}

    /* Card Hover Effect */
    div[data-testid="stVerticalBlock"] > div:has(div.card-click) {{ transition: transform 0.2s ease-in-out; }}
    div[data-testid="stVerticalBlock"] > div:has(div.card-click):hover {{ transform: scale(1.02); cursor: pointer; }}

    /* RIGHT SIDE CHAT STYLING */
    .right-chat-container {{
        position: fixed;
        right: 0;
        top: 50px;
        height: 100vh;
        background-color: #111827;
        border-left: 2px solid #1E293B;
        z-index: 1000;
        transition: width 0.3s ease;
        padding: 20px;
        width: {"350px" if st.session_state.chat_expanded else "60px"};
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
        "avg_time": [15, 45, 120, 300, 80, 95, 350] 
    },
    "Physics I": {
        "topics": ["Kinematics", "Dynamics", "Work & Energy", "Momentum", "Rotational Motion", "Gravity", "Oscillations"],
        "mastery": [45, 50, 42, 60, 30, 55, 40],
        "avg_time": [10, 80, 75, 90, 280, 60, 110]
    }
}

# --- 3. STATE MANAGEMENT ---
if "page" not in st.session_state: st.session_state.page = "Dashboard"
if "selected_course" not in st.session_state: st.session_state.selected_course = None
if "deep_dive_topic" not in st.session_state: st.session_state.deep_dive_topic = None
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! Diagnostic centers are now normalized. 0 is your average speed. Ready to analyze?"}]

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

# Adjust column ratio based on chat state
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
        
        # Unified Study Plan (Checkboxes)
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
            
            # --- NEW NEURAL NETWORK VISUALIZATION CHART ---
            st.subheader("🧠 Neural Retention & Decay Model")
            st.caption("Visualizing the 'Why': Topics are prioritized when current retention drops below the Stability Threshold.")
            
            # Simulated Neural Data
            time_steps = np.arange(0, 10, 1)
            retention = 100 * np.exp(-0.15 * time_steps) # Forgetting curve
            stability_threshold = [75] * len(time_steps)
            
            neural_df = pd.DataFrame({
                "Days Since Review": time_steps,
                "Retention Strength (%)": retention,
                "Stability Threshold": stability_threshold
            })
            
            fig_neural = px.line(neural_df, x="Days Since Review", y=["Retention Strength (%)", "Stability Threshold"],
                                 color_discrete_map={"Retention Strength (%)": "#FDE047", "Stability Threshold": "#EF4444"})
            
            fig_neural.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(17, 24, 39, 0.5)', 
                font_color="white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            # Add highlighting for the 'Danger Zone' (where retention < threshold)
            fig_neural.add_vrect(x0=2, x1=9, fillcolor="red", opacity=0.1, layer="below", line_width=0, annotation_text="Active Decay Phase")
            
            st.plotly_chart(fig_neural, use_container_width=True)
            
            diag_col1, diag_col2 = st.columns(2)
            with diag_col1:
                st.subheader("Neural Path Analysis")
                st.write("Our model traced your error to a **Retrieval Gap**. You correctly identified the formula but failed the execution phase.")
                st.progress(0.4)
                st.caption("Synaptic Strength: Weak")
            with diag_col2:
                st.subheader("Time Allocation")
                st.write("You spent 45% more time on this topic than the quiz average.")
            st.info(f"💡 **AI Diagnostic:** {topic_name} moved to 'Immediate Attention' because your synaptic retrieval speed dropped by 12% since your last session.")

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
                
                # --- NEW REPLACEMENT: TABLE-STYLE CHECKLIST WITH CHECKBOXES ---
                st.markdown("### 📝 Exam Prep Checklist")
                
                # Updated Data Structure to include Hours
                exam_tasks = [
                    {"topic": course_info["topics"][0], "act": "Past Paper Drill", "hours": "2.5h", "due": "Mar 08"},
                    {"topic": course_info["topics"][1], "act": "Blitz-Drill Retake", "hours": "1.0h", "due": "Mar 10"},
                    {"topic": course_info["topics"][2], "act": "Neural Review", "hours": "1.5h", "due": "Mar 12"}
                ]

                # Table Header
                h_col1, h_col2, h_col3, h_col4 = st.columns([0.1, 0.4, 0.25, 0.25])
                h_col2.caption("TASK")
                h_col3.caption("EST. TIME")
                h_col4.caption("DUE DATE")

                for i, t in enumerate(exam_tasks):
                    r_col1, r_col2, r_col3, r_col4 = st.columns([0.1, 0.4, 0.25, 0.25])
                    with r_col1:
                        # Functional Checkbox
                        st.checkbox("", key=f"check_{course_name}_{i}")
                    with r_col2:
                        st.markdown(f"**{t['act']}** \n*{t['topic']}*")
                    with r_col3:
                        st.markdown(f"⏱️ {t['hours']}")
                    with r_col4:
                        st.markdown(f"📅 {t['due']}")
                
                st.markdown("<div class='thin-divider'></div>", unsafe_allow_html=True)
                
                deadline = st.session_state.course_deadlines[course_name]
                days_left = (deadline - datetime.now()).days
                st.error(f"⚠️ Exam countdown: {days_left} days remaining ({deadline.strftime('%b %d')})")
                # --- END OF REPLACEMENT ---
            
            st.subheader("📚 Course Curriculum")
            st.caption("Click a topic to dive into specific neural diagnostics.")
            tag_html = "<div class='tag-container'>"
            for topic in course_info["topics"]:
                tag_html += f"<div class='topic-tag'>{topic}</div>"
            tag_html += "</div>"
            st.markdown(tag_html, unsafe_allow_html=True)
            
            st.subheader("1. Topic-Level Mastery")
            topic_df = pd.DataFrame({
                "Topic": course_info["topics"], 
                "Mastery": course_info["mastery"],
                "Avg Time (s)": course_info["avg_time"]
            })
            
            mean_time = topic_df["Avg Time (s)"].mean()
            topic_df["Time Deviation"] = topic_df["Avg Time (s)"] - mean_time
            
            fig_topics = px.bar(topic_df, x="Mastery", y="Topic", orientation='h', color="Mastery", color_continuous_scale='Sunset')
            fig_topics.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig_topics, use_container_width=True)

            st.subheader("2. Performance Diagnostic (Gap vs. Careless)")
            max_dev = max(abs(topic_df["Time Deviation"].min()), abs(topic_df["Time Deviation"].max())) * 1.2

            fig_diag = px.scatter(
                topic_df, 
                x="Mastery", 
                y="Time Deviation", 
                text="Topic",
                color="Mastery",
                size=[20]*len(topic_df),
                color_continuous_scale='RdYlGn',
                labels={"Mastery": "Accuracy (%)", "Time Deviation": "Time Deviation (Seconds)"}
            )
            
            fig_diag.update_layout(
                shapes=[
                    dict(type="rect", x0=0, y0=0, x1=70, y1=max_dev, fillcolor="#FFD54F", opacity=0.2, layer="below", line_width=0),
                    dict(type="rect", x0=0, y0=-max_dev, x1=70, y1=0, fillcolor="#FF7369", opacity=0.2, layer="below", line_width=0),
                    dict(type="rect", x0=70, y0=0, x1=100, y1=max_dev, fillcolor="#529CCA", opacity=0.2, layer="below", line_width=0),
                    dict(type="rect", x0=70, y0=-max_dev, x1=100, y1=0, fillcolor="#4CAF50", opacity=0.2, layer="below", line_width=0),
                ]
            )
            
            fig_diag.add_vline(x=70, line_dash="dash", line_color="white", opacity=0.3)
            fig_diag.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
            fig_diag.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='white')))
            fig_diag.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white",
                                xaxis=dict(range=[0, 100], gridcolor='rgba(255,255,255,0.05)'),
                                yaxis=dict(range=[-max_dev, max_dev], gridcolor='rgba(255,255,255,0.05)'))
            st.plotly_chart(fig_diag, use_container_width=True)

            st.markdown("---")
            ins_col1, ins_col2 = st.columns(2)
            with ins_col1:
                st.subheader("💡 AI Suggestions")
                st.info(f"The Neural Net detected a recurring bottleneck in your retrieval speed.")
            
            with ins_col2:
                st.subheader("📝 What's next")

                def render_block(df, title, css_class):
                    if df.empty: return
                    st.markdown(f"<div class='whats-next-block {css_class}'>", unsafe_allow_html=True)
                    st.markdown(f"**{title}**")
                    for _, row in df.iterrows():
                        r_col1, r_col2 = st.columns([0.6, 0.4])
                        with r_col1:
                            if st.button(row['Topic'], key=f"next_btn_{row['Topic']}"):
                                st.session_state.deep_dive_topic = row['Topic']
                                st.rerun()
                        with r_col2:
                            if row['Mastery'] > 75: txt, cls, arrow = "Improving", "trend-improving", "↑ +"
                            elif row['Mastery'] > 45: txt, cls, arrow = "Stagnant", "trend-stagnant", "→"
                            else: txt, cls, arrow = "Regressing", "trend-regressing", "↓ -"
                            st.markdown(f"<div class='trend-tag-final {cls}'>{arrow} {txt}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("<div class='thin-divider'></div>", unsafe_allow_html=True)

                urgent_df = topic_df[topic_df["Mastery"] < 50].sort_values("Mastery")
                steady_df = topic_df[(topic_df["Mastery"] >= 50) & (topic_df["Mastery"] < 75)].sort_values("Mastery")
                maintenance_df = topic_df[topic_df["Mastery"] >= 75].sort_values("Mastery")

                render_block(urgent_df, "IMMEDIATE ATTENTION", "bg-urgent-block")
                render_block(steady_df, "POLISH REQUIRED", "bg-polish-block")
                render_block(maintenance_df, "MAINTENANCE", "bg-stable-block")

# AI AGENT POP-UP (RIGHT HAND SIDE)
with col_agent:
    if st.session_state.chat_expanded:
        if st.button("➡️ Minimize AI"):
            toggle_chat()
            st.rerun()
        
        st.subheader("🤖 AI Study Agent")
        chat_container = st.container(height=500)
        with chat_container:
            for msg in st.session_state.messages:
                st.chat_message(msg["role"]).write(msg["content"])
        if prompt := st.chat_input("Ask about your progress..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.rerun()
    else:
        if st.button("⬅️ AI"):
            toggle_chat()
            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)