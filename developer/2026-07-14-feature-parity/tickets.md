# Python Feature Parity: Implementation Tickets

## Working rules

- Use the TDD skill for every behavior-changing ticket.
- Work in vertical slices: write one public-interface test, observe it fail,
  implement only enough behavior to pass, then repeat.
- Refactor only while the complete suite is green.
- Use the git-commit skill and commit each completed ticket before starting the
  next ticket.
- Do not add dependencies without discussing them and receiving approval.
- Preserve prompt, request, cache, scenario, CSV, and statistical comparability.
- The `argparse` handling of hyphen-prefixed `--server-arg` values is an explicit
  non-goal. Document the `--server-arg=VALUE` form instead of changing parsing.
- Do not remove the shell wrapper or shell-only fixtures until the automated and
  manual parity gates that precede their removal are satisfied.

## Ticket 1: Resolve defaults from the working directory

### Objective

Remove the source-package-location dependency from default model, server, and
output paths.

### TDD sequence

1. Run the public CLI from a temporary working directory containing the expected
   model and server layout; assert that configuration resolves those local
   files. Observe the current source-relative behavior fail.
2. Implement current-working-directory defaults with the smallest configuration
   change.
3. Add one test each for explicit relative model, server, and output paths.
4. Add one test proving absolute overrides remain unchanged.
5. Refactor path resolution behind the public configuration interface.

### Acceptance criteria

- Defaults resolve from `Path.cwd()` at command invocation time.
- The default model, server, and output paths match the user story.
- Explicit relative paths resolve from the working directory.
- Absolute paths remain absolute and unchanged.
- Tests do not rely on the package source location or repository-local ignored
  assets.

### Validation

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest tests/test_cli.py
```

### Depends on

None.

## Ticket 2: Preflight the endpoint before creating artifacts

### Objective

Reject an occupied endpoint without creating an empty timestamped result
directory.

### TDD sequence

1. Start the fake server on a loopback port and invoke the public benchmark
   command with an empty output root.
2. Assert a nonzero result and no new result directory; observe the current
   eager directory creation fail.
3. Introduce the smallest preflight boundary that checks endpoint health before
   artifact creation.
4. Add a test proving a post-start request failure retains its prompts, raw
   response evidence, and server log.
5. Refactor duplicate health logic only after both paths are green.

### Acceptance criteria

- Occupied endpoints are detected before timestamped-directory creation.
- Non-mutating validation and endpoint preflight precede artifact writes.
- Rejected runs leave the output root unchanged.
- Failures after execution begins retain useful partial evidence.

### Validation

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest tests/test_integration.py tests/test_server.py
```

### Depends on

Ticket 1.

## Ticket 3: Report startup logs on early exit and timeout

### Objective

Make server startup failures immediately diagnosable from CLI error output while
retaining the complete log file.

### TDD sequence

1. Add a fake child that writes a short diagnostic and exits with a known
   status; assert the public error includes both.
2. Implement short-log extraction after the child has been reaped and the log
   stream has been flushed.
3. Add a fake child that writes more than 80 unique lines and exits; assert only
   the final 80 lines appear in the error.
4. Add a startup-timeout test asserting the endpoint and configured timeout are
   present.
5. Confirm the full server log remains on disk in each post-start failure case.

### Acceptance criteria

- Early exit errors include exit status and up to 80 trailing log lines.
- Logs shorter than 80 lines are included completely.
- Timeout errors identify endpoint and duration.
- Complete logs remain available in the result directory.
- Diagnostic extraction is tested through the public lifecycle boundary.

### Validation

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest tests/test_server.py
```

### Depends on

Ticket 2.

## Ticket 4: Convert expected failures into concise CLI errors

### Objective

Provide stable, traceback-free command-line diagnostics for expected operational
failures without hiding programming defects.

### TDD sequence

1. Invoke the public command against an early-exit fake server; assert one
   concise standard-error report and no traceback.
2. Add equivalent vertical slices for transport failure, non-success HTTP,
   invalid JSON/timing data, result-directory failure, and report-write failure.
3. Introduce a narrow application-error boundary that maps only known
   operational exceptions to nonzero CLI results.
4. Add a test where an unexpected exception is raised and prove it is not
   silently converted into an expected operational error.
5. Refactor error types and formatting only after all public CLI cases pass.

### Acceptance criteria

- Expected failures print concise actionable errors to standard error.
- Expected failures return nonzero without a traceback.
- Messages include relevant endpoint, HTTP status, process status, or path.
- Unexpected programmer errors remain visible.
- Public subprocess tests cover server, request, validation, and filesystem
  categories.

### Validation

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest tests/test_cli.py tests/test_integration.py
```

### Depends on

Ticket 3.

## Ticket 5: Clean up the server on termination signals

### Objective

Guarantee child-server termination and reaping when the benchmark process is
interrupted or terminated.

### TDD sequence

1. Start the benchmark as a subprocess with a fake child that records its PID.
2. Send `SIGTERM`; assert the benchmark exits for that signal and the child PID
   no longer exists. Observe the current cleanup gap fail.
3. Implement scoped signal handling that unwinds through the server lifecycle.
4. Repeat with `SIGHUP` and keyboard interruption as separate tests.
5. Add an uncooperative fake child and prove cleanup escalates from terminate to
   kill after a bounded grace period.
6. Verify the original interruption/termination exit reason is preserved.

### Acceptance criteria

- Normal, exception, keyboard, `SIGTERM`, and `SIGHUP` exits reap the child.
- Uncooperative children are killed after the grace period.
- Tests inspect real subprocess PIDs rather than mocked process methods.
- Signal handlers are restored after scoped execution when applicable.
- Cleanup does not obscure the initiating signal or failure.

### Validation

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest tests/test_server.py tests/test_integration.py
```

### Depends on

Ticket 4.

## Ticket 6: Restore benchmark progress output

### Objective

Show selected configuration, startup readiness, and per-request progress without
changing recorded artifacts.

### TDD sequence

1. Invoke a controlled full run and assert the initial configuration block.
2. Implement configuration output before server startup.
3. Add a test for the startup waiting/ready message and implement it.
4. Add one warm-up progress assertion, implement the request progress callback,
   then add the measured-run case.
5. Snapshot CSV, raw JSON, and summary semantics before and after progress output
   to prove they are unchanged.
6. Refactor output formatting behind a small progress-reporting interface.

### Acceptance criteria

- Initial output reports model, Turbo cache, symmetry, context, long-prompt
  target, run counts, and output directory.
- Startup visibly transitions from waiting to ready.
- Every request reports scenario, phase, run, tokens, and throughput.
- Output works when captured and does not require a TTY.
- Progress reporting does not change measurement artifacts.

### Validation

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest tests/test_integration.py tests/test_requests.py
```

### Depends on

Ticket 5.

## Ticket 7: Replace shell-based pytest fixtures

### Objective

Remove pytest's dependency on shell launchers and fake processes before deleting
the final shell entry point.

### TDD sequence

1. Inventory every executable shell fixture used by pytest and identify its
   observable contract.
2. Replace one fixture at a time with an executable Python equivalent while its
   existing public-boundary test remains green.
3. Replace the fake server launcher with a direct Python executable fixture.
4. Replace early-exit, stalled, and uncooperative-child fixtures with Python.
5. Remove the superseded shell fixture immediately after each replacement.
6. Search tests and configuration for shell-specific invocation assumptions.

### Acceptance criteria

- pytest uses no `.sh` or Bash executable fixture.
- Fake server, early exit, startup stall, and signal-cleanup behavior remain
  covered by real subprocess tests.
- Fixture behavior is expressed through process, HTTP, files, environment, and
  exit status rather than internal mocks.
- The complete pytest suite remains green after each fixture replacement.

### Validation

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest
rg -n 'bash|\.sh|shellcheck|shellspec' tests spec pyproject.toml
```

### Depends on

Ticket 6.

## Ticket 8: Run the automated parity gate

### Objective

Demonstrate that every automated feature-parity story is covered before the
manual hardware test and destructive shell cleanup.

### Work

- Map every acceptance criterion from Stories 1 through 6 to at least one
  public-interface pytest.
- Run the complete suite from `uv sync --locked`.
- Verify result CSV columns, scenario order, request parameters, prompt caching,
  statistics, raw evidence, logging, progress, errors, and cleanup together.
- Confirm the accepted `argparse` non-goal is documented and not accidentally
  tested as required compatibility.
- Record the automated gate result in an epic acceptance document.

### Acceptance criteria

- Every automated parity criterion has traceable pytest coverage.
- Locked sync, formatting, lint, typing, pytest, and diff checks pass.
- No ignored local model or distribution is required by automated tests.
- The acceptance record distinguishes automated success from the still-manual
  TurboQuant gate.

### Validation

```bash
uv sync --locked
uv run ruff format --check
uv run ruff check
uv run ty check
uv run pytest
git diff --check
```

### Depends on

Tickets 1 through 7.

## Ticket 9: Perform and record the manual TurboQuant run

### Objective

Validate the Python workflow against the real local TurboQuant distribution and
GGUF model before shell removal.

### Work

- Remind the maintainer that this ticket is manual and hardware-intensive.
- Confirm the default model and server files exist in the current working
  directory layout.
- Run the minimum three-measurement acceptance command.
- Inspect all four scenarios in `results.csv`.
- Inspect token counts and throughput for plausible positive values.
- Inspect `summary.txt` and `server.log` together with the CSV.
- Confirm no `llama-server` child remains after completion.
- Record pass or fail with the result-directory path and relevant observations.
- If the run cannot be performed, mark the ticket explicitly pending; do not
  claim epic completion and do not proceed to shell removal.

### Manual command

```bash
uv run llama-benchmark --turbo 4 --symmetric off --runs 3
```

### Acceptance criteria

- The real run completes successfully using current-working-directory defaults.
- Four scenarios and twelve measured rows are present.
- Prompt and generation timings are positive and plausible.
- Summary and raw evidence agree with the CSV.
- Server startup and shutdown are clean.
- The acceptance record contains the run outcome and output path.

### Depends on

Ticket 8.

## Ticket 10: Remove the shell version and shell-only artifacts

### Objective

Delete the deprecated shell entry point and all remaining shell-only project
artifacts after automated and manual parity are accepted.

### Work

- Remove `run-benchmark.sh`.
- Remove remaining shell launchers, test fixtures, configuration, and obsolete
  validation references.
- Remove empty directories left by shell-only tooling.
- Search tracked files for Bash, ShellCheck, ShellSpec, and the old command.
- Keep non-shell fake-server assets still required by pytest.
- Run the complete Python suite after deletion.

### Acceptance criteria

- No supported or deprecated shell implementation remains.
- No tracked executable shell fixture remains.
- ShellCheck and ShellSpec are absent from requirements and instructions.
- Tests and package entry points use Python directly.
- Repository searches find no obsolete shell workflow references outside
  historical epic records where retention is intentional.
- All Python validation passes after removal.

### Validation

```bash
uv run ruff format --check
uv run ruff check
uv run ty check
uv run pytest
rg -n 'run-benchmark\.sh|shellcheck|shellspec|#!/usr/bin/env bash' \
  --glob '!developer/2026-07-14-convert-to-python/**'
git diff --check
```

### Depends on

Ticket 9 completed with a passing manual result.

## Ticket 11: Document the Python-only project

### Objective

Make `README.md` and `AGENTS.md` accurately describe the final implementation,
including the explicit `argparse` syntax and future manual acceptance workflow.

### Work

- Update the repository layout and requirements in `README.md`.
- Document uv setup, execution, working-directory defaults, all result
  artifacts, progress, and concise errors.
- Document `--server-arg=--option` for values beginning with a hyphen.
- Preserve the manual TurboQuant command and inspection checklist.
- Update `AGENTS.md` with the `src/` package conventions, TDD expectations,
  quality commands, controlled integration tests, and repository hygiene.
- Remove Bash, wrapper, ShellCheck, and ShellSpec guidance from both documents.
- Verify every documented command against the final tree.

### Acceptance criteria

- README describes one supported Python workflow.
- AGENTS describes one Python development and validation workflow.
- Working-directory-relative defaults and `--server-arg=VALUE` are explicit.
- The real-model run is clearly identified as manual and hardware-intensive.
- No current documentation mentions a shell implementation or wrapper.
- Documented commands execute successfully where they are automated.

### Validation

```bash
uv sync --locked
uv run llama-benchmark --help
uv run ruff format --check
uv run ruff check
uv run ty check
uv run pytest
git diff --check
```

### Depends on

Ticket 10.

## Ticket 12: Close the feature-parity epic

### Objective

Perform final acceptance on the Python-only repository and record completion.

### Work

- Re-run the locked automated validation suite.
- Confirm the Ticket 9 manual result is recorded as passing.
- Confirm no child process or generated benchmark artifact is tracked.
- Audit direct dependencies against the approved dependency policy.
- Confirm shell-removal searches are clean.
- Record final validation results and the ordered ticket commits.

### Acceptance criteria

- Automated validation is green from the locked environment.
- The real TurboQuant/GGUF result is recorded as passing.
- The working tree contains only intended source and documentation changes.
- Models, distributions, results, logs, caches, environments, and build output
  remain ignored.
- The epic acceptance record states feature parity is complete without caveats.

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

Ticket 11.
