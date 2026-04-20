from __future__ import annotations

import os
from typing import Any

try:
    from langfuse import get_client, observe

    _langfuse_client = get_client()
    langfuse_context = _langfuse_client

except Exception:  # pragma: no cover
    _langfuse_client = None  # type: ignore[assignment]

    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator

    class _DummyContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_generation(self, **kwargs: Any) -> None:
            return None

        def flush(self) -> None:
            return None

    langfuse_context = _DummyContext()  # type: ignore[assignment]


def flush_traces() -> None:
    if _langfuse_client is not None:
        _langfuse_client.flush()


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
