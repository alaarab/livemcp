"""LiveMCP — Ableton Live MIDI Remote Script for MCP integration."""

from .server import LiveMCPServer

try:
    from _Framework.ControlSurface import ControlSurface
except ImportError:
    ControlSurface = object


class LiveMCP(ControlSurface):
    """Main control surface that starts the LiveMCP socket server."""

    def __init__(self, c_instance):
        super().__init__(c_instance)
        self._song = self.song()
        self._server = LiveMCPServer(self)
        self._server.start()
        self.show_message("LiveMCP: Server started on port 9877")
        self.log_message("LiveMCP: Initialized successfully")

    def disconnect(self):
        self._server.stop()
        self.log_message("LiveMCP: Disconnected")
        super().disconnect()


def create_instance(c_instance):
    """Entry point called by Ableton Live."""
    return LiveMCP(c_instance)
