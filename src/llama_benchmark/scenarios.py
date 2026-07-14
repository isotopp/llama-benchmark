from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class Scenario:
    """One reproducible benchmark scenario."""

    name: str
    filename: str
    prompt: str
    n_predict: int


class CompletionRequest(TypedDict):
    """JSON request accepted by llama-server's completion endpoint."""

    prompt: str
    n_predict: int
    temperature: int
    top_k: int
    top_p: int
    min_p: int
    seed: int
    ignore_eos: bool
    cache_prompt: bool
    stream: bool


SHORT_PROMPT = """Give a precise explanation of why the sky appears blue during the day. Use exactly four concise paragraphs. Distinguish Rayleigh scattering from absorption and mention why sunsets appear red.
"""

NUMERIC_PROMPT = """A company operates three data centres.

Data centre A consumes 4.8 MW continuously and has a power usage effectiveness of 1.24.
Data centre B consumes 3.1 MW continuously and has a power usage effectiveness of 1.38.
Data centre C consumes 2.6 MW continuously and has a power usage effectiveness of 1.18.

Electricity costs EUR 0.142 per kWh. The company plans to reduce each site's total facility power by 7 percent without changing IT workload.

Calculate the current annual electricity use and cost for each site and for the whole fleet. Then calculate the annual savings after the reduction. Show formulas, intermediate values, units, and a compact final table. Use 365.25 days per year.
"""

CODE_PROMPT = """Write a complete Python 3.12 module that reads newline-delimited JSON records from a pathlib.Path, validates each record, and writes valid records to one output file and invalid records to another.

Requirements:
- Use only the Python standard library.
- Use dataclasses with slots.
- Stream the input instead of loading it into memory.
- Preserve the original line number.
- Treat malformed JSON, non-object JSON, missing "id", and non-string "id" as invalid.
- Write UTF-8 atomically by using temporary files in the destination directory and os.replace.
- Include type annotations, docstrings, explicit error handling, and unittest tests.
- Do not use shell commands or unsafe deserialization.
"""

LONG_CONTEXT_INSTRUCTION = """Read the numbered operational records below. Return only a JSON object with keys "first_id", "last_id", "count", "checksum_rule", and "anomalies". The count must equal the number of records. The first and last IDs must come from the text. The checksum rule is stated repeatedly. List records whose status is ALERT.
"""


def build_long_context_prompt(long_tokens: int) -> str:
    """Build the deterministic ordered ledger for the long-context scenario."""
    record_count = max(8, long_tokens // 59)
    records = []
    for index in range(1, record_count + 1):
        status = "ALERT" if index % 997 == 0 or index == record_count - 3 else "OK"
        reading = (index * 37) % 10000
        records.append(
            f"Record ID R{index:06d}. Region EU-WEST. Status {status}. "
            f"Reading {reading}. Checksum rule: multiply the numeric ID by 17 "
            "and take the remainder modulo 1009. This record is part of one "
            "continuous ordered ledger.\n"
        )
    return f"{LONG_CONTEXT_INSTRUCTION}\n{''.join(records)}"


def completion_request(scenario: Scenario) -> CompletionRequest:
    """Create one independent deterministic request for a scenario."""
    nonce = f"benchmark-{uuid4()}"
    return {
        "prompt": (
            f"Benchmark nonce: {nonce}\n"
            "Ignore the nonce. Follow the task exactly.\n\n"
            f"{scenario.prompt}"
        ),
        "n_predict": scenario.n_predict,
        "temperature": 0,
        "top_k": 1,
        "top_p": 1,
        "min_p": 0,
        "seed": 42,
        "ignore_eos": True,
        "cache_prompt": False,
        "stream": False,
    }


def write_prompts(configured: tuple[Scenario, ...], directory: Path) -> None:
    """Record scenario prompts as UTF-8 before benchmark execution."""
    directory.mkdir(parents=True, exist_ok=True)
    for scenario in configured:
        (directory / scenario.filename).write_text(scenario.prompt, encoding="utf-8")


def scenarios(*, long_tokens: int) -> tuple[Scenario, ...]:
    """Return benchmark scenarios in execution order."""
    return (
        Scenario(
            name="short-generation",
            filename="short.txt",
            prompt=SHORT_PROMPT,
            n_predict=256,
        ),
        Scenario(
            name="numeric-analysis",
            filename="analysis.txt",
            prompt=NUMERIC_PROMPT,
            n_predict=384,
        ),
        Scenario(
            name="code-generation",
            filename="code.txt",
            prompt=CODE_PROMPT,
            n_predict=512,
        ),
        Scenario(
            name="long-context",
            filename="long-context.txt",
            prompt=build_long_context_prompt(long_tokens),
            n_predict=64,
        ),
    )
