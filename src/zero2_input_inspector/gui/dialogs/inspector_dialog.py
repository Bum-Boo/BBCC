from __future__ import annotations

from typing import Iterable, Optional, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...domain.state import UiSnapshot
from ...services.mapper_service import MapperService


class InspectorDialog(QDialog):
    def __init__(self, service: MapperService, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._service = service
        self._snapshot: Optional[UiSnapshot] = None
        self._current_language = ""

        self.setWindowTitle(self._service.tr("inspector"))
        self.setModal(False)
        self.resize(980, 720)

        self._build_ui()
        self._retranslate()

    def apply_snapshot(self, snapshot: UiSnapshot) -> None:
        self._snapshot = snapshot
        if snapshot.selected_language != self._current_language:
            self.retranslate_ui(snapshot.selected_language)
        self._device_name_value.setText(
            snapshot.selected_device_profile.display_name if snapshot.selected_device_profile else "-"
        )
        self._backend_value.setText(snapshot.backend_name)

        if snapshot.normalized_state is None:
            self._family_value.setText("-")
            self._resolution_value.setText("-")
            self._mapping_origin_value.setText("-")
            self._trace_value.setText("-")
            self._layout_value.setText("-")
            self._deadzone_value.setText("-")
            self._threshold_value.setText("-")
        else:
            self._family_value.setText(snapshot.normalized_state.device_family_id)
            self._resolution_value.setText(snapshot.normalized_state.resolution_source)
            self._mapping_origin_value.setText(snapshot.normalized_state.mapping_origin or "-")
            self._trace_value.setText(" -> ".join(snapshot.normalized_state.resolution_trace))
            self._layout_value.setText(snapshot.normalized_state.layout_name)
            self._deadzone_value.setText("{value:.2f}".format(value=snapshot.normalized_state.deadzone))
            self._threshold_value.setText("{value:.2f}".format(value=snapshot.normalized_state.threshold))

        if snapshot.raw_state is None:
            self._power_value.setText("-")
            self._instance_value.setText("-")
            self._guid_value.setText("-")
            self._populate_table(self._axes_table, ())
            self._populate_table(self._buttons_table, ())
            self._populate_table(self._hats_table, ())
        else:
            self._power_value.setText(snapshot.raw_state.info.power_level)
            self._instance_value.setText(str(snapshot.raw_state.info.instance_id))
            self._guid_value.setText(snapshot.raw_state.info.guid or "-")
            self._populate_table(
                self._axes_table,
                (
                    ("Axis {index}".format(index=index), "{value:+0.3f}".format(value=value))
                    for index, value in enumerate(snapshot.raw_state.axes)
                ),
            )
            self._populate_table(
                self._buttons_table,
                (
                    (
                        "Button {index}".format(index=index),
                        self._service.tr("button_down") if value else self._service.tr("button_up"),
                    )
                    for index, value in enumerate(snapshot.raw_state.buttons)
                ),
            )
            self._populate_table(
                self._hats_table,
                (("Hat {index}".format(index=index), str(value)) for index, value in enumerate(snapshot.raw_state.hats)),
            )

        self._log_view.setPlainText("\n".join(snapshot.logs))
        scrollbar = self._log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = QFrame(self)
        header.setObjectName("DialogCard")
        header_layout = QGridLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 16)
        header_layout.setHorizontalSpacing(12)
        header_layout.setVerticalSpacing(10)

        self._device_name_label = QLabel(header)
        self._device_name_value = QLabel("-", header)
        self._backend_label = QLabel(header)
        self._backend_value = QLabel("-", header)
        self._family_label = QLabel(header)
        self._family_value = QLabel("-", header)
        self._resolution_label = QLabel(header)
        self._resolution_value = QLabel("-", header)
        self._mapping_origin_label = QLabel(header)
        self._mapping_origin_value = QLabel("-", header)
        self._layout_label = QLabel(header)
        self._layout_value = QLabel("-", header)
        self._power_label = QLabel(header)
        self._power_value = QLabel("-", header)
        self._instance_label = QLabel(header)
        self._instance_value = QLabel("-", header)
        self._guid_label = QLabel(header)
        self._guid_value = QLabel("-", header)
        self._guid_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._deadzone_label = QLabel(header)
        self._deadzone_value = QLabel("-", header)
        self._threshold_label = QLabel(header)
        self._threshold_value = QLabel("-", header)
        self._trace_label = QLabel(header)
        self._trace_value = QLabel("-", header)
        self._trace_value.setWordWrap(True)

        header_layout.addWidget(self._device_name_label, 0, 0)
        header_layout.addWidget(self._device_name_value, 0, 1)
        header_layout.addWidget(self._backend_label, 0, 2)
        header_layout.addWidget(self._backend_value, 0, 3)
        header_layout.addWidget(self._family_label, 1, 0)
        header_layout.addWidget(self._family_value, 1, 1)
        header_layout.addWidget(self._resolution_label, 1, 2)
        header_layout.addWidget(self._resolution_value, 1, 3)
        header_layout.addWidget(self._mapping_origin_label, 2, 0)
        header_layout.addWidget(self._mapping_origin_value, 2, 1)
        header_layout.addWidget(self._layout_label, 2, 2)
        header_layout.addWidget(self._layout_value, 2, 3)
        header_layout.addWidget(self._power_label, 3, 0)
        header_layout.addWidget(self._power_value, 3, 1)
        header_layout.addWidget(self._instance_label, 3, 2)
        header_layout.addWidget(self._instance_value, 3, 3)
        header_layout.addWidget(self._deadzone_label, 4, 0)
        header_layout.addWidget(self._deadzone_value, 4, 1)
        header_layout.addWidget(self._threshold_label, 4, 2)
        header_layout.addWidget(self._threshold_value, 4, 3)
        header_layout.addWidget(self._guid_label, 5, 0)
        header_layout.addWidget(self._guid_value, 5, 1, 1, 3)
        header_layout.addWidget(self._trace_label, 6, 0)
        header_layout.addWidget(self._trace_value, 6, 1, 1, 3)
        root.addWidget(header)

        self._tabs = QTabWidget(self)
        self._raw_tab = QWidget(self._tabs)
        raw_layout = QVBoxLayout(self._raw_tab)
        raw_layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Horizontal, self._raw_tab)
        self._axes_table = self._build_two_column_table()
        self._buttons_table = self._build_two_column_table()
        self._hats_table = self._build_two_column_table()
        splitter.addWidget(self._wrap_table(self._axes_table))
        splitter.addWidget(self._wrap_table(self._buttons_table))
        splitter.addWidget(self._wrap_table(self._hats_table))
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([300, 300, 260])
        raw_layout.addWidget(splitter)

        self._log_tab = QWidget(self._tabs)
        log_layout = QVBoxLayout(self._log_tab)
        log_layout.setContentsMargins(0, 0, 0, 0)
        self._log_view = QPlainTextEdit(self._log_tab)
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumBlockCount(500)
        log_layout.addWidget(self._log_view)

        self._tabs.addTab(self._raw_tab, "")
        self._tabs.addTab(self._log_tab, "")
        root.addWidget(self._tabs, 1)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self._close_button = QPushButton(self)
        self._close_button.clicked.connect(self.hide)
        footer.addWidget(self._close_button)
        root.addLayout(footer)

    def _retranslate(self) -> None:
        self.setWindowTitle(self._service.tr("inspector"))
        self._device_name_label.setText("{label}:".format(label=self._service.tr("controller")))
        self._backend_label.setText("{label}:".format(label=self._service.tr("backend")))
        self._family_label.setText("{label}:".format(label=self._service.tr("family")))
        self._resolution_label.setText("{label}:".format(label=self._service.tr("resolution")))
        self._mapping_origin_label.setText("{label}:".format(label=self._service.tr("mapping_origin")))
        self._layout_label.setText("{label}:".format(label=self._service.tr("layout")))
        self._power_label.setText("{label}:".format(label=self._service.tr("power")))
        self._instance_label.setText("{label}:".format(label=self._service.tr("instance")))
        self._guid_label.setText("{label}:".format(label=self._service.tr("guid")))
        self._deadzone_label.setText("{label}:".format(label=self._service.tr("deadzone")))
        self._threshold_label.setText("{label}:".format(label=self._service.tr("threshold")))
        self._trace_label.setText("{label}:".format(label=self._service.tr("resolution_trace")))
        self._tabs.setTabText(0, self._service.tr("raw_input"))
        self._tabs.setTabText(1, self._service.tr("log"))
        self._axes_table.setHorizontalHeaderLabels([self._service.tr("button"), self._service.tr("raw_axes")])
        self._buttons_table.setHorizontalHeaderLabels([self._service.tr("button"), self._service.tr("raw_buttons")])
        self._hats_table.setHorizontalHeaderLabels([self._service.tr("button"), self._service.tr("raw_hats")])
        self._close_button.setText(self._service.tr("close"))

    def retranslate_ui(self, language: str) -> None:
        self._current_language = language
        self._retranslate()

    def _build_two_column_table(self) -> QTableWidget:
        table = QTableWidget(0, 2, self)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setStretchLastSection(True)
        return table

    def _wrap_table(self, table: QTableWidget) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("PanelSurface")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(table)
        return frame

    def _populate_table(self, table: QTableWidget, rows: Iterable[Tuple[str, str]]) -> None:
        row_list = list(rows)
        table.setRowCount(len(row_list))
        for row_index, (name, value) in enumerate(row_list):
            self._set_table_item(table, row_index, 0, name)
            self._set_table_item(table, row_index, 1, value)

    def _set_table_item(self, table: QTableWidget, row: int, column: int, text: str) -> None:
        item = table.item(row, column)
        if item is None:
            item = QTableWidgetItem()
            table.setItem(row, column, item)
        item.setText(text)
