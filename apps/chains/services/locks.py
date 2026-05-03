from __future__ import annotations

import secrets
from dataclasses import dataclass
from django.core.cache import cache


@dataclass(frozen=True)
class LockResult:
    acquired: bool
    token: str


def acquire_lock(key: str, ttl_seconds: int = 30) -> LockResult:
    token = secrets.token_hex(16)
    acquired = cache.add(f"lock:{key}", token, ttl_seconds)
    return LockResult(acquired=acquired, token=token)


def release_lock(key: str, token: str) -> bool:
    current = cache.get(f"lock:{key}")
    if current == token:
        cache.delete(f"lock:{key}")
        return True
    return False