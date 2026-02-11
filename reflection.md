# PawPal+ Project Reflection

## 1. System Design

**Core User Actions**

1. **Add a pet care task** – Create a care task (walk, feeding, medication, grooming) with duration and priority.
2. **Generate a daily care plan** – Produce an optimized schedule based on available time windows, task priority, and preferences, with reasoning for why tasks were ordered that way.
3. **Enter pet and owner information** – Input owner details (name, availability) and pet details (name, category, special needs) so the planner can personalize recommendations.
4. **Authenticate / manage account** – Register and log in so pet profiles, task history, and schedules persist across sessions.

*Full system architecture, object designs, tradeoff discussions, and finalized decisions are documented in [system_design.md](system_design.md).*

**a. Initial design**

The initial UML is a class diagram with 8 objects (6 core MVP + 2 stretch goal). The core classes and their responsibilities:

- **User** — Holds login credentials and time-window availability. Owns a list of Pets. Handles authentication and availability updates.
- **Pet** — Represents an individual pet with a name, category (enum), age, health notes, and special needs. Owns its own list of Tasks.
- **PetCategory (Enum)** — Static set of species types (Dog, Cat, Fish, etc.). Each value carries default task templates and care guidelines that auto-populate when a new pet is created.
- **Task** — The core work unit: name, duration, priority, frequency (once/daily/weekly), status, and a deferred-day counter. Handles marking itself complete, missed, or reset for recurrence.
- **TimeWindow** — A simple start/end time pair representing a block of user availability. Used by both User and Scheduler.
- **Scheduler** — The scheduling engine. Takes a pool of tasks + availability windows, scores tasks (priority × overdue days × time-sensitivity), and greedily places them into the best-fit windows. Produces a DailyPlan draft.
- **DailyPlan** — The output of the Scheduler: an ordered list of time-slotted tasks, a deferred list, a backlog, and per-task explanations. Supports accept/edit/regenerate workflow.
- **RewardSystem** *(stretch)* — Tracks streaks, badges, and pet happiness scores. Awards tiered points based on completion timing.
- **Reminder** *(stretch)* — Sends notifications before and at task time.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
