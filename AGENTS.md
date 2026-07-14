# Development Guide

## Purpose

This repository maintains a portable Bash benchmark driver for a local TurboQuant-enabled llama.cpp server. Keep the tracked project small: source code and documentation belong in Git; models, compiled distributions, and generated measurements do not.

## Language

Use English for source code, comments, documentation, commit messages, test output, and user-facing messages emitted by the script.

## Supported environment

- macOS on Apple Silicon
- The system Bash 3.2 and newer Bash releases
- A local TurboQuant/llama.cpp distribution under `llama/`
- Local GGUF models under `models/`

Preserve Bash 3.2 compatibility. In particular, do not use associative arrays, `mapfile`, `&>`, case conversion expansions, or unconditional expansion of empty arrays while `set -u` is active.

## Project conventions

- Keep `run-benchmark.sh` executable and valid under `bash -n`.
- Resolve bundled assets relative to the script directory, not the caller's working directory.
- Quote paths and array expansions because model and binary paths may contain spaces.
- Preserve `set -Eeuo pipefail`; handle commands whose nonzero status is expected explicitly.
- Keep benchmark requests reproducible and record raw data before calculating summaries.
- Do not silently enable prompt reuse. A future cached-prompt benchmark must be an explicit, separately reported mode.
- Avoid changing benchmark prompts or defaults without documenting the comparability impact.

## Validation

Development validation requires ShellCheck, ShellSpec, and Python 3.

At minimum, run:

```bash
bash -n run-benchmark.sh
./run-benchmark.sh --help
shellcheck --shell=bash run-benchmark.sh spec/support/fake-llama-server spec/run_benchmark_spec.sh
shellspec
git check-ignore models/example.gguf
git check-ignore llama/turboquant-plus-tqp-v0.3.0/llama-server
git check-ignore benchmark_results/example/results.csv
```

The ShellSpec suite uses a small Python HTTP fixture instead of loading a real
model. It binds only to the local loopback interface and writes results below
ShellSpec's temporary directory.

For changes to request execution or statistics, use a small controlled run when practical and inspect `results.csv`, `summary.txt`, and `server.log` together.

## Repository hygiene

Never commit:

- GGUF models or model shards
- llama.cpp/TurboQuant executables and dynamic libraries
- benchmark results or server logs
- macOS metadata

Before committing, inspect `git status --short` and verify that only intended source or documentation files are staged. Do not modify or delete local models and distributions as part of routine code changes.
