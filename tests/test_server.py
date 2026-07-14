import socket
import json
from pathlib import Path

import httpx
import pytest

from llama_benchmark import Config
from llama_benchmark.server import ServerProcess


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def test_server_process_starts_becomes_healthy_and_stops(tmp_path: Path) -> None:
    port = free_port()
    log_path = tmp_path / "server.log"
    config = Config(
        model=PROJECT_ROOT / "spec/support/fake-model.bin",
        server=PROJECT_ROOT / "spec/support/fake-llama-server",
        turbo=4,
        symmetric=False,
        host="127.0.0.1",
        port=port,
        context=2048,
        long_tokens=512,
        runs=3,
        warmups=0,
        output_dir=tmp_path,
        server_args=("--threads", "2"),
    )

    with ServerProcess(config, log_path, startup_timeout=3.0):
        response = httpx.get(f"http://127.0.0.1:{port}/health")
        assert response.status_code == 200

    with pytest.raises(httpx.ConnectError):
        httpx.get(f"http://127.0.0.1:{port}/health")

    log = log_path.read_text(encoding="utf-8")
    assert "--cache-type-k turbo4" in log
    assert "--cache-type-v turbo4" in log
    assert "--threads 2" in log


def test_server_process_refuses_an_occupied_endpoint(tmp_path: Path) -> None:
    port = free_port()
    config = Config(
        model=PROJECT_ROOT / "spec/support/fake-model.bin",
        server=PROJECT_ROOT / "spec/support/fake-llama-server",
        turbo=3,
        symmetric=False,
        host="127.0.0.1",
        port=port,
        context=2048,
        long_tokens=512,
        runs=3,
        warmups=0,
        output_dir=tmp_path,
        server_args=(),
    )

    with ServerProcess(config, tmp_path / "first.log", startup_timeout=3.0):
        with pytest.raises(RuntimeError, match="a server is already responding"):
            with ServerProcess(config, tmp_path / "second.log", startup_timeout=3.0):
                pass


def test_server_process_reports_early_child_exit(tmp_path: Path) -> None:
    config = Config(
        model=PROJECT_ROOT / "spec/support/fake-model.bin",
        server=PROJECT_ROOT / "tests/support/exiting-server",
        turbo=4,
        symmetric=False,
        host="127.0.0.1",
        port=free_port(),
        context=2048,
        long_tokens=512,
        runs=3,
        warmups=0,
        output_dir=tmp_path,
        server_args=(),
    )

    with pytest.raises(RuntimeError) as raised:
        with ServerProcess(config, tmp_path / "server.log", startup_timeout=1.0):
            pass

    message = str(raised.value)
    assert "exited during startup (status 17)" in message
    assert "loading fake model" in message
    assert "fatal: incompatible model" in message


def test_server_process_reports_only_the_last_80_log_lines(tmp_path: Path) -> None:
    config = Config(
        model=PROJECT_ROOT / "spec/support/fake-model.bin",
        server=PROJECT_ROOT / "tests/support/noisy-exiting-server",
        turbo=4,
        symmetric=False,
        host="127.0.0.1",
        port=free_port(),
        context=2048,
        long_tokens=512,
        runs=3,
        warmups=0,
        output_dir=tmp_path,
        server_args=(),
    )

    with pytest.raises(RuntimeError) as raised:
        with ServerProcess(config, tmp_path / "server.log", startup_timeout=1.0):
            pass

    lines = str(raised.value).splitlines()
    assert len(lines) == 81
    assert lines[0] == "llama-server exited during startup (status 23)"
    assert lines[1] == "diagnostic-021"
    assert lines[-1] == "diagnostic-100"


def test_server_process_times_out_and_terminates_the_child(tmp_path: Path) -> None:
    config = Config(
        model=PROJECT_ROOT / "spec/support/fake-model.bin",
        server=PROJECT_ROOT / "tests/support/stalled-server",
        turbo=4,
        symmetric=False,
        host="127.0.0.1",
        port=free_port(),
        context=2048,
        long_tokens=512,
        runs=3,
        warmups=0,
        output_dir=tmp_path,
        server_args=(),
    )

    with pytest.raises(RuntimeError) as raised:
        with ServerProcess(config, tmp_path / "server.log", startup_timeout=0.1):
            pass

    message = str(raised.value)
    assert f"http://127.0.0.1:{config.port}/health" in message
    assert "within 0.1 seconds" in message


def test_server_process_enables_symmetric_turbo_environment(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    config = Config(
        model=PROJECT_ROOT / "spec/support/fake-model.bin",
        server=PROJECT_ROOT / "spec/support/fake-llama-server",
        turbo=4,
        symmetric=True,
        host="127.0.0.1",
        port=free_port(),
        context=2048,
        long_tokens=512,
        runs=3,
        warmups=0,
        output_dir=tmp_path,
        server_args=("--state-file", str(state_path)),
    )

    with ServerProcess(config, tmp_path / "server.log", startup_timeout=3.0):
        pass

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["turbo_auto_asymmetric"] == "0"


def test_server_process_removes_inherited_asymmetric_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TURBO_AUTO_ASYMMETRIC", "inherited")
    state_path = tmp_path / "state.json"
    config = Config(
        model=PROJECT_ROOT / "spec/support/fake-model.bin",
        server=PROJECT_ROOT / "spec/support/fake-llama-server",
        turbo=4,
        symmetric=False,
        host="127.0.0.1",
        port=free_port(),
        context=2048,
        long_tokens=512,
        runs=3,
        warmups=0,
        output_dir=tmp_path,
        server_args=("--state-file", str(state_path)),
    )

    with ServerProcess(config, tmp_path / "server.log", startup_timeout=3.0):
        pass

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["turbo_auto_asymmetric"] is None


def test_server_process_cleans_up_after_interruption(tmp_path: Path) -> None:
    port = free_port()
    config = Config(
        model=PROJECT_ROOT / "spec/support/fake-model.bin",
        server=PROJECT_ROOT / "spec/support/fake-llama-server",
        turbo=4,
        symmetric=False,
        host="127.0.0.1",
        port=port,
        context=2048,
        long_tokens=512,
        runs=3,
        warmups=0,
        output_dir=tmp_path,
        server_args=(),
    )

    with pytest.raises(KeyboardInterrupt):
        with ServerProcess(config, tmp_path / "server.log", startup_timeout=3.0):
            raise KeyboardInterrupt

    with pytest.raises(httpx.ConnectError):
        httpx.get(f"http://127.0.0.1:{port}/health")
