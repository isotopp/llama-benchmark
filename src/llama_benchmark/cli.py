import argparse
import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Config:
    """Validated benchmark configuration."""

    model: Path
    server: Path
    turbo: int
    symmetric: bool
    host: str
    port: int
    context: int
    long_tokens: int
    runs: int
    warmups: int
    output_dir: Path
    server_args: tuple[str, ...]


def decimal(value: str) -> int:
    """Parse an unsigned decimal command-line value."""
    if not value.isdecimal():
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return int(value, 10)


def create_parser() -> argparse.ArgumentParser:
    """Create the public command-line parser."""
    working_directory = Path.cwd()
    parser = argparse.ArgumentParser(
        prog="llama-benchmark",
        description="Run repeatable benchmarks against a local llama-server.",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=working_directory
        / "models/qwen3.6-35b-a3b/qwen3.6-35b-a3b-q4_k_m.gguf",
    )
    parser.add_argument(
        "--server",
        type=Path,
        default=working_directory / "llama/turboquant-plus-tqp-v0.3.0/llama-server",
    )
    parser.add_argument("--turbo", type=decimal, choices=(3, 4), required=True)
    parser.add_argument("--symmetric", choices=("on", "off"), required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=decimal, default=8080)
    parser.add_argument("--context", type=decimal, default=65536)
    parser.add_argument("--long-tokens", type=decimal, default=8192)
    parser.add_argument("--runs", type=decimal, default=5)
    parser.add_argument("--warmups", type=decimal, default=1)
    parser.add_argument(
        "--output-dir", type=Path, default=working_directory / "benchmark_results"
    )
    parser.add_argument("--server-arg", action="append", default=[])
    return parser


def parse_config(argv: Sequence[str] | None = None) -> Config:
    """Parse command-line arguments into benchmark configuration."""
    parser = create_parser()
    args = parser.parse_args(argv)
    working_directory = Path.cwd()
    args.model = working_directory / args.model
    args.server = working_directory / args.server
    args.output_dir = working_directory / args.output_dir
    if not args.model.is_file():
        parser.error(f"model not found: {args.model}")
    if not args.server.is_file() or not os.access(args.server, os.X_OK):
        parser.error(f"server not executable: {args.server}")
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    if args.context < 2048:
        parser.error("--context must be at least 2048")
    if args.long_tokens < 512:
        parser.error("--long-tokens must be at least 512")
    if args.runs < 3:
        parser.error("--runs must be at least 3")
    if args.long_tokens + 512 >= args.context:
        parser.error("--context must leave at least 512 tokens beyond --long-tokens")
    return Config(
        model=args.model,
        server=args.server,
        turbo=args.turbo,
        symmetric=args.symmetric == "on",
        host=args.host,
        port=args.port,
        context=args.context,
        long_tokens=args.long_tokens,
        runs=args.runs,
        warmups=args.warmups,
        output_dir=args.output_dir,
        server_args=tuple(args.server_arg),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the benchmark command."""
    from llama_benchmark.application import run_benchmark

    run_benchmark(parse_config(argv))
    return 0
