"""Event definitions."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# Event type constants
USER_TEXT_SUBMITTED = "user.text_submitted"
STATE_CHANGED = "state.changed"
SYSTEM_ERROR = "system.error"


@dataclass
class BaseEvent:
    """Base event structure."""

    event_type: str
    request_id: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    payload: dict[str, Any] = field(default_factory=dict)
