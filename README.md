# BBCC

> Windows-first controller mapping for creative shortcuts, desktop navigation, and media control.

[Overview](README.md) | [English](docs/readme/README.en.md) | [한국어](docs/readme/README.ko.md) | [中文](docs/readme/README.zh-CN.md) | [日本語](docs/readme/README.ja.md)

| Area | Detail |
|---|---|
| Platform | Windows desktop |
| Core model | `Device -> App Profile -> Preset -> Button Mapping` |
| Practical controller focus | 8BitDo Zero 2 and Xbox/XInput-family devices |
| Main workflows | Creative apps, one-handed shortcuts, media control, desktop navigation |

## Preview

The connected controller view shows the remembered device, mapping table, Inspector, and profile settings flow.

![Connected controller detected](docs/demo-screenshots/controller-live-01-device-detected.png)

<details>
<summary>View full demo walkthrough</summary>

The demo flow selects the connected `8BitDo Zero 2 gamepad`, reviews the mapping table, checks raw input in Inspector, and opens app-profile settings.

1. Run `dist\BBCC.exe`.
2. Confirm that the controller is shown as `Connected` on the first screen.
3. Click the connected device row.
4. Review shortcut assignments and labels in the `button_mappings` table.
5. Select a button row to edit its shortcut and label in `mapping_editor`.
6. Click `Inspector` in the top-right area to check raw axes, buttons, hats, backend, and GUID values.
7. Open `Profile Settings` to manage fallback and app-specific profiles by process name.

The first screen confirms that the controller is detected and connected. Select the remembered device row to open its mappings.

![Connected controller detected](docs/demo-screenshots/controller-live-01-device-detected.png)

The mapping view shows the active app profile, button bindings, labels, and the editor panel used to adjust a selected binding.

![8BitDo Zero 2 mapping table](docs/demo-screenshots/controller-live-03-connected-mapping.png)

The `Inspector` button opens live raw input values, including axes, buttons, hats, backend information, and device GUID details.

![Raw input inspector](docs/demo-screenshots/controller-live-04-inspector.png)

`Profile Settings` opens the app-profile editor, where fallback and app-specific profiles can be named and matched by process name.

![App profile settings](docs/demo-screenshots/controller-live-05-profile-settings.png)

### Notes

- BBCC is a Windows-first project
- Browser-based media fallback behavior is part of the broader media workflow
- Layouts and mappings are still being refined
- Some device handling is still evolving as controller coverage expands

### Feedback / Contribution

Bug reports and pull requests are welcome. If you want support for another controller model, please open an issue and include the device name, what happened, and what you expected.

</details>

## Quick Start

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python -m zero2_input_inspector
```

## Documentation

- [English README](docs/readme/README.en.md)
- [한국어 README](docs/readme/README.ko.md)
- [中文 README](docs/readme/README.zh-CN.md)
- [日本語 README](docs/readme/README.ja.md)

## Notes

This overview is intentionally short. Detailed setup, architecture, limitations, and localized walkthroughs live in the linked README files.
