"""Tests for memory confirmation store and service."""

from app.brain.memory import DeterministicMemoryExtractor, MemoryKind
from app.brain.memory.confirmation import (
    InMemoryMemoryConfirmationStore,
    MemoryConfirmationService,
    utc_now,
)
from app.brain.memory.types import MemoryCandidate, MemoryImportance


class TestInMemoryMemoryConfirmationStore:
    """Tests for InMemoryMemoryConfirmationStore."""

    def _make_store(self) -> InMemoryMemoryConfirmationStore:
        return InMemoryMemoryConfirmationStore()

    def _make_candidate(self) -> MemoryCandidate:
        return MemoryCandidate(
            kind=MemoryKind.PREFERENCE,
            importance=MemoryImportance.MEDIUM,
            text="用户喜欢短回复。",
            evidence="用户说：我喜欢短回复。",
            confidence=0.75,
        )

    def test_add_pending_creates_pending_with_uuid_id(self) -> None:
        store = self._make_store()
        candidate = self._make_candidate()
        pending = store.add_pending(candidate)
        assert pending.id is not None
        assert len(pending.id) == 36  # UUID format
        assert pending.candidate == candidate
        assert pending.created_at.tzinfo is not None

    def test_list_pending_returns_tuple(self) -> None:
        store = self._make_store()
        candidate = self._make_candidate()
        store.add_pending(candidate)
        result = store.list_pending()
        assert isinstance(result, tuple)
        assert len(result) == 1

    def test_confirm_moves_pending_to_confirmed(self) -> None:
        store = self._make_store()
        candidate = self._make_candidate()
        pending = store.add_pending(candidate)
        confirmed = store.confirm(pending.id)
        assert confirmed.id == pending.id
        assert confirmed.candidate == pending.candidate
        assert confirmed.created_at == pending.created_at
        assert store.list_pending() == ()
        assert len(store.list_confirmed()) == 1

    def test_reject_moves_pending_to_rejected(self) -> None:
        store = self._make_store()
        candidate = self._make_candidate()
        pending = store.add_pending(candidate)
        rejected = store.reject(pending.id, reason="test_reason")
        assert rejected.id == pending.id
        assert rejected.candidate == pending.candidate
        assert rejected.created_at == pending.created_at
        assert rejected.reason == "test_reason"
        assert store.list_pending() == ()
        assert len(store.list_rejected()) == 1

    def test_confirm_unknown_id_raises_key_error(self) -> None:
        store = self._make_store()
        try:
            store.confirm("unknown-id")
            assert False, "Should have raised KeyError"
        except KeyError as e:
            assert "No pending memory" in str(e)

    def test_reject_unknown_id_raises_key_error(self) -> None:
        store = self._make_store()
        try:
            store.reject("unknown-id")
            assert False, "Should have raised KeyError"
        except KeyError as e:
            assert "No pending memory" in str(e)

    def test_confirm_same_id_twice_raises_key_error(self) -> None:
        store = self._make_store()
        candidate = self._make_candidate()
        pending = store.add_pending(candidate)
        store.confirm(pending.id)
        try:
            store.confirm(pending.id)
            assert False, "Should have raised KeyError"
        except KeyError as e:
            assert "already confirmed" in str(e)

    def test_reject_same_id_twice_raises_key_error(self) -> None:
        store = self._make_store()
        candidate = self._make_candidate()
        pending = store.add_pending(candidate)
        store.reject(pending.id)
        try:
            store.reject(pending.id)
            assert False, "Should have raised KeyError"
        except KeyError as e:
            assert "already rejected" in str(e)

    def test_confirm_after_reject_raises_key_error(self) -> None:
        store = self._make_store()
        candidate = self._make_candidate()
        pending = store.add_pending(candidate)
        store.reject(pending.id)
        try:
            store.confirm(pending.id)
            assert False, "Should have raised KeyError"
        except KeyError as e:
            assert "already rejected" in str(e)

    def test_reject_after_confirm_raises_key_error(self) -> None:
        store = self._make_store()
        candidate = self._make_candidate()
        pending = store.add_pending(candidate)
        store.confirm(pending.id)
        try:
            store.reject(pending.id)
            assert False, "Should have raised KeyError"
        except KeyError as e:
            assert "already confirmed" in str(e)

    def test_list_confirmed_returns_tuple(self) -> None:
        store = self._make_store()
        candidate = self._make_candidate()
        pending = store.add_pending(candidate)
        store.confirm(pending.id)
        result = store.list_confirmed()
        assert isinstance(result, tuple)

    def test_list_rejected_returns_tuple(self) -> None:
        store = self._make_store()
        candidate = self._make_candidate()
        pending = store.add_pending(candidate)
        store.reject(pending.id)
        result = store.list_rejected()
        assert isinstance(result, tuple)

    def test_clear_removes_all_states(self) -> None:
        store = self._make_store()
        candidate = self._make_candidate()
        p1 = store.add_pending(candidate)
        p2 = store.add_pending(candidate)
        store.confirm(p1.id)
        store.reject(p2.id)
        store.clear()
        assert store.list_pending() == ()
        assert store.list_confirmed() == ()
        assert store.list_rejected() == ()

    def test_timestamps_are_timezone_aware_utc(self) -> None:
        store = self._make_store()
        candidate = self._make_candidate()
        pending = store.add_pending(candidate)
        assert pending.created_at.tzinfo is not None
        confirmed = store.confirm(pending.id)
        assert confirmed.created_at.tzinfo is not None
        assert confirmed.confirmed_at.tzinfo is not None

    def test_rejected_reason_is_stored(self) -> None:
        store = self._make_store()
        candidate = self._make_candidate()
        pending = store.add_pending(candidate)
        rejected = store.reject(pending.id, reason="user_declined")
        assert rejected.reason == "user_declined"

    def test_boundary_candidate_can_become_pending(self) -> None:
        extractor = DeterministicMemoryExtractor()
        candidates = extractor.extract("这件事不要记住，我只是随口说说。")
        store = self._make_store()
        pending = store.add_pending(candidates[0])
        assert pending.candidate.kind == MemoryKind.BOUNDARY

    def test_get_pending_returns_pending_or_none(self) -> None:
        store = self._make_store()
        candidate = self._make_candidate()
        pending = store.add_pending(candidate)
        result = store.get_pending(pending.id)
        assert result == pending
        assert store.get_pending("nonexistent") is None


class TestMemoryConfirmationService:
    """Tests for MemoryConfirmationService."""

    def _make_service(self) -> tuple[MemoryConfirmationService, InMemoryMemoryConfirmationStore]:
        store = InMemoryMemoryConfirmationStore()
        return MemoryConfirmationService(store), store

    def _make_candidates(self) -> tuple:
        return (
            MemoryCandidate(
                kind=MemoryKind.PREFERENCE,
                importance=MemoryImportance.MEDIUM,
                text="用户喜欢短回复。",
                evidence="用户说：我喜欢短回复。",
                confidence=0.75,
            ),
            MemoryCandidate(
                kind=MemoryKind.RELATIONSHIP,
                importance=MemoryImportance.HIGH,
                text="用户提到女朋友。",
                evidence="用户说：我女朋友叫红红。",
                confidence=0.80,
            ),
        )

    def test_submit_candidates_empty_returns_empty(self) -> None:
        service, _ = self._make_service()
        result = service.submit_candidates(())
        assert result == ()

    def test_submit_candidates_creates_pending_for_all(self) -> None:
        service, store = self._make_service()
        candidates = self._make_candidates()
        result = service.submit_candidates(candidates)
        assert len(result) == 2
        assert store.list_pending() == result

    def test_submit_candidates_does_not_auto_confirm(self) -> None:
        service, _ = self._make_service()
        candidates = self._make_candidates()
        service.submit_candidates(candidates)
        assert len(service.list_pending()) == 2
        assert len(service.list_confirmed()) == 0

    def test_submit_candidates_does_not_deduplicate(self) -> None:
        service, _ = self._make_service()
        candidates = self._make_candidates() * 2  # duplicate
        result = service.submit_candidates(candidates)
        assert len(result) == 4  # all 4 submitted

    def test_service_confirm_delegates_to_store(self) -> None:
        service, store = self._make_service()
        candidates = self._make_candidates()
        pending = service.submit_candidates(candidates)
        confirmed = service.confirm(pending[0].id)
        assert len(store.list_confirmed()) == 1
        assert confirmed.id == pending[0].id

    def test_service_reject_delegates_to_store(self) -> None:
        service, store = self._make_service()
        candidates = self._make_candidates()
        pending = service.submit_candidates(candidates)
        rejected = service.reject(pending[0].id, reason="test")
        assert len(store.list_rejected()) == 1
        assert rejected.id == pending[0].id

    def test_service_list_pending_delegates(self) -> None:
        service, _ = self._make_service()
        candidates = self._make_candidates()
        service.submit_candidates(candidates)
        result = service.list_pending()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_service_list_confirmed_delegates(self) -> None:
        service, _ = self._make_service()
        candidates = self._make_candidates()
        pending = service.submit_candidates(candidates)
        service.confirm(pending[0].id)
        result = service.list_confirmed()
        assert isinstance(result, tuple)
        assert len(result) == 1

    def test_service_list_rejected_delegates(self) -> None:
        service, _ = self._make_service()
        candidates = self._make_candidates()
        pending = service.submit_candidates(candidates)
        service.reject(pending[0].id)
        result = service.list_rejected()
        assert isinstance(result, tuple)
        assert len(result) == 1

    def test_boundary_candidate_can_be_submitted(self) -> None:
        service, _ = self._make_service()
        extractor = DeterministicMemoryExtractor()
        candidates = extractor.extract("这件事不要记住。")
        result = service.submit_candidates(candidates)
        assert len(result) == 1
        assert result[0].candidate.kind == MemoryKind.BOUNDARY


class TestUctNow:
    """Tests for utc_now helper."""

    def test_utc_now_returns_timezone_aware_datetime(self) -> None:
        now = utc_now()
        assert now.tzinfo is not None

    def test_utc_now_returns_utc_timezone(self) -> None:
        now = utc_now()
        assert str(now.tzinfo) in ("UTC", "UTC+00:00")
