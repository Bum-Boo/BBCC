# BBCC Portfolio Case Study

## Problem

Creative and desktop workflows often depend on repeated shortcuts spread across the keyboard. Small controllers can make those actions easier to reach, but a useful tool needs more than raw button detection. It needs device memory, app-specific profiles, editable presets, clear labels, and a way to inspect what the controller is actually sending.

## Target Users

- Windows users who want controller-driven shortcuts.
- Creative workers using tools such as Photoshop or Illustrator.
- Users who benefit from one-handed shortcut surfaces.
- People who want media control and desktop navigation without keeping a large control window open.

## Design Goal

BBCC turns a small controller, such as an 8BitDo Zero 2, into a local shortcut surface while keeping configuration visible, local, and user-controlled.

Core model:

```text
Device -> App Profile -> Preset -> Button Mapping
```

## Core Workflow

1. Connect or select a remembered controller.
2. Review the active app profile and preset.
3. Inspect button mappings and labels.
4. Edit a selected mapping.
5. Open Inspector to verify raw buttons, axes, hats, backend, and GUID values.
6. Manage fallback and app-specific profiles by process name.

## Architecture Summary

The repository is a Python desktop app with PyQt UI layers, controller input handling, mapping services, diagram assets, saved-device configuration, and tests around mapping behavior and runtime resources.

## Safety / Privacy Decisions

- Configuration stays local.
- Active profile and selected preset should be visible.
- Raw input inspection helps users verify hardware behavior.
- Supported controller claims stay conservative.
- The app should avoid hidden automation or remote-control assumptions.
- Because it can emit local keyboard/mouse input, stop/reset guidance should stay easy to find.

## Technical Highlights

- Controller input normalization.
- App-aware profile and preset model.
- Offline saved-device editing.
- Controller-aware diagrams.
- Inspector for raw input diagnostics.
- Release packaging for Windows ZIP builds.

## Current Limitations

- Practical support focuses on 8BitDo Zero 2 and Xbox/XInput-family devices.
- Some mappings and layouts are still being refined.
- Broader controller support should be added through tested device-specific work.

## Next Steps

- Keep the English README clean and concise.
- Link [Download / Release](download-release.md) from the README after the current dirty documentation work is reconciled.
- Add a short GIF showing controller selection, mapping edit, and inspector view.
- Keep safety and privacy guidance visible near release links.

## Portfolio Value

BBCC demonstrates practical Windows desktop utility design, HCI-oriented workflow modeling, local-first configuration, controller input diagnostics, and visible control over automation that affects the user's active desktop.
