"""LiveMCP remote script command handlers."""

from .session import READ_HANDLERS as SESSION_READ, WRITE_HANDLERS as SESSION_WRITE
from .tracks import READ_HANDLERS as TRACKS_READ, WRITE_HANDLERS as TRACKS_WRITE
from .clips import READ_HANDLERS as CLIPS_READ, WRITE_HANDLERS as CLIPS_WRITE
from .devices import READ_HANDLERS as DEVICES_READ, WRITE_HANDLERS as DEVICES_WRITE
from .mixer import READ_HANDLERS as MIXER_READ, WRITE_HANDLERS as MIXER_WRITE


def get_all_read_handlers():
    handlers = {}
    handlers.update(SESSION_READ)
    handlers.update(TRACKS_READ)
    handlers.update(CLIPS_READ)
    handlers.update(DEVICES_READ)
    handlers.update(MIXER_READ)
    return handlers


def get_all_write_handlers():
    handlers = {}
    handlers.update(SESSION_WRITE)
    handlers.update(TRACKS_WRITE)
    handlers.update(CLIPS_WRITE)
    handlers.update(DEVICES_WRITE)
    handlers.update(MIXER_WRITE)
    return handlers
