# BBCC

> クリエイティブショートカット、デスクトップ操作、メディア操作向けの Windows-first controller mapping tool。

[Overview](../../README.md) | [English](README.en.md) | [한국어](README.ko.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md)

BBCC は creative workflows、desktop navigation、media control のための Windows-first、tray-resident controller mapping tool です。メインウィンドウを邪魔にせず、controller-driven shortcut を素早く使いたいユーザー向けに作られています。

中心概念は次の通りです。

`Device -> App Profile -> Preset -> Button Mapping`

実際には、BBCC は controller を記憶し、active app に応じて behavior を切り替え、profile ごとに複数 preset を保持し、controller inputs を keyboard shortcuts や他の actions に mapping します。

### Key Features

- foreground process name による app-based profile switching。
- workflow ごとの per-profile presets。
- 一般的な media control 向けの `YouTube` / media fallback profile。
- controller が未接続でも remembered devices を編集できる offline saved-device editing。
- Multilingual UI support。
- Theme support。
- Controller-aware layouts and diagrams。
- binding を確認・調整する Inspector と mapping editor。

### Supported Controllers

現在の実用サポートは次を中心にしています。

- 8BitDo Zero 2
- Xbox Controller / XInput-family devices

別の controller model のサポートが必要な場合は issue を開き、device name、起きたこと、期待した動作を書いてください。

### Typical Use Cases

- Photoshop や Illustrator などの creative apps。
- 片手 controller workflows。
- YouTube やその他 media control。
- Desktop navigation と shortcut handling。

### Download / Release

Windows build と release note は [../download-release.md](../download-release.md) を参照してください。stable release と prerelease asset を分けて案内しています。

### Basic Usage

repository を clone し、virtual environment を作成し、dependencies を install してアプリを実行します。

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

demo flow では接続された `8BitDo Zero 2 gamepad` を選び、mapping table を確認し、Inspector で raw input を見て、app-profile settings を開きます。

1. `dist\BBCC.exe` を実行します。
2. 最初の画面で controller が `Connected` と表示されていることを確認します。
3. connected device row をクリックします。
4. `button_mappings` table で shortcut assignments と labels を確認します。
5. button row を選択し、`mapping_editor` で shortcut と label を編集します。
6. 右上の `Inspector` をクリックして axes、buttons、hats、backend、GUID values を確認します。
7. `Profile Settings` を開き、process name による fallback と app-specific profiles を管理します。

最初の画面は controller が検出され接続されたことを示します。remembered device row を選ぶと mappings が開きます。

![Connected controller detected](../demo-screenshots/controller-live-01-device-detected.png)

mapping view には active app profile、button bindings、labels、selected binding を調整する editor panel が表示されます。

![8BitDo Zero 2 mapping table](../demo-screenshots/controller-live-03-connected-mapping.png)

`Inspector` button は axes、buttons、hats、backend information、device GUID details を含む live raw input values を開きます。

![Raw input inspector](../demo-screenshots/controller-live-04-inspector.png)

`Profile Settings` では fallback と app-specific profiles を process name で naming/matching できます。

![App profile settings](../demo-screenshots/controller-live-05-profile-settings.png)

### Notes

- BBCC は Windows-first project です。
- Browser-based media fallback behavior は広い media workflow の一部です。
- Layouts と mappings はまだ refinement 中です。
- Controller coverage が広がるにつれて、一部の device handling は進化中です。
- 実作業で global keyboard や mouse mappings を使う前に [Safety and Privacy](../safety-privacy.md) を読んでください。
- beta testing には [Support Runbook](../support-runbook.md) と [Release Checklist](../release-checklist.md) を使ってください。

### Feedback / Contribution

Bug reports と pull requests を歓迎します。別の controller model のサポートが必要な場合は、device name、実際の動作、期待した動作を issue に書いてください。
