from __future__ import annotations

from pathlib import Path
import re
import unicodedata
from typing import TypedDict

from llm_client import NvidiaLLMClient
from memory_backends import (
    EpisodicMemory,
    LongTermProfileMemory,
    SemanticMemory,
    ShortTermMemory,
)


class MemoryState(TypedDict):
    messages: list[dict[str, str]]
    user_profile: dict
    episodes: list[dict]
    semantic_hits: list[str]
    memory_budget: int
    user_input: str
    assembled_prompt: str


class MultiMemoryAgent:
    def __init__(self, data_dir: Path, memory_budget: int = 700, enable_llm: bool = True) -> None:
        self.short_term = ShortTermMemory(window_size=10)
        self.profile = LongTermProfileMemory(data_dir / "profile_store.json")
        self.episodic = EpisodicMemory(data_dir / "episodes.json")
        self.semantic = SemanticMemory(data_dir / "semantic_corpus.json")
        self.memory_budget = memory_budget
        self.enable_llm = enable_llm
        self.llm_client = NvidiaLLMClient.from_env(data_dir.parent) if enable_llm else None

    def _extract_profile_updates(self, text: str) -> dict[str, str]:
        lowered = text.lower()
        updates: dict[str, str] = {}

        name_match = re.search(
            r"(?:toi|tôi)\s+(?:ten|tên)\s+(?:la|là)\s+(.+?)(?=\s+(?:va|và)\s+(?:toi|tôi)\s+(?:di ung|dị ứng)|[\.,!?]|$)",
            lowered,
        )
        if name_match:
            updates["name"] = name_match.group(1).strip().title()

        role_match = re.search(r"(?:toi|tôi)\s+(?:lam|làm)\s+([^\.,!?]+)", lowered)
        if role_match:
            updates["occupation"] = role_match.group(1).strip()

        allergy_correction = re.search(
            r"(?:toi|tôi)\s+(?:di ung|dị ứng)\s+([^\.,!?]+)\s+(?:chu|chứ)\s+(?:khong phai|không phải)\s+([^\.,!?]+)",
            lowered,
        )
        if allergy_correction:
            updates["allergy"] = allergy_correction.group(1).strip()
            return updates

        allergy_match = re.search(r"(?:toi|tôi)\s+(?:di ung|dị ứng)\s+([^\.,!?]+)", lowered)
        if allergy_match:
            updates["allergy"] = allergy_match.group(1).strip()

        language_match = re.search(r"(?:toi|tôi)\s+(?:thich|thích)\s+([^\.,!?]+)", lowered)
        if language_match:
            updates["preference"] = language_match.group(1).strip()

        return updates

    def _should_save_episode(self, text: str) -> bool:
        lowered = self._normalize_vn(text)
        if "?" in lowered or lowered.strip().startswith("lan truoc"):
            return False
        markers = ["xong", "hoan thanh", "da sua", "da dat", "done", "ket qua"]
        return any(marker in lowered for marker in markers)

    def _normalize_vn(self, text: str) -> str:
        normalized = unicodedata.normalize("NFD", text)
        no_diacritic = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return no_diacritic.lower().replace("đ", "d").replace("Đ", "D")

    def _maybe_update_memory(self, user_id: str, user_input: str) -> None:
        updates = self._extract_profile_updates(user_input)
        if updates:
            self.profile.bulk_update(user_id, updates)

        if self._should_save_episode(user_input):
            self.episodic.add_episode(
                user_id=user_id,
                summary=f"User update: {user_input}",
                outcome="Task marked as completed by user",
                tags=["outcome", "user-note"],
            )

    def _trim_lines(self, lines: list[str], budget: int) -> list[str]:
        consumed = 0
        selected: list[str] = []
        for line in lines:
            line_cost = len(line)
            if consumed + line_cost > budget:
                break
            selected.append(line)
            consumed += line_cost
        return selected

    def retrieve_memory(self, state: MemoryState, user_id: str) -> MemoryState:
        profile = self.profile.get_profile(user_id)
        episodes = self.episodic.get_recent(user_id, limit=3)
        semantic_hits = self.semantic.retrieve(state["user_input"], top_k=3)

        semantic_lines = [f"- {hit['id']}: {hit['text']}" for hit in semantic_hits]
        episode_lines = [
            f"- {ep.get('summary', '')} | outcome={ep.get('outcome', '')}" for ep in episodes
        ]
        profile_lines = [
            f"- {key}: {value.get('value')} (updated_at={value.get('updated_at')})"
            for key, value in profile.items()
        ]
        conv_lines = [
            f"- {msg['role']}: {msg['content']}"
            for msg in self.short_term.get_recent(user_id)
        ]

        # Router gom du lieu tu 4 backends roi trim theo memory budget.
        lines = (
            ["[PROFILE]"]
            + profile_lines
            + ["[EPISODIC]"]
            + episode_lines
            + ["[SEMANTIC]"]
            + semantic_lines
            + ["[RECENT_CONVERSATION]"]
            + conv_lines
        )
        trimmed = self._trim_lines(lines, state["memory_budget"])

        state["user_profile"] = profile
        state["episodes"] = episodes
        state["semantic_hits"] = [hit["text"] for hit in semantic_hits]
        state["assembled_prompt"] = "\n".join(trimmed)
        return state

    def _answer_with_memory(self, state: MemoryState) -> str:
        user_input = self._normalize_vn(state["user_input"])
        profile = state["user_profile"]

        if "tong hop profile" in user_input or "profile chinh" in user_input:
            name = profile.get("name", {}).get("value", "chưa rõ")
            allergy = profile.get("allergy", {}).get("value", "chưa rõ")
            occupation = profile.get("occupation", {}).get("value", "chưa rõ")
            preference = profile.get("preference", {}).get("value", "chưa rõ")
            return (
                "Profile hiện tại: "
                f"name={name}, allergy={allergy}, occupation={occupation}, preference={preference}."
            )

        if "toi ten gi" in user_input or "ten toi" in user_input:
            name = profile.get("name", {}).get("value")
            return f"Bạn tên là {name}." if name else "Mình chưa có thông tin tên của bạn."

        if "nghe nghiep" in user_input or "toi lam gi" in user_input:
            occupation = profile.get("occupation", {}).get("value")
            return (
                f"Bạn làm {occupation}."
                if occupation
                else "Mình chưa có thông tin nghề nghiệp của bạn."
            )

        if "preference" in user_input or "thich gi" in user_input:
            preference = profile.get("preference", {}).get("value")
            if preference:
                return f"Preference của bạn là {preference}."

            # Hỗ trợ fallback cho câu hỏi kết hợp tên + sở thích.
            name = profile.get("name", {}).get("value")
            if name:
                return f"Bạn tên là {name}."

        if "di ung" in user_input:
            allergy = profile.get("allergy", {}).get("value")
            if allergy:
                return f"Thông tin hiện tại: bạn dị ứng {allergy}."

        if "lan truoc" in user_input or "truoc day" in user_input:
            if "faq" in user_input and state["semantic_hits"]:
                latest = state["episodes"][-1] if state["episodes"] else {}
                return (
                    "Lần trước: "
                    f"{latest.get('summary', 'chưa có')} / FAQ: {state['semantic_hits'][0]}"
                )

            if state["episodes"]:
                latest = state["episodes"][-1]
                return (
                    "Lần trước bạn đã ghi nhận: "
                    f"{latest.get('summary')} (kết quả: {latest.get('outcome')})."
                )

        if any(keyword in user_input for keyword in ["docker", "faq", "service"]):
            if state["semantic_hits"]:
                return f"Gợi ý từ semantic memory: {state['semantic_hits'][0]}"

        if state["semantic_hits"]:
            return f"Thông tin semantic liên quan: {state['semantic_hits'][0]}"

        return (
            "Mình đã tổng hợp memory liên quan. "
            "Nếu bạn muốn, mình có thể tóm tắt profile và hành động tiếp theo."
        )

    def _answer_without_memory(self, user_input: str) -> str:
        lowered = self._normalize_vn(user_input)
        if "toi ten gi" in lowered or "di ung" in lowered:
            return "Mình không có bộ nhớ dài hạn nên không chắc thông tin trước đó."
        if any(keyword in lowered for keyword in ["docker", "faq", "service"]):
            return "Có thể dùng localhost để gọi service khác trong Docker Compose."
        return "Mình trả lời theo lượt hiện tại, không giữ được bối cảnh cũ."

    def _answer_with_real_llm(self, state: MemoryState, fallback_answer: str) -> str:
        if not self.llm_client:
            return fallback_answer

        system_prompt = (
            "Bạn là trợ lý AI tiếng Việt. Dùng đúng ngữ cảnh memory đã inject bên dưới để trả lời ngắn gọn, "
            "chính xác và không bịa thông tin. Nếu thiếu dữ liệu thì nói rõ thiếu dữ liệu.\n\n"
            f"MEMORY_CONTEXT:\n{state['assembled_prompt']}"
        )
        user_prompt = (
            f"Câu hỏi hiện tại của người dùng: {state['user_input']}\n"
            f"Gợi ý fallback nội bộ: {fallback_answer}"
        )

        try:
            generated = self.llm_client.generate(system_prompt=system_prompt, user_prompt=user_prompt)
            return generated or fallback_answer
        except Exception:
            return fallback_answer

    def chat_with_memory(
        self,
        user_id: str,
        messages: list[dict[str, str]],
        user_input: str,
    ) -> tuple[str, MemoryState]:
        self.short_term.add_message(user_id, "user", user_input)
        self._maybe_update_memory(user_id, user_input)

        state: MemoryState = {
            "messages": messages + [{"role": "user", "content": user_input}],
            "user_profile": {},
            "episodes": [],
            "semantic_hits": [],
            "memory_budget": self.memory_budget,
            "user_input": user_input,
            "assembled_prompt": "",
        }
        state = self.retrieve_memory(state, user_id=user_id)

        fallback_answer = self._answer_with_memory(state)
        answer = self._answer_with_real_llm(state, fallback_answer)
        self.short_term.add_message(user_id, "assistant", answer)
        return answer, state

    def chat_without_memory(self, user_input: str) -> str:
        return self._answer_without_memory(user_input)
