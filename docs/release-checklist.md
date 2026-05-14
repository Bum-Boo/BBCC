# Release Checklist

## Required Before Controlled Beta

- [ ] License strategy reviewed and documented.
- [ ] `THIRD_PARTY_NOTICES.md` reviewed for runtime and build dependencies.
- [ ] Safety and privacy documentation reviewed.
- [ ] CI passes on a clean checkout.
- [ ] `python -m pytest` passes.
- [ ] `python -m compileall -q src tests check_mapping.py run_bbcc.py` passes.
- [ ] `python -m pip check` passes.
- [ ] `python -m zero2_input_inspector --version` prints the expected version.
- [ ] `python -m zero2_input_inspector --smoke-resources` passes.
- [ ] PyInstaller build succeeds.
- [ ] PyInstaller archive contains app translations, diagrams, and hitmaps.
- [ ] `check_mapping.py` runs against a test APPDATA config.

## Manual Hardware QA

| Check | 8BitDo Zero 2 | Xbox/XInput | Notes |
|---|---|---|---|
| USB connection detected |  |  |  |
| Bluetooth connection detected |  |  |  |
| Device row shows connected state |  |  |  |
| Mapping table opens from device row |  |  |  |
| Inspector shows axes/buttons/hats |  |  |  |
| YouTube/media fallback works in browser |  |  |  |
| Keyboard shortcut mapping works |  |  |  |
| Mouse move/click/scroll mapping works |  |  |  |
| Preset switching works |  |  |  |
| App profile switching works by process name |  |  |  |
| Autostart can be enabled and disabled |  |  |  |
| Packaged exe starts from a clean folder |  |  |  |

## Artifact Trust

- [ ] Release artifact name matches `pyproject.toml` and release notes.
- [ ] SHA256 checksum is published.
- [ ] Code signing decision is documented.
- [ ] Known issues are documented.
- [ ] Rollback artifact is available.

## Required Before Public Release

- [ ] Legal review complete.
- [ ] Vulnerability scan complete.
- [ ] Clean-machine QA complete on supported Windows versions.
- [ ] Support owner and response process assigned.
- [ ] Public issue template available.
