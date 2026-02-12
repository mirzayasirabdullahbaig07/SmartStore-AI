# app.py
import streamlit as st
import random
import requests
from streamlit_autorefresh import st_autorefresh

# -------------------------------
# Streamlit page config
# -------------------------------
st.set_page_config(page_title="🛒 SmartStore AI", layout="wide")
st.title("🛒 SmartStore AI - Gemini AI Simulation")

# -------------------------------
# Load Gemini API key from Streamlit Secrets
# -------------------------------
# Load Gemini API key from Streamlit Secrets (safe fallback)
# Load Gemini API key from Streamlit Secrets (safe fallback)
GEMINI_API_KEY = st.secrets.get("api_key", None)



# -------------------------------
# Initialize store in session state
# -------------------------------
if "store" not in st.session_state:
    st.session_state.store = {
        "shelves": {
            "A": {"status": "full", "empty_minutes": 0, "traffic": "high"},
            "B": {"status": "full", "empty_minutes": 0, "traffic": "low"},
            "C": {"status": "full", "empty_minutes": 0, "traffic": "medium"},
        },
        "robot_position": "Dock",
        "tasks_completed": 0,
        "log": [],
    }

store = st.session_state.store

# -------------------------------
# Gemini AI Decision Function
# -------------------------------
def ai_decide(empty_shelves):
    """Decide which shelf to restock."""
    # Fallback if API key missing
    if not GEMINI_API_KEY:
        return max(empty_shelves, key=lambda x: empty_shelves[x]["empty_minutes"])

    prompt = "Shelves data:\n"
    for name, data in empty_shelves.items():
        prompt += f"Shelf {name}: status={data['status']}, empty_minutes={data['empty_minutes']}, traffic={data['traffic']}\n"
    prompt += "Which shelf should the robot restock first? Return only the shelf letter."

    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gemini-1.5",
        "prompt": prompt,
        "max_tokens": 5
    }

    try:
        response = requests.post("https://api.gemini.com/v1/completions", json=payload, headers=headers, timeout=10)
        result = response.json()
        decision = result.get("choices", [{}])[0].get("text", "").strip().upper()
        # Validate the decision
        if decision not in empty_shelves:
            decision = max(empty_shelves, key=lambda x: empty_shelves[x]["empty_minutes"])
        return decision
    except Exception as e:
        st.error(f"AI request failed: {e}. Using fallback decision.")
        return max(empty_shelves, key=lambda x: empty_shelves[x]["empty_minutes"])

# -------------------------------
# Helper Functions
# -------------------------------
def simulate_empty():
    """Randomly make a shelf empty."""
    shelf = random.choice(list(store["shelves"].keys()))
    store["shelves"][shelf]["status"] = "empty"
    store["shelves"][shelf]["empty_minutes"] = random.randint(1, 15)
    store["log"].append(f"Shelf {shelf} became empty")
    st.success(f"Shelf {shelf} is now empty")

def decide():
    """Ask AI to decide which shelf to restock."""
    empty_shelves = {k: v for k, v in store["shelves"].items() if v["status"] == "empty"}
    if not empty_shelves:
        st.warning("No empty shelves to restock")
        return
    decision = ai_decide(empty_shelves)
    store["robot_position"] = decision
    store["shelves"][decision]["status"] = "full"
    store["tasks_completed"] += 1
    store["log"].append(f"Robot restocked Shelf {decision} (AI decision)")
    st.success(f"🤖 Robot is restocking Shelf {decision} (AI decision)")

# -------------------------------
# Sidebar Controls
# -------------------------------
st.sidebar.header("⚙️ Controls")
auto_simulate = st.sidebar.checkbox("Auto-Simulate Empty Shelves")
simulate_interval = st.sidebar.slider("Simulation Interval (seconds)", 1, 10, 3)

if st.sidebar.button("Reset Store"):
    st.session_state.store = {
        "shelves": {
            "A": {"status": "full", "empty_minutes": 0, "traffic": "high"},
            "B": {"status": "full", "empty_minutes": 0, "traffic": "low"},
            "C": {"status": "full", "empty_minutes": 0, "traffic": "medium"},
        },
        "robot_position": "Dock",
        "tasks_completed": 0,
        "log": [],
    }
    st.experimental_rerun()

# -------------------------------
# Buttons
# -------------------------------
col1, col2 = st.columns(2)
with col1:
    if st.button("Simulate Shelf Becoming Empty"):
        simulate_empty()
with col2:
    if st.button("Ask Robot to Restock"):
        decide()

# -------------------------------
# Auto-Simulation (non-blocking)
# -------------------------------
if auto_simulate:
    st_autorefresh(interval=simulate_interval*1000, limit=None, key="auto_sim")
    simulate_empty()

# -------------------------------
# Shelf Grid Display
# -------------------------------
st.subheader("📦 Shelf Status")
cols = st.columns(len(store["shelves"]))
for name, data in store["shelves"].items():
    color = "🟢 Full" if data["status"] == "full" else "🔴 Empty"
    robot_here = "🤖" if store["robot_position"] == name else ""
    with cols[list(store["shelves"].keys()).index(name)]:
        st.markdown(f"### Shelf {name} {robot_here}")
        st.write(f"**Status:** {color}")
        st.write(f"**Traffic:** {data['traffic']}")
        st.write(f"**Empty Minutes:** {data['empty_minutes']}")

# -------------------------------
# Metrics Panel
# -------------------------------
st.subheader("📊 Metrics")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Restocking Tasks", store["tasks_completed"])
with col2:
    empty_count = sum(1 for s in store["shelves"].values() if s["status"]=="empty")
    st.metric("Empty Shelves", empty_count)
with col3:
    st.metric("Robot Position", store["robot_position"])

# -------------------------------
# Action Log
# -------------------------------
st.subheader("📝 Action Log")
log = store.get("log", [])
for entry in log[-10:][::-1]:
    st.write(f"- {entry}")
