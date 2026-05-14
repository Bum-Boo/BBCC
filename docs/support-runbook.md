# Support Runbook

## Scope

Use this runbook for internal testing and controlled beta support.

## First Response Checklist

Ask the tester for:

- BBCC version
- Windows version
- controller model
- connection type: USB or Bluetooth
- whether the issue happens from source or packaged `BBCC.exe`
- the active app profile and preset name
- a screenshot of Inspector if safe to share
- steps to reproduce

Ask the tester to redact controller GUIDs, private process names, and custom labels when needed.

## Common Recovery Steps

1. Quit BBCC from the tray menu.
2. Disconnect the controller.
3. Restart BBCC.
4. Open Inspector and confirm the backend sees the controller.
5. Reset the current mapping or preset.
6. If the app still misbehaves, rename `%APPDATA%\zero2-input-inspector\config.json` and restart BBCC.

## Autostart Issues

BBCC uses the current-user Run key:

```text
HKCU\Software\Microsoft\Windows\CurrentVersion\Run
```

If a tester cannot disable autostart from the UI, remove the `BBCC` value from that key.

## Release Rollback

For a bad build:

1. Pull the release artifact from the public channel.
2. Publish a short known-issue note.
3. Restore the previous signed/checksummed artifact.
4. Keep the failing artifact for debugging if it is not unsafe to retain.
5. Record the root cause and validation gap in the release checklist.

## Issue Template Fields

- Expected behavior
- Actual behavior
- Controller model and connection type
- Windows version
- App profile and preset
- Packaged exe or source run
- `python -m zero2_input_inspector --smoke-resources` result, when running from source
- Screenshots/logs, redacted if needed
