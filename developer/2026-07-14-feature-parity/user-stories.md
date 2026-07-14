# Python Feature Parity

## Goal

Bring the Python implementation to operational feature parity with the former
shell implementation. After parity is demonstrated, remove the deprecated shell
entry point and every shell-only artifact, then update user and contributor
documentation to describe a Python-only project.

Exact source structure and incidental output formatting do not need to match the
shell implementation. Parity means preserving the useful user-visible behavior,
failure safety, diagnostics, benchmark comparability, and generated artifacts.

## User story 1: Report concise runtime errors

As a user, I want runtime failures reported as concise command-line errors so
that I can understand and correct a failed benchmark without reading a Python
traceback.

### Acceptance criteria

- Expected startup, process, HTTP, response-validation, filesystem, and report
  failures produce a concise error on standard error.
- Expected failures return a nonzero exit status without printing a traceback.
- Error messages identify the failed operation and relevant resource, endpoint,
  status, or file when available.
- Unexpected programmer errors are not silently swallowed.
- pytest covers representative server-startup, request, and filesystem errors
  through the public CLI.

## User story 2: Terminate the server on process signals

As a user, I want the Python benchmark to terminate and reap its child
`llama-server` when the benchmark receives an interruption or termination signal
so that failed and cancelled runs do not leave orphaned servers behind.

### Acceptance criteria

- Normal completion terminates and reaps the child server.
- Exceptions and keyboard interruption terminate and reap the child server.
- `SIGTERM`, `SIGHUP`, and other supported termination paths trigger orderly
  child cleanup before the benchmark exits.
- Cleanup escalates from terminate to kill after a bounded grace period.
- Signal handling does not hide the original exit reason.
- Subprocess tests prove that the fake child is no longer running after every
  covered termination path.

## User story 3: Avoid result directories for rejected runs

As a user, I want preflight checks completed before a timestamped result
directory is created so that rejected benchmarks do not leave empty or
misleading measurement directories.

### Acceptance criteria

- An occupied health endpoint is detected before creating the run directory.
- Configuration and other non-mutating preflight checks run before artifact
  creation where practical.
- A run that is rejected before server startup leaves no new timestamped result
  directory.
- Once execution begins, partial evidence that helps diagnose a failed run is
  retained deliberately rather than deleted silently.
- pytest covers both rejected preflight and post-start failure behavior.

## User story 4: Show useful server startup diagnostics

As a user, I want the most relevant server-log lines included when
`llama-server` exits during startup so that model-loading and configuration
failures are immediately visible.

### Acceptance criteria

- Early child exit reports the process exit status.
- The error includes up to the last 80 available lines from `server.log`.
- Startup timeout errors identify the endpoint and timeout duration.
- The complete log remains available in the result directory after a
  post-startup failure.
- Tests cover a short log, a log longer than 80 lines, early exit, and startup
  timeout.

## User story 5: Resolve local defaults from the working directory

As a user, I want default model, server, and output paths derived from my current
working directory so that the command behaves predictably from the project
layout without depending on where the Python package source is installed.

### Acceptance criteria

- The default model is
  `./models/qwen3.6-35b-a3b/qwen3.6-35b-a3b-q4_k_m.gguf` relative to the current
  working directory.
- The default server is
  `./llama/turboquant-plus-tqp-v0.3.0/llama-server` relative to the current
  working directory.
- The default output root is `./benchmark_results` relative to the current
  working directory.
- Explicit relative paths continue to resolve from the current working
  directory, while absolute overrides remain unchanged.
- Tests execute the CLI from multiple working directories and do not depend on
  the source-package location.

## User story 6: Preserve benchmark progress visibility

As a user, I want useful startup configuration and per-run progress printed
during a benchmark so that I can see what is running and distinguish slow work
from a stalled command.

### Acceptance criteria

- Before startup, the command prints the selected model, cache type, symmetry
  mode, context, long-prompt target, run counts, and output directory.
- Startup readiness produces visible bounded progress or a clear waiting
  message.
- Every warm-up and measured request reports its scenario, phase, run number,
  prompt tokens and throughput, and generated tokens and throughput.
- Progress output does not alter CSV, raw JSON, or summary contents.
- Tests cover representative progress output without relying on terminal-only
  behavior.

## User story 7: Confirm real TurboQuant operation manually

As a maintainer, I want a clearly documented manual TurboQuant/GGUF acceptance
run so that fake-server equivalence is supplemented by validation against the
real local server and model.

### Acceptance criteria

- The documentation provides the exact manual command using the repository's
  default model and server layout.
- The acceptance checklist reminds the maintainer that this test is manual,
  hardware-intensive, and must be run before declaring the epic complete.
- The maintainer inspects `results.csv`, `summary.txt`, and `server.log`
  together.
- The checklist verifies plausible prompt and generation token counts,
  throughput values, all four scenarios, and clean server shutdown.
- The manual result is recorded as pass, fail, or explicitly pending; it is not
  implied by the fake-server pytest suite.

### Manual reminder

Before completing this epic, run:

```bash
uv run llama-benchmark --turbo 4 --symmetric off --runs 3
```

Then inspect the newly created result directory and confirm that no
`llama-server` process remains.

## User story 8: Remove the shell implementation and artifacts

As a maintainer, I want the obsolete shell version and shell-only support files
removed after parity is established so that the repository has one supported
implementation and one test strategy.

### Acceptance criteria

- `run-benchmark.sh` is removed after Stories 1 through 7 are accepted.
- Shell-only test launchers, fixtures, configuration, and validation commands
  are removed or replaced with Python equivalents.
- Fake server, early-exit, and stalled-process fixtures needed by pytest are
  implemented without shell scripts.
- ShellCheck and ShellSpec are no longer project requirements.
- No documentation or test refers to the removed shell entry point.
- A repository search confirms that no obsolete shell artifact or migration
  instruction remains.
- Python tests retain equivalent coverage after the deletion.

## User story 9: Document the Python-only project

As a user and contributor, I want `README.md` and `AGENTS.md` to describe the
final Python-only implementation so that setup, operation, development, and
validation instructions are accurate.

### Acceptance criteria

- `README.md` presents uv and `uv run llama-benchmark` as the only supported
  setup and execution workflow.
- `README.md` documents working-directory-relative defaults, result artifacts,
  failure behavior, progress output, and the manual TurboQuant acceptance run.
- `AGENTS.md` describes the `src/` package, Python compatibility, TDD workflow,
  and the required Ruff, ty, and pytest commands.
- `AGENTS.md` retains repository-hygiene rules for models, distributions,
  results, logs, caches, environments, and build output.
- Neither document describes Bash compatibility, ShellCheck, ShellSpec, or a
  shell wrapper.

## Explicit non-goal: argparse server arguments

The difference in how `argparse` handles `--server-arg` values beginning with a
hyphen is accepted and will not be addressed in this epic. Users may pass such
values with the unambiguous form:

```bash
--server-arg=--threads --server-arg=8
```

This syntax must be documented, but accepting the former separated
`--server-arg --threads` form is not a feature-parity requirement.

## Completion criteria

The epic is complete when the automated parity tests pass, the real TurboQuant
run has been performed and recorded or is visibly marked pending, the shell
implementation and shell-only artifacts are gone, `README.md` and `AGENTS.md`
describe only the Python workflow, and these commands pass:

```bash
uv sync --locked
uv run ruff format --check
uv run ruff check
uv run ty check
uv run pytest
git diff --check
```
