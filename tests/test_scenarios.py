from pathlib import Path

from llama_benchmark.scenarios import completion_request, scenarios, write_prompts


def test_scenarios_include_the_short_generation_task() -> None:
    short = scenarios(long_tokens=8192)[0]

    assert short.name == "short-generation"
    assert short.filename == "short.txt"
    assert short.n_predict == 256
    assert "why the sky appears blue" in short.prompt
    assert "exactly four concise paragraphs" in short.prompt
    assert short.prompt.endswith("\n")


def test_scenarios_include_the_numeric_analysis_task() -> None:
    numeric = scenarios(long_tokens=8192)[1]

    assert numeric.name == "numeric-analysis"
    assert numeric.filename == "analysis.txt"
    assert numeric.n_predict == 384
    assert "Data centre A consumes 4.8 MW" in numeric.prompt
    assert "Use 365.25 days per year" in numeric.prompt


def test_scenarios_include_the_code_generation_task() -> None:
    code = scenarios(long_tokens=8192)[2]

    assert code.name == "code-generation"
    assert code.filename == "code.txt"
    assert code.n_predict == 512
    assert "Python 3.12 module" in code.prompt
    assert "Use only the Python standard library" in code.prompt
    assert "unittest tests" in code.prompt


def test_long_context_scenario_builds_the_ordered_ledger() -> None:
    long_context = scenarios(long_tokens=512)[3]

    assert long_context.name == "long-context"
    assert long_context.filename == "long-context.txt"
    assert long_context.n_predict == 64
    assert long_context.prompt.count("Record ID ") == 8
    assert "Record ID R000001." in long_context.prompt
    assert "Record ID R000008." in long_context.prompt
    assert "Record ID R000005. Region EU-WEST. Status ALERT." in long_context.prompt
    assert "multiply the numeric ID by 17" in long_context.prompt


def test_completion_requests_are_independent_and_deterministic() -> None:
    short = scenarios(long_tokens=8192)[0]

    first = completion_request(short)
    second = completion_request(short)

    assert first["prompt"] != second["prompt"]
    assert first["prompt"].endswith(short.prompt)
    assert first | {"prompt": second["prompt"]} == second
    assert first["n_predict"] == 256
    assert first["temperature"] == 0
    assert first["top_k"] == 1
    assert first["top_p"] == 1
    assert first["min_p"] == 0
    assert first["seed"] == 42
    assert first["ignore_eos"] is True
    assert first["cache_prompt"] is False
    assert first["stream"] is False


def test_write_prompts_records_all_scenarios_as_utf8(tmp_path: Path) -> None:
    configured = scenarios(long_tokens=512)

    write_prompts(configured, tmp_path)

    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "analysis.txt",
        "code.txt",
        "long-context.txt",
        "short.txt",
    ]
    for scenario in configured:
        assert (tmp_path / scenario.filename).read_text(
            encoding="utf-8"
        ) == scenario.prompt
