from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from zero2_input_inspector.services import diagram_assets, translations


class RuntimeResourcePathTest(unittest.TestCase):
    def tearDown(self) -> None:
        if hasattr(sys, "_MEIPASS"):
            delattr(sys, "_MEIPASS")
        translations._load_language_map.cache_clear()

    def test_translations_prefer_pyinstaller_meipass_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            translation_dir = Path(temp_dir) / "assets" / "translations"
            translation_dir.mkdir(parents=True)
            (translation_dir / "en.json").write_text(
                json.dumps({"app": {"title": "Frozen BBCC"}}),
                encoding="utf-8",
            )
            setattr(sys, "_MEIPASS", temp_dir)
            translations._load_language_map.cache_clear()

            self.assertEqual(translations.translate("en", "app.title"), "Frozen BBCC")

    def test_diagram_asset_candidates_include_pyinstaller_meipass_first(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            setattr(sys, "_MEIPASS", temp_dir)

            candidates = list(diagram_assets._candidate_files("assets", "diagrams", "xbox.svg"))

        self.assertGreaterEqual(len(candidates), 1)
        self.assertEqual(candidates[0], Path(temp_dir) / "assets" / "diagrams" / "xbox.svg")
