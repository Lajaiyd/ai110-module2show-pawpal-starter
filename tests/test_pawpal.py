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


# --- Edge cases ---------------------------------------------------------------
def test_empty_schedule_is_safe():
    """An owner with no pets/tasks yields an empty agenda and no conflicts."""
    scheduler = Scheduler(Owner("Sam"))

    assert scheduler.daily_agenda() == []
    assert scheduler.conflicts() == []
    assert scheduler.conflict_warnings() == []
