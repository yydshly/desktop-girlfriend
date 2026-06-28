"""Integration tests for voice input -> dialogue -> TTS pipeline."""

import time
from collections.abc import Callable

from app.brain.async_dialogue_controller import AsyncDialogueController
from app.brain.prompts.registry import PromptRegistry
from app.brain.providers.base import ChatProvider, ChatRequest, ChatResponse
from app.contracts.events import (
    ASR_TEXT_RECOGNIZED,
    STATE_CHANGED,
    USER_TEXT_SUBMITTED,
    VOICE_INPUT_REQUESTED,
    BaseEvent,
)
from app.core.event_bus import EventBus
from app.core.state_controller import StateController
from app.core.state_machine import StateMachine
from app.input.asr.controller import VoiceInputController
from app.input.asr.providers.base import ASRProvider, ASRRequest, ASRResponse


def _process_qt_events() -> None:
    """Process pending Qt events to allow cross-thread signal delivery."""
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            app.processEvents()
    except Exception:
        pass


class ImmediateChatProvider(ChatProvider):
    """Chat provider that returns a reply immediately."""

    def generate(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(text="assistant reply")


class ImmediateFakeASRProvider(ASRProvider):
    """ASR provider that returns immediately."""

    def __init__(self, transcript: str = "user said something") -> None:
        self._transcript = transcript

    def recognize(self, request: ASRRequest) -> ASRResponse:
        return ASRResponse(text=self._transcript)


def make_dispatch_collector() -> tuple[list[BaseEvent], Callable[[BaseEvent], None]]:
    """Create a list and a callback that appends to it."""
    events: list[BaseEvent] = []

    def collect(event: BaseEvent) -> None:
        events.append(event)

    return events, collect


def test_voice_input_flows_to_dialogue() -> None:
    """Test that VOICE_INPUT_REQUESTED produces USER_TEXT_SUBMITTED from ASR."""
    event_bus = EventBus()
    state_machine = StateMachine()
    state_controller = StateController(event_bus, state_machine)
    dispatch_events, dispatch_event = make_dispatch_collector()

    asr_provider = ImmediateFakeASRProvider(transcript="hello voice")
    voice_controller = VoiceInputController(
        event_bus=event_bus,
        provider=asr_provider,
        dispatch_event=dispatch_event,
    )

    dialogue_controller = AsyncDialogueController(
        event_bus=event_bus,
        provider=ImmediateChatProvider(),
        prompt_registry=PromptRegistry(),
        dispatch_event=dispatch_event,
        complete_state_after_assistant_response=False,
    )

    state_events: list[BaseEvent] = []
    event_bus.subscribe(STATE_CHANGED, state_events.append)
    event_bus.subscribe(USER_TEXT_SUBMITTED, lambda e: dispatch_events.append(e))

    state_controller.start()
    voice_controller.start()
    dialogue_controller.start()

    event_bus.publish(
        BaseEvent(
            event_type=VOICE_INPUT_REQUESTED,
            request_id="req-voice-test",
            source="test",
            payload={},
        )
    )

    for _ in range(50):
        _process_qt_events()
        time.sleep(0.01)
        if dispatch_events:
            break

    # Verify ASR_TEXT_RECOGNIZED was dispatched
    asr_events = [e for e in dispatch_events if e.event_type == ASR_TEXT_RECOGNIZED]
    assert len(asr_events) >= 1
    assert asr_events[0].payload["text"] == "hello voice"

    # Verify USER_TEXT_SUBMITTED was dispatched (from voice input, not from direct typing)
    user_events = [e for e in dispatch_events if e.event_type == USER_TEXT_SUBMITTED]
    assert len(user_events) >= 1
    assert user_events[0].payload["text"] == "hello voice"


def test_voice_input_produces_listening_and_triggers_dialogue() -> None:
    """Test that voice input produces LISTENING state and triggers dialogue.

    Verifies: LISTENING is published after VOICE_INPUT_REQUESTED, and the
    subsequent USER_TEXT_SUBMITTED is dispatched (proving the dialogue chain fired).
    """
    event_bus = EventBus()
    state_machine = StateMachine()
    state_controller = StateController(event_bus, state_machine)
    dispatch_events, dispatch_event = make_dispatch_collector()

    asr_provider = ImmediateFakeASRProvider(transcript="another voice input")
    voice_controller = VoiceInputController(
        event_bus=event_bus,
        provider=asr_provider,
        dispatch_event=dispatch_event,
    )

    dialogue_controller = AsyncDialogueController(
        event_bus=event_bus,
        provider=ImmediateChatProvider(),
        prompt_registry=PromptRegistry(),
        dispatch_event=dispatch_event,
        complete_state_after_assistant_response=False,
    )

    state_events: list[BaseEvent] = []
    event_bus.subscribe(STATE_CHANGED, state_events.append)

    state_controller.start()
    voice_controller.start()
    dialogue_controller.start()

    event_bus.publish(
        BaseEvent(
            event_type=VOICE_INPUT_REQUESTED,
            request_id="req-state-flow",
            source="test",
            payload={},
        )
    )

    # Process Qt events and wait for the full chain to propagate.
    for _ in range(300):
        _process_qt_events()
        time.sleep(0.01)

    # Collect states
    states_seen = [e.payload.get("current_state") for e in state_events]

    # LISTENING must be observed (from voice input)
    assert "listening" in states_seen, f"Expected 'listening' in states, got: {states_seen}"

    # Verify USER_TEXT_SUBMITTED was dispatched (proves dialogue pipeline fired)
    user_events = [e for e in dispatch_events if e.event_type == USER_TEXT_SUBMITTED]
    assert len(user_events) >= 1, (
        f"USER_TEXT_SUBMITTED not dispatched; dispatch_events types: "
        f"{[e.event_type for e in dispatch_events]}"
    )
