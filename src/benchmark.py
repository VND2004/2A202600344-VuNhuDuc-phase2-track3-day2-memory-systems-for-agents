from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil

from agent import MultiMemoryAgent


@dataclass
class ConversationScenario:
    scenario: str
    turns: list[str]
    probe: str
    expected_with_memory: str
    expected_without_memory_hint: str


def reset_runtime_data(repo_root: Path) -> None:
    profile_store = repo_root / "data" / "profile_store.json"
    episodes_store = repo_root / "data" / "episodes.json"
    profile_store.write_text("{}", encoding="utf-8")
    episodes_store.write_text("[]", encoding="utf-8")


def run_scenario(
    agent: MultiMemoryAgent,
    scenario: ConversationScenario,
    user_id: str,
) -> dict[str, str]:
    messages: list[dict[str, str]] = []

    no_memory_last = ""
    with_memory_last = ""
    state_snapshot = ""

    for turn in scenario.turns:
        no_memory_last = agent.chat_without_memory(turn)
        with_memory_last, state = agent.chat_with_memory(user_id, messages, turn)
        messages.append({"role": "user", "content": turn})
        messages.append({"role": "assistant", "content": with_memory_last})
        state_snapshot = state["assembled_prompt"]

    no_memory_probe = agent.chat_without_memory(scenario.probe)
    with_memory_probe, state = agent.chat_with_memory(user_id, messages, scenario.probe)

    return {
        "scenario": scenario.scenario,
        "no_memory": no_memory_probe,
        "with_memory": with_memory_probe,
        "expected_with_memory": scenario.expected_with_memory,
        "expected_without_memory_hint": scenario.expected_without_memory_hint,
        "pass": "Pass" if scenario.expected_with_memory.lower() in with_memory_probe.lower() else "Fail",
        "turn_count": str(len(scenario.turns) + 1),
        "prompt_chars": str(len(state["assembled_prompt"])),
        "prompt_words": str(len(state["assembled_prompt"].split())),
    }


def benchmark_scenarios(data_path: Path) -> list[ConversationScenario]:
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    return [ConversationScenario(**item) for item in raw]


def to_markdown(rows: list[dict[str, str]]) -> str:
    header = [
        "# BENCHMARK - Multi-Memory Agent",
        "",
        "So sánh no-memory vs with-memory trên 10 multi-turn conversations.",
        "Token budget ước lượng bằng số ký tự và số từ trong prompt đã assemble.",
        "",
        "| # | Scenario | Turns | No-memory result | With-memory result | Prompt chars | Prompt words | Pass? |",
        "|---|----------|------:|------------------|--------------------|-------------:|-------------:|-------|",
    ]

    lines = []
    for idx, row in enumerate(rows, start=1):
        lines.append(
            "| {idx} | {scenario} | {turns} | {no_memory} | {with_memory} | {prompt_chars} | {prompt_words} | {pass_result} |".format(
                idx=idx,
                scenario=row["scenario"],
                turns=row["turn_count"],
                no_memory=row["no_memory"].replace("|", "/"),
                with_memory=row["with_memory"].replace("|", "/"),
                prompt_chars=row["prompt_chars"],
                prompt_words=row["prompt_words"],
                pass_result=row["pass"],
            )
        )

    detail_header = [
        "",
        "## Coverage",
        "- Profile recall: scenarios 1, 3, 9, 10",
        "- Conflict update: scenario 2",
        "- Episodic recall: scenarios 4, 8",
        "- Semantic retrieval: scenarios 5, 6, 8",
        "- Trim/token budget: scenario 7 (và cột prompt chars/words toàn bộ bảng)",
        "",
        "## Notes",
        "- No-memory mode có chủ đích không giữ profile/episodic/semantic context.",
        "- With-memory mode inject 4 memory sections vào prompt assembled.",
    ]

    return "\n".join(header + lines + detail_header) + "\n"


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    scenarios_path = repo_root / "data" / "benchmark_conversations.json"
    reset_runtime_data(repo_root)

    agent = MultiMemoryAgent(data_dir=repo_root / "data", memory_budget=520, enable_llm=False)
    rows = []
    for idx, scenario in enumerate(benchmark_scenarios(scenarios_path), start=1):
        rows.append(run_scenario(agent, scenario, user_id=f"user-benchmark-{idx}"))

    benchmark_path = repo_root / "BENCHMARK.md"
    benchmark_path.write_text(to_markdown(rows), encoding="utf-8")

    print(f"Benchmark written to: {benchmark_path}")


if __name__ == "__main__":
    main()
