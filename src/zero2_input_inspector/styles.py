from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from PyQt5.QtWidgets import QApplication


@dataclass(frozen=True)
class ThemeDefinition:
    label: str
    tokens: Dict[str, str]


DEFAULT_THEME_ID = "default_light"

THEME_DEFINITIONS: Dict[str, ThemeDefinition] = {
    "default_light": ThemeDefinition(
        label="Default Light",
        tokens={
            "bg_default": "#F7F8FA",
            "bg_panel": "#EFF1F4",
            "bg_elevated": "#FFFFFF",
            "text_primary": "#18212D",
            "text_secondary": "#5F6C7A",
            "text_strong": "#2B3442",
            "border_subtle": "#D7DDE6",
            "border_strong": "#B7C0CC",
            "primary": "#5E7086",
            "primary_hover": "#526378",
            "primary_active": "#465565",
            "primary_deep": "#2C3B4E",
            "selection_bg": "#E8EDF3",
            "hover_tint": "#F4F6F8",
            "focus_ring": "#5E7086",
            "danger": "#C85A5A",
            "danger_soft": "#F8EAEA",
            "warning": "#C6A24A",
            "warning_soft": "#F6EFD9",
            "accent_red": "#C85A5A",
            "accent_amber": "#C6A24A",
            "accent_neon": "#5E7086",
            "frame_surface": "#ECEFF3",
            "frame_border": "#B7C0CC",
            "frame_text": "#2C3B4E",
            "frame_muted": "#5F6C7A",
            "table_alt": "#FAFBFC",
            "status_connected_bg": "#C85A5A",
            "status_connected_text": "#FFFFFF",
            "status_connected_border": "#C85A5A",
            "status_disconnected_bg": "#F6EFD9",
            "status_disconnected_text": "#2C3B4E",
            "status_disconnected_border": "#C6A24A",
        },
    ),
    "gquuuuuux": ThemeDefinition(
        label="GQuuuuuuX",
        tokens={
            "bg_default": "#DCEAF6",
            "bg_panel": "#C7D8EA",
            "bg_elevated": "#F3F8FD",
            "text_primary": "#132238",
            "text_secondary": "#42566F",
            "text_strong": "#0E1A2B",
            "border_subtle": "#A9BED6",
            "border_strong": "#5E7EA5",
            "primary": "#3C6FA7",
            "primary_hover": "#315F90",
            "primary_active": "#284E79",
            "primary_deep": "#1E3553",
            "selection_bg": "#D4E6F7",
            "hover_tint": "#E6F1FB",
            "focus_ring": "#39FF66",
            "danger": "#B1263A",
            "danger_soft": "#F4D9DE",
            "warning": "#D88A1E",
            "warning_soft": "#F9E5C8",
            "accent_red": "#B1263A",
            "accent_amber": "#D88A1E",
            "accent_neon": "#39FF66",
            "frame_surface": "#1E3553",
            "frame_border": "#5E7EA5",
            "frame_text": "#F3F8FD",
            "frame_muted": "#D5E3F1",
            "table_alt": "#EAF2FA",
            "status_connected_bg": "#B1263A",
            "status_connected_text": "#FFFFFF",
            "status_connected_border": "#B1263A",
            "status_disconnected_bg": "#F9E5C8",
            "status_disconnected_text": "#1E3553",
            "status_disconnected_border": "#D88A1E",
        },
    ),
    "midnight_dark": ThemeDefinition(
        label="Midnight Dark",
        tokens={
            "bg_default": "#0F1724",
            "bg_panel": "#152033",
            "bg_elevated": "#1B2738",
            "text_primary": "#E7EEF8",
            "text_secondary": "#B5C0D2",
            "text_strong": "#F2F6FB",
            "border_subtle": "#2B3A52",
            "border_strong": "#40567A",
            "primary": "#4C8BFF",
            "primary_hover": "#3F7DF0",
            "primary_active": "#316BD9",
            "primary_deep": "#CFE0FF",
            "selection_bg": "#243652",
            "hover_tint": "#1E2A40",
            "focus_ring": "#4C8BFF",
            "danger": "#F16B6B",
            "danger_soft": "#402022",
            "warning": "#F0C95E",
            "warning_soft": "#40351A",
            "accent_red": "#F16B6B",
            "accent_amber": "#F0C95E",
            "accent_neon": "#4C8BFF",
            "frame_surface": "#111C2D",
            "frame_border": "#40567A",
            "frame_text": "#F2F6FB",
            "frame_muted": "#B5C0D2",
            "table_alt": "#182335",
            "status_connected_bg": "#F16B6B",
            "status_connected_text": "#FFFFFF",
            "status_connected_border": "#F16B6B",
            "status_disconnected_bg": "#40351A",
            "status_disconnected_text": "#F2F6FB",
            "status_disconnected_border": "#F0C95E",
        },
    ),
    "graphite_neutral": ThemeDefinition(
        label="Graphite Neutral",
        tokens={
            "bg_default": "#F4F6F8",
            "bg_panel": "#E9EDF2",
            "bg_elevated": "#FFFFFF",
            "text_primary": "#18212B",
            "text_secondary": "#596678",
            "text_strong": "#2F3945",
            "border_subtle": "#CAD2DC",
            "border_strong": "#A9B4C3",
            "primary": "#4E6C90",
            "primary_hover": "#42607F",
            "primary_active": "#36516B",
            "primary_deep": "#223443",
            "selection_bg": "#DDE7F2",
            "hover_tint": "#F0F4F8",
            "focus_ring": "#4E6C90",
            "danger": "#C85D5D",
            "danger_soft": "#F7E7E7",
            "warning": "#C4A04C",
            "warning_soft": "#F4EDDA",
            "accent_red": "#C85D5D",
            "accent_amber": "#C4A04C",
            "accent_neon": "#4E6C90",
            "frame_surface": "#DEE5ED",
            "frame_border": "#A9B4C3",
            "frame_text": "#223443",
            "frame_muted": "#596678",
            "table_alt": "#F7F9FC",
            "status_connected_bg": "#C85D5D",
            "status_connected_text": "#FFFFFF",
            "status_connected_border": "#C85D5D",
            "status_disconnected_bg": "#F4EDDA",
            "status_disconnected_text": "#223443",
            "status_disconnected_border": "#C4A04C",
        },
    ),
    "forest_tech": ThemeDefinition(
        label="Forest Tech",
        tokens={
            "bg_default": "#F1F7F4",
            "bg_panel": "#E3EEE8",
            "bg_elevated": "#FFFFFF",
            "text_primary": "#12211B",
            "text_secondary": "#52655E",
            "text_strong": "#2D3A35",
            "border_subtle": "#C4D4CB",
            "border_strong": "#95B1A5",
            "primary": "#2B7A6A",
            "primary_hover": "#25695C",
            "primary_active": "#1F594D",
            "primary_deep": "#16453C",
            "selection_bg": "#D6ECE4",
            "hover_tint": "#EEF7F3",
            "focus_ring": "#2B7A6A",
            "danger": "#C95757",
            "danger_soft": "#F4E5E5",
            "warning": "#C0A44A",
            "warning_soft": "#F3EED8",
            "accent_red": "#C95757",
            "accent_amber": "#C0A44A",
            "accent_neon": "#2B7A6A",
            "frame_surface": "#D8E7DF",
            "frame_border": "#95B1A5",
            "frame_text": "#16453C",
            "frame_muted": "#52655E",
            "table_alt": "#F4FBF7",
            "status_connected_bg": "#C95757",
            "status_connected_text": "#FFFFFF",
            "status_connected_border": "#C95757",
            "status_disconnected_bg": "#F3EED8",
            "status_disconnected_text": "#16453C",
            "status_disconnected_border": "#C0A44A",
        },
    ),
}

AVAILABLE_THEMES: Tuple[Tuple[str, str], ...] = tuple(
    (definition.label, theme_id) for theme_id, definition in THEME_DEFINITIONS.items()
)
AVAILABLE_THEME_IDS = {theme_id for theme_id in THEME_DEFINITIONS}

DEFAULT_FONT_FAMILY_STACK = (
    '"Noto Sans", "Noto Sans KR", "Noto Sans JP", "Noto Sans SC", '
    '"Segoe UI", "Malgun Gothic", "Arial", sans-serif'
)
DEFAULT_FONT_SIZE_PT = 10.5


def normalize_theme_id(theme_id: str, fallback: str = DEFAULT_THEME_ID) -> str:
    normalized = str(theme_id or "").strip().lower().replace(" ", "_")
    if not normalized:
        return fallback
    alias_map = {
        "default": DEFAULT_THEME_ID,
        "default_light": DEFAULT_THEME_ID,
        "light": DEFAULT_THEME_ID,
        "gquuuuuux": "gquuuuuux",
        "gqux": "gquuuuuux",
        "midnight": "midnight_dark",
        "midnight_dark": "midnight_dark",
        "dark": "midnight_dark",
        "graphite": "graphite_neutral",
        "graphite_neutral": "graphite_neutral",
        "neutral": "graphite_neutral",
        "forest": "forest_tech",
        "forest_tech": "forest_tech",
        "green": "forest_tech",
    }
    resolved = alias_map.get(normalized, normalized)
    if resolved in AVAILABLE_THEME_IDS:
        return resolved
    return fallback


def theme_label(theme_id: str) -> str:
    return THEME_DEFINITIONS[normalize_theme_id(theme_id)].label


def theme_tokens(theme_id: str) -> Dict[str, str]:
    return THEME_DEFINITIONS[normalize_theme_id(theme_id)].tokens


def current_theme_id() -> str:
    app = QApplication.instance()
    if app is not None:
        theme_id = app.property("theme_id")
        if theme_id:
            return normalize_theme_id(str(theme_id))
    return DEFAULT_THEME_ID


def current_theme_tokens() -> Dict[str, str]:
    return theme_tokens(current_theme_id())


def build_stylesheet(
    theme_id: str = DEFAULT_THEME_ID,
    font_family_stack: str = DEFAULT_FONT_FAMILY_STACK,
    base_font_size_pt: float = DEFAULT_FONT_SIZE_PT,
) -> str:
    tokens = theme_tokens(theme_id)
    return """
QWidget {{
    background: {bg_default};
    color: {text_primary};
    font-family: {font_family_stack};
    font-size: {base_font_size_pt}pt;
}}
QMainWindow,
QDialog {{
    background: {bg_default};
}}
QFrame#PanelCard,
QFrame#DialogCard,
QFrame#ToastCard {{
    background: {bg_panel};
    border: 1px solid {border_subtle};
    border-radius: 16px;
}}
QFrame#ToolbarCard,
QFrame#WorkspaceHeaderCard {{
    background: {frame_surface};
    border: 1px solid {frame_border};
    border-radius: 15px;
}}
QFrame#EmptyStateCard {{
    background: {bg_elevated};
    border: 1px solid {border_strong};
    border-radius: 22px;
}}
QFrame#PresetStrip {{
    background: {bg_elevated};
    border: 1px solid {accent_amber};
    border-radius: 14px;
}}
QFrame#DeviceNameChip {{
    background: {bg_elevated};
    border: 1px solid {border_strong};
    border-radius: 11px;
}}
QFrame#MappingEditorCard,
QFrame#PanelSurface,
QFrame#DeviceItemCard {{
    background: {bg_elevated};
    border: 1px solid {border_subtle};
    border-radius: 14px;
}}
QFrame#DeviceItemCard:hover {{
    background: {hover_tint};
    border-color: {primary};
}}
QFrame#DeviceItemCard[selected="true"] {{
    background: {selection_bg};
    border: 1px solid {primary_deep};
}}
QLabel#PageTitle {{
    color: {primary_deep};
    font-size: 18pt;
    font-weight: 700;
}}
QLabel#HeaderTitle {{
    color: {primary_deep};
    font-size: 13.5pt;
    font-weight: 700;
}}
QLabel#SectionTitle {{
    color: {primary_deep};
    font-size: 13pt;
    font-weight: 700;
}}
QLabel#MutedText {{
    color: {text_secondary};
}}
QLabel#StrongText {{
    color: {text_strong};
    font-weight: 600;
}}
QLabel#ToolbarHint {{
    background: transparent;
    color: {frame_muted};
}}
QLabel#ConnectedPill {{
    color: {status_connected_text};
    background: {status_connected_bg};
    border: 1px solid {status_connected_border};
    border-radius: 11px;
    padding: 2px 9px;
    font-weight: 600;
}}
QLabel#DisconnectedPill {{
    color: {status_disconnected_text};
    background: {status_disconnected_bg};
    border: 1px solid {status_disconnected_border};
    border-radius: 11px;
    padding: 2px 9px;
    font-weight: 600;
}}
QPushButton {{
    background: {bg_elevated};
    color: {text_primary};
    border: 1px solid {border_strong};
    border-radius: 10px;
    padding: 8px 12px;
    min-height: 18px;
}}
QPushButton:hover {{
    background: {hover_tint};
    border-color: {primary};
}}
QPushButton:pressed {{
    background: {selection_bg};
    border-color: {primary_active};
}}
QPushButton:focus {{
    border: 2px solid {focus_ring};
}}
QPushButton:disabled {{
    background: {bg_panel};
    color: {text_secondary};
    border-color: {border_subtle};
}}
QPushButton#PrimaryButton {{
    background: {primary};
    color: #FFFFFF;
    border-color: {primary_hover};
    font-weight: 600;
}}
QPushButton#PrimaryButton:hover {{
    background: {primary_hover};
}}
QPushButton#PrimaryButton:pressed {{
    background: {primary_active};
}}
QPushButton#DangerButton {{
    background: {danger_soft};
    color: {danger};
    border-color: {danger};
    font-weight: 600;
}}
QPushButton#DangerButton:hover {{
    background: {danger_soft};
    border-color: {danger};
}}
QFrame#ToolbarCard QPushButton,
QFrame#WorkspaceHeaderCard QPushButton {{
    background: {bg_elevated};
    color: {text_primary};
    border: 1px solid {border_strong};
}}
QFrame#ToolbarCard QPushButton:hover,
QFrame#WorkspaceHeaderCard QPushButton:hover {{
    background: {hover_tint};
    border-color: {accent_neon};
}}
QFrame#ToolbarCard QPushButton:pressed,
QFrame#WorkspaceHeaderCard QPushButton:pressed {{
    background: {selection_bg};
    border-color: {primary};
}}
QLineEdit,
QComboBox,
QPlainTextEdit,
QTableWidget,
QListWidget {{
    background: {bg_elevated};
    color: {text_primary};
    border: 1px solid {border_subtle};
    border-radius: 10px;
}}
QLineEdit,
QComboBox {{
    padding: 8px 10px;
    min-height: 20px;
}}
QLineEdit:hover,
QComboBox:hover,
QPlainTextEdit:hover,
QTableWidget:hover,
QListWidget:hover {{
    border-color: {border_strong};
}}
QLineEdit:focus,
QComboBox:focus,
QPlainTextEdit:focus,
QTableWidget:focus,
QListWidget:focus {{
    border: 2px solid {focus_ring};
}}
QComboBox::drop-down {{
    border: none;
    width: 26px;
}}
QComboBox QAbstractItemView {{
    background: {bg_elevated};
    color: {text_primary};
    selection-background-color: {selection_bg};
    selection-color: {text_primary};
    border: 1px solid {border_strong};
    outline: 0;
}}
QComboBox QAbstractItemView::item:hover {{
    background: {hover_tint};
}}
QMenu {{
    background: {bg_elevated};
    color: {text_primary};
    border: 1px solid {border_strong};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 20px 6px 22px;
    border-radius: 6px;
}}
QMenu::item:selected {{
    background: {hover_tint};
    color: {text_primary};
}}
QCheckBox {{
    color: {text_primary};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {border_strong};
    border-radius: 5px;
    background: {bg_elevated};
}}
QCheckBox::indicator:hover {{
    border-color: {primary};
}}
QCheckBox::indicator:checked {{
    background: {primary};
    border-color: {primary_hover};
}}
QTableWidget {{
    gridline-color: {border_subtle};
    selection-background-color: {selection_bg};
    selection-color: {text_primary};
    alternate-background-color: {table_alt};
}}
QTableWidget::item,
QListWidget::item {{
    padding: 4px 6px;
}}
QTableWidget::item:selected {{
    background: {selection_bg};
    color: {text_primary};
}}
QHeaderView::section {{
    background: {bg_elevated};
    color: {primary_deep};
    border: none;
    border-bottom: 2px solid {accent_amber};
    padding: 8px;
    font-weight: 600;
}}
""".format(font_family_stack=font_family_stack, base_font_size_pt=base_font_size_pt, **tokens)
