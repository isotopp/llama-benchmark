import csv
from pathlib import Path

from llama_benchmark.reporting import metric_stats, write_reports
from llama_benchmark.requests import Measurement


def test_metric_stats_cover_median_p95_mean_and_bounds() -> None:
    odd = metric_stats([1.0, 2.0, 100.0])
    even = metric_stats([1.0, 2.0, 3.0, 100.0])

    assert odd is not None
    assert odd.median == 2.0
    assert odd.p95 == 100.0
    assert odd.mean == 103.0 / 3.0
    assert odd.minimum == 1.0
    assert odd.maximum == 100.0
    assert even is not None
    assert even.median == 2.5
    assert even.p95 == 100.0
    assert metric_stats([]) is None


def test_write_reports_keeps_warmups_out_of_the_summary(tmp_path: Path) -> None:
    raw = tmp_path / "raw.json"
    measurements = [
        Measurement(
            test="short-generation",
            phase=phase,
            run=run,
            prompt_n=100,
            prompt_ms=50.0,
            prompt_tps=prompt_tps,
            predicted_n=10,
            predicted_ms=100.0,
            predicted_tps=predicted_tps,
            total_ms=150.0,
            http_code=200,
            response_file=raw,
        )
        for phase, run, prompt_tps, predicted_tps in [
            ("warmup", 1, 9999.0, 9999.0),
            ("measured", 1, 100.0, 10.0),
            ("measured", 2, 200.0, 20.0),
        ]
    ]
    csv_path = tmp_path / "results.csv"
    summary_path = tmp_path / "summary.txt"

    summary = write_reports(
        measurements,
        csv_path=csv_path,
        summary_path=summary_path,
        model=Path("model.gguf"),
        cache_type="turbo4",
        symmetric=False,
        context=65536,
        runs=2,
        warmups=1,
        raw_dir=tmp_path / "raw",
        server_log=tmp_path / "server.log",
    )

    with csv_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.reader(stream))
    assert len(rows) == 4
    assert rows[0][0:4] == ["test", "phase", "run", "prompt_n"]
    assert "150.00" in summary
    assert "15.00" in summary
    assert "9999" not in summary
    assert "prompt=100, generated=10" in summary
    assert summary_path.read_text(encoding="utf-8") == summary
