from __future__ import annotations

import os
from contextlib import contextmanager
from functools import lru_cache
from typing import Any

try:
    from langfuse import get_client, observe, propagate_attributes

    LANGFUSE_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - chỉ dùng khi chưa cài requirements
    LANGFUSE_SDK_AVAILABLE = False

    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func

        return decorator

    class _DummyClient:
        def update_current_span(self, **kwargs: Any) -> None:
            return None

        def update_current_generation(self, **kwargs: Any) -> None:
            return None

    def get_client():
        return _DummyClient()

    @contextmanager
    def propagate_attributes(**kwargs: Any):
        yield


def get_langfuse_client():
    return get_client()


def tracing_enabled() -> bool:
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
    if not LANGFUSE_SDK_AVAILABLE or not public_key or not secret_key:
        return False
    return _credentials_are_valid(public_key, secret_key, base_url)


@lru_cache(maxsize=4)
def _credentials_are_valid(public_key: str, secret_key: str, base_url: str) -> bool:
    """Verify credentials once per process/config so health never reports a false positive."""
    if not public_key or not secret_key or not base_url:
        return False
    try:
        return bool(get_langfuse_client().auth_check())
    except Exception:
        return False
