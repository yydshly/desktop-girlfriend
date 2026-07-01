"""Process lifecycle helper for the Live2D desktop companion window."""

from __future__ import annotations

import logging
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from subprocess import Popen

logger = logging.getLogger(__name__)


class Live2DDesktopProcess:
    """Launch and stop the separate Live2D desktop window process."""

    def __init__(
        self,
        *,
        python_executable: str | None = None,
        cwd: Path | None = None,
        scale: float = 1.0,
        opacity: float = 1.0,
        model_id: str = "",
        popen_factory: Callable[..., Popen] = subprocess.Popen,
    ) -> None:
        self.python_executable = python_executable or sys.executable
        self.cwd = cwd or Path(__file__).resolve().parents[2]
        self.scale = scale
        self.opacity = opacity
        self.model_id = model_id
        self._popen_factory = popen_factory
        self._process: Popen | None = None

    @property
    def running(self) -> bool:
        """Return True when the managed Live2D desktop process is alive."""

        return self._process is not None and self._process.poll() is None

    def start(self) -> None:
        """Start the Live2D desktop process if it is not already running."""

        if self.running:
            return
        logger.info(
            "Starting Live2D desktop process scale=%s opacity=%s cwd=%s command=%s",
            _format_float(self.scale),
            _format_float(self.opacity),
            self.cwd,
            " ".join(self.command),
        )
        self._process = self._popen_factory(
            self.command,
            cwd=str(self.cwd),
            creationflags=_creation_flags(),
        )
        logger.info(
            "Live2D desktop process started pid=%s",
            getattr(self._process, "pid", "unknown"),
        )

    def stop(self) -> None:
        """Terminate the Live2D desktop process if this helper started it."""

        process = self._process
        if process is None:
            return
        process_pid = getattr(process, "pid", "unknown")
        logger.info("Stopping Live2D desktop process pid=%s", process_pid)
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                logger.warning(
                    "Live2D desktop process did not stop in time; killing pid=%s",
                    process_pid,
                )
                process.kill()
                process.wait(timeout=2)
        self._process = None
        logger.info("Live2D desktop process stopped pid=%s", process_pid)

    @property
    def command(self) -> Sequence[str]:
        """Return the command used to launch the Live2D desktop window."""

        command = [self.python_executable, "-m", "app.live2d_desktop"]
        if self.scale != 1.0:
            command.extend(["--scale", _format_float(self.scale)])
        if self.opacity != 1.0:
            command.extend(["--opacity", _format_float(self.opacity)])
        if self.model_id:
            command.extend(["--model-id", self.model_id])
        return command


def _creation_flags() -> int:
    if sys.platform != "win32":
        return 0
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _format_float(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")
