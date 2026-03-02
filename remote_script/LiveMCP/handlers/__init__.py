"""LiveMCP remote script command handlers."""

from .session import READ_HANDLERS as SESSION_READ, WRITE_HANDLERS as SESSION_WRITE
from .tracks import READ_HANDLERS as TRACKS_READ, WRITE_HANDLERS as TRACKS_WRITE
from .clips import READ_HANDLERS as CLIPS_READ, WRITE_HANDLERS as CLIPS_WRITE
from .devices import READ_HANDLERS as DEVICES_READ, WRITE_HANDLERS as DEVICES_WRITE
from .mixer import READ_HANDLERS as MIXER_READ, WRITE_HANDLERS as MIXER_WRITE
from .arrangement import READ_HANDLERS as ARRANGEMENT_READ, WRITE_HANDLERS as ARRANGEMENT_WRITE
from .grooves import READ_HANDLERS as GROOVES_READ, WRITE_HANDLERS as GROOVES_WRITE


def get_all_read_handlers():
    handlers = {}
    handlers.update(SESSION_READ)
    handlers.update(TRACKS_READ)
    handlers.update(CLIPS_READ)
    handlers.update(DEVICES_READ)
    handlers.update(MIXER_READ)
    handlers.update(ARRANGEMENT_READ)
    handlers.update(GROOVES_READ)
    return handlers


def get_all_write_handlers():
    handlers = {}
    handlers.update(SESSION_WRITE)
    handlers.update(TRACKS_WRITE)
    handlers.update(CLIPS_WRITE)
    handlers.update(DEVICES_WRITE)
    handlers.update(MIXER_WRITE)
    handlers.update(ARRANGEMENT_WRITE)
    handlers.update(GROOVES_WRITE)
    return handlers
