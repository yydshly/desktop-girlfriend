"""Event definitions."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Event type constants
USER_TEXT_SUBMITTED = "user.text_submitted"
ASSISTANT_TEXT_RECEIVED = "assistant.text_received"
STATE_CHANGE_REQUESTED = "state.change_requested"
STATE_CHANGED = "state.changed"
SYSTEM_ERROR = "system.error"
CONVERSATION_CLEARED = "conversation.cleared"
TTS_AUDIO_READY = "tts.audio_ready"
TTS_STOP_REQUESTED = "tts.stop_requested"
TTS_STOPPED = "tts.stopped"
VOICE_INPUT_REQUESTED = "voice.input_requested"
VOICE_RECORDING_STARTED = "voice.recording_started"
VOICE_RECORDING_FINISHED = "voice.recording_finished"
ASR_RECOGNITION_STARTED = "asr.recognition_started"
ASR_TEXT_RECOGNIZED = "asr.text_recognized"

# Memory suggestion events (V8-H)
MEMORY_SUGGESTIONS_DETECTED = "memory.suggestions_detected"
MEMORY_CONFIRM_REQUESTED = "memory.confirm_requested"
MEMORY_REJECT_REQUESTED = "memory.reject_requested"
MEMORY_CONFIRMED = "memory.confirmed"
MEMORY_REJECTED = "memory.rejected"
MEMORY_ERROR = "memory.error"


@dataclass
class BaseEvent:
    """Base event structure."""

    event_type: str
    request_id: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    payload: dict[str, Any] = field(default_factory=dict)
