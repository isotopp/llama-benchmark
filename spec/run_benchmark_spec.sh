run_without_jq() {
    restricted_path="${SHELLSPEC_TMPBASE}/path-without-jq"
    mkdir -p "$restricted_path"

    for command_name in bash dirname curl awk sort mktemp date basename sed head tail tee wc tr; do
        ln -sf "$(command -v "$command_name")" "$restricted_path/$command_name"
    done

    PATH="$restricted_path" ./run-benchmark.sh \
        --server ./spec/support/fake-llama-server \
        --model ./spec/support/fake-model.bin \
        --turbo 4 \
        --symmetric off
}

run_with_occupied_port() {
    ./spec/support/fake-llama-server \
        --host 127.0.0.1 --port "$occupied_port" >/dev/null 2>&1 &
    fake_server_pid=$!

    attempt=0
    while ! curl --silent --fail --max-time 1 \
        "http://127.0.0.1:$occupied_port/health" >/dev/null 2>&1; do
        attempt=$((attempt + 1))
        if ((attempt >= 20)); then
            kill "$fake_server_pid" 2>/dev/null || true
            wait "$fake_server_pid" 2>/dev/null || true
            return 1
        fi
        sleep 0.1
    done

    ./run-benchmark.sh \
        --server ./spec/support/fake-llama-server \
        --model ./spec/support/fake-model.bin \
        --turbo 4 \
        --symmetric off \
        --port "$occupied_port"
    status=$?

    kill "$fake_server_pid" 2>/dev/null || true
    wait "$fake_server_pid" 2>/dev/null || true
    return "$status"
}

Describe 'run-benchmark.sh'
    Describe '--help'
        It 'exits successfully and shows the local defaults'
            When run script ./run-benchmark.sh --help
            The status should equal 0
            The output should include 'Usage:'
            The output should include 'Default: ./models/qwen3.6-35b-a3b/qwen3.6-35b-a3b-q4_k_m.gguf'
            The output should include 'Default: ./llama/turboquant-plus-tqp-v0.3.0/llama-server'
            The error should equal ''
        End
    End

    Describe 'argument validation'
        It 'rejects unknown options'
            When run script ./run-benchmark.sh --not-an-option
            The status should equal 1
            The output should equal ''
            The error should equal 'Error: unknown argument: --not-an-option'
        End


        It 'rejects unsupported Turbo modes'
            When run script ./run-benchmark.sh \
                --server ./spec/support/fake-llama-server \
                --model ./spec/support/fake-model.bin \
                --turbo 5 \
                --symmetric off

            The status should equal 1
            The output should equal ''
            The error should equal 'Error: --turbo must be 3 or 4'
        End

        It 'rejects unsupported symmetry modes'
            When run script ./run-benchmark.sh \
                --server ./spec/support/fake-llama-server \
                --model ./spec/support/fake-model.bin \
                --turbo 4 \
                --symmetric automatic

            The status should equal 1
            The output should equal ''
            The error should equal 'Error: --symmetric must be on or off'
        End

        It 'rejects a port outside the valid range'
            When run script ./run-benchmark.sh \
                --server ./spec/support/fake-llama-server \
                --model ./spec/support/fake-model.bin \
                --turbo 4 \
                --symmetric off \
                --port 0

            The status should equal 1
            The output should equal ''
            The error should equal 'Error: --port must be between 1 and 65535'
        End

        It 'requires enough measured runs for statistics'
            When run script ./run-benchmark.sh \
                --server ./spec/support/fake-llama-server \
                --model ./spec/support/fake-model.bin \
                --turbo 4 \
                --symmetric off \
                --runs 2

            The status should equal 1
            The output should equal ''
            The error should equal 'Error: --runs must be at least 3'
        End

        It 'requires generation room beyond the long prompt'
            When run script ./run-benchmark.sh \
                --server ./spec/support/fake-llama-server \
                --model ./spec/support/fake-model.bin \
                --turbo 4 \
                --symmetric off \
                --context 2048 \
                --long-tokens 1600

            The status should equal 1
            The output should equal ''
            The error should equal 'Error: --context must leave at least 512 tokens beyond --long-tokens'
        End

        It 'reports a missing model before starting the server'
            When run script ./run-benchmark.sh \
                --server ./spec/support/fake-llama-server \
                --model ./spec/support/not-present.bin \
                --turbo 4 \
                --symmetric off

            The status should equal 1
            The output should equal ''
            The error should equal 'Error: model not found: ./spec/support/not-present.bin'
        End

        It 'reports a non-executable server before running requests'
            When run script ./run-benchmark.sh \
                --server ./spec/support/fake-model.bin \
                --model ./spec/support/fake-model.bin \
                --turbo 4 \
                --symmetric off

            The status should equal 1
            The output should equal ''
            The error should equal 'Error: server not executable: ./spec/support/fake-model.bin'
        End

        It 'reports a missing runtime dependency'
            When call run_without_jq

            The status should equal 1
            The output should equal ''
            The error should equal 'Error: required command not found: jq'
        End

        It 'refuses to replace a server already using the endpoint'
            occupied_port=$((30000 + ($$ % 1000)))

            When call run_with_occupied_port

            The status should equal 1
            The output should equal ''
            The error should equal "Error: a server is already responding at http://127.0.0.1:$occupied_port; choose another --port or stop it"
        End

        It 'accepts leading zeroes in decimal numeric options'
            output_root="${SHELLSPEC_TMPBASE}/leading-zero-results"
            port="0$((28000 + ($$ % 1000)))"

            When run script ./run-benchmark.sh \
                --server ./spec/support/fake-llama-server \
                --model ./spec/support/fake-model.bin \
                --turbo 4 \
                --symmetric off \
                --runs 03 \
                --warmups 00 \
                --long-tokens 0512 \
                --context 02048 \
                --port "$port" \
                --output-dir "$output_root"

            The status should equal 0
            The output should include 'Benchmark completed successfully.'
            The error should equal ''
        End
    End

    Describe 'a controlled benchmark run'
        It 'writes raw measurements and a statistical summary'
            output_root="${SHELLSPEC_TMPBASE}/benchmark-results"
            port=$((20000 + ($$ % 20000)))

            When run script ./run-benchmark.sh \
                --server ./spec/support/fake-llama-server \
                --model ./spec/support/fake-model.bin \
                --turbo 4 \
                --symmetric off \
                --runs 3 \
                --warmups 0 \
                --long-tokens 512 \
                --context 2048 \
                --port "$port" \
                --output-dir "$output_root"

            The status should equal 0
            The output should include 'Benchmark completed successfully.'
            The error should equal ''
            The path "$output_root" should be directory

            run_dir="$(find "$output_root" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
            The path "$run_dir/results.csv" should be file
            The contents of file "$run_dir/results.csv" should include 'short-generation,measured,1'
            The contents of file "$run_dir/results.csv" should include 'long-context,measured,3'
            csv_lines="$(awk 'END { print NR }' "$run_dir/results.csv")"
            prompt_files="$(find "$run_dir/prompts" -type f | awk 'END { print NR }')"
            raw_files="$(find "$run_dir/raw" -type f | awk 'END { print NR }')"
            The value "$csv_lines" should equal 13
            The value "$prompt_files" should equal 4
            The value "$raw_files" should equal 12
            The path "$run_dir/summary.txt" should be file
            The contents of file "$run_dir/summary.txt" should include 'prompt tok/s'
            The contents of file "$run_dir/summary.txt" should include 'gen tok/s'
            The path "$run_dir/server.log" should be file
            The contents of file "$run_dir/server.log" should include '--cache-type-k turbo4'
        End
    End
End
