import csv
import math
import os
import statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from llama_benchmark.requests import Measurement


@dataclass(frozen=True, slots=True)
class MetricStats:
    """Summary statistics for one positive benchmark metric."""

    median: float
    p95: float
    mean: float
    minimum: float
    maximum: float


def metric_stats(values: list[float]) -> MetricStats | None:
    """Calculate median, nearest-rank P95, mean, and bounds."""
    positive = sorted(value for value in values if value > 0)
    if not positive:
        return None
    p95_index = math.ceil(0.95 * len(positive)) - 1
    return MetricStats(
        median=statistics.median(positive),
        p95=positive[p95_index],
        mean=statistics.fmean(positive),
        minimum=positive[0],
        maximum=positive[-1],
    )


CSV_HEADER = [
    "test",
    "phase",
    "run",
    "prompt_n",
    "prompt_ms",
    "prompt_tps",
    "predicted_n",
    "predicted_ms",
    "predicted_tps",
    "total_ms",
    "http_code",
    "response_file",
]


def write_reports(
    measurements: list[Measurement],
    *,
    csv_path: Path,
    summary_path: Path,
    model: Path,
    cache_type: str,
    symmetric: bool,
    context: int,
    runs: int,
    warmups: int,
    raw_dir: Path,
    server_log: Path,
) -> str:
    """Atomically write raw measurement CSV and its statistical summary."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=csv_path.parent, delete=False
    ) as stream:
        temporary_csv = Path(stream.name)
        writer = csv.writer(stream)
        writer.writerow(CSV_HEADER)
        for item in measurements:
            writer.writerow(
                [
                    item.test,
                    item.phase,
                    item.run,
                    item.prompt_n,
                    item.prompt_ms,
                    item.prompt_tps,
                    item.predicted_n,
                    item.predicted_ms,
                    item.predicted_tps,
                    item.total_ms,
                    item.http_code,
                    item.response_file,
                ]
            )
    os.replace(temporary_csv, csv_path)

    lines = [
        "llama.cpp server benchmark",
        "==========================",
        "",
        f"Model:       {model}",
        f"KV cache:    {cache_type}",
        f"Symmetric:   {'on' if symmetric else 'off'}",
        f"Context:     {context}",
        f"Runs:        {runs} measured, {warmups} warm-up",
        f"Date:        {datetime.now().astimezone().isoformat()}",
        "",
        "Test                 Metric       Median          P95         Mean      Min/Max",
    ]
    test_names = list(dict.fromkeys(item.test for item in measurements))
    for test_name in test_names:
        measured = [
            item
            for item in measurements
            if item.test == test_name and item.phase == "measured"
        ]
        for label, values in (
            ("prompt tok/s", [item.prompt_tps for item in measured]),
            ("gen tok/s", [item.predicted_tps for item in measured]),
        ):
            stats = metric_stats(values)
            if stats is not None:
                lines.append(
                    f"{test_name:<20} {label:<12} {stats.median:12.2f} "
                    f"{stats.p95:12.2f} {stats.mean:12.2f} "
                    f"{stats.minimum:.2f}/{stats.maximum:.2f}"
                )
                test_name = ""
    lines.extend(["", "Measured token counts", "---------------------"])
    for test_name in test_names:
        first = next(
            (
                item
                for item in measurements
                if item.test == test_name and item.phase == "measured"
            ),
            None,
        )
        if first is not None:
            lines.append(
                f"{test_name:<20} prompt={first.prompt_n}, "
                f"generated={first.predicted_n}"
            )
    lines.extend(
        [
            "",
            "Files",
            "-----",
            f"CSV:        {csv_path}",
            f"Raw JSON:   {raw_dir}",
            f"Server log: {server_log}",
        ]
    )
    summary = "\n".join(lines) + "\n"
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=summary_path.parent, delete=False
    ) as stream:
        temporary_summary = Path(stream.name)
        stream.write(summary)
    os.replace(temporary_summary, summary_path)
    return summary
