"""TCP socket server and command dispatcher for LiveMCP."""

import json
import socket
import threading
import traceback
from queue import Queue

from .handlers import get_all_read_handlers, get_all_write_handlers

PORT = 9877
RECV_SIZE = 8192
RESPONSE_TIMEOUT = 15.0


class LiveMCPServer:
    """TCP server that accepts JSON commands and dispatches to handlers."""

    def __init__(self, control_surface):
        self._cs = control_surface
        self._song = control_surface._song
        self._server_socket = None
        self._server_thread = None
        self._client_threads = []
        self._running = False
        self._read_handlers = get_all_read_handlers()
        self._write_handlers = get_all_write_handlers()

    def log(self, msg):
        self._cs.log_message("LiveMCP: " + str(msg))

    def start(self):
        """Start the TCP server on a background thread."""
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.settimeout(1.0)
            self._server_socket.bind(("127.0.0.1", PORT))
            self._server_socket.listen(5)
            self._running = True
            self._server_thread = threading.Thread(target=self._accept_loop, daemon=True)
            self._server_thread.start()
            self.log("Server started on port {0}".format(PORT))
        except Exception as e:
            self.log("Failed to start server: {0}".format(e))

    def stop(self):
        """Shut down the server and all client threads."""
        self._running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
        if self._server_thread:
            self._server_thread.join(timeout=2.0)
        self.log("Server stopped")

    def _accept_loop(self):
        """Accept incoming connections."""
        while self._running:
            try:
                client, addr = self._server_socket.accept()
                self.log("Client connected from {0}".format(addr))
                self._client_threads = [t for t in self._client_threads if t.is_alive()]
                t = threading.Thread(target=self._handle_client, args=(client,), daemon=True)
                t.start()
                self._client_threads.append(t)
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    self.log("Accept error: {0}".format(e))

    def _handle_client(self, client):
        """Handle a single client connection."""
        buffer = ""
        try:
            while self._running:
                data = client.recv(RECV_SIZE)
                if not data:
                    break
                buffer += data.decode("utf-8")
                try:
                    command = json.loads(buffer)
                    buffer = ""
                except (json.JSONDecodeError, ValueError):
                    continue

                try:
                    response = self._dispatch(command)
                    self._send_json(client, {"status": "success", "result": response})
                except Exception as e:
                    self.log("Command error: {0}\n{1}".format(e, traceback.format_exc()))
                    self._send_json(client, {"status": "error", "error": str(e)})
        except Exception as e:
            self.log("Client error: {0}".format(e))
        finally:
            try:
                client.close()
            except Exception:
                pass

    def _send_json(self, client, data):
        """Send a JSON response to the client."""
        payload = json.dumps(data)
        client.sendall(payload.encode("utf-8"))

    def _dispatch(self, command):
        """Route a command to the appropriate handler."""
        cmd_type = command.get("type", "")
        params = command.get("params", {})

        # Read-only commands run on the socket thread
        if cmd_type in self._read_handlers:
            handler = self._read_handlers[cmd_type]
            return handler(self._cs, params)

        # Write commands run on Ableton's main thread
        if cmd_type in self._write_handlers:
            handler = self._write_handlers[cmd_type]
            return self._run_on_main_thread(handler, params)

        raise ValueError("Unknown command: {0}".format(cmd_type))

    def _run_on_main_thread(self, handler, params):
        """Schedule a handler on Ableton's main thread and wait for the result."""
        response_queue = Queue()

        def task():
            try:
                result = handler(self._cs, params)
                response_queue.put({"ok": True, "result": result})
            except Exception as e:
                self.log("Handler error: {0}\n{1}".format(e, traceback.format_exc()))
                response_queue.put({"ok": False, "error": str(e)})

        try:
            self._cs.schedule_message(0, task)
        except AssertionError:
            # Already on main thread
            task()

        response = response_queue.get(timeout=RESPONSE_TIMEOUT)
        if response["ok"]:
            return response["result"]
        raise RuntimeError(response["error"])
