from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from typing import Any

from avatar_ws import MessageSender, serve_avatar_ws


HOST = "127.0.0.1"
PORT = 8765


@dataclass(frozen=True)
class TimedMessage:
    delay: float
    payload: dict[str, Any]


SCRIPT = [
    TimedMessage(0.4, {"type": "avatar.sequence", "name": "greet", "source": "mock-ws"}),
    TimedMessage(4.0, {"type": "avatar.sequence", "name": "reply", "source": "mock-ws"}),
    TimedMessage(8.8, {"type": "avatar.state", "version": 1, "source": "mock-ws", "emotion": "calm", "action": "idle", "mouth": "closed", "gaze": "cursor", "speaking": False, "intensity": 0.35}),
]


async def scripted_client(send: MessageSender) -> None:
    start = asyncio.get_running_loop().time()
    for item in SCRIPT:
        wait = start + item.delay - asyncio.get_running_loop().time()
        if wait > 0:
            await asyncio.sleep(wait)
        await send(item.payload)
    await asyncio.sleep(1.0)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Mock avatar WebSocket backend.")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    await serve_avatar_ws(args.host, args.port, scripted_client)


if __name__ == "__main__":
    asyncio.run(main())
