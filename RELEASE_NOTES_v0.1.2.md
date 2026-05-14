# BBCC v0.1.2

BBCC v0.1.2 refreshes the Windows distribution package after the release-readiness audit and remediation pass.

## Fixes and Improvements

- Bundles runtime translations, controller diagrams, and hitmap JSON files into the PyInstaller executable
- Resolves frozen-app resource lookup so one-file builds can load packaged assets correctly
- Removes the remote editable self-dependency from runtime requirements
- Adds a separate development requirements file for local editable installs and test/build tooling
- Fixes `check_mapping.py` so the diagnostic script works with the current controller snapshot API
- Adds regression coverage for packaged resource lookup and the mapping diagnostic script

## Verification

- Full test suite passed: `44 passed`
- `pip check` passed
- PyInstaller build passed
- Packaged executable asset inspection confirmed translations, diagrams, and hitmaps are present
- Clean temp-directory executable smoke test passed

## Notes

- This build is suitable for internal or limited beta testing.
- Broad public release should still complete license, privacy/safety documentation, CI, and manual hardware QA.
