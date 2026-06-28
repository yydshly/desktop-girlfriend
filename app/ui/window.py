"""Desktop window implementation."""

from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from app.core.config import get_config


class DesktopWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        config = get_config()
        self.setWindowTitle(config.app_name)
        self.setMinimumSize(config.window_width, config.window_height)

        # Central widget with label
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        label = QLabel("Desktop Girlfriend - V1 Scaffold")
        label.setStyleSheet("font-size: 16px; padding: 10px;")
        layout.addWidget(label)
