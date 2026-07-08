# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**Agent used:** Claude Code (Opus 4.8).

**What task did you give the agent?**

Extend PawPal+ with a *third* algorithmic capability beyond the existing time-sorting and
recurrence/conflict logic. I chose **"next available slot"**: given a task length in minutes,
find the earliest free time of day that doesn't collide with tasks already scheduled. I asked
the agent to implement it in the core system, cover it with tests, and surface it in both the
CLI demo and the Streamlit UI — without changing the `Task` data model.

**What did the agent do?**

Files modified:

| File | Change |
|------|--------|
| `pawpal_system.py` | Added `Scheduler.next_available_slot(duration_minutes, *, on, day_start, day_end, gap_minutes)`; added `_to_minutes()` / `_from_minutes()` helpers and refactored `_minutes_between()` to reuse them. |
| `tests/test_pawpal.py` | Added 4 tests: empty schedule → day start; a busy block pushes the slot past its gap; picks the earliest opening; returns `None` when nothing fits. |
| `main.py` | Added `print_next_available_slot()` and wired it into `main()` so the CLI demo prints the earliest 30- and 90-minute openings. |
| `app.py` | Added a "💡 Find a free time" expander (duration input + button) that calls `next_available_slot()` and reports the suggested time with `st.success` / `st.warning`. |

The algorithm treats each pending task as occupying `gap_minutes` (default 30) from its start,
walks the day's tasks in sorted order, and returns the first opening in the `06:00–22:00` window
long enough for the requested duration — or `None` if the day is full. The agent ran the test
suite (**19 passing**) and executed `main.py` to confirm the demo output.

**What did you have to verify or fix manually?**

- **Window-boundary correctness.** The agent's first cut checked each gap only against the *next
  task's* start time. I flagged that a task scheduled after `day_end` could yield a slot running
  past the end of the day; the fix was to clamp with `usable_end = min(start, window_end)` and to
  bail out once the cursor passes `day_end`. I verified with a deliberately tiny 40-minute window
  test that now returns `None`.
- **No data-model creep.** I rejected an early suggestion to add a `duration` field to `Task`
  (which would have rippled through the UI, `__str__`, and every existing test). Keeping duration
  as a *parameter* of the slot search, with tasks occupying a fixed `gap_minutes`, kept the change
  localized to the `Scheduler`.
- **Verification I ran myself:** re-ran `python -m pytest` (19 passing) and `python main.py`, and
  confirmed the new Streamlit expander behaves sensibly (suggests `06:00` on an empty day, warns
  when no slot fits).

> Note: earlier in the project the same agent workflow also caught a recurrence **duplication bug**
> (`complete_task()` and `start_new_day()` were two competing recurrence mechanisms). I had it write
> a reproduction script to confirm the root cause before accepting the fix — a reminder to verify
> agent output by running it, not just reading it.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | | |
| **Prompt** | | |
| **Response summary** | | |
| **What was useful** | | |
| **Problems noticed** | | |
| **Decision** | | |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->
