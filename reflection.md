# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

Core user actions I identified:
1. Add a pet with basic information (name, species, age)
2. Add care tasks to a pet (walks, feeding, medications, vet appointments)
3. View a generated daily schedule that organizes all tasks by priority and time

I designed four classes: Owner, Pet, Task, and Scheduler. Owner holds a list of Pets. Each Pet holds a list of Tasks. Scheduler is the brain — it retrieves all tasks across all pets, sorts them, filters them, detects conflicts, and generates the daily plan. The design followed a clear hierarchy: Owner → Pet → Task, with Scheduler operating on top of that structure.

**b. Design changes**

After asking Cursor AI to review the class skeletons, two changes were made to Task:

1. Added `due_date` (string "YYYY-MM-DD") — the original design had no way to know when a "once" or "weekly" task should run. Without this, the scheduler couldn't decide if a task belongs to today.

2. Added `pet_name` (string) — when the Scheduler flattens all tasks from all pets into one list, tasks lost their pet identity. This field lets the schedule display "Feed Luna at 08:00" instead of just "Feed at 08:00".

Suggestions rejected: changing `time` to `datetime.time` (too complex for this stage), narrowing `filter_tasks` signature (deferred to Phase 4), and changing `detect_conflicts` return type (deferred to Phase 4).

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers:
- **Time** — tasks are sorted chronologically by their "HH:MM" attribute
- **Priority** — when two tasks share the same time, high priority tasks appear first (high → medium → low)
- **Completion status** — `filter_tasks()` separates done vs. pending tasks
- **Pet identity** — each task carries `pet_name` so the schedule always shows which pet needs what

Time was prioritized first because a daily schedule is fundamentally time-ordered. Priority serves as a tie-breaker, which is realistic — if two things are scheduled at the same time, do the most important one first.

**b. Tradeoffs**

The conflict detector only flags tasks with the exact same start time — it does not check for overlapping durations. For example, a 30-minute task at 08:00 and a 10-minute task at 08:15 would not be flagged as a conflict even though they overlap in real life. This is a reasonable tradeoff for a first version because it keeps the logic simple, readable, and fast. A full interval-overlap check would require converting all times to minutes-from-midnight and comparing ranges — valid, but out of scope for this stage.

---

## 3. AI Collaboration

**a. How I used AI**

I used Cursor AI as my primary development tool throughout every phase of this project — from UML design to implementation, testing, UI integration, and documentation. This was my first time using Cursor for a complete project (I had only used it for small tasks before), and the experience was impressive. 

The workflow that worked best was keeping a **new chat session per phase** — design, implementation, testing, and UI each had their own focused conversation. This prevented context pollution and kept AI responses sharp and relevant.

The most effective prompts were specific and structured: stating what file to reference, what the app does, and exactly what I wanted. Vague prompts gave vague results. Precise prompts gave production-quality code.

The moment that surprised me most was when the Streamlit app appeared live in the browser for the first time — seeing the backend logic I had built respond to real user input in real time made everything click. Mermaid.js was also a highlight: turning a text description into a visual class diagram instantly is something I'll use in every future project.

An important Cursor workflow discovery: reusing the correct 
chat history context instead of starting a new chat every 
time. When fixing a CSS issue, returning to the original 
theme chat gives the AI the full styling context — leading 
to more accurate fixes. New chat = clean context for new 
features. Existing chat = better context for related fixes.

**b. Judgment and verification**

The clearest example of human oversight paying off was during the AI review of the class skeletons. Cursor flagged five issues — I accepted two (adding `due_date` and `pet_name` to Task), partially accepted one (kept `time` as string instead of `datetime.time`), and deferred two to a later phase. Accepting everything blindly would have added unnecessary complexity too early.

A second example: when Cursor suggested extracting a named `_task_sort_key` function for readability, I evaluated it, agreed it was cleaner, and accepted it. That's the right loop — AI suggests, human evaluates, human decides.

A key lesson learned during the Optional Extensions: 
after implementing interval overlap in detect_conflicts(), 
the warning boxes appeared empty — which looked like a 
regression. The real issue was a CSS contrast problem, 
not broken logic. This reinforced two habits: always run 
pytest after every change before committing, and always 
verify manually in the browser. Automated tests catch 
logic regressions; manual testing catches visual ones.

---

## 4. Testing and Verification

**a. What I tested**

The test suite covers 16 behaviors across the full system:
- Task completion (`mark_complete` sets `is_complete` to True)
- Pet task management (adding tasks increases task count)
- Chronological sorting (tasks ordered by time)
- Priority tie-breaking (high priority first when times match)
- Case-insensitive pet name filtering
- Recurring task rescheduling (daily → +1 day, weekly → +7 days, once → None)
- Unknown frequency handling (returns None, no task added)
- Rescheduled task starts incomplete (`is_complete = False`)
- Conflict detection (2 tasks, 3 tasks at same time)
- Edge cases: owner with no pets, pet with no tasks, empty schedule

The most valuable test was `test_reschedule_recurring_daily_new_task_is_not_complete` — it caught a real bug where `dataclasses.replace` was copying `is_complete=True` from the completed task into the new one. Without that test, that bug would have reached production silently.

**b. Confidence**

⭐⭐⭐⭐ (4/5)

Core scheduling behaviors are well verified including edge cases. Remaining gaps: overlapping duration detection (interval-based conflicts) and calendar boundary cases (e.g., December 31 + daily recurrence). These would be the next tests to add.

---

## 5. Reflection

**a. What went well**

The CLI-first workflow was the best decision of the project. Building and verifying all logic in `main.py` before touching the Streamlit UI meant that when I connected the two, everything worked on the first try. Keeping backend (`pawpal_system.py`), UI (`app.py`), and tests (`test_pawpal.py`) as separate files with clear responsibilities made the system easy to reason about and easy to extend.

**b. What I would improve**

I would add interval-based conflict detection from the start — checking only for exact time matches is a known limitation. I would also wire `reschedule_recurring` directly into the UI so users can mark a task complete and see the next occurrence appear automatically, without manual intervention.

**c. Key takeaway**

Human oversight in AI-assisted development is not optional — it's what makes the difference between good software and broken software. The more precise your prompts, the more on top of each step you are, and the more you understand what the AI is doing and why, the better the outcome and the fewer the bugs. Planning and understanding every step is not wasted time — it's the most valuable time you spend. AI is a powerful consultant, but you are always the architect.