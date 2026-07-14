import argparse
from collections.abc import Sequence


def create_parser() -> argparse.ArgumentParser:
    """Create the public command-line parser."""
    parser = argparse.ArgumentParser(
        prog="llama-benchmark",
        description="Run repeatable benchmarks against a local llama-server.",
    )
    parser.add_argument("--turbo", choices=("3", "4"))
    parser.add_argument("--symmetric", choices=("on", "off"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the benchmark command."""
    create_parser().parse_args(argv)
    return 0
