# Dependency and Supply Chain Audit

## Overall supply-chain risk

High until install and package-build ambiguity is fixed.

## Files inspected

`pyproject.toml`, `requirements.txt`, `BBCC.spec`, `.gitignore`, `build/BBCC/warn-BBCC.txt`, `dist/BBCC.exe`, `dist/BBCC-win64-v0.1.1.zip`, `pip freeze`, `pip check`.

## Dependency inventory

| Ecosystem | Manifest | Lockfile | Notes |
|---|---|---|---|
| Python | `pyproject.toml`, `requirements.txt` | No lockfile with hashes | Runtime deps are listed; dev/build deps are implicit in current venv |
| PyInstaller | `BBCC.spec` | Build output in `build/`/`dist/` | App data files are not included in `datas` |
| CI/CD | None found | N/A | No workflow files found |

## Critical findings

| ID | Finding | Evidence | Impact | Recommended fix |
|---|---|---|---|---|
| None | No Critical supply-chain issue confirmed | No install scripts, postinstall hooks, CI secrets, Docker, or remote script execution found | N/A | N/A |

## High findings

| ID | Finding | Evidence | Impact | Recommended fix |
|---|---|---|---|---|
| DEP-H01 | `requirements.txt` contains a remote editable install of the project itself | `requirements.txt:9`; current venv freeze shows a different editable Git commit | Tests or builds may run a stale remote checkout instead of local source; network dependency increases supply-chain ambiguity | Remove the remote editable self-dependency; document `pip install -e .`; create `requirements-dev.txt` for pytest/PyInstaller |
| DEP-H02 | PyInstaller spec omits app data assets | `BBCC.spec:8` has `datas=[]`; runtime code expects `assets/translations`, `assets/diagrams`, and `config/hitmaps` | Packaged release can miss user-facing assets | Add data files to `BBCC.spec`; add package data metadata and verification |

## Suspicious dependencies or scripts

| Item | Evidence | Concern | Recommended action |
|---|---|---|---|
| Remote editable self-dependency | `requirements.txt:9` | Incorrect install target and remote supply-chain dependency | Remove |
| Missing dev dependency declaration | `pip freeze` includes `pytest`, `pyinstaller`; `pyproject.toml` does not define dev extras | Reproducibility gap | Add optional dependency group or dev requirements file |

## CI/CD supply-chain risks

| Workflow/file | Risk | Evidence | Recommended fix |
|---|---|---|---|
| None | No automated supply-chain checks | No `.github` workflow files found | Add CI for tests, pip check, packaging smoke, and artifact verification |

## Container or infrastructure risks

| File/path | Risk | Evidence | Recommended fix |
|---|---|---|---|
| None found | No container/IaC surface | No Dockerfile/IaC files found | N/A |

## License risks

| Dependency/file | License issue | Evidence | Recommended action |
|---|---|---|---|
| Repository | No license file found | Root search found no `LICENSE`/`COPYING`/`NOTICE` | Add license before public release |
| Python dependencies | License inventory not documented | `requirements.txt`, `pyproject.toml` list dependencies but no license report | Generate dependency license inventory and review PyQt5 terms for intended distribution |

## Missing controls

| Control | Status | Priority |
|---|---|---|
| Lockfile or hash-pinned install | Missing | Medium |
| Vulnerability scanning | Missing | Medium |
| SBOM/provenance/signing | Missing | Medium |
| CI checks | Missing | Medium |
| Release artifact verification | Missing | High |

## Unknowns

| Unknown | Why it matters | How to verify |
|---|---|---|
| Exact intended dependency policy | Determines lockfile vs constraints strategy | Decide and document |
| PyQt5 distribution/license obligations | Required for public/commercial distribution | Legal/license review |
| Artifact signing/provenance | Required for user trust | Define release process |

## Minimum work before release

Remove the remote editable project dependency, declare dev/build dependencies separately, bundle and verify app assets in release artifacts, add a license, and add at least a basic CI/test/package verification workflow.
