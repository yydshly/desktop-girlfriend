"""Desktop window implementation."""

from collections.abc import Callable

from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.config import get_config
from app.ui.view_model import DesktopViewModel


class DesktopWindow(QMainWindow):
    """Main application window."""

    def __init__(
        self,
        view_model: DesktopViewModel,
        on_user_text_submitted: Callable[[str], None],
    ) -> None:
        super().__init__()
        self._view_model = view_model
        self._on_user_text_submitted = on_user_text_submitted

        config = get_config()
        self.setWindowTitle(config.app_name)
        self.setMinimumSize(config.window_width, config.window_height)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # State label
        self._state_label = QLabel(self._view_model.display_text)
        self._state_label.setStyleSheet("font-size: 16px; padding: 10px;")
        layout.addWidget(self._state_label)

        # Assistant reply display
        self._assistant_label = QLabel(self._view_model.assistant_text)
        self._assistant_label.setWordWrap(True)
        self._assistant_label.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(self._assistant_label)

        # Input field
        self._input_field = QLineEdit()
        self._input_field.setPlaceholderText("输入文字后点击发送...")
        layout.addWidget(self._input_field)

        # Send button
        self._send_button = QPushButton("发送")
        self._send_button.clicked.connect(self._on_send_clicked)
        layout.addWidget(self._send_button)

    def _on_send_clicked(self) -> None:
        """Handle send button click."""
        text = self._input_field.text()
        self._on_user_text_submitted(text)
        self._input_field.clear()

    def update_from_view_model(self) -> None:
        """Update UI from view model state."""
        self._state_label.setText(self._view_model.display_text)
        self._assistant_label.setText(self._view_model.assistant_text)
