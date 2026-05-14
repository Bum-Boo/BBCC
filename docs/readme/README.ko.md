# BBCC

> Windows-first controller mapping for creative shortcuts, desktop navigation, and media control.

[Overview](../../README.md) | [English](README.en.md) | [한국어](README.ko.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md)

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
pip install -r requirements-dev.txt
python -m zero2_input_inspector
```

### 데모 흐름

실제 데모는 연결된 `8BitDo Zero 2 gamepad`를 선택하고, 매핑 표와 raw input Inspector를 확인한 뒤 앱별 프로필 설정을 여는 흐름입니다.

1. `dist\BBCC.exe`를 실행합니다.
2. 첫 화면에서 컨트롤러가 `Connected`로 표시되는지 확인합니다.
3. 연결된 장치 행을 클릭합니다.
4. `button_mappings` 표에서 버튼별 단축키와 라벨을 확인합니다.
5. 표의 버튼 행을 선택하면 아래 `mapping_editor`에서 단축키와 라벨을 수정할 수 있습니다.
6. 오른쪽 위 `Inspector`를 눌러 raw axes, raw buttons, raw hats, backend, GUID 값을 확인합니다.
7. `Profile Settings`에서 fallback 프로필과 앱별 프로필의 이름, 프로세스명을 관리합니다.

첫 화면에서는 컨트롤러가 `Connected`로 표시되는지 확인합니다. 저장된 장치 행을 선택하면 해당 컨트롤러의 매핑 화면으로 들어갑니다.

![연결된 컨트롤러 감지](../demo-screenshots/controller-live-01-device-detected.png)

매핑 화면에서는 현재 프로필, 버튼별 단축키, 라벨, 선택한 버튼을 수정하는 편집 영역을 확인합니다.

![8BitDo Zero 2 매핑 표](../demo-screenshots/controller-live-03-connected-mapping.png)

오른쪽 위 `Inspector`를 누르면 axes, buttons, hats 같은 raw input 값과 장치 GUID/백엔드 정보가 표시됩니다.

![Raw input Inspector](../demo-screenshots/controller-live-04-inspector.png)

`Profile Settings`에서는 `YouTube` 같은 fallback 프로필이나 앱별 프로필 이름과 프로세스명을 관리합니다.

![앱 프로필 설정](../demo-screenshots/controller-live-05-profile-settings.png)

### 참고 사항

- BBCC는 Windows 우선 프로젝트입니다
- 브라우저 기반 미디어 fallback 동작은 전체 미디어 워크플로우의 일부입니다
- 레이아웃과 매핑은 아직 계속 다듬는 중입니다
- 컨트롤러 지원 범위가 넓어지면서 일부 장치 처리도 계속 발전하고 있습니다

### 피드백 / 기여

버그 제보와 pull request를 환영합니다. 다른 컨트롤러 모델을 지원해 달라면 이슈를 열어 장치 이름, 발생한 상황, 기대한 동작을 함께 적어 주세요.
