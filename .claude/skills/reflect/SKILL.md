---
name: reflect
description: The weekly self-evolution loop. Use when asked to "run the reflection", "distill rules from bugs", "review recurring incidents", or on a schedule. Clusters the incident ledger and fix history; recurrences become rule proposals via pull request; also prunes stale rules and pushes active ones toward mechanical enforcement.
---

# Reflect

Turn recurring failures into durable rules, keep the rule set small and alive,
and push rules toward being machines rather than prose. Output is always a
**proposal** — reflect never writes a rule straight into a map, because a rule
nobody reviewed is a rule nobody agreed to.

## Trigger

Weekly, paired with the drift audit. The scheduled agent that runs this lives
outside the repository, so the repository cannot see whether it still exists —
which is why the freshness workflow ships alongside and goes red when reports
stop arriving. **A routine that quietly stopped looks exactly like a quiet week.**

## Step 1 — Gather

1. Read the incident ledger and every incident file.
2. Read the backlog and note any phase bounced three or more times. Repeated
   bounces signal a fuzzy spec or under-scoped work — a process finding, not a
   code one, and worth reporting separately so it does not get lost among bugs.
3. `git log --grep='^fix('` since the last run. Every fix should reference an
   incident that exists. **Fixes without one are a process leak**: the loop can
   only cluster what was written down, so an unrecorded fix is a lesson that
   cannot recur into a rule. List them and file the backfill.
4. Read the current rules and when each last fired.

## Step 2 — Cluster (mechanical first, then judgment)

1. Mechanical: group by (module, root cause category) and by recurrence links.
2. Judgment: for each mechanical cluster of two or more, READ the incidents and
   decide whether they truly share a root cause or merely a category. Then look
   ACROSS modules for the same mechanism in different places — that is the more
   valuable pattern and the one the mechanical pass cannot see.
3. Be honest that this step cannot be mechanised. Err toward proposing: the
   review is the filter, and a proposal costs a conversation while a missed
   pattern costs the next incident.

## Step 3 — Propose (for each confirmed cluster)

Open one change containing:

1. The rule file, from the template, listing the incidents it was born from.
2. The one-line rule placed where readers will meet it: a module rule in that
   module's map, a global rule in the root map. **Respect the global cap** — if
   it is full, this change must also retire or graduate one. A rule list nobody
   can hold in their head is a rule list nobody follows.
3. An answer, in the description, to: *can this be a lint rule, a check, or a
   type instead of prose?* If yes, include the check in the same change. **Prose
   that could be a machine should be born a machine** — prose degrades silently,
   a check fails loudly.
4. Approval routed by tier: a module rule to its owner, a global rule or anything
   that adds a check to whoever owns the root map and CI.

## Step 4 — Graduate and prune

For each active rule:

- **Graduate**: can it move up the ladder now — a convention into a lint rule, an
  invariant into a type or a check? On graduation, DELETE the prose and replace
  it with a pointer to the check. Leaving both means two things to keep in step,
  and they will drift.
- **Prune**: not triggered in six months, or the code it guarded is gone →
  propose retiring it. An unfireable rule is not free: it takes up room in the
  cap and teaches readers the list is decorative.
- Update the last-fired date for any rule that demonstrably caught something,
  with the evidence.

## Step 5 — Report

Write the report to the configured reports directory, named for the date:

```markdown
# Reflect YYYY-MM-DD
## Incidents since last run: N (M undocumented fixes — backfill filed)
## Clusters found
- (module, category) ×k → rule proposed | judged coincidental because …
## Proposals opened
## Graduations / prunes proposed
## Rule budget: X of the cap
```

Keep it under forty lines. Comment the summary on the standing audit issue and
tick this box; the issue closes once the drift audit has run too.
