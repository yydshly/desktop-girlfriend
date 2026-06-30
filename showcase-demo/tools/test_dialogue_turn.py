from __future__ import annotations

from dialogue_turn import DialogueTurnFactory


def main() -> int:
    factory = DialogueTurnFactory()
    turn = factory.create("hello", "greet")
    data = turn.to_dict()

    checks = {
        "turn_id": bool(data.get("turn_id")),
        "created_at": bool(data.get("created_at")),
        "user_text": data.get("user_text") == "hello",
        "intent": data.get("intent") == "greet",
        "response_text": data.get("response_text") == "Hi, I am here.",
        "tts_state": data.get("tts_state") == "pending",
    }

    for name, passed in checks.items():
        print(f"{name:<14} {passed}")

    if not all(checks.values()):
        return 1

    print()
    print("DialogueTurn tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
