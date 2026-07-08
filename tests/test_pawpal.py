"""Tests for core PawPal+ behaviors."""

import datetime

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_status():
    """Calling mark_complete() flips a task from not-done to done."""
    task = Task("Morning walk", datetime.time(8, 0))

    assert task.completed is False  # tasks start incomplete

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet increases that pet's task count by one."""
    pet = Pet("Biscuit", "dog")

    assert len(pet.tasks) == 0

    pet.add_task(Task("Feeding", datetime.time(7, 30)))

    assert len(pet.tasks) == 1


# --- Helpers ------------------------------------------------------------------
def _owner_with_tasks(*tasks: Task) -> Owner:
    """Build an Owner with a single pet carrying the given tasks."""
    pet = Pet("Biscuit", "dog")
    for task in tasks:
        pet.add_task(task)
    return Owner("Sam", pets=[pet])


# --- Sorting correctness ------------------------------------------------------
def test_daily_agenda_returns_tasks_in_chronological_order():
    """Tasks added out of order come back earliest time first."""
    evening = Task("Dinner", datetime.time(18, 0))
    morning = Task("Walk", datetime.time(8, 0))
    noon = Task("Lunch", datetime.time(12, 0))
    scheduler = Scheduler(_owner_with_tasks(evening, morning, noon))

    agenda = scheduler.daily_agenda()

    assert [task.description for task in agenda] == ["Walk", "Lunch", "Dinner"]


def test_sort_by_time_does_not_mutate_input():
    """sort_by_time returns a new list and leaves the original order intact."""
    late = Task("Dinner", datetime.time(18, 0))
    early = Task("Walk", datetime.time(8, 0))
    original = [late, early]

    result = Scheduler.sort_by_time(original)

    assert result == [early, late]      # sorted copy
    assert original == [late, early]    # source untouched


def test_same_time_tasks_keep_insertion_order():
    """Two tasks at the exact same time preserve insertion order (stable sort)."""
    first = Task("Walk", datetime.time(8, 0))
    second = Task("Medication", datetime.time(8, 0))
    scheduler = Scheduler(_owner_with_tasks(first, second))

    agenda = scheduler.daily_agenda()

    assert [task.description for task in agenda] == ["Walk", "Medication"]


# --- Recurrence logic ---------------------------------------------------------
def test_completing_daily_task_creates_next_day_occurrence():
    """Completing a daily task queues a fresh copy dated one day later."""
    task = Task("Walk", datetime.time(8, 0), frequency="daily")
    owner = _owner_with_tasks(task)
    scheduler = Scheduler(owner)
    pet = owner.pets[0]

    follow_up = scheduler.complete_task(task)

    assert task.completed is True
    assert follow_up is not None
    assert follow_up.completed is False
    assert follow_up.date == datetime.date.today() + datetime.timedelta(days=1)
    assert follow_up in pet.tasks               # attached to the same pet
    assert follow_up not in scheduler.daily_agenda()  # hidden until its day


def test_completing_weekly_task_recurs_seven_days_later():
    """Weekly tasks repeat a week out, not a day out."""
    task = Task("Vet check-up", datetime.time(15, 30), frequency="weekly")
    scheduler = Scheduler(_owner_with_tasks(task))

    follow_up = scheduler.complete_task(task)

    assert follow_up is not None
    assert follow_up.date == datetime.date.today() + datetime.timedelta(days=7)


def test_once_task_does_not_recur():
    """A one-off task is marked done but queues no follow-up."""
    task = Task("Adoption paperwork", datetime.time(10, 0), frequency="once")
    owner = _owner_with_tasks(task)
    scheduler = Scheduler(owner)

    follow_up = scheduler.complete_task(task)

    assert task.completed is True
    assert follow_up is None
    assert len(owner.pets[0].tasks) == 1  # nothing new added


# --- Conflict detection -------------------------------------------------------
def test_scheduler_flags_duplicate_times():
    """Two pending tasks at the same time of day are reported as a conflict."""
    walk = Task("Walk", datetime.time(8, 0))
    meds = Task("Medication", datetime.time(8, 0))
    scheduler = Scheduler(_owner_with_tasks(walk, meds))

    conflicts = scheduler.conflicts()

    assert len(conflicts) == 1
    assert conflicts[0] == (walk, meds)
    assert len(scheduler.conflict_warnings()) == 1


def test_no_conflict_when_times_differ():
    """Tasks at distinct times raise no conflict."""
    scheduler = Scheduler(
        _owner_with_tasks(
            Task("Walk", datetime.time(8, 0)),
            Task("Dinner", datetime.time(18, 0)),
        )
    )

    assert scheduler.conflicts() == []
    assert scheduler.conflict_warnings() == []


def test_completed_task_does_not_conflict():
    """A completed task no longer clashes with a pending one at the same time."""
    done = Task("Walk", datetime.time(8, 0))
    done.mark_complete()
    pending = Task("Medication", datetime.time(8, 0))
    scheduler = Scheduler(_owner_with_tasks(done, pending))

    assert scheduler.conflicts() == []


# --- New-day rollover ---------------------------------------------------------
def test_start_new_day_does_not_duplicate_recurring_tasks():
    """Complete + roll over should not accumulate duplicate recurring tasks.

    complete_task() already queues the next occurrence, so start_new_day()
    must retire the finished task rather than resurrect it. Repeated cycles
    keep exactly one live occurrence.
    """
    owner = _owner_with_tasks(Task("Feed", datetime.time(8, 30), frequency="daily"))
    scheduler = Scheduler(owner)

    for _ in range(3):
        due = scheduler.daily_agenda()
        if due:
            scheduler.complete_task(due[0])
        scheduler.start_new_day()

    assert len(owner.all_tasks()) == 1
    assert owner.all_tasks()[0].completed is False


def test_start_new_day_drops_completed_once_task():
    """A finished one-off task is removed and does not come back."""
    task = Task("Adoption paperwork", datetime.time(10, 0), frequency="once")
    owner = _owner_with_tasks(task)
    scheduler = Scheduler(owner)

    scheduler.complete_task(task)
    scheduler.start_new_day()

    assert owner.all_tasks() == []


def test_start_new_day_keeps_pending_tasks():
    """Tasks left unfinished carry over to the new day untouched."""
    owner = _owner_with_tasks(Task("Walk", datetime.time(8, 0), frequency="daily"))
    scheduler = Scheduler(owner)

    scheduler.start_new_day()

    assert len(owner.all_tasks()) == 1
    assert owner.all_tasks()[0].completed is False


# --- Next available slot ------------------------------------------------------
def test_next_slot_is_day_start_when_schedule_is_empty():
    """With nothing booked, the earliest slot is the start of the day window."""
    scheduler = Scheduler(_owner_with_tasks())

    slot = scheduler.next_available_slot(30, day_start=datetime.time(6, 0))

    assert slot == datetime.time(6, 0)


def test_next_slot_skips_a_busy_block():
    """A task at day_start pushes the next slot past its gap window."""
    scheduler = Scheduler(
        _owner_with_tasks(Task("Walk", datetime.time(6, 0), frequency="daily"))
    )

    # 06:00 task blocks 06:00–06:30 (default gap), so 30-min slot lands at 06:30.
    slot = scheduler.next_available_slot(
        30, day_start=datetime.time(6, 0), gap_minutes=30
    )

    assert slot == datetime.time(6, 30)


def test_next_slot_fits_into_a_gap_between_tasks():
    """An opening long enough between two tasks is chosen over a later one."""
    scheduler = Scheduler(
        _owner_with_tasks(
            Task("Walk", datetime.time(8, 0)),   # blocks 08:00–08:30
            Task("Dinner", datetime.time(18, 0)),
        )
    )

    # Earliest 30-min opening is right at day_start (06:00), before the 08:00 task.
    slot = scheduler.next_available_slot(30, day_start=datetime.time(6, 0))

    assert slot == datetime.time(6, 0)


def test_next_slot_returns_none_when_day_is_full():
    """No opening long enough anywhere in the window yields None, not a guess."""
    # A tiny 40-minute window with a task blocking its first 30 minutes leaves
    # only a 10-minute tail — too short for a 30-minute task.
    scheduler = Scheduler(
        _owner_with_tasks(Task("Walk", datetime.time(6, 0)))
    )

    slot = scheduler.next_available_slot(
        30,
        day_start=datetime.time(6, 0),
        day_end=datetime.time(6, 40),
        gap_minutes=30,
    )

    assert slot is None


# --- JSON persistence ---------------------------------------------------------
def test_json_round_trip_preserves_pets_and_tasks(tmp_path):
    """Saving then loading rebuilds pets and tasks, including time/date fields."""
    owner = Owner("Sam", pets=[Pet("Biscuit", "dog"), Pet("Whiskers", "cat")])
    owner.pets[0].add_task(Task("Walk", datetime.time(8, 0), frequency="weekly"))
    owner.pets[0].add_task(
        Task(
            "Meds",
            datetime.time(9, 30),
            frequency="daily",
            completed=True,
            date=datetime.date(2026, 7, 8),
        )
    )

    path = tmp_path / "data.json"
    owner.save_to_json(str(path))
    loaded = Owner.load_from_json(str(path))

    assert loaded.name == "Sam"
    assert [pet.name for pet in loaded.pets] == ["Biscuit", "Whiskers"]

    walk, meds = loaded.pets[0].tasks
    assert walk.time == datetime.time(8, 0)          # datetime.time survives
    assert walk.frequency == "weekly"
    assert walk.date is None                          # None round-trips as null
    assert meds.completed is True
    assert meds.date == datetime.date(2026, 7, 8)     # datetime.date survives


def test_load_missing_file_raises(tmp_path):
    """Loading a non-existent file raises so callers can start fresh."""
    import pytest

    with pytest.raises(FileNotFoundError):
        Owner.load_from_json(str(tmp_path / "nope.json"))


# --- Edge cases ---------------------------------------------------------------
def test_empty_schedule_is_safe():
    """An owner with no pets/tasks yields an empty agenda and no conflicts."""
    scheduler = Scheduler(Owner("Sam"))

    assert scheduler.daily_agenda() == []
    assert scheduler.conflicts() == []
    assert scheduler.conflict_warnings() == []
