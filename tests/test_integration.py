import csv
import socket
import subprocess
import sys
from pathlib import Path


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
