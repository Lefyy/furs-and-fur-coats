from __future__ import annotations

from contextlib import contextmanager
from typing import Generator
from uuid import uuid4

from infrastructure.cache.redis_client import redis_client


class RedisLockError(RuntimeError):
    pass


class RedisLockManager:
    def __init__(self, *, key_prefix: str = "") -> None:
        self.key_prefix = key_prefix

    def build_key(self, suffix: str) -> str:
        return f"{self.key_prefix}{suffix}"

    @contextmanager
    def acquire(self, suffix: str, *, ttl_seconds: int) -> Generator[str, None, None]:
        key = self.build_key(suffix)
        token = str(uuid4())
        is_locked = redis_client.set(key, token, nx=True, ex=ttl_seconds)
        if not is_locked:
            raise RedisLockError(f"Lock '{key}' is already acquired")

        try:
            yield token
        finally:
            current_token = redis_client.get(key)
            if current_token == token:
                redis_client.delete(key)


product_description_generation_lock = RedisLockManager(key_prefix="product-description-generation:")


@contextmanager
def redis_lock(key: str, *, ttl_seconds: int) -> Generator[str, None, None]:
    manager = RedisLockManager()
    with manager.acquire(key, ttl_seconds=ttl_seconds) as token:
        yield token