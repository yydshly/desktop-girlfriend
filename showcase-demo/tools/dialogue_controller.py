from __future__ import annotations


class DialogueController:
    """Tiny rule-based intent controller.

    This is intentionally small. A real LLM intent classifier can replace this
    module later without touching the WebSocket bridge or avatar renderer.
    """

    greeting_keywords = {
        "hi",
        "hello",
        "hey",
        "\u4f60\u597d",
        "\u55e8",
        "\u54c8\u55bd",
        "\u65e9\u5b89",
        "\u65e9\u4e0a\u597d",
        "\u665a\u4e0a\u597d",
    }

    comfort_keywords = {
        "sad",
        "tired",
        "lonely",
        "unhappy",
        "depressed",
        "anxious",
        "stress",
        "\u96be\u8fc7",
        "\u4f24\u5fc3",
        "\u7d2f",
        "\u5b64\u72ec",
        "\u5bc2\u5bde",
        "\u4e0d\u5f00\u5fc3",
        "\u59d4\u5c48",
        "\u538b\u529b",
        "\u7126\u8651",
        "\u5bb3\u6015",
    }

    def classify(self, text: str) -> str:
        normalized = text.strip().lower()
        if not normalized:
            return "idle"
        if any(keyword in normalized for keyword in self.greeting_keywords):
            return "greet"
        if any(keyword in normalized for keyword in self.comfort_keywords):
            return "comfort"
        return "reply"
