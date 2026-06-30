from __future__ import annotations

from dialogue_controller import DialogueController


def main() -> int:
    controller = DialogueController()
    cases = {
        "hello": "greet",
        "hey there": "greet",
        "\u4f60\u597d": "greet",
        "I feel sad today": "comfort",
        "too tired": "comfort",
        "\u6211\u6709\u70b9\u96be\u8fc7": "comfort",
        "tell me a story": "reply",
        "what should we do next": "reply",
        "": "idle",
    }

    failed = []
    for text, expected in cases.items():
        actual = controller.classify(text)
        print(f"{text!r:28} -> {actual}")
        if actual != expected:
            failed.append((text, expected, actual))

    if failed:
        print()
        print("Failed cases:")
        for text, expected, actual in failed:
            print(f"- {text!r}: expected {expected}, got {actual}")
        return 1

    print()
    print("DialogueController tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
