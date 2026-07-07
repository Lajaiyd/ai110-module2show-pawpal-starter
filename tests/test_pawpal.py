"""Tests for core PawPal+ behaviors."""

import datetime

from pawpal_system import Pet, Task


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
