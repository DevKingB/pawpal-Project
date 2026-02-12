# PawPal+ System Architecture & Design

This document captures the full system design process — core concepts, tradeoff discussions, decisions made, and the finalized architecture — prior to implementation.

---

## 1. Core User Actions

1. **Add a pet care task** – Create a care task (walk, feeding, medication, grooming) with duration and priority so the system knows what needs to get done.
2. **Generate a daily care plan** – Produce an optimized schedule based on time-window availability, task priority, and preferences, with per-task reasoning for why things were ordered that way.
3. **Enter pet and owner information** – Input owner details (name, availability windows) and pet details (name, category, special needs) so the planner personalizes recommendations.
4. **Authenticate / manage account** – Register and log in with secure credentials so pet profiles, history, and schedules persist across sessions.

---

## 2. Pet Category System

Different pet types have distinct care needs. The system supports pet categories as an **enum** (not a full class) since species are static and breed-level differences rarely change *what* care is needed — only the specifics, which are captured in each Pet's `special_needs` and `health_notes` fields.

**Supported categories:** Dog, Cat, Spider, Reptile, Fish, Bird (expandable).

Each category carries **default task templates** that auto-populate when a new pet is created:
- **Dogs** — walks, outdoor exercise, socialization, grooming.
- **Cats** — litter box maintenance, indoor enrichment, scratching/play sessions.
- **Spiders/Reptiles** — habitat temperature/humidity checks, specialized feeding schedules (e.g., weekly).
- **Fish** — tank water quality checks, feeding, filter maintenance.
- **Birds** — cage cleaning, social interaction time, flight/exercise time.

**Why enum over class:** An enum is simpler and sufficient. Users aren't inventing new species. If we ever need sub-categories (dog breeds), we can extend later. The individual Pet object's `special_needs` field handles anything breed- or individual-specific.

---

## 3. Multi-Pet Support

A user's account can hold **multiple pets**, including multiple pets of the **same type** (e.g., two dogs, three cats). Each pet is an individual profile with its own name, age, health notes, and task list.

**MVP scope:** Start with one pet per account to keep the initial build simple.
**Future scope:** One-to-many relationship (one owner → many pets) with a dashboard to add, view, and switch between pet profiles.

### Design Tradeoff: Per-Individual vs. Per-Category Tracking

| Approach | Pros | Cons |
|---|---|---|
| **Per-individual tracking** | Accurate — each pet has its own schedule and history. "Dog A" and "Dog B" can have completely different meds/walk durations. | More items for the user to manage. |
| **Per-category tracking** | Simpler — one "Dogs" tracker covers all dogs. | Falls apart when individual pets differ (different meds, surgery recovery, etc.). |

**Decision: Per-individual tracking.** Category defaults *bootstrap* a new pet's task list, but once created, each pet's tasks are independent.

---

## 4. User Availability Model

The scheduler requires **structured time-window availability**, not a single "minutes available" number. A user free 8am–9am and 6pm–8pm has two distinct blocks with different practical uses.

- Availability = **list of time windows per day**
  - Example: `monday: [{start: "08:00", end: "09:00"}, {start: "18:00", end: "20:00"}]`
- Different days can have different windows (weekday vs. weekend).
- Uses local time via Python's `datetime.now()` — no timezone API for MVP.
- User can update availability for a specific day and regenerate the plan on demand.

### Scheduling Conflict Resolution

When multiple pets have tasks competing for the same time windows, the Scheduler resolves via:

1. **Hard constraints first** — Tasks with specific required times are placed first (e.g., medication at 8am sharp).
2. **Time-sensitive tasks next** — Tasks with preferred windows get slotted into their ideal blocks (morning feeds → morning window).
3. **Fill remaining time by priority** — High-priority tasks get remaining slots before medium/low.
4. **Overflow handling** — If tasks don't fit, the Scheduler reports what was cut and why so the user can adjust.

**Future consideration (not MVP):**
- **Task batching** — Feeding cat + dog in the same window takes less time than the sum of both tasks individually. Would require an `is_batchable` flag on tasks.
- **Task dependencies** — "Don't walk the dog right after feeding." Would require a `depends_on` relationship. For MVP, the user handles this during the edit/review step.
- **Multi-occurrence per day** — "Feed the dog morning AND evening." Would require `times_per_day` + `preferred_times` attributes. MVP supports one occurrence per task per day.

---

## 5. DailyPlan Flow

### Unified Plan Model

The scheduler produces a **single DailyPlan per user per day** that combines tasks from **all** pets. Tasks from different pets are interleaved by priority score, not grouped by pet. For example, a user with a dog and a cat gets one plan:

```
8:00 — Feed Rex (dog, 10 min, HIGH)
8:10 — Feed Whiskers (cat, 10 min, HIGH)
8:20 — Walk Rex (dog, 30 min, HIGH)
8:50 — Clean litter box (cat, 10 min, HIGH)
9:00 — Play with Whiskers (cat, 15 min, MEDIUM)
```

**Why unified over per-pet plans:**

| Approach | Pros | Cons |
|---|---|---|
| **One plan, all pets** | Optimizes globally — highest priority task goes first regardless of pet. Simpler for user to follow one timeline. | Tasks from different pets are mixed together. |
| **Separate plan per pet** | Clear per-pet view. | Can't optimize across pets. User juggles multiple schedules. Two HIGH tasks from different pets might conflict with no resolution. |

**Decision: Unified plan.** The scheduler's job is to optimize the *user's time*, not individual pets' schedules. The UI can filter by `pet_id` if a per-pet view is wanted:
```python
rex_tasks = [t for t in plan.scheduled_tasks if t.pet_id == rex.pet_id]
```

### Scheduler Decoupling from User

The `Scheduler.generate_plan()` method accepts `pets: list[Pet]` and `availability: list[TimeWindow]` as raw inputs rather than a `User` object. This was an intentional design change:

- **Testability** — Tests can pass pets and windows directly without constructing a full User with credentials, email, etc.
- **Reusability** — The scheduler could work for any source of tasks, not just User-owned pets.
- **Separation of concerns** — The Scheduler's job is "fit tasks into time." It doesn't need to know about authentication, usernames, or emails.

The tradeoff is that `DailyPlan.owner` receives a placeholder User (`user_id=0, username="system"`). The real owner is assigned by the application layer when connecting the plan to the logged-in user.

### Plan Lifecycle

The schedule is a **guide, not a lock.** The user always retains freedom to deviate.

1. **Generate** — User hits "Plan My Day." Scheduler pulls all recurring + one-off tasks across all pets, fits them into available time windows, produces a **draft** with per-task reasoning.
2. **Review** — Plan is presented as a draft with ordered tasks, time slots, and explanations.
3. **Accept / Edit / Regenerate:**
   - Accept as-is → plan locks in, reminders activate.
   - Edit → add/remove/reorder tasks, insert custom one-off tasks (e.g., vet appointment). Then accept.
   - Regenerate → change availability constraints and get a new draft.
4. **Execute** — Mark any task complete at any time (earlier or later than scheduled).
5. **Regenerate mid-day** — If availability changes significantly, regenerate for remaining incomplete tasks only. Already-completed tasks stay done.

**DailyPlan status lifecycle:** `draft` → `accepted` → `in_progress` → `completed`

---

## 6. Deferred Task Handling

When tasks are not completed by end of day:

| Priority | Task Type | Behavior |
|---|---|---|
| **High / Medium** | **Recurring** (daily/weekly) | **Do not carry over.** The miss is logged (happiness penalty, broken streak), but tomorrow already has a fresh auto-generated instance. No duplication. |
| **High / Medium** | **One-off** | **Carry over** to tomorrow's plan with a priority boost. These won't auto-regenerate, so they'd be lost otherwise. Multi-day deferrals trigger escalation warnings (e.g., "Flea medication deferred 2 days — needs immediate attention"). |
| **Low** | **Recurring** (daily/weekly) | The missed *instance* moves to **Backlog** and decays over 3 days (50% → 25% → cleared). However, the task itself **auto-regenerates** on its next scheduled cycle — the user doesn't lose the task permanently, just that specific occurrence's reward points. |
| **Low** | **One-off** | Moves to **Backlog**. If not completed within 3 days, it is **cleared entirely**. The user must manually re-add it if they still want it. This is intentional — if users forget about a low-priority one-off, it's on them. |

**Key distinction:** "Cleared after 3 days" means the *backlog entry* is removed, not that a recurring task stops existing. Recurring tasks always produce a fresh instance on their next frequency cycle regardless of whether the previous one was completed.

This split eliminates duplication: recurring tasks always exist exactly once per scheduled day, and one-off tasks persist until completed or escalated.

Each task tracks `days_deferred` so the Scheduler factors overdue status into weighted scoring.

---

## 7. Reward & Reminder System (Stretch Goal)

### Reward Tiers Based on Completion Timing

| Completion Timing | Reward | Reasoning |
|---|---|---|
| **On-time** (within scheduled window) | 100% points | Full reward — followed the plan |
| **Same-day late** (done today, off-schedule) | 75% points | Still got it done today |
| **Backlog Day 1** (1 day after deferral) | 50% points | Still recent — worth catching up |
| **Backlog Day 2** (critical day) | 25% points | Last meaningful incentive |
| **Backlog Day 3+** | 0 points — **cleared from backlog** | Task is removed entirely |
| **Missed entirely** (never completed) | 0 points + happiness penalty | Negative feedback triggers |

**Backlog decay window: 3 days total.** Day 1 in backlog earns 50%, day 2 earns 25%, and on day 3 the task is cleared from the backlog entirely. This keeps the backlog lean, prevents it from becoming a stale graveyard, and gives a tight but fair window to catch up. For recurring tasks (e.g., weekly grooming), clearing doesn't matter — the task regenerates on its next frequency cycle. For one-off tasks, the user can re-add manually if still needed. An "expired archive" could be added in the future if users want visibility into cleared items.

### Additional Reward Mechanics
- **Streaks** — e.g., "5-day feeding streak!" tracked per task type.
- **Badges** — milestone awards for consistent care.
- **Pet happiness score** — rises with on-time completions, drops with missed tasks.

### Reminders
- Notification X minutes before a scheduled task.
- Second notification when the task is due.
- Gentle negative feedback if task goes overdue (e.g., "Your pet is getting hungry — try to complete this soon!").

### Feedback Animations

**MVP:** One generic positive response for task completion (e.g., celebration animation + "Great job!") and one generic negative response for missed tasks (e.g., sad pet graphic + "Your pet missed this — try to catch up!"). Simple, consistent, low effort to implement.

**Future:** Custom feedback tailored to the task and pet category using the static data we already have. For example:
- Completing a dog walk → "Rex loved that walk! 🐕" (uses pet name + category context)
- Missing a fish feeding → "Your fish haven't eaten — they're getting hungry!" (species-specific language)
- User-created custom tasks → fall back to generic responses since we have no contextual data for arbitrary tasks.

### Honor System Tradeoff
We cannot verify the user actually performed a task. This is trust-based (same as Duolingo). If users game it, they only hurt their pet. Future mitigation: optional photo verification or smart device integrations — well beyond MVP.

---

## 8. Data Persistence

| Option | MVP? | Notes |
|---|---|---|
| **SQLite** | **Yes** | Built into Python, zero-setup, file-based. Handles relational structure (User → Pet → Task). Single-user Streamlit app makes concurrency irrelevant. |
| **PostgreSQL / MySQL** | Future | For multi-user deployed version. SQL schema migrates cleanly from SQLite. |
| **MongoDB** | Not recommended | Flexible schema is nice but requires rethinking the relational data model. |

**Authentication:** `username` + `password_hash` (via `bcrypt` or `hashlib`) stored in SQLite.

---

## 9. Finalized Object Designs

### 1. User
- **Attributes:** `user_id`, `username`, `email`, `password_hash`, `availability` (list of time windows per day), `pets` (list of Pet objects)
- **Methods:** `add_pet()`, `remove_pet()`, `get_pets()`, `authenticate()`, `get_total_task_load()`, `update_availability()`

### 2. Pet
- **Attributes:** `pet_id`, `name`, `category` (PetCategory enum), `age`, `weight`, `health_notes`, `special_needs`, `tasks` (list of Task objects)
- **Methods:** `add_task()`, `remove_task()`, `get_tasks()`, `get_profile_summary()`

### 3. PetCategory (Enum)
- **Values:** DOG, CAT, SPIDER, REPTILE, FISH, BIRD (expandable)
- **Associated data per value:** `default_tasks` (template list), `care_guidelines` (species tips)
- **Methods:** `get_default_tasks()`, `get_care_tips()`

### 4. Task
- **Attributes:** `task_id`, `name`, `description`, `duration` (minutes), `priority` (high/medium/low), `frequency` (once, daily, weekly), `status` (pending, completed, missed, skipped), `scheduled_time`, `pet_id`, `days_deferred` (overdue counter), `preferred_times` (optional preferred time-of-day slots)
- **Methods:** `mark_complete()`, `mark_missed()`, `is_overdue()`, `reset()` (for recurring tasks)

### 5. Scheduler
- **Attributes:** `constraints` (availability windows, preferences), `tasks` (pool to schedule)
- **Algorithm:** Weighted scoring + greedy time-window placement. Composite score = priority weight × overdue days × time-sensitivity. Sorted by score, greedily placed in best-fit window.
- **Methods:** `generate_plan(pets, availability)` → DailyPlan (draft), `prioritize_tasks()`, `resolve_conflicts()` (reports what was cut and why)

### 6. DailyPlan
- **Attributes:** `date`, `owner` (User ref), `scheduled_tasks` (ordered + time-slotted), `deferred_tasks` (didn't fit), `backlog` (low-priority deferred), `total_duration`, `explanation` (per-task reasoning), `status` (draft/accepted/in_progress/completed)
- **Methods:** `accept()`, `add_task()`, `remove_task()`, `reorder_tasks()`, `regenerate(new_availability)`, `get_next_task()`, `get_completion_percentage()`

### 7. RewardSystem (Stretch Goal)
- **Attributes:** `streaks` (per task type), `badges`, `happiness_score` (per pet), `total_points`
- **Methods:** `award_completion(task, timing_tier)`, `penalize_miss(task)`, `get_streak()`, `get_happiness()`

### 8. Reminder (Stretch Goal)
- **Attributes:** `task_reference`, `remind_before_minutes`, `message`
- **Methods:** `send_reminder()`, `check_overdue()`

---

## 10. Key Relationships

```
User ──(1 to many)──► Pet
Pet  ──(many to 1)──► PetCategory (enum)
Pet  ──(1 to many)──► Task
Scheduler ──(uses)──► Tasks + Availability → produces DailyPlan
DailyPlan ──(contains)──► scheduled Tasks + deferred Tasks
RewardSystem ──(observes)──► Task completions/misses
Reminder ──(references)──► Task
```

---

## 11. Finalized Design Decisions

| Decision | Resolution | Scope |
|---|---|---|
| PetCategory | Enum with default task templates | MVP |
| Multi-pet | Per-individual tracking; start with one, scale to many | MVP: 1 pet; Future: many |
| Authentication | Real login, hashed passwords, SQLite | MVP |
| Availability | Time-window based (list of start/end blocks per day) | MVP |
| Task recurrence | `frequency` field + auto-regeneration in plans | MVP |
| Multi-occurrence/day | Multiple occurrences of same task within a day | Future |
| Task batching | Batch compatible tasks across pets in same window | Future |
| Task dependencies | User handles via manual edit/review | Future |
| DailyPlan flow | Generate draft → Review → Accept/Edit/Regenerate | MVP |
| Deferred (high/med recurring) | Log the miss, no carry-over (next day auto-generates fresh instance) | MVP |
| Deferred (high/med one-off) | Auto-carry with priority boost + escalation warnings | MVP |
| Deferred (low) | Backlog with 3-day decay (50% → 25% → cleared) | MVP |
| Scheduler algorithm | Weighted scoring + greedy time-window placement | MVP |
| Database | SQLite for local persistence | MVP |
| Reward/Reminder | Tiered points, happiness score, reminders | Stretch Goal |
| Honor system | Trust-based; future: photo verification | Known limitation |
| Time handling | Local time via `datetime.now()` | MVP |
| Feedback animations | Generic positive/negative responses | MVP |
| Custom feedback | Tailored responses using pet name + category context | Future |

---

## 12. Design Gap: Cross-Day Task Lifecycle (TODO)

### Problem Statement

Sections 5 and 6 describe a rich cross-day task lifecycle — deferred tasks carry over with priority boosts, `days_deferred` increments to boost scoring, backlog items decay over 3 days, and the scheduler prevents recurring task duplication. **The current implementation does not wire any of this up.**

### What the Design Says vs. What the Code Does

| Design Intent (Sections 5–7) | Current Implementation | Gap |
|---|---|---|
| `days_deferred` increments when a task is missed, boosting its score next generation | `days_deferred` is never incremented outside of `mark_missed()`, which is never called by the app | **No cross-day scoring boost** |
| High/Med one-off deferred tasks carry over to tomorrow | Scheduler pulls fresh from Pet.tasks each time — no carry-over logic; deferred list is display-only | **Deferred list is informational, not functional** |
| High/Med recurring missed tasks log the miss but don't duplicate (fresh instance auto-generates) | No end-of-day process to mark tasks MISSED; no auto-regeneration of recurring task instances | **No end-of-day lifecycle** |
| Low-priority backlog decays over 3 days (50% → 25% → cleared) | Backlog list is display-only; no day-tracking, no decay, no clearing | **Backlog decay not implemented** |
| Duplicate prevention: recurring tasks exist exactly once per scheduled day | Scheduler collects all Pet.tasks including already-scheduled ones; no instance management | **No task instance vs. task template distinction** |

### Root Cause

The current architecture uses **persistent Task objects on Pet** as both the task *template* (definition) and the task *instance* (today's scheduled occurrence). The design in Section 6 implicitly assumes a **template → instance** model where:

- The **template** lives on Pet forever (e.g., "Walk — daily, 30min, high")
- Each plan generation creates a fresh **instance** for today
- Instances track their own status (PENDING → COMPLETED / MISSED / SKIPPED)
- `days_deferred` lives on the template to influence future instance scoring
- Recurring templates auto-generate new instances on their frequency cycle

Without this split, there's no way to:
1. Mark yesterday's *instance* as MISSED without corrupting the *template*
2. Prevent the same template from producing duplicate instances in tomorrow's plan
3. Track backlog decay (which day is this instance on?)
4. Reset task status for a new day while preserving the accumulated `days_deferred`

---

### Finalized Cross-Day Lifecycle Rules

#### Task End-State Definitions

| End State | How it happens | User's fault? |
|---|---|---|
| **COMPLETED** | User clicked Done | N/A (good) |
| **SKIPPED** | User clicked "Skip — not today" | No — intentional |
| **MISSED** | Scheduled but user never acted by end-of-day | Yes — forgot/neglected |
| **DEFERRED** | Scheduler couldn't fit it (med/high priority) | No — system limitation |
| **BACKLOG** | Scheduler couldn't fit it (low priority) | No — system limitation |

#### `days_deferred` Rules

| End State | Increment `days_deferred`? | Reasoning |
|---|---|---|
| **COMPLETED** | Reset to 0 | Done. Clean slate. |
| **SKIPPED** | No change | User acknowledged it. No penalty, no boost. Intentional defer. |
| **MISSED** | +1 | User failed to act. Task needs to bubble up tomorrow so it doesn't keep getting ignored. |
| **DEFERRED** (scheduler) | No change | Not user's fault — system capacity limitation. Task re-evaluated tomorrow at same priority. |
| **BACKLOG** (scheduler) | No change | Same as deferred — system decision, not user's. |

**Scheduler-deferred escalation:** If the same task is deferred by the scheduler for 3+ consecutive plan generations, surface an alert: *"'Flea medication' has been unable to fit in your schedule for 3 days. Consider adjusting your availability or removing lower-priority tasks."* This keeps scoring clean while surfacing capacity problems to the user.

#### Cross-Day Carry-Over Matrix

| Yesterday's State | Task Type | Tomorrow's Behavior | Penalty? |
|---|---|---|---|
| **COMPLETED** | Recurring | Fresh instance auto-generated on next cycle | None |
| **COMPLETED** | One-off | Task is done. Remove from Pet or mark permanently complete. | None |
| **SKIPPED** | Recurring | Fresh instance on next cycle. Skipped instance disappears. | None |
| **SKIPPED** | One-off | Stays in pool, re-evaluated by scheduler. **7-day TTL** — cleared after 7 days of being skipped. User must re-add manually if still wanted. | None |
| **MISSED** | Recurring (high/med) | Miss logged (happiness penalty, broken streak). Fresh instance auto-generates. No carry-over (prevents duplication). | Yes — penalty + streak break |
| **MISSED** | Recurring (low) | Instance moves to backlog with 3-day decay. Fresh instance still auto-generates on next cycle. | Yes — penalty |
| **MISSED** | One-off (high/med) | Carries over with priority boost (`days_deferred` +1). Escalation warning if multi-day. | Yes — penalty + streak break |
| **MISSED** | One-off (low) | Moves to backlog. Cleared after 3 days if not completed. | Yes — penalty |
| **DEFERRED** | Any | Same carry-over rules as MISSED but **without any penalty**. No happiness hit, no broken streak. Just re-evaluated tomorrow. | None |

#### Backlog Decay (unchanged from Section 7)

| Day in Backlog | Reward if Completed | Notes |
|---|---|---|
| Day 1 | 50% points | Still recent — worth catching up |
| Day 2 | 25% points | Last meaningful incentive |
| Day 3 | 0% — cleared from backlog | Entry removed. Recurring tasks still auto-regenerate on next cycle. |

#### Double-Dip Ruling

When a recurring task is MISSED and a fresh instance is generated, both the backlog entry (decaying points) and the fresh instance (full points) exist simultaneously. The user can complete both and earn points from each. **This is allowed for MVP.**

Rationale:
- The user DID miss Monday — the happiness penalty and broken streak already happened. The backlog recovery is a consolation prize, not a bonus.
- The user DID complete Tuesday — that's a legitimate full-value completion.
- The exploit is self-limiting: backlog decays over 3 days (50% → 25% → 0%). Max theoretical double-dip is 150% → 125% → 100% over 3 days.
- Future optimization: auto-clear backlog copies of a template when its fresh instance is completed. One line of logic, not worth the complexity for MVP.

---

### Proposed Solution (TODO)

**Phase 1 — Minimal viable cross-day support (no data model changes):**
- On MISSED (end-of-day): call `task.mark_missed()` to increment `days_deferred`
- On Generate Plan: reset all task statuses to PENDING (new day = fresh start)
- On Skip: set status to SKIPPED, do NOT increment `days_deferred`
- Add 3+ consecutive deferral alert in plan UI
- Add 7-day TTL tracking for skipped one-off tasks
- This gives us working `days_deferred` boosting for missed tasks without restructuring

**Phase 2 — Full template/instance model (future, with SQLite):**
- Introduce `TaskTemplate` (lives on Pet) and `TaskInstance` (lives on DailyPlan)
- Scheduler creates instances from templates each generation
- Instances track per-day status; templates track `days_deferred` and frequency
- Backlog decay tracks instance age (day counter)
- End-of-day process: review plan, mark uncompleted instances as MISSED, update template `days_deferred`
- Auto-clear backlog copies when fresh instance is completed (eliminates double-dip)

Phase 1 is achievable without restructuring the data model. Phase 2 requires the template/instance split and likely coincides with SQLite persistence.
