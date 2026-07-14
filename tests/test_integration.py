import csv
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def test_python_command_runs_all_scenarios_and_writes_artifacts(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "benchmark-results"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "llama_benchmark",
            "--server",
            str(PROJECT_ROOT / "spec/support/fake-llama-server"),
            "--model",
            str(PROJECT_ROOT / "spec/support/fake-model.bin"),
            "--turbo",
            "4",
            "--symmetric",
            "off",
            "--runs",
            "3",
            "--warmups",
            "0",
            "--long-tokens",
            "512",
            "--context",
            "2048",
            "--port",
            str(free_port()),
            "--output-dir",
            str(output_root),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Benchmark completed successfully." in completed.stdout
    [run_dir] = list(output_root.iterdir())
    assert sorted(path.name for path in (run_dir / "prompts").iterdir()) == [
        "analysis.txt",
        "code.txt",
        "long-context.txt",
        "short.txt",
    ]
    assert len(list((run_dir / "raw").iterdir())) == 12
    with (run_dir / "results.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 12
    assert {row["test"] for row in rows} == {
        "short-generation",
        "numeric-analysis",
        "code-generation",
        "long-context",
    }
    assert {row["phase"] for row in rows} == {"measured"}
    summary = (run_dir / "summary.txt").read_text(encoding="utf-8")
    assert "prompt tok/s" in summary
    assert "gen tok/s" in summary
    assert "--cache-type-k turbo4" in (run_dir / "server.log").read_text(
        encoding="utf-8"
    )


def test_occupied_endpoint_is_rejected_before_creating_output(
    tmp_path: Path,
) -> None:
    port = free_port()
    fake_server = subprocess.Popen(
        [
            str(PROJECT_ROOT / "spec/support/fake-llama-server"),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ]
    )
    try:
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            try:
                if httpx.get(f"http://127.0.0.1:{port}/health").is_success:
                    break
            except httpx.RequestError:
                time.sleep(0.02)
        output_root = tmp_path / "benchmark-results"

        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "llama_benchmark",
                "--server",
                str(PROJECT_ROOT / "spec/support/fake-llama-server"),
                "--model",
                str(PROJECT_ROOT / "spec/support/fake-model.bin"),
                "--turbo",
                "4",
                "--symmetric",
                "off",
                "--port",
                str(port),
                "--output-dir",
                str(output_root),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert completed.returncode != 0
        assert not output_root.exists()
    finally:
        fake_server.terminate()
        fake_server.wait(timeout=3)


def test_request_failure_retains_partial_run_evidence(tmp_path: Path) -> None:
    output_root = tmp_path / "benchmark-results"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "llama_benchmark",
            "--server",
            str(PROJECT_ROOT / "spec/support/fake-llama-server"),
            "--model",
            str(PROJECT_ROOT / "spec/support/fake-model.bin"),
            "--turbo",
            "4",
            "--symmetric",
            "off",
            "--port",
            str(free_port()),
            "--output-dir",
            str(output_root),
            "--server-arg=--completion-status",
            "--server-arg=503",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode != 0
    assert "Error: completion request returned HTTP 503" in completed.stderr
    assert "Traceback" not in completed.stderr
    [run_dir] = list(output_root.iterdir())
    assert len(list((run_dir / "prompts").iterdir())) == 4
    assert (run_dir / "raw" / "short-generation-warmup-1.json").is_file()
    assert (run_dir / "server.log").is_file()


def test_expected_server_failure_is_reported_without_a_traceback(
    tmp_path: Path,
) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "llama_benchmark",
            "--server",
            str(PROJECT_ROOT / "tests/support/exiting-server"),
            "--model",
            str(PROJECT_ROOT / "spec/support/fake-model.bin"),
            "--turbo",
            "4",
            "--symmetric",
            "off",
            "--port",
            str(free_port()),
            "--output-dir",
            str(tmp_path / "results"),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 1
    assert "Error: llama-server exited during startup (status 17)" in completed.stderr
    assert "fatal: incompatible model" in completed.stderr
    assert "Traceback" not in completed.stderr


def test_expected_filesystem_failure_is_reported_without_a_traceback(
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "not-a-directory"
    output_file.write_text("occupied", encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "llama_benchmark",
            "--server",
            str(PROJECT_ROOT / "spec/support/fake-llama-server"),
            "--model",
            str(PROJECT_ROOT / "spec/support/fake-model.bin"),
            "--turbo",
            "4",
            "--symmetric",
            "off",
            "--port",
            str(free_port()),
            "--output-dir",
            str(output_file),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert "Error:" in completed.stderr
    assert str(output_file) in completed.stderr
    assert "Traceback" not in completed.stderr


@pytest.mark.parametrize("termination_signal", [signal.SIGTERM, signal.SIGHUP])
def test_termination_signal_reaps_the_child_server(
    tmp_path: Path, termination_signal: signal.Signals
) -> None:
    pid_file = tmp_path / "child.pid"
    benchmark = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "llama_benchmark",
            "--server",
            str(PROJECT_ROOT / "tests/support/stalled-server"),
            "--model",
            str(PROJECT_ROOT / "spec/support/fake-model.bin"),
            "--turbo",
            "4",
            "--symmetric",
            "off",
            "--port",
            str(free_port()),
            "--output-dir",
            str(tmp_path / "results"),
            "--server-arg=--pid-file",
            f"--server-arg={pid_file}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    child_pid: int | None = None
    try:
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and not pid_file.exists():
            time.sleep(0.02)
        assert pid_file.is_file()
        child_pid = int(pid_file.read_text(encoding="utf-8"))

        benchmark.send_signal(termination_signal)
        assert benchmark.wait(timeout=3) == -termination_signal

        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)
    finally:
        if benchmark.poll() is None:
            benchmark.kill()
            benchmark.wait()
        if child_pid is not None:
            try:
                os.kill(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
