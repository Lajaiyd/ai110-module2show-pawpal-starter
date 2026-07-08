"""Demo script for PawPal+.

Builds an owner with a couple of pets, gives them some care tasks, and
prints today's schedule (all pending tasks ordered by time of day).

Run with:  python main.py
"""

import datetime

from pawpal_system import Owner, Pet, Scheduler, Task


def build_owner() -> Owner:
    """Create a sample owner with two pets and a few tasks each.

    Tasks are added deliberately OUT OF TIME ORDER (evening before morning,
    etc.) so the terminal output proves the sorting methods are doing the work
    rather than just echoing insertion order.
    """
    biscuit = Pet("Biscuit", "dog")
    biscuit.add_task(Task("Dinner", datetime.time(18, 0)))                       # 18:00 first
    biscuit.add_task(Task("Morning walk", datetime.time(8, 0)))                  # 08:00 second
    biscuit.add_task(Task("Give medication", datetime.time(8, 0)))               # 08:00 too -> same-pet clash
    biscuit.add_task(Task("Vet check-up", datetime.time(15, 30), frequency="weekly"))

    whiskers = Pet("Whiskers", "cat")
    whiskers.add_task(Task("Litter box clean", datetime.time(9, 0), frequency="daily"))
    whiskers.add_task(Task("Breakfast", datetime.time(7, 30)))                   # earliest, added late
    # Same 08:00 slot as Biscuit's walk -> a scheduling conflict to surface.
    whiskers.add_task(Task("Grooming", datetime.time(8, 0), frequency="weekly"))

    return Owner("Sam", pets=[biscuit, whiskers])


def print_schedule(owner: Owner) -> None:
    """Print today's schedule for every pet, ordered by time."""
    scheduler = Scheduler(owner)

    print(f"Today's Schedule for {owner.name}")
    print("=" * 32)

    for task in scheduler.daily_agenda():
        # pet_for_task replaces the old manual `next(...)` reverse lookup.
        pet = scheduler.pet_for_task(task)
        label = pet.name if pet else "?"
        print(f"{task.time.strftime('%H:%M')}  {label:<9} {task.description} ({task.frequency})")

    print("-" * 32)
    print(f"{len(scheduler.pending_tasks())} tasks pending across {len(owner.pets)} pets")


def print_conflicts(owner: Owner) -> None:
    """Print lightweight warnings for pending tasks that clash in time."""
    scheduler = Scheduler(owner)
    warnings = scheduler.conflict_warnings()

    print("\nScheduling conflicts")
    print("=" * 32)
    if not warnings:
        print("  None — the schedule is clear.")
    for message in warnings:
        print(f"  {message}")


def print_pet_agenda(owner: Owner, pet_name: str) -> None:
    """Show one pet's pending tasks, sorted by time (filter-by-pet demo)."""
    scheduler = Scheduler(owner)
    tasks = scheduler.agenda(pet_name=pet_name, completed=False)

    print(f"\nPending for {pet_name}")
    print("=" * 32)
    for task in tasks:
        print(f"  {task}")


def demonstrate_recurrence(owner: Owner) -> None:
    """Complete recurring tasks and show their next occurrences auto-created."""
    scheduler = Scheduler(owner)

    print("\nRecurring-task auto-generation")
    print("=" * 32)
    print(f"Total tasks before: {len(scheduler.all_tasks())}")

    # Complete one daily and one weekly task THROUGH the scheduler.
    for pet_name, description in [("Whiskers", "Litter box clean"), ("Biscuit", "Vet check-up")]:
        task = next(t for t in owner.find_pet(pet_name).tasks if t.description == description)
        follow_up = scheduler.complete_task(task)
        when = follow_up.date.strftime("%a %d %b") if follow_up and follow_up.date else "n/a"
        print(f"  Completed {description:<16} ({task.frequency:<6}) -> next occurrence {when}")

    print(f"Total tasks after:  {len(scheduler.all_tasks())}")
    # The completed occurrences are gone from today; their follow-ups are dated
    # ahead, so today's agenda stays clean.
    print(f"Today's agenda now: {[t.description for t in scheduler.daily_agenda()]}")


def print_by_status(owner: Owner) -> None:
    """Split every task into done vs. pending (filter-by-status demo)."""
    scheduler = Scheduler(owner)
    done = scheduler.filter_tasks(completed=True)
    pending = scheduler.filter_tasks(completed=False)

    print(f"\nCompleted ({len(done)})")
    print("=" * 32)
    for task in done:
        print(f"  {task}")

    print(f"\nStill to do ({len(pending)})")
    print("=" * 32)
    for task in pending:
        print(f"  {task}")


def main() -> None:
    owner = build_owner()

    print_schedule(owner)               # sorting: full agenda by time
    print_conflicts(owner)              # conflict detection (08:00 clash)
    print_pet_agenda(owner, "Biscuit")  # filter by pet + sort
    demonstrate_recurrence(owner)       # complete recurring tasks -> next occurrence auto-created
    print_by_status(owner)              # filter by completion status


if __name__ == "__main__":
    main()
