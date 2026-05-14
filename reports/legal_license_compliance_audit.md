# Legal, License, and Compliance Audit

## Overall legal/compliance risk

Medium / Unknown.

## Non-legal-advice disclaimer

This report is a technical risk screen and is not legal advice.

## Critical legal/compliance blockers

| ID | Blocker | Evidence | Risk | Required action |
|---|---|---|---|---|
| None confirmed | No regulated domain, payments, accounts, or cloud data transfer found | Source search and project summary | N/A | N/A |

## License review

| Item | License/status | Risk | Recommended action |
|---|---|---|---|
| Repository | Missing/unknown | Public/commercial reuse terms are undefined | Add a repository license |
| PyQt5 | Dependency license requires review | GUI framework distribution terms can affect packaged apps | Confirm PyQt5 license obligations for intended distribution |
| pygame, psutil, pynput, pywin32, six | Not inventoried in repo | Dependency license compatibility unknown | Generate and review dependency license inventory |
| Built exe/zip | No signing/provenance docs | User trust and redistribution clarity gap | Add release provenance/signing plan |

## Privacy and terms gaps

| Document/control | Status | Why it matters | Recommended action |
|---|---|---|---|
| Privacy notice | Missing | App stores local device metadata and process-profile config | Add local-data privacy notice |
| Terms/usage boundaries | Missing | App emits global keyboard/mouse inputs | Add safe-use disclaimer and user responsibility boundaries |
| Data deletion instructions | Missing | Users need to remove `%APPDATA%` config and autostart | Add uninstall/reset instructions |
| Support policy | Missing | External users need issue path | Add support docs/issue template |

## AI disclosure and responsibility gaps

| Gap | Evidence | Risk | Recommended action |
|---|---|---|---|
| No runtime AI features found | Source search found no LLM/API client | N/A | N/A |
| AI-generated-code provenance unknown | Project was audited using AI tooling; no provenance doc | Low legal risk, medium maintenance risk | Optional: document review/testing process, not as legal disclosure |

## Regulated-domain risks

| Domain | Relevance | Risk | Expert review needed? |
|---|---|---|---|
| Healthcare/finance/legal/children/government | Not relevant from inspected code/docs | Low | No, unless product positioning changes |
| Accessibility | Desktop utility may affect input workflows | Unknown | Consider review if marketed as assistive tech |

## Marketplace/app-store risks

| Requirement area | Status | Risk | Recommended action |
|---|---|---|---|
| Windows code signing | Unknown | SmartScreen/trust friction | Define signing plan |
| Installer/uninstaller | Unknown | Autostart/config cleanup gaps | Document or implement uninstall cleanup |
| Privacy disclosures | Missing | Required by many distribution channels | Add privacy/local-data notice |

## Expert review required

| Area | Why | Priority |
|---|---|---|
| Repository and dependency licensing | Needed before public/commercial distribution | High |
| PyQt5 packaged-app licensing | GUI dependency terms can be material | High |
| Privacy/terms text | Needed for public release | Medium |

## Minimum legal/compliance work before release

Add a license, create a dependency license inventory, review PyQt5 distribution obligations, and add privacy/terms/safety documentation before public release.
