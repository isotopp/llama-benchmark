# Convert llama-benchmark to Python

## Goal

Replace the current shell implementation with an equivalent, modern Python
project. Preserve user-visible benchmark behavior and result compatibility where
it matters, but design the Python implementation idiomatically instead of
performing a line-for-line port.

## User story 1: Create the Python package

As a developer, I want `llama-benchmark` to use uv's `--package` project
structure so that the application has a standard, maintainable Python package
layout and reproducible development environment.

### Acceptance criteria

- The repository is initialized as a uv package project.
- Application code lives in a conventional `src/` package layout.
- The benchmark has a documented command-line entry point.
- The supported Python version and project metadata are declared in
  `pyproject.toml`.
- uv manages the project environment, lock file, and development commands.

## User story 2: Preserve benchmark capabilities

As a developer, I want the Python application to provide functionality
equivalent to the shell benchmark so that existing benchmark workflows and
comparisons remain useful after the migration.

### Acceptance criteria

- The application starts and stops the configured local `llama-server` safely.
- The existing model, server, Turbo cache, symmetry, host, port, context, run,
  warm-up, long-prompt, output-directory, and extra-server-argument settings
  remain available through a clear CLI.
- The current short-generation, numeric-analysis, code-generation, and
  long-context scenarios remain represented without silently changing their
  comparability.
- Prompt reuse remains disabled unless a future explicit benchmark mode enables
  and reports it.
- Raw prompts and server responses are recorded before summaries are computed.
- The application produces equivalent CSV measurements, server logs, and a
  human-readable statistical summary.
- Failures produce clear diagnostics and leave no orphaned server process or
  partial temporary request file.
- The implementation uses modern, idiomatic Python design rather than mirroring
  shell functions or control flow one for one.

## User story 3: Develop test-first

As a developer, I want the migration implemented with the TDD skill so that
each behavior is specified through a public interface before its implementation
and regressions are caught throughout the conversion.

### Acceptance criteria

- The TDD skill is used for migration work.
- Work proceeds in small red-green-refactor cycles, one observable behavior at
  a time.
- Tests exercise public CLI and package interfaces rather than private
  implementation details.
- pytest covers argument validation, server lifecycle, HTTP requests, generated
  artifacts, statistics, failures, and cleanup behavior.
- Controlled tests do not load a real model or require a real TurboQuant server.
- Existing ShellSpec behavior provides migration guidance until equivalent
  pytest coverage is established.

## User story 4: Enforce Python quality checks

As a developer, I want formatting, linting, type checking, and tests to use the
standard project commands so that the migrated codebase remains consistent and
safe to change.

### Acceptance criteria

- `uv run ruff format` formats the Python sources.
- `uv run ruff check --fix` reports no remaining lint violations after applying
  safe fixes.
- `uv run ty check` reports no type errors.
- `uv run pytest` passes the complete test suite.
- Tool configuration is stored in `pyproject.toml` where supported.
- Contributor instructions list the required validation commands.

## User story 5: Approve dependencies before adoption

As a developer, I want potentially useful external dependencies discussed
before they are added so that convenience, maintenance cost, portability, and
standard-library alternatives can be evaluated explicitly.

### Acceptance criteria

- No runtime or development dependency beyond the requested uv, Ruff, ty, and
  pytest toolchain is added without prior discussion and approval.
- A dependency proposal explains its purpose, the standard-library or in-house
  alternative, and the resulting maintenance trade-off.
- Approved dependencies are added and locked with uv.
- Dependencies are used where they materially simplify or strengthen the
  implementation, not merely to replace small standard-library capabilities.

## User story 6: Keep migration history reviewable

As a developer, I want the migration committed with the git-commit skill in
thematically separated commits so that each conversion step is understandable,
testable, and easy to review or revert.

### Acceptance criteria

- The git-commit skill is used whenever migration changes are committed.
- Commits group one coherent theme and include its tests.
- Commit messages follow the repository's required title and itemized-detail
  structure, including relevant file references.
- Every commit leaves the repository in a valid state with its applicable
  formatting, lint, type, and test checks passing.
- Models, compiled distributions, generated benchmark results, logs, and other
  local artifacts remain untracked.

## Completion criteria

The epic is complete when the uv-based Python package provides the agreed
equivalent benchmark behavior, all requested quality commands pass, the pytest
suite replaces the necessary ShellSpec coverage, contributor documentation is
current, and the obsolete shell implementation can be removed without losing a
supported workflow.
