"""Small local WebSocket bridge for the Live2D desktop page."""

from __future__ import annotations

import base64
import hashlib
import json
import socket
import socketserver
import threading
from collections.abc import Mapping
from typing import Any

_WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


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


class _Live2DBridgeTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address: tuple[str, int]) -> None:
        super().__init__(server_address, _Live2DBridgeRequestHandler)
        self.clients: set[socket.socket] = set()
        self.clients_lock = threading.RLock()

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


class _Live2DBridgeRequestHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        server = self.server
        if not isinstance(server, _Live2DBridgeTCPServer):
            return
        if not self._perform_handshake():
            return
        server.add_client(self.request)
        try:
            while self.request.recv(1024):
                pass
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


class Live2DBridgeServer:
    """Background localhost WebSocket broadcaster for Live2D bridge messages."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8879) -> None:
        self.host = host
        self.port = port
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

    def start(self) -> None:
        """Start the bridge server in a background thread."""

        if self.running:
            return
        self._server = _Live2DBridgeTCPServer((self.host, self.port))
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="live2d-bridge-server",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the background bridge server."""

        server = self._server
        if server is None:
            return
        server.shutdown()
        server.server_close()
        self._server = None
        self._thread = None

    def broadcast(self, message: Mapping[str, Any]) -> None:
        """Broadcast a JSON bridge message to connected Live2D clients."""

        server = self._server
        if server is None:
            return
        server.broadcast_text(json.dumps(message, ensure_ascii=False))
