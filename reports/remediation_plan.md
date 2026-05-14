# Remediation Plan

## Executive summary

No Critical issue was confirmed. Two High issues should be fixed before controlled beta or public release: packaged assets are likely missing from the frozen app, and `requirements.txt` can install remote/stale code instead of the local project. Medium issues include a broken helper script, absent CI, version mismatch, and missing safety/support/legal docs.

## Release blockers

| Priority | Finding ID | Source report | Fix objective | Files likely involved | Human approval required? |
|---|---|---|---|---|---|
| P0 | H-01 / DEPLOY-H01 / DEP-H02 | Post-build, deployment, dependency | Bundle and verify translations, diagrams, and hitmaps in packaged builds | `BBCC.spec`, `pyproject.toml`, tests | Yes |
| P0 | H-02 / DEP-H01 | Post-build, dependency | Remove remote editable self-dependency and define reproducible local/dev install | `requirements.txt`, optional `requirements-dev.txt`, README | Yes |
| P1 | M-01 | Post-build, testing, operations | Repair or remove `check_mapping.py` | `check_mapping.py`, tests | Yes |
| P1 | M-02 | Testing/dependency | Add CI quality gates | `.github/workflows/*` | Yes |
| P1 | M-03 | Post-build/product/deployment | Align version/release metadata | `pyproject.toml`, release notes, artifact naming docs | Yes |

## Fix batches

| Batch | Objective | Included findings | Excluded findings | Why this batch is safe |
|---|---|---|---|---|
| Batch 1 | Release packaging correctness | H-01, DEPLOY-H01, DEP-H02, T-H01 | CI, legal docs | Localized to build metadata and tests |
| Batch 2 | Install/dependency reproducibility | H-02, DEP-H01, T-H02 | License inventory | Does not change runtime behavior |
| Batch 3 | QA tooling repair | M-01 | CI | Small script/test fix |
| Batch 4 | Release docs/process | M-02, M-03, legal/privacy/support docs | Code behavior | Documentation/process only |

## Critical fixes

| Finding | Required fix | Implementation notes | Validation method |
|---|---|---|---|
| None | N/A | N/A | N/A |

## High-priority fixes

| Finding | Required fix | Implementation notes | Validation method |
|---|---|---|---|
| Packaged app omits assets | Add `assets/translations/*.json`, `assets/diagrams/*.svg`, and `config/hitmaps/*.json` to PyInstaller datas and package data | Prefer robust resource lookup via `sys._MEIPASS` or `importlib.resources`; keep source-tree fallback | Inspect PyInstaller archive and run exe outside repo verifying translated UI/diagram asset availability |
| Remote editable self-dependency | Remove `-e git+https://github.com/Bum-Boo/BBCC...` from runtime requirements | Use `pip install -e .` in README; create dev requirements for pytest/PyInstaller if needed | Fresh venv install from local checkout; `pip check`; `pytest` |

## Medium-priority backlog

| Finding | Recommended action | Owner | Target timing |
|---|---|---|---|
| Broken `check_mapping.py` | Update to current `UiSnapshot` or config model, add smoke test | Engineering | Before next release |
| No CI | Add tests, compile, pip check, asset parse, packaged asset check | Engineering | Before next release |
| Version mismatch | Align project version, release notes, artifact names | Release owner | Before next release |
| Safety/privacy docs missing | Add local-data, autostart, emergency disable/reset docs | Product/engineering | Before external users |
| License/legal docs missing | Add license and dependency inventory | Owner/legal | Before public distribution |

## Unknowns to investigate

| Unknown | Investigation task | Expected output |
|---|---|---|
| Clean-machine packaged behavior | Run `BBCC.exe` from a directory with no repo assets and verify UI text/diagrams | Pass/fail release smoke record |
| Code signing | Decide if release exe will be signed | Signing plan or accepted risk |
| Hardware matrix | Test documented controllers on target Windows versions | Manual QA results |

## Expert review required

| Area | Why expert review is needed | Suggested reviewer |
|---|---|---|
| PyQt5/app licensing | Distribution obligations can affect public/commercial release | Legal/licensing reviewer |
| Code signing/distribution | Windows trust and installer behavior | Release/security owner |

## Next safe coding-agent task

Paste this into the coding agent only after human approval:

```text
Fix the approved High release-readiness issues from reports/remediation_plan.md.

Scope:
1. Ensure packaged/frozen builds include and can load app assets:
   - assets/translations/*.json
   - assets/diagrams/*.svg
   - config/hitmaps/*.json
   Update BBCC.spec and package metadata/resource lookup only as needed.
2. Replace the remote editable self-dependency in requirements.txt with a reproducible local/dev install structure.
3. Add focused regression checks for packaged asset inclusion/resource lookup and fresh local install assumptions.

Constraints:
- Do not deploy, push, or rotate secrets.
- Preserve existing app behavior.
- Run pytest, compileall, asset parsing, and a packaged/resource smoke check if PyInstaller is available.
- Summarize exact files changed and remaining manual QA.
```
