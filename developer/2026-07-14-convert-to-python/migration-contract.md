# Shell-to-Python Migration Contract

## Purpose

This document records the observable contract of `run-benchmark.sh` before the
Python migration. The Python implementation should preserve these capabilities
and comparability properties. It does not need to preserve shell-specific
structure, internal functions, implementation order, or incidental formatting.

## Command-line contract

The command exits with status 0 for `--help` and a successful benchmark. It
exits nonzero with a concise `Error:` message for invalid configuration,
unavailable resources, startup failure, or request failure.

| Option | Required | Default | Contract |
| --- | --- | --- | --- |
| `--model FILE` | No | `models/qwen3.6-35b-a3b/qwen3.6-35b-a3b-q4_k_m.gguf` relative to the project | Must name an existing file. |
| `--server FILE` | No | `llama/turboquant-plus-tqp-v0.3.0/llama-server` relative to the project | Must name an executable file. |
| `--turbo 3\|4` | Yes | None | Selects `turbo3` or `turbo4` for both K and V cache types. |
| `--symmetric on\|off` | Yes | None | `on` sets `TURBO_AUTO_ASYMMETRIC=0`; `off` removes that variable from the server environment. |
| `--host ADDRESS` | No | `127.0.0.1` | Server bind and request address. |
| `--port PORT` | No | `8080` | Unsigned decimal integer in the range 1 through 65535. Leading zeroes are accepted as decimal. |
| `--context TOKENS` | No | `65536` | Unsigned decimal integer of at least 2048. |
| `--long-tokens TOKENS` | No | `8192` | Unsigned decimal integer of at least 512. |
| `--runs N` | No | `5` | At least three measured runs per scenario. |
| `--warmups N` | No | `1` | Zero or more warm-up runs per scenario. |
| `--output-dir DIR` | No | `benchmark_results` relative to the project | Parent of timestamped result directories. |
| `--server-arg ARG` | No | None | Repeatable; values are appended to the server command in input order. |
| `-h`, `--help` | No | — | Prints usage without validating local model or server files. |

The context must leave more than 512 tokens beyond `--long-tokens`. Unknown
options, missing option values, invalid unsigned integers, and invalid enum
values are rejected before the server starts. Required external commands are
checked before output artifacts are created.

## Server lifecycle contract

Before startup, the command checks `http://HOST:PORT/health` and refuses to
replace a responding server. It then creates the result directories and starts
the configured server with these effective arguments:

```text
-m MODEL
--cache-type-k turboN
--cache-type-v turboN
-ngl all
-fa on
-c CONTEXT
-np 1
--jinja
--host HOST
--port PORT
[repeated extra server arguments]
```

The command records the effective command in `server.log`, redirects server
output there, waits up to approximately 180 seconds for health, and reports an
early server exit with the last 80 log lines. It terminates and reaps the child
on normal completion, command failure, or a handled signal.

## Scenario contract

Scenarios run in this order:

| Scenario | Prompt behavior | Predicted tokens |
| --- | --- | ---: |
| `short-generation` | Four concise paragraphs explaining the blue sky, Rayleigh scattering versus absorption, and red sunsets. | 256 |
| `numeric-analysis` | Annual energy, cost, and seven-percent savings calculation for three supplied data centres, with formulas and a compact table. | 384 |
| `code-generation` | Complete standard-library Python 3.12 NDJSON validation module with atomic output and unittest coverage. | 512 |
| `long-context` | Ordered operational ledger followed by a JSON-only retrieval task. | 64 |

The long-context ledger contains approximately `LONG_TOKENS / 59` records with
a minimum of eight. IDs are sequential `R000001` values. A record is `ALERT`
when its index is divisible by 997 or it is the fourth record from the end. The
reading is `(index * 37) % 10000`, and every record repeats the checksum rule.

Each scenario performs all configured warm-ups before all measured runs.

## Completion request contract

Every request is sent to `http://HOST:PORT/completion` as non-streaming JSON.
The prompt begins with a unique benchmark nonce and an instruction to ignore
the nonce, followed by the saved scenario prompt. The remaining request fields
are:

```json
{
  "n_predict": "scenario-specific integer",
  "temperature": 0,
  "top_k": 1,
  "top_p": 1,
  "min_p": 0,
  "seed": 42,
  "ignore_eos": true,
  "cache_prompt": false,
  "stream": false
}
```

The request timeout is 1800 seconds. Transport failure and non-200 status are
fatal. A non-200 response is still retained as raw evidence and printed as JSON
when possible.

## Result directory and raw-data contract

The result directory name is:

```text
YYYYMMDD-HHMMSS-MODEL_BASENAME-turboN-symmetric-on|off
```

It contains:

```text
prompts/short.txt
prompts/analysis.txt
prompts/code.txt
prompts/long-context.txt
raw/SCENARIO-PHASE-RUN.json
results.csv
server.log
summary.txt
```

Raw response JSON is written before timing fields are interpreted or summary
statistics are calculated. Temporary request JSON files are removed after each
request, including curl failure. Prompt caching is explicitly disabled; cached
and uncached benchmark modes must never be combined silently.

## Measurement contract

`results.csv` begins with this header:

```text
test,phase,run,prompt_n,prompt_ms,prompt_tps,predicted_n,predicted_ms,predicted_tps,total_ms,http_code,response_file
```

Timing values come from `timings.prompt_n`, `prompt_ms`,
`prompt_per_second`, `predicted_n`, `predicted_ms`, and
`predicted_per_second`. A missing or non-numeric timing field currently becomes
zero. `total_ms` is prompt milliseconds plus predicted milliseconds.

Only positive values from measured rows contribute to statistics. For prompt
and generation throughput, `summary.txt` reports median, nearest-rank P95,
arithmetic mean, minimum, and maximum. Median averages the two middle values for
an even count. The summary also reports the first measured prompt and generated
token counts for each scenario and the paths of the CSV, raw JSON directory,
and server log. The same summary is printed to standard output.

## Characterized failures

The existing ShellSpec suite fixes these observable cases:

- help includes repository-local model and server defaults;
- unknown options are rejected;
- unsupported Turbo and symmetry modes are rejected;
- port, measured-run, and context-capacity limits are enforced;
- missing model and non-executable server paths are identified;
- missing runtime commands are identified;
- an occupied endpoint is not replaced;
- leading-zero decimal values are accepted;
- a controlled run creates four prompts, twelve measured raw responses,
  thirteen CSV lines, a statistical summary, and a server log.

## Decisions requiring approval

These are not required to remain identical if a deliberate replacement is
agreed before implementation:

- Python CLI framework and exact help/error formatting.
- HTTP client implementation and timeout exception wording.
- Installed-resource strategy for repository-local default model/server paths.
- Whether malformed or incomplete successful JSON should remain zero-filled or
  become a fatal data-quality error.
- Exact whitespace and column alignment of `summary.txt`.
- Timestamp formatting and collision handling for result directories.
- Whether the shell entry point is removed or retained as a temporary wrapper.

Changes to prompts, request parameters, cache behavior, scenario order,
measured statistics, or CSV column meanings have benchmark-comparability impact
and require explicit documentation and approval.
