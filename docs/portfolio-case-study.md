# BBCC Portfolio Case Study

BBCC is a Windows-first controller mapping utility for creative workflows, desktop navigation, and media control. It turns a small controller, such as an 8BitDo Zero 2, into a local shortcut surface for app-specific actions.

## Positioning

BBCC fits the portfolio theme of Windows desktop utilities for real users. It is not a generic gamepad experiment; it is a practical workflow tool for people who want faster access to repeated shortcuts while keeping setup local and inspectable.

The public framing should stay focused on productivity and HCI:

- controller input as a compact shortcut surface
- app-aware profiles for different desktop workflows
- offline-editable device and mapping configuration
- visible raw input inspection for debugging and trust
- local Windows behavior without account or cloud requirements

## Problem

Creative and desktop workflows often depend on repeated shortcuts spread across the keyboard. Small controllers can make those actions easier to reach, but a useful tool needs more than raw button detection. It needs device memory, app-specific profiles, editable presets, clear labels, and a way to inspect what the controller is actually sending.

BBCC addresses that workflow by organizing mappings around:

```text
Device -> App Profile -> Preset -> Button Mapping
```

## Product Shape

The app is built around a tray-resident Windows workflow. Users can connect a supported controller, select the remembered device, review mappings, edit shortcut labels, and manage app-profile settings.

Core surfaces include:

- connected device list
- mapping table for active profile and preset
- mapping editor for selected buttons
- raw input inspector for buttons, axes, hats, backend, and GUID values
- profile settings for fallback and app-specific process matching

## Safety and Trust Boundaries

Because BBCC maps controller input to desktop actions, the README should keep safety expectations visible. The project should avoid overclaiming broad controller support and should document that mappings are local and user-controlled.

Good public boundaries:

- keep configuration local
- make active profile and selected preset visible
- expose raw input inspection for debugging
- document supported controllers clearly
- avoid hidden automation or remote control assumptions

## Implementation Notes

The repository is a Python desktop app with PyQt UI layers, controller input handling, mapping services, diagram assets, and tests around mapping behavior and resource paths.

The portfolio value is strongest when the README shows the real UI screenshots:

- connected controller detected
- mapping table
- raw input inspector
- app profile settings

## Portfolio Value

BBCC demonstrates:

- practical Windows desktop utility design
- HCI-oriented workflow modeling
- local-first configuration
- controller input normalization
- user-facing diagnostics for hardware input
- testable behavior around saved mappings and runtime resources

## Next Steps

- Keep the English README section clean and concise.
- Repair or remove corrupted translated README sections before promoting the repo heavily.
- Add a short GIF showing controller selection, mapping edit, and inspector view.
- Keep supported-controller claims conservative.
- Document validation commands after the current dependency cleanup lands.
