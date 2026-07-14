# Python Migration Acceptance

## Status

Tickets 1 through 11 are complete. The supported implementation is the
uv-managed Python 3.12 package in `src/llama_benchmark/`. The former shell
implementation has been replaced by a temporary deprecation wrapper that
delegates to `uv run llama-benchmark`.

## Completed validation

The final locked-environment acceptance run completed successfully on
2026-07-14:

```text
uv sync --locked              passed
uv run ruff format --check    15 files already formatted
uv run ruff check             passed
uv run ty check               passed
uv run pytest                 36 passed
git diff --check              passed
repository ignore checks      passed
```

The pytest suite covers CLI behavior, all four scenarios, request construction,
server lifecycle and cleanup, HTTP success and failure boundaries, raw-response
preservation, statistics, reports, and the complete fake-server workflow.

## Dependency audit

Direct dependencies match the approved policy:

- runtime: `httpx`;
- development: pytest, Ruff, and ty.

The remaining installed packages are transitive dependencies of those approved
tools. No additional direct dependency was introduced.

## Migration decisions

- `argparse`, `subprocess`, dataclasses, `pathlib`, `csv`, `json`, and
  `statistics` provide the non-HTTP implementation.
- Successful responses with malformed JSON or invalid timing data are fatal
  data-quality errors instead of silently becoming zero measurements.
- Summary whitespace is idiomatic Python output; CSV columns, statistical
  meanings, measured-token reporting, and artifact roles remain equivalent.
- `run-benchmark.sh` remains temporarily as a deprecation wrapper for existing
  callers. It contains no benchmark implementation.
- ShellSpec was removed after its observable coverage was represented in
  pytest. The fake HTTP server remains as a pytest integration boundary.

## Controlled execution

The end-to-end pytest starts a real child process, communicates over loopback
HTTP, executes all four scenarios with three measured requests each, writes
twelve raw responses plus CSV, summary, prompts, and server log, and verifies
child cleanup.

A real GGUF/TurboQuant run was not launched automatically during migration
acceptance because it is hardware-intensive and can run for a long time. The
local models and distribution were not modified. A maintainer can perform the
hardware acceptance run with:

```bash
uv run llama-benchmark --turbo 4 --symmetric off --runs 3
```

Afterward, inspect `results.csv`, `summary.txt`, and `server.log` together in
the newly created `benchmark_results/` directory.

## Commit sequence

```text
055b1f1  Ticket 1: capture migration baseline
fff7e54  Ticket 2: decide dependency policy
b5b11ee  Ticket 3: initialize uv package
efd1413  Ticket 4: implement CLI configuration
4a97b46  Ticket 5: generate benchmark scenarios
5046aaf  Ticket 6: manage llama-server lifecycle
776e86b  Ticket 7: execute benchmark requests
925978f  Ticket 8: write benchmark reports
da90214  Ticket 9: complete equivalence workflow
8d9ded7  Ticket 10: switch supported entry point
```
