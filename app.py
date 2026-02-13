import streamlit as st
import hashlib
from datetime import date, time, datetime

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
    regenerate_plan_system,
)

# ──────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")


# ──────────────────────────────────────────────
# Session State Initialization
# ──────────────────────────────────────────────
# Streamlit reruns top-to-bottom on every interaction.
# st.session_state is the persistent "vault" — objects survive across reruns.

def init_session_state():
    """Initialize session state with default values if not already set."""
    # FIX BUG #17: user-specific state (current_plan, next_task_id,
    # next_pet_id) is now cleared in register and login handlers.
    if "user" not in st.session_state:
        st.session_state.user = None
    if "scheduler" not in st.session_state:
        st.session_state.scheduler = Scheduler()
    if "current_plan" not in st.session_state:
        st.session_state.current_plan = None
    if "next_task_id" not in st.session_state:
        st.session_state.next_task_id = 1
    if "next_pet_id" not in st.session_state:
        st.session_state.next_pet_id = 1
    if "pet_form_counter" not in st.session_state:
        st.session_state.pet_form_counter = 0
    if "task_form_counter" not in st.session_state:
        st.session_state.task_form_counter = 0
    if "page" not in st.session_state:
        st.session_state.page = "login"
    # BUG C: Track availability changes for plan regeneration
    if "availability_changed" not in st.session_state:
        st.session_state.availability_changed = False
    if "success_message" not in st.session_state:
        st.session_state.success_message = None

init_session_state()


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using SHA-256 (MVP; future: bcrypt)."""
    return hashlib.sha256(password.encode()).hexdigest()


def show_success_message():
    """Display and clear any pending success message."""
    if st.session_state.success_message:
        st.success(st.session_state.success_message)
        st.session_state.success_message = None


def get_user() -> User:
    """Return the currently logged-in user."""
    return st.session_state.user


def regenerate_plan_preserving_progress(user: User, existing_plan: DailyPlan) -> str:
    """
    BUG C FIX: UI wrapper — gather pets/windows from user, delegate to
    pawpal_system.regenerate_plan_system(), update session state, and return summary.
    """
    # Snapshot finished statuses is handled inside regenerate_plan_system (system-side)
    # Gather pets and flatten user's availability into a list of TimeWindow
    pets = list(user.pets or [])
    all_windows = []
    if isinstance(user.availability, dict):
        for day_windows in user.availability.values():
            if day_windows:
                all_windows.extend(day_windows)
    else:
        all_windows = list(user.availability or [])

    # Defensive defaults
    pets = list(pets)
    all_windows = list(all_windows)

    if not pets:
        return "No pets to schedule."

    scheduler = st.session_state.get("scheduler")
    if scheduler is None:
        scheduler = Scheduler()
        st.session_state.scheduler = scheduler

    # Delegate to system-level helper
    new_plan, msg = regenerate_plan_system(scheduler, pets, all_windows, existing_plan)

    # Update session state with regenerated plan
    st.session_state.current_plan = new_plan

    return msg


# ──────────────────────────────────────────────
# Page: Login / Register
# ──────────────────────────────────────────────

def render_login_page():
    """Render the authentication page."""
    st.title("🐾 PawPal+")
    st.markdown("**Your AI-powered pet care planning assistant.**")
    st.divider()

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_register:
        st.subheader("Create Account")
        with st.form("register_form"):
            reg_username = st.text_input("Username")
            reg_email = st.text_input("Email")
            reg_password = st.text_input("Password", type="password")
            reg_confirm = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Register")

            if submitted:
                # FIX BUG #3: Strip whitespace to reject blank-only inputs
                reg_username = reg_username.strip()
                reg_email = reg_email.strip()
                reg_password = reg_password.strip()
                reg_confirm = reg_confirm.strip()
                if not reg_username or not reg_email or not reg_password:
                    st.error("All fields are required.")
                elif reg_password != reg_confirm:
                    st.error("Passwords do not match.")
                else:
                    # FIX BUG #17: Clear all user-specific state before
                    # creating a new user so old plan/pets don't carry over.
                    st.session_state.current_plan = None
                    st.session_state.next_task_id = 1
                    st.session_state.next_pet_id = 1
                    st.session_state.pet_form_counter = 0
                    st.session_state.task_form_counter = 0

                    user = User(
                        user_id=1,
                        username=reg_username,
                        email=reg_email,
                        password_hash=hash_password(reg_password),
                    )
                    st.session_state.user = user
                    st.session_state.page = "dashboard"
                    st.success(f"Welcome, {reg_username}! Account created.")
                    st.rerun()

    with tab_login:
        st.subheader("Sign In")
        with st.form("login_form"):
            login_username = st.text_input("Username")
            login_password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                user = st.session_state.user
                if user and user.username == login_username and user.authenticate(login_password):
                    # FIX BUG #17: Clear plan state on login so stale data
                    # from a previous session doesn't bleed through.
                    st.session_state.current_plan = None
                    st.session_state.page = "dashboard"
                    st.success(f"Welcome back, {login_username}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Register first if you don't have an account.")


# ──────────────────────────────────────────────
# Sidebar Navigation
# ──────────────────────────────────────────────

def render_sidebar():
    """Render the sidebar with navigation and user info."""
    user = get_user()
    with st.sidebar:
        st.title("🐾 PawPal+")
        st.caption(f"Logged in as **{user.username}**")
        st.divider()

        if st.button("📋 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        if st.button("🐕 My Pets", use_container_width=True):
            st.session_state.page = "pets"
            st.rerun()
        if st.button("📝 Add Task", use_container_width=True):
            st.session_state.page = "add_task"
            st.rerun()
        if st.button("⏰ Availability", use_container_width=True):
            st.session_state.page = "availability"
            st.rerun()
        if st.button("📅 Generate Plan", use_container_width=True):
            st.session_state.page = "plan"
            st.rerun()

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()


# ──────────────────────────────────────────────
# Page: Dashboard
# ──────────────────────────────────────────────

def render_dashboard():
    """Render the main dashboard overview."""
    user = get_user()
    st.title("📋 Dashboard")
    st.markdown(f"Welcome back, **{user.username}**!")

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pets", len(user.pets))
    with col2:
        total_tasks = sum(len(p.tasks) for p in user.pets)
        st.metric("Total Tasks", total_tasks)
    with col3:
        load = user.get_total_task_load()
        st.metric("Pending Load", f"{load} min")

    st.divider()

    # Current plan status
    plan = st.session_state.current_plan
    if plan:
        st.subheader("Today's Plan")
        pct = plan.get_completion_percentage()
        st.progress(pct / 100, text=f"{pct:.0f}% complete")

        for task in plan.scheduled_tasks:
            icon = "✅" if task.status == TaskStatus.COMPLETED else "⏳"
            st.write(f"{icon} **{task.name}** — {task.duration} min ({task.priority.value})")
    else:
        st.info("No plan generated yet. Go to **Generate Plan** to create today's schedule.")

    # Pet summaries
    if user.pets:
        st.divider()
        st.subheader("Pet Summaries")
        for pet in user.pets:
            with st.expander(f"🐾 {pet.name} ({pet.category.value})"):
                st.text(pet.get_profile_summary())
                tips = pet.category.get_care_tips()
                st.caption(f"💡 {tips}")


# ──────────────────────────────────────────────
# Page: My Pets (Add / View / Remove)
# ──────────────────────────────────────────────

def render_pets_page():
    """Render the pet management page."""
    user = get_user()
    st.title("🐕 My Pets")

    # FIX BUG #1: Counter-based form key forces Streamlit to create a fresh
    # form after each submission, clearing all widget values.
    #
    # FIX BUG #3: Whitespace-only pet name is now rejected.
    form_key = f"add_pet_form_{st.session_state.pet_form_counter}"
    with st.expander("➕ Add a New Pet", expanded=not user.pets):
        with st.form(form_key):
            pet_name = st.text_input("Pet Name")
            category = st.selectbox("Species", [c.value for c in PetCategory])
            col1, col2 = st.columns(2)
            with col1:
                age = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
            with col2:
                weight = st.number_input("Weight (kg)", min_value=0.1, max_value=200.0, value=5.0)
            health_notes = st.text_area("Health Notes (optional)")
            special_needs = st.text_area("Special Needs (optional)")
            submitted = st.form_submit_button("Add Pet")

            if submitted:
                # FIX BUG #3: Strip whitespace to catch blank/space-only names
                pet_name = pet_name.strip()
                if not pet_name:
                    st.error("Pet name is required.")
                else:
                    pet = Pet(
                        pet_id=st.session_state.next_pet_id,
                        name=pet_name,
                        category=PetCategory(category),
                        age=age,
                        weight=weight,
                        health_notes=health_notes,
                        special_needs=special_needs,
                    )
                    user.add_pet(pet)
                    st.session_state.next_pet_id += 1
                    # FIX BUG #4: toast() survives rerun as an overlay
                    st.toast(f"Added {pet_name} the {category}! 🐾")

                    # Auto-populate default tasks for the pet's category
                    defaults = pet.category.get_default_tasks()
                    for t in defaults:
                        task = Task(
                            task_id=st.session_state.next_task_id,
                            name=t["name"],
                            description=f"Default {category} task",
                            duration=t["duration"],
                            priority=Priority(t["priority"]),
                            frequency=Frequency(t["frequency"]),
                            pet_id=pet.pet_id,
                        )
                        pet.add_task(task)
                        st.session_state.next_task_id += 1
                    if defaults:
                        st.toast(f"Auto-added {len(defaults)} default {category} tasks.")
                    # FIX BUG #1: Bump counter so next render creates a fresh form
                    st.session_state.pet_form_counter += 1
                    st.rerun()

    # Display existing pets
    if user.pets:
        st.divider()
        for pet in user.pets:
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"### 🐾 {pet.name}")
                    st.write(f"**Species:** {pet.category.value} | **Age:** {pet.age} | **Weight:** {pet.weight}kg")
                    if pet.health_notes:
                        st.caption(f"🏥 {pet.health_notes}")
                    if pet.special_needs:
                        st.caption(f"⚠️ {pet.special_needs}")
                    pending = [t for t in pet.tasks if t.status == TaskStatus.PENDING]
                    st.write(f"**Tasks:** {len(pet.tasks)} total, {len(pending)} pending")
                with col2:
                    if st.button("🗑️ Remove", key=f"remove_pet_{pet.pet_id}"):
                        user.remove_pet(pet.pet_id)
                        st.rerun()

                # Show this pet's tasks
                # TODO #6: Add edit and delete buttons per task here.
                # User should be able to fix mistakes before generating a plan.
                if pet.tasks:
                    with st.expander(f"View {pet.name}'s tasks"):
                        for task in pet.tasks:
                            status_icon = "✅" if task.status == TaskStatus.COMPLETED else "⏳"
                            st.write(
                                f"{status_icon} **{task.name}** — {task.duration}min, "
                                f"{task.priority.value} priority, {task.frequency.value}"
                            )
    else:
        st.info("No pets yet. Add your first pet above!")


# ──────────────────────────────────────────────
# Page: Add Task
# ──────────────────────────────────────────────

def render_add_task_page():
    """Render the task creation page."""
    user = get_user()
    st.title("📝 Add Task")

    if not user.pets:
        st.warning("You need to add a pet first before creating tasks.")
        if st.button("Go to My Pets"):
            st.session_state.page = "pets"
            st.rerun()
        return

    # FIX BUG #1 (Add Task form): Counter-based key clears fields after submit
    task_form_key = f"add_task_form_{st.session_state.task_form_counter}"
    with st.form(task_form_key):
        pet_options = {f"{p.name} ({p.category.value})": p for p in user.pets}
        selected_pet_label = st.selectbox("Assign to Pet", list(pet_options.keys()))
        selected_pet = pet_options[selected_pet_label]

        task_name = st.text_input("Task Name")
        description = st.text_area("Description (optional)")

        col1, col2 = st.columns(2)
        with col1:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=15)
            priority = st.selectbox("Priority", [p.value for p in Priority])
        with col2:
            frequency = st.selectbox("Frequency", [f.value for f in Frequency])

        submitted = st.form_submit_button("Add Task")

        if submitted:
            # FIX BUG #3: Strip whitespace to catch blank/space-only names
            task_name = task_name.strip()
            if not task_name:
                st.error("Task name is required.")
            else:
                # FIX BUG #5: Check for duplicate task name on the same pet
                # Note: Duplicate detection is intentionally case-insensitive (using .lower())
                # to treat "Walk" and "walk" as the same task for a given pet, while still
                # storing and displaying the task name with the user's original casing.
                existing_names = [t.name.lower() for t in selected_pet.tasks]
                if task_name.lower() in existing_names:
                    st.error(f"**{selected_pet.name}** already has a task named \"{task_name}\". Use a different name or edit the existing task.")
                else:
                    task = Task(
                        task_id=st.session_state.next_task_id,
                        name=task_name,
                        description=description,
                        duration=int(duration),
                        priority=Priority(priority),
                        frequency=Frequency(frequency),
                        pet_id=selected_pet.pet_id,
                    )
                    selected_pet.add_task(task)
                    st.session_state.next_task_id += 1
                    # FIX BUG #4: toast() survives rerun as an overlay
                    st.toast(f"Added {task_name} to {selected_pet.name}! ✅")
                    st.session_state.task_form_counter += 1
                    st.rerun()


# ──────────────────────────────────────────────
# Page: Availability
# ──────────────────────────────────────────────

def render_availability_page():
    """Page for setting daily availability windows."""
    st.title("⏰ Set Your Availability")
    st.caption("Define your free time windows for each day. The scheduler uses these to build your plan.")

    user = get_user()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for day in days:
        with st.expander(f"📅 {day}"):
            # Show existing windows for this day
            day_lower = day.lower()
            day_windows = [w for w in user.availability.get(day_lower, []) if w.day_of_week == day_lower]

            if day_windows:
                for w in day_windows:
                    duration = int((datetime.combine(date.today(), w.end) -
                                    datetime.combine(date.today(), w.start)).total_seconds() / 60)
                    st.write(f"{w.start.strftime('%H:%M')} — {w.end.strftime('%H:%M')} ({duration} min)")
            else:
                st.write("No windows set.")

            # Time pickers for adding a new window
            col1, col2, col3 = st.columns([2, 2, 1])
            time_options = [time(h, m) for h in range(24) for m in (0, 15, 30, 45)]
            time_labels = [t.strftime("%H:%M") for t in time_options]

            with col1:
                start_idx = st.selectbox(
                    "Start", range(len(time_options)),
                    format_func=lambda i: time_labels[i],
                    key=f"start_{day}",
                    label_visibility="visible"
                )
            with col2:
                end_idx = st.selectbox(
                    "End", range(len(time_options)),
                    format_func=lambda i: time_labels[i],
                    key=f"end_{day}",
                    index=min(4, len(time_options) - 1),
                    label_visibility="visible"
                )
            with col3:
                st.write("")  # spacer
                if st.button("Add", key=f"add_{day}"):
                    start_t = time_options[start_idx]
                    end_t = time_options[end_idx]
                    if start_t >= end_t:
                        st.error("Start must be before end.")
                    else:
                        new_window = TimeWindow(
                            day_of_week=day_lower,
                            start=start_t,
                            end=end_t,
                        )
                        if day_lower not in user.availability:
                            user.availability[day_lower] = []
                        user.availability[day_lower].append(new_window)

                        # ── BUG C FIX: Re-evaluate plan on availability change ──
                        plan = st.session_state.current_plan
                        if plan is not None:
                            if plan.status == PlanStatus.DRAFT:
                                msg = regenerate_plan_preserving_progress(user, plan)
                                st.toast(f"🔄 {msg}")
                            elif plan.status == PlanStatus.ACCEPTED:
                                st.session_state.availability_changed = True
                        # ─────────────────────────────────────────────────────────

                        st.rerun()

            # Clear all windows for this day
            if day_windows:
                if st.button(f"Clear {day.lower()}", key=f"clear_{day}"):
                    user.availability[day_lower] = []  # <-- FIXED
                    # Plan re-evaluation logic here as above
                    plan = st.session_state.current_plan
                    if plan is not None:
                        if plan.status == PlanStatus.DRAFT:
                            msg = regenerate_plan_preserving_progress(user, plan)
                            st.toast(f"🔄 {msg}")
                        elif plan.status == PlanStatus.ACCEPTED:
                            st.session_state.availability_changed = True
                    st.rerun()


# ──────────────────────────────────────────────
# Page: Generate Plan
# ──────────────────────────────────────────────

def render_plan_page():
    """Page for generating and viewing the daily care plan."""
    st.title("📋 Daily Care Plan")

    user = get_user()
    plan = st.session_state.current_plan

    # ── BUG C FIX: Prompt to regenerate if availability changed during ACCEPTED plan ──
    if (st.session_state.get("availability_changed")
            and plan is not None
            and plan.status == PlanStatus.ACCEPTED):
        st.info("📢 Your availability has changed since this plan was accepted. "
                "Regenerate to fit deferred tasks into your new free time?")
        col_regen, col_dismiss = st.columns(2)
        with col_regen:
            if st.button("🔄 Regenerate Plan", key="regen_availability"):
                msg = regenerate_plan_preserving_progress(user, plan)
                st.session_state.availability_changed = False
                st.success(msg)
                st.rerun()
        with col_dismiss:
            if st.button("Keep Current Plan", key="dismiss_availability"):
                st.session_state.availability_changed = False
                st.rerun()
    # ──────────────────────────────────────────────────────────────────────────────────

    # Determine today's day of week for availability lookup
    today = date.today()
    day_name = today.strftime("%A").lower()
    today_windows = user.availability.get(day_name, [])

    if not today_windows:
        st.warning(f"No availability set for **{day_name.capitalize()}**. Go to Availability to set your time windows.")
        if st.button("Set Availability"):
            st.session_state.page = "availability"
            st.rerun()
        return

    total_available = sum(w.get_duration_minutes() for w in today_windows)
    st.info(f"**{day_name.capitalize()}** — {len(today_windows)} window(s), {total_available} min available")

    # FIX BUG #10: Only show Generate Plan button if no plan exists or plan is DRAFT.
    # Once ACCEPTED, the plan is locked — user must complete or wait for next day.
    plan = st.session_state.current_plan
    if not plan or plan.status == PlanStatus.DRAFT:
        if st.button("🔄 Generate Plan", use_container_width=True):
            scheduler = st.session_state.scheduler
            new_plan = scheduler.generate_plan(user.pets, today_windows)
            new_plan.owner = user
            st.session_state.current_plan = new_plan
            st.rerun()

    plan = st.session_state.current_plan
    if not plan:
        st.info("Click **Generate Plan** to create today's schedule.")
        return

    # Plan status and progress
    pct = plan.get_completion_percentage()
    status_label = f"Status: **{plan.status.value.upper()}**"
    st.markdown(status_label)
    st.progress(pct / 100, text=f"{pct:.0f}% complete")

    # FIX BUG #11 / #8 / #10: DRAFT vs ACCEPTED flow corrected.
    # DRAFT  → [View tasks, Regenerate, Accept]
    # ACCEPTED → [Done, Skip ("not today, no penalty")]. Plan locked.

    # Accept plan if still draft
    if plan.status == PlanStatus.DRAFT:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Accept Plan", use_container_width=True):
                plan.accept()
                st.rerun()
        with col2:
            if st.button("🔄 Regenerate", use_container_width=True):
                scheduler = st.session_state.scheduler
                new_plan = scheduler.generate_plan(user.pets, today_windows)
                new_plan.owner = user
                st.session_state.current_plan = new_plan
                st.rerun()

    # Scheduled tasks
    st.subheader("Scheduled Tasks")
    if plan.scheduled_tasks:
        for task in plan.scheduled_tasks:
            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    # FIX BUG #8: Visual distinction for each task state
                    if task.status == TaskStatus.COMPLETED:
                        icon = "✅"
                    elif task.status == TaskStatus.SKIPPED:
                        icon = "⏭️"
                    else:
                        icon = "⏳"
                    pet_name = next((p.name for p in user.pets if p.pet_id == task.pet_id), "Unknown")
                    st.markdown(f"{icon} **{task.name}** — {pet_name}")
                    st.caption(f"{task.duration}min | {task.priority.value} | {task.frequency.value}")
                    if task.task_id in plan.explanation:
                        st.caption(f"💡 {plan.explanation[task.task_id]}")
                    # FIX BUG #8: Show skip reason inline
                    if task.status == TaskStatus.SKIPPED:
                        st.caption("⏭️ Skipped — not today, no penalty")
                with col2:
                    # FIX BUG #11: Only show Done when plan is ACCEPTED
                    if plan.status == PlanStatus.ACCEPTED and task.status == TaskStatus.PENDING:
                        if st.button("Done", key=f"complete_{task.task_id}"):
                            task.mark_complete()
                            st.rerun()
                with col3:
                    # FIX BUG #11 + #8: Only show Skip when plan ACCEPTED;
                    # label clarifies "no penalty" per Section 12 rules.
                    if plan.status == PlanStatus.ACCEPTED and task.status == TaskStatus.PENDING:
                        if st.button("Skip", key=f"skip_{task.task_id}", help="Not today — no penalty"):
                            task.status = TaskStatus.SKIPPED
                            st.rerun()
    else:
        st.info("No tasks scheduled.")

    # Deferred and backlog sections
    if plan.deferred_tasks:
        st.subheader("⚠️ Deferred (didn't fit)")
        for task in plan.deferred_tasks:
            pet_name = next((p.name for p in user.pets if p.pet_id == task.pet_id), "Unknown")
            st.write(f"🔸 **{task.name}** — {pet_name}, {task.duration}min, {task.priority.value}")

    if plan.backlog:
        st.subheader("📦 Backlog")
        for task in plan.backlog:
            pet_name = next((p.name for p in user.pets if p.pet_id == task.pet_id), "Unknown")
            st.write(f"🔹 **{task.name}** — {pet_name}, {task.duration}min, {task.priority.value}")

    # Next task shortcut
    # TODO #9: Add onboarding / guided flow hints on dashboard.
    # Show step indicators: Add Pets → Add Tasks → Set Availability → Generate Plan.
    # Future #13: Tie task completion into RewardSystem — show points, streaks.
    st.divider()
    next_task = plan.get_next_task()
    if next_task:
        pet_name = next((p.name for p in user.pets if p.pet_id == next_task.pet_id), "Unknown")
        st.success(f"**Up next:** {next_task.name} for {pet_name} ({next_task.duration} min)")
    else:
        st.balloons()
        st.success("🎉 All tasks complete for today!")


# ──────────────────────────────────────────────
# Main App Router
# ──────────────────────────────────────────────

def main():
    """Route to the correct page based on session state."""
    page = st.session_state.page

    if page == "login" or st.session_state.user is None:
        render_login_page()
    else:
        render_sidebar()
        if page == "dashboard":
            render_dashboard()
        elif page == "pets":
            render_pets_page()
        elif page == "add_task":
            render_add_task_page()
        elif page == "availability":
            render_availability_page()
        elif page == "plan":
            render_plan_page()
        else:
            render_dashboard()


if __name__ == "__main__":
    main()
