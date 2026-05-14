# BBCC

> Windows-first controller mapping for creative shortcuts, desktop navigation, and media control.

[Overview](../../README.md) | [English](README.en.md) | [한국어](README.ko.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md)

BBCC 是一个面向 Windows 的、常驻托盘的控制器映射工具，适合创意工作流、桌面导航和媒体控制。它面向那些想用手柄快速执行快捷操作、又不想让主窗口一直挡在眼前的用户。

核心概念是：

`Device -> App Profile -> Preset -> Button Mapping`

实际使用中，BBCC 会记住你的控制器，按当前应用切换行为，在每个 Profile 里保留多个 Preset，并把控制器输入映射到键盘快捷键或其他动作。

### 主要功能

- 按前台进程名切换应用 Profile
- 每个 Profile 支持多个 Preset，便于分工作流使用
- 提供 `YouTube` / 媒体 fallback Profile，用于通用媒体控制
- 支持离线已保存设备编辑，设备断开后仍可继续使用
- 支持多语言界面
- 支持主题切换
- 提供适配控制器的布局和图示
- 提供 Inspector 和映射编辑器，方便查看与调整绑定

### 支持的控制器

当前重点支持以下设备：

- 8BitDo Zero 2
- Xbox Controller / XInput 系列设备

如果你希望支持其他控制器型号，欢迎提交 issue，并说明设备名称、出现了什么情况，以及你期望的结果。其他控制器支持也可以通过 issue 申请和讨论。

### 常见用途

- Photoshop、Illustrator 等创意软件
- 单手控制器工作流
- YouTube 和其他媒体控制
- 桌面导航与快捷操作

### 基本用法

先克隆仓库，创建虚拟环境，安装依赖，然后运行程序：

```powershell
git clone <repository-url>
cd BBCC
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python -m zero2_input_inspector
```

### 演示流程

这个演示会选择已连接的 `8BitDo Zero 2 gamepad`，查看按钮映射表，检查 Inspector 中的原始输入值，然后打开应用 Profile 设置。

1. 运行 `dist\BBCC.exe`。
2. 在首屏确认控制器显示为 `Connected`。
3. 单击已连接的设备行。
4. 在 `button_mappings` 表中查看每个按钮的快捷键和标签。
5. 选择某个按钮行后，可在下方的 `mapping_editor` 中修改快捷键和标签。
6. 点击右上角的 `Inspector`，查看 raw axes、raw buttons、raw hats、backend 和 GUID。
7. 在 `Profile Settings` 中管理 fallback Profile 以及按进程名匹配的应用 Profile。

首屏会确认控制器已被检测并连接。选择已保存的设备行即可打开它的映射设置。

![已连接的控制器](../demo-screenshots/controller-live-01-device-detected.png)

映射视图会显示当前应用 Profile、按钮绑定、标签，以及用于调整所选绑定的编辑区域。

![8BitDo Zero 2 映射表](../demo-screenshots/controller-live-03-connected-mapping.png)

点击 `Inspector` 可打开实时原始输入值，包括 axes、buttons、hats、backend 信息和设备 GUID。

![原始输入 Inspector](../demo-screenshots/controller-live-04-inspector.png)

`Profile Settings` 会打开应用 Profile 编辑器，可在其中设置 fallback Profile 和特定应用 Profile 的名称与进程匹配规则。

![应用 Profile 设置](../demo-screenshots/controller-live-05-profile-settings.png)

### 说明

- BBCC 是一个 Windows 优先项目
- 基于浏览器的媒体 fallback 行为属于整体媒体工作流的一部分
- 布局和映射仍在持续打磨中
- 随着设备支持范围扩展，一些设备处理逻辑也还在演进

### 反馈 / 贡献

欢迎提交 issue 和 pull request。如果你想要支持其他控制器型号，请在 issue 中提供设备名称、发生了什么、以及你期望看到什么。
