# PawPal+ Context Handoff

> **Purpose:** This document preserves all project context so a new chat session can continue seamlessly.
> **Last updated:** 2026-02-12
> **Read this file first in any new session.**

---

## 1. Project Overview

**PawPal+** is a CodePath AI110 Module 2 project — a Streamlit-based pet care planning assistant. Users register, add pets, define tasks per pet, set availability windows, and generate an AI-scheduled daily plan using a weighted scoring algorithm.

- **Language:** Python 3.14
- **Frontend:** Streamlit >= 1.30
- **Testing:** pytest >= 7.0
- **Workspace:** `C:\Users\brtah\OneDrive\Desktop\Mah Heart\pawpal-starter`
- **Venv:** `.venv` (streamlit installed)
- **GitHub Remote:** `https://github.com/DevKingB/pawpal-Project.git`

---

## 2. File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `app.py` | ~627 | Full Streamlit frontend — login, pets, tasks, availability, plan execution |
| `pawpal_system.py` | ~488 | Backend: User, Pet, Task, Scheduler, DailyPlan, TimeWindow, enums |
| `tests/test_pawpal.py` | ~750 | 75 unit tests (58 original TDD + 17 regression). ALL PASSING. |
| `system_design.md` | 12 sections | Architecture doc: data model, scheduler algorithm, lifecycle rules |
| `PR_BUGFIX_NOTES.md` | ~55 | PR description template with bug/todo/future tracking tables |
| `reflection.md` | Sections 1-5 | Module reflection (Section 1 started, 2-5 still needed) |
| `requirements.txt` | 3 lines | streamlit, pytest |
| `CONTEXT_HANDOFF.md` | this file | Session continuity document |

---

## 3. Git Branch Structure

```
main                    ← untouched CodePath starter (default branch)
└── feature/core-logic  ← full implementation (pawpal_system.py, app.py, tests, design doc)
    └── bugfix/ui-fixes ← bug fixes (2 rounds merged + 1 round uncommitted)
```

**Current branch:** `bugfix/ui-fixes` (note: remote may show `buggix/ui-fixes` due to earlier typo — was renamed locally)

**PR History:**
- PR #1: `bugfix/ui-fixes` → `feature/core-logic` — **MERGED** (7 verified bug fixes + 17 regression tests)
- Round 2 fixes: 4 additional bugs fixed, **UNCOMMITTED** (see Section 5 below)

---

## 4. Bug Tracking — Complete Status

### All Fixed (11 total)

| # | Bug | Fix Summary | PR/Status |
|---|-----|-------------|-----------|
| 17 | Plan carries across users | Clear `current_plan`, IDs, counters on register/login | PR #1 ✅ |
| 11 | Done/Skip in DRAFT state | Gate buttons behind `plan.status == PlanStatus.ACCEPTED` | PR #1 ✅ |
| 10 | Generate Plan always visible | Hide button when plan is ACCEPTED: `if not plan or plan.status == PlanStatus.DRAFT` | Round 2 (uncommitted) |
| 8 | Skip label unclear | ⏭️ icon, "not today, no penalty" caption, tooltip | PR #1 ✅ |
| 1 | Form pre-populated after submit | Counter-based form keys (`pet_form_counter`, `task_form_counter`) | PR #1 ✅ |
| 3 | Whitespace-only names accepted | `.strip()` on all text inputs | PR #1 ✅ |
| 4 | Toast not visible before rerun | Replaced `st.toast()` with session state flag (`success_msg`) + `show_success_message()` helper | Round 2 (uncommitted) |
| 5 | Duplicate task spam | Case-insensitive duplicate detection per pet | PR #1 ✅ |
| 7 | Availability error expands UI | `st.toast()` instead of inline `st.error()` | PR #1 ✅ |
| NEW | Regenerate wipes completed tasks | Downstream of #10 — fixed by hiding Generate Plan in ACCEPTED | Round 2 (uncommitted) |
| NEW | Logout doesn't clear state | Full state reset on logout (user, plan, IDs, counters) | Round 2 (uncommitted) |

### TODOs (not yet implemented)

| # | TODO | Description | File(s) |
|---|------|-------------|---------|
| 6 | Task edit/delete | User cannot fix mistakes on tasks after creation | app.py |
| 9 | Onboarding flow | Guided hints: Add Pets → Tasks → Availability → Plan | app.py |
| 12a | Cross-day lifecycle Phase 1 | Wire `mark_missed()`, `reset()`, deferral routing (Section 12 of system_design.md) | pawpal_system.py |
| 12b | `days_deferred` tracking | `_score_task()` formula correct but `days_deferred` never increments | pawpal_system.py |

### Future Enhancements (stretch goals)

| # | Enhancement | Description |
|---|-------------|-------------|
| 13 | Reward system | Tie completion into `RewardSystem` — points, streaks, badges |
| 14 | Persistence (SQLite) | Replace in-memory session state with database |
| 15 | Template vs Instance | Task template/instance split for proper lifecycle |
| 16 | Toast positioning | `st.toast()` always top-right; Streamlit limitation |

---

## 5. Current Uncommitted Changes (Round 2)

The diff on `app.py` contains 4 fixes:

1. **BUG #10 fix:** Generate Plan button gated with `if not plan or plan.status == PlanStatus.DRAFT`
2. **Logout fix:** Clears `user`, `current_plan`, `next_task_id`, `next_pet_id`, `pet_form_counter`, `task_form_counter` on logout
3. **BUG #4 fix:** New `success_msg` session state key + `show_success_message()` helper replaces all `st.toast()` calls with flag pattern
4. **Regenerate wipes tasks:** Resolved as downstream of #10

**Validation:** `py_compile app.py` clean, 75/75 pytest passing.

**Next step:** Commit, push, then either update the existing PR or create a new one.

---

## 6. Architecture Highlights

### Session State Keys (app.py)
- `user` — User object (None when logged out)
- `scheduler` — Scheduler singleton
- `current_plan` — DailyPlan object
- `next_task_id` / `next_pet_id` — auto-increment counters
- `pet_form_counter` / `task_form_counter` — counter-based form keys (BUG #1 fix)
- `page` — current page string ("login", "dashboard", "pets", "add_task", "availability", "plan")
- `success_msg` — pending success message string (BUG #4 fix)

### Scheduler Algorithm (pawpal_system.py)
- **Score:** `priority_weight × (1 + days_deferred)` where weights are Critical=4, High=3, Medium=2, Low=1
- **Placement:** Greedy time-window — sort tasks by score descending, place into first window with remaining capacity
- **Overflow:** Tasks that don't fit go to `deferred_tasks`; weekly-only or already-completed go to `backlog`

### Plan Lifecycle (system_design.md Section 12)
- **DRAFT:** User can view, regenerate freely. No Done/Skip visible.
- **ACCEPTED:** Plan locked. Done/Skip enabled. Generate Plan button hidden.
- **Skip semantics:** "Not today, no penalty" — task stays PENDING on the template, only skipped on today's plan instance.
- **Cross-day rules (TODO #12a):** At day boundary: PENDING tasks → `mark_missed()`, completed tasks acknowledged, plan resets for next day.

### Key Design Decisions
- **Counter-based form keys** (not `st.empty()`): Streamlit creates a fresh form widget tree each render
- **Session state flag for success messages** (not `st.toast()`): `st.toast()` fires before `st.rerun()` — invisible to user
- **Case-insensitive duplicate detection**: "Walk" and "walk" treated as same task per pet
- **No post-acceptance re-planning**: Once accepted, plan is locked. Future feature would require task-state persistence.

---

## 7. Test Structure

```
tests/test_pawpal.py
├── TestUserModel (5 tests)
├── TestPetModel (6 tests)
├── TestTaskModel (5 tests)
├── TestPetCategory (5 tests)
├── TestTimeWindow (4 tests)
├── TestScheduler (10 tests)
├── TestDailyPlan (6 tests)
├── TestPriority (3 tests)
├── TestFrequency (3 tests)
├── TestIntegration (11 tests)
└── TestBugFixRegressions (17 tests)
    ├── BUG #17 — user isolation (3)
    ├── BUG #11 — DRAFT vs ACCEPTED gating (3)
    ├── BUG #10 — regenerate in DRAFT only (1)
    ├── BUG #8 — skip visual state (3)
    ├── BUG #5 — duplicate task detection (3)
    ├── BUG #3 — whitespace handling (2)
    └── Skip lifecycle (2)
```

---

## 8. Remaining Work (Priority Order)

1. **Commit + push Round 2 fixes** → create/update PR to `feature/core-logic`
2. **Live server test** of all fixes (user was about to do this)
3. **Update PR_BUGFIX_NOTES.md** — move BUG #10, #4, logout, regenerate from "Needs Further Work" to "Verified"
4. **reflection.md** — Complete sections 2-5 (required for Module 2 submission)
5. **TODOs #6, #9** — Task edit/delete, onboarding flow (likely in a `feature/todo-enhancements` branch)
6. **TODOs #12a, #12b** — Cross-day lifecycle (requires `pawpal_system.py` changes)
7. **Stretch goals** — RewardSystem, SQLite, Template/Instance split

---

## 9. How to Resume in a New Chat

1. Open the workspace: `C:\Users\brtah\OneDrive\Desktop\Mah Heart\pawpal-starter`
2. Tell the new chat: **"Read CONTEXT_HANDOFF.md first — it has full project context from previous sessions."**
3. The new chat will read this file and have everything needed to continue.
4. If needed, also point it to `system_design.md` for architecture details and `PR_BUGFIX_NOTES.md` for bug tracking tables.

---

## 10. Commands Cheat Sheet

```bash
# Activate venv
.venv\Scripts\activate

# Run tests
python -m pytest -v

# Start Streamlit
streamlit run app.py

# Check current branch
git branch

# See uncommitted changes
git diff

# Commit round 2
git add app.py
git commit -m "fix: resolve remaining 4 bugs - Generate Plan gate, logout cleanup, success messages"
git push origin bugfix/ui-fixes
```
