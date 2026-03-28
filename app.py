from collections import defaultdict
from datetime import date
import json
from pathlib import Path

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

DATA_PATH = Path(__file__).resolve().parent / "data.json"


def _persist_owner() -> None:
    o = st.session_state.get("owner")
    if o is not None:
        o.save_to_json(DATA_PATH)


def _inject_pawpal_theme() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

:root {
  --pp-purple-deep: #6b5b95;
  --pp-purple-soft: #9b8fc9;
  --pp-purple-mist: #e8e2f4;
  --pp-green: #6bae7d;
  --pp-green-deep: #4a9d63;
  --pp-green-mist: #e6f4ea;
  --pp-warm-white: #fffbf7;
  --pp-cream: #fff5ef;
  --pp-card: #fffcfa;
  --pp-text: #3d3550;
  --pp-muted: #6b6378;
  --pp-accent-warm: #d4a574;
  --pp-shadow: rgba(107, 91, 149, 0.12);
}

html, body, .stApp {
  font-family: "Nunito", sans-serif !important;
  color: var(--pp-text);
}

.stApp {
  background: linear-gradient(180deg, var(--pp-purple-mist) 0%, var(--pp-warm-white) 45%, var(--pp-green-mist) 100%) !important;
}

section[data-testid="stMain"] > div {
  background: transparent !important;
}

.main .block-container {
  padding-top: 1.25rem;
  padding-bottom: 2.5rem;
  max-width: 46rem;
  background: rgba(255, 252, 250, 0.88);
  backdrop-filter: blur(10px);
  border-radius: 24px;
  box-shadow: 0 8px 40px var(--pp-shadow);
  border: 1px solid rgba(155, 143, 201, 0.22);
}

.pp-hero {
  text-align: center;
  padding: 1.75rem 1.5rem 2rem;
  margin: -1rem -1rem 1.5rem -1rem;
  border-radius: 0 0 24px 24px;
  background: linear-gradient(135deg, var(--pp-purple-deep) 0%, var(--pp-purple-soft) 42%, var(--pp-green) 100%);
  box-shadow: 0 12px 40px var(--pp-shadow);
}
.pp-hero-title {
  font-family: "Nunito", sans-serif !important;
  font-weight: 800 !important;
  font-size: 2.35rem !important;
  letter-spacing: -0.02em;
  margin: 0 !important;
  color: #fffef9 !important;
  text-shadow: 0 2px 16px rgba(0, 0, 0, 0.15);
}

div[data-testid="stMarkdownContainer"] h2 {
  font-family: "Nunito", sans-serif !important;
  font-weight: 700 !important;
  color: var(--pp-purple-deep) !important;
  margin-top: 1.35rem !important;
  padding: 0.65rem 1rem !important;
  background: var(--pp-card) !important;
  border-radius: 14px !important;
  border-left: 4px solid var(--pp-green) !important;
  box-shadow: 0 4px 20px var(--pp-shadow) !important;
}

div[data-testid="stMarkdownContainer"] h3 {
  font-family: "Nunito", sans-serif !important;
  color: var(--pp-purple-deep) !important;
}

.stDivider {
  margin-top: 1.5rem !important;
  margin-bottom: 1.5rem !important;
  background: linear-gradient(90deg, transparent, var(--pp-purple-soft), transparent) !important;
  height: 2px !important;
  border: none !important;
}

.stApp, .main, .block-container {
  color-scheme: light !important;
}

.stTextInput label, .stNumberInput label, .stSelectbox label, .stDateInput label {
  font-family: "Nunito", sans-serif !important;
  font-weight: 600 !important;
  color: var(--pp-muted) !important;
}

/* Text, number, date — input + BaseWeb wrappers (dark theme often styles inner divs) */
.stTextInput input,
[data-testid="stTextInput"] input,
.stNumberInput input,
[data-testid="stNumberInput"] input,
.stDateInput input,
[data-testid="stDateInput"] input {
  background-color: var(--pp-card) !important;
  background: var(--pp-card) !important;
  color: var(--pp-text) !important;
  caret-color: var(--pp-text) !important;
  -webkit-text-fill-color: var(--pp-text) !important;
  border-radius: 12px !important;
  border: 1.5px solid var(--pp-purple-mist) !important;
  font-family: "Nunito", sans-serif !important;
}
.stTextInput input::placeholder,
.stNumberInput input::placeholder,
.stDateInput input::placeholder {
  color: var(--pp-muted) !important;
  opacity: 1 !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus,
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stDateInput"] input:focus {
  border-color: var(--pp-green) !important;
  box-shadow: 0 0 0 2px var(--pp-green-mist) !important;
}

.stTextInput [data-baseweb="input"],
.stNumberInput [data-baseweb="input"],
.stDateInput [data-baseweb="input"] {
  background-color: var(--pp-card) !important;
  border-radius: 12px !important;
}
.stTextInput [data-baseweb="input"] > div,
.stNumberInput [data-baseweb="input"] > div,
.stDateInput [data-baseweb="input"] > div {
  background-color: var(--pp-card) !important;
  color: var(--pp-text) !important;
}

.stNumberInput button {
  background-color: var(--pp-cream) !important;
  color: var(--pp-purple-deep) !important;
  border: 1.5px solid var(--pp-purple-mist) !important;
}
.stNumberInput button:hover {
  background-color: var(--pp-purple-mist) !important;
  color: var(--pp-purple-deep) !important;
}

/* Selectbox — closed control + value text */
.stSelectbox [data-baseweb="select"],
div[data-baseweb="select"] {
  background-color: var(--pp-card) !important;
}
.stSelectbox [data-baseweb="select"] > div,
div[data-baseweb="select"] > div {
  background-color: var(--pp-card) !important;
  color: var(--pp-text) !important;
  border-radius: 12px !important;
  border-color: var(--pp-purple-mist) !important;
}
.stSelectbox [data-baseweb="select"] * {
  color: var(--pp-text) !important;
}
.stSelectbox svg {
  fill: var(--pp-purple-deep) !important;
}

/* BaseWeb menus / date calendar (portaled; keep lists readable on cream) */
div[data-baseweb="popover"] [data-baseweb="menu"],
div[data-baseweb="popover"] ul {
  background-color: var(--pp-card) !important;
  border-radius: 12px !important;
  border: 1px solid var(--pp-purple-mist) !important;
}
div[data-baseweb="popover"] li,
div[data-baseweb="menu"] li {
  background-color: var(--pp-card) !important;
  color: var(--pp-text) !important;
}
div[data-baseweb="popover"] li:hover,
div[data-baseweb="menu"] li:hover {
  background-color: var(--pp-purple-mist) !important;
}

[data-baseweb="calendar"],
[data-baseweb="calendar"] table,
[data-baseweb="calendar"] th,
[data-baseweb="calendar"] td {
  background-color: var(--pp-card) !important;
  color: var(--pp-text) !important;
}

.stButton > button {
  font-family: "Nunito", sans-serif !important;
  font-weight: 700 !important;
  border-radius: 14px !important;
  padding: 0.5rem 1.25rem !important;
  transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
.stButton > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px var(--pp-shadow) !important;
}

.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
  background: linear-gradient(135deg, var(--pp-accent-warm) 0%, #c9956a 100%) !important;
  color: #fffef9 !important;
  border: none !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover {
  background: linear-gradient(135deg, #ddb882 0%, var(--pp-accent-warm) 100%) !important;
  color: #fffef9 !important;
}

.stButton > button[kind="secondary"],
.stButton > button[data-testid="baseButton-secondary"] {
  background: var(--pp-card) !important;
  color: var(--pp-purple-deep) !important;
  border: 2px solid var(--pp-purple-soft) !important;
}
.stButton > button[kind="secondary"]:hover,
.stButton > button[data-testid="baseButton-secondary"]:hover {
  background: var(--pp-purple-mist) !important;
  border-color: var(--pp-purple-deep) !important;
  color: var(--pp-purple-deep) !important;
}

div[data-testid="stDataFrame"],
[data-testid="stDataFrame"] {
  border-radius: 16px !important;
  overflow: hidden !important;
  box-shadow: 0 6px 28px var(--pp-shadow) !important;
  border: 1px solid var(--pp-purple-mist) !important;
}

.stAlert,
.stAlertContainer,
[data-testid="stNotification"] {
  border-radius: 14px !important;
  font-family: "Nunito", sans-serif !important;
}

/* st.warning — stronger contrast vs cream page (Streamlit: stAlertContentWarning) */
div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {
  background: linear-gradient(135deg, #fff0c8 0%, #ffe08a 55%, #ffd666 100%) !important;
  background-color: #ffe08a !important;
  border: 2px solid #d97706 !important;
  box-shadow: 0 4px 20px rgba(217, 119, 6, 0.28) !important;
}
div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) [data-testid="stMarkdownContainer"],
div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) [data-testid="stMarkdownContainer"] p,
div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) [data-testid="stMarkdownContainer"] li,
div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) [data-testid="stMarkdownContainer"] span {
  color: #5c3d10 !important;
}

.stCaption, .stMarkdown p, .stMarkdown li {
  font-family: "Nunito", sans-serif !important;
}
</style>
""",
        unsafe_allow_html=True,
    )


def _priority_display(priority: str) -> str:
    key = (priority or "").strip().lower()
    return {
        "high": "🔴 High",
        "medium": "🟡 Medium",
        "low": "🟢 Low",
    }.get(key, priority)


_inject_pawpal_theme()

if "owner" not in st.session_state:
    st.session_state.owner = None
    try:
        st.session_state.owner = Owner.load_from_json(DATA_PATH)
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        pass
if "schedule_generated" not in st.session_state:
    st.session_state.schedule_generated = False


def _time_sort_key(time_str: str) -> tuple[int, int]:
    parts = time_str.split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    return (hour, minute)

st.markdown(
    '<div class="pp-hero"><h1 class="pp-hero-title">🐾 PawPal+</h1></div>',
    unsafe_allow_html=True,
)

# --- Owner ---
st.subheader("Owner")
owner_name = st.text_input("Owner name", placeholder="Your name")

if st.button("Initialize owner", type="primary"):
    if not owner_name.strip():
        st.error("Please enter an owner name.")
    else:
        st.session_state.owner = Owner(name=owner_name.strip())
        st.session_state.schedule_generated = False
        _persist_owner()
        st.success(f"Owner **{owner_name.strip()}** is ready.")
        st.rerun()

owner = st.session_state.owner
if owner is None:
    st.info("Initialize an owner above to add pets and tasks.")
    st.stop()

st.caption(f"Signed in as **{owner.name}**.")

# --- Add pet ---
st.subheader("Pets")
c1, c2, c3 = st.columns(3)
with c1:
    pet_name = st.text_input("Pet name", key="pet_name")
with c2:
    pet_age = st.number_input("Age", min_value=0, max_value=50, value=1, step=1)
with c3:
    pet_breed = st.text_input("Breed", key="pet_breed")

if st.button("Add pet"):
    if not pet_name.strip():
        st.error("Pet name is required.")
    else:
        owner.add_pet(Pet(name=pet_name.strip(), age=int(pet_age), breed=pet_breed.strip() or "—"))
        _persist_owner()
        st.rerun()

if owner.pets:
    st.write("**Your pets:**")
    for p in owner.pets:
        st.write(f"- **{p.name}** — age {p.age}, {p.breed} ({len(p.tasks)} task(s))")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Add task ---
st.subheader("Tasks")
if not owner.pets:
    st.warning("Add at least one pet before creating tasks.")
else:
    pet_labels = [p.name for p in owner.pets]
    task_pet = st.selectbox("Pet", pet_labels, key="task_pet_select")

    t1, t2 = st.columns(2)
    with t1:
        task_name = st.text_input("Task name", key="task_name")
    with t2:
        task_time = st.text_input("Time (HH:MM)", placeholder="09:30", key="task_time")

    t3, t4 = st.columns(2)
    with t3:
        task_duration = st.number_input("Duration (minutes)", min_value=1, max_value=24 * 60, value=30)
    with t4:
        task_due = st.date_input("Due date", value=date.today(), key="task_due")

    t5, t6 = st.columns(2)
    with t5:
        task_priority = st.selectbox("Priority", ["low", "medium", "high"], index=1)
    with t6:
        task_frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])

    if st.button("Add task"):
        if not task_name.strip():
            st.error("Task name is required.")
        elif not task_time.strip():
            st.error("Time is required.")
        else:
            pet = next(p for p in owner.pets if p.name == task_pet)
            task = Task(
                name=task_name.strip(),
                duration=int(task_duration),
                time=task_time.strip(),
                frequency=task_frequency,
                priority=task_priority,
                due_date=task_due.isoformat(),
                pet_name=pet.name,
            )
            pet.add_task(task)
            _persist_owner()
            st.rerun()

st.divider()

# --- Schedule ---
st.subheader("Schedule")
scheduler = Scheduler(owner)

_schedule_sort_options = (
    "By time (chronological)",
    "By priority, then time",
)
schedule_sort_mode = st.selectbox(
    "Sort schedule by",
    _schedule_sort_options,
    key="schedule_sort_mode",
)

if st.button("Generate schedule", type="primary"):
    st.session_state.schedule_generated = True
    st.rerun()

if st.session_state.schedule_generated:
    all_tasks = scheduler.get_all_tasks()
    if schedule_sort_mode == "By time (chronological)":
        scheduled = scheduler.generate_schedule()
    else:
        scheduled = scheduler.sort_by_priority_then_time(all_tasks)
    conflicts = scheduler.detect_conflicts(all_tasks)

    if scheduled:
        order_note = (
            "time"
            if schedule_sort_mode == "By time (chronological)"
            else "priority, then time"
        )
        st.success(f"{len(scheduled)} task(s) ordered by {order_note}.")

    if conflicts:
        by_time: defaultdict[str, list] = defaultdict(list)
        for t in conflicts:
            by_time[t.time].append(t)
        for slot in sorted(by_time.keys(), key=_time_sort_key):
            group = by_time[slot]
            lines = [
                f"**{t.pet_name}** — task **{t.name}** at **{t.time}**"
                for t in group
            ]
            detail = "; ".join(lines)
            st.warning(
                f"**Time conflict at {slot}:** {len(group)} task(s) share this time. {detail} "
                "Consider staggering times so care blocks do not overlap."
            )
            for t in group:
                suggested = scheduler.find_next_available_slot(
                    t.duration, t.time, exclude_tasks=[t]
                )
                if suggested:
                    st.info(
                        f"💡 Suggested free slot for **{t.name}** ({t.pet_name}): {suggested}"
                    )

    if not scheduled:
        st.info("No tasks to schedule. Add tasks to your pets first.")
    else:
        rows = []
        for i, t in enumerate(scheduled, start=1):
            rows.append(
                {
                    "#": i,
                    "Time": t.time,
                    "Task": t.name,
                    "Pet": t.pet_name,
                    "Duration (min)": t.duration,
                    "Priority": _priority_display(t.priority),
                    "Frequency": t.frequency,
                    "Due": t.due_date,
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)

        st.subheader("Filter tasks")
        fp1, fp2 = st.columns(2)
        with fp1:
            pet_filter_options = ["All pets"] + [p.name for p in owner.pets]
            filter_pet = st.selectbox("Pet", pet_filter_options, key="schedule_filter_pet")
        with fp2:
            filter_status = st.selectbox(
                "Completion status",
                ["All", "Pending", "Completed"],
                key="schedule_filter_status",
            )

        pet_all = filter_pet == "All pets"
        status_all = filter_status == "All"

        if pet_all and status_all:
            st.caption("Select a pet and/or completion status to narrow the list below.")
            filtered: list = []
        elif pet_all:
            crit = "pending" if filter_status == "Pending" else "complete"
            filtered = scheduler.filter_tasks(crit)
        elif status_all:
            filtered = scheduler.filter_tasks(filter_pet)
        else:
            crit = "pending" if filter_status == "Pending" else "complete"
            by_pet = scheduler.filter_tasks(filter_pet)
            by_stat = scheduler.filter_tasks(crit)
            filtered = [t for t in by_pet if t in by_stat]

        if not (pet_all and status_all):
            filtered_sorted = scheduler.sort_by_time(filtered)
            if not filtered_sorted:
                st.info("No tasks match your filters.")
            else:
                filter_rows = []
                for i, t in enumerate(filtered_sorted, start=1):
                    filter_rows.append(
                        {
                            "#": i,
                            "Time": t.time,
                            "Task": t.name,
                            "Pet": t.pet_name,
                            "Duration (min)": t.duration,
                            "Priority": _priority_display(t.priority),
                            "Frequency": t.frequency,
                            "Due": t.due_date,
                        }
                    )
                st.dataframe(filter_rows, use_container_width=True, hide_index=True)
