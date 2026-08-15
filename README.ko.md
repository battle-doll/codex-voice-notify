# Voice Notify for Codex

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

macOS와 Windows에서 Codex 생명주기 이벤트 10종을 알려 주는 오프라인 다국어
음성 알림 플러그인입니다. 한국어·일본어·영어·러시아어·중국어 간체 중에서
따뜻한 허스키 음성이나 낮고 밝은 음성을 선택할 수 있습니다.

이 플러그인은 OpenAI와 제휴하거나 OpenAI가 보증한 제품이 아닌 독립
플러그인입니다. 소스 코드는 MIT 라이선스이며 음성 자산에는 별도 라이선스가
적용됩니다.

## 주요 기능

플러그인은 다음 이벤트마다 로컬 WAV를 재생합니다.

- `SessionStart`
- `UserPromptSubmit`
- `PreToolUse`
- `PostToolUse`
- `PermissionRequest`
- `PreCompact`
- `PostCompact`
- `SubagentStart`
- `SubagentStop`
- `Stop`

버전 0.1.6에는 음성 프로필 2종, 언어 5종, 생명주기 이벤트 10종의 모든 조합인
100 WAV 파일이 포함됩니다. 이번 패치는 영어·한국어·일본어·중국어 간체·
러시아어 README 전체를 제공합니다. 음성 자산과 런타임 동작은 0.1.5와
같습니다.

macOS에 기본 포함된 `/bin/sh`, `plutil`, `afplay`, `osascript`를 사용하며,
Windows에서는 PowerShell과 `System.Media.SoundPlayer`를 사용합니다. Python이나
Xcode Command Line Tools가 필요하지 않습니다. 네트워크 코드와 텔레메트리가
없으며 프롬프트·메시지·도구 입력·도구 출력을 저장하지 않습니다. 재생은
비동기이며 로컬 잠금과 짧은 재생 간격으로 음성이 겹치지 않게 합니다.

### 대화형 코드 온톨로지

[이 저장소의 대화형 코드 온톨로지 열기](https://rawcdn.githack.com/battle-doll/codex-voice-notify/ce42d10e88fc490271bea2c123a611bfa3d12b13/codex-voice-notify-code-ontology.html)를
선택하면 [Code Ontology Companion](https://github.com/battle-doll/code-ontology-companion)으로
Voice Notify `0.1.6`을 분석해 생성한 결과를 볼 수 있습니다.
[저장소에 게시된 HTML 원본](https://github.com/battle-doll/codex-voice-notify/blob/code-ontology-showcase/codex-voice-notify-code-ontology.html)도
직접 확인할 수 있습니다.

이 자체 완결형 스냅샷은 Python 파일 6개를 노드 417개와 관계 769개로
구성하며, 파싱 경고는 0개이고 모든 관계에 추출 근거와 소스 위치가 포함됩니다.
기호 검색, 호출자·종속성 확인, 2D 구조와 3D 별자리 보기, 관계별 규칙·근거·
런타임 상태·소스 위치·한계를 탐색할 수 있습니다.

이는 런타임 증명이 아니라 정적 분석 근거입니다. 실제 Windows와 macOS 훅
진입점은 PowerShell 및 POSIX shell이므로 이 Python 스냅샷의 adapter 범위
밖입니다. 게시에는 명시적인 승인을 받았습니다. 미리보기는 HTML content type을
제공하기 위해 raw.githack만 사용하며, 워크벤치 자체에는 런타임 CDN 또는
네트워크 종속성이 없습니다.

## GitHub에서 설치

Codex에 저장소 URL을 주고 플러그인 설치를 요청하거나 다음 명령을 실행합니다.

macOS:

```bash
codex plugin marketplace add battle-doll/codex-voice-notify --ref main
codex plugin add codex-voice-notify@codex-voice-notify
```

Windows PowerShell:

```powershell
codex.cmd plugin marketplace add battle-doll/codex-voice-notify --ref main
codex.cmd plugin add codex-voice-notify@codex-voice-notify
```

## 최초 설정

설치 후 플러그인의 **최초 설정 완료** 프롬프트를 선택하거나 Codex에 자연어로
요청합니다.

> Voice Notify를 여성 한국어 음성으로 최초 설정해줘. 필요한 경우 Codex CLI를
> 확인하고 업데이트해줘.

이 시작 프롬프트는 안전하게 반복 실행할 수 있습니다. 현재 Codex 플러그인 UI는
첫 실행 후 프롬프트를 조건부로 숨기지 않으므로 복구하거나 설정을 다시 할 때도
계속 사용할 수 있습니다.

안내식 설정은 다음 작업을 수행합니다.

1. `/hooks`를 지원하는 Codex CLI 버전을 확인하고, 설정 프롬프트에서 명시적으로
   허용한 경우에만 npm 또는 Homebrew 설치를 필요에 따라 업데이트합니다.
2. 선택한 음성과 언어를 저장합니다.
3. 로컬 `Stop` 알림을 시험 재생합니다.
4. 새 터미널 창을 열어 확인된 Codex CLI를 그 안에서 시작합니다. 단순히
   `/hooks` 입력 안내만 출력하지 않습니다.

번들 설정 스크립트 자체는 호환성만 보고하며 호스트 설치를 수정하지 않습니다.
Codex는 CLI가 npm, Homebrew cask 또는 다른 경로에서 설치되었는지 확인한 다음,
사용자가 허용한 업데이트만 수행합니다.

새로 열린 Codex CLI 터미널에서 `/hooks`를 입력하고 번들 명령을 검토한 뒤 직접
신뢰하십시오. 그 다음 Codex를 완전히 종료하고 다시 실행한 후 실제 생명주기
이벤트를 시험합니다. 훅 신뢰는 저장되지만 이미 실행 중인 Codex 프로세스에는
다음 시작 전까지 새로 신뢰한 플러그인 훅이 활성화되지 않을 수 있습니다.
Codex는 설치 시 서드파티 훅을 자동으로 신뢰하지 않으며, 이 플러그인도 해당
검토 절차를 우회하지 않습니다.

실행 중인 CLI 파일을 교체하지 못해 업데이트가 실패하면 해당 CLI를 종료하고,
표시된 업데이트 명령을 별도 터미널에서 실행한 뒤 설정을 다시 시작하십시오.

## 설정

언제든 자연어로 요청할 수 있습니다. 예:

- “여성 영어 음성으로 바꿔줘.”
- “Voice Notify를 남성 일본어로 설정해줘.”
- “여성 러시아어 음성으로 바꿔줘.”
- “Voice Notify를 남성 중국어 간체로 설정해줘.”
- “여성 한국어 음성으로 바꿔줘.”
- “Voice Notify를 음소거해줘.”
- “Stop 알림을 테스트해줘.”

Codex는 `female` 또는 `male`과 한국어/한글(`ko`)·일본어(`ja`)·영어(`en`)·
러시아어(`ru`)·중국어 간체(`zh-CN`)를 번들 설정 명령에 매핑합니다. 번들된
중국어 변형은 `zh-CN` 하나이므로 변형을 지정하지 않은 “중국어” 또는 “中文”
요청은 `zh-CN`(중국어 간체·중국 본토 표준중국어)으로 매핑합니다. 저장소를
복제한 뒤 다음 명령을 직접 실행할 수도 있습니다.

macOS:

```bash
/bin/sh scripts/voice_notify_config.sh setup --voice female --language ko --open-hooks
/bin/sh scripts/voice_notify_config.sh show
/bin/sh scripts/voice_notify_config.sh set --voice female --language ko
/bin/sh scripts/voice_notify_config.sh set --voice male --language en
/bin/sh scripts/voice_notify_config.sh set --voice female --language ru
/bin/sh scripts/voice_notify_config.sh set --voice male --language zh-CN
/bin/sh scripts/voice_notify_config.sh test --event Stop
/bin/sh scripts/voice_notify_config.sh mute
```

Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 setup -Voice female -Language ko -OpenHooks
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 show
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice female -Language ko
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice male -Language ru
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice female -Language zh-CN
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 test -Event Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 mute
```

기본값은 `female`, `ko`, 최소 재생 간격 450ms, 이벤트 8종 활성화입니다.
도구마다 알림이 울리지 않도록 `PreToolUse`와 `PostToolUse`는 사용할 수 있지만
기본적으로 꺼져 있습니다. `PermissionRequest`는 Codex가 실제로 권한을 요청할
때만 재생됩니다.

## 문제 해결

- `/hooks`가 인식되지 않으면 Codex CLI를 `0.145.0` 이상으로 업데이트하고
  설정을 다시 시작하십시오.
- PowerShell이 `codex.ps1` 또는 `npm.ps1`을 차단하면 `codex.cmd` 또는
  `npm.cmd`를 사용하십시오. 번들 Windows 설정 명령의
  `-ExecutionPolicy Bypass`는 해당 프로세스에만 적용되며 시스템 실행 정책을
  변경하지 않습니다.
- 시험 음성은 들리지만 생명주기 알림이 나오지 않으면 `/hooks`에서 훅을
  검토하고 신뢰한 다음 Codex를 완전히 다시 시작하십시오.

## 호환성

버전 0.1.6은 시스템 기본 오디오 및 스크립트 구성 요소를 사용하는 macOS와
Windows를 지원합니다. macOS에서는 Python이나 Xcode Command Line Tools가
필요하지 않습니다. 훅 안내식 설정에는 Codex CLI `0.145.0` 이상이 필요합니다.
Linux는 아직 지원하지 않습니다.

## 라이선스

소스 코드는 MIT 라이선스입니다. `assets/audio/` 아래의 모든 WAV 파일에는 MIT
라이선스가 적용되지 않습니다. [ASSET_LICENSE.md](ASSET_LICENSE.md)의 제한적
사용 허락에 따라, 해당 파일은 수정하지 않은 상태로, 수정하지 않은 무료 Voice
Notify for Codex 사본의 일부로서, 개인적·비상업적 알림 재생 용도로만 사용·복사·
재배포할 수 있습니다.

[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)는 생성 출처만 기록합니다.
남성 알림 세트 대부분은 Fish Audio로 생성되었고, 한국어 서브 에이전트 파일 2개는
현재 문구와 일치하도록 Qwen Base로 다시 생성되었습니다. 이러한 출처 정보는 음성
자산의 사용 조건을 변경하지 않습니다.
