from __future__ import annotations

from pathlib import Path

from agent import MultiMemoryAgent


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    agent = MultiMemoryAgent(data_dir=repo_root / "data", memory_budget=520, enable_llm=True)

    if not agent.llm_client:
        print("Khong tim thay cau hinh NVIDIA_API_KEY/NVIDIA_BASE_URL/AGENT_MODEL tu environment hoac .env")
        return

    messages: list[dict[str, str]] = []
    user_id = "user-live-check"

    # Turn 1 de luu memory profile
    _, _ = agent.chat_with_memory(user_id, messages, "Tôi tên là Đức và tôi dị ứng đậu nành")
    messages.append({"role": "user", "content": "Tôi tên là Đức và tôi dị ứng đậu nành"})

    # Turn 2 goi LLM that
    answer, state = agent.chat_with_memory(
        user_id,
        messages,
        "Bạn nhắc lại tên và dị ứng của tôi, trả lời ngắn gọn 1 câu.",
    )

    print("=== LLM RESPONSE ===")
    print(answer)
    print("\n=== MEMORY CONTEXT PREVIEW ===")
    print(state["assembled_prompt"])


if __name__ == "__main__":
    main()
