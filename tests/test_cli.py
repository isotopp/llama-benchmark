import subprocess
import sys
from pathlib import Path

import pytest

from llama_benchmark import main, parse_config


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


def test_cli_requires_a_symmetry_mode() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "llama_benchmark", "--turbo", "4"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "--symmetric" in completed.stderr


def test_parse_config_returns_all_command_line_overrides(tmp_path: Path) -> None:
    model = tmp_path / "model.gguf"
    model.touch()
    server = tmp_path / "llama server"
    server.touch(mode=0o755)
    output = tmp_path / "measurements"

    config = parse_config(
        [
            "--model",
            str(model),
            "--server",
            str(server),
            "--turbo",
            "3",
            "--symmetric",
            "on",
            "--host",
            "localhost",
            "--port",
            "018080",
            "--context",
            "032768",
            "--long-tokens",
            "04096",
            "--runs",
            "07",
            "--warmups",
            "02",
            "--output-dir",
            str(output),
            "--server-arg=--threads",
            "--server-arg=8",
        ]
    )

    assert config.model == model
    assert config.server == server
    assert config.turbo == 3
    assert config.symmetric is True
    assert config.host == "localhost"
    assert config.port == 18080
    assert config.context == 32768
    assert config.long_tokens == 4096
    assert config.runs == 7
    assert config.warmups == 2
    assert config.output_dir == output
    assert config.server_args == ("--threads", "8")


def test_parse_config_rejects_a_missing_model(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing_model = tmp_path / "missing.gguf"

    with pytest.raises(SystemExit, match="2"):
        parse_config(
            [
                "--model",
                str(missing_model),
                "--server",
                str(tmp_path),
                "--turbo",
                "4",
                "--symmetric",
                "off",
            ]
        )

    assert f"model not found: {missing_model}" in capsys.readouterr().err


def test_parse_config_rejects_a_non_executable_server(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    model = tmp_path / "model.gguf"
    model.touch()
    server = tmp_path / "llama-server"
    server.touch()

    with pytest.raises(SystemExit, match="2"):
        parse_config(
            [
                "--model",
                str(model),
                "--server",
                str(server),
                "--turbo",
                "4",
                "--symmetric",
                "off",
            ]
        )

    assert f"server not executable: {server}" in capsys.readouterr().err


def test_parse_config_rejects_a_port_outside_the_valid_range(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    model = tmp_path / "model.gguf"
    model.touch()
    server = tmp_path / "llama-server"
    server.touch(mode=0o755)

    with pytest.raises(SystemExit, match="2"):
        parse_config(
            [
                "--model",
                str(model),
                "--server",
                str(server),
                "--turbo",
                "4",
                "--symmetric",
                "off",
                "--port",
                "0",
            ]
        )

    assert "--port must be between 1 and 65535" in capsys.readouterr().err


def test_parse_config_requires_a_minimum_context(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    model = tmp_path / "model.gguf"
    model.touch()
    server = tmp_path / "llama-server"
    server.touch(mode=0o755)

    with pytest.raises(SystemExit, match="2"):
        parse_config(
            [
                "--model",
                str(model),
                "--server",
                str(server),
                "--turbo",
                "4",
                "--symmetric",
                "off",
                "--context",
                "1024",
            ]
        )

    assert "--context must be at least 2048" in capsys.readouterr().err


def test_parse_config_requires_a_minimum_long_prompt(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    model = tmp_path / "model.gguf"
    model.touch()
    server = tmp_path / "llama-server"
    server.touch(mode=0o755)

    with pytest.raises(SystemExit, match="2"):
        parse_config(
            [
                "--model",
                str(model),
                "--server",
                str(server),
                "--turbo",
                "4",
                "--symmetric",
                "off",
                "--long-tokens",
                "511",
            ]
        )

    assert "--long-tokens must be at least 512" in capsys.readouterr().err


def test_parse_config_requires_three_measured_runs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    model = tmp_path / "model.gguf"
    model.touch()
    server = tmp_path / "llama-server"
    server.touch(mode=0o755)

    with pytest.raises(SystemExit, match="2"):
        parse_config(
            [
                "--model",
                str(model),
                "--server",
                str(server),
                "--turbo",
                "4",
                "--symmetric",
                "off",
                "--runs",
                "2",
            ]
        )

    assert "--runs must be at least 3" in capsys.readouterr().err


def test_parse_config_requires_generation_room_after_the_long_prompt(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    model = tmp_path / "model.gguf"
    model.touch()
    server = tmp_path / "llama-server"
    server.touch(mode=0o755)

    with pytest.raises(SystemExit, match="2"):
        parse_config(
            [
                "--model",
                str(model),
                "--server",
                str(server),
                "--turbo",
                "4",
                "--symmetric",
                "off",
                "--context",
                "2048",
                "--long-tokens",
                "1536",
            ]
        )

    assert (
        "--context must leave at least 512 tokens beyond --long-tokens"
        in capsys.readouterr().err
    )


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (["--turbo", "5", "--symmetric", "off"], "invalid choice"),
        (["--turbo", "4", "--symmetric", "automatic"], "invalid choice"),
        (
            ["--turbo", "4", "--symmetric", "off", "--warmups", "-1"],
            "must be a non-negative integer",
        ),
    ],
)
def test_cli_rejects_invalid_enum_and_unsigned_values(
    arguments: list[str], message: str
) -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "llama_benchmark", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert message in completed.stderr


def test_default_assets_are_resolved_from_the_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model = tmp_path / "models" / "qwen3.6-35b-a3b" / "qwen3.6-35b-a3b-q4_k_m.gguf"
    model.parent.mkdir(parents=True)
    model.touch()
    server = tmp_path / "llama" / "turboquant-plus-tqp-v0.3.0" / "llama-server"
    server.parent.mkdir(parents=True)
    server.touch(mode=0o755)
    monkeypatch.chdir(tmp_path)

    config = parse_config(["--turbo", "4", "--symmetric", "off"])

    assert config.model == model
    assert config.server == server
    assert config.output_dir == tmp_path / "benchmark_results"


def test_relative_overrides_are_resolved_from_the_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model = tmp_path / "custom" / "model.gguf"
    model.parent.mkdir()
    model.touch()
    server = tmp_path / "bin" / "llama-server"
    server.parent.mkdir()
    server.touch(mode=0o755)
    monkeypatch.chdir(tmp_path)

    config = parse_config(
        [
            "--model",
            "custom/model.gguf",
            "--server",
            "bin/llama-server",
            "--output-dir",
            "measurements",
            "--turbo",
            "4",
            "--symmetric",
            "off",
        ]
    )

    assert config.model == model
    assert config.server == server
    assert config.output_dir == tmp_path / "measurements"


def test_main_does_not_hide_unexpected_programmer_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model = tmp_path / "model.gguf"
    model.touch()
    server = tmp_path / "llama-server"
    server.touch(mode=0o755)

    def fail_unexpectedly(config: object) -> None:
        del config
        raise ValueError("programmer defect")

    monkeypatch.setattr("llama_benchmark.application.run_benchmark", fail_unexpectedly)

    with pytest.raises(ValueError, match="programmer defect"):
        main(
            [
                "--model",
                str(model),
                "--server",
                str(server),
                "--turbo",
                "4",
                "--symmetric",
                "off",
            ]
        )
