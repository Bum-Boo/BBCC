# Project Summary

## One-line summary

BBCC is a Windows-first tray-resident Python/PyQt controller mapping app that maps controller input to keyboard, mouse, media, and profile-specific actions.

## Project type

Desktop utility application for Windows.

## Apparent target users

Creative workflow users, desktop navigation users, and media-control users who want controller-driven shortcuts without keeping the main window open.

## Technology stack

| Layer | Detected technology | Evidence |
|---|---|---|
| Runtime | Python 3.8+ | `pyproject.toml:10` |
| GUI | PyQt5 | `pyproject.toml:12`, `src/zero2_input_inspector/main.py:5` |
| Controller backend | pygame / SDL2 joystick | `pyproject.toml:13`, `src/zero2_input_inspector/backend/pygame_backend.py` |
| System integration | pywin32, psutil, winreg, pynput, ctypes user32 | `pyproject.toml:14-16`, `src/zero2_input_inspector/services/autostart.py:7`, `src/zero2_input_inspector/services/keyboard_output.py:3-11` |
| Storage | Local JSON in `%APPDATA%/zero2-input-inspector/config.json` | `src/zero2_input_inspector/services/settings_store.py:34-36`, `src/zero2_input_inspector/services/settings_store.py:308-309` |
| Packaging | PyInstaller single-file exe | `BBCC.spec`, `dist/BBCC.exe` |
| Tests | pytest/unittest-style tests | `tests/*.py`; command result: `41 passed` |

## Repository structure

| Path | Purpose | Notes |
|---|---|---|
| `src/zero2_input_inspector/` | Main application package | Service, backend, GUI, domain modules |
| `src/zero2_input_inspector/gui/` | PyQt main window, dialogs, widgets | Main user-facing surface |
| `src/zero2_input_inspector/services/` | Settings, mapping, shortcuts, autostart, translations, assets | High-risk local OS integration lives here |
| `src/zero2_input_inspector/backend/` | pygame joystick backend | Polls SDL/pygame controller state |
| `assets/` | Translation JSON and controller SVG diagrams | Required at runtime for UI text and diagrams |
| `config/hitmaps/` | Controller diagram hit maps | Required for clickable diagrams |
| `tests/` | Regression tests | Covers mappings, normalization, GUI selection, pygame hardening |
| `dist/` | Built exe/zip artifacts | Existing local release artifacts |
| `build/` | PyInstaller build output | Contains `warn-BBCC.txt` and build internals |

## Main entry points

| File/path | Role | Evidence |
|---|---|---|
| `run_bbcc.py` | Script wrapper for the packaged app | Imports `zero2_input_inspector.main:main` |
| `src/zero2_input_inspector/__main__.py` | `python -m zero2_input_inspector` entry | Calls `main()` |
| `src/zero2_input_inspector/main.py` | CLI and QApplication startup | Defines `--background` and starts `ControllerMapperApplication` |
| `src/zero2_input_inspector/application.py` | Assembles backend, service, window, tray | Creates `MapperService`, `MainWindow`, `QSystemTrayIcon` |

## Core user flows

| Flow | Evidence | Unknowns |
|---|---|---|
| Detect connected controller | `PygameJoystickBackend.start()` and `_refresh_connected_joysticks()` | Full coverage across controller models is unknown |
| Select remembered/offline device | `MainWindow._on_device_selected()` and `MapperService.select_device()` | Long-term config migration behavior with many old configs is unknown |
| Edit mappings | `MainWindow._on_save_mapping()` and `MapperService.update_mapping()` | No full manual QA matrix exists |
| Switch app profile by foreground process | `ForegroundAppMonitor.current_process_name()` and `MapperService._resolve_active_app_profile()` | Behavior under elevated apps/UAC is unknown |
| Emit keyboard/mouse/media output | `KeyboardShortcutSender` uses pynput and `user32.keybd_event` | OS-level edge cases and permission failures are unknown |
| Autostart in tray | `WindowsAutoStartService` writes HKCU Run key | Installer/uninstaller behavior is unknown |

## Data and storage

| Data type | Storage location | Sensitivity | Evidence |
|---|---|---|---|
| Device IDs, names, GUIDs, shape signatures | `%APPDATA%/zero2-input-inspector/config.json` | Local device metadata | `settings_store.py:34-36`, `settings_store.py:308-309` |
| App profile process names | Same config file | May reveal user app/workflow habits | `domain/profiles.py`, `settings_store.py` |
| Shortcut/mouse mappings | Same config file | Can trigger powerful local actions | `settings_store.py`, `mapper_service.py` |
| Runtime logs | In-memory deque, max 500 | Low to medium; can include device/app state | `mapper_service.py:155`, `mapper_service.py:426`, `mapper_service.py:1650` |

## External integrations

| Integration | Purpose | Risk | Evidence |
|---|---|---|---|
| Windows foreground window APIs | App-profile switching | Incorrect process detection or privacy concerns | `app_monitor.py` |
| Windows registry HKCU Run | Autostart | Persistence behavior must be transparent and removable | `autostart.py:11-38` |
| Global keyboard/mouse APIs | User-selected shortcut output | Accidental destructive shortcut execution | `keyboard_output.py:55-120` |
| pygame/SDL2 | Controller input | Device compatibility and polling performance | `pygame_backend.py` |

## Build/test/deploy commands

| Command | Purpose | Evidence | Notes |
|---|---|---|---|
| `python -m zero2_input_inspector` | Run app from source | README basic usage lines 42-53 | Works in current environment |
| `python -m zero2_input_inspector --help` | CLI smoke | Command returned usage | Pass |
| `python -m pytest -q` | Test suite | Command result: `41 passed` | `pytest` is not declared in project dependencies |
| `pyinstaller BBCC.spec` | Implied exe build | `BBCC.spec` and `dist/BBCC.exe` | Asset bundling gap found |

## Immediate audit concerns

| Concern | Why it matters | Suggested next audit |
|---|---|---|
| Packaged exe appears to omit app assets | Advertised translation/diagram features may fail outside the repo | Deployment and testing |
| `requirements.txt` installs the project from remote Git | Local installs can silently use stale/different code | Supply chain |
| `check_mapping.py` is broken against current snapshot API | Developer diagnostic workflow is unreliable | Testing and quality |
| No CI workflow, release checklist, license, privacy/terms, or support runbook | Public release readiness is incomplete | Operations/legal |

## Unknowns

| Unknown | Why it matters | How to verify |
|---|---|---|
| Intended distribution channel | Determines installer, code-signing, update, license, support requirements | Confirm release plan |
| License status of the app and dependencies | Needed before public release/commercial use | Add LICENSE and dependency license inventory |
| Hardware QA matrix | Controller behavior depends on devices and drivers | Run scripted/manual QA on supported controllers |
| Code signing / Windows reputation plan | Unsigned exe may trigger SmartScreen/user trust issues | Define signing/release process |
