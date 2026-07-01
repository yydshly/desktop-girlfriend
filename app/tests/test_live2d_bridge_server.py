"""Tests for the local Live2D WebSocket bridge server."""

from __future__ import annotations

import json
import logging
import socket
import time

from app.ui.live2d_bridge_server import (
    Live2DBridgeServer,
    build_websocket_accept_key,
    decode_websocket_text_frame,
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


def test_decode_masked_client_text_frame() -> None:
    """Client-to-server masked text frames are decoded for status messages."""
    payload = b'{"type":"live2d.runtime_ready"}'
    mask = b"\x01\x02\x03\x04"
    masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    frame = bytes([0x81, 0x80 | len(payload)]) + mask + masked

    assert decode_websocket_text_frame(frame) == payload.decode("utf-8")


def test_bridge_server_start_stop() -> None:
    """Bridge server starts and stops cleanly."""
    server = Live2DBridgeServer(port=0)

    server.start()
    assert server.running is True
    assert server.url.startswith("ws://127.0.0.1:")

    server.stop()
    assert server.running is False


def test_bridge_server_logs_start_stop(caplog) -> None:
    """Bridge server logs its bound URL and shutdown for diagnostics."""
    caplog.set_level(logging.INFO)
    server = Live2DBridgeServer(port=0)

    server.start()
    assert "Live2D bridge server started" in caplog.text
    assert "ws://127.0.0.1:" in caplog.text

    server.stop()
    assert "Live2D bridge server stopped" in caplog.text


def test_bridge_server_logs_broadcast_message_type(caplog) -> None:
    """Bridge broadcast logs message type and connected client count."""
    caplog.set_level(logging.INFO)
    server = Live2DBridgeServer(port=0)
    server.start()
    try:
        server.broadcast({"type": "avatar.state", "payload": {"state": "happy"}})
    finally:
        server.stop()

    assert "Broadcasting Live2D bridge message" in caplog.text
    assert "type=avatar.state" in caplog.text
    assert "clients=0" in caplog.text


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


def test_bridge_server_records_runtime_status_from_client_frame() -> None:
    """Web Live2D clients can report runtime status back to Python."""
    received: list[dict] = []
    server = Live2DBridgeServer(port=0, on_runtime_status=received.append)
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
        assert b"101 Switching Protocols" in client.recv(4096)

        message = {
            "type": "live2d.model_loaded",
            "timestamp": "2026-07-02T00:00:00.000Z",
            "modelUrl": "./model.model3.json",
            "modelId": "sample/Hiyori",
            "details": {"motionCount": 10},
        }
        client.sendall(_masked_client_text_frame(json.dumps(message)))
        for _ in range(20):
            if server.latest_runtime_status:
                break
            time.sleep(0.02)

        assert server.latest_runtime_status == message
        assert received[-1] == message
    finally:
        client.close()
        server.stop()


def test_bridge_server_ignores_invalid_runtime_status(caplog) -> None:
    """Invalid Web status messages are ignored and logged, not raised."""
    caplog.set_level(logging.WARNING)
    server = Live2DBridgeServer(port=0)

    server.handle_runtime_status_message({"type": "avatar.state"})
    server.handle_runtime_status_message("not a dict")  # type: ignore[arg-type]

    assert server.latest_runtime_status == {}
    assert "Ignored invalid Live2D runtime status" in caplog.text


def _masked_client_text_frame(text: str) -> bytes:
    payload = text.encode("utf-8")
    mask = b"\x01\x02\x03\x04"
    masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    if len(payload) < 126:
        header = bytes([0x81, 0x80 | len(payload)])
    else:
        header = bytes([0x81, 0x80 | 126]) + len(payload).to_bytes(2, "big")
    return header + mask + masked
