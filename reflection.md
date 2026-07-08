# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML modeled four classes with a clear split between *data* and *behavior*:

- **`Task`** — a single care activity: `description`, `time` of day, `frequency`, and a `completed` flag, with `mark_complete()` / `reset()`.
- **`Pet`** — a pet's `name` and `species` plus the list of its `Task`s, with add/remove and pending/completed queries.
- **`Owner`** — a person who manages one or more `Pet`s (`add_pet`, `find_pet`, `all_tasks`).
- **`Scheduler`** — the "brain" that reads across an owner's pets and organizes their tasks (sorting, filtering, the daily agenda).

`Task`, `Pet`, and `Owner` are dataclasses because they mostly hold data; `Scheduler` is a plain class because it is pure behavior over an `Owner`.

**b. Design changes**

The three data classes stayed stable, but `Task` and `Scheduler` grew during implementation:

- **Added `Task.date` (and `next_occurrence()`).** Originally a `Task` only knew its time of day. To support recurrence I added a `date` field so an occurrence could belong to a specific day. Without it, an auto-generated "next occurrence" had nowhere to live except today, and it would clutter the current agenda.
- **Grew the `Scheduler`.** I added a single shared sorting primitive `sort_by_time()` that both `daily_agenda()` and `agenda()` route through, plus `filter_tasks()`/`agenda()` for filtering, `conflicts()`/`conflict_warnings()` for clash detection, and `complete_task()`/`start_new_day()` for recurrence and rollover.
- **Fixed the recurrence model.** Late in the build I found the Scheduler had *two* competing recurrence mechanisms; I reconciled them (see §3b) and updated `diagrams/uml_final.mmd` to show the Scheduler's behavioral dependencies — it doesn't just read the model, it **creates** `Task`s and **reaches into** `Pet`s to queue follow-ups.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler's primary constraint is **time of day**: the daily agenda is pending tasks sorted earliest-first, because the core user need is "what do I do next, in order." The second constraint is **frequency** (`daily` / `weekly` / `once`), which governs whether and when a task recurs. A third, softer constraint is the **owner's single availability** — a person can only be in one place at once — which is what makes two tasks at the same time a *conflict*. I treated time as most important because sorting is the foundation everything else (filtering, recurrence, conflicts) is organized around.

**b. Tradeoffs**

- **Lightweight conflict warnings instead of hard blocking.** `conflict_warnings()` *describes* a clash and returns a string rather than raising or refusing the schedule. That's reasonable for a personal planner: an owner may legitimately choose to do two things at 08:00, so the app's job is to inform, not to police.
- **Adjacent-pair conflict scan.** `conflicts()` compares each task only to the next one in the sorted agenda — O(n) and simple. The tradeoff: with three tasks at the same time it reports (A,B) and (B,C) but not (A,C). Acceptable, because a warning on that time slot already tells the owner enough.
- **Identity-based reverse lookup.** `pet_for_task()` matches with `is`, not `==`, so two look-alike tasks (same time and description) never resolve to the wrong pet — a deliberate choice given `Task` is a dataclass with value equality.

---

## 3. AI Collaboration

**a. How you used AI**

I used the AI assistant across the whole lifecycle: generating a **test plan** (enumerating happy paths and edge cases from the actual code), drafting **pytest** tests, refactoring the **Streamlit UI** to present sorted/filtered data with `st.table` and status filters, updating the **UML** and **README**, and **debugging**. The most helpful prompts were specific and verifiable — "test that completing a daily task creates a next-day occurrence," "use the `Scheduler` methods for the display logic" — rather than open-ended "make it better." Asking the AI to *run* the code and *reproduce* behavior was far more valuable than asking it to reason in the abstract.

**b. Judgment and verification**

The clearest moment: the running app was accumulating **duplicate recurring tasks** while "Today's Schedule" showed empty. Instead of accepting a doc edit, I pasted the actual on-screen state and had the AI investigate. It wrote a small reproduction script that pinned the root cause — **two conflicting recurrence mechanisms**: `complete_task()` creates a forward-dated follow-up, while `start_new_day()` was *also* resetting the completed original to pending, so every cycle left a duplicate. One tempting fix was to make `complete_task()` stop creating follow-ups, but I **rejected** that because it would delete a tested, documented feature. We instead changed `start_new_day()` to *retire* completed tasks, then added regression tests. I verified with the reproduction (task count stayed at 1 across cycles) and the full suite (15 passing).

---

## 4. Testing and Verification

**a. What you tested**

Three core behaviors plus edge cases: **sorting** (chronological order, non-mutation of the input list, stable tie-breaking for equal times), **recurrence** (daily → +1 day, weekly → +7, `once` → no recurrence, and no duplicate accumulation across new-day rollovers), and **conflict detection** (same-time tasks flagged, distinct times and already-completed tasks not flagged). These matter because they are exactly the algorithms the scheduler is judged on — and the recurrence tests directly guard the duplication bug we fixed.

**b. Confidence**

Confidence is **4/5**. All 15 tests pass and the three headline behaviors are covered on both happy and edge paths. I held back one point because a few cases remain untested: three-or-more tasks at the same time (the adjacent-pair gap), the `within_minutes` conflict window, and the interaction between the real calendar date and the app's logical "new day." Those are what I'd test next.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the single sorting primitive (`sort_by_time()`) that every agenda routes through, and with catching the recurrence duplication bug from live app behavior rather than shipping it. The system reads cleanly because behavior is concentrated in `Scheduler`.

**b. What you would improve**

I'd unify the recurrence model conceptually. The app uses the real calendar date while "Start a new day" is a *logical* rollover, and the two don't fully line up — a follow-up dated "tomorrow" stays hidden until the real date arrives. I'd add a simulated "today" the app can advance so the demo flows without confusion.

**c. Key takeaway — being the "lead architect" with powerful AI tools**

The AI was fastest at *generation and mechanical verification* — writing tests, refactoring the UI, and especially building reproduction scripts on demand. But it does not own the design's invariants; I do. The duplication bug existed because two individually-reasonable mechanisms conflicted, and only a human holding the whole model in view could see that and reject the "easy" fix that would have broken a feature.

What worked as lead architect:
- **Most effective AI features:** multi-file context (pointing at `app.py`, `pawpal_system.py`, `main.py` together), on-demand code execution to *run* tests and reproduce bugs, and grounded test-plan generation from the real code instead of guesses.
- **A suggestion I modified to keep the design clean:** when the UI moved to a professional `st.table`, the first pass dropped the per-task "Done" controls; I kept completion working by adding a selectbox-driven form rather than silently losing functionality. (And on the bug, I rejected the follow-up-removal "fix" in favor of fixing `start_new_day()`.)
- **How separate phases/sessions helped:** keeping design (UML), implementation, testing, UI, and documentation as distinct phases — visible in the commit history — kept each conversation focused on one concern, so the AI wasn't juggling unrelated context and I could trace which decision belonged to which phase.
- **The lesson:** treat AI output as a *proposal from a fast junior engineer* — accept what fits the architecture, run everything, and reject anything that trades a real invariant for local convenience. The AI amplifies judgment; it does not replace it.
