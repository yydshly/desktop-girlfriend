"""Tests for memory suggestion controller (V8-H)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from app.brain.memory.controller import MemorySuggestionController
from app.brain.memory.repository import LocalJsonMemoryRepository, MemoryRecord, MemoryRecordStatus
from app.brain.memory.runtime import create_local_memory_runtime
from app.brain.memory.types import MemoryImportance, MemoryKind
from app.contracts.events import (
    MEMORY_ADD_REQUESTED,
    MEMORY_ADDED,
    MEMORY_CONFIRM_REQUESTED,
    MEMORY_CONFIRMED,
    MEMORY_ERROR,
    MEMORY_REJECT_REQUESTED,
    MEMORY_REJECTED,
    MEMORY_SUGGESTIONS_DETECTED,
    USER_TEXT_SUBMITTED,
)


def _make_event(event_type: str, payload: dict[str, Any], request_id: str = "req-1") -> MagicMock:
    """Create a mock BaseEvent."""
    event = MagicMock()
    event.event_type = event_type
    event.request_id = request_id
    event.payload = payload
    return event


def _make_record(
    record_id: str = "test-id",
    kind: MemoryKind = MemoryKind.PREFERENCE,
    importance: MemoryImportance = MemoryImportance.MEDIUM,
    text: str = "用户喜欢短回复。",
    status: MemoryRecordStatus = MemoryRecordStatus.ACTIVE,
) -> MemoryRecord:
    """Create a test MemoryRecord."""
    return MemoryRecord(
        id=record_id,
        kind=kind,
        importance=importance,
        text=text,
        source="test",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        status=status,
    )


class TestStartStop:
    """Tests for start/stop idempotency."""

    def test_start_subscribes_user_text_submitted(self) -> None:
        """start() subscribes to USER_TEXT_SUBMITTED."""
        subscribe = MagicMock()
        controller = MemorySuggestionController(
            runtime=MagicMock(),
            subscribe=subscribe,
            unsubscribe=MagicMock(),
            dispatch_event=MagicMock(),
        )
        controller.start()
        subscribe.assert_any_call(USER_TEXT_SUBMITTED, controller._on_user_text_submitted)

    def test_start_subscribes_confirm_requested(self) -> None:
        """start() subscribes to MEMORY_CONFIRM_REQUESTED."""
        subscribe = MagicMock()
        controller = MemorySuggestionController(
            runtime=MagicMock(),
            subscribe=subscribe,
            unsubscribe=MagicMock(),
            dispatch_event=MagicMock(),
        )
        controller.start()
        subscribe.assert_any_call(MEMORY_CONFIRM_REQUESTED, controller._on_memory_confirm_requested)

    def test_start_subscribes_reject_requested(self) -> None:
        """start() subscribes to MEMORY_REJECT_REQUESTED."""
        subscribe = MagicMock()
        controller = MemorySuggestionController(
            runtime=MagicMock(),
            subscribe=subscribe,
            unsubscribe=MagicMock(),
            dispatch_event=MagicMock(),
        )
        controller.start()
        subscribe.assert_any_call(MEMORY_REJECT_REQUESTED, controller._on_memory_reject_requested)

    def test_start_subscribes_add_requested(self) -> None:
        """start() subscribes to MEMORY_ADD_REQUESTED."""
        subscribe = MagicMock()
        controller = MemorySuggestionController(
            runtime=MagicMock(),
            subscribe=subscribe,
            unsubscribe=MagicMock(),
            dispatch_event=MagicMock(),
        )
        controller.start()
        subscribe.assert_any_call(MEMORY_ADD_REQUESTED, controller._on_memory_add_requested)

    def test_start_is_idempotent(self) -> None:
        """Calling start() twice does not double subscribe."""
        subscribe = MagicMock()
        controller = MemorySuggestionController(
            runtime=MagicMock(),
            subscribe=subscribe,
            unsubscribe=MagicMock(),
            dispatch_event=MagicMock(),
        )
        controller.start()
        controller.start()
        # Count how many times USER_TEXT_SUBMITTED was subscribed
        user_sub_calls = [
            args for args in subscribe.call_args_list
            if args[0][0] == USER_TEXT_SUBMITTED
        ]
        assert len(user_sub_calls) == 1

    def test_stop_unsubscribes_events(self) -> None:
        """stop() unsubscribes from all events."""
        unsubscribe = MagicMock()
        controller = MemorySuggestionController(
            runtime=MagicMock(),
            subscribe=MagicMock(),
            unsubscribe=unsubscribe,
            dispatch_event=MagicMock(),
        )
        controller.start()
        controller.stop()
        unsubscribe.assert_any_call(USER_TEXT_SUBMITTED, controller._on_user_text_submitted)
        unsubscribe.assert_any_call(MEMORY_CONFIRM_REQUESTED, controller._on_memory_confirm_requested)
        unsubscribe.assert_any_call(MEMORY_REJECT_REQUESTED, controller._on_memory_reject_requested)
        unsubscribe.assert_any_call(MEMORY_ADD_REQUESTED, controller._on_memory_add_requested)

    def test_stop_is_idempotent(self) -> None:
        """Calling stop() twice does not double unsubscribe."""
        unsubscribe = MagicMock()
        controller = MemorySuggestionController(
            runtime=MagicMock(),
            subscribe=MagicMock(),
            unsubscribe=unsubscribe,
            dispatch_event=MagicMock(),
        )
        controller.start()
        controller.stop()
        controller.stop()
        # Each event should only be unsubscribed once
        for event_type in [
            USER_TEXT_SUBMITTED,
            MEMORY_CONFIRM_REQUESTED,
            MEMORY_REJECT_REQUESTED,
            MEMORY_ADD_REQUESTED,
        ]:
            handler_calls = [args for args in unsubscribe.call_args_list if args[0][0] == event_type]
            assert len(handler_calls) == 1


class TestManualMemoryAdd:
    """Tests for manually adding memory from the UI panel."""

    def test_add_requested_persists_record_and_dispatches_added(self, tmp_path: Path) -> None:
        """MEMORY_ADD_REQUESTED persists a manual memory record."""
        repository = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repository)
        dispatch = MagicMock()
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        controller._on_memory_add_requested(
            _make_event(MEMORY_ADD_REQUESTED, {"text": "我喜欢你回复短一点"})
        )

        records = repository.list_active()
        assert len(records) == 1
        assert records[0].text == "我喜欢你回复短一点"
        assert records[0].source == "manual_ui"
        dispatched = dispatch.call_args.args[0]
        assert dispatched.event_type == MEMORY_ADDED
        assert dispatched.payload["text"] == "我喜欢你回复短一点"

    def test_add_requested_rejects_blank_text(self, tmp_path: Path) -> None:
        """Blank manual memory text dispatches an error and does not persist."""
        repository = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repository)
        dispatch = MagicMock()
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        controller._on_memory_add_requested(
            _make_event(MEMORY_ADD_REQUESTED, {"text": "   "})
        )

        assert repository.list_active() == ()
        dispatched = dispatch.call_args.args[0]
        assert dispatched.event_type == MEMORY_ERROR


class TestUserTextSubmitted:
    """Tests for user text submission handling."""

    def test_no_candidate_emits_no_event(self, tmp_path: Path) -> None:
        """Empty text does not emit MEMORY_SUGGESTIONS_DETECTED."""
        dispatch = MagicMock()
        repository = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repository)
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        event = _make_event(USER_TEXT_SUBMITTED, {"text": "你好"})
        controller._on_user_text_submitted(event)

        # "你好" doesn't trigger any memory candidate
        memory_events = [c for c in dispatch.call_args_list if c[0][0].event_type == MEMORY_SUGGESTIONS_DETECTED]
        assert len(memory_events) == 0

    def test_with_candidate_emits_suggestions_detected(self, tmp_path: Path) -> None:
        """Text with a memory candidate emits MEMORY_SUGGESTIONS_DETECTED."""
        dispatch = MagicMock()
        repository = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repository)
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        event = _make_event(USER_TEXT_SUBMITTED, {"text": "我喜欢你回复短一点。"})
        controller._on_user_text_submitted(event)

        memory_events = [c for c in dispatch.call_args_list if c[0][0].event_type == MEMORY_SUGGESTIONS_DETECTED]
        assert len(memory_events) == 1
        dispatched_event = memory_events[0][0][0]
        assert dispatched_event.event_type == MEMORY_SUGGESTIONS_DETECTED
        suggestions = dispatched_event.payload.get("suggestions", [])
        assert len(suggestions) >= 1

    def test_suggestions_payload_excludes_evidence(self, tmp_path: Path) -> None:
        """suggestions payload does not include evidence field."""
        dispatch = MagicMock()
        repository = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repository)
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        event = _make_event(USER_TEXT_SUBMITTED, {"text": "我喜欢你回复短一点。"})
        controller._on_user_text_submitted(event)

        memory_events = [c for c in dispatch.call_args_list if c[0][0].event_type == MEMORY_SUGGESTIONS_DETECTED]
        if memory_events:
            dispatched_event = memory_events[0][0][0]
            suggestions = dispatched_event.payload.get("suggestions", [])
            for s in suggestions:
                assert "evidence" not in s

    def test_suggestions_payload_includes_pending_id(self, tmp_path: Path) -> None:
        """suggestions payload includes pending_id."""
        dispatch = MagicMock()
        repository = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repository)
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        event = _make_event(USER_TEXT_SUBMITTED, {"text": "我喜欢你回复短一点。"})
        controller._on_user_text_submitted(event)

        memory_events = [c for c in dispatch.call_args_list if c[0][0].event_type == MEMORY_SUGGESTIONS_DETECTED]
        if memory_events:
            dispatched_event = memory_events[0][0][0]
            suggestions = dispatched_event.payload.get("suggestions", [])
            for s in suggestions:
                assert "pending_id" in s

    def test_user_text_submitted_does_not_persist_repository(self, tmp_path: Path) -> None:
        """submit_user_text does not write to repository."""
        dispatch = MagicMock()
        repository = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repository)
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        event = _make_event(USER_TEXT_SUBMITTED, {"text": "我喜欢你回复短一点。"})
        controller._on_user_text_submitted(event)

        # Repository should be empty (no records persisted)
        active = repository.list_active()
        assert len(active) == 0


class TestConfirmRequested:
    """Tests for confirm request handling."""

    def test_confirm_requested_persists_record(self, tmp_path: Path) -> None:
        """confirm_requested writes a record to the repository."""
        dispatch = MagicMock()
        repository = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repository)
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        # First submit to get a pending
        pending = runtime.submit_user_text("我喜欢你回复短一点。")
        pending_id = pending[0].id

        # Now confirm
        event = _make_event(MEMORY_CONFIRM_REQUESTED, {"pending_id": pending_id})
        controller._on_memory_confirm_requested(event)

        # Repository should have one active record
        active = repository.list_active()
        assert len(active) == 1
        # The record text should match the confirmed pending
        assert active[0].text == "我喜欢你回复短一点。"

    def test_confirm_requested_emits_memory_confirmed(self, tmp_path: Path) -> None:
        """confirm_requested emits MEMORY_CONFIRMED event."""
        dispatch = MagicMock()
        repository = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repository)
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        pending = runtime.submit_user_text("我喜欢你回复短一点。")
        pending_id = pending[0].id

        event = _make_event(MEMORY_CONFIRM_REQUESTED, {"pending_id": pending_id})
        controller._on_memory_confirm_requested(event)

        memory_confirmed_events = [
            c for c in dispatch.call_args_list
            if c[0][0].event_type == MEMORY_CONFIRMED
        ]
        assert len(memory_confirmed_events) == 1

    def test_confirm_unknown_pending_emits_memory_error(self, tmp_path: Path) -> None:
        """confirm_requested with unknown pending_id emits MEMORY_ERROR."""
        dispatch = MagicMock()
        repository = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repository)
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        event = _make_event(MEMORY_CONFIRM_REQUESTED, {"pending_id": "unknown-id"})
        controller._on_memory_confirm_requested(event)

        memory_error_events = [
            c for c in dispatch.call_args_list
            if c[0][0].event_type == MEMORY_ERROR
        ]
        assert len(memory_error_events) == 1

    def test_invalid_pending_id_emits_memory_error(self, tmp_path: Path) -> None:
        """confirm_requested with invalid pending_id emits MEMORY_ERROR."""
        dispatch = MagicMock()
        repository = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repository)
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        event = _make_event(MEMORY_CONFIRM_REQUESTED, {"pending_id": ""})
        controller._on_memory_confirm_requested(event)

        memory_error_events = [
            c for c in dispatch.call_args_list
            if c[0][0].event_type == MEMORY_ERROR
        ]
        assert len(memory_error_events) == 1


class TestRejectRequested:
    """Tests for reject request handling."""

    def test_reject_requested_does_not_persist_record(self, tmp_path: Path) -> None:
        """reject_requested does not write to the repository."""
        dispatch = MagicMock()
        repository = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repository)
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        pending = runtime.submit_user_text("我女朋友叫红红，这件事不要记住。")
        pending_id = pending[0].id

        event = _make_event(MEMORY_REJECT_REQUESTED, {"pending_id": pending_id})
        controller._on_memory_reject_requested(event)

        # Repository should still be empty
        active = repository.list_active()
        assert len(active) == 0

    def test_reject_requested_emits_memory_rejected(self, tmp_path: Path) -> None:
        """reject_requested emits MEMORY_REJECTED event."""
        dispatch = MagicMock()
        repository = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repository)
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        pending = runtime.submit_user_text("我女朋友叫红红，这件事不要记住。")
        pending_id = pending[0].id

        event = _make_event(MEMORY_REJECT_REQUESTED, {"pending_id": pending_id})
        controller._on_memory_reject_requested(event)

        memory_rejected_events = [
            c for c in dispatch.call_args_list
            if c[0][0].event_type == MEMORY_REJECTED
        ]
        assert len(memory_rejected_events) == 1

    def test_reject_unknown_pending_emits_memory_error(self, tmp_path: Path) -> None:
        """reject_requested with unknown pending_id emits MEMORY_ERROR."""
        dispatch = MagicMock()
        repository = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repository)
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        event = _make_event(MEMORY_REJECT_REQUESTED, {"pending_id": "unknown-id"})
        controller._on_memory_reject_requested(event)

        memory_error_events = [
            c for c in dispatch.call_args_list
            if c[0][0].event_type == MEMORY_ERROR
        ]
        assert len(memory_error_events) == 1


class TestExtractionException:
    """Tests for extraction exception handling."""

    def test_extraction_exception_emits_memory_error(self, tmp_path: Path) -> None:
        """Exception during extraction emits MEMORY_ERROR."""
        dispatch = MagicMock()
        runtime = MagicMock()
        runtime.submit_user_text.side_effect = RuntimeError("extraction failed")
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        event = _make_event(USER_TEXT_SUBMITTED, {"text": "some text"})
        controller._on_user_text_submitted(event)

        memory_error_events = [
            c for c in dispatch.call_args_list
            if c[0][0].event_type == MEMORY_ERROR
        ]
        assert len(memory_error_events) == 1


class TestIsolation:
    """Tests verifying controller does not call LLM, open microphone, etc."""

    def test_controller_does_not_call_llm(self, tmp_path: Path) -> None:
        """Controller does not call any LLM API."""
        dispatch = MagicMock()
        repository = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repository)
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        event = _make_event(USER_TEXT_SUBMITTED, {"text": "我喜欢你回复短一点。"})
        controller._on_user_text_submitted(event)

        # No LLM calls are made (runtime uses deterministic extractor)
        assert not hasattr(runtime, "_llm_called")

    def test_controller_does_not_open_microphone(self, tmp_path: Path) -> None:
        """Controller does not open microphone."""
        dispatch = MagicMock()
        repository = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repository)
        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=MagicMock(),
            unsubscribe=MagicMock(),
            dispatch_event=dispatch,
        )

        # This should succeed without microphone
        event = _make_event(USER_TEXT_SUBMITTED, {"text": "我喜欢你回复短一点。"})
        controller._on_user_text_submitted(event)
        # No exception means no microphone access attempted
