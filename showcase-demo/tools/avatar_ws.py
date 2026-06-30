from __future__ import annotations

import asyncio
import base64
import hashlib
import json
from collections.abc import Awaitable, Callable
from typing import Any


WS_MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
MessageSender = Callable[[dict[str, Any]], Awaitable[None]]
ClientHandler = Callable[[MessageSender], Awaitable[None]]


async def read_http_headers(reader: asyncio.StreamReader) -> dict[str, str]:
    raw = b""
    while b"\r\n\r\n" not in raw:
        chunk = await reader.read(1024)
        if not chunk:
            break
        raw += chunk

    lines = raw.decode("utf-8", errors="replace").split("\r\n")
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


def websocket_accept_key(client_key: str) -> str:
    digest = hashlib.sha1((client_key + WS_MAGIC).encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")


def encode_text_frame(text: str) -> bytes:
    payload = text.encode("utf-8")
    length = len(payload)
    if length < 126:
        header = bytes([0x81, length])
    elif length < 65536:
        header = bytes([0x81, 126]) + length.to_bytes(2, "big")
    else:
        header = bytes([0x81, 127]) + length.to_bytes(8, "big")
    return header + payload


async def serve_avatar_ws(host: str, port: int, client_handler: ClientHandler) -> None:
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        headers = await read_http_headers(reader)
        client_key = headers.get("sec-websocket-key")
        if not client_key:
            writer.close()
            await writer.wait_closed()
            return

        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {websocket_accept_key(client_key)}\r\n"
            "\r\n"
        )
        writer.write(response.encode("ascii"))
        await writer.drain()
        print(f"client connected: {peer}")

        async def send(payload: dict[str, Any]) -> None:
            text = json.dumps(payload, ensure_ascii=False)
            writer.write(encode_text_frame(text))
            await writer.drain()
            print(f"sent: {text}")

        try:
            await client_handler(send)
        finally:
            writer.close()
            await writer.wait_closed()
            print(f"client disconnected: {peer}")

    server = await asyncio.start_server(handle_client, host, port)
    print(f"avatar websocket listening on ws://{host}:{port}/avatar")
    async with server:
        await server.serve_forever()
