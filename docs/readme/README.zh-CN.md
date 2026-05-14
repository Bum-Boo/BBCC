# BBCC

> 面向创作快捷键、桌面导航和媒体控制的 Windows-first 控制器映射工具。

[Overview](../../README.md) | [English](README.en.md) | [한국어](README.ko.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md)

BBCC 是一个 Windows-first、常驻托盘的 controller mapping tool，面向 creative workflows、desktop navigation 和 media control。它适合希望用控制器快速触发快捷键、同时不想让主窗口挡住工作的用户。

核心概念是：

`Device -> App Profile -> Preset -> Button Mapping`

实际使用中，BBCC 会记住 controller，根据 active app 切换行为，让每个 profile 保留多个 preset，并把 controller input 映射到 keyboard shortcut 或其他 action。

### Key Features

- 基于 foreground process name 的 app profile switching。
- 不同 workflow 的 per-profile presets。
- 用于通用 media control 的 `YouTube` / media fallback profile。
- Offline saved-device editing，即使设备断开也能编辑 remembered devices。
- Multilingual UI support。
- Theme support。
- Controller-aware layouts and diagrams。
- 用于检查和调整 binding 的 Inspector 与 mapping editor。

### Supported Controllers

当前实际支持重点是：

- 8BitDo Zero 2
- Xbox Controller / XInput-family devices

如果需要支持其他 controller model，请开 issue，并说明 device name、发生的情况和预期行为。

### Typical Use Cases

- Photoshop、Illustrator 等 creative apps。
- 单手 controller workflow。
- YouTube 和其他 media control。
- Desktop navigation 与 shortcut handling。

### Download / Release

Windows build 和 release note 请参见 [../download-release.md](../download-release.md)。该文档区分 stable release 和 prerelease asset。

### Basic Usage

clone repository，创建 virtual environment，安装 dependencies，然后运行应用：

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

demo flow 会选择已连接的 `8BitDo Zero 2 gamepad`，查看 mapping table，在 Inspector 中检查 raw input，并打开 app-profile settings。

1. 运行 `dist\BBCC.exe`。
2. 确认第一屏显示 controller 为 `Connected`。
3. 点击 connected device row。
4. 在 `button_mappings` table 中查看 shortcut assignments 和 labels。
5. 选择一个 button row，在 `mapping_editor` 中编辑 shortcut 和 label。
6. 点击右上角的 `Inspector`，检查 axes、buttons、hats、backend 和 GUID values。
7. 打开 `Profile Settings`，按 process name 管理 fallback 和 app-specific profiles。

第一屏确认 controller 已被检测并连接。选择 remembered device row 后会打开 mappings。

![Connected controller detected](../demo-screenshots/controller-live-01-device-detected.png)

mapping view 显示 active app profile、button bindings、labels，以及用于调整 selected binding 的 editor panel。

![8BitDo Zero 2 mapping table](../demo-screenshots/controller-live-03-connected-mapping.png)

`Inspector` button 会打开 live raw input values，包括 axes、buttons、hats、backend information 和 device GUID details。

![Raw input inspector](../demo-screenshots/controller-live-04-inspector.png)

`Profile Settings` 会打开 app-profile editor，可按 process name 命名和匹配 fallback / app-specific profiles。

![App profile settings](../demo-screenshots/controller-live-05-profile-settings.png)

### Notes

- BBCC 是 Windows-first project。
- Browser-based media fallback behavior 是更广泛 media workflow 的一部分。
- Layouts 和 mappings 仍在完善。
- 随着 controller coverage 扩展，部分 device handling 仍在演进。
- 在真实工作中使用 global keyboard 或 mouse mappings 前，请阅读 [Safety and Privacy](../safety-privacy.md)。
- beta testing 请使用 [Support Runbook](../support-runbook.md) 和 [Release Checklist](../release-checklist.md)。

### Feedback / Contribution

欢迎 bug reports 和 pull requests。如果需要支持其他 controller model，请开 issue，并包含 device name、实际发生的情况和预期行为。
