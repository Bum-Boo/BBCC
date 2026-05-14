# Post-Build Audit

## Scope

Broad post-build release-readiness audit for the current Windows desktop controller mapping project. This audit followed the `bumboo-build-inspector` master prompt in read-only audit mode. Source code was not modified.

## Files inspected

`README.md`, `RELEASE_NOTES_v0.1.0.md`, `pyproject.toml`, `requirements.txt`, `BBCC.spec`, `.gitignore`, `check_mapping.py`, `run_bbcc.py`, `src/zero2_input_inspector/**`, `tests/**`, `assets/**`, `config/**`, `build/BBCC/warn-BBCC.txt`, `dist/BBCC.exe`.

## Executive summary

The app is functional from source in the current environment: the actual Qt window starts, a connected Bluetooth controller is detected, key UI workflows passed manual/integration checks, the built exe stays running, and the automated test suite passes. The project is not yet release-ready for external users because the packaged distribution and install path have unresolved reliability/supply-chain issues: required app assets are not bundled in `BBCC.spec`, `requirements.txt` points at a remote editable Git install of the same project, and a developer diagnostic script is currently broken.

## Critical blockers

| ID | Finding | Evidence | Impact | Recommended fix | Release implication |
|---|---|---|---|---|---|
| None | No Critical blocker confirmed | No secrets, auth bypass, remote API, payment, or destructive deployment path found | N/A | N/A | N/A |

## High-risk issues

| ID | Finding | Evidence | Impact | Recommended fix | Release implication |
|---|---|---|---|---|---|
| H-01 | Packaged app likely omits required application assets | `BBCC.spec:8` has `datas=[]`; runtime lookup expects `assets/translations`, `assets/diagrams`, and `config/hitmaps` in `translations.py:140-145` and `diagram_assets.py:128-129`; PyInstaller archive inspection matched PyQt translations but no app `assets/` or `config/hitmaps/` entries | Frozen release may show translation keys, lose multilingual UI, lose controller diagrams/hitmaps, or degrade advertised features outside the source tree | Add app data files to PyInstaller `datas`, add package data to build metadata, and add an exe smoke test that verifies translations and diagrams load from a temp working directory | Not ready for external release until fixed |
| H-02 | Installation requirements can pull stale/different remote project code | `requirements.txt:9` contains `-e git+https://github.com/Bum-Boo/BBCC.git@a7f3b0...`; current venv freeze shows a different editable commit `8d912...` | Developers/testers may install code that is not the local checkout, producing false test results and supply-chain ambiguity | Replace with local editable install instructions (`pip install -e .`) and separate dev requirements; pin dev tools separately | Fix before beta/release |

## Medium-risk issues

| ID | Finding | Evidence | Impact | Recommended fix | Owner |
|---|---|---|---|---|---|
| M-01 | `check_mapping.py` is broken against the current `UiSnapshot` model | Running it raises `AttributeError: 'UiSnapshot' object has no attribute 'devices'`; code uses `snap.devices` at `check_mapping.py:15`, while `UiSnapshot` exposes `device_entries` and selected profiles in `domain/state.py:70-84` | Diagnostic tooling fails and can mislead release verification | Update script to inspect `service._config.devices` or supported snapshot fields; add a smoke test | Engineering |
| M-02 | No CI quality gate is present | No `.github` workflow files found; tests are local only | Regressions can land without automated verification | Add CI for tests, compile check, asset parsing, and packaged asset smoke | Engineering |
| M-03 | Public release metadata is inconsistent | `pyproject.toml` version is `1.0.0`; release notes are `v0.1.0`; artifact is `dist/BBCC-win64-v0.1.1.zip` | Users and maintainers cannot tell what version is current | Align version, release notes, artifact names, and changelog | Release owner |
| M-04 | Powerful local behavior lacks a documented safety boundary | App can send global keyboard/mouse/media inputs via `keyboard_output.py:55-120` and autostart via registry `autostart.py:11-38` | Accidental mappings can affect the foreground app, including destructive shortcuts | Add first-run warning/help, emergency pause/disable guidance, and documented safe defaults | Product/engineering |

## Low-risk issues

| ID | Finding | Evidence | Recommended fix |
|---|---|---|---|
| L-01 | No explicit release checklist or manual QA matrix | No release checklist file found | Add controller/device/OS/manual UI checklist |
| L-02 | Build output is committed only as local ignored artifacts | `.gitignore` ignores `build/` and `dist/`; artifacts exist locally | Decide whether releases are GitHub Releases only and document process |

## Unknowns

| Unknown | Why it matters | How to verify |
|---|---|---|
| Whether released exe is expected to run without repo files nearby | Determines severity of the packaging asset gap | Test packaged exe on a clean machine/temp directory and verify text/diagrams |
| Supported Windows versions and privilege assumptions | Global input and foreground process APIs can vary | Define support matrix |
| User support and issue-response process | Needed for real users | Add support/runbook docs |

## Recommended next action

Fix H-01 and H-02 first, then add regression coverage for packaged assets and `check_mapping.py`. After that, repeat the runtime smoke test and rebuild the exe.
