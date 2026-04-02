from __future__ import annotations

import unittest

from zero2_input_inspector.backend.models import ControllerInfo, RawControllerState
from zero2_input_inspector.domain.profiles import build_default_device_profile
from zero2_input_inspector.services.device_registry import DeviceRegistry
from zero2_input_inspector.services.device_templates import XBOX_VISIBLE_CONTROLS
from zero2_input_inspector.services.normalization import InputNormalizer


def _make_xbox_info(*, is_standard_controller: bool = False) -> ControllerInfo:
    return ControllerInfo(
        device_id="xbox-1",
        instance_id=1,
        name="Xbox Series X Controller",
        guid="",
        is_standard_controller=is_standard_controller,
        standard_mapping=(),
        power_level="unknown",
        axes_count=6,
        buttons_count=11,
        hats_count=1,
    )


class XboxFallbackRegressionTest(unittest.TestCase):
    def test_xbox_fallback_stays_usable_when_unverified(self) -> None:
        registry = DeviceRegistry()
        normalizer = InputNormalizer(device_registry=registry)

        saved_device = build_default_device_profile(
            "xbox-1",
            "Xbox Series X Controller",
            family_id="xbox",
        )
        info = _make_xbox_info(is_standard_controller=False)
        raw_state = RawControllerState(
            info=info,
            axes=(0.0,) * 6,
            buttons=(False,) * 11,
            hats=((0, 0),),
        )

        resolved = registry.resolve_runtime(info, saved_device)
        normalized = normalizer.normalize(raw_state, saved_device)

        self.assertEqual(resolved.template.family_id, "xbox")
        self.assertFalse(resolved.template.has_exact_diagram)
        self.assertEqual(resolved.source, "saved_family_fallback")

        self.assertEqual(normalized.device_family_id, "xbox")
        self.assertEqual(normalized.diagram_kind, "xbox")
        self.assertFalse(normalized.has_exact_diagram)
        self.assertTrue(normalized.has_canonical_mapping)
        self.assertEqual(normalized.visible_controls, XBOX_VISIBLE_CONTROLS)

        # This is the core regression guard: the fallback path must remain usable,
        # not collapse into the "no trusted button map" dead-end.
        self.assertTrue(normalized.visible_controls)
        self.assertIn("FACE_SOUTH", normalized.control_labels)
        self.assertIn("SELECT", normalized.visible_controls)


if __name__ == "__main__":
    unittest.main()
