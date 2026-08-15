#!/usr/bin/env bash
# SessionEnd hook — write this session's work log and distilled transcript.
#
# Thin on purpose: every decision lives in the harness package, where its suites
# can reach it. Guard logic must not live in shell — a decision embedded in an
# untested hook is a decision nobody can prove works.
#
# NEVER FAILS THE SESSION. `|| true` is deliberate and is not a fail-open,
# because nothing here is being guarded: this is a logger. A teardown that dies
# would cost the log AND the clean exit — the record is already the thing that
# was lost.
#
# Receives the hook payload as JSON on stdin and passes it straight through.
set -uo pipefail
REPO="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
harness log session-end --repo "$REPO" || true
