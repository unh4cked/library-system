"""Redis cache utilities for the library system backend."""
from __future__ import annotations

import json
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from .config import settings
from .logging_config import get_logger

logger = get_logger(__name__)

_BOOK_SEARCH_PREFIX = "books:search:"
_STUDENT_SEARCH_PREFIX = "students:search:"
_CATEGORY_LIST_KEY = "categories:list"

_redis_client: Redis | None = None


def get_redis_client() -> Redis | None:
    """
    Return a singleton Redis client instance when Redis is available.
    
    Returns:
        Redis client or None if Redis is unavailable or disabled.
    """
    global _redis_client
    
    if not settings.cache_enabled:
        logger.debug("Cache is disabled in settings")
        return None
    
    if _redis_client is not None:
        return _redis_client

    try:
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        _redis_client.ping()
        logger.info(f"Redis connected successfully: {settings.redis_url}")
    except RedisError as exc:
        logger.warning(f"Redis unavailable: {exc}")
        _redis_client = None
    
    return _redis_client


def _safe_json_loads(payload: str | None) -> Any | None:
    if payload is None:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        logger.error("Failed to decode cached payload: %s", exc)
        return None


def _safe_json_dumps(data: Any) -> str | None:
    try:
        return json.dumps(data)
    except (TypeError, ValueError) as exc:
        logger.error("Failed to serialize cache payload: %s", exc)
        return None


def build_book_search_key(term: str) -> str:
    """Build the cache key for a book search term."""
    normalized = term.strip().lower()
    return f"{_BOOK_SEARCH_PREFIX}{normalized}"


def get_cached_value(key: str) -> Any | None:
    """Retrieve a cached JSON-serializable value from Redis."""
    client = get_redis_client()
    if client is None:
        return None
    try:
        payload = client.get(key)
    except RedisError as exc:
        logger.error("Redis get failed for %s: %s", key, exc)
        return None
    return _safe_json_loads(payload)


def set_cached_value(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    """
    Store a JSON-serializable value in Redis with a TTL.
    
    Args:
        key: Cache key
        value: Value to cache (must be JSON-serializable)
        ttl_seconds: Time to live in seconds (uses settings default if None)
    """
    client = get_redis_client()
    if client is None:
        return
    
    payload = _safe_json_dumps(value)
    if payload is None:
        return
    
    ttl = ttl_seconds if ttl_seconds is not None else settings.cache_ttl
    
    try:
        client.setex(key, ttl, payload)
        logger.debug(f"Cached key: {key} (TTL: {ttl}s)")
    except RedisError as exc:
        logger.error(f"Redis set failed for {key}: {exc}")


def invalidate_book_search_cache() -> None:
    """Invalidate all cached book search results."""
    client = get_redis_client()
    if client is None:
        return
    try:
        for key in client.scan_iter(match=f"{_BOOK_SEARCH_PREFIX}*"):
            client.delete(key)
    except RedisError as exc:
        logger.error("Redis invalidate failed: %s", exc)
