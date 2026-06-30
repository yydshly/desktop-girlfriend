"""Process lifecycle helper for the Live2D desktop companion window."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from subprocess import Popen


class Live2DDesktopProcess:
    """Launch and stop the separate Live2D desktop window process."""

    def __init__(
        self,
        *,
        python_executable: str | None = None,
        cwd: Path | None = None,
        popen_factory: Callable[..., Popen] = subprocess.Popen,
    ) -> None:
        self.python_executable = python_executable or sys.executable
        self.cwd = cwd or Path(__file__).resolve().parents[2]
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
        self._process = self._popen_factory(
            self.command,
            cwd=str(self.cwd),
            creationflags=_creation_flags(),
        )

    def stop(self) -> None:
        """Terminate the Live2D desktop process if this helper started it."""

        process = self._process
        if process is None:
            return
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        self._process = None

    @property
    def command(self) -> Sequence[str]:
        """Return the command used to launch the Live2D desktop window."""

        return [self.python_executable, "-m", "app.live2d_desktop"]


def _creation_flags() -> int:
    if sys.platform != "win32":
        return 0
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)
