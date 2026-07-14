# llama-benchmark

`llama-benchmark` is a uv-managed Python application that runs repeatable HTTP benchmarks against a local TurboQuant-enabled `llama-server`. It compares prompt processing and generation performance with Turbo3 or Turbo4 KV-cache quantization and symmetric or automatic asymmetric handling.

## Repository layout

The project expects this local layout:

```text
llama-benchmark/
├── pyproject.toml
├── uv.lock
├── src/llama_benchmark/
├── tests/
├── llama/
│   └── turboquant-plus-tqp-v0.3.0/
│       └── llama-server
├── models/
│   ├── qwen3.6-27b/
│   └── qwen3.6-35b-a3b/
└── benchmark_results/
```

The `llama/`, `models/`, and `benchmark_results/` directories are intentionally excluded from Git because they contain platform-specific binaries, very large model files, or generated results.

## Requirements

- macOS on Apple Silicon
- uv and Python 3.12 or newer
- A TurboQuant-enabled `llama-server` distribution at the path shown above
- At least one GGUF model below `models/`

## Running a benchmark

Prepare the locked environment and run the installed Python command. Defaults
are resolved from the current working directory at invocation time. From the
repository root, the command therefore uses
`llama/turboquant-plus-tqp-v0.3.0/llama-server` and the local
`models/qwen3.6-35b-a3b/qwen3.6-35b-a3b-q4_k_m.gguf` model:

```bash
uv sync --locked
uv run llama-benchmark \
  --turbo 4 \
  --symmetric off
```

Use `--model` or `--server` to override either default. Paths supplied on the
command line may be relative to the current working directory or absolute.
`--output-dir` defaults to `benchmark_results/` below that same directory.

Extra server options may be repeated. When a value starts with a hyphen, use
the explicit equals-sign form required by `argparse`:

```bash
uv run llama-benchmark \
  --turbo 4 \
  --symmetric off \
  --server-arg=--threads \
  --server-arg=8
```

Use `--help` to see all settings:

```bash
uv run llama-benchmark --help
```

The command prints the selected configuration, server readiness, and token
throughput for each warm-up and measured request. Expected operational failures
produce a concise `Error: ...` message without a traceback; retained artifacts
and the server-log tail provide additional diagnostics.

Results are written to a timestamped directory containing:

- `prompts/`: the exact generated scenario prompts;
- `raw/`: each raw JSON response;
- `results.csv`: warm-up and measured request data;
- `summary.txt`: aggregate statistics and artifact paths;
- `server.log`: complete server output.

## Benchmark behavior

Each scenario performs one warm-up followed by five measured runs. Prompt caching is disabled and every request receives a unique nonce, so measured requests are independent. Turbo3 or Turbo4 still controls the KV-cache representation used within each request.

`--symmetric on` sets `TURBO_AUTO_ASYMMETRIC=0`. `--symmetric off` leaves TurboQuant automatic asymmetric handling enabled.

## Development and acceptance

Run the automated quality gate with:

```bash
uv sync --locked
uv run ruff format --check
uv run ruff check
uv run ty check
uv run pytest
```

Changes that affect server execution, requests, or reporting also require a
manual, hardware-intensive TurboQuant run. It loads the real GGUF model and is
not part of pytest:

```bash
uv run llama-benchmark --turbo 4 --symmetric off --runs 3
```

Afterward, inspect all four scenarios in `results.csv`, confirm positive and
plausible token counts and throughput, compare `summary.txt` and `server.log`
with the CSV and raw responses, and confirm that no `llama-server` remains.

## Local data and Git

Do not force-add GGUF files, llama.cpp binaries, dynamic libraries, or benchmark outputs. Before committing, verify the staged files with:

```bash
git status --short
git diff --cached --stat
```
