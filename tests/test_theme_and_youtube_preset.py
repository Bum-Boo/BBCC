from __future__ import annotations

import unittest

from zero2_input_inspector.domain.profiles import (
    AppProfile,
    MAPPING_ACTION_KEYBOARD,
    MappingAssignment,
    RIGHT_STICK_MODE_WHEEL_STEP_4WAY,
    RIGHT_STICK_MODE_WHEEL_STEP_VERTICAL,
    XBOX_MEDIA_FALLBACK_LEGACY_ASSIGNMENTS,
    build_default_media_presets_for_family,
    migrate_media_fallback_profile,
)
from zero2_input_inspector.styles import theme_tokens


class ThemeAndYoutubePresetRegressionTest(unittest.TestCase):
    def test_gquuuuuux_disconnected_badge_is_readable(self) -> None:
        tokens = theme_tokens("gquuuuuux")

        self.assertNotEqual(tokens["status_disconnected_bg"], tokens["status_disconnected_text"])
        self.assertNotEqual(tokens["status_connected_bg"], tokens["status_connected_text"])
        self.assertNotEqual(tokens["status_disconnected_bg"], tokens["bg_elevated"])

    def test_xbox_youtube_defaults_match_canonical_layout(self) -> None:
        presets = build_default_media_presets_for_family("xbox")
        preset = presets[0]

        self.assertEqual(preset.assignment_for("FACE_SOUTH").action_kind, "mouse_left_click")
        self.assertEqual(preset.assignment_for("FACE_EAST").shortcut, "Alt+Left")
        self.assertEqual(preset.assignment_for("FACE_WEST").shortcut, "J")
        self.assertEqual(preset.assignment_for("FACE_NORTH").shortcut, "K")
        self.assertEqual(preset.assignment_for("L").shortcut, "Left")
        self.assertEqual(preset.assignment_for("R").shortcut, "Right")
        self.assertEqual(preset.assignment_for("LEFT_TRIGGER").shortcut, "Down")
        self.assertEqual(preset.assignment_for("RIGHT_TRIGGER").shortcut, "Up")
        self.assertEqual(preset.assignment_for("DPAD_LEFT").shortcut, "0")
        self.assertEqual(preset.assignment_for("DPAD_RIGHT").shortcut, "Shift+N")
        self.assertEqual(preset.assignment_for("DPAD_UP").shortcut, "C")
        self.assertEqual(preset.assignment_for("DPAD_DOWN").shortcut, "/")
        self.assertEqual(preset.right_stick_mode, RIGHT_STICK_MODE_WHEEL_STEP_4WAY)
        self.assertEqual(preset.assignment_for("LEFT_STICK_UP").action_kind, "mouse_move")
        self.assertEqual(preset.assignment_for("LEFT_STICK_DOWN").action_kind, "mouse_move")
        self.assertEqual(preset.assignment_for("RIGHT_STICK_LEFT").shortcut, "")
        self.assertEqual(preset.assignment_for("RIGHT_STICK_RIGHT").shortcut, "")
        self.assertEqual(preset.assignment_for("GUIDE").shortcut, "")

    def test_xbox_legacy_youtube_layout_migrates_to_new_canonical_mapping(self) -> None:
        app_profile = AppProfile(
            app_profile_id="app-1",
            name="YouTube",
            process_name="*",
            family_id="xbox",
            presets=build_default_media_presets_for_family("xbox"),
        )
        app_profile.presets[0].mappings = {
            control: MappingAssignment(
                control=assignment.control,
                shortcut=assignment.shortcut,
                label=assignment.label,
                action_kind=assignment.action_kind,
            )
            for control, assignment in XBOX_MEDIA_FALLBACK_LEGACY_ASSIGNMENTS.items()
        }

        migrated = migrate_media_fallback_profile(app_profile)
        preset = app_profile.presets[0]

        self.assertTrue(migrated)
        self.assertEqual(preset.assignment_for("FACE_NORTH").shortcut, "K")
        self.assertEqual(preset.assignment_for("FACE_WEST").shortcut, "J")
        self.assertEqual(preset.assignment_for("L").shortcut, "Left")
        self.assertEqual(preset.assignment_for("R").shortcut, "Right")
        self.assertEqual(preset.assignment_for("LEFT_TRIGGER").shortcut, "Down")
        self.assertEqual(preset.assignment_for("RIGHT_TRIGGER").shortcut, "Up")
        self.assertEqual(preset.assignment_for("DPAD_LEFT").shortcut, "0")
        self.assertEqual(preset.assignment_for("DPAD_RIGHT").shortcut, "Shift+N")
        self.assertEqual(preset.assignment_for("DPAD_UP").shortcut, "C")
        self.assertEqual(preset.assignment_for("DPAD_DOWN").shortcut, "/")
        self.assertEqual(preset.right_stick_mode, RIGHT_STICK_MODE_WHEEL_STEP_4WAY)
        self.assertNotIn("RIGHT_STICK_UP", preset.mappings)
        self.assertNotIn("RIGHT_STICK_DOWN", preset.mappings)
        self.assertNotIn("RIGHT_STICK_LEFT", preset.mappings)
        self.assertNotIn("RIGHT_STICK_RIGHT", preset.mappings)

    def test_xbox_customized_youtube_layout_is_not_overwritten(self) -> None:
        app_profile = AppProfile(
            app_profile_id="app-2",
            name="YouTube",
            process_name="*",
            family_id="xbox",
            presets=build_default_media_presets_for_family("xbox"),
        )
        app_profile.presets[0].mappings = {
            control: MappingAssignment(
                control=assignment.control,
                shortcut=assignment.shortcut,
                label=assignment.label,
                action_kind=assignment.action_kind,
            )
            for control, assignment in XBOX_MEDIA_FALLBACK_LEGACY_ASSIGNMENTS.items()
        }
        app_profile.presets[0].mappings["R"] = MappingAssignment(
            control="R",
            shortcut="P",
            label="Custom Forward",
            action_kind=MAPPING_ACTION_KEYBOARD,
        )

        migrated = migrate_media_fallback_profile(app_profile)

        self.assertFalse(migrated)
        self.assertEqual(app_profile.presets[0].assignment_for("R").shortcut, "P")
        self.assertIn("RIGHT_STICK_LEFT", app_profile.presets[0].mappings)


if __name__ == "__main__":
    unittest.main()
