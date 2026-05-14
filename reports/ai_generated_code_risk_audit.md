# AI-Generated Code Risk Audit

## Overall judgment

Medium risk. The implementation is organized and has useful regression tests, but there are classic post-build gaps: packaging assumptions are not tested, a helper script drifted from the current API, and dependency/install instructions can cause the wrong code to be tested.

## Evidence that the project may contain AI-generated code

| Evidence | File/path | Why it suggests AI-generated or unreviewed code |
|---|---|---|
| Broad feature set with limited release infrastructure | Repository-wide | Feature work is ahead of packaging/CI/legal release controls |
| Broken helper script after API change | `check_mapping.py:15` | Indicates refactor drift not caught by tests |
| Runtime assets handled by path heuristics but packaging metadata omits them | `translations.py:140-145`, `diagram_assets.py:128-129`, `BBCC.spec:8` | Common generated-code gap: source tree works, packaged app not fully verified |

## Critical AI-code risks

| ID | Risk | Evidence | Why AI-generated code often causes this | Recommended fix |
|---|---|---|---|---|
| None | No Critical AI-code risk confirmed | Current app has no auth, payments, database, or remote agent features | N/A | N/A |

## High-risk weak spots

| ID | Risk | Evidence | Impact | Recommended fix |
|---|---|---|---|---|
| AI-H01 | Source-run success can hide packaged-app failure | `BBCC.spec:8` has no data files; source code expects external assets | Release exe can miss core UX assets | Add packaging tests and asset bundling |
| AI-H02 | Requirements file can install a remote copy rather than local code | `requirements.txt:9` | Audit/test results can be detached from current source | Split runtime/dev requirements and remove remote editable self-dependency |

## Shallow or misleading tests

| Test file | Problem | Missing scenario | Recommended test |
|---|---|---|---|
| `tests/*` | Good regression coverage, but mostly service/unit level with mocks | Frozen exe resource loading, clean-machine packaged app UI text/diagram verification | Add PyInstaller archive/resource test or post-build smoke |
| `tests/*` | No test covers `check_mapping.py` | Diagnostic script compatibility | Add command smoke for helper scripts |
| `tests/test_main_window_mapping_selection.py` | Useful GUI logic tests, offscreen only | Live connected hardware behavior and end-user flow | Keep a manual hardware QA checklist or add optional hardware smoke |

## Suspicious or unnecessary dependencies

| Dependency | Evidence | Concern | Recommended action |
|---|---|---|---|
| Remote editable self install | `requirements.txt:9` | Installs the project from GitHub instead of local checkout | Remove from requirements |
| PyInstaller/dev tools absent from pyproject extras | `pip freeze` shows PyInstaller/pytest, but `pyproject.toml` does not define dev extras | Build/test environment is implicit | Add `dev` extra or `requirements-dev.txt` |

## Architecture concerns

| Concern | Evidence | Impact | Recommended fix |
|---|---|---|---|
| Runtime resource lookup is path-based and not packaged explicitly | `translations.py:140-145`, `diagram_assets.py:40-46` | Works in source tree but fragile in frozen/wheel installs | Use importlib resources or explicit PyInstaller datas/package data |
| Global input behavior has no centralized safety gate | `keyboard_output.py:55-120`, mapping dispatch in `mapper_service.py` | Harder to add pause/safe mode later | Add a top-level enable/disable state before dispatch |

## Agent safety concerns

| Concern | Evidence | Risk | Recommended fix |
|---|---|---|---|
| External prompt kits/repo instructions are being used | Current audit request | Prompt files can conflict with local goals | Keep read-only audit first and require approval for fixes |

## Human review required

| File/path | Reason | Priority |
|---|---|---|
| `BBCC.spec` | Release correctness depends on it | High |
| `requirements.txt` | Supply-chain/install correctness | High |
| `keyboard_output.py` | Global input safety | Medium |
| `mapper_service.py` | Core mapping dispatch | Medium |

## Minimum remediation before release

Fix packaged asset bundling, remove remote editable self-dependency, repair `check_mapping.py`, and add tests/checks that prevent these regressions.
