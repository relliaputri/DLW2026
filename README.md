<div align="center">

# 🎓 AxonAI

### *Intelligent Study Analytics Platform*

**Transforming raw study data into actionable, explainable learning strategies powered by cognitive science and AI.**

[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![OpenAI](https://img.shields.io/badge/Powered%20by-GPT--4o-412991?logo=openai&logoColor=white)](https://openai.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*Built for DLW Hackathon 2026*

</div>

---

## 🧠 What is AxonAI?

AxonAI is an AI-powered study analytics dashboard that goes beyond simple grade tracking. It models how your brain actually retains knowledge using the **Ebbinghaus Forgetting Curve**, diagnoses *why* you're struggling (not just *where*), and generates personalized, adaptive study plans — all explained transparently with real data.

**The core insight:** A student who scores 60% because they rush through questions needs a completely different intervention than one who scores 60% despite spending extra time. AxonAI tells the difference.

---

## ✨ Key Features

### 📊 Mastery Modeling (Ebbinghaus Decay)
- Time-decayed mastery scores that naturally decrease when you stop practicing
- Forgetting curve projections showing when your knowledge will drop below threshold
- Per-topic, per-course mastery tracking over weeks

### 🔬 Four-Quadrant Diagnostic Engine
- **Careless Mistake** — Low accuracy + fast completion → You know it but rush
- **Genuine Weakness** — Low accuracy + slow completion → Fundamental gap
- **Expert** — High accuracy + fast → Fully mastered
- **Good** — High accuracy + slow → Solid but could improve efficiency

### 📈 Priority Algorithm (Explainable AI)
Every topic gets a priority score using a transparent, weighted formula:

$$Priority = 0.7 \cdot (1 - Mastery) + 0.1 \cdot P_{weakness} + 0.2 \cdot P_{trend}$$

The system explains *why* each topic is ranked where it is — no black boxes.

### 🤖 AI Study Agent
- GPT-4o-powered conversational tutor with full context awareness
- Knows your diagnostic data, explanation plans, and exam schedules
- Provides data-driven advice referencing your exact metrics

### 🎯 Adaptive Exam Scheduler (Goal Mode)
- Set an exam date and daily study hours
- AI generates a personalized daily schedule based on your weak spots
- Adapts to your behavior patterns (accelerating, regressing, or steady)
- Explains the logic behind every scheduling decision

### 📉 Deep Dive Analytics
- Click any topic for a full diagnostic page
- Weekly mastery & accuracy dual-axis chart with current week highlights
- Forgetting curve projection (12-week forward decay)
- Diagnostic card with trend slope and color-coded diagnosis

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (test2.py)                   │
│              Streamlit + Plotly + Custom CSS             │
├─────────────────────────────────────────────────────────┤
│  Dashboard  │  Course Analytics  │  Deep Dive  │ Settings│
│  • Metrics  │  • Mastery bars    │  • Decay    │ • AI    │
│  • Deltas   │  • Scatter plot    │  • Trends   │ • Model │
│  • Progress │  • AI Explanation  │  • Diagnosis│ • λ     │
├─────────────────────────────────────────────────────────┤
│                    BACKEND (logic.py)                    │
│              NumPy + Pandas + OpenAI API                 │
├─────────────────────────────────────────────────────────┤
│  Ebbinghaus  │  Four-Quadrant  │  Trend      │  Priority│
│  Mastery     │  Diagnosis      │  Detection  │  Scoring │
│  Decay Model │  (E_r × R_t)    │  (polyfit)  │  (α,β,γ) │
├─────────────────────────────────────────────────────────┤
│                   LLM INTEGRATION                       │
│  AI Feedback │ Explanation │ Goal Mode │ Context         │
│  Agent       │ Generator   │ Scheduler │ Injection       │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key

### Installation

```bash
# Clone the repo
git clone https://github.com/relliaputri/DLW2026.git
cd DLW2026

# Install dependencies
pip install streamlit pandas numpy plotly openai

# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# Run the app
streamlit run test2.py
```

### Usage
1. Upload a CSV file with student practice data
2. Explore the **Dashboard** for overall metrics and progress tracking
3. Navigate to **Courses** to see per-topic mastery and diagnostics
4. Click any topic for a **Deep Dive** with forgetting curves and trend analysis
5. Toggle **Goal Mode** to generate an AI-powered exam prep schedule
6. Chat with the **AI Study Agent** for personalized advice

---

## 📁 CSV Format

Your data should include these columns:

| Column | Description |
|--------|-------------|
| `timestamp` | When the practice occurred |
| `topic` | Course/subject name |
| `question_topic` | Specific topic within the course |
| `correct` | 1 = correct, 0 = incorrect |
| `time_spent_s` | Time spent in seconds |
| `avg_time_all_users_s` | Peer average time (for R_t calculation) |
| `week` | Week number |

---

## 🔬 The Science

### Ebbinghaus Forgetting Curve
Mastery decays exponentially over time:

$$M(t) = M_0 \cdot e^{-\lambda t}$$

Where λ (default 0.15) controls the decay rate. This means a topic you mastered 4 weeks ago with no review has naturally lower mastery than one you practiced yesterday — even if your historical accuracy is identical.

### Four-Quadrant Classification
We compute two metrics per topic:
- **Error Rate (E_r):** `1 - accuracy` — how often you get it wrong
- **Time Ratio (R_t):** `your_avg_time / peer_avg_time` — how long you take vs peers

These create four diagnostic quadrants that determine the right intervention strategy.

### Trend Detection
Weekly accuracy is fitted with linear regression (`np.polyfit`). The slope determines if you're improving (> 0.3%/week), regressing (< -0.3%/week), or stagnant.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit, Plotly, Custom CSS |
| Backend | Python, NumPy, Pandas |
| AI | OpenAI GPT-4o-mini |
| Mastery Model | Ebbinghaus Forgetting Curve |
| Trend Analysis | Linear Regression (NumPy polyfit) |
| Diagnostics | Four-Quadrant Error × Time Classification |

---

## 👥 Team

Built with ❤️ for **DLW Hackathon 2026**

---

<div align="center">

*"Don't just study harder — study smarter."*

**AxonAI** — Where cognitive science meets artificial intelligence.

</div>
