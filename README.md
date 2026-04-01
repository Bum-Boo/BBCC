# zero2-input-inspector

`zero2-input-inspector` is a Windows-first tray-resident controller mapper built for creative shortcut workflows.

The current major version keeps the original raw input inspector, but the main screen is now focused on mapping:

`Device -> App Profile -> Preset -> Button Mapping`

This makes it practical to hold a small controller in one hand and use a pen in the other while working in apps like Photoshop and Illustrator.

## What This Version Does

- Runs in the system tray and continues mapping while the main window is hidden
- Reads controllers through the existing `pygame` / SDL backend
- Uses a device-family resolver that checks saved family, GUID fragments, name tokens, and input shape
- Uses SDL standard-controller metadata when available, with family-specific raw fallback maps for known devices
- Normalizes raw input into canonical controls such as `DPAD_LEFT`, `FACE_SOUTH`, `START`, and `SELECT`
- Keeps device/app/preset profile storage in `%APPDATA%`
- Switches active app profiles by foreground process name
- Treats the wildcard `YouTube` profile as the media/general-use fallback when no foreground app matches
- Supports 1 to 5 presets per app profile
- Reserves preset switching as a system action separate from ordinary shortcut mappings
- Prefers the Noto Sans family for multilingual typography and will load bundled font files from `assets/fonts` when present
- Shows a small non-stacking preset toast
- Keeps the inspector as a separate advanced popup window
- Moves language and auto-start controls into a separate settings popup; language changes are pending until Save is clicked

## UI Model

### Empty State

- Large remembered-device browser
- Simple connect-to-start message
- No raw tables in the main screen
- No mapping workspace until at least one controller is connected

### Connected State

Top toolbar:

- App profile selector
- Preset selector
- Inspector button
- Settings button

Main workspace:

- Left: remembered devices list
- Right:
  - device/profile header
  - controller diagram
  - mapping list
  - selected mapping editor

Bottom strip:

- Previous / Next / Add / Delete
- Current preset name

### Snapshot Updates

- Fast snapshots keep runtime visuals current: controller highlights, device status, and raw inspector data
- Slow sync is limited to model-driven controls: language lists, app/preset lists, and editable text fields
- Live runtime focus stays separate from the selected mapping target, so telemetry updates do not steal editing focus
- While a line edit has focus or contains an unsaved draft, incoming snapshots do not overwrite the user's text

## Preset Rules

- Default preset count: 3
- Minimum preset count: 1
- Maximum preset count: 5
- Delete is disabled when only 1 preset remains
- Add is disabled when 5 presets already exist
- Preset switching wraps around

Default preset switching for app-specific profiles:

- `Select`-like button -> previous preset
- `Start`-like button -> next preset

Wildcard fallback profile:

- `YouTube` is the built-in fallback profile used for general desktop and media control
- The default `YouTube` preset is tuned for YouTube/media shortcuts
- The fallback profile does not reserve its `Select` and `Start` mappings for preset switching

## Supported Devices Right Now

Current practical target:

- 8BitDo Zero 2
- Xbox Controller / XInput-family devices

Current secondary support:

- Generic SDL joystick devices with best-effort normalization

## Current Device-Specific Behavior

### 8BitDo Zero 2

- Main UI uses a simplified Zero 2 placeholder layout
- No fake analog sticks are shown
- Face buttons use the actual hardware labels in the correct positions
- D-pad, A/B/X/Y, L/R, Select, and Start are mapped through canonical controls
- Zero 2 has its own device template and raw fallback button map instead of sharing a generic map

### Xbox / Generic Controllers

- Xbox-family devices now have their own device template, button map, and simplified placeholder diagram
- The Xbox diagram includes sticks, triggers, shoulders, face buttons, View, Menu, and Xbox
- Stick directions are canonicalized for Xbox-family devices so live highlighting follows the real hardware
- Standard SDL controllers can still map through canonical controls
- Inspector works
- The app still avoids fake controller art when no exact device diagram exists
- Unknown layouts show a neutral placeholder instead of a pretend gamepad

## Localization And Diagram Layouts

- Diagram placeholder layouts live in `src/zero2_input_inspector/gui/widgets/controller_diagram_layouts.py`
- Hit areas are defined alongside the placeholder layouts so styling stays separate from geometry
- Translation dictionaries live in `assets/translations/*.json`
- The translation loader falls back to English when a target language file does not define a key
- Save applies the selected language and closes the Settings dialog

## Known Limitations

- Shortcut output is still tap-on-press, not full hold-state mapping
- Per-device preset-switch override UI is not exposed yet
- Xbox diagram support is limited to devices that the resolver identifies as Xbox-family; other standard controllers stay on the generic path
- Unknown non-standard controllers stay out of the main mapping flow until they have a trusted canonical map
- Translation keys that are not defined in a target language fall back to English
- Process matching is exact executable-name matching such as `photoshop.exe`, with `*` used as the fallback profile
- Controller diagrams are temporary placeholder layouts and are intended to be replaced with custom artwork later

## Architecture

```text
src/zero2_input_inspector/
|-- application.py              # tray bootstrap and lifetime management
|-- main.py                     # CLI entry point
|-- styles.py                   # global UI styling
|-- backend/
|   |-- base.py                 # input backend contract
|   |-- models.py               # raw backend state + SDL controller metadata
|   `-- pygame_backend.py       # SDL joystick reader
|-- domain/
|   |-- controls.py             # canonical control ids
|   |-- profiles.py             # device/app/preset config models
|   `-- state.py                # normalized + UI snapshot models
|-- services/
|   |-- app_monitor.py          # foreground process detection
|   |-- autostart.py            # Windows Run key integration
|   |-- device_registry.py      # family resolution and reconnect matching
|   |-- device_templates.py     # family metadata, layouts, and button maps
|   |-- keyboard_output.py      # shortcut sender
|   |-- mapper_service.py       # runtime coordinator and UI snapshot builder
|   |-- normalization.py        # device identification + raw -> canonical controls
|   |-- settings_store.py       # AppData persistence
|   |-- typography.py           # font loading + language-aware font stack
|   `-- translations.py         # UI strings
|-- assets/
|   `-- translations/
|       |-- en.json
|       |-- ja.json
|       |-- ko.json
|       `-- zh.json
`-- gui/
    |-- dialogs/
    |   |-- inspector_dialog.py
    |   `-- settings_dialog.py
    |-- main_window.py          # product-style mapper window
    `-- widgets/
        |-- controller_diagram.py          # compatibility wrapper
        |-- controller_diagram_placeholder.py
        |-- controller_diagram_layouts.py
        |-- device_list.py
        |-- stable_combobox.py
        `-- toast.py
```

## Runtime Flow

1. `pygame_backend.py` polls connected controllers and captures SDL standard-controller mappings when SDL recognizes the device.
2. `device_registry.py` resolves the family using saved identity, GUID fragments, name tokens, and input shape.
3. `normalization.py` converts raw input into canonical controls using the resolved family template.
4. `mapper_service.py` picks the active app profile from the foreground process name.
5. The active preset maps canonical controls to keyboard shortcuts.
6. The main UI shows only mapping-focused information.
7. `controller_diagram_layouts.py` provides the temporary placeholder geometry for rendering and click selection.
8. The inspector popup exposes raw input and logs for advanced diagnostics.

## Unknown Layout

An unknown layout means the app does not have a trusted exact hardware template for the connected device.

- The app does not draw a fake controller for that device
- The main workspace shows a neutral explanatory panel instead
- If SDL still provides canonical controls, the mapping table can remain usable
- If no trusted canonical mapping exists, use Inspector until a device template is added

## Data Storage

Mappings and settings are stored here:

```text
%APPDATA%\zero2-input-inspector\config.json
```

Auto-start uses this registry location:

```text
HKCU\Software\Microsoft\Windows\CurrentVersion\Run
```

## Setup

1. Create a virtual environment:

   ```powershell
   py -3 -m venv .venv
   ```

2. Activate it:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the project:

   ```powershell
   python -m pip install --upgrade pip
   pip install -e .
   ```

## Run

Normal windowed start:

```powershell
python -m zero2_input_inspector
```

Start hidden in the tray:

```powershell
python -m zero2_input_inspector --background
```

Console entry point:

```powershell
zero2-input-inspector
```

## Validation

Validated locally with:

- `python -m compileall src`
- hidden tray startup smoke test

## Next Logical Steps

- Add shortcut capture and hold/repeat output modes
- Expose per-device preset-switch override editing in the UI
- Expand device-family normalization coverage beyond Zero 2 and Xbox
