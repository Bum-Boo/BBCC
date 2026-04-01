from __future__ import annotations

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPixmap


def build_app_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    body_color = QColor("#163A7A")
    accent_color = QColor("#2B63D9")
    white = QColor("#FFFFFF")

    painter.setPen(Qt.NoPen)
    painter.setBrush(body_color)
    painter.drawRoundedRect(QRectF(6, 12, 52, 40), 18, 18)

    painter.setBrush(accent_color)
    painter.drawEllipse(QRectF(14, 26, 10, 10))
    painter.drawEllipse(QRectF(40, 18, 7, 7))
    painter.drawEllipse(QRectF(47, 25, 7, 7))
    painter.drawEllipse(QRectF(33, 25, 7, 7))
    painter.drawEllipse(QRectF(40, 32, 7, 7))

    painter.setBrush(white)
    painter.drawRoundedRect(QRectF(20, 22, 12, 4), 2, 2)
    painter.drawRoundedRect(QRectF(24, 18, 4, 12), 2, 2)
    painter.drawRoundedRect(QRectF(26, 35, 12, 5), 2, 2)

    painter.end()
    return QIcon(pixmap)

