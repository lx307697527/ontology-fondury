---
name: bug-fix
description: The mandatory workflow for fixing bugs, defects, regressions, or "X is broken / not working / wrong output" reports. Use whenever incorrect behavior is reported, an error is pasted, or something is asked to be fixed — even if the word "bug" is never used. Do NOT use for new features or behavior changes.
---

# Bug Fix

```
EXPLORE → REPRODUCE → ROOT CAUSE → FIX → REGRESSION → SPEC BACKFILL → COMMIT
```

**The prime directive: no failing reproduction test, no code change.** If you
cannot reproduce the bug in a test, you do not understand it yet, and "fixing" it
is guessing. The test is also the only thing that will still be defending this
behaviour in six months, when everyone has forgotten the conversation.

## State 1 — EXPLORE

Root map → module map → only the files they point at. Also read the incident
ledger for similar past bugs: a recurrence is a different and more serious
finding than a one-off, because it means the first fix addressed a symptom.

Read the spec that defined the intended behaviour. **The bug is a divergence from
the spec, not from your idea of what the code should do** — and when the spec is
silent, that silence is itself the finding.

If you cannot reproduce it from what you have — exact input, environment,
expected versus actual — ask. At most three rounds, each question carrying its
own default.

## State 2 — REPRODUCE (mandatory failing test)

Write a test that fails **because of the bug**. Run it and confirm it fails for
the reported reason, not for a typo or a missing import — a test that fails for
the wrong reason will pass for the wrong reason too, and you will believe you
fixed something.

## State 3 — ROOT CAUSE

Reserve the incident ID and write the incident file from the template. Its
frontmatter is machine-read — module, root cause category, and whether this
recurs — so fill it honestly. Reaching for "other" to save thirty seconds is what
makes the reflection loop blind, and the reflection loop is the only thing that
turns a pile of incidents into a rule.

Then append the matching row to the incident ledger, and check for recurrence:
the same module and category, or the same MECHANISM in a different module. If you
find one, say so in the file — that link is the signal the weekly reflection
clusters on.

Distinguish, because the fix differs:

- **Implementation bug** — the code diverged from the spec. Fix the code.
- **Spec bug** — the spec was wrong or silent. Confirm the intended behaviour
  with whoever owns it BEFORE fixing, then update the spec in the same change.
  Fixing code against a spec nobody corrected just moves the disagreement.

## State 4 — FIX

The minimal change that makes the reproduction test pass. Resist drive-by
refactors: they make the diff hard to review and hide the one line that mattered.
Unrelated debt you spot goes in the incident file, where it will be found again.

## State 5 — REGRESSION

Run the module's full suite plus the suites of anything the module maps list as
depending on it. The reproduction test stays in the suite permanently — it is now
this bug's regression guard, and deleting it later re-opens the bug silently.

## State 6 — SPEC BACKFILL

If the root cause was a spec bug, update the spec's acceptance criteria in the
same change. If a module map's stated invariants turned out to be wrong, fix
them — a map that survives a bug it should have prevented will mislead the next
reader too.

## State 7 — COMMIT

Use the commit workflow, with a `fix(...)` type and the incident ID. The change
must show the reproduction test in its diff: a fix nobody can see being tested is
a fix nobody can trust.
