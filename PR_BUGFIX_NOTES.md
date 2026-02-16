# PR: bugfix/ui-fixes → implementation

## Summary
This branch fixes **7 verified UI/UX bugs** identified during user testing of the PawPal+ Streamlit frontend, and adds **17 regression tests** (75 total).

---

## Category Table

### Bug Fixes — Verified (this PR)

| # | Bug | Description | Severity | Verified |
|---|-----|-------------|----------|----------|
| 17 | Plan carries across users | `current_plan`, `next_task_id`, `next_pet_id` not cleared on register/login — new user inherits previous user's data | **Critical** | ✅ Manual |
| 11 | Done/Skip in DRAFT | Done and Skip buttons render when plan is still DRAFT; should only appear in ACCEPTED state | **High** | ✅ Manual + Unit |
| 8 | Skip label unclear | Skip gives no feedback; label doesn't explain "not today, no penalty" semantics; no visual distinction for skipped tasks | **Medium** | ✅ Manual + Unit |
| 1 | Form pre-populated | After adding a pet, form fields retain previous input on next render | **Medium** | ✅ Manual |
| 3 | Accidental submit | Pressing Enter submits form; whitespace-only names accepted | **Medium** | ✅ Manual + Unit |
| 5 | Duplicate task spam | No duplicate detection; user can add identical tasks repeatedly | **Low** | ✅ Manual + Unit |
| 7 | Availability error expands | Inline `st.error()` for bad time range causes the expander to visually jump/expand | **Low** | ✅ Toast swap |

### Bug Fixes — Needs Further Work (next PR)

| # | Bug | Description | Status |
|---|-----|-------------|--------|
| 10 | Generate Plan always visible | Top-level "Generate Plan" button shows even in ACCEPTED state, allowing user to overwrite an accepted plan and lose completed task progress | **Not fixed** — needs gate |
| 4 | Notification not visible | `st.toast()` fires but may not be visible before rerun; consider badge/indicator approach | **Partially fixed** — needs UX pivot |
| NEW | Regenerate wipes completed tasks | Generating a new plan creates fresh Task references; `mark_complete()` on old tasks is lost | ✅Fixed |
| NEW | Logout doesn't fully clear plan | Dashboard says "no plan" but pending load still reflects incomplete tasks | ✅Fixed |
| — | Availability carry-over | Availability windows from previous session may persist unexpectedly | **Deferred** |

### TODOs (deferred to `feature/todo-enhancements` branch)

| # | TODO | Description | File(s) |
|---|------|-------------|---------|
| 6 | Task edit/delete | User cannot fix mistakes on tasks after creation | app.py |
| 9 | Onboarding flow | No guided hints for new users (Add Pets → Tasks → Availability → Plan) | app.py |
| 12a | Cross-day lifecycle Phase 1 | Wire `mark_missed()`, `reset()`, deferral routing; see Section 12 of system_design.md | pawpal_system.py |
| 12b | `days_deferred` tracking | `_score_task()` formula correct but `days_deferred` never increments in practice | pawpal_system.py |

### Future Enhancements (stretch goals)

| # | Enhancement | Description | File(s) |
|---|-------------|-------------|---------|
| 13 | Reward system | Tie task completion into `RewardSystem` — points, streaks, badges | app.py, pawpal_system.py |
| 14 | Persistence (SQLite) | Replace in-memory session state with database storage | pawpal_system.py |
| 15 | Template vs Instance | Task template/instance split for proper cross-day lifecycle (Phase 2) | pawpal_system.py |
| 16 | Toast positioning | `st.toast()` always renders top-right; availability error toast should appear near the slot component for context — Streamlit limitation, requires custom CSS or inline approach | app.py |

---

## Testing
- **75 unit tests passing** (`python -m pytest`) — 58 original + 17 regression tests
- Manual walkthrough of each bug fix via live Streamlit server
- Regression test class: `TestBugFixRegressions` covers BUG #17, #11, #10, #8, #5, #3

---

## CURRENT UNRESOLVED / IN-PROGRESS BUGS (ACTIONABLE)
These issues remain after the micro-optimization work and should be prioritized before merging major refactors.

1. Availability snapshot fragility (HIGH)
   - Symptom: regenerate_plan_system reacts to availability edits on other days; snapshot comparison fails when TimeWindow.day_of_week formats differ (int vs string) or timezone/format mismatches.
   - Impact: regenerating after editing a different day's availability incorrectly alters today's plan.
   - Next step: canonicalize day representation, store per-day availability snapshots, and compare only the plan's date snapshot.

2. Regenerate can wipe completed task progress (HIGH)
   - Symptom: regenerate returns new Task instances, losing completed/skipped state from the previous plan.
   - Impact: users lose progress; tests sometimes fail.
   - Next step: adopt Template vs Instance model or ensure plan-local TaskInstance copies preserve status and task templates are immutable.

3. Over-scheduling safety net needed (MEDIUM)
   - Symptom: scheduler can place more active minutes than available (safety trimming exists but is a band-aid).
   - Impact: incorrect plans; inconsistent UI counts.
   - Next step: implement per-window placement (fill windows individually) in Scheduler.generate_plan and make trimming unnecessary.

4. copy module shadowing & import issues (MEDIUM)
   - Symptom: local symbols named `copy` or `_copy` shadow stdlib `copy`, causing AttributeError.
   - Impact: runtime failures in regenerate logic.
   - Next step: search/rename local symbols; use `import copy as _copy` and consistent `_copy.copy(...)` or prefer deep copy when needed.

5. Shallow vs deep copy semantics (MEDIUM)
   - Symptom: restored tasks use shallow copies; nested mutable fields (if present) can leak/ mutate templates.
   - Impact: subtle cross-plan mutation bugs.
   - Next step: decide on deep-copying restored instances or refactor to template/instance separation.

6. Test/fixture divergence (LOW)
   - Symptom: temporary fixtures added to validate optimizations conflict with canonical fixtures in the suite.
   - Impact: CI noise and future test brittleness.
   - Next step: reconcile and restore original fixtures; put opt-in fixtures into test modules scoped to the PR.

7. UI gating / regenerate UX (LOW → MEDIUM)
   - Symptom: "Generate Plan" visible in ACCEPTED state; regenerate lacks clear preview and day-targeting.
   - Impact: users can unintentionally overwrite accepted plans.
   - Next step: add UI gate (disable generate when accepted), show regenerate preview diff, and require explicit target day for availability edits.

8. Logout/Session cleanup (LOW)
   - Symptom: logout doesn't fully clear application plan/session state.
   - Impact: cross-user data leakage.
   - Next step: ensure session state keys are cleared and app reloads cleanly.

---

## Recommended next PRs (safe order)
1. fix/availability-snapshot — normalize days, per-day snapshot, unit tests for regenerate ignore unrelated-day edits.
2. feat/window-placement — per-window placement algorithm and tests (removes trimming).
3. refactor/template-instance — split TaskTemplate/TaskInstance, migrate tests, ensure status persistence.
4. ui/polish — disable generate in ACCEPTED, regenerate preview, toast improvements, task edit/delete.

---
