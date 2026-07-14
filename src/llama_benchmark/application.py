from datetime import datetime
from pathlib import Path

import httpx

from llama_benchmark.cli import Config
from llama_benchmark.reporting import write_reports
from llama_benchmark.requests import CompletionClient, execute_all
from llama_benchmark.scenarios import scenarios, write_prompts
from llama_benchmark.server import ServerProcess, ensure_endpoint_available


def create_run_directory(config: Config) -> Path:
    """Create and return the timestamped scenario output directory."""
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    model_name = (
        config.model.stem if config.model.suffix == ".gguf" else config.model.name
    )
    name = (
        f"{stamp}-{model_name}-turbo{config.turbo}-"
        f"symmetric-{'on' if config.symmetric else 'off'}"
    )
    run_dir = config.output_dir / name
    run_dir.mkdir(parents=True)
    return run_dir


def run_benchmark(config: Config) -> Path:
    """Execute a complete benchmark and return its output directory."""
    ensure_endpoint_available(config)
    run_dir = create_run_directory(config)
    raw_dir = run_dir / "raw"
    prompt_dir = run_dir / "prompts"
    configured = scenarios(long_tokens=config.long_tokens)
    write_prompts(configured, prompt_dir)
    server_log = run_dir / "server.log"

    with ServerProcess(config, server_log):
        with httpx.Client(timeout=1800.0) as http:
            client = CompletionClient(
                http, base_url=f"http://{config.host}:{config.port}"
            )
            measurements = execute_all(
                client,
                configured,
                warmups=config.warmups,
                runs=config.runs,
                raw_dir=raw_dir,
            )

    summary = write_reports(
        measurements,
        csv_path=run_dir / "results.csv",
        summary_path=run_dir / "summary.txt",
        model=config.model,
        cache_type=f"turbo{config.turbo}",
        symmetric=config.symmetric,
        context=config.context,
        runs=config.runs,
        warmups=config.warmups,
        raw_dir=raw_dir,
        server_log=server_log,
    )
    print(summary, end="")
    print("\nBenchmark completed successfully.")
    return run_dir
