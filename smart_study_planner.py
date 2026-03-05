import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from openai import OpenAI

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="📚 Smart AI Study Planner", page_icon="🎓", layout="wide")
st.title("📚 Smart AI Study Planner Pro")

DATA_FILE = "tasks.csv"

# =========================
# Load / Save Data
# =========================
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        
        # Force proper datetime conversion
        if "Deadline" in df.columns:
            df["Deadline"] = pd.to_datetime(df["Deadline"], errors="coerce")
        
        return df
    
    return pd.DataFrame(columns=["Task", "Subject", "Priority", "Deadline", "Completed"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

tasks = load_data()

# =========================
# SIDEBAR - ADD TASK
# =========================
st.sidebar.header("➕ Add Task")

with st.sidebar.form("add_task"):
    task = st.text_input("Task Name")
    subject = st.selectbox("Subject", ["Math", "Science", "English", "History", "Other"])
    priority = st.selectbox("Priority", ["Low", "Medium", "High"])
    deadline = st.date_input("Deadline")
    submitted = st.form_submit_button("Add")

    if submitted and task:
        new_task = pd.DataFrame([{
            "Task": task,
            "Subject": subject,
            "Priority": priority,
            "Deadline": pd.to_datetime(deadline),
            "Completed": False
        }])
        tasks = pd.concat([tasks, new_task], ignore_index=True)
        save_data(tasks)
        st.success("Task added!")
        st.rerun()

# =========================
# TABS
# =========================
tab1, tab2, tab3 = st.tabs(["📋 Task List", "📆 Calendar View", "🤖 AI Study Generator"])

# ======================================================
# 📋 TASK LIST
# ======================================================
with tab1:

    st.header("Your Tasks")

    if tasks.empty:
        st.info("No tasks yet.")
    else:
        today = pd.Timestamp(datetime.today().date())

        for i, row in tasks.iterrows():
            col1, col2, col3 = st.columns([3,1,1])

            with col1:
                status = "✅" if row["Completed"] else "⬜"
                st.write(f"{status} **{row['Task']}**")
                due_date = row["Deadline"]
                if pd.notnull(due_date):
                    due_text = due_date.strftime("%Y-%m-%d")
                else:
                    due_text = "No deadline"
                
                st.caption(f"{row['Subject']} | {row['Priority']} | Due: {due_text}")

                # 🔔 Deadline Alerts
                if not row["Completed"]:
                    if row["Deadline"] < today:
                        st.error("⚠️ Overdue!")
                    elif row["Deadline"] <= today + timedelta(days=3):
                        st.warning("⏳ Due Soon!")

            with col2:
                if not row["Completed"]:
                    if st.button("Complete", key=f"c{i}"):
                        tasks.at[i, "Completed"] = True
                        save_data(tasks)
                        st.rerun()

            with col3:
                if st.button("Delete", key=f"d{i}"):
                    tasks = tasks.drop(i)
                    save_data(tasks)
                    st.rerun()

    # Progress
    if not tasks.empty:
        completed = tasks["Completed"].sum()
        total = len(tasks)
        st.progress(completed / total)
        st.write(f"{completed} / {total} tasks completed")

# ======================================================
# 📆 CALENDAR VIEW
# ======================================================
with tab2:

    st.header("Calendar View")

    if tasks.empty:
        st.info("No tasks to display.")
    else:
        calendar = tasks.sort_values("Deadline")

        grouped = calendar.groupby("Deadline")

        for date, group in grouped:
            st.subheader(f"📅 {date.date()}")
            for _, row in group.iterrows():
                status = "✅" if row["Completed"] else "⬜"
                st.write(f"{status} {row['Task']} ({row['Subject']})")

# ======================================================
# 🤖 AI STUDY SCHEDULE GENERATOR
# ======================================================
with tab3:

    st.header("AI Study Schedule Generator")

    st.write("Generate a personalized study plan based on your tasks.")

    study_hours = st.number_input("How many hours can you study per day?", min_value=1, max_value=12, value=3)

    if st.button("Generate AI Study Plan"):

        if tasks.empty:
            st.error("No tasks available.")
        else:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            task_summary = tasks[~tasks["Completed"]][["Task","Subject","Priority","Deadline"]].to_string()

            prompt = f"""
You are a smart academic planner.

Here are my tasks:
{task_summary}

I can study {study_hours} hours per day.

Create a detailed 7-day study schedule.
Distribute time based on priority and deadline.
Be clear and structured.
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            st.subheader("📚 Your AI Study Plan")
            st.write(response.choices[0].message.content)
