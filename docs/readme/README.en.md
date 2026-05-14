# BBCC

> Windows-first controller mapping for creative shortcuts, desktop navigation, and media control.

[Overview](../../README.md) | [English](README.en.md) | [한국어](README.ko.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md)

BBCC is a Windows-first, tray-resident controller mapping tool for creative workflows, desktop navigation, and media control. It is built for people who want quick controller-driven shortcuts without keeping the main window in the way.

The core concept is:

`Device -> App Profile -> Preset -> Button Mapping`

In practice, BBCC remembers your controller, switches behavior by active app, lets you keep multiple presets per profile, and maps controller inputs to keyboard shortcuts or other actions.

### Key Features

- App-based profile switching by foreground process name
- Per-profile presets for different workflows
- `YouTube` / media fallback profile for general media control
- Offline saved-device editing, so remembered devices stay usable even when disconnected
- Multilingual UI support
- Theme support
- Controller-aware layouts and diagrams
- Inspector and mapping editor for reviewing and adjusting bindings

### Supported Controllers

Current practical support focuses on:

- 8BitDo Zero 2
- Xbox Controller / XInput-family devices

If you want support for another controller model, please open an issue and describe the device. Additional controller support can be requested and discussed there.

### Typical Use Cases

- Creative apps such as Photoshop and Illustrator
- One-handed controller workflows
- YouTube and other media control
- Desktop navigation and shortcut handling

### Basic Usage

Clone the repository, create a virtual environment, install dependencies, and run the app:

```powershell
git clone <repository-url>
cd BBCC
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python -m zero2_input_inspector
```

### Demo Walkthrough

The demo flow selects the connected `8BitDo Zero 2 gamepad`, reviews the mapping table, checks raw input in Inspector, and opens app-profile settings.

1. Run `dist\BBCC.exe`.
2. Confirm that the controller is shown as `Connected` on the first screen.
3. Click the connected device row.
4. Review shortcut assignments and labels in the `button_mappings` table.
5. Select a button row to edit its shortcut and label in `mapping_editor`.
6. Click `Inspector` in the top-right area to check raw axes, buttons, hats, backend, and GUID values.
7. Open `Profile Settings` to manage fallback and app-specific profiles by process name.

The first screen confirms that the controller is detected and connected. Select the remembered device row to open its mappings.

![Connected controller detected](../demo-screenshots/controller-live-01-device-detected.png)

The mapping view shows the active app profile, button bindings, labels, and the editor panel used to adjust a selected binding.

![8BitDo Zero 2 mapping table](../demo-screenshots/controller-live-03-connected-mapping.png)

The `Inspector` button opens live raw input values, including axes, buttons, hats, backend information, and device GUID details.

![Raw input inspector](../demo-screenshots/controller-live-04-inspector.png)

`Profile Settings` opens the app-profile editor, where fallback and app-specific profiles can be named and matched by process name.

![App profile settings](../demo-screenshots/controller-live-05-profile-settings.png)

### Notes

- BBCC is a Windows-first project
- Browser-based media fallback behavior is part of the broader media workflow
- Layouts and mappings are still being refined
- Some device handling is still evolving as controller coverage expands

### Feedback / Contribution

Bug reports and pull requests are welcome. If you want support for another controller model, please open an issue and include the device name, what happened, and what you expected.
