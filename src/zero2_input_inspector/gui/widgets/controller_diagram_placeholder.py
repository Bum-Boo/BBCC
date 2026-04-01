from __future__ import annotations

from typing import Dict, Iterable, Optional, Set, Tuple

from PyQt5.QtCore import QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QMouseEvent, QPainter, QPainterPath, QPen, QTransform
from PyQt5.QtWidgets import QApplication, QWidget

from ...styles import current_theme_tokens
from .controller_diagram_layouts import DEFAULT_VIEWBOX, DiagramLayout, load_diagram_layout


class ControllerDiagramWidget(QWidget):
    control_selected = pyqtSignal(str)

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._diagram_kind = "unknown"
        self._has_exact_diagram = False
        self._visible_controls: Tuple[str, ...] = ()
        self._control_labels: Dict[str, str] = {}
        self._active_controls: Set[str] = set()
        self._selected_control = ""
        self._live_control = ""
        self._placeholder_title = ""
        self._placeholder_body = ""
        self._diagram_layout: Optional[DiagramLayout] = None
        self._presentation_signature: Tuple[object, ...] = ()
        self.setMinimumHeight(320)

    def set_presentation(
        self,
        diagram_kind: str,
        control_labels: Dict[str, str],
        visible_controls: Iterable[str],
        has_exact_diagram: bool,
        placeholder_title: str = "",
        placeholder_body: str = "",
    ) -> None:
        visible_controls_tuple = tuple(visible_controls)
        presentation_signature = (
            diagram_kind,
            visible_controls_tuple,
            has_exact_diagram,
            placeholder_title,
            placeholder_body,
            tuple(sorted(control_labels.items())),
        )
        if presentation_signature == self._presentation_signature:
            return

        self._presentation_signature = presentation_signature
        self._diagram_kind = diagram_kind
        self._control_labels = dict(control_labels)
        self._visible_controls = visible_controls_tuple
        self._has_exact_diagram = has_exact_diagram
        self._placeholder_title = placeholder_title
        self._placeholder_body = placeholder_body
        self._diagram_layout = load_diagram_layout(diagram_kind) if has_exact_diagram else None
        self.update()

    def set_active_controls(self, controls: Set[str]) -> None:
        normalized_controls = set(controls)
        if normalized_controls == self._active_controls:
            return
        self._active_controls = normalized_controls
        self.update()

    def set_selected_control(self, control: str) -> None:
        if control == self._selected_control:
            return
        self._selected_control = control
        self.update()

    def set_live_control(self, control: str) -> None:
        if control == self._live_control:
            return
        self._live_control = control
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._diagram_layout is not None:
            for control, path in self._interactive_paths_for_rect(self.rect()).items():
                if path.contains(event.localPos()):
                    self.control_selected.emit(control)
                    event.accept()
                    return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            canvas = self._aspect_rect(self.rect().adjusted(18, 16, -18, -16), self._current_view_box())
            if canvas.width() <= 0 or canvas.height() <= 0:
                return

            if self._diagram_layout is None or not self._has_exact_diagram:
                self._paint_unknown_panel(painter, canvas)
                return

            self._paint_placeholder_diagram(painter, canvas)
        finally:
            painter.end()

    def _paint_placeholder_diagram(self, painter: QPainter, canvas: QRectF) -> None:
        layout = self._diagram_layout
        if layout is None:
            self._paint_unknown_panel(painter, canvas)
            return

        theme = current_theme_tokens()

        transform = self._build_transform(canvas, layout.view_box)

        body_path = transform.map(layout.body_path)
        painter.fillPath(body_path, QColor(theme["bg_panel"]))
        painter.setPen(QPen(QColor(theme["border_subtle"]), 1.8))
        painter.drawPath(body_path)

        for control in self._visible_controls:
            path = layout.control_paths.get(control)
            if path is None:
                continue
            mapped_path = transform.map(path)
            label = self._control_labels.get(control, control)
            fill_color, border_color, text_color = self._state_style(control)
            painter.fillPath(mapped_path, fill_color)
            painter.setPen(QPen(border_color, 1.6))
            painter.drawPath(mapped_path)
            self._paint_label(painter, mapped_path, label, text_color)

    def _paint_unknown_panel(self, painter: QPainter, canvas: QRectF) -> None:
        theme = current_theme_tokens()
        panel = self._rounded_rect_path(canvas.adjusted(6, 6, -6, -6), 22)
        painter.fillPath(panel, QColor(theme["bg_elevated"]))
        painter.setPen(QPen(QColor(theme["border_subtle"]), 2))
        painter.drawPath(panel)

        badge = self._rounded_rect_path(QRectF(canvas.center().x() - 52, canvas.top() + 48, 104, 38), 19)
        painter.fillPath(badge, QColor(theme["selection_bg"]))
        painter.setPen(QPen(QColor(theme["primary"]), 1.5))
        painter.drawPath(badge)

        title_rect = QRectF(canvas.left() + 40, canvas.center().y() - 32, canvas.width() - 80, 34)
        body_rect = QRectF(canvas.left() + 92, canvas.center().y() + 10, canvas.width() - 184, 60)

        painter.setPen(QColor(theme["primary_deep"]))
        painter.setFont(self._font(12, True))
        painter.drawText(title_rect, Qt.AlignCenter, self._placeholder_title or "No exact device diagram")

        painter.setPen(QColor(theme["text_secondary"]))
        painter.setFont(self._font(10, False))
        painter.drawText(
            body_rect,
            Qt.AlignCenter | Qt.TextWordWrap,
            self._placeholder_body or "Use the mapping list while device-specific support is added.",
        )

    def _paint_label(self, painter: QPainter, path: QPainterPath, label: str, color: QColor) -> None:
        text_rect = path.boundingRect().adjusted(4, 2, -4, -2)
        painter.setPen(color)
        painter.setFont(self._label_font_for_label(label))
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, label)

    def _state_style(self, control: str) -> Tuple[QColor, QColor, QColor]:
        theme = current_theme_tokens()
        if control in self._active_controls:
            active_fill = QColor(theme["primary"])
            active_fill.setAlpha(220)
            return active_fill, QColor(theme["primary_deep"]), QColor("#FFFFFF")
        if control == self._selected_control and control:
            selected_fill = QColor(theme["selection_bg"])
            selected_fill.setAlpha(235)
            return selected_fill, QColor(theme["primary"]), QColor(theme["primary_deep"])
        if control == self._live_control and control:
            live_fill = QColor(theme["hover_tint"])
            live_fill.setAlpha(220)
            return live_fill, QColor(theme["primary_hover"]), QColor(theme["primary_deep"])
        return QColor(theme["bg_elevated"]), QColor(theme["border_subtle"]), QColor(theme["text_primary"])

    def _label_font_for_label(self, label: str) -> QFont:
        font = self._font(self._label_font_size(label), True)
        return font

    def _label_font_size(self, label: str) -> int:
        label_length = len(label.strip())
        if label_length <= 2:
            return 10
        if label_length <= 4:
            return 8
        return 7

    def _interactive_paths_for_rect(self, widget_rect: QRectF) -> Dict[str, QPainterPath]:
        layout = self._diagram_layout
        if layout is None:
            return {}
        canvas = self._aspect_rect(widget_rect.adjusted(18, 16, -18, -16), layout.view_box)
        transform = self._build_transform(canvas, layout.view_box)
        return {
            control: transform.map(path)
            for control, path in layout.control_paths.items()
        }

    def _current_view_box(self) -> QRectF:
        if self._diagram_layout is not None:
            return self._diagram_layout.view_box
        return DEFAULT_VIEWBOX

    def _aspect_rect(self, available: QRectF, view_box: QRectF) -> QRectF:
        if available.width() <= 0 or available.height() <= 0:
            return QRectF()
        if view_box.width() <= 0 or view_box.height() <= 0:
            view_box = DEFAULT_VIEWBOX
        scale = min(available.width() / view_box.width(), available.height() / view_box.height())
        width = view_box.width() * scale
        height = view_box.height() * scale
        x = available.left() + (available.width() - width) / 2.0
        y = available.top() + (available.height() - height) / 2.0
        return QRectF(x, y, width, height)

    def _build_transform(self, canvas: QRectF, view_box: QRectF) -> QTransform:
        transform = QTransform()
        transform.translate(canvas.left(), canvas.top())
        transform.scale(canvas.width() / view_box.width(), canvas.height() / view_box.height())
        return transform

    def _rounded_rect_path(self, rect: QRectF, radius: float) -> QPainterPath:
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        return path

    def _font(self, size: int, bold: bool) -> QFont:
        app = QApplication.instance()
        font = QFont(app.font()) if app is not None else QFont()
        font.setPointSize(size)
        font.setBold(bold)
        return font
