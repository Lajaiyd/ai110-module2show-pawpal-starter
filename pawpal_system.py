"""PawPal+ core system classes.

Skeleton generated from diagrams/uml_draft.mmd. Data objects (Pet, Task,
Owner) use dataclasses; Scheduler holds the scheduling behavior.
Method bodies are stubs to be implemented.
"""

from dataclasses import dataclass, field
from datetime import time


@dataclass
class Pet:
    name: str
    species: str
    feeding_interval: int      # hours between feedings
    exercise_minutes: int      # target exercise per day

    def needs_summary(self) -> str:
        """Return a short human-readable summary of this pet's care needs."""
        raise NotImplementedError


@dataclass
class Task:
    title: str
    duration: int              # minutes
    priority: int              # higher = more important
    task_type: str             # e.g. "walk", "feeding", "meds", "grooming"

    def estimate_end_time(self, start: time) -> time:
        """Return the clock time this task would finish if begun at `start`."""
        raise NotImplementedError

    def is_high_priority(self) -> bool:
        """Return True if this task counts as high priority."""
        raise NotImplementedError


@dataclass
class Owner:
    name: str
    wake_up_time: time
    sleep_time: time
    pet: Pet                                        # Owner "cares for" one Pet
    preferred_task_order: list[str] = field(default_factory=list)

    def can_schedule(self, duration: int) -> bool:
        """Return True if `duration` minutes still fit in the owner's day."""
        raise NotImplementedError

    def prefers(self, task: Task) -> bool:
        """Return True if this task ranks in the owner's preferred order."""
        raise NotImplementedError


class Scheduler:
    def generate_daily_plan(self, owner: Owner, tasks: list[Task]) -> list[Task]:
        """Build an ordered, time-feasible plan for the owner's day."""
        raise NotImplementedError

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by scheduling importance (e.g. priority)."""
        raise NotImplementedError

    def filter_tasks(self, tasks: list[Task], owner: Owner) -> list[Task]:
        """Return only the tasks that fit the owner's constraints."""
        raise NotImplementedError
