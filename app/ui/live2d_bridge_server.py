"""Small local WebSocket bridge for the Live2D desktop page."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import socket
import socketserver
import threading
from collections.abc import Mapping
from collections.abc import Callable
from typing import Any

_WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
logger = logging.getLogger(__name__)


def build_websocket_accept_key(client_key: str) -> str:
    """Build the Sec-WebSocket-Accept response value."""

    digest = hashlib.sha1(f"{client_key}{_WEBSOCKET_GUID}".encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")


def encode_websocket_text_frame(text: str) -> bytes:
    """Encode a server-to-client WebSocket text frame."""

    payload = text.encode("utf-8")
    length = len(payload)
    if length < 126:
        return bytes([0x81, length]) + payload
    if length <= 0xFFFF:
        return bytes([0x81, 126]) + length.to_bytes(2, "big") + payload
    return bytes([0x81, 127]) + length.to_bytes(8, "big") + payload


def decode_websocket_text_frame(data: bytes) -> str:
    """Decode a client-to-server WebSocket text frame."""

    if len(data) < 2:
        return ""
    first, second = data[0], data[1]
    opcode = first & 0x0F
    if opcode != 0x01:
        return ""
    masked = bool(second & 0x80)
    length = second & 0x7F
    offset = 2
    if length == 126:
        if len(data) < offset + 2:
            return ""
        length = int.from_bytes(data[offset : offset + 2], "big")
        offset += 2
    elif length == 127:
        if len(data) < offset + 8:
            return ""
        length = int.from_bytes(data[offset : offset + 8], "big")
        offset += 8
    if masked:
        if len(data) < offset + 4:
            return ""
        mask = data[offset : offset + 4]
        offset += 4
        payload = data[offset : offset + length]
        return bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload)).decode(
            "utf-8",
            errors="replace",
        )
    return data[offset : offset + length].decode("utf-8", errors="replace")


class _Live2DBridgeTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        on_runtime_status: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        super().__init__(server_address, _Live2DBridgeRequestHandler)
        self.clients: set[socket.socket] = set()
        self.clients_lock = threading.RLock()
        self.latest_runtime_status: dict[str, Any] = {}
        self.on_runtime_status = on_runtime_status

    def add_client(self, client: socket.socket) -> None:
        with self.clients_lock:
            self.clients.add(client)

    def remove_client(self, client: socket.socket) -> None:
        with self.clients_lock:
            self.clients.discard(client)

    def broadcast_text(self, text: str) -> None:
        frame = encode_websocket_text_frame(text)
        with self.clients_lock:
            clients = list(self.clients)
        for client in clients:
            try:
                client.sendall(frame)
            except OSError:
                self.remove_client(client)

    def handle_runtime_status_message(self, message: Any) -> None:
        if not is_valid_runtime_status(message):
            logger.warning("Ignored invalid Live2D runtime status message=%r", message)
            return
        self.latest_runtime_status = dict(message)
        logger.info("Live2D runtime status received type=%s", message.get("type"))
        if self.on_runtime_status is not None:
            self.on_runtime_status(dict(message))


class _Live2DBridgeRequestHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        server = self.server
        if not isinstance(server, _Live2DBridgeTCPServer):
            return
        if not self._perform_handshake():
            return
        server.add_client(self.request)
        try:
            while True:
                data = self.request.recv(4096)
                if not data:
                    break
                text = decode_websocket_text_frame(data)
                if not text:
                    continue
                try:
                    message = json.loads(text)
                except json.JSONDecodeError:
                    logger.warning("Ignored invalid Live2D runtime status frame")
                    continue
                server.handle_runtime_status_message(message)
        except OSError:
            pass
        finally:
            server.remove_client(self.request)

    def _perform_handshake(self) -> bool:
        data = self.request.recv(4096)
        headers = _parse_http_headers(data)
        client_key = headers.get("sec-websocket-key")
        if not client_key:
            return False
        accept_key = build_websocket_accept_key(client_key)
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept_key}\r\n"
            "\r\n"
        )
        self.request.sendall(response.encode("ascii"))
        return True


def _parse_http_headers(data: bytes) -> dict[str, str]:
    text = data.decode("ascii", errors="ignore")
    headers: dict[str, str] = {}
    for line in text.split("\r\n")[1:]:
        if ":" not in line:
            continue
        name, value = line.split(":", 1)
        headers[name.strip().lower()] = value.strip()
    return headers


def is_valid_runtime_status(message: Any) -> bool:
    if not isinstance(message, Mapping):
        return False
    message_type = message.get("type")
    if not isinstance(message_type, str) or not message_type.startswith("live2d."):
        return False
    return True


class Live2DBridgeServer:
    """Background localhost WebSocket broadcaster for Live2D bridge messages."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8879,
        on_runtime_status: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self._on_runtime_status = on_runtime_status
        self._server: _Live2DBridgeTCPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        """Return the WebSocket URL consumed by the Live2D page."""

        return f"ws://{self.host}:{self.port}"

    @property
    def running(self) -> bool:
        """Return True when the background server is active."""

        return self._server is not None and self._thread is not None and self._thread.is_alive()

    @property
    def latest_runtime_status(self) -> dict[str, Any]:
        """Return the latest Web-reported Live2D runtime status."""

        if self._server is None:
            return {}
        return dict(self._server.latest_runtime_status)

    def start(self) -> None:
        """Start the bridge server in a background thread."""

        if self.running:
            return
        self._server = _Live2DBridgeTCPServer((self.host, self.port), self._on_runtime_status)
        bound_host, bound_port = self._server.server_address
        self.host = str(bound_host)
        self.port = int(bound_port)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="live2d-bridge-server",
            daemon=True,
        )
        self._thread.start()
        logger.info("Live2D bridge server started url=%s", self.url)

    def stop(self) -> None:
        """Stop the background bridge server."""

        server = self._server
        if server is None:
            return
        logger.info("Stopping Live2D bridge server url=%s", self.url)
        server.shutdown()
        server.server_close()
        self._server = None
        self._thread = None
        logger.info("Live2D bridge server stopped")

    def broadcast(self, message: Mapping[str, Any]) -> None:
        """Broadcast a JSON bridge message to connected Live2D clients."""

        server = self._server
        if server is None:
            return
        with server.clients_lock:
            client_count = len(server.clients)
        logger.info(
            "Broadcasting Live2D bridge message type=%s clients=%s",
            message.get("type", "unknown"),
            client_count,
        )
        server.broadcast_text(json.dumps(message, ensure_ascii=False))

    def handle_runtime_status_message(self, message: Any) -> None:
        """Record a runtime status message without requiring a socket."""

        if self._server is not None:
            self._server.handle_runtime_status_message(message)
            return
        if not is_valid_runtime_status(message):
            logger.warning("Ignored invalid Live2D runtime status message=%r", message)

    def set_runtime_status_callback(
        self,
        callback: Callable[[dict[str, Any]], None] | None,
    ) -> None:
        """Set the callback invoked when Web clients report runtime status."""

        self._on_runtime_status = callback
        if self._server is not None:
            self._server.on_runtime_status = callback
