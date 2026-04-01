from __future__ import annotations

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QFrame, QLabel, QVBoxLayout


class ToastWidget(QFrame):
    def __init__(self) -> None:
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setObjectName("ToastCard")
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self._label = QLabel(self)
        self._label.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.addWidget(self._label)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, message: str) -> None:
        self._label.setText(message)
        self.adjustSize()
        screen = QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            self.move(available.right() - self.width() - 24, available.top() + 24)
        self.show()
        self.raise_()
        self._timer.start(1800)

