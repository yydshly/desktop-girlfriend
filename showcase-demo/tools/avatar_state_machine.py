from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from typing import Any

from avatar_ws import MessageSender, serve_avatar_ws
from dialogue_controller import DialogueController
from dialogue_turn import DialogueTurn, DialogueTurnFactory


HOST = "127.0.0.1"
PORT = 8765


@dataclass(frozen=True)
class RuntimeEvent:
    delay: float
    name: str
    payload: dict[str, Any]


class AvatarStateMachine:
    def __init__(self, send: MessageSender) -> None:
        self.send = send

    async def emit(self, name: str, payload: dict[str, Any]) -> None:
        message = {"source": f"state-machine:{name}", **payload}
        await self.send(message)

    async def user_input_started(self) -> None:
        await self.emit("user_input_started", {"type": "avatar.sequence", "name": "listen"})

    async def model_thinking(self) -> None:
        await self.emit("model_thinking", {
            "type": "avatar.state",
            "version": 1,
            "emotion": "calm",
            "action": "think",
            "mouth": "closed",
            "gaze": "center",
            "speaking": False,
            "intensity": 0.5,
        })

    async def tts_started(self) -> None:
        await self.emit("tts_started", {"type": "avatar.sequence", "name": "reply"})

    async def tts_viseme(self, mouth: str, intensity: float) -> None:
        await self.emit("tts_viseme", {
            "type": "avatar.state",
            "version": 1,
            "emotion": "happy",
            "action": "speak",
            "mouth": mouth,
            "gaze": "cursor",
            "speaking": True,
            "intensity": intensity,
        })

    async def tts_finished(self) -> None:
        await self.emit("tts_finished", {
            "type": "avatar.state",
            "version": 1,
            "emotion": "calm",
            "action": "idle",
            "mouth": "closed",
            "gaze": "cursor",
            "speaking": False,
            "intensity": 0.35,
        })

    async def run_sequence(self, name: str) -> None:
        await self.emit(f"sequence_{name}", {"type": "avatar.sequence", "name": name})

    async def run_reply_cycle(self, user_text: str = "") -> None:
        if user_text:
            print(f"user input: {user_text}")
        await self.user_input_started()
        await asyncio.sleep(0.8)
        await self.model_thinking()
        await asyncio.sleep(1.0)
        await self.tts_started()
        for mouth, intensity in [
            ("small", 0.55),
            ("medium", 0.7),
            ("large", 0.85),
            ("medium", 0.68),
        ]:
            await asyncio.sleep(0.45)
            await self.tts_viseme(mouth, intensity)
        await asyncio.sleep(0.7)
        await self.tts_finished()

    async def dialogue_turn_created(self, turn: DialogueTurn) -> None:
        await self.emit("dialogue_turn_created", {"type": "dialogue.turn", "turn": turn.to_dict()})

    async def handle_intent(self, intent: str, user_text: str = "") -> str:
        print(f"dialogue intent: {intent}")

        if intent == "greet":
            await self.run_sequence("greet")
            await asyncio.sleep(2.8)
            return intent

        if intent == "comfort":
            await self.user_input_started()
            await asyncio.sleep(0.6)
            await self.run_sequence("comfort")
            await asyncio.sleep(3.8)
            return intent

        if intent == "reply":
            await self.run_reply_cycle(user_text)
            return intent

        await self.tts_finished()
        return intent

    async def handle_turn(self, turn: DialogueTurn) -> str:
        await self.dialogue_turn_created(turn)
        turn.tts_state = "started"
        intent = await self.handle_intent(turn.intent, turn.user_text)
        turn.tts_state = "finished"
        await self.emit("dialogue_turn_finished", {"type": "dialogue.turn", "turn": turn.to_dict()})
        return intent


DEMO_SCRIPT = [
    RuntimeEvent(0.4, "user_input_started", {}),
    RuntimeEvent(1.5, "model_thinking", {}),
    RuntimeEvent(2.7, "tts_started", {}),
    RuntimeEvent(3.3, "tts_viseme", {"mouth": "small", "intensity": 0.55}),
    RuntimeEvent(3.8, "tts_viseme", {"mouth": "medium", "intensity": 0.7}),
    RuntimeEvent(4.3, "tts_viseme", {"mouth": "large", "intensity": 0.85}),
    RuntimeEvent(5.0, "tts_viseme", {"mouth": "medium", "intensity": 0.68}),
    RuntimeEvent(6.2, "tts_finished", {}),
]


async def state_machine_client(send: MessageSender) -> None:
    machine = AvatarStateMachine(send)
    start = asyncio.get_running_loop().time()

    for item in DEMO_SCRIPT:
        wait = start + item.delay - asyncio.get_running_loop().time()
        if wait > 0:
            await asyncio.sleep(wait)
        handler = getattr(machine, item.name)
        await handler(**item.payload)

    await asyncio.sleep(1.0)


async def interactive_client(send: MessageSender) -> None:
    machine = AvatarStateMachine(send)
    controller = DialogueController()
    turn_factory = DialogueTurnFactory()
    print("interactive avatar state machine ready.")
    print("type a message and press Enter. type /quit to stop this client.")

    while True:
        user_text = await asyncio.to_thread(input, "you> ")
        user_text = user_text.strip()
        if user_text in {"/q", "/quit", "quit", "exit"}:
            await machine.tts_finished()
            break
        if not user_text:
            continue
        intent = controller.classify(user_text)
        turn = turn_factory.create(user_text, intent)
        await machine.handle_turn(turn)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Avatar state machine WebSocket backend.")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--interactive", action="store_true", help="Read user text from stdin and emit one reply cycle per line.")
    args = parser.parse_args()
    await serve_avatar_ws(args.host, args.port, interactive_client if args.interactive else state_machine_client)


if __name__ == "__main__":
    asyncio.run(main())
