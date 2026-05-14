# Third-Party Notices

This file is a release-readiness inventory, not legal advice. Review it before distributing BBCC binaries.

## Project License

The project license has not been selected in this repository. Choose and add a `LICENSE` file before public or commercial distribution.

## Runtime Dependencies

| Package | Version in current environment | License metadata | Use |
|---|---:|---|---|
| PyQt5 | 5.15.11 | GPL v3 | GUI toolkit |
| PyQt5-Qt5 | 5.15.2 | GPL v3 | Qt runtime bundled by PyQt5 |
| PyQt5_sip | 12.18.0 | SIP | PyQt support |
| pygame | 2.6.1 | LGPL | SDL/controller input |
| psutil | 7.2.2 | BSD-3-Clause | Foreground process lookup support |
| pynput | 1.8.1 | LGPLv3 | Keyboard and mouse output |
| pywin32 | 311 | PSF | Windows foreground/autostart integration |
| six | 1.17.0 | MIT | Transitive compatibility dependency |

## Build and Test Dependencies

| Package | Version in current environment | License metadata | Use |
|---|---:|---|---|
| pyinstaller | 6.19.0 | GPLv2-or-later with PyInstaller exception | Windows exe packaging |
| pyinstaller-hooks-contrib | 2026.4 | Unknown in this audit | PyInstaller hooks |
| pytest | 9.0.3 | MIT | Test runner |

## Release Notes

- Confirm exact dependency versions from the release environment.
- Review PyQt5 and LGPL obligations before publishing binaries.
- Include third-party license texts or links as required by the final distribution model.
