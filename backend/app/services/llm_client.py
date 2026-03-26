import json
import re
from typing import Any, Dict, Optional

import httpx

from app.config import get_settings


class LLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        return self.settings.llm_enabled

    def _candidate_urls(self) -> list[str]:
        base = self.settings.llm_base_url.rstrip("/")
        if not base:
            return []
        if base.endswith("/v1"):
            return [f"{base}/chat/completions"]
        return [f"{base}/chat/completions", f"{base}/v1/chat/completions"]

    @staticmethod
    def _extract_json(content: str) -> Optional[Dict[str, Any]]:
        text = content.strip()
        try:
            return json.loads(text)
        except Exception:
            pass

        fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if fenced:
            try:
                return json.loads(fenced.group(1))
            except Exception:
                pass

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            maybe_json = text[start : end + 1]
            try:
                return json.loads(maybe_json)
            except Exception:
                return None
        return None

    async def chat_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None

        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.llm_model,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        urls = self._candidate_urls()
        if not urls:
            return None

        for url in urls:
            try:
                async with httpx.AsyncClient(timeout=40) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                parsed = self._extract_json(content)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                continue
        return None


llm_client = LLMClient()

