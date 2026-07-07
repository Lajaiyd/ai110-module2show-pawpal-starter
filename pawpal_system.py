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

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def reset(self) -> None:
        """Mark this task as not yet done (e.g. at the start of a new day)."""
        self.completed = False

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

    def daily_agenda(self) -> list[Task]:
        """Pending tasks ordered by time of day (earliest first)."""
        return sorted(self.pending_tasks(), key=lambda task: task.time)

    def tasks_for_pet(self, pet_name: str) -> list[Task]:
        """All tasks for a single named pet ([] if the pet isn't found)."""
        pet = self.owner.find_pet(pet_name)
        return list(pet.tasks) if pet else []

    def tasks_by_frequency(self, frequency: str) -> list[Task]:
        """All tasks across pets matching a given frequency (e.g. 'daily')."""
        return [task for task in self.all_tasks() if task.frequency == frequency]

    def reset_all(self) -> None:
        """Reset every task to not-completed (e.g. to start a fresh day)."""
        for task in self.all_tasks():
            task.reset()
