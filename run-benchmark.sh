#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
printf '%s\n' 'Warning: run-benchmark.sh is deprecated; use uv run llama-benchmark.' >&2
exec uv run --directory "$SCRIPT_DIR" llama-benchmark "$@"
