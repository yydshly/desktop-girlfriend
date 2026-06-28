"""Application state definitions."""

from enum import StrEnum


class AppState(StrEnum):
    """Application state enumeration."""

    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    ERROR = "error"
