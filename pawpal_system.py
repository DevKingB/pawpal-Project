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
        # TODO: implement default task templates per category
        pass

    def get_care_tips(self) -> str:
        """Return species-specific care guidelines as a string."""
        # TODO: implement care tips per category
        pass


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

    start: time
    end: time

    def get_duration_minutes(self) -> int:
        """Return the length of this window in minutes."""
        # TODO: implement duration calculation
        pass


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
        # TODO: implement
        pass

    def mark_missed(self) -> None:
        """Set status to MISSED and increment days_deferred."""
        # TODO: implement
        pass

    def is_overdue(self) -> bool:
        """Return True if the task is past its scheduled time and still pending."""
        # TODO: implement
        pass

    def reset(self) -> None:
        """Reset status to PENDING for the next recurrence cycle."""
        # TODO: implement
        pass


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
        # TODO: implement
        pass

    def remove_task(self, task_id: int) -> None:
        """Remove a task by its ID."""
        # TODO: implement
        pass

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        # TODO: implement
        pass

    def get_profile_summary(self) -> str:
        """Return a human-readable summary of this pet's info and pending tasks."""
        # TODO: implement
        pass


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
        # TODO: implement
        pass

    def remove_pet(self, pet_id: int) -> None:
        """Remove a pet by its ID."""
        # TODO: implement
        pass

    def get_pets(self) -> list[Pet]:
        """Return all pets belonging to this user."""
        # TODO: implement
        pass

    def authenticate(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        # TODO: implement with bcrypt/hashlib
        pass

    def get_total_task_load(self) -> int:
        """Return total duration (minutes) of all pending tasks across all pets."""
        # TODO: implement
        pass

    def update_availability(self, day: str, windows: list[TimeWindow]) -> None:
        """Replace the availability windows for a specific day."""
        # TODO: implement
        pass


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
        # TODO: implement
        pass

    def add_task(self, task: Task) -> None:
        """Manually insert a task into the plan (user edit)."""
        # TODO: implement
        pass

    def remove_task(self, task_id: int) -> None:
        """Remove a task from the plan (user edit)."""
        # TODO: implement
        pass

    def reorder_tasks(self, new_order: list[int]) -> None:
        """Rearrange scheduled_tasks by a list of task IDs in desired order."""
        # TODO: implement
        pass

    def regenerate(self, new_availability: list[TimeWindow]) -> DailyPlan:
        """Re-run the Scheduler on remaining incomplete tasks with updated windows."""
        # TODO: implement — delegate to Scheduler
        pass

    def get_next_task(self) -> Optional[Task]:
        """Return the next pending task in the schedule."""
        # TODO: implement
        pass

    def get_completion_percentage(self) -> float:
        """Return the percentage of scheduled tasks that are completed."""
        # TODO: implement
        pass


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
        # TODO: implement
        pass

    def prioritize_tasks(self) -> list[Task]:
        """Score and sort tasks by weighted composite score (descending)."""
        # TODO: implement scoring formula
        pass

    def resolve_conflicts(self) -> list[Task]:
        """Identify tasks that don't fit and return them with reasons for deferral."""
        # TODO: implement overflow handling
        pass


# ──────────────────────────────────────────────
# Stretch Goal Classes
# ──────────────────────────────────────────────

@dataclass
class RewardSystem:
    """Tracks streaks, badges, and pet happiness (stretch goal)."""

    streaks: dict[str, int] = field(default_factory=dict)
    # streaks format: {"feeding": 5, "walking": 3}
    badges: list[str] = field(default_factory=list)
    happiness_score: dict[int, float] = field(default_factory=dict)
    # happiness_score format: {pet_id: 85.0}
    total_points: int = 0

    def award_completion(self, task: Task, timing_tier: str) -> None:
        """
        Award points based on when the task was completed.

        Tiers: 'on_time' (100%), 'same_day_late' (75%),
               'backlog_day1' (50%), 'backlog_day2' (25%).
        """
        # TODO: implement tiered reward logic
        pass

    def penalize_miss(self, task: Task) -> None:
        """Apply a happiness penalty for a missed task."""
        # TODO: implement
        pass

    def get_streak(self, task_name: str) -> int:
        """Return the current streak count for a given task type."""
        # TODO: implement
        pass

    def get_happiness(self, pet_id: int) -> float:
        """Return the happiness score for a specific pet."""
        # TODO: implement
        pass


@dataclass
class Reminder:
    """A scheduled notification for an upcoming task (stretch goal)."""

    task_reference: Task
    remind_before_minutes: int
    message: str = ""

    def send_reminder(self) -> None:
        """Trigger a notification to the user."""
        # TODO: implement
        pass

    def check_overdue(self) -> bool:
        """Return True if the referenced task is past due."""
        # TODO: implement
        pass
