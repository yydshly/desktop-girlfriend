"""Tests for application shutdown wiring."""

from app.main import _wire_shutdown


class FakeSignal:
    """Minimal signal test double."""

    def __init__(self) -> None:
        self._callback = None

    def connect(self, callback) -> None:
        self._callback = callback

    def emit(self) -> None:
        assert self._callback is not None
        self._callback()


class FakeApp:
    """Minimal app test double with an aboutToQuit signal."""

    def __init__(self) -> None:
        self.aboutToQuit = FakeSignal()


class FakeComponent:
    """Component test double that records stop calls."""

    def __init__(self) -> None:
        self.stop_called = False

    def stop(self) -> None:
        self.stop_called = True


def test_wire_shutdown_stops_components_on_app_quit() -> None:
    """Test shutdown wiring stops all registered components."""
    app = FakeApp()
    first = FakeComponent()
    second = FakeComponent()

    _wire_shutdown(app, first, second)
    app.aboutToQuit.emit()

    assert first.stop_called is True
    assert second.stop_called is True
