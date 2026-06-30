"""Send demo app events through the Live2D desktop bridge."""

from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.contracts.events import (  # noqa: E402
    ASSISTANT_TEXT_RECEIVED,
    STATE_CHANGED,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)
from app.ui.live2d_bridge import Live2DBridgeEventMapper  # noqa: E402
from app.ui.live2d_bridge_server import Live2DBridgeServer  # noqa: E402


def _event(event_type: str, request_id: str, payload: dict) -> BaseEvent:
    return BaseEvent(
        event_type=event_type,
        request_id=request_id,
        source="live2d_bridge_demo",
        payload=payload,
    )


def main() -> int:
    """Run a short bridge demo for an already-open Live2D desktop window."""

    server = Live2DBridgeServer()
    mapper = Live2DBridgeEventMapper()
    server.start()
    print(f"Live2D bridge demo running at {server.url}")
    print("Open or focus the Live2D desktop window; demo events will play now.")

    events = [
        _event(USER_TEXT_SUBMITTED, "demo-1", {"text": "你好，小云"}),
        _event(STATE_CHANGED, "demo-2", {"current_state": "thinking"}),
        _event(
            ASSISTANT_TEXT_RECEIVED,
            "demo-3",
            {"text": "我在这里，正在听你说。"},
        ),
        _event(STATE_CHANGED, "demo-4", {"current_state": "idle"}),
    ]

    try:
        time.sleep(1.2)
        for event in events:
            message = mapper.map_event(event)
            if message is not None:
                server.broadcast(message)
                print(f"sent: {message['type']} {message['payload']}")
            time.sleep(1.4)
    finally:
        server.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
