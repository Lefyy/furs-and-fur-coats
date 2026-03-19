from __future__ import annotations

from contextlib import contextmanager
from typing import Generator
from uuid import uuid4

from infrastructure.cache.redis_client import redis_client


class RedisLockError(RuntimeError):
    pass


@contextmanager
def redis_lock(key: str, *, ttl_seconds: int) -> Generator[str, None, None]:
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