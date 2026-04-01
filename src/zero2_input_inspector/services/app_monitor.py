from __future__ import annotations

import time

import psutil
import win32gui
import win32process


class ForegroundAppMonitor:
    def __init__(self, cache_seconds: float = 0.35) -> None:
        self._cache_seconds = cache_seconds
        self._last_read_at = 0.0
        self._last_process_name = ""

    def current_process_name(self) -> str:
        now = time.monotonic()
        if now - self._last_read_at < self._cache_seconds:
            return self._last_process_name

        process_name = ""
        try:
            window_handle = win32gui.GetForegroundWindow()
            if window_handle:
                _, process_id = win32process.GetWindowThreadProcessId(window_handle)
                if process_id:
                    process_name = psutil.Process(process_id).name().lower()
        except Exception:
            process_name = ""

        self._last_read_at = now
        self._last_process_name = process_name
        return process_name

