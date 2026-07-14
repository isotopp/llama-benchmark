# Dependency Policy

## Decision

The Python migration will use `httpx` as its sole runtime dependency.

The approved development toolchain is:

- uv for project and dependency management;
- Ruff for formatting and linting;
- ty for static type checking;
- pytest for tests.

Any additional runtime or development dependency requires a new discussion and
explicit approval before it is added.

## Approved runtime dependency

### httpx

`httpx` will provide the health-check and completion-request HTTP boundary. It
is preferred over `urllib.request` because it offers a clearer typed interface,
explicit timeout configuration, straightforward response and JSON handling,
and a well-defined exception hierarchy. These properties simplify the
benchmark's high-value error paths and their tests.

The trade-off is an additional runtime package and its transitive dependencies.
This is accepted because HTTP communication is central to the application and
the improved interface materially reduces boundary-handling complexity.

## Standard-library choices

The following proposed dependency categories were considered and rejected:

- CLI framework: use `argparse`; Typer or Click would add dependencies without
  enough benefit for this command surface.
- Process management: use `subprocess`; no external process library is needed
  to start, monitor, terminate, and reap one child server.
- Data models: use dataclasses and standard typing; no validation framework is
  needed for internal configuration objects.
- Serialization and artifacts: use `json`, `csv`, `pathlib`, and atomic file
  operations from the standard library.
- Statistics: use `statistics` plus a small explicit nearest-rank P95 function.
- Time and identifiers: use `datetime`, `time`, and `uuid` from the standard
  library.

## Review rule

Before proposing another dependency, document:

1. the concrete capability it supplies;
2. the standard-library or in-project alternative;
3. effects on portability, typing, testability, and maintenance;
4. why the benefit outweighs another direct or transitive dependency.

Add an approved package with uv and commit both `pyproject.toml` and `uv.lock`.
