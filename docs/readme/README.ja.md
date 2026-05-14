# BBCC

> Windows-first controller mapping for creative shortcuts, desktop navigation, and media control.

[Overview](../../README.md) | [English](README.en.md) | [한국어](README.ko.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md)

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
- 割り当て内容を確認・調整できる Inspector とマッピング編集機能

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
pip install -r requirements-dev.txt
python -m zero2_input_inspector
```

### デモ手順

このデモでは、接続された `8BitDo Zero 2 gamepad` を選択し、マッピング表、Inspector の raw input、アプリ別 Profile 設定を順番に確認します。

1. `dist\BBCC.exe` を実行します。
2. 最初の画面でコントローラーが `Connected` と表示されていることを確認します。
3. 接続済みデバイスの行をクリックします。
4. `button_mappings` 表で、ボタンごとのショートカットとラベルを確認します。
5. 表のボタン行を選択すると、下の `mapping_editor` でショートカットとラベルを編集できます。
6. 右上の `Inspector` をクリックし、raw axes、raw buttons、raw hats、backend、GUID の値を確認します。
7. `Profile Settings` で、fallback Profile とアプリ別 Profile の名前やプロセス名を管理します。

最初の画面では、コントローラーが検出されて接続済みであることを確認します。保存済みデバイスの行を選択すると、そのデバイスのマッピング画面が開きます。

![接続されたコントローラー](../demo-screenshots/controller-live-01-device-detected.png)

マッピング画面では、現在のアプリ Profile、ボタン割り当て、ラベル、選択した割り当てを編集する領域を確認できます。

![8BitDo Zero 2 マッピング表](../demo-screenshots/controller-live-03-connected-mapping.png)

`Inspector` を開くと、axes、buttons、hats などの raw input 値と、backend 情報、デバイス GUID が表示されます。

![Raw input Inspector](../demo-screenshots/controller-live-04-inspector.png)

`Profile Settings` では、`YouTube` のような fallback Profile やアプリ別 Profile の名前、プロセス名を管理できます。

![アプリ Profile 設定](../demo-screenshots/controller-live-05-profile-settings.png)

### 補足

- BBCC は Windows 優先のプロジェクトです
- ブラウザベースのメディア fallback 動作は、メディア全体のワークフローの一部です
- レイアウトとマッピングはまだ調整の途中です
- 対応デバイスが増えるにつれて、個別のデバイス処理も今後さらに進化していきます

### フィードバック / 貢献

issue や pull request は歓迎します。別のコントローラーモデルの対応を希望する場合は、issue にデバイス名、起きたこと、期待した動作を書いてください。
