import pandas as pd
import numpy as np
import json
from datetime import datetime
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")

# ==============================================================================
# Core Data Processing Pipeline
# ==============================================================================

def calculate_topic_mastery(df_topic, current_date, decay_constant=0.15):
    """
    Calculate the mastery of a single topic using Ebbinghaus forgetting curve based on weeks.
    Returns a value between 0.0 and 1.0.
    """
    if df_topic.empty:
        return 0.0

    weeks_ago = (current_date - df_topic['timestamp']).dt.total_seconds() / (7 * 24 * 3600)
    weeks_ago = np.maximum(weeks_ago, 0)

    # Decay weight: W = e^(-λ * t)
    weights = np.exp(-decay_constant * weeks_ago)

    # Historical weighted average baseline
    if np.sum(weights) == 0:
        historical_baseline = 0.0
    else:
        historical_baseline = np.sum(weights * df_topic['correct']) / np.sum(weights)

    # Global time gap penalty
    weeks_since_last_active = weeks_ago.min()
    final_mastery = historical_baseline * np.exp(-decay_constant * weeks_since_last_active)

    # [MINE] np.clip safety net
    return round(np.clip(final_mastery, 0.0, 1.0), 3)


def calculate_careless_weakness(df_topic):
    """
    Calculate four-quadrant metrics: Error Rate (E_r) and Relative Time Spent (R_t),
    and output P_weakness.
    """
    if df_topic.empty:
        return 0.0, 1.0, 0, "Normal/Mastered"

    e_r = 1.0 - df_topic['correct'].mean()

    avg_time_spent = df_topic['time_spent_s'].mean()
    avg_time_expected = df_topic['avg_time_all_users_s'].mean()
    r_t = avg_time_spent / avg_time_expected if avg_time_expected > 0 else 1.0

    # [MINE] Threshold at e_r > 0.3 (accuracy < 70%)
    p_weakness = 1.0 if e_r > 0.3 else 0.0

    if e_r > 0.3 and r_t < 1.0:
        category = "Careless Mistake"
    elif e_r > 0.3 and r_t >= 1.0:
        category = "Genuine Weakness"
    else:
        category = "Normal/Mastered"

    # [MINE] Return rounded values
    return round(e_r, 3), round(r_t, 3), p_weakness, category


def calculate_trend(df_topic):
    """
    Calculate trend (P_trend) and weekly accuracy using Linear Regression.
    """
    if df_topic.empty:
        return 0.5, "Stagnant", [], [], 0.0

    weekly_stats = df_topic.groupby('week')['correct'].mean().reset_index().sort_values('week')

    weeks = weekly_stats['week'].tolist()
    accuracies = (weekly_stats['correct'] * 100).tolist()

    if len(weekly_stats) > 1:
        # [THEIRS] np.polyfit linear regression for more robust slope
        slope, _ = np.polyfit(weeks, accuracies, 1)
    else:
        slope = 0.0

    # [THEIRS] Threshold 0.3 on percentage scale
    threshold = 0.3
    if slope > threshold:
        p_trend = 0.25
        trend_label = "Improving"
    elif slope < -threshold:
        p_trend = 0.75
        trend_label = "Regressing"
    else:
        p_trend = 0.50
        trend_label = "Stagnant"

    # [MINE] Return 5 values — slope as 5th for display in trend card
    return p_trend, trend_label, weeks, accuracies, slope


def process_student_dataframe(df):
    """
    Main controller interface: Outputs COURSE_DATA containing all features.
    Priority is normalized to 0.0 - 1.0 range.
    """
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    current_date = df['timestamp'].max()

    course_data_dict = {}
    courses = df['topic'].unique()

    for course in courses:
        course_df = df[df['topic'] == course]

        c_topics, c_mastery, c_avg_time = [], [], []
        c_er, c_rt, c_category = [], [], []
        c_priority, c_trend_label = [], []
        c_weekly_weeks, c_weekly_acc = [], []

        sub_topics = course_df['question_topic'].unique()

        for sub_topic in sub_topics:
            sub_df = course_df[course_df['question_topic'] == sub_topic].copy()

            # 1. Mastery
            mastery = calculate_topic_mastery(sub_df, current_date)

            # 2. Four-quadrant
            e_r, r_t, p_weakness, category = calculate_careless_weakness(sub_df)
            avg_time = int(sub_df['time_spent_s'].mean())

            # 3. Trend
            p_trend, trend_label, weeks_list, acc_list, _ = calculate_trend(sub_df)

            # 4. [THEIRS] Priority formula: 0.7 / 0.1 / 0.2 weights
            priority = 0.7 * (1.0 - mastery) + 0.1 * p_weakness + 0.2 * p_trend

            c_topics.append(sub_topic)
            c_mastery.append(mastery)
            c_avg_time.append(avg_time)
            c_er.append(e_r)
            c_rt.append(r_t)
            c_category.append(category)
            c_priority.append(round(priority, 3))
            c_trend_label.append(trend_label)
            c_weekly_weeks.append(weeks_list)
            c_weekly_acc.append(acc_list)

        course_data_dict[course] = {
            "topics": c_topics,
            "mastery": c_mastery,
            "avg_time": c_avg_time,
            "e_r": c_er,
            "r_t": c_rt,
            "category": c_category,
            "priority": c_priority,
            "trend_label": c_trend_label,
            "weekly_acc_weeks": c_weekly_weeks,
            "weekly_acc_rates": c_weekly_acc
        }

    return course_data_dict


# ==============================================================================
# Deep Dive Analytics Pipeline [MINE]
# ==============================================================================

def get_deep_dive_data(df, course_name, topic_name, decay_constant=0.15):
    """
    Generate all data needed for the Deep Dive page of a specific topic.

    Returns a dict with:
      - mastery_per_week: list of (week, mastery) tuples — mastery recomputed at each week's end
      - accuracy_per_week: list of (week, accuracy%) tuples — raw accuracy per week
      - current_mastery: float 0-1, the latest mastery value
      - trend_label: str
      - avg_slope: float, the polyfit slope for display
      - e_r, r_t, category: four-quadrant diagnosis
      - decay_curve: list of (weeks_from_now, projected_mastery) for the decay projection
      - weekly_volume: list of (week, count) — practice volume per week
    """
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    topic_df = df[(df['topic'] == course_name) & (df['question_topic'] == topic_name)].copy()

    if topic_df.empty:
        return None

    topic_df = topic_df.sort_values('timestamp')
    current_date = df['timestamp'].max()
    all_weeks = sorted(topic_df['week'].unique())

    # --- 1. Mastery per week (cumulative, recomputed at each week boundary) ---
    mastery_per_week = []
    for w in all_weeks:
        cumulative_df = topic_df[topic_df['week'] <= w]
        week_end = cumulative_df['timestamp'].max()
        m = calculate_topic_mastery(cumulative_df, week_end, decay_constant)
        mastery_per_week.append((int(w), round(m * 100, 1)))

    # --- 2. Raw accuracy per week ---
    accuracy_per_week = []
    weekly_acc = topic_df.groupby('week')['correct'].mean()
    for w in all_weeks:
        acc = weekly_acc.get(w, 0.0)
        accuracy_per_week.append((int(w), round(acc * 100, 1)))

    # --- 3. Current mastery = mastery at the last week displayed ---
    current_mastery = mastery_per_week[-1][1] / 100.0

    # --- 4. Trend ---
    _, trend_label, _, _, avg_slope = calculate_trend(topic_df)

    # --- 5. Four-quadrant diagnosis ---
    e_r, r_t, _, category = calculate_careless_weakness(topic_df)

    # --- 6. Forward decay projection starting from current_mastery ---
    decay_curve = []
    for future_weeks in np.arange(0, 13, 1):
        projected = current_mastery * np.exp(-decay_constant * future_weeks)
        decay_curve.append((int(future_weeks), round(projected * 100, 1)))

    # --- 7. Weekly practice volume ---
    weekly_volume = []
    vol = topic_df.groupby('week').size()
    for w in all_weeks:
        weekly_volume.append((int(w), int(vol.get(w, 0))))

    return {
        "mastery_per_week": mastery_per_week,
        "accuracy_per_week": accuracy_per_week,
        "current_mastery": current_mastery,
        "trend_label": trend_label,
        "avg_slope": round(avg_slope, 4),
        "e_r": e_r,
        "r_t": r_t,
        "category": category,
        "decay_curve": decay_curve,
        "weekly_volume": weekly_volume,
    }


# ==============================================================================
# Dashboard Aggregation Functions [MINE]
# ==============================================================================

def compute_dashboard_metrics(df, course_data):
    """
    Compute global dashboard metrics from the loaded data.
    Returns dict with overall_mastery, study_velocity, careless_rate, weekly_progress,
    plus delta values comparing recent half vs earlier half of weeks.
    """
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # --- Overall Mastery: average of all topic masteries ---
    all_masteries = []
    for course, data in course_data.items():
        all_masteries.extend(data['mastery'])
    overall_mastery = np.mean(all_masteries) if all_masteries else 0.0

    # --- Careless Rate: fraction of topics diagnosed as "Careless Mistake" ---
    total_topics = 0
    careless_count = 0
    for course, data in course_data.items():
        for cat in data['category']:
            total_topics += 1
            if cat == "Careless Mistake":
                careless_count += 1
    careless_rate = careless_count / total_topics if total_topics > 0 else 0.0

    # --- Study Velocity: avg hours per day over last 7 days ---
    max_date = df['timestamp'].max()
    last_7 = df[df['timestamp'] >= (max_date - pd.Timedelta(days=7))]
    if not last_7.empty:
        days_span = max((last_7['timestamp'].max() - last_7['timestamp'].min()).days, 1)
        total_seconds = last_7['time_spent_s'].sum()
        velocity = (total_seconds / 3600) / days_span
    else:
        velocity = 0.0

    # --- Weekly progress: overall mastery per week (average of all topic masteries at each week) ---
    weekly_progress = []
    all_weeks = sorted(df['week'].unique())

    # Per-course weekly mastery
    course_weekly_mastery = {}
    for course_name in df['topic'].unique():
        course_df = df[df['topic'] == course_name]
        course_weeks_mastery = []
        for w in all_weeks:
            # For each week, compute mastery for each topic up to that week, then average
            cumulative = course_df[course_df['week'] <= w]
            if cumulative.empty:
                course_weeks_mastery.append(0.0)
                continue
            week_end = cumulative['timestamp'].max()
            topic_masteries = []
            for t in cumulative['question_topic'].unique():
                t_df = cumulative[cumulative['question_topic'] == t]
                m = calculate_topic_mastery(t_df, week_end)
                topic_masteries.append(m)
            course_weeks_mastery.append(round(np.mean(topic_masteries) * 100, 1) if topic_masteries else 0.0)
        course_weekly_mastery[course_name] = course_weeks_mastery

    # Overall weekly mastery (average across all courses)
    for i, w in enumerate(all_weeks):
        all_course_vals = [course_weekly_mastery[c][i] for c in course_weekly_mastery]
        overall = round(np.mean(all_course_vals), 1) if all_course_vals else 0.0
        weekly_progress.append({"week": int(w), "mastery": overall})

    # --- Deltas: compare recent half vs earlier half of weeks ---
    mid = len(all_weeks) // 2
    early_weeks = all_weeks[:mid]
    recent_weeks = all_weeks[mid:]

    early_df = df[df['week'].isin(early_weeks)]
    recent_df = df[df['week'].isin(recent_weeks)]

    early_acc = early_df['correct'].mean() if not early_df.empty else 0.0
    recent_acc = recent_df['correct'].mean() if not recent_df.empty else 0.0
    mastery_delta = round((recent_acc - early_acc) * 100, 1)

    prev_7 = df[(df['timestamp'] >= (max_date - pd.Timedelta(days=14))) &
                (df['timestamp'] < (max_date - pd.Timedelta(days=7)))]
    if not prev_7.empty:
        prev_days = max((prev_7['timestamp'].max() - prev_7['timestamp'].min()).days, 1)
        prev_velocity = (prev_7['time_spent_s'].sum() / 3600) / prev_days
        velocity_delta = round(((velocity - prev_velocity) / prev_velocity) * 100, 1) if prev_velocity > 0 else 0.0
    else:
        velocity_delta = 0.0

    early_er = 1 - early_acc if not early_df.empty else 0.0
    recent_er = 1 - recent_acc if not recent_df.empty else 0.0
    careless_delta = round((recent_er - early_er) * 100, 1)

    return {
        "overall_mastery": round(overall_mastery * 100, 1),
        "mastery_delta": mastery_delta,
        "careless_rate": round(careless_rate * 100, 1),
        "careless_delta": careless_delta,
        "study_velocity": round(velocity, 1),
        "velocity_delta": velocity_delta,
        "weekly_progress": weekly_progress,
        "course_weekly_mastery": course_weekly_mastery,
        "weeks": [int(w) for w in all_weeks],
    }


# ==============================================================================
# LLM Integration Pipeline (OpenAI API)
# ==============================================================================

def get_ai_feedback(user_message, course_data_dict, chat_history, current_course=None, current_plan="", current_goal_plan=""):
    """
    6-param signature. Calls the LLM with student data + explanation context + goal schedule.
    """
    if client is None:
        return "⚠️ System Alert: OpenAI library not installed or API Key missing."

    # Intelligently condense data context
    context_str = ""
    for course, data in course_data_dict.items():
        if "priority" not in data:
            continue

        context_str += f"\n[{course}] Performance Report:\n"
        has_issues = False
        for i in range(len(data['topics'])):
            if data['priority'][i] >= 0.4 or data['category'][i] != "Normal/Mastered":
                has_issues = True
                context_str += f"- Topic: {data['topics'][i]} | Mastery: {data['mastery'][i]:.2f} | Diagnosis: [{data['category'][i]}] | Trend: [{data['trend_label'][i]}] | Priority Score: {data['priority'][i]}\n"
        if not has_issues:
            context_str += "Recent performance in this course is stable with no major weaknesses detected.\n"

    # Inject explanation plan + goal schedule context
    plan_context = ""
    if current_course:
        if current_plan:
            plan_context += f"\n\n[DIAGNOSTIC CONTEXT] You recently provided them with this diagnostic explanation:\n{current_plan}\n"
        if current_goal_plan:
            plan_context += f"\n\n[GOAL MODE CONTEXT] The student has activated Exam Goal Mode. You generated this schedule and explanation for them:\n{current_goal_plan}\n"

        if plan_context:
            plan_context += "\nMake sure your conversational answers align with these contexts. If they ask about their schedule, what to do next, or why a topic is scheduled on a certain day, refer directly to the GOAL MODE CONTEXT."

    # System prompt
    system_prompt = f"""You are a top-tier educational data analysis AI tutor.
The backend system has calculated the following diagnostic data and priority areas for the student based on their recent activities:
{context_str}{plan_context}

Please respond to the student's message based strictly on this quantitative data. Core rules:
1. Be empathetic, highly analytical, and act as a dedicated personal tutor.
2. Keep your response concise, well-structured, and under 150 words.
3. If the user asks general questions, actively guide them back to the specific topics and tasks identified in their diagnostic data or the provided explanation context.
"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history[-5:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"🚨 LLM API Request Failed: {str(e)}"


def get_explanation_feedback(course_name, topic_df):
    """
    [THEIRS] Calls GPT to explain Priority ranking with a case study comparison.
    """
    if client is None:
        return "⚠️ System Alert: OpenAI library not installed or API Key missing."

    context_str = ""
    for _, row in topic_df.iterrows():
        context_str += f"- Topic: {row['Topic']} | Priority Score: {row['Priority']:.2f} | Mastery: {row['Mastery']:.1f}% | Accuracy: {row['Accuracy']:.1f}% | Time Ratio: {row['Time Ratio']:.2f} | Trend: {row['Trend']}\n"

    system_prompt = f"""You are an elite AI educational data scientist and study strategist.
Here is the student's diagnostic data for the course '{course_name}':
{context_str}

BACKGROUND KNOWLEDGE (DO NOT output this formula):
The "Priority Score" is calculated internally as: Priority = 0.7 * (1 - Mastery) + 0.1 * Weakness_Penalty + 0.2 * Trend_Penalty.
Use this understanding to explain the logic behind the topic rankings.

Please strictly follow this structure:

### Case Study: Why this ranking?
- Select ONE high-priority topic (from the top of the list) and ONE Mastered or low-priority topic.
- Compare them using their EXACT numbers (Mastery %, Accuracy %, Time Ratio, Trend).
- Analytically explain *why* the first outranks the second. Focus on explaining how the specific metrics pushed the Priority Score up, contrasting it with the healthy metrics of the Mastered topic.

Format your response in clean Markdown. Be analytical, precise with the numbers, but keep the tone encouraging. Your answer is supposed to be concise (under 200 words).
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"🚨 LLM API Request Failed: {str(e)}"


# ==============================================================================
# Goal Mode Adaptive Planner
# ==============================================================================

def get_goal_mode_schedule(course_name, topic_df, days_left, daily_hours):
    """
    Calls GPT to generate an adaptive daily study schedule (JSON) based on
    exam deadline, daily hours, and student behavior patterns.
    """
    if client is None:
        return json.dumps({"adaptation_message": "⚠️ OpenAI API not configured.", "tasks": []})

    # Detect behavior context
    improving_count = (topic_df['Trend'] == 'Improving').sum()
    regressing_count = (topic_df['Trend'] == 'Regressing').sum()

    if improving_count > regressing_count + 1:
        behavior_context = "Accelerated progress detected: Multiple topics are showing strong improvement."
    elif regressing_count > improving_count + 1:
        behavior_context = "Inactivity or memory decay detected: Multiple topics are regressing. Prioritize recovering lost memory and foundational review."
    else:
        behavior_context = "Steady progress detected. Maintain current momentum with balanced drills."

    # Format topic data (using our column names: Mastery, Accuracy, Category)
    topic_context = ""
    for _, row in topic_df.sort_values("Priority", ascending=False).iterrows():
        topic_context += f"- {row['Topic']} (Priority: {row['Priority']:.2f}, Mastery: {row['Mastery']:.1f}%, Trend: {row['Trend']}, Category: {row['Category']})\n"

    system_prompt = f"""You are an elite AI exam strategist. The student is preparing for a '{course_name}' exam in {days_left} days.
They can dedicate {daily_hours} hours per day for this course.

STUDENT BEHAVIOR CONTEXT: {behavior_context}

TOPIC BACKLOG (Ranked by Priority/Urgency):
{topic_context}

TASK:
1. First, provide an 'adaptation_message' (1-2 sentences) explaining how you adapted the plan specifically based on the STUDENT BEHAVIOR CONTEXT. Add an appropriate Emoji.
2. Create a daily schedule up to {days_left} days, assigning the most urgent topics first.
3. Actions should be specific (e.g., 'Concept Recovery', 'High-Yield Drill', 'Mock Exam').
4. The total 'duration_hours' per day must not exceed {daily_hours}.
5. Provide a detailed 'explanation' justifying why you scheduled the topics this way as a Markdown bulleted list. Reference exact numbers from the TOPIC BACKLOG.

OUTPUT FORMAT: Respond with ONLY valid JSON matching this schema:
{{
  "adaptation_message": "🚀 System Alert: ...",
  "tasks": [
    {{"date": "Day 1", "topic": "Limits", "action": "Concept Recovery", "duration_hours": 1.5}},
    {{"date": "Day 2", "topic": "Derivatives", "action": "High-Yield Drill", "duration_hours": 2.0}}
  ],
  "explanation": "- **Limits (Day 1):** Scheduled first because..."
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        return json.dumps({"adaptation_message": f"🚨 LLM API Failed: {str(e)}", "tasks": []})