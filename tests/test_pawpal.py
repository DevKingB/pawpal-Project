"""
PawPal+ Unit Tests
===================
Test-driven development: tests are written first, then implementation follows.
Organized bottom-up by class dependency order.

Run with: pytest tests/test_pawpal.py -v
"""

import pytest
from datetime import date, datetime, time

from pawpal_system import (
    DailyPlan,
    Frequency,
    Pet,
    PetCategory,
    PlanStatus,
    Priority,
    Scheduler,
    Task,
    TaskStatus,
    TimeWindow,
    User,
)


# ──────────────────────────────────────────────
# Helper Factories
# ──────────────────────────────────────────────
# Reusable fixtures to avoid repeating constructor args in every test.

@pytest.fixture
def sample_task():
    """A basic high-priority daily feeding task."""
    return Task(
        task_id=1,
        name="Feed the dog",
        description="Morning feeding",
        duration=15,
        priority=Priority.HIGH,
        frequency=Frequency.DAILY,
        pet_id=1,
    )


@pytest.fixture
def sample_task_low():
    """A low-priority one-off grooming task."""
    return Task(
        task_id=2,
        name="Groom the cat",
        description="Brush fur",
        duration=30,
        priority=Priority.LOW,
        frequency=Frequency.ONCE,
        pet_id=2,
    )


@pytest.fixture
def sample_pet():
    """A basic dog pet with no tasks."""
    return Pet(
        pet_id=1,
        name="Rex",
        category=PetCategory.DOG,
        age=3,
        weight=25.0,
    )


@pytest.fixture
def sample_user():
    """A basic user with no pets or availability set."""
    return User(
        user_id=1,
        username="testowner",
        email="test@example.com",
        password_hash="hashed_password_123",
    )


@pytest.fixture
def morning_window():
    """An 8:00–9:00 AM time window."""
    return TimeWindow(start=time(8, 0), end=time(9, 0))


@pytest.fixture
def evening_window():
    """A 6:00–8:00 PM time window."""
    return TimeWindow(start=time(18, 0), end=time(20, 0))


# ──────────────────────────────────────────────
# TimeWindow Tests
# ──────────────────────────────────────────────

class TestTimeWindow:
    """Tests for the TimeWindow data class."""

    def test_duration_one_hour(self, morning_window):
        """8:00–9:00 should be 60 minutes."""
        assert morning_window.get_duration_minutes() == 60

    def test_duration_two_hours(self, evening_window):
        """18:00–20:00 should be 120 minutes."""
        assert evening_window.get_duration_minutes() == 120

    def test_duration_thirty_minutes(self):
        """A 30-minute window."""
        window = TimeWindow(start=time(12, 0), end=time(12, 30))
        assert window.get_duration_minutes() == 30

    def test_duration_zero(self):
        """Same start and end should return 0."""
        window = TimeWindow(start=time(10, 0), end=time(10, 0))
        assert window.get_duration_minutes() == 0


# ──────────────────────────────────────────────
# Task Tests
# ──────────────────────────────────────────────

class TestTask:
    """Tests for Task lifecycle and state transitions."""

    def test_default_status_is_pending(self, sample_task):
        """New tasks should start as PENDING."""
        assert sample_task.status == TaskStatus.PENDING

    def test_default_days_deferred_is_zero(self, sample_task):
        """New tasks should have 0 days deferred."""
        assert sample_task.days_deferred == 0

    def test_mark_complete(self, sample_task):
        """mark_complete() should set status to COMPLETED."""
        sample_task.mark_complete()
        assert sample_task.status == TaskStatus.COMPLETED

    def test_mark_missed(self, sample_task):
        """mark_missed() should set status to MISSED and increment days_deferred."""
        sample_task.mark_missed()
        assert sample_task.status == TaskStatus.MISSED
        assert sample_task.days_deferred == 1

    def test_mark_missed_increments_deferred(self, sample_task):
        """Calling mark_missed() multiple times should keep incrementing."""
        sample_task.mark_missed()
        sample_task.mark_missed()
        assert sample_task.days_deferred == 2

    def test_is_overdue_when_past_scheduled_time(self, sample_task):
        """A pending task past its scheduled_time should be overdue."""
        sample_task.scheduled_time = datetime(2026, 1, 1, 8, 0)
        assert sample_task.is_overdue() is True

    def test_is_not_overdue_when_no_scheduled_time(self, sample_task):
        """A task with no scheduled_time should not be overdue."""
        assert sample_task.is_overdue() is False

    def test_is_not_overdue_when_completed(self, sample_task):
        """A completed task should not be considered overdue."""
        sample_task.scheduled_time = datetime(2026, 1, 1, 8, 0)
        sample_task.mark_complete()
        assert sample_task.is_overdue() is False

    def test_reset(self, sample_task):
        """reset() should restore status to PENDING and zero out days_deferred."""
        sample_task.mark_missed()
        sample_task.reset()
        assert sample_task.status == TaskStatus.PENDING
        assert sample_task.days_deferred == 0

    def test_preferred_times_default_empty(self, sample_task):
        """preferred_times should default to an empty list."""
        assert sample_task.preferred_times == []


# ──────────────────────────────────────────────
# Pet Tests
# ──────────────────────────────────────────────

class TestPet:
    """Tests for Pet profile and task management."""

    def test_add_task(self, sample_pet, sample_task):
        """add_task() should append the task to the pet's list."""
        sample_pet.add_task(sample_task)
        assert len(sample_pet.tasks) == 1
        assert sample_pet.tasks[0].name == "Feed the dog"

    def test_add_multiple_tasks(self, sample_pet, sample_task, sample_task_low):
        """Adding multiple tasks should grow the list."""
        sample_pet.add_task(sample_task)
        sample_pet.add_task(sample_task_low)
        assert len(sample_pet.tasks) == 2

    def test_remove_task(self, sample_pet, sample_task):
        """remove_task() should remove the task by ID."""
        sample_pet.add_task(sample_task)
        sample_pet.remove_task(task_id=1)
        assert len(sample_pet.tasks) == 0

    def test_remove_nonexistent_task(self, sample_pet):
        """Removing a task that doesn't exist should not raise an error."""
        sample_pet.remove_task(task_id=999)  # should not crash
        assert len(sample_pet.tasks) == 0

    def test_get_tasks(self, sample_pet, sample_task):
        """get_tasks() should return all tasks."""
        sample_pet.add_task(sample_task)
        tasks = sample_pet.get_tasks()
        assert len(tasks) == 1
        assert tasks[0].task_id == 1

    def test_get_profile_summary_contains_name(self, sample_pet):
        """Profile summary should at minimum include the pet's name."""
        summary = sample_pet.get_profile_summary()
        assert "Rex" in summary

    def test_get_profile_summary_contains_category(self, sample_pet):
        """Profile summary should mention the pet's category."""
        summary = sample_pet.get_profile_summary()
        assert "dog" in summary.lower()

    def test_tasks_are_independent_between_pets(self):
        """Two pets should not share the same task list (mutable default safety)."""
        pet_a = Pet(pet_id=1, name="A", category=PetCategory.DOG, age=1, weight=10.0)
        pet_b = Pet(pet_id=2, name="B", category=PetCategory.CAT, age=2, weight=5.0)
        task = Task(
            task_id=1, name="Walk", description="", duration=30,
            priority=Priority.HIGH, frequency=Frequency.DAILY, pet_id=1,
        )
        pet_a.add_task(task)
        assert len(pet_b.tasks) == 0  # pet_b should be unaffected


# ──────────────────────────────────────────────
# User Tests
# ──────────────────────────────────────────────

class TestUser:
    """Tests for User account management and availability."""

    def test_add_pet(self, sample_user, sample_pet):
        """add_pet() should add a pet to the user's list."""
        sample_user.add_pet(sample_pet)
        assert len(sample_user.pets) == 1
        assert sample_user.pets[0].name == "Rex"

    def test_remove_pet(self, sample_user, sample_pet):
        """remove_pet() should remove the pet by ID."""
        sample_user.add_pet(sample_pet)
        sample_user.remove_pet(pet_id=1)
        assert len(sample_user.pets) == 0

    def test_remove_nonexistent_pet(self, sample_user):
        """Removing a pet that doesn't exist should not crash."""
        sample_user.remove_pet(pet_id=999)
        assert len(sample_user.pets) == 0

    def test_get_pets(self, sample_user, sample_pet):
        """get_pets() should return all pets."""
        sample_user.add_pet(sample_pet)
        pets = sample_user.get_pets()
        assert len(pets) == 1

    def test_update_availability(self, sample_user, morning_window, evening_window):
        """update_availability() should set windows for a specific day."""
        sample_user.update_availability("monday", [morning_window, evening_window])
        assert len(sample_user.availability["monday"]) == 2

    def test_update_availability_replaces(self, sample_user, morning_window, evening_window):
        """Updating the same day should replace, not append."""
        sample_user.update_availability("monday", [morning_window, evening_window])
        sample_user.update_availability("monday", [morning_window])
        assert len(sample_user.availability["monday"]) == 1

    def test_get_total_task_load(self, sample_user, sample_pet, sample_task):
        """Should sum durations of all pending tasks across all pets."""
        sample_pet.add_task(sample_task)  # 15 min
        sample_user.add_pet(sample_pet)
        assert sample_user.get_total_task_load() == 15

    def test_get_total_task_load_ignores_completed(self, sample_user, sample_pet, sample_task):
        """Completed tasks should not count toward the load."""
        sample_task.mark_complete()
        sample_pet.add_task(sample_task)
        sample_user.add_pet(sample_pet)
        assert sample_user.get_total_task_load() == 0

    def test_get_total_task_load_multiple_pets(self, sample_user, sample_task):
        """Should sum across multiple pets."""
        pet1 = Pet(pet_id=1, name="Rex", category=PetCategory.DOG, age=3, weight=25.0)
        pet2 = Pet(pet_id=2, name="Whiskers", category=PetCategory.CAT, age=5, weight=4.0)
        task2 = Task(
            task_id=2, name="Clean litter", description="", duration=10,
            priority=Priority.MEDIUM, frequency=Frequency.DAILY, pet_id=2,
        )
        pet1.add_task(sample_task)  # 15 min
        pet2.add_task(task2)        # 10 min
        sample_user.add_pet(pet1)
        sample_user.add_pet(pet2)
        assert sample_user.get_total_task_load() == 25

    def test_pets_are_independent_between_users(self):
        """Two users should not share the same pets list."""
        user_a = User(user_id=1, username="a", email="a@a.com", password_hash="x")
        user_b = User(user_id=2, username="b", email="b@b.com", password_hash="y")
        pet = Pet(pet_id=1, name="Rex", category=PetCategory.DOG, age=3, weight=25.0)
        user_a.add_pet(pet)
        assert len(user_b.pets) == 0


# ──────────────────────────────────────────────
# PetCategory Enum Tests
# ──────────────────────────────────────────────

class TestPetCategory:
    """Tests for PetCategory enum default tasks and care tips."""

    def test_dog_has_default_tasks(self):
        """DOG category should return a non-empty default task list."""
        tasks = PetCategory.DOG.get_default_tasks()
        assert isinstance(tasks, list)
        assert len(tasks) > 0

    def test_cat_has_default_tasks(self):
        """CAT category should return a non-empty default task list."""
        tasks = PetCategory.CAT.get_default_tasks()
        assert isinstance(tasks, list)
        assert len(tasks) > 0

    def test_fish_has_default_tasks(self):
        """FISH category should return a non-empty default task list."""
        tasks = PetCategory.FISH.get_default_tasks()
        assert isinstance(tasks, list)
        assert len(tasks) > 0

    def test_dog_care_tips_is_string(self):
        """Care tips should return a non-empty string."""
        tips = PetCategory.DOG.get_care_tips()
        assert isinstance(tips, str)
        assert len(tips) > 0

    def test_different_categories_have_different_defaults(self):
        """DOG and FISH should have different default task lists."""
        dog_tasks = PetCategory.DOG.get_default_tasks()
        fish_tasks = PetCategory.FISH.get_default_tasks()
        dog_names = {t["name"] for t in dog_tasks}
        fish_names = {t["name"] for t in fish_tasks}
        assert dog_names != fish_names


# ──────────────────────────────────────────────
# DailyPlan Tests
# ──────────────────────────────────────────────

class TestDailyPlan:
    """Tests for DailyPlan lifecycle and editing."""

    @pytest.fixture
    def sample_plan(self, sample_user, sample_task):
        """A draft plan with one scheduled task."""
        return DailyPlan(
            date=date(2026, 2, 11),
            owner=sample_user,
            scheduled_tasks=[sample_task],
            total_duration=15,
        )

    def test_default_status_is_draft(self, sample_plan):
        """New plans should start as DRAFT."""
        assert sample_plan.status == PlanStatus.DRAFT

    def test_accept_changes_status(self, sample_plan):
        """accept() should change status from DRAFT to ACCEPTED."""
        sample_plan.accept()
        assert sample_plan.status == PlanStatus.ACCEPTED

    def test_add_task_to_plan(self, sample_plan, sample_task_low):
        """add_task() should insert a task into scheduled_tasks."""
        sample_plan.add_task(sample_task_low)
        assert len(sample_plan.scheduled_tasks) == 2

    def test_remove_task_from_plan(self, sample_plan):
        """remove_task() should remove a task by ID."""
        sample_plan.remove_task(task_id=1)
        assert len(sample_plan.scheduled_tasks) == 0

    def test_get_next_task_returns_first_pending(self, sample_plan):
        """get_next_task() should return the first pending task."""
        next_task = sample_plan.get_next_task()
        assert next_task is not None
        assert next_task.status == TaskStatus.PENDING

    def test_get_next_task_skips_completed(self, sample_plan, sample_task_low):
        """get_next_task() should skip completed tasks."""
        sample_plan.scheduled_tasks[0].mark_complete()
        sample_plan.add_task(sample_task_low)
        next_task = sample_plan.get_next_task()
        assert next_task.task_id == 2

    def test_get_next_task_returns_none_when_all_done(self, sample_plan):
        """get_next_task() should return None when all tasks are completed."""
        sample_plan.scheduled_tasks[0].mark_complete()
        assert sample_plan.get_next_task() is None

    def test_completion_percentage_none_done(self, sample_plan):
        """0 of 1 tasks completed = 0%."""
        assert sample_plan.get_completion_percentage() == 0.0

    def test_completion_percentage_all_done(self, sample_plan):
        """1 of 1 tasks completed = 100%."""
        sample_plan.scheduled_tasks[0].mark_complete()
        assert sample_plan.get_completion_percentage() == 100.0

    def test_completion_percentage_partial(self, sample_plan, sample_task_low):
        """1 of 2 tasks completed = 50%."""
        sample_plan.add_task(sample_task_low)
        sample_plan.scheduled_tasks[0].mark_complete()
        assert sample_plan.get_completion_percentage() == 50.0

    def test_completion_percentage_empty_plan(self, sample_user):
        """An empty plan should return 0% (not divide by zero)."""
        plan = DailyPlan(date=date(2026, 2, 11), owner=sample_user)
        assert plan.get_completion_percentage() == 0.0

    def test_reorder_tasks(self, sample_plan, sample_task_low):
        """reorder_tasks() should rearrange tasks by the given ID order."""
        sample_plan.add_task(sample_task_low)
        sample_plan.reorder_tasks([2, 1])
        assert sample_plan.scheduled_tasks[0].task_id == 2
        assert sample_plan.scheduled_tasks[1].task_id == 1


# ──────────────────────────────────────────────
# Scheduler Tests
# ──────────────────────────────────────────────

class TestScheduler:
    """Tests for the scheduling engine."""

    @pytest.fixture
    def scheduler(self):
        return Scheduler()

    @pytest.fixture
    def pet_with_tasks(self):
        """A dog with three tasks of varying priority."""
        pet = Pet(pet_id=1, name="Rex", category=PetCategory.DOG, age=3, weight=25.0)
        pet.add_task(Task(
            task_id=1, name="Walk", description="Morning walk", duration=30,
            priority=Priority.HIGH, frequency=Frequency.DAILY, pet_id=1,
        ))
        pet.add_task(Task(
            task_id=2, name="Feed", description="Breakfast", duration=10,
            priority=Priority.HIGH, frequency=Frequency.DAILY, pet_id=1,
        ))
        pet.add_task(Task(
            task_id=3, name="Groom", description="Brush coat", duration=20,
            priority=Priority.LOW, frequency=Frequency.WEEKLY, pet_id=1,
        ))
        return pet

    def test_generate_plan_returns_daily_plan(self, scheduler, pet_with_tasks, morning_window):
        """generate_plan() should return a DailyPlan object."""
        plan = scheduler.generate_plan([pet_with_tasks], [morning_window])
        assert isinstance(plan, DailyPlan)

    def test_generate_plan_is_draft(self, scheduler, pet_with_tasks, morning_window):
        """The generated plan should always start as a DRAFT."""
        plan = scheduler.generate_plan([pet_with_tasks], [morning_window])
        assert plan.status == PlanStatus.DRAFT

    def test_high_priority_scheduled_before_low(self, scheduler, pet_with_tasks, evening_window):
        """High-priority tasks should appear before low-priority in the plan."""
        plan = scheduler.generate_plan([pet_with_tasks], [evening_window])
        scheduled_priorities = [t.priority for t in plan.scheduled_tasks]
        # All HIGH tasks should come before any LOW tasks
        if Priority.LOW in scheduled_priorities:
            first_low = scheduled_priorities.index(Priority.LOW)
            for i in range(first_low):
                assert scheduled_priorities[i] in (Priority.HIGH, Priority.MEDIUM)

    def test_tasks_that_dont_fit_are_deferred(self, scheduler, pet_with_tasks):
        """If time is too short, some tasks should land in deferred_tasks or backlog."""
        tiny_window = TimeWindow(start=time(8, 0), end=time(8, 15))  # only 15 min
        plan = scheduler.generate_plan([pet_with_tasks], [tiny_window])
        total_scheduled = len(plan.scheduled_tasks)
        total_deferred = len(plan.deferred_tasks) + len(plan.backlog)
        assert total_scheduled + total_deferred == 3  # all tasks accounted for
        assert total_deferred > 0  # some must be deferred

    def test_low_priority_deferred_goes_to_backlog(self, scheduler, pet_with_tasks):
        """Low-priority tasks that don't fit should go to backlog, not deferred_tasks."""
        tiny_window = TimeWindow(start=time(8, 0), end=time(8, 15))
        plan = scheduler.generate_plan([pet_with_tasks], [tiny_window])
        backlog_priorities = [t.priority for t in plan.backlog]
        deferred_priorities = [t.priority for t in plan.deferred_tasks]
        for p in backlog_priorities:
            assert p == Priority.LOW
        for p in deferred_priorities:
            assert p in (Priority.HIGH, Priority.MEDIUM)

    def test_overdue_tasks_score_higher(self, scheduler, morning_window):
        """A task with days_deferred > 0 should be scheduled ahead of a fresh task."""
        pet = Pet(pet_id=1, name="Rex", category=PetCategory.DOG, age=3, weight=25.0)
        overdue = Task(
            task_id=1, name="Overdue med", description="", duration=10,
            priority=Priority.MEDIUM, frequency=Frequency.ONCE, pet_id=1,
            days_deferred=3,
        )
        fresh = Task(
            task_id=2, name="Fresh med", description="", duration=10,
            priority=Priority.MEDIUM, frequency=Frequency.ONCE, pet_id=1,
        )
        pet.add_task(overdue)
        pet.add_task(fresh)
        plan = scheduler.generate_plan([pet], [morning_window])
        # The overdue task should appear first
        assert plan.scheduled_tasks[0].task_id == 1

    def test_empty_pet_list_produces_empty_plan(self, scheduler, morning_window):
        """No pets means an empty plan with no tasks."""
        plan = scheduler.generate_plan([], [morning_window])
        assert len(plan.scheduled_tasks) == 0
        assert len(plan.deferred_tasks) == 0

    def test_plan_explanation_has_entries(self, scheduler, pet_with_tasks, evening_window):
        """Each scheduled task should have an explanation entry."""
        plan = scheduler.generate_plan([pet_with_tasks], [evening_window])
        for task in plan.scheduled_tasks:
            assert task.task_id in plan.explanation

    def test_multiple_pets_tasks_are_combined(self, scheduler, evening_window):
        """Tasks from multiple pets should all be considered for scheduling."""
        dog = Pet(pet_id=1, name="Rex", category=PetCategory.DOG, age=3, weight=25.0)
        cat = Pet(pet_id=2, name="Whiskers", category=PetCategory.CAT, age=5, weight=4.0)
        dog.add_task(Task(
            task_id=1, name="Walk dog", description="", duration=30,
            priority=Priority.HIGH, frequency=Frequency.DAILY, pet_id=1,
        ))
        cat.add_task(Task(
            task_id=2, name="Clean litter", description="", duration=15,
            priority=Priority.MEDIUM, frequency=Frequency.DAILY, pet_id=2,
        ))
        plan = scheduler.generate_plan([dog, cat], [evening_window])
        all_task_ids = [t.task_id for t in plan.scheduled_tasks]
        assert 1 in all_task_ids
        assert 2 in all_task_ids
