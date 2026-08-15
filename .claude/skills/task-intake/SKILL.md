---
name: task-intake
description: The front door for ANY new work. Use at the start of every new task or session — whenever the user gives a development request, a bug report, or says "let's work on X", "start a new task", or pastes a requirement. Checks the backlog for pending work, confirms the autonomy level, allocates the spec ID, then routes. Always run this BEFORE the feature or bug-fix workflow.
---

# Task Intake (session front door)

Run this before starting any work. Four jobs: recover state, check the backlog,
set autonomy, route.

Every path below is the one declared in `harness.toml`. Where this file says
"the backlog" or "the specs directory", read the configured location — nothing
here assumes a particular layout, and a skill that hardcodes one silently undoes
the reason the config exists.

## Step 1 — Recover any in-flight task

Read `.claude/state/current-task.json` (local, gitignored). If it exists and
`status` is not `done`/`abandoned`:

> "There's an unfinished task in progress: **{spec_id} — {title}**, last state
> **{state}** (tests: {test_status}). Resume it, or set it aside and start
> something new?"

If resuming, hand back to the owning workflow AT that state — do not restart from
the beginning. A resumed task that re-explores has lost the thing resuming was
for.

## Step 2 — Check the backlog

Read the configured backlog. Collect every item or phase with `status: pending`
or `blocked` whose `depends_on` are all `done`.

- If there are ready items, surface them BEFORE taking the new request. Never
  silently ignore them: this is the "check the todo list on every new task"
  guarantee, and it is the only thing standing between a backlog and a graveyard.
- If the new request looks like something already in the backlog, say so and
  offer to continue that item rather than duplicating it.

**Then reconcile, with the command rather than by eye:**

```
harness check backlog-schema
```

Exit 0 means nothing malformed. This prose used to ask for a manual
cross-reference of merged work against the backlog; no session ever did it,
which is how rows went stale unnoticed — so it is a command now.

Surface findings and close them **through the merge automation**, never by
editing rows. `done` is the merge's to write; a hand-written `done` is
indistinguishable from a real one afterwards, which is exactly what made an
earlier breakage invisible for weeks.

## Step 3 — Set the autonomy level

Confirm how autonomously to run (default from the state file, else ask once).

| Level | Clarify gate | Approval gate | Runs to |
|---|---|---|---|
| **L1 Supervised** | asks | hard stop after spec | you drive each gate |
| **L2 Batch** (recommended) | batches ALL questions + spec into ONE checkpoint | that one checkpoint | then straight to PR |
| **L3 Autonomous** | asks only if truly blocked | skipped | straight to PR |

Higher autonomy never bypasses the hard invariants: a failing test before any
fix, migrations referencing their spec ID, and same-change documentation sync.
Autonomy decides how often you stop, never what you may skip.

## Step 4 — Allocate the spec ID and route

1. Take the next free ID and **reserve it before work starts** — append it to the
   registry in the configured specs directory. Reserving after the fact is how
   two tasks end up claiming one number.
2. Reserve against the latest default branch, not your local copy: a parallel
   session may already have taken it.
3. Initialize `.claude/state/current-task.json` with the spec ID, autonomy, and
   `state: EXPLORE`.
4. Route: a new feature or change → the feature workflow. A bug or defect → the
   bug-fix workflow.
