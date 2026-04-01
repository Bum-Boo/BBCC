from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import winreg


class WindowsAutoStartService:
    RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    VALUE_NAME = "zero2-input-inspector"

    def is_enabled(self) -> bool:
        return bool(self.current_command())

    def current_command(self) -> Optional[str]:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.RUN_KEY) as run_key:
                value, _ = winreg.QueryValueEx(run_key, self.VALUE_NAME)
                return str(value)
        except OSError:
            return None

    def set_enabled(self, enabled: bool) -> None:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            self.RUN_KEY,
            0,
            winreg.KEY_SET_VALUE,
        ) as run_key:
            if enabled:
                winreg.SetValueEx(
                    run_key,
                    self.VALUE_NAME,
                    0,
                    winreg.REG_SZ,
                    self._build_command(),
                )
            else:
                try:
                    winreg.DeleteValue(run_key, self.VALUE_NAME)
                except FileNotFoundError:
                    pass

    def _build_command(self) -> str:
        executable = Path(sys.executable)
        if executable.name.lower() == "python.exe":
            pythonw = executable.with_name("pythonw.exe")
            if pythonw.exists():
                executable = pythonw
        return '"{executable}" -m zero2_input_inspector --background'.format(
            executable=executable,
        )

