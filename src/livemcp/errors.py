"""Shared package-side error helpers for LiveMCP transport responses."""

from __future__ import annotations

from typing import Any, Optional


class RemoteCommandError(RuntimeError):
    """Structured error returned by the Ableton-side remote script."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.details = details or {}


def error_from_payload(error_payload: Any) -> RuntimeError:
    """Convert a remote-script error payload into a Python exception."""
    if isinstance(error_payload, dict):
        message = str(error_payload.get("message") or "Unknown error")
        code = error_payload.get("code")
        details = error_payload.get("details")
        return RemoteCommandError(message, code=code, details=details)

    if error_payload is None:
        return RuntimeError("Unknown error")

    return RuntimeError(str(error_payload))
