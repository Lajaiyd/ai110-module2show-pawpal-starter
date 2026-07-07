"""Demo script for PawPal+.

Builds an owner with a couple of pets, gives them some care tasks, and
prints today's schedule (all pending tasks ordered by time of day).

Run with:  python main.py
"""

import datetime

from pawpal_system import Owner, Pet, Scheduler, Task


def build_owner() -> Owner:
    """Create a sample owner with two pets and a few tasks each."""
    biscuit = Pet("Biscuit", "dog")
    biscuit.add_task(Task("Morning walk", datetime.time(8, 0)))
    biscuit.add_task(Task("Dinner", datetime.time(18, 0)))
    biscuit.add_task(Task("Vet check-up", datetime.time(15, 30), frequency="weekly"))

    whiskers = Pet("Whiskers", "cat")
    whiskers.add_task(Task("Breakfast", datetime.time(7, 30)))
    whiskers.add_task(Task("Litter box clean", datetime.time(9, 0), frequency="daily"))

    return Owner("Sam", pets=[biscuit, whiskers])


def print_schedule(owner: Owner) -> None:
    """Print today's schedule for every pet, ordered by time."""
    scheduler = Scheduler(owner)

    print(f"Today's Schedule for {owner.name}")
    print("=" * 32)

    for task in scheduler.daily_agenda():
        # Find which pet this task belongs to, for a clearer line.
        pet = next(p for p in owner.pets if task in p.tasks)
        print(f"{task.time.strftime('%H:%M')}  {pet.name:<9} {task.description} ({task.frequency})")

    print("-" * 32)
    print(f"{len(scheduler.pending_tasks())} tasks pending across {len(owner.pets)} pets")


def main() -> None:
    owner = build_owner()
    print_schedule(owner)


if __name__ == "__main__":
    main()
