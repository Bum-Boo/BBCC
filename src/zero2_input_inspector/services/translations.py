from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, Tuple

AVAILABLE_LANGUAGES: Tuple[Tuple[str, str], ...] = (
    ("English", "en"),
    ("Korean", "ko"),
    ("Japanese", "ja"),
    ("Chinese", "zh"),
)

AVAILABLE_LANGUAGE_CODES = {code for _, code in AVAILABLE_LANGUAGES}

_LANGUAGE_CODE_ALIASES: Dict[str, str] = {
    "en": "en",
    "english": "en",
    "ko": "ko",
    "kr": "ko",
    "ko-kr": "ko",
    "korean": "ko",
    "ja": "ja",
    "jp": "ja",
    "ja-jp": "ja",
    "japanese": "ja",
    "zh": "zh",
    "cn": "zh",
    "zh-cn": "zh",
    "zh-hans": "zh",
    "chinese": "zh",
}

_TRANSLATION_KEY_ALIASES: Dict[str, str] = {
    "app_title": "app.title",
    "devices": "app.devices",
    "remembered_devices": "app.remembered_devices",
    "connected": "state.connected",
    "disconnected": "state.disconnected",
    "empty_title": "empty.title",
    "empty_body": "empty.body",
    "app_profile": "toolbar.app_profile",
    "current_profile": "toolbar.current_profile",
    "active_preset": "toolbar.active_preset",
    "profile_name": "app.profile_name",
    "process_name": "app.process_name",
    "current_app": "app.current_app",
    "preset": "preset.title",
    "preset_name": "preset.name",
    "previous": "preset.previous",
    "next": "preset.next",
    "add": "preset.add",
    "delete": "preset.delete",
    "add_app": "toolbar.add_app",
    "delete_app": "toolbar.delete_app",
    "show_devices": "toolbar.show_devices",
    "hide_devices": "toolbar.hide_devices",
    "profile_settings": "toolbar.profile_settings",
    "preset_manager": "toolbar.preset_manager",
    "inspector": "inspector.title",
    "settings": "settings.title",
    "controller": "app.controller",
    "button_mappings": "mapping.title",
    "mapping_editor": "mapping.editor",
    "selected_button": "mapping.selected_button",
    "shortcut": "mapping.shortcut",
    "mapping_type": "mapping.type",
    "mapping_value": "mapping.value",
    "mapping_type_shortcut": "mapping.type_shortcut",
    "mapping_type_special": "mapping.type_special",
    "mapping_type_mouse": "mapping.type_mouse",
    "label": "mapping.label",
    "save": "settings.save",
    "cancel": "mapping.cancel",
    "reset": "mapping.reset",
    "clear": "mapping.clear",
    "close": "settings.close",
    "button": "mapping.button",
    "assigned_action": "mapping.assigned_action",
    "mapping_hint": "mapping.hint",
    "system_prev": "mapping.system_prev",
    "system_next": "mapping.system_next",
    "system_action": "mapping.system_action",
    "system_mapping_note": "mapping.system_mapping_note",
    "no_selection": "mapping.no_selection",
    "no_device": "app.no_device",
    "zero2_exact": "diagram.zero2_exact",
    "xbox_exact": "diagram.xbox_exact",
    "generic_layout": "diagram.generic_layout",
    "unknown_layout_supported": "diagram.unknown_layout_supported",
    "unknown_layout_unavailable": "diagram.unknown_layout_unavailable",
    "unknown_diagram_title": "diagram.unknown_diagram_title",
    "unknown_diagram_body": "diagram.unknown_diagram_body",
    "unmapped_diagram_title": "diagram.unmapped_diagram_title",
    "unmapped_diagram_body": "diagram.unmapped_diagram_body",
    "toolbar_hint": "toolbar.hint",
    "language": "settings.language",
    "theme": "settings.theme",
    "auto_start": "settings.auto_start",
    "reset_presets": "settings.reset_presets",
    "settings_hint": "settings.hint",
    "inspector_hint": "inspector.hint",
    "raw_input": "inspector.raw_input",
    "backend_details": "inspector.backend_details",
    "backend": "inspector.backend",
    "family": "inspector.family",
    "resolution": "inspector.resolution",
    "resolution_trace": "inspector.resolution_trace",
    "mapping_origin": "inspector.mapping_origin",
    "layout": "inspector.layout",
    "power": "inspector.power",
    "instance": "inspector.instance",
    "guid": "inspector.guid",
    "deadzone": "inspector.deadzone",
    "threshold": "inspector.threshold",
    "raw_axes": "inspector.raw_axes",
    "raw_buttons": "inspector.raw_buttons",
    "raw_hats": "inspector.raw_hats",
    "log": "inspector.log",
    "button_down": "state.button_down",
    "button_up": "state.button_up",
    "toast_preset": "state.toast_preset",
    "toast_reset": "state.toast_reset",
    "app_removed": "state.app_removed",
    "preset_deleted": "preset.deleted",
    "process_wildcard_hint": "app.process_wildcard_hint",
    "unsupported_diagram": "diagram.unsupported_diagram",
}


def _translation_root_candidates() -> Tuple[Path, ...]:
    service_root = Path(__file__).resolve().parents[3]
    package_root = Path(__file__).resolve().parents[1]
    return (
        service_root / "assets" / "translations",
        package_root / "assets" / "translations",
    )


def normalize_language_code(language: str, fallback: str = "en") -> str:
    normalized = str(language or "").strip().lower()
    if not normalized:
        return fallback
    resolved = _LANGUAGE_CODE_ALIASES.get(normalized, normalized)
    if resolved in AVAILABLE_LANGUAGE_CODES:
        return resolved
    return fallback


def _translation_file_path(language: str) -> Path:
    filename = "{language}.json".format(language=language)
    for root in _translation_root_candidates():
        candidate = root / filename
        if candidate.exists():
            return candidate
    return _translation_root_candidates()[0] / filename


def _flatten_translation_tree(node, prefix: str = "") -> Dict[str, str]:
    flattened: Dict[str, str] = {}
    if isinstance(node, dict):
        for key, value in node.items():
            full_key = "{prefix}.{key}".format(prefix=prefix, key=key) if prefix else key
            if isinstance(value, dict):
                flattened.update(_flatten_translation_tree(value, full_key))
            else:
                flattened[full_key] = str(value)
    return flattened


@lru_cache(maxsize=None)
def _load_language_map(language: str) -> Dict[str, str]:
    language_code = normalize_language_code(language)
    path = _translation_file_path(language_code)
    if not path.exists() and language_code != "en":
        path = _translation_file_path("en")
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return _flatten_translation_tree(payload)


def translate(language: str, key: str, **kwargs: str) -> str:
    language_code = normalize_language_code(language)
    lookup_key = _TRANSLATION_KEY_ALIASES.get(key, key)
    language_map = _load_language_map(language_code)
    english_map = _load_language_map("en")
    template = language_map.get(lookup_key) or english_map.get(lookup_key) or key
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return template
    return template
