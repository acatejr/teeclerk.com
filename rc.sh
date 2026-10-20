#!/usr/bin/env bash
# Relaunch Claude Code in this repo, continuing the most recent conversation.
# Exit the running session first (/exit or Ctrl+D), then run ./rc.sh.
# Extra arguments are passed through to claude.
set -euo pipefail

cd "$(dirname "$0")"
exec claude --continue "$@"
