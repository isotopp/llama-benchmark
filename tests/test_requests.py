import json
from pathlib import Path

import httpx
import pytest

from llama_benchmark.requests import CompletionClient, CompletionError, execute_all
from llama_benchmark.scenarios import scenarios


def successful_response() -> dict[str, object]:
    return {
        "content": "fake completion",
        "timings": {
            "prompt_n": 100,
            "prompt_ms": 50.0,
            "prompt_per_second": 2000.0,
            "predicted_n": 10,
            "predicted_ms": 100.0,
            "predicted_per_second": 100.0,
        },
    }


def test_completion_client_records_raw_response_before_returning_measurement(
    tmp_path: Path,
) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url == "http://127.0.0.1:8080/completion"
        body = json.loads(request.content)
        assert body["cache_prompt"] is False
        return httpx.Response(200, json=successful_response())

    with httpx.Client(transport=httpx.MockTransport(respond)) as http:
        client = CompletionClient(http, base_url="http://127.0.0.1:8080")
        measurement = client.execute(
            scenarios(long_tokens=512)[0],
            phase="measured",
            run=1,
            raw_dir=tmp_path,
        )

    raw_path = tmp_path / "short-generation-measured-1.json"
    assert json.loads(raw_path.read_text(encoding="utf-8")) == successful_response()
    assert measurement.test == "short-generation"
    assert measurement.phase == "measured"
    assert measurement.run == 1
    assert measurement.prompt_n == 100
    assert measurement.prompt_ms == 50.0
    assert measurement.prompt_tps == 2000.0
    assert measurement.predicted_n == 10
    assert measurement.predicted_ms == 100.0
    assert measurement.predicted_tps == 100.0
    assert measurement.total_ms == 150.0
    assert measurement.http_code == 200
    assert measurement.response_file == raw_path


def test_completion_client_preserves_an_http_error_response(tmp_path: Path) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "not ready"})

    with httpx.Client(transport=httpx.MockTransport(respond)) as http:
        client = CompletionClient(http, base_url="http://127.0.0.1:8080")
        with pytest.raises(CompletionError, match="HTTP 503"):
            client.execute(
                scenarios(long_tokens=512)[0],
                phase="warmup",
                run=1,
                raw_dir=tmp_path,
            )

    raw_path = tmp_path / "short-generation-warmup-1.json"
    assert json.loads(raw_path.read_text(encoding="utf-8")) == {"error": "not ready"}


def test_completion_client_reports_transport_failure(tmp_path: Path) -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with httpx.Client(transport=httpx.MockTransport(fail)) as http:
        client = CompletionClient(http, base_url="http://127.0.0.1:8080")
        with pytest.raises(CompletionError, match="request failed: connection refused"):
            client.execute(
                scenarios(long_tokens=512)[0],
                phase="measured",
                run=1,
                raw_dir=tmp_path,
            )

    assert list(tmp_path.iterdir()) == []


def test_completion_client_preserves_and_rejects_invalid_json(tmp_path: Path) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not json")

    with httpx.Client(transport=httpx.MockTransport(respond)) as http:
        client = CompletionClient(http, base_url="http://127.0.0.1:8080")
        with pytest.raises(CompletionError, match="invalid JSON"):
            client.execute(
                scenarios(long_tokens=512)[0],
                phase="measured",
                run=1,
                raw_dir=tmp_path,
            )

    assert (tmp_path / "short-generation-measured-1.json").read_bytes() == b"not json"


def test_completion_client_rejects_missing_timing_data(tmp_path: Path) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"content": "missing timings"})

    with httpx.Client(transport=httpx.MockTransport(respond)) as http:
        client = CompletionClient(http, base_url="http://127.0.0.1:8080")
        with pytest.raises(CompletionError, match="invalid timing data"):
            client.execute(
                scenarios(long_tokens=512)[0],
                phase="measured",
                run=1,
                raw_dir=tmp_path,
            )


def test_execute_all_runs_warmups_before_measured_requests(tmp_path: Path) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=successful_response())

    with httpx.Client(transport=httpx.MockTransport(respond)) as http:
        client = CompletionClient(http, base_url="http://127.0.0.1:8080")
        measurements = execute_all(
            client,
            scenarios(long_tokens=512),
            warmups=1,
            runs=3,
            raw_dir=tmp_path,
        )

    assert len(measurements) == 16
    for offset in range(0, 16, 4):
        assert [item.phase for item in measurements[offset : offset + 4]] == [
            "warmup",
            "measured",
            "measured",
            "measured",
        ]
        assert [item.run for item in measurements[offset : offset + 4]] == [1, 1, 2, 3]
