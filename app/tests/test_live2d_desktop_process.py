"""Tests for managing the Live2D desktop window process."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from app.ui.live2d_desktop_process import Live2DDesktopProcess


class FakeProcess:
    def __init__(self, wait_raises: bool = False) -> None:
        self.terminated = False
        self.killed = False
        self.wait_raises = wait_raises

    def poll(self):
        return None if not (self.terminated or self.killed) else 0

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout=None):
        if self.wait_raises and not self.killed:
            raise subprocess.TimeoutExpired("fake", timeout)
        return 0


def test_command_launches_live2d_desktop_module() -> None:
    """Launch command uses the current Python executable and module entrypoint."""
    process = Live2DDesktopProcess(python_executable="python.exe")

    assert process.command == ["python.exe", "-m", "app.live2d_desktop"]


def test_command_includes_live2d_desktop_controls() -> None:
    """Launch command carries desktop companion scale and opacity controls."""
    process = Live2DDesktopProcess(
        python_executable="python.exe",
        scale=0.82,
        opacity=0.74,
    )

    assert process.command == [
        "python.exe",
        "-m",
        "app.live2d_desktop",
        "--scale",
        "0.82",
        "--opacity",
        "0.74",
    ]


def test_command_includes_selected_live2d_model_id() -> None:
    """Launch command carries the selected Live2D model id."""
    process = Live2DDesktopProcess(
        python_executable="python.exe",
        model_id="custom/Xiaoyun",
    )

    assert process.command == [
        "python.exe",
        "-m",
        "app.live2d_desktop",
        "--model-id",
        "custom/Xiaoyun",
    ]


def test_start_uses_popen_factory_with_workspace_cwd() -> None:
    """Process start delegates to Popen with a stable workspace cwd."""
    calls = []
    fake = FakeProcess()

    def popen_factory(*args, **kwargs):
        calls.append((args, kwargs))
        return fake

    process = Live2DDesktopProcess(
        python_executable="python.exe",
        cwd=Path("D:/project"),
        popen_factory=popen_factory,
    )

    process.start()

    assert process.running is True
    assert calls[0][0][0] == ["python.exe", "-m", "app.live2d_desktop"]
    assert calls[0][1]["cwd"] == "D:\\project" or calls[0][1]["cwd"] == "D:/project"


def test_start_logs_command_and_controls(caplog) -> None:
    """Process start log includes launch controls for later diagnosis."""
    caplog.set_level(logging.INFO)
    fake = FakeProcess()
    fake.pid = 1234

    process = Live2DDesktopProcess(
        python_executable="python.exe",
        cwd=Path("D:/project"),
        scale=1.2,
        opacity=0.8,
        popen_factory=lambda *args, **kwargs: fake,
    )

    process.start()

    assert "Starting Live2D desktop process" in caplog.text
    assert "scale=1.2" in caplog.text
    assert "opacity=0.8" in caplog.text
    assert "pid=1234" in caplog.text


def test_start_is_idempotent_while_process_is_running() -> None:
    """Repeated start calls do not launch duplicate Live2D windows."""
    calls = []

    def popen_factory(*args, **kwargs):
        calls.append((args, kwargs))
        return FakeProcess()

    process = Live2DDesktopProcess(popen_factory=popen_factory)

    process.start()
    process.start()

    assert len(calls) == 1


def test_stop_terminates_running_process() -> None:
    """Stop terminates the managed process."""
    fake = FakeProcess()
    process = Live2DDesktopProcess(popen_factory=lambda *args, **kwargs: fake)

    process.start()
    process.stop()

    assert fake.terminated is True
    assert process.running is False


def test_stop_logs_process_shutdown(caplog) -> None:
    """Process stop log records the managed process shutdown."""
    caplog.set_level(logging.INFO)
    fake = FakeProcess()
    fake.pid = 4321
    process = Live2DDesktopProcess(popen_factory=lambda *args, **kwargs: fake)

    process.start()
    process.stop()

    assert "Stopping Live2D desktop process" in caplog.text
    assert "pid=4321" in caplog.text
    assert "Live2D desktop process stopped" in caplog.text


def test_stop_kills_process_when_terminate_times_out() -> None:
    """Stop escalates to kill if the process ignores terminate."""
    fake = FakeProcess(wait_raises=True)
    process = Live2DDesktopProcess(popen_factory=lambda *args, **kwargs: fake)

    process.start()
    process.stop()

    assert fake.terminated is True
    assert fake.killed is True
