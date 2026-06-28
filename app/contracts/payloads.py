"""Payload type definitions."""

from dataclasses import dataclass
from typing import Any

from app.contracts.states import AppState

# Type alias for payload dictionaries
Payload = dict[str, Any]


@dataclass
class StateChangeRequestedPayload:
    """Payload for state change request events."""

    target_state: AppState | str
    reason: str | None = None


@dataclass
class StateChangedPayload:
    """Payload for state changed events."""

    previous_state: AppState
    current_state: AppState
