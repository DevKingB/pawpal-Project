"""
PawPal+ Logic Layer
====================
Backend classes for the PawPal+ pet care scheduling app.
All core objects, enums, and data structures live here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum
from typing import Optional


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class PetCategory(Enum):
    """Supported pet species. Each value maps to default tasks and care tips."""

    DOG = "dog"
    CAT = "cat"
    SPIDER = "spider"
    REPTILE = "reptile"
    FISH = "fish"
    BIRD = "bird"

    def get_default_tasks(self) -> list[dict]:
        """Return a list of template task dicts for this species."""
        defaults = {
            "dog": [
                {"name": "Walk", "duration": 30, "priority": "high", "frequency": "daily"},
                {"name": "Feed", "duration": 10, "priority": "high", "frequency": "daily"},
                {"name": "Groom", "duration": 20, "priority": "medium", "frequency": "weekly"},
            ],
            "cat": [
                {"name": "Feed", "duration": 10, "priority": "high", "frequency": "daily"},
                {"name": "Clean litter box", "duration": 10, "priority": "high", "frequency": "daily"},
                {"name": "Play session", "duration": 15, "priority": "medium", "frequency": "daily"},
            ],
            "spider": [
                {"name": "Feed", "duration": 5, "priority": "high", "frequency": "weekly"},
                {"name": "Mist enclosure", "duration": 5, "priority": "medium", "frequency": "daily"},
            ],
            "reptile": [
                {"name": "Feed", "duration": 10, "priority": "high", "frequency": "daily"},
                {"name": "Check temperature", "duration": 5, "priority": "high", "frequency": "daily"},
                {"name": "Clean enclosure", "duration": 20, "priority": "medium", "frequency": "weekly"},
            ],
            "fish": [
                {"name": "Feed", "duration": 5, "priority": "high", "frequency": "daily"},
                {"name": "Check water quality", "duration": 10, "priority": "high", "frequency": "weekly"},
                {"name": "Clean tank", "duration": 30, "priority": "medium", "frequency": "weekly"},
            ],
            "bird": [
                {"name": "Feed", "duration": 10, "priority": "high", "frequency": "daily"},
                {"name": "Clean cage", "duration": 15, "priority": "medium", "frequency": "daily"},
                {"name": "Social time", "duration": 20, "priority": "medium", "frequency": "daily"},
            ],
        }
        return defaults.get(self.value, [])

    def get_care_tips(self) -> str:
        """Return species-specific care guidelines as a string."""
        tips = {
            "dog": "Dogs need daily walks, consistent feeding schedules, and regular vet checkups. Socialize early and often.",
            "cat": "Cats need clean litter boxes, fresh water, and vertical spaces to climb. Schedule regular play sessions.",
            "spider": "Maintain proper humidity in the enclosure. Feed appropriately sized prey. Avoid handling during molting.",
            "reptile": "Monitor temperature and humidity closely. Provide UVB lighting. Research species-specific diet needs.",
            "fish": "Test water parameters weekly. Avoid overfeeding. Perform partial water changes regularly.",
            "bird": "Birds need daily social interaction. Keep cages clean and provide foraging toys for mental stimulation.",
        }
        return tips.get(self.value, "No tips available for this category.")


class Priority(Enum):
    """Task priority levels used for scheduling weight."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Frequency(Enum):
    """How often a task recurs."""

    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


class TaskStatus(Enum):
    """Lifecycle states of a task instance."""

    PENDING = "pending"
    COMPLETED = "completed"
    MISSED = "missed"
    SKIPPED = "skipped"


class PlanStatus(Enum):
    """Lifecycle states of a daily plan."""

    DRAFT = "draft"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# ──────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────

@dataclass
class TimeWindow:
    """A single block of available time (e.g., 08:00–09:00)."""
    day_of_week: str
    start: time
    end: time

    def get_duration_minutes(self) -> int:
        """Return the length of this window in minutes."""
        start_minutes = self.start.hour * 60 + self.start.minute
        end_minutes = self.end.hour * 60 + self.end.minute
        return end_minutes - start_minutes


@dataclass
class Task:
    """A single pet care task (e.g., 'Walk the dog – 30 min, high priority')."""

    task_id: int
    name: str
    description: str
    duration: int  # minutes
    priority: Priority
    frequency: Frequency
    pet_id: int
    status: TaskStatus = TaskStatus.PENDING
    scheduled_time: Optional[datetime] = None
    days_deferred: int = 0
    preferred_times: list[str] = field(default_factory=list)

    def mark_complete(self) -> None:
        """Set status to COMPLETED."""
        self.status = TaskStatus.COMPLETED

    def mark_missed(self) -> None:
        """Set status to MISSED and increment days_deferred."""
        # TODO #12b: This method exists but is never called by app.py.
        # Needs an end-of-day trigger (button or automatic) to mark
        # uncompleted scheduled tasks as MISSED. Only MISSED increments
        # days_deferred — SKIPPED and DEFERRED do not (Section 12 rules).
        self.status = TaskStatus.MISSED
        self.days_deferred += 1

    def is_overdue(self) -> bool:
        """Return True if the task is past its scheduled time and still pending."""
        if self.status != TaskStatus.PENDING:
            return False
        if self.scheduled_time is None:
            return False
        return datetime.now() > self.scheduled_time 

    def reset(self) -> None:
        """Reset status to PENDING for the next recurrence cycle."""
        # TODO #12a: Currently only called manually. Needs to be wired into
        # plan generation so tasks start fresh each day. Also need 7-day TTL
        # tracking for skipped one-off tasks (Section 12 rules).
        self.status = TaskStatus.PENDING
        self.days_deferred = 0

@dataclass
class Pet:
    """An individual pet profile with its own task list."""

    pet_id: int
    name: str
    category: PetCategory
    age: int
    weight: float
    health_notes: str = ""
    special_needs: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task_id: int) -> None:
        """Remove a task by its ID."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        return self.tasks

    def get_profile_summary(self) -> str:
        """Return a human-readable summary of this pet's info and pending tasks."""
        pending = [t for t in self.tasks if t.status == TaskStatus.PENDING]
        summary = (
            f"{self.name} ({self.category.value}) \u2014 Age: {self.age}, "
            f"Weight: {self.weight}kg\n"
            f"Pending tasks: {len(pending)}"
        )
        if self.health_notes:
            summary += f"\nHealth notes: {self.health_notes}"
        if self.special_needs:
            summary += f"\nSpecial needs: {self.special_needs}"
        return summary

@dataclass
class User:
    """A registered pet owner with login credentials and availability."""

    user_id: int
    username: str
    email: str
    password_hash: str
    availability: dict[str, list[TimeWindow]] = field(default_factory=dict)
    # availability format: {"monday": [TimeWindow(...), ...], "tuesday": [...], ...}
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the user's profile."""
        self.pets.append(pet)

    def remove_pet(self, pet_id: int) -> None:
        """Remove a pet by its ID."""
        self.pets = [p for p in self.pets if p.pet_id != pet_id]

    def get_pets(self) -> list[Pet]:
        """Return all pets belonging to this user."""
        return self.pets

    def authenticate(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        # MVP: simple hash comparison. Future: use bcrypt.
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() == self.password_hash

    def get_total_task_load(self) -> int:
        """Return total duration (minutes) of all pending tasks across all pets."""
        total = 0
        for pet in self.pets:
            for task in pet.tasks:
                if task.status == TaskStatus.PENDING:
                    total += task.duration
        return total

    def update_availability(self, day: str, windows: list[TimeWindow]) -> None:
        """Replace the availability windows for a specific day."""
        self.availability[day] = windows


# ──────────────────────────────────────────────
# Core Logic Classes
# ──────────────────────────────────────────────

@dataclass
class DailyPlan:
    """The output of the Scheduler — an ordered, time-slotted plan for one day."""

    date: date
    owner: User
    scheduled_tasks: list[Task] = field(default_factory=list)
    deferred_tasks: list[Task] = field(default_factory=list)
    backlog: list[Task] = field(default_factory=list)
    total_duration: int = 0
    explanation: dict[int, str] = field(default_factory=dict)
    # explanation format: {task_id: "reason this task was placed here"}
    status: PlanStatus = PlanStatus.DRAFT

    def accept(self) -> None:
        """Promote the plan from DRAFT to ACCEPTED."""
        self.status = PlanStatus.ACCEPTED

    def add_task(self, task: Task) -> None:
        """Manually insert a task into the plan (user edit)."""
        self.scheduled_tasks.append(task)
        self.total_duration += task.duration

    def remove_task(self, task_id: int) -> None:
        """Remove a task from the plan (user edit)."""
        for task in self.scheduled_tasks:
            if task.task_id == task_id:
                self.total_duration -= task.duration
                break
        self.scheduled_tasks = [t for t in self.scheduled_tasks if t.task_id != task_id]

    def reorder_tasks(self, new_order: list[int]) -> None:
        """Rearrange scheduled_tasks by a list of task IDs in desired order."""
        task_map = {t.task_id: t for t in self.scheduled_tasks}
        self.scheduled_tasks = [task_map[tid] for tid in new_order if tid in task_map]

    # def regenerate(self, new_availability: list[TimeWindow]) -> DailyPlan:
    #     """Re-run the Scheduler on remaining incomplete tasks with updated windows."""
    #     # TODO: implement — delegate to Scheduler
    #     pass

    def get_next_task(self) -> Optional[Task]:
        """Return the next pending task in the schedule."""
        for task in self.scheduled_tasks:
            if task.status == TaskStatus.PENDING:
                return task
        return None

    def get_completion_percentage(self) -> float:
        """Return the percentage of scheduled tasks that are completed."""
        if not self.scheduled_tasks:
            return 0.0
        completed = sum(1 for t in self.scheduled_tasks if t.status == TaskStatus.COMPLETED)
        return (completed / len(self.scheduled_tasks)) * 100.0


class Scheduler:
    """
    The scheduling engine.

    Algorithm: Weighted scoring + greedy time-window placement.
    Composite score = priority_weight × (1 + days_deferred) × time_sensitivity.
    Tasks are sorted by score descending, then greedily placed in the best-fit window.
    """

    def __init__(self) -> None:
        self.constraints: list[TimeWindow] = []
        self.tasks: list[Task] = []

    def generate_plan(self, pets: list[Pet], availability: list[TimeWindow]) -> DailyPlan:
        """
        Build a DailyPlan (draft) from all pets' tasks fitted into availability windows.

        Steps:
        1. Collect all pending tasks across pets.
        2. Score and rank tasks via prioritize_tasks().
        3. Greedily place tasks into time windows.
        4. Tasks that don't fit go to deferred_tasks or backlog.
        5. Return a DailyPlan with per-task explanations.
        """
        # 1. Collect all pending tasks across all pets
        self.tasks = []
        for pet in pets:
            for task in pet.tasks:
                if task.status == TaskStatus.PENDING:
                    self.tasks.append(task)

        self.constraints = availability

        # 2. Calculate total available minutes
        total_available = sum(w.get_duration_minutes() for w in availability)

        # 3. Score and sort tasks (highest priority first)
        ranked = self.prioritize_tasks()

        # 4. Greedily place tasks into available time
        scheduled = []
        deferred = []
        backlog = []
        explanation = {}
        time_used = 0

        for task in ranked:
            if time_used + task.duration <= total_available:
                scheduled.append(task)
                explanation[task.task_id] = (
                    f"Scheduled: priority={task.priority.value}, "
                    f"score={self._score_task(task):.1f}, "
                    f"duration={task.duration}min"
                )
                time_used += task.duration
            else:
                # Doesn't fit — route by priority
                # TODO #12a: Deferred/backlog lists are display-only.
                # Per Section 12 finalized rules:
                #   - Do NOT increment days_deferred here (not user's fault)
                #   - Track consecutive deferral count per task
                #   - Alert user if same task deferred 3+ consecutive gens
                #   - Carry-over follows same matrix as MISSED but no penalty
                if task.priority == Priority.LOW:
                    backlog.append(task)
                else:
                    deferred.append(task)

        # 5. Build and return the DailyPlan
        owner = User(user_id=0, username="system", email="", password_hash="")
        return DailyPlan(
            date=date.today(),
            owner=owner,
            scheduled_tasks=scheduled,
            deferred_tasks=deferred,
            backlog=backlog,
            total_duration=time_used,
            explanation=explanation,
            status=PlanStatus.DRAFT,
        )

    def _score_task(self, task: Task) -> float:
        """Calculate the composite score for a single task."""
        # TODO #12a: days_deferred only increments on MISSED (not on
        # scheduler-deferred or skipped). Scoring formula is correct,
        # but the input (days_deferred) is never updated by the app yet.
        priority_weights = {
            Priority.HIGH: 3.0,
            Priority.MEDIUM: 2.0,
            Priority.LOW: 1.0,
        }
        weight = priority_weights[task.priority]
        return weight * (1 + task.days_deferred)

    def prioritize_tasks(self) -> list[Task]:
        """Score and sort tasks by weighted composite score (descending)."""
        return sorted(self.tasks, key=lambda t: self._score_task(t), reverse=True)

    def resolve_conflicts(self) -> list[Task]:
        """Identify tasks that don't fit and return them with reasons for deferral."""
        total_available = sum(w.get_duration_minutes() for w in self.constraints)
        ranked = self.prioritize_tasks()
        conflicts = []
        time_used = 0
        for task in ranked:
            if time_used + task.duration > total_available:
                conflicts.append(task)
            else:
                time_used += task.duration
        return conflicts


def regenerate_plan_system(
    scheduler: Scheduler,
    pets: Iterable[Pet],
    windows: Optional[Iterable[TimeWindow]],
    existing_plan: DailyPlan,
) -> Tuple[DailyPlan, str]:
    """
    Re-run scheduler but preserve completed/skipped task statuses.
    Returns (new_plan, summary_message).
    """
    pets_list: List[Pet] = list(pets or [])
    windows_list: List[TimeWindow] = list(windows or [])

    # Snapshot finished statuses from existing plan (scheduled + deferred + backlog)
    finished = {}
    existing_tasks = []
    if hasattr(existing_plan, "scheduled_tasks"):
        existing_tasks.extend(existing_plan.scheduled_tasks)
    if hasattr(existing_plan, "deferred_tasks"):
        existing_tasks.extend(existing_plan.deferred_tasks)
    if hasattr(existing_plan, "backlog"):
        existing_tasks.extend(existing_plan.backlog)
    for t in existing_tasks:
        if t.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED):
            finished[t.task_id] = t.status

    # Run scheduler
    new_plan = scheduler.generate_plan(pets_list, windows_list)

    # If some finished tasks were removed by the scheduler, restore them from the existing plan
    existing_map = {t.task_id: t for t in existing_tasks}
    # build set of task ids present in new_plan
    present_ids = set()
    if hasattr(new_plan, "scheduled_tasks"):
        present_ids.update(t.task_id for t in new_plan.scheduled_tasks)
    if hasattr(new_plan, "deferred_tasks"):
        present_ids.update(t.task_id for t in new_plan.deferred_tasks)
    if hasattr(new_plan, "backlog"):
        present_ids.update(t.task_id for t in new_plan.backlog)

    # For any finished task that isn't present, re-insert it into scheduled_tasks (preserve status)
    for tid, status in finished.items():
        if tid not in present_ids and tid in existing_map:
            restored = existing_map[tid]
            restored.status = status
            if not hasattr(new_plan, "scheduled_tasks"):
                new_plan.scheduled_tasks = []
            new_plan.scheduled_tasks.append(restored)
            present_ids.add(tid)

    # Restore finished statuses
    new_tasks = []
    if hasattr(new_plan, "scheduled_tasks"):
        new_tasks.extend(new_plan.scheduled_tasks)
    if hasattr(new_plan, "deferred_tasks"):
        new_tasks.extend(new_plan.deferred_tasks)
    if hasattr(new_plan, "backlog"):
        new_tasks.extend(new_plan.backlog)
    for t in new_tasks:
        if t.task_id in finished:
            t.status = finished[t.task_id]

    # Preserve original plan status
    new_plan.status = existing_plan.status

    old_ids = {t.task_id for t in existing_tasks}
    new_ids = {t.task_id for t in new_tasks}
    newly_added = new_ids - old_ids
    removed = old_ids - new_ids

    parts = []
    if newly_added:
        parts.append(f"{len(newly_added)} deferred task(s) now fit")
    if removed:
        parts.append(f"{len(removed)} task(s) no longer fit")
    if not parts:
        summary = "Plan re-evaluated — no changes needed."
    else:
        summary = "Plan updated — " + ", ".join(parts) + "."

    return new_plan, summary
