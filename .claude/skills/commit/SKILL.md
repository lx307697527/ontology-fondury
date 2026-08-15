---
name: commit
description: Generate and create git commits. Use whenever committing staged changes, when asked to "commit this", or at the COMMIT state of the feature and bug-fix workflows. Enforces Conventional Commits plus spec/bug ID traceability.
---

# Commit

## Procedure

1. `git status` and `git diff --staged` — read what is **actually** being
   committed. Staging is a claim about scope, and it drifts: a base branch that
   moved while you worked can sweep in files that are not yours.
2. Identify the spec context: the active spec or incident ID. If neither exists
   and the change is non-trivial, **stop** — untraceable work is the thing the
   ID exists to prevent. Trivial chores and documentation may omit it.
3. Split unrelated changes into separate commits. Things that serve one step of
   one spec may share a commit; things that merely happened at the same time may
   not.

## Format

```
<type>(<scope>): <imperative summary, ≤72 chars> [SPEC-ID]

- What changed and why (1–4 bullets, referencing acceptance criteria where they apply)
- Migration / schema change: <name> (if any)
- Docs updated: <paths>, or "no-doc-impact: <reason>"
```

Types: `feat` `fix` `refactor` `test` `docs` `chore` `perf` `ci` `build`.
Scope: the module name from the root map.

Write the body for someone who will read it in a year with no memory of today —
which includes you. "Why" survives; "what" is already in the diff.

## The pull-request title is governed, not cosmetic

Under squash-merge the title BECOMES the commit on the default branch, and the
merge automation extracts the spec ID and phase from it to close the backlog. A
title without an ID cannot be linked, and the backlog will not close.

- Title: `<type>(<scope>): <summary> [SPEC-ID]`, plus the phase when there is one.
- **Check what the title will actually close before you write it.** The
  automation reads the branch name too, so a title with no phase is not
  automatically safe. This is thirty seconds of checking against an outcome that
  cannot be undone cleanly: a wrongly-closed row looks exactly like a correctly
  closed one afterwards.
- Body: 2–4 prose sentences saying what, why, and the blast radius. Linking the
  spec is not a substitute for summarising it — the reviewer is deciding whether
  to read further.

## Rules

- Never commit failing tests, **except** the intentional red commit that opens a
  test-first cycle — which must say so in its subject, because that is what the
  test-amendment guard and every human reader key on.
- Never include secrets, environment files, or generated artifacts.
- Do not amend or force-push a shared branch. Someone may already have read it,
  and a rewritten branch makes their review a comment on something that no
  longer exists.
