# Feature-Parity Acceptance

## Current status

Automated feature-parity acceptance passed on 2026-07-14. The manual
TurboQuant/GGUF acceptance run is pending and remains a hard gate before shell
removal and final epic completion.

## Automated validation

```text
uv sync --locked              passed
uv run ruff format --check    17 files already formatted
uv run ruff check             passed
uv run ty check               passed
uv run pytest                 46 passed
git diff --check              passed
shell-fixture search          no matches in tests, spec, or pyproject.toml
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

Status: **PENDING**

The following hardware-intensive command must pass before Ticket 10 begins:

```bash
uv run llama-benchmark --turbo 4 --symmetric off --runs 3
```

Record the generated result-directory path and verify all four scenarios,
twelve measured rows, positive timings, consistent CSV/summary/log evidence,
and clean `llama-server` shutdown.
