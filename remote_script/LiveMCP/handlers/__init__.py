"""LiveMCP remote script command handlers."""

from .session import READ_HANDLERS as SESSION_READ, WRITE_HANDLERS as SESSION_WRITE
from .tracks import READ_HANDLERS as TRACKS_READ, WRITE_HANDLERS as TRACKS_WRITE
from .clips import READ_HANDLERS as CLIPS_READ, WRITE_HANDLERS as CLIPS_WRITE
from .devices import READ_HANDLERS as DEVICES_READ, WRITE_HANDLERS as DEVICES_WRITE
from .mixer import READ_HANDLERS as MIXER_READ, WRITE_HANDLERS as MIXER_WRITE
from .arrangement import READ_HANDLERS as ARRANGEMENT_READ, WRITE_HANDLERS as ARRANGEMENT_WRITE
from .grooves import READ_HANDLERS as GROOVES_READ, WRITE_HANDLERS as GROOVES_WRITE


def _merge_handler_dicts(*handler_sets):
    """Merge handler dicts and fail fast on duplicate command names."""
    handlers = {}
    for handler_set in handler_sets:
        overlaps = sorted(set(handlers).intersection(handler_set))
        if overlaps:
            raise ValueError("Duplicate handler registrations: {}".format(", ".join(overlaps)))
        handlers.update(handler_set)
    return handlers


def get_all_read_handlers():
    return _merge_handler_dicts(
        SESSION_READ,
        TRACKS_READ,
        CLIPS_READ,
        DEVICES_READ,
        MIXER_READ,
        ARRANGEMENT_READ,
        GROOVES_READ,
    )


def get_all_write_handlers():
    return _merge_handler_dicts(
        SESSION_WRITE,
        TRACKS_WRITE,
        CLIPS_WRITE,
        DEVICES_WRITE,
        MIXER_WRITE,
        ARRANGEMENT_WRITE,
        GROOVES_WRITE,
    )
