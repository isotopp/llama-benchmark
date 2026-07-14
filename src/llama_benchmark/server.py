from __future__ import annotations

import os
import shlex
import subprocess
import time
from pathlib import Path
from types import TracebackType

import httpx

from llama_benchmark.cli import Config


class ServerProcess:
    """Own one configured llama-server child process."""

    def __init__(
        self, config: Config, log_path: Path, *, startup_timeout: float = 180.0
    ) -> None:
        self.config = config
        self.log_path = log_path
        self.startup_timeout = startup_timeout
        self._process: subprocess.Popen[bytes] | None = None
        self._log = None

    @property
    def health_url(self) -> str:
        """Return the configured health endpoint."""
        return f"http://{self.config.host}:{self.config.port}/health"

    def __enter__(self) -> ServerProcess:
        if self._is_healthy():
            raise RuntimeError(
                f"a server is already responding at {self.health_url}; "
                "choose another --port or stop it"
            )

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log = self.log_path.open("w", encoding="utf-8")
        command = self._command()
        self._log.write(f"Command: {shlex.join(command)}\n")
        self._log.flush()

        environment = os.environ.copy()
        if self.config.symmetric:
            environment["TURBO_AUTO_ASYMMETRIC"] = "0"
        else:
            environment.pop("TURBO_AUTO_ASYMMETRIC", None)

        self._process = subprocess.Popen(
            command,
            stdout=self._log,
            stderr=subprocess.STDOUT,
            env=environment,
        )
        try:
            self._wait_until_healthy()
        except BaseException:
            self.stop()
            raise
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc_value, traceback
        self.stop()

    def stop(self) -> None:
        """Terminate and reap the child process, if one was started."""
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
        self._process = None
        if self._log is not None:
            self._log.close()
            self._log = None

    def _command(self) -> list[str]:
        cache_type = f"turbo{self.config.turbo}"
        return [
            str(self.config.server),
            "-m",
            str(self.config.model),
            "--cache-type-k",
            cache_type,
            "--cache-type-v",
            cache_type,
            "-ngl",
            "all",
            "-fa",
            "on",
            "-c",
            str(self.config.context),
            "-np",
            "1",
            "--jinja",
            "--host",
            self.config.host,
            "--port",
            str(self.config.port),
            *self.config.server_args,
        ]

    def _is_healthy(self) -> bool:
        try:
            response = httpx.get(self.health_url, timeout=1.0)
        except httpx.RequestError:
            return False
        return response.is_success

    def _wait_until_healthy(self) -> None:
        assert self._process is not None
        deadline = time.monotonic() + self.startup_timeout
        while time.monotonic() < deadline:
            status = self._process.poll()
            if status is not None:
                raise RuntimeError(
                    f"llama-server exited during startup (status {status})"
                )
            if self._is_healthy():
                return
            time.sleep(0.05)
        raise RuntimeError("server did not become healthy")
