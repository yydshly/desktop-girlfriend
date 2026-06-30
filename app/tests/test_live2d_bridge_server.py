"""Tests for the local Live2D WebSocket bridge server."""

from __future__ import annotations

import json
import socket
import time

from app.ui.live2d_bridge_server import (
    Live2DBridgeServer,
    build_websocket_accept_key,
    encode_websocket_text_frame,
)


def test_build_websocket_accept_key_matches_rfc_example() -> None:
    """Handshake accept key follows RFC 6455."""
    assert (
        build_websocket_accept_key("dGhlIHNhbXBsZSBub25jZQ==")
        == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="
    )


def test_encode_text_frame_short_payload() -> None:
    """Short text payloads are encoded as unmasked server frames."""
    assert encode_websocket_text_frame("hi") == b"\x81\x02hi"


def test_bridge_server_start_stop() -> None:
    """Bridge server starts and stops cleanly."""
    server = Live2DBridgeServer(port=0)

    server.start()
    assert server.running is True
    assert server.url.startswith("ws://127.0.0.1:")

    server.stop()
    assert server.running is False


def test_bridge_server_accepts_client_and_broadcasts_json() -> None:
    """A WebSocket client can connect and receive a JSON bridge message."""
    server = Live2DBridgeServer(port=0)
    server.start()
    assert server._server is not None
    host, port = server._server.server_address

    client = socket.create_connection((host, port), timeout=2)
    try:
        client.sendall(
            (
                "GET / HTTP/1.1\r\n"
                f"Host: {host}:{port}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                "Sec-WebSocket-Version: 13\r\n"
                "\r\n"
            ).encode("ascii")
        )
        handshake = client.recv(4096)
        assert b"101 Switching Protocols" in handshake
        client.settimeout(0.2)

        message = {"type": "avatar.state", "payload": {"state": "happy"}}
        frame = b""
        for _ in range(10):
            server.broadcast(message)
            try:
                frame = client.recv(4096)
                if frame:
                    break
            except TimeoutError:
                pass
            time.sleep(0.01)

        assert frame[0] == 0x81
        payload_length = frame[1]
        assert json.loads(frame[2 : 2 + payload_length].decode("utf-8")) == message
    finally:
        client.close()
        server.stop()
