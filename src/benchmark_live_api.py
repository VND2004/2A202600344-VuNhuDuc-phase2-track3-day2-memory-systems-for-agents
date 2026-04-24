from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import unicodedata

from agent import MultiMemoryAgent


@dataclass
class ConversationScenario:
    scenario: str
    turns: list[str]
    probe: str
    expected_with_memory: str
    expected_without_memory_hint: str


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    no_diacritic = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return no_diacritic.lower().replace("đ", "d").replace("Đ", "D")


def reset_runtime_data(repo_root: Path) -> None:
    profile_store = repo_root / "data" / "profile_store.json"
    episodes_store = repo_root / "data" / "episodes.json"
    profile_store.write_text("{}", encoding="utf-8")
    episodes_store.write_text("[]", encoding="utf-8")


def load_scenarios(data_path: Path) -> list[ConversationScenario]:
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    return [ConversationScenario(**item) for item in raw]


def run_scenario_live(
    with_memory_agent: MultiMemoryAgent,
    no_memory_agent: MultiMemoryAgent,
    scenario: ConversationScenario,
    user_id: str,
) -> dict[str, str]:
    messages: list[dict[str, str]] = []

    for turn in scenario.turns:
        no_memory_agent.chat_without_memory(turn)
        with_answer, _ = with_memory_agent.chat_with_memory(user_id, messages, turn)
        messages.append({"role": "user", "content": turn})
        messages.append({"role": "assistant", "content": with_answer})

    no_memory_probe = no_memory_agent.chat_without_memory(scenario.probe)
    with_memory_probe, state = with_memory_agent.chat_with_memory(user_id, messages, scenario.probe)

    expected_norm = normalize_text(scenario.expected_with_memory)
    with_norm = normalize_text(with_memory_probe)

    return {
        "scenario": scenario.scenario,
        "turn_count": str(len(scenario.turns) + 1),
        "no_memory": no_memory_probe,
        "with_memory": with_memory_probe,
        "expected": scenario.expected_with_memory,
        "pass": "Pass" if expected_norm in with_norm else "Fail",
        "prompt_chars": str(len(state["assembled_prompt"])),
        "prompt_words": str(len(state["assembled_prompt"].split())),
    }


def to_markdown(rows: list[dict[str, str]]) -> str:
    header = [
        "# BENCHMARK LIVE API - Multi-Memory Agent",
        "",
        "Chạy benchmark gọi LLM API thật (NVIDIA) trên 10 multi-turn conversations.",
        "",
        "| # | Scenario | Turns | Expected key | No-memory result | With-memory result | Prompt chars | Prompt words | Pass? |",
        "|---|----------|------:|--------------|------------------|--------------------|-------------:|-------------:|-------|",
    ]

    lines = []
    for idx, row in enumerate(rows, start=1):
        lines.append(
            "| {idx} | {scenario} | {turn_count} | {expected} | {no_memory} | {with_memory} | {prompt_chars} | {prompt_words} | {pass_result} |".format(
                idx=idx,
                scenario=row["scenario"],
                turn_count=row["turn_count"],
                expected=row["expected"].replace("|", "/"),
                no_memory=row["no_memory"].replace("|", "/"),
                with_memory=row["with_memory"].replace("|", "/"),
                prompt_chars=row["prompt_chars"],
                prompt_words=row["prompt_words"],
                pass_result=row["pass"],
            )
        )

    summary = [
        "",
        "## Notes",
        "- Kết quả with-memory phụ thuộc vào phản hồi LLM thực tế tại thời điểm chạy.",
        "- Tiêu chí pass dùng so khớp không phân biệt dấu và hoa/thường với expected key.",
    ]

    return "\n".join(header + lines + summary) + "\n"


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    scenarios_path = repo_root / "data" / "benchmark_conversations.json"
    reset_runtime_data(repo_root)

    with_memory_agent = MultiMemoryAgent(data_dir=repo_root / "data", memory_budget=520, enable_llm=True)
    no_memory_agent = MultiMemoryAgent(data_dir=repo_root / "data", memory_budget=520, enable_llm=False)

    if not with_memory_agent.llm_client:
        print("Không tìm thấy NVIDIA_API_KEY/NVIDIA_BASE_URL/AGENT_MODEL từ environment hoặc .env")
        return

    rows = []
    for idx, scenario in enumerate(load_scenarios(scenarios_path), start=1):
        rows.append(
            run_scenario_live(
                with_memory_agent=with_memory_agent,
                no_memory_agent=no_memory_agent,
                scenario=scenario,
                user_id=f"user-live-benchmark-{idx}",
            )
        )

    output_path = repo_root / "BENCHMARK_LIVE_API.md"
    output_path.write_text(to_markdown(rows), encoding="utf-8")
    print(f"Live API benchmark written to: {output_path}")


if __name__ == "__main__":
    main()
