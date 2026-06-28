"""Application state definitions."""

from enum import Enum


class AppState(str, Enum):
    """Application state enumeration."""

    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    ERROR = "error"
