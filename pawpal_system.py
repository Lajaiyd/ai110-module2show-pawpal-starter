"""PawPal+ core system classes.

Data model:
    Task      - a single care activity (description, time, frequency, done?).
    Pet       - pet details plus the list of tasks for that pet.
    Owner     - a person who manages one or more pets.
    Scheduler - the "brain" that retrieves and organizes tasks across pets.

Task, Pet, and Owner are dataclasses (they mostly hold data); Scheduler is a
plain class since it is pure behavior over an Owner's pets.
"""

import datetime
from dataclasses import dataclass, field


@dataclass
class Task:
    description: str
    time: datetime.time             # time of day the activity should happen
    frequency: str = "daily"        # e.g. "daily", "weekly", "once"
    completed: bool = False
    date: datetime.date | None = None  # day this occurrence falls on; None = undated / every day

    # How far ahead each recurring frequency repeats. "once" is absent on
    # purpose: it never recurs.
    _RECUR_DAYS = {"daily": 1, "weekly": 7}

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def reset(self) -> None:
        """Mark this task as not yet done (e.g. at the start of a new day)."""
        self.completed = False

    def next_occurrence(self) -> "Task | None":
        """Build the fresh (uncompleted) task for this activity's next repeat.

        Daily tasks recur one day later, weekly tasks one week later; any other
        frequency ('once') does not recur and returns None. If this task has no
        date, the next occurrence is measured from today.
        """
        step_days = self._RECUR_DAYS.get(self.frequency)
        if step_days is None:
            return None
        base = self.date or datetime.date.today()
        return Task(
            description=self.description,
            time=self.time,
            frequency=self.frequency,
            completed=False,
            date=base + datetime.timedelta(days=step_days),
        )

    def __str__(self) -> str:
        """Return a one-line, readable view of the task."""
        mark = "✓" if self.completed else "○"
        return f"{mark} {self.time.strftime('%H:%M')} — {self.description} ({self.frequency})"


@dataclass
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet (raises ValueError if not present)."""
        self.tasks.remove(task)

    def pending_tasks(self) -> list[Task]:
        """Return this pet's tasks that are not yet completed."""
        return [task for task in self.tasks if not task.completed]

    def completed_tasks(self) -> list[Task]:
        """Return this pet's tasks that are already completed."""
        return [task for task in self.tasks if task.completed]


@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's care."""
        self.pets.append(pet)

    def find_pet(self, name: str) -> Pet | None:
        """Return the pet with the given name, or None if not found."""
        for pet in self.pets:
            if pet.name == name:
                return pet
        return None

    def all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        tasks: list[Task] = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks


class Scheduler:
    """Organizes and manages tasks across all of an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler that works over the given owner's pets."""
        self.owner = owner

    def all_tasks(self) -> list[Task]:
        """Every task the owner has, across all pets."""
        return self.owner.all_tasks()

    def pending_tasks(self) -> list[Task]:
        """All not-yet-completed tasks across every pet."""
        return [task for task in self.all_tasks() if not task.completed]

    # --- Sorting --------------------------------------------------------------
    @staticmethod
    def sort_by_time(tasks: list[Task]) -> list[Task]:
        """Return `tasks` ordered by time of day, earliest first.

        This is the one place sorting happens; daily_agenda() and agenda() both
        route through it. It relies on Task.time being a datetime.time (which is
        directly comparable), so the sort key is simply each task's time. Returns
        a new list and leaves the input untouched.
        """
        return sorted(tasks, key=lambda task: task.time)

    def daily_agenda(self, on: datetime.date | None = None) -> list[Task]:
        """Pending tasks due on a given day (default today), ordered by time.

        An undated task counts as due every day. A dated task only shows once
        its day has arrived, so the follow-up occurrences created by
        complete_task() stay hidden until then instead of cluttering today.
        """
        day = on or datetime.date.today()
        due = [
            task
            for task in self.pending_tasks()
            if task.date is None or task.date <= day
        ]
        return self.sort_by_time(due)

    def tasks_for_pet(self, pet_name: str) -> list[Task]:
        """All tasks for a single named pet ([] if the pet isn't found)."""
        pet = self.owner.find_pet(pet_name)
        return list(pet.tasks) if pet else []

    def tasks_by_frequency(self, frequency: str) -> list[Task]:
        """All tasks across pets matching a given frequency (e.g. 'daily')."""
        return [task for task in self.all_tasks() if task.frequency == frequency]

    # --- Filtering ------------------------------------------------------------
    def filter_tasks(
        self,
        *,
        pet_name: str | None = None,
        completed: bool | None = None,
        frequency: str | None = None,
    ) -> list[Task]:
        """Return tasks matching every criterion given.

        Any argument left as None is ignored, so callers can mix and match:
        e.g. filter_tasks(pet_name="Biscuit", completed=False) is Biscuit's
        pending tasks. Pass nothing to get every task.
        """
        tasks = self.tasks_for_pet(pet_name) if pet_name else self.all_tasks()
        if completed is not None:
            tasks = [task for task in tasks if task.completed == completed]
        if frequency is not None:
            tasks = [task for task in tasks if task.frequency == frequency]
        return tasks

    def agenda(
        self,
        *,
        pet_name: str | None = None,
        completed: bool | None = None,
        frequency: str | None = None,
    ) -> list[Task]:
        """Filtered tasks sorted by time of day (earliest first)."""
        tasks = self.filter_tasks(
            pet_name=pet_name, completed=completed, frequency=frequency
        )
        return self.sort_by_time(tasks)

    def pet_for_task(self, task: Task) -> Pet | None:
        """Return the pet that owns a given task, or None if unattached.

        Uses identity ('is') rather than equality so two tasks that happen to
        look alike (same time/description) never resolve to the wrong pet.
        """
        for pet in self.owner.pets:
            if any(task is owned for owned in pet.tasks):
                return pet
        return None

    # --- Recurring tasks & conflicts -----------------------------------------
    def complete_task(self, task: Task) -> Task | None:
        """Mark a task complete and auto-queue its next occurrence if it recurs.

        This is the preferred way to finish a task. Daily and weekly tasks get a
        fresh instance added to the same pet, dated for the next day/week (so it
        does not resurface on today's agenda). Non-recurring ('once') tasks are
        simply marked done. Returns the follow-up Task, or None if none recurs.
        """
        task.mark_complete()
        follow_up = task.next_occurrence()
        if follow_up is not None:
            pet = self.pet_for_task(task)
            if pet is not None:
                pet.add_task(follow_up)
        return follow_up

    def start_new_day(self) -> None:
        """Roll over to a fresh day, respecting each task's frequency.

        Recurring tasks (e.g. 'daily', 'weekly') are reset to pending so they
        show up again. One-off ('once') tasks that are already done are removed,
        since they should not recur.
        """
        for pet in self.owner.pets:
            for task in list(pet.tasks):
                if task.frequency == "once":
                    if task.completed:
                        pet.remove_task(task)
                else:
                    task.reset()

    def conflicts(self, within_minutes: int = 0) -> list[tuple[Task, Task]]:
        """Pairs of pending tasks that clash in time.

        An owner can only be in one place at a time, so two pending tasks at the
        same time of day (or within `within_minutes` of each other) are a
        conflict. Returns each clashing pair once, ordered by time.
        """
        agenda = self.daily_agenda()  # already sorted by time
        clashes: list[tuple[Task, Task]] = []
        for earlier, later in zip(agenda, agenda[1:]):
            if _minutes_between(earlier.time, later.time) <= within_minutes:
                clashes.append((earlier, later))
        return clashes

    def conflict_warnings(self, within_minutes: int = 0) -> list[str]:
        """Human-readable warnings for each time clash (never raises).

        A "lightweight" strategy: instead of blocking or erroring when two tasks
        overlap, this just describes the clash so the caller can print it and
        carry on. It notes whether the two tasks belong to the same pet or to
        different pets. Returns an empty list when nothing conflicts.
        """
        warnings: list[str] = []
        for earlier, later in self.conflicts(within_minutes):
            pet_a = self.pet_for_task(earlier)
            pet_b = self.pet_for_task(later)
            name_a = pet_a.name if pet_a else "?"
            name_b = pet_b.name if pet_b else "?"
            when = earlier.time.strftime("%H:%M")

            if pet_a is not None and pet_a is pet_b:
                who = f"{name_a} has two tasks"
            else:
                who = f"{name_a} and {name_b} are both scheduled"

            warnings.append(
                f"⚠ Conflict at {when}: {who} "
                f"('{earlier.description}' and '{later.description}')."
            )
        return warnings

    def reset_all(self) -> None:
        """Reset every task to not-completed (e.g. to start a fresh day)."""
        for task in self.all_tasks():
            task.reset()


def _minutes_between(earlier: datetime.time, later: datetime.time) -> int:
    """Whole minutes from `earlier` to `later` on the same day."""
    return (later.hour * 60 + later.minute) - (earlier.hour * 60 + earlier.minute)