# Product and Strategy Audit

## Product maturity score

Score: 63/100

Stage: Controlled beta candidate after release-blocking packaging/install fixes.

## One-sentence judgment

The product has a coherent core workflow and real utility, but external-user readiness is held back by packaging reliability, safety/onboarding gaps, and missing release/support documentation.

## Target user assessment

| Item | Finding | Evidence | Risk |
|---|---|---|---|
| Target user | Clear enough: Windows users who want controller-driven shortcuts for creative apps, media, and desktop navigation | `README.md:7-13`, `README.md:35-40` | Low |
| Supported controller scope | Narrow and understandable: 8BitDo Zero 2 and Xbox/XInput family | `README.md:26-33`, `RELEASE_NOTES_v0.1.0.md:18-22` | Low |
| Product promise | Multilingual UI, themes, controller diagrams, inspector, editable mappings | `README.md:15-24` | High if packaged assets are missing |
| Commercial readiness | Not defined | No pricing, support, license, installer, privacy/terms found | Medium |

## Value proposition assessment

The value proposition is credible: fast controller-based shortcut control without a persistent main window. The implemented architecture matches the stated model: `Device -> App Profile -> Preset -> Button Mapping`. The strongest product gap is not feature coherence; it is release trust. Users need to know what global shortcuts can do, how to pause/quit safely, what data is stored locally, and how to recover from a bad mapping.

## MVP scope assessment

| Feature | Keep in MVP? | Reason | Risk if kept/removed |
|---|---|---|---|
| Tray-resident mapper | Yes | Core product behavior | Removing it weakens the product |
| App profile switching | Yes | Differentiates workflow use | Needs transparent process matching behavior |
| Per-profile presets | Yes | Core repeated-use value | Keep but document limits |
| YouTube/media fallback | Yes | Useful default workflow | Ensure defaults are safe and tested |
| Multilingual UI | Yes, if packaged correctly | Promised in README | High trust risk if translations do not ship |
| Controller diagrams/hitmaps | Yes, if packaged correctly | Important UX for mapping | High UX risk if missing in exe |
| Autostart | Optional MVP | Useful but sensitive | Needs clear opt-in and easy disable |

## Commercialization gaps

| Gap | Severity | Why it matters | Recommended fix |
|---|---|---|---|
| No explicit license | Medium | Blocks public reuse/commercial clarity | Add `LICENSE` |
| No support policy | Medium | Users need a path for controller compatibility issues | Add support/issue template and troubleshooting doc |
| No installer/update strategy | Medium | A raw exe/zip is harder to trust and update | Define release channel, signing, update docs |
| No privacy/safety notice | Medium | App stores local device/app-profile metadata and emits global input | Add local-data and shortcut-risk notice |

## User experience gaps

| Gap | Evidence | Impact | Recommended fix |
|---|---|---|---|
| First-run safety guidance is not visible in repo docs | README has usage but no safety/escape-hatch section | New users may not know how to pause/quit or recover from bad mappings | Add "Safety and recovery" docs |
| Packaged assets may be missing | `BBCC.spec:8` and asset lookup code | Diagrams/translations can fail in release build | Bundle assets and test them |
| Hardware onboarding is limited | README lists supported controllers but no pairing/calibration/troubleshooting | More support load | Add controller setup checklist |

## Trust and quality gaps

| Gap | Evidence | Risk | Recommended fix |
|---|---|---|---|
| No visible release QA checklist | No checklist file found | Releases can miss hardware/packaging regressions | Add manual QA checklist |
| Version mismatch | `pyproject.toml` `1.0.0`; release notes `v0.1.0`; artifact `v0.1.1` | User confusion | Align release metadata |

## Product release blockers

| Severity | Blocker | Evidence | Required action |
|---|---|---|---|
| High | Packaged app asset completeness is unproven and likely broken | `BBCC.spec:8`, archive inspection | Bundle assets and verify packaged UI |
| High | Install instructions/dependency file can install remote stale code | `requirements.txt:9` | Replace with local/dev requirements structure |

## Recommended MVP definition

- Core user: Windows user with an 8BitDo Zero 2 or Xbox/XInput controller.
- Core problem: Repeated desktop/media/creative shortcuts are awkward without a keyboard.
- Core workflow: Connect controller, select or remember device, choose app profile, edit preset mappings, run from tray.
- Must-have features: controller detection, safe defaults, mapping editor, profiles/presets, tray quit, local settings, release package with assets.
- Excluded features: broad controller support beyond documented devices, cloud sync, account/auth, payment, auto-update.
- Success metric: supported-controller user can install, map, and use shortcuts for 30 minutes without drift/misfire.
- Failure metric: packaged app loses diagrams/translations or emits unintended inputs.

## Next product tasks

| Priority | Task | Output | Owner |
|---|---|---|---|
| P0 | Fix packaged asset release path | Verified exe with translations/diagrams/hitmaps | Engineering |
| P0 | Fix requirements/install ambiguity | Clean runtime/dev install docs | Engineering |
| P1 | Add safety/troubleshooting docs | README section or docs page | Product/engineering |
| P1 | Add release QA checklist | Manual device and packaged-app checklist | Release owner |
