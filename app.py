import datetime
import json
from pathlib import Path

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

# Persist next to this script so it works regardless of the current directory.
DATA_FILE = Path(__file__).with_name("data.json")


def persist() -> None:
    """Save the whole owner tree to data.json after any change."""
    st.session_state.owner.save_to_json(str(DATA_FILE))


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan care tasks across all your pets and see today's schedule.")

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. Add your pets, schedule their care
tasks, and PawPal+ builds today's schedule ordered by time of day.
"""
    )

st.divider()

# --- Persist the Owner across reruns AND across runs --------------------------
# Streamlit re-runs this whole script on every interaction. Storing the Owner in
# st.session_state (a dict-like "vault") means we build it once and reuse the
# SAME object each rerun, so pets and tasks added earlier are not lost.
#
# For persistence *between application runs*, we seed that vault from data.json
# on first load (falling back to a fresh Owner if the file is missing or
# corrupt), and re-save after every change via persist().
if "owner" not in st.session_state:
    try:
        st.session_state.owner = Owner.load_from_json(str(DATA_FILE))
    except (FileNotFoundError, json.JSONDecodeError):
        st.session_state.owner = Owner("Jordan")

owner = st.session_state.owner

new_owner_name = st.text_input("Owner name", value=owner.name)
if new_owner_name != owner.name:
    owner.name = new_owner_name
    persist()

st.divider()

# --- Add a Pet ----------------------------------------------------------------
st.subheader("Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    new_pet_name = st.text_input("Pet name", value="")
    new_species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        if new_pet_name.strip():
            # Owner.add_pet() handles the data; the rerun below re-reads
            # owner.pets, so the new pet shows up everywhere automatically.
            owner.add_pet(Pet(new_pet_name.strip(), new_species))
            persist()
            st.success(f"Added {new_pet_name.strip()} ({new_species}).")
        else:
            st.warning("Please enter a pet name.")

if owner.pets:
    st.caption("Pets: " + ", ".join(f"{p.name} ({p.species})" for p in owner.pets))

st.divider()

# --- Schedule a Task ----------------------------------------------------------
st.subheader("Schedule a Task")
if not owner.pets:
    st.info("Add a pet first, then you can schedule tasks for it.")
else:
    # Suggest the earliest free time today for a task of a given length, so the
    # owner can avoid clashes before they happen (Scheduler.next_available_slot).
    with st.expander("💡 Find a free time"):
        duration = st.number_input(
            "Task length (minutes)", min_value=5, max_value=240, value=30, step=5
        )
        if st.button("Suggest earliest free slot"):
            slot = Scheduler(owner).next_available_slot(int(duration))
            if slot is not None:
                st.success(
                    f"Earliest free {int(duration)}-min slot today: "
                    f"**{slot.strftime('%H:%M')}**."
                )
            else:
                st.warning("No free slot that long left in the day (06:00–22:00).")

    with st.form("add_task_form", clear_on_submit=True):
        pet_name = st.selectbox("Pet", [p.name for p in owner.pets])
        description = st.text_input("Task description", value="")
        task_time = st.time_input("Time of day", value=datetime.time(8, 0))
        frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        if st.form_submit_button("Add task"):
            if description.strip():
                pet = owner.find_pet(pet_name)
                pet.add_task(Task(description.strip(), task_time, frequency))
                persist()
                st.success(f"Added '{description.strip()}' for {pet_name}.")
            else:
                st.warning("Please enter a task description.")

st.divider()

# --- Today's Schedule ---------------------------------------------------------
st.subheader("Today's Schedule")
scheduler = Scheduler(owner)
agenda = scheduler.daily_agenda()  # pending tasks due today, sorted by time


def pet_name_for(task):
    """Name of the pet that owns a task ('?' if somehow unattached)."""
    pet = scheduler.pet_for_task(task)
    return pet.name if pet else "?"


def task_table(tasks):
    """A time-sorted, column-aligned view of tasks for st.table."""
    return {
        "Time": [task.time.strftime("%H:%M") for task in tasks],
        "Pet": [pet_name_for(task) for task in tasks],
        "Task": [task.description for task in tasks],
        "Frequency": [task.frequency for task in tasks],
        "Status": ["✓ done" if task.completed else "○ pending" for task in tasks],
    }


# Warn about tasks the owner can't do at once (same time of day).
for message in scheduler.conflict_warnings():
    st.warning(message)

if not agenda:
    st.info("No pending tasks. Add some above to build the schedule.")
else:
    # Sorted agenda rendered as a professional, read-only table.
    st.table(task_table(agenda))
    st.caption(f"{len(agenda)} pending across {len(owner.pets)} pets")

    # Completing a task lives outside the table: complete_task drops it from
    # today's agenda and, for daily/weekly tasks, auto-queues the next
    # occurrence for tomorrow/next week.
    with st.form("complete_task_form"):
        choice = st.selectbox(
            "Mark a task done",
            options=list(range(len(agenda))),
            format_func=lambda i: (
                f"{agenda[i].time.strftime('%H:%M')} — "
                f"{pet_name_for(agenda[i])}: {agenda[i].description}"
            ),
        )
        if st.form_submit_button("Done"):
            follow_up = scheduler.complete_task(agenda[choice])
            persist()
            if follow_up is not None and follow_up.date is not None:
                st.success(
                    f"Completed. Next occurrence: "
                    f"{follow_up.date.strftime('%a %d %b')}."
                )
            else:
                st.success("Completed.")
            st.rerun()

# Offer a rollover once everything has been completed. start_new_day() resets
# recurring tasks and drops completed one-off ("once") tasks, so they don't come
# back tomorrow.
if scheduler.all_tasks() and not agenda:
    if st.button("Start a new day"):
        scheduler.start_new_day()
        persist()
        st.rerun()

st.divider()

# --- Browse Tasks -------------------------------------------------------------
# Demonstrates Scheduler.agenda(), which filters (by pet / status / frequency)
# and sorts by time in one call.
st.subheader("Browse Tasks")
if not scheduler.all_tasks():
    st.info("No tasks yet. Schedule some above to browse them here.")
else:
    pet_col, status_col, freq_col = st.columns(3)
    pet_filter = pet_col.selectbox("Pet", ["All"] + [p.name for p in owner.pets])
    status_filter = status_col.selectbox("Status", ["All", "Pending", "Completed"])
    freq_filter = freq_col.selectbox("Frequency", ["All", "daily", "weekly", "once"])

    completed = {"All": None, "Pending": False, "Completed": True}[status_filter]
    filtered = scheduler.agenda(
        pet_name=None if pet_filter == "All" else pet_filter,
        completed=completed,
        frequency=None if freq_filter == "All" else freq_filter,
    )

    if filtered:
        st.table(task_table(filtered))
        st.caption(f"{len(filtered)} task(s) match.")
    else:
        st.info("No tasks match those filters.")
