# Operations and Incident Response Audit

## Operational readiness

Partially ready for internal testing. Not ready for broad external users without support, diagnostics, rollback, and release-process documentation.

## Critical operational blockers

| ID | Blocker | Evidence | Impact | Required fix |
|---|---|---|---|---|
| None | No Critical operational blocker confirmed | Local desktop app with no server dependency | N/A | N/A |

## Monitoring and alerting

| Area | Status | Evidence | Gap | Required action |
|---|---|---|---|---|
| Runtime diagnostics | Basic in-app inspector/logs | `InspectorDialog`, `mapper_service.py:155`, `mapper_service.py:1650` | No export/report workflow | Add troubleshooting/export or issue-template guidance |
| Crash reporting | Missing | No crash reporter or logs to disk found | External failures invisible | Decide local diagnostic package or manual issue template |
| Release health | Missing | No CI/release dashboard found | Maintainers cannot see release regressions | Add CI and release checklist |

## Logging and diagnostics

| Area | Status | Risk | Required action |
|---|---|---|---|
| Backend logs | In-memory, max 500 | Useful but ephemeral | Add copy/export if users report issues |
| Device diagnostics | Inspector has raw and diagnostics tabs | Good for support if user can access it | Document how to open/use inspector |
| Helper script | Broken | `check_mapping.py` fails | Fix or remove |

## Backup and restore

| Data/system | Backup status | Restore status | Risk | Required action |
|---|---|---|---|---|
| User config JSON | Unknown/manual | Unknown/manual | Users can lose mappings or get stuck with bad config | Document file location, backup, reset, and restore |
| Registry autostart | Manual disable via app | Unknown if app cannot start | Users may need external disable path | Document registry value and safe removal |

## Incident response

| Item | Status | Gap | Required action |
|---|---|---|---|
| Owner/on-call | Unknown | No support ownership visible | Define support owner/channel |
| Severity handling | Missing | No incident process | Add simple support triage policy |
| Rollback | Missing | No release rollback doc | Document previous release restore |
| User communication | Missing | No status/support doc | Add issue template and known-issues section |

## Customer support readiness

| Area | Status | Gap | Required action |
|---|---|---|---|
| Controller compatibility reports | README asks users to open issues | No structured template | Add issue template fields: OS, controller, driver, logs, screenshot |
| Troubleshooting | Sparse | No device detection/autostart/reset guide | Add troubleshooting doc |
| Safety support | Missing | No bad mapping recovery guide | Add emergency quit/reset/autostart disable instructions |

## Abuse and misuse scenarios

| Scenario | Risk | Detection | Response |
|---|---|---|---|
| Accidental destructive shortcut in foreground app | Medium | User reports/logs | Provide safe defaults, reset, disable/pause guidance |
| App autostarts unexpectedly | Medium | User sees tray process | Clear opt-in, disable guide, registry cleanup |
| Unsupported controller maps incorrectly | Medium | Inspector diagnostics | Issue template and fallback mapping process |

## Minimum operations work before release

Add troubleshooting/support docs, fix diagnostic script, document config/autostart reset, add a manual QA checklist, and define release rollback/version process.
