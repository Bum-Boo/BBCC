from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_xbox_media_fallback_load_path import _legacy_xbox_payload


class CheckMappingScriptTest(unittest.TestCase):
    def test_check_mapping_script_runs_against_current_snapshot_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "zero2-input-inspector"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.json").write_text(
                json.dumps(_legacy_xbox_payload()),
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["APPDATA"] = temp_dir
            env["QT_QPA_PLATFORM"] = "offscreen"

            result = subprocess.run(
                [sys.executable, "check_mapping.py"],
                cwd=Path(__file__).resolve().parents[1],
                env=env,
                text=True,
                capture_output=True,
                timeout=15,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[YouTube PROFILE FOUND]", result.stdout)
        self.assertIn("FACE_SOUTH", result.stdout)
