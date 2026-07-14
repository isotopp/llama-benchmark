# llama-benchmark

`llama-benchmark` runs repeatable HTTP benchmarks against a local TurboQuant-enabled `llama-server`. It compares prompt processing and generation performance with Turbo3 or Turbo4 KV-cache quantization and symmetric or automatic asymmetric handling.

## Repository layout

The project expects this local layout:

```text
llama-benchmark/
├── run-benchmark.sh
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
- Bash 3.2 or newer
- `curl`, `jq`, and standard Unix command-line tools
- A TurboQuant-enabled `llama-server` distribution at the path shown above
- At least one GGUF model below `models/`

## Running a benchmark

From the repository root, run the script. By default it uses the bundled
`llama/turboquant-plus-tqp-v0.3.0/llama-server` and the local
`models/qwen3.6-35b-a3b/qwen3.6-35b-a3b-q4_k_m.gguf` model:

```bash
./run-benchmark.sh \
  --turbo 4 \
  --symmetric off
```

Use `--model` or `--server` to override either default. Paths supplied on the
command line may be relative to the current working directory or absolute.

Use `--help` to see all settings:

```bash
./run-benchmark.sh --help
```

By default, results are written below `benchmark_results/` in a timestamped directory. Each run contains the generated prompts, raw server responses, a CSV data file, the server log, and a text summary.

## Benchmark behavior

Each scenario performs one warm-up followed by five measured runs. Prompt caching is disabled and every request receives a unique nonce, so measured requests are independent. Turbo3 or Turbo4 still controls the KV-cache representation used within each request.

`--symmetric on` sets `TURBO_AUTO_ASYMMETRIC=0`. `--symmetric off` leaves TurboQuant automatic asymmetric handling enabled.

## Local data and Git

Do not force-add GGUF files, llama.cpp binaries, dynamic libraries, or benchmark outputs. Before committing, verify the staged files with:

```bash
git status --short
git diff --cached --stat
```
