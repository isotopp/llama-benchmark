# Convert llama-benchmark to Python: Implementation Tickets

## Working rules

- Use the TDD skill for every behavior-changing ticket.
- Implement one observable behavior at a time using red-green-refactor cycles.
- Use the git-commit skill and create a thematic commit after each ticket, or
  after a tightly coupled group of tickets when the repository cannot otherwise
  remain usable.
- Do not add dependencies beyond uv, Ruff, ty, and pytest without completing
  Ticket 2 and receiving explicit approval.
- Keep the shell implementation and its tests available as the behavioral
  reference until equivalent pytest coverage exists.
- Keep models, local llama.cpp distributions, generated results, logs, caches,
  virtual environments, and build output out of Git.

## Ticket 1: Capture the migration baseline

### Objective

Record the current shell application's public behavior and artifact contract so
that the Python migration can be assessed for equivalence rather than source
similarity.

### Work

- Run the existing ShellCheck and ShellSpec validation.
- Inventory the CLI options, defaults, validation rules, exit behavior, and
  user-facing errors.
- Inventory the four benchmark scenarios and their generation limits.
- Document the prompt, request JSON, CSV, raw-response, server-log, and summary
  contracts that must remain comparable.
- Identify behaviors that may intentionally change and mark them as decisions
  requiring approval.

### Acceptance criteria

- A concise migration contract exists beside these epic documents.
- Every current public CLI option and generated artifact is accounted for.
- Baseline ShellSpec tests pass without modification.
- No production behavior changes in this ticket.

### Validation

```bash
shellcheck --shell=bash run-benchmark.sh spec/support/fake-llama-server spec/run_benchmark_spec.sh
shellspec
```

### Depends on

None.

## Ticket 2: Decide the dependency policy

### Objective

Agree on whether the migration should use only the Python standard library or
adopt optional packages for the CLI, HTTP client, process management, or other
concerns.

### Work

- Identify each proposed dependency and the capability it would provide.
- Compare it with the standard-library or small in-project alternative.
- Describe effects on portability, typing, testability, maintenance, and CLI
  compatibility.
- Present the recommendation and alternatives to the user.
- Record the user's decisions before adding any optional dependency.

### Acceptance criteria

- The approved dependency set is documented.
- No unapproved dependency has been added to the project.
- Rejected dependencies and the selected alternatives are recorded briefly.

### Validation

Review `pyproject.toml` and `uv.lock` after Ticket 3 to confirm that only the
approved dependency set is present.

### Depends on

Ticket 1.

## Ticket 3: Initialize the uv package

### Objective

Create the installable Python project and its quality-tool configuration without
yet replacing benchmark behavior.

### Work

- Initialize the repository with uv's `--package` structure.
- Choose and declare the supported Python version.
- Create the `src/` package and a console-script entry point.
- Add Ruff, ty, and pytest as development dependencies with uv.
- Add only the optional dependencies approved in Ticket 2.
- Configure Ruff, ty, and pytest in `pyproject.toml` where supported.
- Update ignore rules for Python, uv, test, type-checker, coverage, and build
  artifacts.
- Add a first pytest that invokes the public entry point and verifies `--help`.
- Keep the shell entry point operational during the migration.

### Acceptance criteria

- `uv sync` creates a reproducible development environment from `uv.lock`.
- The package imports from the `src/` layout.
- The installed console command displays help and exits successfully.
- The initial test was observed failing before the minimal implementation made
  it pass.
- The shell benchmark remains usable.

### Validation

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest
shellspec
```

### Depends on

Tickets 1 and 2.

## Ticket 4: Implement CLI configuration and validation

### Objective

Provide an idiomatic Python CLI with behavior equivalent to the current shell
interface.

### Work

- Add one failing pytest for one CLI behavior at a time.
- Implement model and server defaults relative to the project installation or
  another explicitly agreed resource strategy.
- Implement Turbo mode, symmetry mode, host, port, context, long-token, run,
  warm-up, output-directory, and repeated server-argument options.
- Preserve clear validation for files, executability, enum values, unsigned
  decimal input, numeric ranges, and context capacity.
- Define stable Python configuration types after the public behavior is covered.
- Test execution from a working directory other than the repository root.

### Acceptance criteria

- Every baseline CLI option and validation rule has pytest coverage.
- Defaults and overrides behave consistently from arbitrary working
  directories.
- Errors are concise, user-facing, and return a nonzero exit status.
- Numeric values with leading zeroes are interpreted as decimal.
- No server process is started by CLI validation tests.

### Validation

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest
```

### Depends on

Ticket 3.

## Ticket 5: Generate reproducible benchmark scenarios and requests

### Objective

Generate the four benchmark prompts and deterministic request bodies through
Python while preserving benchmark comparability.

### Work

- Add pytest coverage for each scenario before implementing it.
- Reproduce the short-generation, numeric-analysis, code-generation, and
  long-context tasks.
- Preserve the long-context record-count and anomaly rules or document and
  approve any deliberate comparability change.
- Generate a unique nonce for every request.
- Preserve deterministic inference parameters, disabled prompt caching, and
  non-streaming completion requests.
- Write prompts and request data as UTF-8 without loading unnecessary large
  intermediate structures into memory.

### Acceptance criteria

- All four prompts are covered by behavioral tests.
- Repeated requests contain different nonces but otherwise stable benchmark
  parameters.
- `cache_prompt` remains false.
- Long-context generation respects the requested approximate token target and
  minimum record count.
- Prompt changes with comparability impact are explicitly documented.

### Validation

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest
```

### Depends on

Ticket 4.

## Ticket 6: Manage the llama-server lifecycle

### Objective

Start, monitor, and stop the configured `llama-server` safely from Python.

### Work

- Add controlled subprocess and loopback-server tests before implementation.
- Construct the server command with the configured model, Turbo cache, context,
  host, port, and extra arguments.
- Apply the symmetric/asymmetric environment behavior.
- Refuse to start when the configured endpoint is already serving.
- Wait for health with a bounded timeout and detect early process exit.
- Record the command and server output in `server.log`.
- Terminate and reap the child on success, failure, interruption, and timeout.

### Acceptance criteria

- Server startup, readiness, early exit, occupied port, timeout, and cleanup are
  covered by pytest.
- No test loads a real model.
- No test leaves a child process running.
- Extra server arguments and symmetry environment handling are verified through
  observable fake-server behavior.

### Validation

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest
```

### Depends on

Tickets 4 and 5.

## Ticket 7: Execute benchmark HTTP requests

### Objective

Run warm-up and measured completion requests and preserve every raw server
response before interpreting it.

### Work

- Add tests against the controlled fake HTTP server one behavior at a time.
- Implement health and completion requests with explicit timeouts.
- Write each raw response before extracting timing values.
- Treat transport failures, non-200 responses, malformed JSON, and missing or
  invalid timing data as clear benchmark failures.
- Run the configured number of warm-up and measured requests for every
  scenario.
- Keep warm-up results distinguishable from measured results.

### Acceptance criteria

- Successful, transport-error, HTTP-error, invalid-JSON, and invalid-timing
  responses have pytest coverage.
- Every accepted response has a corresponding raw file.
- Warm-up and measured run counts match the CLI configuration.
- Requests remain independent and deterministic apart from their nonce.

### Validation

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest
```

### Depends on

Ticket 6.

## Ticket 8: Write CSV measurements and statistical summaries

### Objective

Produce durable benchmark artifacts and equivalent summary statistics from the
measured responses.

### Work

- Add tests for artifact creation and each statistical rule before
  implementation.
- Write the CSV header and warm-up/measured rows with stable column meanings.
- Calculate total duration, median, nearest-rank P95, mean, minimum, and maximum
  for prompt and generation throughput.
- Preserve measured token-count reporting.
- Write the human-readable summary and print it to standard output.
- Use safe temporary-file and replacement patterns where partial artifacts
  would otherwise be misleading.

### Acceptance criteria

- Tests cover odd and even medians, P95 index boundaries, empty data, and
  decimal values.
- A controlled full run creates prompts, raw JSON, `results.csv`, `summary.txt`,
  and `server.log` in one timestamped directory.
- Warm-up rows remain in raw measurements but do not influence summary
  statistics.
- Artifact contents are equivalent to the migration contract from Ticket 1.

### Validation

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest
```

### Depends on

Ticket 7.

## Ticket 9: Complete end-to-end equivalence testing

### Objective

Demonstrate that the Python command supports the complete benchmark workflow
without a real model server.

### Work

- Build a pytest fake-server integration fixture around public process and HTTP
  boundaries.
- Run all four scenarios with the minimum valid measured-run count.
- Verify CLI output, server arguments, environment behavior, prompts, request
  counts, raw responses, CSV rows, summary values, logging, and cleanup.
- Compare the observable outputs with the baseline contract and ShellSpec suite.
- Resolve or explicitly approve every behavioral difference.

### Acceptance criteria

- The end-to-end pytest passes on the supported macOS environment.
- The integration test uses only loopback networking and temporary directories.
- No real GGUF model or TurboQuant distribution is required.
- All agreed baseline behaviors are represented in pytest.
- Any intentional differences are documented and approved.

### Validation

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest
shellspec
```

### Depends on

Tickets 4 through 8.

## Ticket 10: Switch the supported entry point to Python

### Objective

Make the uv-installed Python command the documented benchmark interface after
equivalence is established.

### Work

- Update user documentation with uv setup and Python CLI usage.
- Update `AGENTS.md` with the Python development and validation workflow.
- Decide whether `run-benchmark.sh` should be removed or retained temporarily
  as a deprecation wrapper; obtain approval if this was not settled in Ticket 1.
- Remove ShellCheck and ShellSpec instructions only when their covered behavior
  exists in pytest.
- Remove obsolete shell fixtures and code when they are no longer required.
- Confirm repository ignore rules still protect models, distributions, results,
  logs, and Python-generated artifacts.

### Acceptance criteria

- The documented quick-start invokes the Python package entry point.
- Contributor instructions require `uv run ruff format`,
  `uv run ruff check --fix`, `uv run ty check`, and `uv run pytest`.
- No obsolete test tool or shell implementation remains without a documented
  transition purpose.
- A fresh checkout can be prepared with uv using the documented steps.

### Validation

```bash
uv sync
uv run ruff format --check
uv run ruff check
uv run ty check
uv run pytest
git check-ignore models/example.gguf
git check-ignore llama/turboquant-plus-tqp-v0.3.0/llama-server
git check-ignore benchmark_results/example/results.csv
```

### Depends on

Ticket 9.

## Ticket 11: Perform migration acceptance and cleanup

### Objective

Verify the finished migration as a coherent release candidate and remove only
artifacts made obsolete by the approved transition plan.

### Work

- Run the complete quality and test suite from a clean environment.
- Perform one small controlled run against a real local TurboQuant server when
  practical.
- Inspect `results.csv`, `summary.txt`, and `server.log` together.
- Confirm child-process cleanup after success and an interrupted run.
- Review the lock file and installed dependency graph against Ticket 2.
- Inspect Git status for generated or local-only artifacts.
- Update the epic documents with final decisions and completion status.

### Acceptance criteria

- All requested quality commands pass without uncommitted formatter or fixer
  changes.
- The real controlled run produces plausible, internally consistent artifacts,
  or a documented reason explains why it could not be performed.
- The dependency set matches the approved policy.
- The working tree contains only intended source and documentation changes.
- The migration can be reviewed as thematic commits created with the
  git-commit skill.

### Validation

```bash
uv sync --locked
uv run ruff format --check
uv run ruff check
uv run ty check
uv run pytest
git status --short
git diff --check
```

### Depends on

Ticket 10.
