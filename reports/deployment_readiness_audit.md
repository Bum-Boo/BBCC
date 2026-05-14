# Deployment Readiness Audit

## Overall deployment readiness

Ready with fixes for source/local testing. Not ready for external packaged release until asset bundling, install metadata, and release process gaps are fixed.

## Deployment target

Windows desktop distribution via `dist/BBCC.exe` and `dist/BBCC-win64-v0.1.1.zip`.

## Build and runtime commands

| Command | Purpose | Evidence | Risk |
|---|---|---|---|
| `python -m zero2_input_inspector` | Source run | README basic usage | Works locally |
| `python -m zero2_input_inspector --background` | Tray/background start | `main.py` parser and autostart command | Needs tray/quit QA |
| `pyinstaller BBCC.spec` | Build exe | `BBCC.spec` | Currently omits app assets |
| `dist/BBCC.exe` | Packaged app | Local smoke: process stayed running | Needs clean-machine asset/UI verification |

## Environment configuration

| Variable/config | Required? | Documented? | Sensitive? | Risk |
|---|---|---|---|---|
| `%APPDATA%/zero2-input-inspector/config.json` | Runtime local settings | Partially implicit | Local metadata | Needs privacy/reset docs |
| HKCU Run registry value | Optional autostart | UI setting exists, docs sparse | Persistence control | Needs uninstall/disable docs |
| `QT_QPA_PLATFORM=offscreen` | Test-only | Tests set locally | No | Fine for tests |

## Critical deployment blockers

| ID | Blocker | Evidence | Impact | Required fix |
|---|---|---|---|---|
| None | No Critical deployment blocker confirmed | App starts locally and exe stays running | N/A | N/A |

## High deployment risks

| ID | Risk | Evidence | Impact | Recommended fix |
|---|---|---|---|---|
| DEPLOY-H01 | Release exe likely lacks app translations/diagrams/hitmaps | `BBCC.spec:8`; code loads assets from filesystem paths; archive inspection showed no app asset entries | Packaged app can lose advertised features | Add datas/package data and clean-directory exe smoke test |
| DEPLOY-H02 | Release/install process can install wrong source | `requirements.txt:9` remote editable Git dependency | Reproducibility and support risk | Replace with local install/dev requirements |

## Database and migration readiness

| Area | Status | Risk | Required action |
|---|---|---|---|
| Database | None | N/A | N/A |
| Config migrations | Present in `SettingsStore.load()` | Old config edge cases possible | Keep migration regression tests |

## Rollback readiness

| Area | Status | Gap | Required action |
|---|---|---|---|
| App binary rollback | Unknown | No documented release artifact/version rollback | Document how to revert to previous exe/zip |
| User config rollback | Weak | No backup/restore docs for config | Add config reset/backup guidance |

## Monitoring and logging readiness

| Area | Status | Gap | Required action |
|---|---|---|---|
| Runtime logs | In-memory inspector logs | No persisted crash/error report path | Add troubleshooting/export guidance if needed |
| Crash reporting | Missing | Cannot know external user failures | Decide whether to add local-only diagnostics or issue template |

## Staging checklist

| Item | Status | Required action |
|---|---|---|
| Clean-machine exe startup | Partially verified locally | Test outside source tree and verify visible text/diagrams |
| Controller hardware matrix | Partial | Test 8BitDo Zero 2 and Xbox/XInput devices |
| Autostart enable/disable | Needs manual QA | Verify registry value and disable path |
| Settings migration | Partially tested | Add old config fixtures as needed |

## Production checklist

| Item | Status | Required action |
|---|---|---|
| Version alignment | Failing | Align `pyproject`, release notes, artifact names |
| Code signing | Unknown | Decide signing strategy |
| License/privacy/support docs | Missing | Add before public release |
| CI/release automation | Missing | Add minimum checks |

## Unknowns

| Unknown | Why it matters | How to verify |
|---|---|---|
| Whether app is distributed as zip, installer, or store app | Determines deployment controls | Confirm release channel |
| Whether exe is code-signed | Affects trust and Windows warnings | Confirm signing |
| Whether assets are expected to be external beside exe | Determines packaging design | Confirm distribution layout |

## Minimum deployment work before release

Fix PyInstaller data bundling, verify the exe in a clean temp/non-repo environment with UI text and diagrams, align version metadata, and document install/uninstall/autostart behavior.
