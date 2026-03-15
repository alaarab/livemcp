"""Structured error helpers for the Ableton-side remote script."""


class LiveMCPError(RuntimeError):
    """Structured error with stable code/message/details fields."""

    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code = code
        self.details = details or {}

    def to_payload(self):
        payload = {
            "code": self.code,
            "message": str(self),
        }
        if self.details:
            payload["details"] = self.details
        return payload
