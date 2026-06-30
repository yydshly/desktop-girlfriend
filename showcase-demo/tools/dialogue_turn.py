from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class DialogueTurn:
    user_text: str
    intent: str
    response_text: str
    tts_state: str = "pending"
    turn_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class DialogueTurnFactory:
    responses = {
        "greet": "Hi, I am here.",
        "comfort": "I hear you. I will stay with you for a bit.",
        "reply": "I am thinking about that with you.",
        "idle": "",
    }

    def create(self, user_text: str, intent: str) -> DialogueTurn:
        return DialogueTurn(
            user_text=user_text,
            intent=intent,
            response_text=self.responses.get(intent, self.responses["reply"]),
        )
