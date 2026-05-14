# Testing and Quality Audit

## Overall quality risk

Medium. The existing regression suite is useful and passes, but it does not yet cover packaged artifacts, helper scripts, CI execution, or hardware/manual QA.

## Test command inventory

| Command | Purpose | Evidence | Notes |
|---|---|---|---|
| `python -m pytest -q` | Automated test suite | Command result: `41 passed` | `pytest` not declared in project metadata |
| `python -m compileall -q src tests run_bbcc.py check_mapping.py` | Syntax/import compilation | Previously run successfully | Useful but not in CI |
| `python -m zero2_input_inspector --help` | CLI smoke | Command returned usage | Pass |
| `python check_mapping.py` | Mapping diagnostic | Fails with `AttributeError` | Needs fix |
| `dist/BBCC.exe` smoke | Packaged app starts | Process stayed running for 3 seconds | Does not verify assets/UI text |

## Existing test coverage summary

| Area | Test coverage | Evidence | Risk |
|---|---|---|---|
| Xbox media fallback migration/defaults | Good | `tests/test_xbox_media_fallback_load_path.py`, `tests/test_theme_and_youtube_preset.py` | Low |
| Analog scroll/right-stick behavior | Good | `tests/test_analog_scroll_behavior.py` | Low to medium |
| Normalization/stick vector sources | Good | `tests/test_normalization_stick_vector_sources.py` | Low |
| GUI mapping selection | Some | `tests/test_main_window_mapping_selection.py` | Medium; offscreen only |
| pygame backend hardening | Some | `tests/test_pygame_backend_hardening.py` | Medium |
| Packaged exe resources | Missing | No test found; `BBCC.spec:8` suggests gap | High |
| Real hardware flow | Manual only | Runtime check detected a controller in this audit | Medium |
| Helper scripts | Missing | `check_mapping.py` fails | Medium |

## Critical missing tests

| ID | Missing test | Why it matters | Suggested test |
|---|---|---|---|
| None | No Critical missing test identified | N/A | N/A |

## High-priority missing tests

| ID | Missing test | Why it matters | Suggested test |
|---|---|---|---|
| T-H01 | Packaged asset inclusion/resource loading | Release exe may miss translations/diagrams/hitmaps | Build/inspect PyInstaller artifact and assert app assets exist; run exe from clean temp dir and verify translated labels/diagram asset load |
| T-H02 | Requirements/install reproducibility | Current `requirements.txt` can install remote code | CI job that installs local package with dev requirements and verifies import path |

## Shallow or misleading tests

| Test file | Problem | Impact | Recommended fix |
|---|---|---|---|
| `tests/test_main_window_mapping_selection.py` | Uses dummy backend and offscreen Qt | Does not catch real tray/hardware/packaging issues | Keep it, add packaged/live smoke checks |
| `tests/*` | No CI execution visible | Passing locally does not protect branch/release | Add CI |
| `check_mapping.py` | Not tested and broken | Diagnostic script cannot support release validation | Add script smoke or remove script |

## CI quality gates

| Gate | Present? | Evidence | Required action |
|---|---|---|---|
| Unit/regression tests | Local only | No `.github` workflows found | Add CI |
| Compile/import check | Local only | Manual command | Add CI |
| Packaging check | Missing | No artifact test | Add build/archive/resource verification |
| Dependency check | Local only | `pip check` passed | Add CI |
| Lint/typecheck | Missing | No config or command found | Consider adding focused lint/typecheck if useful |

## Manual QA gaps

| Gap | Risk | Recommended checklist item |
|---|---|---|
| Supported hardware matrix | Controller-specific regressions | Test 8BitDo Zero 2 and Xbox/XInput on supported Windows versions |
| Autostart | Registry persistence/user trust | Enable, reboot/login or simulate, disable, verify registry cleanup |
| Global input safety | Accidental destructive shortcuts | Test pause/quit/reset and drift scenarios in safe apps |
| Packaged UI | Missing assets/text | Run release exe outside repo and verify language/theme/diagram screens |

## Minimum testing work before release

Fix `check_mapping.py`, add packaged asset/resource tests, add CI for current regression suite, and add a manual hardware/release QA checklist.
