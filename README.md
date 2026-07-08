# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## ✨ Features

Every feature below is backed by a method on the `Scheduler` (or `Task`) class in
`pawpal_system.py` — see [Smarter Scheduling](#-smarter-scheduling) for the details.

- **Sorting by time of day** — `Scheduler.sort_by_time()` orders any list of tasks earliest-first using each `Task.time` (a `datetime.time`) as the sort key. It's the single sorting primitive that `daily_agenda()` and `agenda()` both route through, and it returns a new list rather than mutating its input.
- **Date-aware daily agenda** — `Scheduler.daily_agenda(on=...)` returns only the *pending* tasks due on a given day (today by default), sorted by time. Undated tasks count as due every day; future-dated occurrences stay hidden until their day arrives.
- **Multi-criteria filtering** — `Scheduler.filter_tasks()` / `Scheduler.agenda()` filter by pet, completion status, and/or frequency in one composable call; any criterion left as `None` is ignored, so the same method covers "by pet," "by status," "by frequency," or any combination.
- **Conflict detection & warnings** — `Scheduler.conflicts()` finds pairs of pending tasks that land at the same time (or within an optional `within_minutes` window); `Scheduler.conflict_warnings()` turns each clash into a human-readable message and **returns it instead of raising**, distinguishing a same-pet clash from a two-pet clash.
- **Daily & weekly recurrence** — `Task.next_occurrence()` builds the next fresh instance of a recurring task (`daily` → +1 day, `weekly` → +7 days via `datetime.timedelta`, `once` → none); `Scheduler.complete_task()` marks a task done and auto-queues that next occurrence on the same pet, dated ahead.
- **New-day rollover** — `Scheduler.start_new_day()` resets recurring tasks to pending and drops completed one-off (`once`) tasks so they don't come back.
- **Identity-safe task → pet lookup** — `Scheduler.pet_for_task()` matches by identity (`is`), so two look-alike tasks (same time and description) never resolve to the wrong pet.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

A quick glance at today's schedule, sorted by time (full run in the
[Demo Walkthrough](#-demo-walkthrough) below):

```
Today's Schedule for Sam
================================
07:30  Whiskers  Breakfast (daily)
08:00  Biscuit   Morning walk (daily)
08:00  Biscuit   Give medication (daily)
08:00  Whiskers  Grooming (weekly)
09:00  Whiskers  Litter box clean (daily)
15:30  Biscuit   Vet check-up (weekly)
18:00  Biscuit   Dinner (daily)
--------------------------------
7 tasks pending across 2 pets
```

## 🧪 Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

The tests in `tests/test_pawpal.py` cover the system's core scheduling behaviors:

- **Sorting correctness** — tasks added out of order are returned earliest-time-first, the sort returns a copy (never mutates its input), and tasks at the same time keep their insertion order (stable sort).
- **Recurrence logic** — completing a `daily` task queues a fresh, uncompleted copy dated for the next day and attached to the same pet; `weekly` recurs seven days out; and `once` tasks are marked done without recurring.
- **Conflict detection** — two pending tasks at the same time of day are flagged as a single conflict pair with a matching warning, while tasks at distinct times and already-completed tasks raise no conflict.
- **Edge cases** — an owner with no pets or tasks yields an empty agenda and no conflicts instead of crashing.

Successful test run:

```
jideakinyemi@MacBookPro ai110-module2show-pawpal-starter % python -m pytest
============================================================================================= test session starts =============================================================================================
platform darwin -- Python 3.13.9, pytest-8.3.4, pluggy-1.5.0
rootdir: /Users/jideakinyemi/Documents/python-primer/ai110-module2show-pawpal-starter
plugins: anyio-4.7.0
collected 12 items

tests/test_pawpal.py ............                                                                                                                                                                       [100%]

============================================================================================= 12 passed in 0.03s ==============================================================================================
```

### Confidence Level

**(4 / 5)**

All 12 tests pass and the three most important behaviors — sorting, recurrence, and conflict detection — are verified across both happy paths and key edge cases. One star is held back because a few known gaps remain untested: three-or-more tasks at the same time (only consecutive pairs are reported), the `start_new_day()` rollover, and the `within_minutes` conflict window. Reliability for the core scheduling logic is high; the confidence ceiling reflects coverage breadth, not observed defects.

## 📐 Smarter Scheduling

All scheduling logic lives on the `Scheduler` class in `pawpal_system.py`, which
works over one `Owner`'s pets. Each feature below names the method that
implements it.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting by time | `Scheduler.sort_by_time()` | Shared primitive used by `daily_agenda()` and `agenda()` |
| Filtering | `Scheduler.filter_tasks()` / `Scheduler.agenda()` | By pet, completion status, and/or frequency |
| Conflict detection | `Scheduler.conflicts()` / `Scheduler.conflict_warnings()` | Same-time clashes; warnings never crash |
| Recurring tasks | `Task.next_occurrence()` / `Scheduler.complete_task()` | Daily/weekly auto-generate the next occurrence |

### Sorting behavior — `Scheduler.sort_by_time(tasks)`

The single place sorting happens. It returns a new list ordered by time of day
(earliest first) using `sorted(tasks, key=lambda task: task.time)`. This works
because `Task.time` is a `datetime.time`, which is directly comparable — no
string parsing needed. Both `daily_agenda()` (today's pending tasks) and
`agenda(...)` (filtered tasks) route through it, so ordering is defined once.

### Filtering behavior — `Scheduler.filter_tasks(...)`

One composable filter with keyword-only arguments:

```python
scheduler.filter_tasks(pet_name="Biscuit", completed=False)  # Biscuit's pending tasks
scheduler.filter_tasks(completed=True)                        # everything already done
scheduler.filter_tasks(frequency="weekly")                    # all weekly tasks
```

Any argument left as `None` is ignored, so the same method covers "by pet,"
"by status," "by frequency," or any combination. `Scheduler.agenda(...)` takes
the same arguments and additionally sorts the result by time.
`Scheduler.pet_for_task(task)` is a supporting helper that finds which pet owns
a task by identity (`is`), so look-alike tasks never resolve to the wrong pet.

### Conflict detection — `Scheduler.conflicts()` and `Scheduler.conflict_warnings()`

`conflicts(within_minutes=0)` scans the time-sorted agenda and returns pairs of
pending tasks that land at the same time (or within `within_minutes` of each
other) — an owner can only be in one place at once, whether the clash is for the
**same pet or two different pets**. `conflict_warnings(...)` is the "lightweight"
layer on top: it turns each pair into a human-readable string and **returns it
rather than raising**, so a clash never crashes the program. It distinguishes
the two cases automatically:

```
⚠ Conflict at 08:00: Biscuit has two tasks ('Morning walk' and 'Give medication').
⚠ Conflict at 08:00: Biscuit and Whiskers are both scheduled ('Give medication' and 'Grooming').
```

### Recurring task logic — `Task.next_occurrence()` and `Scheduler.complete_task()`

`Task.next_occurrence()` builds the next fresh (uncompleted) instance of a
recurring task: `daily` repeats one day later, `weekly` one week later (via
`datetime.timedelta`, so month/year/leap-year rollover is handled correctly),
and `once` returns `None`. `Scheduler.complete_task(task)` is the preferred way
to finish a task — it marks the task done and, if it recurs, automatically adds
the next occurrence to the same pet, dated ahead. Because `daily_agenda()` only
shows tasks due today or earlier, those future occurrences stay hidden until
their day arrives instead of piling up on today's list.

## 💾 Data Persistence

PawPal+ remembers your pets and tasks **between runs** by saving them to a
`data.json` file. The web app loads it on startup and re-saves after every
change, so closing the browser and reopening later brings everything back.

### Workflow

1. **On startup**, `app.py` calls `Owner.load_from_json("data.json")`. If the file
   doesn't exist yet (first run) or is corrupt, it falls back to a fresh `Owner`.
2. **After every change** — adding a pet, scheduling a task, marking one done,
   renaming the owner, or starting a new day — the app calls a small `persist()`
   helper that runs `owner.save_to_json("data.json")`.
3. **On the next run**, that file is read back and the full owner → pets → tasks
   tree is reconstructed.

`data.json` is written next to `app.py` and is **git-ignored** (it's per-user
runtime data, not source).

### How serialization works (custom dictionary conversion)

The tricky part is that a `Task` holds `datetime.time` and `datetime.date`
objects, which the `json` module **cannot** serialize on its own
(`TypeError: Object of type time is not JSON serializable`). Rather than add a
dependency, PawPal+ uses **custom `to_dict()` / `from_dict()` methods** on each
class, converting the awkward types to and from ISO-8601 strings:

```python
# Task.to_dict()  ->  JSON-safe
{"description": "Walk", "time": "08:00:00", "frequency": "weekly",
 "completed": false, "date": "2026-07-09"}

# Task.from_dict()  parses the strings back into real objects
datetime.time.fromisoformat("08:00:00")   # -> datetime.time(8, 0)
datetime.date.fromisoformat("2026-07-09") # -> datetime.date(2026, 7, 9)
```

Each level nests the one below it — `Owner.to_dict()` calls `Pet.to_dict()`,
which calls `Task.to_dict()` — so the whole tree serializes recursively, and
`Owner.save_to_json()` / `load_from_json()` just wrap `json.dump` / `json.load`
around it. A round-trip preserves times, dates (including `None`), completion
status, and frequency exactly.

> **Alternative: marshmallow.** A schema library like
> [marshmallow](https://marshmallow.readthedocs.io/) can automate this with
> declarative schemas (e.g. `fields.Time()`, `fields.Date(allow_none=True)`) and
> add validation on load. We chose hand-written `to_dict()`/`from_dict()` here
> because the object graph is small and fixed, it keeps the project
> dependency-free, and it makes the `datetime` conversion explicit and easy to
> test. marshmallow would earn its keep once the schema grows or needs strict
> input validation.

### Files modified for persistence

| File | Change |
|------|--------|
| `pawpal_system.py` | Added `to_dict()` / `from_dict()` to `Task`, `Pet`, and `Owner`, plus `Owner.save_to_json()` and `Owner.load_from_json()`. |
| `app.py` | Loads `data.json` on startup (fresh `Owner` fallback) and calls `persist()` after every change. |
| `tests/test_pawpal.py` | Added a save→load round-trip test and a missing-file test. |
| `.gitignore` | Ignores the generated `data.json`. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
