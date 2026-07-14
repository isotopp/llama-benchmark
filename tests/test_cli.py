import subprocess
import sys


def test_module_help_describes_the_benchmark_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "llama_benchmark", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "usage: llama-benchmark" in completed.stdout
    assert "--turbo" in completed.stdout
    assert "--symmetric" in completed.stdout
    assert completed.stderr == ""
