# Safety and Privacy

## Scope

BBCC is a local Windows desktop controller mapper. It does not require accounts, a server, cloud sync, payments, analytics, or an external API.

## What BBCC Can Do

- Read controller state through pygame/SDL.
- Read the foreground process name to choose an app profile.
- Send keyboard, mouse, and media-key events to the current foreground app.
- Store controller profiles and settings in the current user's Windows profile.
- Optionally register itself in the current user's Windows startup list.

## Local Data

BBCC stores settings in:

```text
%APPDATA%\zero2-input-inspector\config.json
```

The file can include:

- remembered controller names and IDs
- controller GUIDs when available
- app profile names and process names
- button mappings, labels, and presets
- language, theme, and autostart preference

No telemetry or network upload path is present in the current project.

## Safety Rules

- Test new mappings in a low-risk app before using them in real work.
- Avoid assigning destructive shortcuts such as delete, close, save-overwrite, or send/post actions until you have tested the profile.
- Remember that mappings act on the foreground app, not on BBCC itself.
- Keep a keyboard or mouse available while testing controller navigation.
- Disable autostart while experimenting with new mappings.

## Stop or Recover

Use these options if a mapping behaves unexpectedly:

1. Quit BBCC from the tray menu.
2. Disconnect or power off the controller.
3. Open BBCC and clear or reset the mapping.
4. Delete `%APPDATA%\zero2-input-inspector\config.json` to reset local settings.
5. If autostart is enabled, turn it off in BBCC settings or remove the `BBCC` value from:

```text
HKCU\Software\Microsoft\Windows\CurrentVersion\Run
```

## Support Redaction

When sharing screenshots or logs, review them for:

- controller names and GUIDs
- foreground process names
- custom app profile names
- shortcut labels that reveal private workflows

## Release Status

The current audit decision is internal testing only. External beta or public release should wait for license review, CI, artifact trust controls, and hardware QA.
