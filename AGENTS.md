# Development Guide

## Purpose

This repository maintains a uv-managed Python benchmark application for a local TurboQuant-enabled llama.cpp server. Keep the tracked project small: source code and documentation belong in Git; models, compiled distributions, and generated measurements do not.

## Language

Use English for source code, comments, documentation, commit messages, test output, and user-facing messages emitted by the script.

## Supported environment

- macOS on Apple Silicon
- Python 3.12 or newer managed with uv
- A local TurboQuant/llama.cpp distribution under `llama/`
- Local GGUF models under `models/`

## Project conventions

- Keep application code in the `src/llama_benchmark/` package.
- Resolve default model, server, and result paths relative to the caller's working directory.
- Keep benchmark requests reproducible and record raw data before calculating summaries.
- Do not silently enable prompt reuse. A future cached-prompt benchmark must be an explicit, separately reported mode.
- Avoid changing benchmark prompts or defaults without documenting the comparability impact.

## Validation

Development validation uses uv, Ruff, ty, and pytest.

At minimum, run:

```bash
uv sync --locked
uv run ruff format --check
uv run ruff check
uv run ty check
uv run pytest
git check-ignore models/example.gguf
git check-ignore llama/turboquant-plus-tqp-v0.3.0/llama-server
git check-ignore benchmark_results/example/results.csv
```

The pytest suite uses a small Python HTTP fixture instead of loading a real
model. It binds only to the local loopback interface and writes results below
pytest's temporary directory.

For changes to request execution or statistics, use a small controlled run when practical and inspect `results.csv`, `summary.txt`, and `server.log` together.

## Repository hygiene

Never commit:

- GGUF models or model shards
- llama.cpp/TurboQuant executables and dynamic libraries
- benchmark results or server logs
- macOS metadata

Before committing, inspect `git status --short` and verify that only intended source or documentation files are staged. Do not modify or delete local models and distributions as part of routine code changes.
