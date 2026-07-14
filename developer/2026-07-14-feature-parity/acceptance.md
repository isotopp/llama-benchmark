# Feature-Parity Acceptance

## Current status

**COMPLETE** — the Python implementation has accepted feature parity, the
manual TurboQuant/GGUF run passed, and the shell implementation and its
dependent artifacts have been removed.

## Automated validation

```text
uv sync --locked              passed
uv run ruff format --check    17 files already formatted
uv run ruff check             passed
uv run ty check               passed
uv run pytest                 46 passed
git diff --check              passed
shell-fixture search          no matches in tests, spec, or pyproject.toml
uv tree                      one approved runtime dependency: httpx
tracked-artifact audit        no models, distributions, results, caches, or builds
current-project shell search  no matches outside intentional epic history
ignore checks                 model, server, results, logs, and .venv passed
```

## Acceptance-criterion coverage

| Story | Public coverage |
| --- | --- |
| Working-directory defaults | `tests/test_cli.py` invokes configuration after changing directories and covers default, relative, and absolute paths. |
| Preflight before artifacts | `tests/test_integration.py` runs against an occupied loopback endpoint and proves the output root is not created; a post-start HTTP failure retains evidence. |
| Startup diagnostics | `tests/test_server.py` executes short-log, 100-line, early-exit, and timeout child processes and verifies bounded diagnostics plus retained logs. |
| Concise runtime errors | `tests/test_integration.py` invokes the public module for server, HTTP, and filesystem failures; `tests/test_cli.py` proves unexpected exceptions remain visible. |
| Signal-safe cleanup | `tests/test_integration.py` sends `SIGTERM` and `SIGHUP` to real benchmark subprocesses; `tests/test_server.py` covers normal, keyboard, timeout, and kill-escalation paths. |
| Progress visibility | `tests/test_integration.py` verifies configuration, waiting/ready, measured-run tokens, and throughput; `tests/test_requests.py` proves warm-up and measured callbacks preserve ordering. |
| Benchmark comparability | Scenario, request, reporting, and end-to-end tests retain prompt order, request parameters, disabled caching, CSV meanings, statistics, raw evidence, and summary artifacts. |

## Accepted argparse difference

Hyphen-prefixed extra server arguments use the explicit form:

```bash
--server-arg=--threads --server-arg=8
```

Supporting the former separated `--server-arg --threads` form is not a parity
requirement.

## Manual TurboQuant gate

Status: **PASSED**

The maintainer ran this hardware-intensive command:

```bash
uv run llama-benchmark \
  --model ./models/qwen3.6-35b-a3b/qwen3.6-35b-a3b-q4_k_m.gguf \
  --turbo 3 \
  --symmetric off
```

Result directory:

```text
benchmark_results/20260714-200927-qwen3.6-35b-a3b-q4_k_m-turbo3-symmetric-off
```

The run used Turbo3 rather than the suggested Turbo4 mode and exceeded the
minimum run count. Inspection confirmed:

- four scenarios, twenty measured rows, and four warm-up rows;
- positive prompt tokens, prompt throughput, generated tokens, and generation
  throughput in every row;
- plausible measured medians ranging from 570.46 to 901.04 prompt tokens per
  second and 85.19 to 99.79 generation tokens per second;
- consistent `results.csv`, `summary.txt`, raw responses, and `server.log`;
- successful server cleanup, with port 8080 released after completion.

## Ordered ticket commits

1. `43797fc` — resolve working-directory defaults
2. `0117ed0` — preflight endpoint before artifacts
3. `34a60f0` — report startup diagnostics
4. `a9bbc6f` — report concise CLI errors
5. `54f987b` — clean up server on signals
6. `efe3883` — restore benchmark progress
7. `3da023c` — replace shell test fixtures
8. `9b2b816` — pass automated parity gate
9. `896610a` — pass manual TurboQuant run
10. `c64557e` — remove shell implementation
11. `973b8a7` — document the Python-only project

Ticket 12 records this final acceptance after all locked validation, dependency,
ignore, tracked-artifact, and shell-removal audits passed on 2026-07-14.
