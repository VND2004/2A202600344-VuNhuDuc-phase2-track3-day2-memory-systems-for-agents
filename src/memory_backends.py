from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return default
    return json.loads(raw)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@dataclass
class ShortTermMemory:
    window_size: int = 8

    def __post_init__(self) -> None:
        self._messages_by_user: dict[str, list[dict[str, str]]] = {}

    def add_message(self, user_id: str, role: str, content: str) -> None:
        history = self._messages_by_user.setdefault(user_id, [])
        history.append({"role": role, "content": content})
        if len(history) > self.window_size:
            self._messages_by_user[user_id] = history[-self.window_size :]

    def get_recent(self, user_id: str) -> list[dict[str, str]]:
        return list(self._messages_by_user.get(user_id, []))


@dataclass
class LongTermProfileMemory:
    store_path: Path

    def get_profile(self, user_id: str) -> dict[str, Any]:
        db = _read_json(self.store_path, {})
        return dict(db.get(user_id, {}))

    def update_fact(self, user_id: str, key: str, value: Any) -> None:
        db = _read_json(self.store_path, {})
        profile = dict(db.get(user_id, {}))
        profile[key] = {
            "value": value,
            "updated_at": utc_now_iso(),
        }
        db[user_id] = profile
        _write_json(self.store_path, db)

    def bulk_update(self, user_id: str, updates: dict[str, Any]) -> None:
        for key, value in updates.items():
            self.update_fact(user_id, key, value)


@dataclass
class EpisodicMemory:
    store_path: Path

    def add_episode(
        self,
        user_id: str,
        summary: str,
        outcome: str,
        tags: list[str] | None = None,
    ) -> None:
        payload = _read_json(self.store_path, [])
        payload.append(
            {
                "user_id": user_id,
                "summary": summary,
                "outcome": outcome,
                "tags": tags or [],
                "created_at": utc_now_iso(),
            }
        )
        _write_json(self.store_path, payload)

    def get_recent(self, user_id: str, limit: int = 3) -> list[dict[str, Any]]:
        payload = _read_json(self.store_path, [])
        episodes = [row for row in payload if row.get("user_id") == user_id]
        return episodes[-limit:]


@dataclass
class SemanticMemory:
    corpus_path: Path

    def __post_init__(self) -> None:
        self._corpus = _read_json(self.corpus_path, [])

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        terms = [token.lower() for token in query.split() if token.strip()]
        scored: list[tuple[int, dict[str, Any]]] = []

        for item in self._corpus:
            text = str(item.get("text", "")).lower()
            tags = " ".join(item.get("tags", [])).lower()
            haystack = f"{text} {tags}"
            score = sum(1 for term in terms if term in haystack)
            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [row for _, row in scored[:top_k]]
