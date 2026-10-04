"""Translate expected bridge failures at the MCP protocol boundary."""

from functools import wraps
from typing import Callable, ParamSpec, TypeVar, get_type_hints

from .errors import RemoteCommandError

P = ParamSpec("P")
R = TypeVar("R")


def mcp_handler(fn: Callable[P, R], error_type: type[Exception]) -> Callable[P, R]:
    """Preserve tool/resource schemas and expose actionable bridge errors in MCP 2."""

    @wraps(fn)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return fn(*args, **kwargs)
        except (RemoteCommandError, ConnectionError, ValueError) as exc:
            raise error_type(str(exc)) from exc

    # Resources use postponed annotations from their defining module. Resolve
    # them there before the SDK inspects this wrapper in a different module.
    wrapped.__annotations__ = get_type_hints(fn)
    return wrapped
