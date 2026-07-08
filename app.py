import datetime

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

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

# --- Persist the Owner across reruns ------------------------------------------
# Streamlit re-runs this whole script on every interaction. Storing the Owner in
# st.session_state (a dict-like "vault") means we build it once and reuse the
# SAME object each rerun, so pets and tasks added earlier are not lost.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")

owner = st.session_state.owner
owner.name = st.text_input("Owner name", value=owner.name)

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
    with st.form("add_task_form", clear_on_submit=True):
        pet_name = st.selectbox("Pet", [p.name for p in owner.pets])
        description = st.text_input("Task description", value="")
        task_time = st.time_input("Time of day", value=datetime.time(8, 0))
        frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        if st.form_submit_button("Add task"):
            if description.strip():
                pet = owner.find_pet(pet_name)
                pet.add_task(Task(description.strip(), task_time, frequency))
                st.success(f"Added '{description.strip()}' for {pet_name}.")
            else:
                st.warning("Please enter a task description.")

st.divider()

# --- Today's Schedule ---------------------------------------------------------
st.subheader("Today's Schedule")
scheduler = Scheduler(owner)
agenda = scheduler.daily_agenda()

# Warn about tasks the owner can't do at once (same time of day).
for message in scheduler.conflict_warnings():
    st.warning(message)

if not agenda:
    st.info("No pending tasks. Add some above to build the schedule.")
else:
    for index, task in enumerate(agenda):
        pet = scheduler.pet_for_task(task)
        row, button_col = st.columns([5, 1])
        row.write(
            f"**{task.time.strftime('%H:%M')}**  {pet.name}: "
            f"{task.description}  _({task.frequency})_"
        )
        # complete_task drops it from today's agenda and, for daily/weekly
        # tasks, auto-queues the next occurrence for tomorrow/next week.
        if button_col.button("Done", key=f"done-{index}"):
            scheduler.complete_task(task)
            st.rerun()

    st.caption(f"{len(agenda)} pending across {len(owner.pets)} pets")

# Offer a rollover once everything has been completed. start_new_day() resets
# recurring tasks and drops completed one-off ("once") tasks, so they don't come
# back tomorrow.
if scheduler.all_tasks() and not agenda:
    if st.button("Start a new day"):
        scheduler.start_new_day()
        st.rerun()
