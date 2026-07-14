from dataclasses import dataclass
from collections.abc import Callable
from pathlib import Path

import httpx

from llama_benchmark.scenarios import Scenario, completion_request
from llama_benchmark.errors import BenchmarkError


class CompletionError(BenchmarkError):
    """A completion request failed or returned unusable data."""


@dataclass(frozen=True, slots=True)
class Measurement:
    """One warm-up or measured llama-server response."""

    test: str
    phase: str
    run: int
    prompt_n: int
    prompt_ms: float
    prompt_tps: float
    predicted_n: int
    predicted_ms: float
    predicted_tps: float
    total_ms: float
    http_code: int
    response_file: Path


class CompletionClient:
    """Execute completion requests and preserve raw responses."""

    def __init__(self, http: httpx.Client, *, base_url: str) -> None:
        self.http = http
        self.base_url = base_url.rstrip("/")

    def execute(
        self,
        scenario: Scenario,
        *,
        phase: str,
        run: int,
        raw_dir: Path,
    ) -> Measurement:
        """Execute one scenario request and return its timings."""
        raw_dir.mkdir(parents=True, exist_ok=True)
        response_file = raw_dir / f"{scenario.name}-{phase}-{run}.json"
        try:
            response = self.http.post(
                f"{self.base_url}/completion", json=completion_request(scenario)
            )
        except httpx.RequestError as error:
            raise CompletionError(f"completion request failed: {error}") from error
        response_file.write_bytes(response.content)
        if not response.is_success:
            raise CompletionError(
                f"completion request returned HTTP {response.status_code}"
            )
        try:
            payload = response.json()
        except ValueError as error:
            raise CompletionError(
                "completion response contains invalid JSON"
            ) from error
        try:
            timings = payload["timings"]
            prompt_ms = float(timings["prompt_ms"])
            predicted_ms = float(timings["predicted_ms"])
            return Measurement(
                test=scenario.name,
                phase=phase,
                run=run,
                prompt_n=int(timings["prompt_n"]),
                prompt_ms=prompt_ms,
                prompt_tps=float(timings["prompt_per_second"]),
                predicted_n=int(timings["predicted_n"]),
                predicted_ms=predicted_ms,
                predicted_tps=float(timings["predicted_per_second"]),
                total_ms=prompt_ms + predicted_ms,
                http_code=response.status_code,
                response_file=response_file,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise CompletionError(
                "completion response has invalid timing data"
            ) from error


def execute_all(
    client: CompletionClient,
    configured: tuple[Scenario, ...],
    *,
    warmups: int,
    runs: int,
    raw_dir: Path,
    on_measurement: Callable[[Measurement], None] | None = None,
) -> list[Measurement]:
    """Execute every configured warm-up and measured scenario request."""
    measurements = []
    for scenario in configured:
        for run in range(1, warmups + 1):
            measurement = client.execute(
                scenario, phase="warmup", run=run, raw_dir=raw_dir
            )
            measurements.append(measurement)
            if on_measurement is not None:
                on_measurement(measurement)
        for run in range(1, runs + 1):
            measurement = client.execute(
                scenario, phase="measured", run=run, raw_dir=raw_dir
            )
            measurements.append(measurement)
            if on_measurement is not None:
                on_measurement(measurement)
    return measurements
