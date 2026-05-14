# Performance and Scalability Audit

## Overall performance risk

Low to Medium for a single-user desktop app.

## Likely first bottleneck

The 16 ms Qt timer polling loop emits snapshots frequently and can drive repeated UI refresh work when controllers are active.

## Critical performance risks

| ID | Risk | Evidence | Impact | Recommended fix |
|---|---|---|---|---|
| None | No Critical performance risk confirmed | Desktop app, no database/network/server scaling surface | N/A | N/A |

## High performance risks

| ID | Risk | Evidence | Impact | Recommended fix |
|---|---|---|---|---|
| None | No High performance risk confirmed | Existing tests and runtime smoke did not show hangs | N/A | N/A |

## Cost risks

| Cost driver | Evidence | Failure mode | Recommended control |
|---|---|---|---|
| None | No cloud/API/AI calls found | N/A | N/A |

## Database risks

| Query/model/area | Risk | Evidence | Recommended fix |
|---|---|---|---|
| None | No database found | N/A | N/A |

## Frontend risks

| Area | Risk | Evidence | Recommended fix |
|---|---|---|---|
| Qt snapshot/UI update frequency | Medium if many devices/logs or slower machines | `MapperService` starts a 16 ms timer at `mapper_service.py:167`; `_tick()` emits snapshots at `mapper_service.py:422-431` | Measure CPU usage with connected controllers; skip snapshot emission when state has not changed |
| SVG/hitmap rendering | Low to medium | `diagram_assets.py` loads SVG renderer and hitmaps | Cache already exists via `lru_cache`; keep packaged asset test |

## External API and AI-call risks

| Integration | Risk | Evidence | Recommended fix |
|---|---|---|---|
| Windows foreground process polling | Low | `ForegroundAppMonitor` caches for 0.35s | Existing cache is reasonable |
| pygame event polling | Low to medium | `pygame_backend.py:251` and 16 ms service timer | Profile with supported controllers |

## Load testing recommendations

| Scenario | Why it matters | Suggested test |
|---|---|---|
| Idle app for 1 hour with controller connected | Detect CPU/memory/log growth | Track process CPU/RAM and log count |
| Rapid button/stick input | Detect UI lag and accidental repeats | Script/manual hardware stress test |
| Multiple remembered devices and profiles | Detect snapshot/UI scaling issues | Generate config with many profiles/presets and measure responsiveness |

## Minimum performance work before release

Run a basic CPU/memory soak test with supported controllers, and consider emitting UI snapshots only when state changes materially.
