from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Optional, Tuple

from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPainterPath

from ...domain.controls import (
    DPAD_DOWN,
    DPAD_LEFT,
    DPAD_RIGHT,
    DPAD_UP,
    FACE_EAST,
    FACE_NORTH,
    FACE_SOUTH,
    FACE_WEST,
    GUIDE,
    L,
    LEFT_STICK_DOWN,
    LEFT_STICK_LEFT,
    LEFT_STICK_PRESS,
    LEFT_STICK_RIGHT,
    LEFT_STICK_UP,
    LEFT_TRIGGER,
    R,
    RIGHT_STICK_DOWN,
    RIGHT_STICK_LEFT,
    RIGHT_STICK_PRESS,
    RIGHT_STICK_RIGHT,
    RIGHT_STICK_UP,
    RIGHT_TRIGGER,
    SELECT,
    START,
)

DEFAULT_VIEWBOX = QRectF(0.0, 0.0, 1000.0, 560.0)


@dataclass(frozen=True)
class DiagramLayout:
    diagram_kind: str
    view_box: QRectF
    body_path: QPainterPath
    control_paths: Dict[str, QPainterPath]


def _rounded_rect_path(x: float, y: float, width: float, height: float, radius: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(QRectF(x, y, width, height), radius, radius)
    return path


def _ellipse_path(x: float, y: float, width: float, height: float) -> QPainterPath:
    path = QPainterPath()
    path.addEllipse(QRectF(x, y, width, height))
    return path


def _zero2_layout() -> DiagramLayout:
    body = _rounded_rect_path(140, 124, 720, 272, 136)
    controls = {
        L: _rounded_rect_path(168, 84, 168, 32, 16),
        R: _rounded_rect_path(664, 84, 168, 32, 16),
        SELECT: _rounded_rect_path(430, 344, 74, 30, 14),
        START: _rounded_rect_path(506, 344, 74, 30, 14),
        DPAD_UP: _rounded_rect_path(200, 236, 74, 34, 14),
        DPAD_LEFT: _rounded_rect_path(164, 270, 74, 34, 14),
        DPAD_DOWN: _rounded_rect_path(200, 304, 74, 34, 14),
        DPAD_RIGHT: _rounded_rect_path(236, 270, 74, 34, 14),
        FACE_NORTH: _ellipse_path(714, 234, 44, 44),
        FACE_WEST: _ellipse_path(672, 276, 44, 44),
        FACE_SOUTH: _ellipse_path(714, 318, 44, 44),
        FACE_EAST: _ellipse_path(756, 276, 44, 44),
    }
    return DiagramLayout(
        diagram_kind="zero2",
        view_box=DEFAULT_VIEWBOX,
        body_path=body,
        control_paths=controls,
    )


def _xbox_layout() -> DiagramLayout:
    body = _rounded_rect_path(132, 122, 736, 304, 152)
    controls = {
        L: _rounded_rect_path(160, 84, 170, 32, 16),
        R: _rounded_rect_path(670, 84, 170, 32, 16),
        LEFT_TRIGGER: _rounded_rect_path(150, 48, 170, 24, 12),
        RIGHT_TRIGGER: _rounded_rect_path(680, 48, 170, 24, 12),
        SELECT: _rounded_rect_path(426, 208, 56, 24, 12),
        START: _rounded_rect_path(518, 208, 56, 24, 12),
        GUIDE: _ellipse_path(466, 158, 68, 68),
        LEFT_STICK_PRESS: _ellipse_path(268, 284, 36, 36),
        LEFT_STICK_UP: _rounded_rect_path(262, 242, 52, 26, 10),
        LEFT_STICK_LEFT: _rounded_rect_path(220, 284, 52, 26, 10),
        LEFT_STICK_DOWN: _rounded_rect_path(262, 326, 52, 26, 10),
        LEFT_STICK_RIGHT: _rounded_rect_path(304, 284, 52, 26, 10),
        RIGHT_STICK_PRESS: _ellipse_path(628, 338, 36, 36),
        RIGHT_STICK_UP: _rounded_rect_path(620, 296, 52, 26, 10),
        RIGHT_STICK_LEFT: _rounded_rect_path(578, 338, 52, 26, 10),
        RIGHT_STICK_DOWN: _rounded_rect_path(620, 380, 52, 26, 10),
        RIGHT_STICK_RIGHT: _rounded_rect_path(662, 338, 52, 26, 10),
        DPAD_UP: _rounded_rect_path(182, 304, 72, 34, 14),
        DPAD_LEFT: _rounded_rect_path(146, 340, 72, 34, 14),
        DPAD_DOWN: _rounded_rect_path(182, 376, 72, 34, 14),
        DPAD_RIGHT: _rounded_rect_path(218, 340, 72, 34, 14),
        FACE_NORTH: _ellipse_path(738, 282, 44, 44),
        FACE_WEST: _ellipse_path(694, 326, 44, 44),
        FACE_SOUTH: _ellipse_path(738, 370, 44, 44),
        FACE_EAST: _ellipse_path(782, 326, 44, 44),
    }
    return DiagramLayout(
        diagram_kind="xbox",
        view_box=DEFAULT_VIEWBOX,
        body_path=body,
        control_paths=controls,
    )


@lru_cache(maxsize=None)
def load_diagram_layout(diagram_kind: str) -> Optional[DiagramLayout]:
    normalized_kind = (diagram_kind or "").strip().lower()
    if normalized_kind == "zero2":
        return _zero2_layout()
    if normalized_kind == "xbox":
        return _xbox_layout()
    return None
