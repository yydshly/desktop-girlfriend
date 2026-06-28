"""Integration tests for dialogue completion and TTS speaking state."""

import time
from collections.abc import Callable

from app.brain.async_dialogue_controller import AsyncDialogueController
from app.brain.prompts.registry import PromptRegistry
from app.brain.providers.base import ChatProvider, ChatRequest, ChatResponse
from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    STATE_CHANGED,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)
from app.contracts.states import AppState
from app.core.event_bus import EventBus
from app.core.state_controller import StateController
from app.core.state_machine import StateMachine
from app.expression.tts.controller import TTSController
from app.expression.tts.providers.base import TTSProvider, TTSRequest, TTSResponse


class ImmediateChatProvider(ChatProvider):
    """Chat provider that returns a reply immediately."""

    def generate(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(text="Reply with voice")


class AudioPathTTSProvider(TTSProvider):
    """TTS provider that returns an audio path for embedded playback."""

    supports_audio_path_playback = True

    def synthesize(self, request: TTSRequest) -> TTSResponse:
        return TTSResponse(duration_seconds=0.0, audio_path="/tmp/reply.mp3")

    def speak(self, request: TTSRequest) -> TTSResponse:
        return self.synthesize(request)


class HoldingAudioPlayer:
    """Audio player that stays playing until explicitly stopped or finished."""

    def __init__(self) -> None:
        self._is_playing = False
        self._on_finished: Callable[[], None] | None = None

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def play(
        self,
        path: str,
        on_finished: Callable[[], None],
        on_error: Callable[[str], None],
    ) -> None:
        self._is_playing = True
        self._on_finished = on_finished

    def stop(self) -> bool:
        was_playing = self._is_playing
        self._is_playing = False
        self._on_finished = None
        return was_playing


def test_dialogue_complete_does_not_override_tts_speaking_state() -> None:
    """Assistant response should leave the app SPEAKING while audio is playing."""
    event_bus = EventBus()
    state_machine = StateMachine()
    state_controller = StateController(event_bus, state_machine)
    audio_player = HoldingAudioPlayer()

    def dispatch_event(event: BaseEvent) -> None:
        event_bus.publish(event)

    dialogue = AsyncDialogueController(
        event_bus=event_bus,
        provider=ImmediateChatProvider(),
        prompt_registry=PromptRegistry(),
        dispatch_event=dispatch_event,
        complete_state_after_assistant_response=False,
    )
    tts = TTSController(
        event_bus=event_bus,
        provider=AudioPathTTSProvider(),
        dispatch_event=dispatch_event,
        audio_player=audio_player,  # type: ignore[arg-type]
    )

    state_events: list[BaseEvent] = []
    assistant_events: list[BaseEvent] = []
    event_bus.subscribe(STATE_CHANGED, state_events.append)
    event_bus.subscribe(ASSISTANT_TEXT_RECEIVED, assistant_events.append)
    state_controller.start()
    tts.start()
    dialogue.start()

    event_bus.publish(
        BaseEvent(
            event_type=USER_TEXT_SUBMITTED,
            request_id="req-dialogue-tts",
            source="test",
            payload={"text": "Hello"},
        )
    )

    for _ in range(50):
        if audio_player.is_playing and assistant_events:
            break
        time.sleep(0.01)

    assert audio_player.is_playing is True
    assert state_machine.get_state() == AppState.SPEAKING
    assert state_events[-1].payload["current_state"] == AppState.SPEAKING.value
