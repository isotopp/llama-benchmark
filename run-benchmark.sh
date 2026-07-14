#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SERVER="$SCRIPT_DIR/llama/turboquant-plus-tqp-v0.3.0/llama-server"
MODEL=""
TURBO=""
SYMMETRIC=""
HOST="127.0.0.1"
PORT=8080
CONTEXT=65536
RUNS=5
WARMUPS=1
LONG_TOKENS=8192
OUTPUT_ROOT="$SCRIPT_DIR/benchmark_results"
EXTRA_SERVER_ARGS=()
EXTRA_SERVER_ARG_COUNT=0

usage() {
    cat <<'EOF'
Usage:
  run-benchmark.sh --model FILE --turbo 3|4 --symmetric on|off [options]

Required:
  --model FILE
  --turbo 3|4
  --symmetric on|off

Options:
  --server FILE          llama-server executable
  --host ADDRESS         Default: 127.0.0.1
  --port PORT            Default: 8080
  --context TOKENS       Server context size. Default: 65536
  --long-tokens TOKENS   Approximate long-context prompt size. Default: 8192
  --runs N               Measured runs per test. Default: 5
  --warmups N            Warm-up runs per test. Default: 1
  --output-dir DIR       Default: ./benchmark_results
  --server-arg ARG       Additional llama-server argument. Repeatable.
  -h, --help

Examples:
  ./run-benchmark.sh \
    --model "$HOME/Downloads/GGUF/qwen3.6-35b-a3b/qwen3.6-35b-a3b-q8_0.gguf" \
    --turbo 4 --symmetric off

  ./run-benchmark.sh \
    --model "$HOME/Downloads/GGUF/qwen3.6-27b/qwen3.6-27b-q6_k.gguf" \
    --turbo 3 --symmetric on \
    --long-tokens 32768 --runs 7
EOF
}

die() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

need_value() {
    (($# >= 2)) || die "$1 requires a value"
}

is_uint() {
    [[ "$1" =~ ^[0-9]+$ ]]
}

while (($#)); do
    case "$1" in
        --model)
            need_value "$@"; MODEL="$2"; shift 2 ;;
        --server)
            need_value "$@"; SERVER="$2"; shift 2 ;;
        --turbo)
            need_value "$@"; TURBO="$2"; shift 2 ;;
        --symmetric)
            need_value "$@"; SYMMETRIC="$2"; shift 2 ;;
        --host)
            need_value "$@"; HOST="$2"; shift 2 ;;
        --port)
            need_value "$@"; PORT="$2"; shift 2 ;;
        --context)
            need_value "$@"; CONTEXT="$2"; shift 2 ;;
        --long-tokens)
            need_value "$@"; LONG_TOKENS="$2"; shift 2 ;;
        --runs)
            need_value "$@"; RUNS="$2"; shift 2 ;;
        --warmups)
            need_value "$@"; WARMUPS="$2"; shift 2 ;;
        --output-dir)
            need_value "$@"; OUTPUT_ROOT="$2"; shift 2 ;;
        --server-arg)
            need_value "$@"
            EXTRA_SERVER_ARGS+=("$2")
            ((EXTRA_SERVER_ARG_COUNT += 1))
            shift 2 ;;
        -h|--help)
            usage
            exit 0 ;;
        *)
            die "unknown argument: $1" ;;
    esac
done

[[ -n "$MODEL" ]] || die "--model is required"
[[ -f "$MODEL" ]] || die "model not found: $MODEL"
[[ -x "$SERVER" ]] || die "server not executable: $SERVER"
[[ "$TURBO" == 3 || "$TURBO" == 4 ]] || die "--turbo must be 3 or 4"
[[ "$SYMMETRIC" == on || "$SYMMETRIC" == off ]] || die "--symmetric must be on or off"

for value_name in PORT CONTEXT LONG_TOKENS RUNS WARMUPS; do
    value="${!value_name}"
    is_uint "$value" || die "$value_name must be a non-negative integer"
done

(( PORT > 0 && PORT <= 65535 )) || die "--port must be between 1 and 65535"
(( CONTEXT >= 2048 )) || die "--context must be at least 2048"
(( LONG_TOKENS >= 512 )) || die "--long-tokens must be at least 512"
(( LONG_TOKENS + 512 < CONTEXT )) ||
    die "--context must leave at least 512 tokens beyond --long-tokens"
(( RUNS >= 3 )) || die "--runs must be at least 3"

for cmd in curl jq awk sort mktemp date basename sed head tail tee wc tr; do
    command -v "$cmd" >/dev/null 2>&1 || die "required command not found: $cmd"
done

CACHE_TYPE="turbo${TURBO}"
MODEL_BASENAME="$(basename "$MODEL" .gguf)"
STAMP="$(date '+%Y%m%d-%H%M%S')"
SCENARIO="${MODEL_BASENAME}-${CACHE_TYPE}-symmetric-${SYMMETRIC}"
OUTPUT_DIR="$OUTPUT_ROOT/$STAMP-$SCENARIO"
RAW_DIR="$OUTPUT_DIR/raw"
PROMPT_DIR="$OUTPUT_DIR/prompts"
CSV="$OUTPUT_DIR/results.csv"
SUMMARY="$OUTPUT_DIR/summary.txt"
SERVER_LOG="$OUTPUT_DIR/server.log"
SERVER_PID=""

mkdir -p "$RAW_DIR" "$PROMPT_DIR"

if curl --silent --fail --max-time 1 \
    "http://$HOST:$PORT/health" >/dev/null 2>&1; then
    die "a server is already responding at http://$HOST:$PORT; choose another --port or stop it"
fi

cleanup() {
    local status=$?
    if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
    exit "$status"
}
trap cleanup EXIT INT TERM HUP

server_command=(
    "$SERVER"
    -m "$MODEL"
    --cache-type-k "$CACHE_TYPE"
    --cache-type-v "$CACHE_TYPE"
    -ngl all
    -fa on
    -c "$CONTEXT"
    -np 1
    --jinja
    --host "$HOST"
    --port "$PORT"
)

# Bash 3.2 with `set -u` treats expansion of an empty array as an unbound
# variable. Only expand it after at least one --server-arg was supplied.
if (( EXTRA_SERVER_ARG_COUNT > 0 )); then
    server_command+=("${EXTRA_SERVER_ARGS[@]}")
fi

printf 'Model:           %s\n' "$MODEL"
printf 'KV cache:        %s\n' "$CACHE_TYPE"
printf 'Symmetric:       %s\n' "$SYMMETRIC"
printf 'Context:         %s tokens\n' "$CONTEXT"
printf 'Long prompt:     approximately %s tokens\n' "$LONG_TOKENS"
printf 'Runs:            %s measured, %s warm-up\n' "$RUNS" "$WARMUPS"
printf 'Output:          %s\n\n' "$OUTPUT_DIR"

{
    printf 'Command:'
    if [[ "$SYMMETRIC" == on ]]; then
        printf ' TURBO_AUTO_ASYMMETRIC=0'
    fi
    printf ' %q' "${server_command[@]}"
    printf '\n'
} >"$SERVER_LOG"

if [[ "$SYMMETRIC" == on ]]; then
    TURBO_AUTO_ASYMMETRIC=0 "${server_command[@]}" >>"$SERVER_LOG" 2>&1 &
else
    env -u TURBO_AUTO_ASYMMETRIC "${server_command[@]}" >>"$SERVER_LOG" 2>&1 &
fi
SERVER_PID=$!

printf 'Waiting for llama-server'
for _ in $(seq 1 180); do
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        printf '\n'
        tail -n 80 "$SERVER_LOG" >&2
        die "llama-server exited during startup"
    fi

    if curl --silent --fail --max-time 1 \
        "http://$HOST:$PORT/health" >/dev/null 2>&1; then
        printf ' ready\n\n'
        break
    fi

    printf '.'
    sleep 1
done

curl --silent --fail --max-time 2 \
    "http://$HOST:$PORT/health" >/dev/null ||
    die "server did not become healthy"

cat >"$PROMPT_DIR/short.txt" <<'EOF'
Give a precise explanation of why the sky appears blue during the day. Use exactly four concise paragraphs. Distinguish Rayleigh scattering from absorption and mention why sunsets appear red.
EOF

cat >"$PROMPT_DIR/analysis.txt" <<'EOF'
A company operates three data centres.

Data centre A consumes 4.8 MW continuously and has a power usage effectiveness of 1.24.
Data centre B consumes 3.1 MW continuously and has a power usage effectiveness of 1.38.
Data centre C consumes 2.6 MW continuously and has a power usage effectiveness of 1.18.

Electricity costs EUR 0.142 per kWh. The company plans to reduce each site's total facility power by 7 percent without changing IT workload.

Calculate the current annual electricity use and cost for each site and for the whole fleet. Then calculate the annual savings after the reduction. Show formulas, intermediate values, units, and a compact final table. Use 365.25 days per year.
EOF

cat >"$PROMPT_DIR/code.txt" <<'EOF'
Write a complete Python 3.12 module that reads newline-delimited JSON records from a pathlib.Path, validates each record, and writes valid records to one output file and invalid records to another.

Requirements:
- Use only the Python standard library.
- Use dataclasses with slots.
- Stream the input instead of loading it into memory.
- Preserve the original line number.
- Treat malformed JSON, non-object JSON, missing "id", and non-string "id" as invalid.
- Write UTF-8 atomically by using temporary files in the destination directory and os.replace.
- Include type annotations, docstrings, explicit error handling, and unittest tests.
- Do not use shell commands or unsafe deserialization.
EOF

LONG_FILE="$PROMPT_DIR/long-context.txt"
{
    printf '%s\n\n' \
        'Read the numbered operational records below. Return only a JSON object with keys "first_id", "last_id", "count", "checksum_rule", and "anomalies". The count must equal the number of records. The first and last IDs must come from the text. The checksum rule is stated repeatedly. List records whose status is ALERT.'

    # With the target models, one ledger record tokenizes to roughly 59 tokens.
    # Keep a small minimum so low --long-tokens values remain representative.
    record_count=$(( LONG_TOKENS / 59 ))
    (( record_count >= 8 )) || record_count=8

    for ((i = 1; i <= record_count; i++)); do
        status="OK"
        if (( i % 997 == 0 || i == record_count - 3 )); then
            status="ALERT"
        fi
        printf 'Record ID R%06d. Region EU-WEST. Status %s. Reading %d. Checksum rule: multiply the numeric ID by 17 and take the remainder modulo 1009. This record is part of one continuous ordered ledger.\n' \
            "$i" "$status" "$(( (i * 37) % 10000 ))"
    done
} >"$LONG_FILE"

printf 'test,phase,run,prompt_n,prompt_ms,prompt_tps,predicted_n,predicted_ms,predicted_tps,total_ms,http_code,response_file\n' >"$CSV"

json_number() {
    local file="$1"
    local expression="$2"
    jq -r "$expression // 0 | numbers" "$file" 2>/dev/null || printf '0'
}

run_request() {
    local test_name="$1"
    local phase="$2"
    local run_number="$3"
    local prompt_file="$4"
    local n_predict="$5"

    local nonce request_file response_file http_code
    nonce="benchmark-${SCENARIO}-${test_name}-${phase}-${run_number}-$(date +%s)-$$-$RANDOM"
    request_file="$(mktemp "$OUTPUT_DIR/request.XXXXXX.json")"
    response_file="$RAW_DIR/${test_name}-${phase}-${run_number}.json"

    jq -n \
        --arg nonce "$nonce" \
        --rawfile prompt "$prompt_file" \
        --argjson n_predict "$n_predict" \
        '{
            prompt: ("Benchmark nonce: " + $nonce + "\nIgnore the nonce. Follow the task exactly.\n\n" + $prompt),
            n_predict: $n_predict,
            temperature: 0,
            top_k: 1,
            top_p: 1,
            min_p: 0,
            seed: 42,
            ignore_eos: true,
            cache_prompt: false,
            stream: false
        }' >"$request_file"

    if ! http_code="$(
        curl --silent --show-error \
            --output "$response_file" \
            --write-out '%{http_code}' \
            --max-time 1800 \
            -H 'Content-Type: application/json' \
            --data-binary "@$request_file" \
            "http://$HOST:$PORT/completion"
    )"; then
        rm -f "$request_file"
        printf 'Request failed: test=%s phase=%s run=%s (curl error)\n' \
            "$test_name" "$phase" "$run_number" >&2
        return 1
    fi
    rm -f "$request_file"

    if [[ "$http_code" != 200 ]]; then
        printf 'Request failed: test=%s phase=%s run=%s HTTP=%s\n' \
            "$test_name" "$phase" "$run_number" "$http_code" >&2
        jq . "$response_file" >&2 2>/dev/null || cat "$response_file" >&2
        return 1
    fi

    local prompt_n prompt_ms prompt_tps predicted_n predicted_ms predicted_tps total_ms

    prompt_n="$(json_number "$response_file" '.timings.prompt_n')"
    prompt_ms="$(json_number "$response_file" '.timings.prompt_ms')"
    prompt_tps="$(json_number "$response_file" '.timings.prompt_per_second')"
    predicted_n="$(json_number "$response_file" '.timings.predicted_n')"
    predicted_ms="$(json_number "$response_file" '.timings.predicted_ms')"
    predicted_tps="$(json_number "$response_file" '.timings.predicted_per_second')"
    total_ms="$(awk -v a="$prompt_ms" -v b="$predicted_ms" 'BEGIN { printf "%.3f", a + b }')"

    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
        "$test_name" "$phase" "$run_number" \
        "$prompt_n" "$prompt_ms" "$prompt_tps" \
        "$predicted_n" "$predicted_ms" "$predicted_tps" \
        "$total_ms" "$http_code" "$response_file" >>"$CSV"

    printf '  %-14s %-7s %2d: prompt %7s tok %9.2f tok/s, generation %4s tok %8.2f tok/s\n' \
        "$test_name" "$phase" "$run_number" \
        "$prompt_n" "$prompt_tps" "$predicted_n" "$predicted_tps"
}

run_test() {
    local test_name="$1"
    local prompt_file="$2"
    local n_predict="$3"

    printf '%s\n' "$test_name"

    for ((i = 1; i <= WARMUPS; i++)); do
        run_request "$test_name" warmup "$i" "$prompt_file" "$n_predict"
    done

    for ((i = 1; i <= RUNS; i++)); do
        run_request "$test_name" measured "$i" "$prompt_file" "$n_predict"
    done

    printf '\n'
}

run_test short-generation "$PROMPT_DIR/short.txt" 256
run_test numeric-analysis "$PROMPT_DIR/analysis.txt" 384
run_test code-generation "$PROMPT_DIR/code.txt" 512
run_test long-context "$LONG_FILE" 64

metric_stats() {
    local test_name="$1"
    local column="$2"
    local values_file count p95_index median p95 mean min max

    values_file="$(mktemp "$OUTPUT_DIR/values.XXXXXX")"

    awk -F, -v test="$test_name" -v col="$column" '
        NR > 1 && $1 == test && $2 == "measured" && $col + 0 > 0 {
            print $col + 0
        }
    ' "$CSV" | sort -n >"$values_file"

    count="$(wc -l <"$values_file" | tr -d ' ')"
    if (( count == 0 )); then
        rm -f "$values_file"
        printf 'n/a,n/a,n/a,n/a,n/a\n'
        return
    fi

    p95_index=$(( (95 * count + 99) / 100 ))
    (( p95_index <= count )) || p95_index="$count"

    median="$(awk '
        { values[NR] = $1 }
        END {
            if (NR % 2) printf "%.3f", values[(NR + 1) / 2]
            else printf "%.3f", (values[NR / 2] + values[NR / 2 + 1]) / 2
        }
    ' "$values_file")"
    p95="$(sed -n "${p95_index}p" "$values_file")"
    min="$(head -n 1 "$values_file")"
    max="$(tail -n 1 "$values_file")"
    mean="$(awk '{ s += $1 } END { printf "%.3f", s / NR }' "$values_file")"

    rm -f "$values_file"
    printf '%s,%s,%s,%s,%s\n' "$median" "$p95" "$mean" "$min" "$max"
}

{
    printf 'llama.cpp server benchmark\n'
    printf '==========================\n\n'
    printf 'Model:       %s\n' "$MODEL"
    printf 'KV cache:    %s\n' "$CACHE_TYPE"
    printf 'Symmetric:   %s\n' "$SYMMETRIC"
    printf 'Context:     %s\n' "$CONTEXT"
    printf 'Runs:        %s measured, %s warm-up\n' "$RUNS" "$WARMUPS"
    printf 'Date:        %s\n\n' "$(date -Iseconds)"

    printf '%-20s %12s %12s %12s %12s %12s\n' \
        'Test' 'Metric' 'Median' 'P95' 'Mean' 'Min/Max'

    for test_name in short-generation numeric-analysis code-generation long-context; do
        IFS=, read -r median p95 mean min max < <(metric_stats "$test_name" 6)
        printf '%-20s %12s %12.2f %12.2f %12.2f %5.2f/%-5.2f\n' \
            "$test_name" 'prompt tok/s' "$median" "$p95" "$mean" "$min" "$max"

        IFS=, read -r median p95 mean min max < <(metric_stats "$test_name" 9)
        printf '%-20s %12s %12.2f %12.2f %12.2f %5.2f/%-5.2f\n' \
            '' 'gen tok/s' "$median" "$p95" "$mean" "$min" "$max"
    done

    printf '\nMeasured token counts\n'
    printf '%s\n' '---------------------'
    awk -F, '
        NR > 1 && $2 == "measured" {
            key=$1
            if (!(key in seen)) {
                printf "%-20s prompt=%s, generated=%s\n", $1, $4, $7
                seen[key]=1
            }
        }
    ' "$CSV"

    printf '\nFiles\n'
    printf '%s\n' '-----'
    printf 'CSV:        %s\n' "$CSV"
    printf 'Raw JSON:   %s\n' "$RAW_DIR"
    printf 'Server log: %s\n' "$SERVER_LOG"
} | tee "$SUMMARY"

printf '\nBenchmark completed successfully.\n'
