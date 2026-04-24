from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib import error, request


def _load_dotenv(dotenv_path: Path) -> dict[str, str]:
    if not dotenv_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value
    return values


class NvidiaLLMClient:
    def __init__(self, api_key: str, base_url: str, model: str, timeout: int = 60) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") + "/"
        self.model = model
        self.timeout = timeout

    @classmethod
    def from_env(cls, repo_root: Path | None = None) -> NvidiaLLMClient | None:
        env_values: dict[str, str] = {}
        if repo_root is not None:
            env_values = _load_dotenv(repo_root / ".env")

        api_key = os.getenv("NVIDIA_API_KEY") or env_values.get("NVIDIA_API_KEY")
        base_url = os.getenv("NVIDIA_BASE_URL") or env_values.get("NVIDIA_BASE_URL")
        model = os.getenv("AGENT_MODEL") or env_values.get("AGENT_MODEL")

        if not api_key or not base_url or not model:
            return None

        return cls(api_key=api_key, base_url=base_url, model=model)

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 512) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }

        req = request.Request(
            url=self.base_url + "chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"NVIDIA API HTTP error {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"NVIDIA API connection error: {exc.reason}") from exc

        parsed: dict[str, Any] = json.loads(body)
        choices = parsed.get("choices") or []
        if not choices:
            raise RuntimeError("NVIDIA API returned no choices.")

        message = choices[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, list):
            chunks = [piece.get("text", "") for piece in content if isinstance(piece, dict)]
            return "".join(chunks).strip()
        return str(content).strip()
