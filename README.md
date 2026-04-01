[English](#english) | [한국어](#한국어) | [中文](#中文) | [日本語](#日本語)

# BBCC

## English

BBCC is a Windows-first, tray-resident controller mapping tool for creative workflows, desktop navigation, and media control. It is built for people who want quick controller-driven shortcuts without keeping the main window in the way.

The core concept is:

`Device -> App Profile -> Preset -> Button Mapping`

In practice, BBCC remembers your controller, switches behavior by active app, lets you keep multiple presets per profile, and maps controller inputs to keyboard shortcuts or other actions.

### Key Features

- App-based profile switching by foreground process name
- Per-profile presets for different workflows
- `YouTube` / media fallback profile for general media control
- Offline saved-device editing, so remembered devices stay usable even when disconnected
- Multilingual UI support
- Theme support
- Controller-aware layouts and diagrams
- Inspector and mapping editor for reviewing and adjusting bindings

### Supported Controllers

Current practical support focuses on:

- 8BitDo Zero 2
- Xbox Controller / XInput-family devices

If you want support for another controller model, please open an issue and describe the device. Additional controller support can be requested and discussed there.

### Typical Use Cases

- Creative apps such as Photoshop and Illustrator
- One-handed controller workflows
- YouTube and other media control
- Desktop navigation and shortcut handling

### Basic Usage

Clone the repository, create a virtual environment, install dependencies, and run the app:

```powershell
git clone <repository-url>
cd BBCC
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
python -m zero2_input_inspector
```

### Notes

- BBCC is a Windows-first project
- Browser-based media fallback behavior is part of the broader media workflow
- Layouts and mappings are still being refined
- Some device handling is still evolving as controller coverage expands

### Feedback / Contribution

Bug reports and pull requests are welcome. If you want support for another controller model, please open an issue and include the device name, what happened, and what you expected.

---

## 한국어

BBCC는 Windows 중심의 트레이 상주형 컨트롤러 매핑 도구로, 크리에이티브 작업, 데스크톱 이동, 미디어 제어를 위한 워크플로우에 맞춰 만들어졌습니다. 메인 창을 계속 띄워 둘 필요 없이, 컨트롤러 기반 단축키를 빠르게 쓰고 싶은 사용자를 위한 도구입니다.

핵심 개념은 다음과 같습니다.

`Device -> App Profile -> Preset -> Button Mapping`

실제로 BBCC는 컨트롤러를 기억하고, 활성 앱에 따라 동작을 전환하며, 프로필마다 여러 프리셋을 둘 수 있고, 컨트롤러 입력을 키보드 단축키나 다른 동작으로 매핑합니다.

### 주요 기능

- 포그라운드 프로세스 이름 기준의 앱별 프로필 전환
- 워크플로우별로 나눠 쓰는 프로필당 프리셋
- `YouTube` / 미디어 fallback 프로필을 통한 일반 미디어 제어
- 오프라인 저장 장치 편집 지원, 연결이 끊겨도 기억된 장치는 계속 편집 가능
- 다국어 UI 지원
- 테마 지원
- 컨트롤러를 고려한 레이아웃과 다이어그램
- 매핑을 확인하고 수정할 수 있는 Inspector와 편집기 제공

### 지원 컨트롤러

현재 실사용 기준으로는 다음 장치를 중심으로 지원합니다.

- 8BitDo Zero 2
- Xbox Controller / XInput 계열 장치

다른 컨트롤러 모델이 필요하다면 이슈를 열어 주세요. 장치 이름, 어떤 상황인지, 기대한 동작이 무엇인지 함께 적어 주시면 추가 지원을 검토할 수 있습니다.

### 일반적인 사용 예

- Photoshop, Illustrator 같은 크리에이티브 앱에서 사용
- 한 손으로 컨트롤러를 조작하는 워크플로우
- YouTube 및 기타 미디어 제어
- 데스크톱 탐색과 단축키 처리

### 기본 사용법

리포지토리를 클론하고, 가상 환경을 만든 뒤, 의존성을 설치하고 실행합니다.

```powershell
git clone <repository-url>
cd BBCC
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
python -m zero2_input_inspector
```

### 참고 사항

- BBCC는 Windows 우선 프로젝트입니다
- 브라우저 기반 미디어 fallback 동작은 전체 미디어 워크플로우의 일부입니다
- 레이아웃과 매핑은 아직 계속 다듬는 중입니다
- 컨트롤러 지원 범위가 넓어지면서 일부 장치 처리도 계속 발전하고 있습니다

### 피드백 / 기여

버그 제보와 pull request를 환영합니다. 다른 컨트롤러 모델을 지원해 달라면 이슈를 열어 장치 이름, 발생한 상황, 기대한 동작을 함께 적어 주세요.

---

## 中文

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
pip install -e .
python -m zero2_input_inspector
```

### 说明

- BBCC 是一个 Windows 优先项目
- 基于浏览器的媒体 fallback 行为属于整体媒体工作流的一部分
- 布局和映射仍在持续打磨中
- 随着设备支持范围扩展，一些设备处理逻辑也还在演进

### 反馈 / 贡献

欢迎提交 issue 和 pull request。如果你想要支持其他控制器型号，请在 issue 中提供设备名称、发生了什么、以及你期望看到什么。

---

## 日本語

BBCC は、Windows 向けのトレイ常駐型コントローラーマッピングツールです。クリエイティブ作業、デスクトップ操作、メディアコントロールに向けて設計されており、メインウィンドウを前面に出し続けずに、コントローラー中心のショートカットを使いたい人に向いています。

基本の考え方は次の通りです。

`Device -> App Profile -> Preset -> Button Mapping`

BBCC は、コントローラーを記憶し、アクティブなアプリに応じて挙動を切り替え、Profile ごとに複数の Preset を持たせ、コントローラー入力をキーボードショートカットや他の操作へ割り当てます。

### 主な機能

- フォアグラウンドのプロセス名に応じたアプリ別 Profile 切り替え
- Workflow ごとに使い分けられる Profile 単位の Preset
- `YouTube` / メディア fallback Profile による一般的なメディア操作
- オフラインでも保存済みデバイスの編集ができ、接続が切れても使い続けられる
- 多言語 UI 対応
- テーマ対応
- コントローラーを意識したレイアウトと図示
- 绑定内容を確認・調整できる Inspector とマッピング編集機能

### 対応コントローラー

現在の実用上の重点は次のデバイスです。

- 8BitDo Zero 2
- Xbox Controller / XInput 系デバイス

他のコントローラーモデルの対応を希望する場合は、issue を立ててください。デバイス名、何が起きたか、期待していた動作を添えてもらえると助かります。追加対応は issue ベースで受け付けています。

### 主な用途

- Photoshop や Illustrator などのクリエイティブアプリ
- 片手でコントローラーを使うワークフロー
- YouTube やその他メディアの操作
- デスクトップナビゲーションとショートカット操作

### 基本的な使い方

リポジトリを clone し、仮想環境を作成して依存関係をインストールし、起動します。

```powershell
git clone <repository-url>
cd BBCC
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
python -m zero2_input_inspector
```

### 補足

- BBCC は Windows 優先のプロジェクトです
- ブラウザベースのメディア fallback 動作は、メディア全体のワークフローの一部です
- レイアウトとマッピングはまだ調整の途中です
- 対応デバイスが増えるにつれて、個別のデバイス処理も今後さらに進化していきます

### フィードバック / 貢献

issue や pull request は歓迎します。別のコントローラーモデルの対応を希望する場合は、issue にデバイス名、起きたこと、期待した動作を書いてください。
