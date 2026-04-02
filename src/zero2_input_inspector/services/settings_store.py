from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from ..domain.controls import canonicalize_control_id
from ..domain.profiles import (
    AppConfig,
    AppProfile,
    DeviceProfile,
    MappingAssignment,
    Preset,
    PresetSwitchBinding,
    Settings,
    build_default_device_profile,
    build_default_presets_for_process,
    default_selected_app_profile_id,
    is_media_fallback_name,
    is_media_fallback_profile,
    migrate_media_fallback_profile,
    normalize_mapping_action_kind,
    normalize_right_stick_mode,
)
from ..identity import DEFAULT_FALLBACK_PROFILE_NAME
from .shortcuts import normalize_shortcut_text
from ..styles import normalize_theme_id
from .translations import normalize_language_code


class SettingsStore:
    def __init__(self) -> None:
        app_data_root = Path(os.getenv("APPDATA", str(Path.home())))
        self._config_dir = app_data_root / "zero2-input-inspector"
        self._config_path = self._config_dir / "config.json"
        self._last_load_report: Dict[str, Any] = {}

    @property
    def config_path(self) -> Path:
        return self._config_path

    @property
    def last_load_report(self) -> Dict[str, Any]:
        return dict(self._last_load_report)

    def load(self) -> AppConfig:
        if not self._config_path.exists():
            self._last_load_report = {
                "source": "defaults",
                "migrated": False,
                "legacy_xbox_recognized": False,
                "rebuilt_from_canonical_defaults": False,
            }
            return AppConfig()

        try:
            payload = json.loads(self._config_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self._last_load_report = {
                "source": "defaults",
                "migrated": False,
                "legacy_xbox_recognized": False,
                "rebuilt_from_canonical_defaults": False,
            }
            return AppConfig()

        settings_payload = payload.get("settings", {})
        raw_language = str(settings_payload.get("language", "en"))
        normalized_language = normalize_language_code(raw_language)
        migrated = normalized_language != raw_language
        raw_theme = str(settings_payload.get("theme", "") or "")
        normalized_theme = normalize_theme_id(raw_theme)
        migrated = migrated or normalized_theme != raw_theme
        rebuilt_from_canonical_defaults = False
        settings = Settings(
            language=normalized_language,
            theme=normalized_theme,
            auto_start=bool(settings_payload.get("auto_start", False)),
        )

        devices: List[DeviceProfile] = []
        for device_payload in payload.get("devices", []):
            family_id = str(device_payload.get("family_override_id", "") or "").strip().lower() or str(
                device_payload.get("saved_family_id", "") or ""
            ).strip().lower()
            app_profiles: List[AppProfile] = []
            for app_payload in device_payload.get("app_profiles", []):
                app_migration_needed = any(
                    key not in app_payload
                    for key in (
                        "family_id",
                        "mouse_sensitivity",
                        "scroll_sensitivity",
                        "analog_deadzone",
                        "scroll_deadzone",
                        "scroll_activation_threshold",
                        "analog_curve",
                        "slow_speed_multiplier",
                        "fast_speed_multiplier",
                        "slow_modifier_control",
                        "fast_modifier_control",
                    )
                )
                app_family_id = str(app_payload.get("family_id", family_id) or family_id).strip().lower() or family_id
                mouse_sensitivity = _read_float(app_payload, "mouse_sensitivity", 1.0)
                scroll_sensitivity = _read_float(app_payload, "scroll_sensitivity", 1.0)
                analog_deadzone = _read_float(app_payload, "analog_deadzone", 0.16)
                scroll_deadzone = _read_float(app_payload, "scroll_deadzone", 0.32)
                scroll_activation_threshold = _read_float(app_payload, "scroll_activation_threshold", 0.6)
                analog_curve = _read_float(app_payload, "analog_curve", 1.7)
                slow_speed_multiplier = _read_float(app_payload, "slow_speed_multiplier", 0.45)
                fast_speed_multiplier = _read_float(app_payload, "fast_speed_multiplier", 1.75)
                presets: List[Preset] = []
                for preset_payload in app_payload.get("presets", []):
                    mappings = {}
                    for control, mapping_payload in preset_payload.get("mappings", {}).items():
                        canonical_control = canonicalize_control_id(str(control))
                        raw_shortcut = str(mapping_payload.get("shortcut", "") or "")
                        shortcut = normalize_shortcut_text(raw_shortcut)
                        migrated = migrated or shortcut != raw_shortcut
                        raw_action_kind = str(mapping_payload.get("action_kind", "keyboard") or "keyboard")
                        action_kind = normalize_mapping_action_kind(raw_action_kind)
                        migrated = migrated or action_kind != raw_action_kind
                        mappings[canonical_control] = MappingAssignment(
                            control=canonical_control,
                            shortcut=shortcut,
                            label=str(mapping_payload.get("label", "")),
                            action_kind=action_kind,
                        )
                    presets.append(
                        Preset(
                            preset_id=str(preset_payload.get("preset_id", "")),
                            name=str(preset_payload.get("name", "Preset")),
                            mappings=mappings,
                            right_stick_mode=normalize_right_stick_mode(preset_payload.get("right_stick_mode", "")),
                        )
                    )
                if not presets:
                    presets = build_default_presets_for_process(
                        str(app_payload.get("process_name", "*")),
                        app_family_id or family_id,
                    )
                    rebuilt_from_canonical_defaults = True
                raw_process_name = str(app_payload.get("process_name", "*") or "*")
                raw_name = str(app_payload.get("name", "") or "")
                normalized_name = self._normalize_app_profile_name(
                    raw_name,
                    raw_process_name,
                )
                normalized_process_name = self._normalize_app_profile_process_name(
                    raw_process_name,
                    normalized_name,
                )
                migrated = migrated or normalized_name != raw_name
                migrated = migrated or normalized_process_name != raw_process_name
                migrated = migrated or app_migration_needed
                app_profile = AppProfile(
                    app_profile_id=str(app_payload.get("app_profile_id", "")),
                    name=normalized_name,
                    process_name=normalized_process_name,
                    family_id=app_family_id,
                    presets=presets,
                    active_preset_index=int(app_payload.get("active_preset_index", 0)),
                    mouse_sensitivity=mouse_sensitivity,
                    scroll_sensitivity=scroll_sensitivity,
                    analog_deadzone=analog_deadzone,
                    scroll_deadzone=scroll_deadzone,
                    scroll_activation_threshold=scroll_activation_threshold,
                    analog_curve=analog_curve,
                    slow_speed_multiplier=slow_speed_multiplier,
                    fast_speed_multiplier=fast_speed_multiplier,
                    slow_modifier_control=str(app_payload.get("slow_modifier_control", "") or ""),
                    fast_modifier_control=str(app_payload.get("fast_modifier_control", "") or ""),
                )
                legacy_xbox_recognized = False
                if migrate_media_fallback_profile(app_profile):
                    migrated = True
                    legacy_xbox_recognized = (
                        app_profile.family_id.strip().lower() == "xbox"
                        and app_profile.process_name.strip() == "*"
                    )
                if is_media_fallback_profile(app_profile) or not self._last_load_report:
                    self._last_load_report = {
                        "source": "saved_config",
                        "migrated": migrated,
                        "legacy_xbox_recognized": legacy_xbox_recognized,
                        "rebuilt_from_canonical_defaults": rebuilt_from_canonical_defaults,
                    }
                app_profiles.append(app_profile)
            device_id = str(device_payload.get("device_id", "") or "")
            display_name = str(device_payload.get("display_name", "Controller") or "Controller")
            if not app_profiles:
                migrated = True
                devices.append(build_default_device_profile(device_id, display_name, family_id=family_id))
                continue
            selected_app_profile_id = str(device_payload.get("selected_app_profile_id", ""))
            if not any(profile.app_profile_id == selected_app_profile_id for profile in app_profiles):
                selected_app_profile_id = default_selected_app_profile_id(app_profiles, family_id)
                migrated = True
            devices.append(
                DeviceProfile(
                    device_id=device_id,
                    display_name=display_name,
                    guid=str(device_payload.get("guid", "") or ""),
                    last_seen_name=str(device_payload.get("last_seen_name", display_name) or display_name),
                    saved_family_id=str(device_payload.get("saved_family_id", "") or ""),
                    family_override_id=str(device_payload.get("family_override_id", "") or ""),
                    shape_signature=str(device_payload.get("shape_signature", "") or ""),
                    app_profiles=app_profiles,
                    selected_app_profile_id=str(selected_app_profile_id or ""),
                    preset_switch=PresetSwitchBinding(
                        previous_control=canonicalize_control_id(
                            str(device_payload.get("preset_switch", {}).get("previous_control", "SELECT"))
                        ),
                        next_control=canonicalize_control_id(
                            str(device_payload.get("preset_switch", {}).get("next_control", "START"))
                        ),
                    ),
                )
            )

        config = AppConfig(
            version=int(payload.get("version", 1)),
            settings=settings,
            devices=devices,
            selected_device_id=str(payload.get("selected_device_id", "")),
        )
        if migrated:
            self.save(config)
        if not self._last_load_report:
            self._last_load_report = {
                "source": "saved_config",
                "migrated": migrated,
                "legacy_xbox_recognized": False,
                "rebuilt_from_canonical_defaults": rebuilt_from_canonical_defaults,
            }
        return config

    def save(self, config: AppConfig) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)
        config.settings.language = normalize_language_code(config.settings.language)
        config.settings.theme = normalize_theme_id(config.settings.theme)
        payload: Dict[str, Any] = {
            "version": config.version,
            "selected_device_id": config.selected_device_id,
            "settings": {
                "language": config.settings.language,
                "theme": config.settings.theme,
                "auto_start": config.settings.auto_start,
            },
            "devices": [],
        }

        for device in config.devices:
            device_payload = {
                "device_id": device.device_id,
                "display_name": device.display_name,
                "guid": device.guid,
                "last_seen_name": device.last_seen_name,
                "saved_family_id": device.saved_family_id,
                "family_override_id": device.family_override_id,
                "shape_signature": device.shape_signature,
                "selected_app_profile_id": device.selected_app_profile_id,
                "preset_switch": {
                    "previous_control": device.preset_switch.previous_control,
                    "next_control": device.preset_switch.next_control,
                },
                "app_profiles": [],
            }
            for app_profile in device.app_profiles:
                app_payload = {
                    "app_profile_id": app_profile.app_profile_id,
                    "name": app_profile.name,
                    "process_name": app_profile.process_name,
                    "family_id": app_profile.family_id,
                    "active_preset_index": app_profile.active_preset_index,
                    "mouse_sensitivity": app_profile.mouse_sensitivity,
                    "scroll_sensitivity": app_profile.scroll_sensitivity,
                    "analog_deadzone": app_profile.analog_deadzone,
                    "scroll_deadzone": app_profile.scroll_deadzone,
                    "scroll_activation_threshold": app_profile.scroll_activation_threshold,
                    "analog_curve": app_profile.analog_curve,
                    "slow_speed_multiplier": app_profile.slow_speed_multiplier,
                    "fast_speed_multiplier": app_profile.fast_speed_multiplier,
                    "slow_modifier_control": app_profile.slow_modifier_control,
                    "fast_modifier_control": app_profile.fast_modifier_control,
                    "presets": [],
                }
                for preset in app_profile.presets:
                    preset_payload = {
                        "preset_id": preset.preset_id,
                        "name": preset.name,
                        "right_stick_mode": normalize_right_stick_mode(preset.right_stick_mode),
                        "mappings": {
                            control: {
                                "shortcut": normalize_shortcut_text(mapping.shortcut),
                                "label": mapping.label,
                                "action_kind": normalize_mapping_action_kind(mapping.action_kind),
                            }
                            for control, mapping in preset.mappings.items()
                        },
                    }
                    app_payload["presets"].append(preset_payload)
                device_payload["app_profiles"].append(app_payload)
            payload["devices"].append(device_payload)

        self._config_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def _normalize_app_profile_name(name: str, process_name: str) -> str:
        if process_name.strip() == "*":
            normalized = name.strip()
            if not normalized:
                return DEFAULT_FALLBACK_PROFILE_NAME
            if normalized.lower() in {"global", "global (*)"}:
                return DEFAULT_FALLBACK_PROFILE_NAME
            return normalized
        normalized = name.strip()
        return normalized if normalized else "New App"

    @staticmethod
    def _normalize_app_profile_process_name(process_name: str, profile_name: str) -> str:
        normalized = str(process_name or "").strip().lower()
        if not normalized:
            return "*" if is_media_fallback_name(profile_name) else "*"
        if is_media_fallback_name(profile_name) and normalized in {
            DEFAULT_FALLBACK_PROFILE_NAME.casefold(),
            "global",
            "global (*)",
        }:
            return "*"
        return normalized


def _read_float(payload: Dict[str, Any], key: str, default: float) -> float:
    raw_value = payload.get(key, default)
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return float(default)
