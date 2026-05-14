# Security and Privacy Audit

## Overall risk level

Medium.

## Release recommendation

No Critical remote security issue was found. For public release, add explicit local-data/privacy and safety documentation, and treat global input/autostart as sensitive local capabilities.

## Data flow summary

| Step | Data | Source | Destination | Stored? | External transfer? | Risk |
|---|---|---|---|---|---|---|
| Controller polling | axes/buttons/hats/device metadata | pygame/SDL | in-memory backend state | No persistent raw input | No | Low |
| Device/profile persistence | device id, display name, GUID, app process names, mappings | UI/backend | `%APPDATA%/zero2-input-inspector/config.json` | Yes | No | Medium |
| Foreground app detection | process name | Windows API/psutil | in-memory and mapping resolver | Not persisted by default | No | Medium |
| Output dispatch | keyboard/mouse/media events | controller mappings | active desktop session | No | No | Medium |
| Autostart | executable command | app settings | HKCU Run registry key | Yes | No | Medium |

## Sensitive data inventory

| Data type | Location | Sensitivity | Evidence | Required protection |
|---|---|---|---|---|
| Controller GUID/device name | Local config | Low to medium local device fingerprint | `settings_store.py:34-36`, `settings_store.py:308-309` | Document local storage and deletion |
| App process names/profiles | Local config | May reveal user app/workflow habits | `domain/profiles.py`, `settings_store.py` | Document local-only storage |
| Shortcut mappings | Local config | Can encode privileged/destructive local actions | `settings_store.py`, `keyboard_output.py` | Provide safety guidance and reset path |
| Runtime logs | In-memory only | Low, but includes backend and mapping diagnostics | `mapper_service.py:155`, `mapper_service.py:1650` | Avoid writing logs unless redacted |

## Critical security findings

| ID | Finding | Evidence | Attack scenario | Impact | Recommended fix |
|---|---|---|---|---|---|
| None | No Critical security issue confirmed | No network server, auth system, remote API, payments, database, or file upload surface found | N/A | N/A | N/A |

## High security findings

| ID | Finding | Evidence | Impact | Recommended fix |
|---|---|---|---|---|
| None | No High security issue confirmed | Local desktop-only tool; no remote attack surface found | N/A | N/A |

## Privacy findings

| ID | Finding | Evidence | Privacy impact | Recommended fix |
|---|---|---|---|---|
| P-01 | No privacy/local-data notice | No privacy or terms files found; config stores device/app profile metadata | Users may not understand what is stored and how to remove it | Add a short privacy/local-data section covering `%APPDATA%`, registry autostart, no external transfer |
| P-02 | Foreground process monitoring is core behavior but not fully explained | `app_monitor.py` reads foreground process name via Windows APIs | Users may perceive this as sensitive app-usage monitoring | Explain that process names are used locally for profile switching |

## AI/LLM security findings

| ID | Finding | Evidence | Risk | Recommended fix |
|---|---|---|---|---|
| None | No AI/LLM runtime integration found | No OpenAI/LLM/API client references found in source search | N/A | N/A |

## Missing controls

| Control | Missing or weak? | Why it matters | Priority |
|---|---|---|---|
| First-run safety/consent copy | Missing in repository docs | App emits global keyboard/mouse input | Medium |
| Emergency pause/disable documentation | Missing | Users need recovery from bad mappings/drift | Medium |
| Config deletion/reset documentation | Missing | Privacy and support requirement | Medium |
| Code signing / trusted distribution | Unknown | Windows users may distrust unsigned input-control software | Medium |

## Files requiring human security review

| File/path | Reason | Priority |
|---|---|---|
| `src/zero2_input_inspector/services/keyboard_output.py` | Emits global keyboard/mouse/media events | High |
| `src/zero2_input_inspector/services/autostart.py` | Writes HKCU Run registry key | Medium |
| `src/zero2_input_inspector/services/settings_store.py` | Persists local profile/device metadata | Medium |
| `src/zero2_input_inspector/services/app_monitor.py` | Reads foreground process names | Medium |

## Unknowns

| Unknown | Why it matters | How to verify |
|---|---|---|
| Whether the exe will be code-signed | Affects Windows trust and tamper expectations | Confirm release process |
| Whether installers modify registry/uninstall config | Affects user control and privacy | Define installer/uninstaller behavior |
| Whether logs will ever be written to disk | Could create privacy footprint | Confirm future logging plan |

## Minimum security work before release

Add safety/privacy documentation, include a visible recovery/disable path, and manually review global input/autostart behavior on a clean Windows user account.

## Minimum privacy work before release

Document local data stored in `%APPDATA%`, registry autostart behavior, no external data transfer, and how users can delete/reset settings.
