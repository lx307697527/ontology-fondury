#!/usr/bin/env bash
# SessionStart hook — say which session logs are still only half written, and
# which have never reached git.
#
# Thin on purpose. What counts as an unwritten judgment layer, what counts as
# untracked, and which failures are preconditions rather than findings all live
# in the harness package where its suite can reach them.
#
# Receives hook JSON on stdin; unused, and deliberately not drained — the harness
# takes no input here and a `cat` would only add a way to hang.
#
# NEVER FAILS THE SESSION. `|| true` is not a fail-open: nothing is being
# guarded, this is a notice. A SessionStart hook that exits non-zero breaks EVERY
# session in every container — a far larger failure than the one it would be
# reporting. The command's own exit 2 (repository unreadable) still prints its
# reason, which is the part a human acts on.
set -uo pipefail
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$HOOK_DIR/../.." && pwd)}"
harness log unfilled --repo "$REPO_ROOT" || true
