"""Desktop window implementation."""

from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from app.core.config import get_config
from app.ui.view_model import DesktopViewModel


class DesktopWindow(QMainWindow):
    """Main application window."""

    def __init__(self, view_model: DesktopViewModel) -> None:
        super().__init__()
        self._view_model = view_model

        config = get_config()
        self.setWindowTitle(config.app_name)
        self.setMinimumSize(config.window_width, config.window_height)

        # Central widget with label
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self._state_label = QLabel(self._view_model.display_text)
        self._state_label.setStyleSheet("font-size: 16px; padding: 10px;")
        layout.addWidget(self._state_label)

    def update_from_view_model(self) -> None:
        """Update UI from view model state."""
        self._state_label.setText(self._view_model.display_text)
