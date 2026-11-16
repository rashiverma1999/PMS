
import os
import json
import random
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Groww Pulse", page_icon="🟢", layout="wide")
random.seed(42)

# ---------- SYNTHETIC DEMO DATA ----------
@st.cache_data
def make_data():
    teams = ["Platforms", "Wealth", "Customer Success", "AMC"]
    rows = []
    for i in range(1, 201):
        score = round(random.uniform(2.4, 4.8), 2)
        rows.append({
            "Employee_ID": f"GRW{i:03}",
            "Employee": f"Employee {i:03}",
            "Team": random.choice(teams),
            "Manager": f"MGR{(i-1)//10+1:02}",
            "Performance_Score": score,
            "Manager_Rating": round(max(1, min(5, score + random.uniform(-0.8, 0.8))), 1),
            "Quality": round(random.uniform(2.5, 5), 1),
            "Goal_Completion": random.randint(45, 120),
            "Learning_Hours": random.randint(2, 45),
            "Feedback": random.choice([
                "Strong ownership and timely delivery.",
                "Needs better cross-functional communication.",
                "Consistently delivers high-quality work.",
                "Should improve prioritisation and planning.",
                "Demonstrates initiative and problem-solving."
            ])
        })
    return pd.DataFrame(rows)

df = make_data()


def ask_ai(feature, question, context):
    key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

    if not key:
        return "Gemini AI is not connected. Add GEMINI_API_KEY in Streamlit Secrets."

    instructions = """
    You are Groww Pulse, an evidence-based HR performance intelligence assistant.
    Analyse only the supplied synthetic data. Separate observed facts from
    interpretations. Explain limitations and give practical recommendations.
    Never make final ratings, promotion, pay, hiring or termination decisions.
    Fairness alerts are prompts for human investigation, not proof of bias.
    Do not infer sensitive personal traits. Be clear, structured and concise.
    """

    context_text = json.dumps(context, default=str)[:15000]
    prompt = (
        f"{instructions}\n\nModule: {feature}\n"
        f"Question: {question}\n\nSynthetic data:\n{context_text}"
    )

    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",
            headers={
                "x-goog-api-key": key,
                "Content-Type": "application/json"
            },
            json={
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()

        return "\n".join(
            part.get("text", "")
            for part in result["candidates"][0]["content"]["parts"]
            if "text" in part
        ) or "Gemini returned no text."

    except requests.exceptions.HTTPError as e:
        return f"Gemini API error: {e} — {response.text[:1000]}"
    except Exception as e:
        return f"AI connection error: {e}"


# ---------- DESIGN ----------
st.markdown("""
<style>
.stApp {background:#f4f7f4}
.block-container {padding-top:2rem;max-width:1450px}
.hero {background:linear-gradient(110deg,#10271e,#315b43);
padding:28px 32px;border-radius:18px;color:white;margin-bottom:22px}
.hero h1 {color:white;font-size:38px;margin:5px 0}
.hero p {color:#dce9df;margin:0}
div[data-testid="stMetric"] {background:white;padding:16px;
border:1px solid #e0e9e1;border-radius:13px}
</style>
<div class="hero">
<div style="color:#b8ed75;font-weight:700;letter-spacing:2px">GROWW PULSE · AI PERFORMANCE INTELLIGENCE</div>
<h1>Performance. With context.</h1>
<p>An AI-first performance management experience — from goals to feedback, fairness and growth.</p>
</div>
""", unsafe_allow_html=True)

st.caption("Independent hackathon prototype · Synthetic data only · Not affiliated with Groww")

# ---------- NAVIGATION ----------
pages = [
    "Overview", "Employee Workspace", "Manager Workspace",
    "Goal Intelligence", "Performance Intelligence",
    "Feedback Intelligence", "Fairness Monitor",
    "Growth Intelligence", "AI Manager Copilot", "Governance"
]
page = st.sidebar.radio("Navigate", pages)
st.sidebar.markdown("---")
st.sidebar.caption("Evidence-first AI · Human-governed decisions")

# ---------- OVERVIEW ----------
if page == "Overview":
    a,b,c,d = st.columns(4)
    a.metric("Synthetic employees", len(df))
    b.metric("Average performance", round(df.Performance_Score.mean(), 2))
    c.metric("Average goal completion", f"{df.Goal_Completion.mean():.1f}%")
    d.metric("Learning hours", int(df.Learning_Hours.sum()))

    st.subheader("Performance at a glance")
    left, right = st.columns(2)
    with left:
        st.markdown("**Performance distribution**")
        st.bar_chart(df.groupby("Team").Performance_Score.mean())
    with right:
        st.markdown("**Goal completion by team**")
        st.bar_chart(df.groupby("Team").Goal_Completion.mean())

    st.subheader("Six connected intelligence modules")
    cards = [
        ("🎯 Goal Intelligence", "Improve goal quality and measurable outcomes."),
        ("📊 Performance Intelligence", "Interpret performance trends and context."),
        ("💬 Feedback Intelligence", "Turn feedback into actionable insights."),
        ("⚖️ Fairness Monitor", "Identify rating differences for review."),
        ("🌱 Growth Intelligence", "Create targeted employee development plans."),
        ("🤖 Manager Copilot", "Ask questions in natural language.")
    ]
    cols = st.columns(3)
    for i,(title,desc) in enumerate(cards):
        with cols[i%3]:
            st.info(f"**{title}**\n\n{desc}")

# ---------- EMPLOYEE WORKSPACE ----------
elif page == "Employee Workspace":
    selected = st.selectbox("Select employee", df.Employee_ID)
    emp = df[df.Employee_ID == selected].iloc[0]
    st.subheader(f"{emp.Employee} · {emp.Employee_ID}")
    a,b,c = st.columns(3)
    a.metric("Performance score", emp.Performance_Score)
    b.metric("Goal completion", f"{emp.Goal_Completion}%")
    c.metric("Learning hours", emp.Learning_Hours)
    st.write("**Team:**", emp.Team, " | **Manager:**", emp.Manager)
    st.write("**Recent feedback:**", emp.Feedback)
    st.write("**Quality score:**", emp.Quality)

# ---------- MANAGER WORKSPACE ----------
elif page == "Manager Workspace":
    manager = st.selectbox("Select manager", sorted(df.Manager.unique()))
    team = df[df.Manager == manager]
    st.metric("Team size", len(team))
    st.metric("Average team score", round(team.Performance_Score.mean(), 2))
    st.dataframe(team, use_container_width=True, hide_index=True)

# ---------- GOAL INTELLIGENCE ----------
elif page == "Goal Intelligence":
    st.subheader("🎯 Goal Intelligence")
    goal = st.text_area("Enter an employee goal",
                        "Improve customer response time.")
    context = st.text_input("Role / business context", "Customer Success")
    if st.button("✨ Improve goal with AI"):
        st.markdown(ask_ai("Goal Intelligence",
            f"Rewrite this as a measurable SMART goal with key results, milestones and dependencies. Goal: {goal}. Context: {context}",
            {"example_employee_records": df.head(5).to_dict("records")}))

# ---------- PERFORMANCE INTELLIGENCE ----------
elif page == "Performance Intelligence":
    st.subheader("📊 Performance Intelligence")
    question = st.text_area("What would you like to understand?",
        "Identify performance patterns, quality-productivity trade-offs and records requiring more context.")
    if st.button("Analyse performance with AI"):
        st.markdown(ask_ai("Performance Intelligence", question,
            df.to_dict("records")))

# ---------- FEEDBACK INTELLIGENCE ----------
elif page == "Feedback Intelligence":
    st.subheader("💬 Feedback Intelligence")
    st.dataframe(df[["Employee_ID","Team","Feedback"]], use_container_width=True, hide_index=True)
    question = st.text_area("Feedback analysis request",
        "Identify recurring themes, distinguish specific evidence from vague feedback, and recommend constructive actions.")
    if st.button("Summarise feedback with AI"):
        st.markdown(ask_ai("Feedback Intelligence", question,
            df[["Employee_ID","Team","Feedback"]].to_dict("records")))

# ---------- FAIRNESS MONITOR ----------
elif page == "Fairness Monitor":
    st.subheader("⚖️ Fairness & Governance Monitor")
    audit = df.copy()
    audit["Rating_Gap"] = (audit.Manager_Rating - audit.Performance_Score).round(2)
    st.write("Exploratory differences between manager ratings and illustrative performance scores.")
    st.dataframe(audit[["Employee_ID","Team","Manager","Performance_Score",
                        "Manager_Rating","Rating_Gap"]], use_container_width=True, hide_index=True)
    question = st.text_area("Ask the Fairness AI",
        "Interpret rating differences cautiously. Identify checks HR should conduct before drawing conclusions.")
    if st.button("Review fairness signals with AI"):
        st.markdown(ask_ai("Fairness Monitor", question,
            audit.to_dict("records")))

# ---------- GROWTH INTELLIGENCE ----------
elif page == "Growth Intelligence":
    st.subheader("🌱 Growth Intelligence")
    selected = st.selectbox("Choose employee", df.Employee_ID, key="growth_emp")
    emp = df[df.Employee_ID == selected].iloc[0]
    st.write(f"Employee: **{emp.Employee}** · Team: **{emp.Team}**")
    st.write(f"Learning hours recorded: **{emp.Learning_Hours}**")
    skill = st.text_input("Skill to develop", "Stakeholder management")
    if st.button("Create AI development plan"):
        st.markdown(ask_ai("Growth Intelligence",
            f"Create a practical 30-60-90 day development plan for {skill}. Include actions, practice, milestones and success measures.",
            emp.to_dict()))

# ---------- AI COPILOT ----------
elif page == "AI Manager Copilot":
    st.subheader("🤖 Ask Groww Pulse")
    question = st.text_area("Ask a performance or people question",
        "Which employees may need a supportive performance conversation, and what evidence should a manager review?")
    if st.button("Ask AI Copilot"):
        st.markdown(ask_ai("Manager Copilot", question,
            df.to_dict("records")))

# ---------- GOVERNANCE ----------
elif page == "Governance":
    st.subheader("Responsible AI and methodology")
    st.markdown("""
    - All employee records are synthetic and generated for demonstration.
    - This prototype is independent and is not affiliated with Groww.
    - AI assists analysis, summarisation and drafting; humans retain decision authority.
    - AI does not make final performance ratings, promotion, compensation or termination decisions.
    - Rating differences are investigation prompts, not proof of bias.
    - The illustrative scores are not Groww policy or validated appraisal rules.
    - Employees should be able to correct records, add context and challenge conclusions.
    """)
    st.subheader("Enable live AI")
    st.write("Add OPENAI_API_KEY in your Streamlit app's Secrets settings. Keep the key private; never paste it into this source code.")

st.markdown("---")
st.caption("GROWW PULSE · Independent prototype · Synthetic data · Human decisions remain with people")
