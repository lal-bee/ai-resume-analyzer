import json
import time
import uuid
from typing import Any, Dict, Optional

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None  # type: ignore[assignment]

from app.config import get_settings


class CacheService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._redis_client = None
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._resume_store: Dict[str, Dict[str, Any]] = {}
        self._filehash_to_resume_id: Dict[str, str] = {}

    async def _get_redis(self):
        if not self.settings.redis_enabled or redis is None:
            return None
        if self._redis_client is None:
            self._redis_client = redis.from_url(self.settings.redis_url, decode_responses=True)
        return self._redis_client

    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        redis_client = await self._get_redis()
        if redis_client:
            data = await redis_client.get(key)
            if data:
                return json.loads(data)
            return None

        item = self._memory_cache.get(key)
        if not item:
            return None
        if item["expires_at"] < time.time():
            self._memory_cache.pop(key, None)
            return None
        return item["value"]

    async def set_json(self, key: str, value: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds or self.settings.cache_ttl_seconds
        redis_client = await self._get_redis()
        if redis_client:
            await redis_client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
            return
        self._memory_cache[key] = {"value": value, "expires_at": time.time() + ttl}

    def upsert_resume(self, file_hash: str, resume_data: Dict[str, Any]) -> str:
        resume_id = self._filehash_to_resume_id.get(file_hash)
        if not resume_id:
            resume_id = str(uuid.uuid4())
            self._filehash_to_resume_id[file_hash] = resume_id
        payload = dict(resume_data)
        payload["resume_id"] = resume_id
        self._resume_store[resume_id] = payload
        return resume_id

    def get_resume(self, resume_id: str) -> Optional[Dict[str, Any]]:
        return self._resume_store.get(resume_id)


cache_service = CacheService()

