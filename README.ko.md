# Voice Notify for Codex

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

Codex가 주의를 요구하거나 작업을 마쳤을 때 비공개 로컬 음성으로 알려 줍니다.
macOS, Windows, Linux를 지원합니다.

### 사용

- GitHub에서 설치한 뒤 `Voice Notify를 여성 한국어 음성으로 최초 설정해줘. 훅 내용을 설명하고 승인 전에 물어봐줘.`라고 요청합니다.
- Codex가 호환성과 오디오를 확인하고 설정을 저장한 뒤 정확한 Voice Notify 훅 명령을 보여 줍니다. 내용을 검토하고 승인하면 Codex의 공식 로컬 인터페이스로 승인 처리를 자동화할 수 있습니다.
- 음성, 언어, 생명주기 이벤트, 재생 간격을 선택하고 언제든 시험·음소거·음소거 해제할 수 있습니다.

### 사용해 보기

- `Codex가 권한을 요청하거나 끝나면 여성 영어 음성으로 알려줘.`
- `Codex 업데이트 후 Voice Notify가 안 되는 원인을 확인해줘.`
- `로컬 Stop 알림을 시험한 뒤 Voice Notify를 음소거해줘.`

### 주요 경계

- 재생은 오프라인이며 대화 내용을 보관하거나 전송하지 않습니다.
- Codex 생명주기 음성 설정만 다룹니다. 일반 TTS·내레이션, 음성 전사, 클라우드 알림, 임의의 OS 오디오 자동화, 스크린샷 작업 추출에는 사용하지 않습니다.
- 훅 승인에는 사용자 검토와 동의가 필요합니다. 검토한 Voice Notify 훅만 승인하며 다른 훅과 알림 설정은 변경하지 않습니다.

2026-10-03 확인: OpenAI Platform의 기존 0.1.7 항목은 **Published**입니다. 0.2.0은 제출하지 않았으며 현재 디렉터리 검색·목록 노출은 미확인입니다. 과거 기록 — Verified on 2026-08-29: 카탈로그의 **GLOBAL/AVAILABLE**, **UNLISTED**는 과거 스냅샷이며 현재 노출 상태의 증거가 아닙니다. [기존 항목](https://chatgpt.com/plugins/plugins_6a6600dd92148191a6dfe0c16eb85c83).

2026-10-03 확인한 [OpenAI 제출 문서](https://developers.openai.com/plugins/deploy/submission)는 생명주기 훅 ZIP의 제출을 현재 허용하지 않습니다. 0.2.0은 준비된 업데이트 후보이며 공개 제출은 보류 중입니다. [SUBMISSION.md](SUBMISSION.md)를 참고하십시오.

OpenAI와 제휴하거나 OpenAI가 보증한 제품이 아닌 독립 플러그인입니다. 소스 코드는 MIT 라이선스이며 음성 자산에는 별도 라이선스가 적용됩니다.

## 주요 기능

다음 이벤트마다 로컬 WAV를 재생합니다.

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

버전 0.2.0에는 음성 프로필 2종, 언어 5종, 이벤트 10종의 모든 조합인 100 WAV 파일이 포함됩니다. 음성 자산과 기본값은 같습니다. 최신 Codex prerelease 버전 표기 지원, 읽기 전용 진단, 사용자 동의 후 훅 승인 처리 및 Linux 재생을 추가했습니다.

macOS의 일반 재생·설정은 기본 제공 `/bin/sh`, `plutil`, `afplay`, `osascript`를 사용하며 Python이나 Xcode Command Line Tools가 필요하지 않습니다. Windows는 PowerShell과 `System.Media.SoundPlayer`를 사용합니다. Linux는 Python 3 표준 라이브러리와 `pw-play`, `paplay`, `aplay`, `ffplay` 중 먼저 설치되어 있는 재생기를 사용합니다. 오디오 패키지는 자동 설치하지 않습니다. 런타임 재생에는 네트워크 코드와 텔레메트리가 없으며 프롬프트·메시지·도구 입력·도구 출력을 저장하지 않습니다. 로컬 잠금과 짧은 재생 간격으로 음성 겹침을 방지합니다.

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

이것은 과거 0.1.6 스냅샷이며 0.2.0의 Linux·훅 승인 변경을 반영해 다시 생성한 결과가 아닙니다.

## GitHub에서 설치

macOS / Linux:

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

Codex는 사용자의 대화 언어로 설치를 안내하며 음성 언어 5종(한국어·영어·일본어·러시아어·중국어 간체)과 여성·남성 목소리를 보여 줍니다. 안내 언어와 알림 음성 언어는 따로 선택할 수 있습니다. 기존 설정과 명시한 선택을 유지하고 미지정 항목만 간단히 묻습니다. 신규 설정은 여성 목소리와 사용자의 지원 음성 언어를 제안하며, 해당 음성이 없으면 한국어를 제안합니다. 스크립트의 기본값 `female/ko`는 바뀌지 않습니다. 훅 검토·동의·실제 청취 확인도 사용자 언어로 안내합니다.

설치 후 **최초 설정 완료** 프롬프트를 선택하거나 다음과 같이 요청합니다.

> Voice Notify를 여성 한국어 음성으로 최초 설정해줘. 훅 내용을 설명하고 승인 전에 물어봐줘.

반복 가능한 안내식 설정 순서입니다.

1. 읽기 전용 `doctor`로 선택한 Codex CLI, 버전, 오디오 재생기, 설정을 확인합니다. Codex CLI `0.145.0` 이상이 필요하며 최신 prerelease 접미사도 인식합니다.
2. 선택한 음성과 언어를 저장하고 로컬 `Stop` 알림을 시험합니다. 실제로 들렸는지 확인합니다.
3. `review-hooks`로 정확한 Voice Notify 명령·승인 범위·`approvalDigest` 값을 보여 주고 해당 명령의 승인을 요청합니다.
4. 사용자가 명시적으로 승인한 뒤 그 `approvalDigest` 값으로 `approve-hooks`를 실행합니다. Codex의 공식 로컬 app-server 인터페이스가 검토한 Voice Notify 훅만 승인합니다. 명령이 바뀌면 다시 검토해야 하며 신뢰 저장소를 직접 수정하거나 검토를 우회하지 않습니다.
5. Codex를 완전히 종료하고 다시 실행한 뒤 활성 이벤트 하나의 음성을 실제로 듣습니다. 설정 시험이나 승인 영수증만으로 실제 생명주기 재생 성공을 단정하지 않습니다.

자동 승인 인터페이스가 없으면 macOS/Linux의 `setup --open-hooks` 또는 Windows의 `setup -OpenHooks`로 보이는 Codex CLI 터미널을 엽니다. 여기서 `/hooks`를 입력하고 번들 명령을 검토한 뒤 명시적으로 신뢰하십시오. Codex를 완전히 종료하고 다시 실행한 후 실제 이벤트를 시험합니다. headless 환경이거나 터미널 실행기가 없으면 선택한 CLI를 직접 시작하고 `/hooks`를 입력합니다.

스크립트는 Codex나 의존성을 조용히 설치·업데이트하지 않습니다. CLI가 오래되었다면 별도 업데이트를 명시적으로 허용한 경우에만 설치 출처를 확인한 npm·Homebrew 설치를 업데이트합니다. 데스크톱 번들이나 알 수 없는 설치는 해당 설치의 공식 업데이트 경로를 사용합니다. 실행 파일이 사용 중이면 해당 CLI를 종료한 뒤 업데이트합니다.

## 설정

“여성 영어 음성으로 바꿔줘”, “남성 일본어로 설정해줘”, “여성 러시아어 음성으로 바꿔줘”, “남성 중국어 간체로 설정해줘”, “Voice Notify를 음소거해줘”처럼 자연어로 요청할 수 있습니다.

`female` 또는 `male`과 한국어/한글(`ko`), 일본어(`ja`), 영어(`en`), 러시아어(`ru`), 중국어 간체(`zh-CN`)를 번들 설정에 매핑합니다. 일반적인 “중국어”·“中文”는 유일한 중국어 변형인 `zh-CN`(중국어 간체·중국 본토 표준중국어)으로 매핑합니다. 저장소 복제본에서 직접 실행하는 명령:

macOS:

```bash
/bin/sh scripts/voice_notify_config.sh doctor
/bin/sh scripts/voice_notify_config.sh setup --voice female --language ko
/bin/sh scripts/voice_notify_config.sh review-hooks
# 명시적 승인 후 <approvalDigest>를 현재 검토에서 반환된 값으로 바꿉니다:
/bin/sh scripts/voice_notify_config.sh approve-hooks --approve "<approvalDigest>"
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
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 doctor
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 setup -Voice female -Language ko
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 review-hooks
# 명시적 승인 후 <approvalDigest>를 현재 검토에서 반환된 값으로 바꿉니다:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 approve-hooks -Approve "<approvalDigest>"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 show
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice female -Language ko
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice male -Language ru
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice female -Language zh-CN
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 test -Event Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 mute
```

Linux:

```bash
python3 scripts/voice_notify_config.py doctor
python3 scripts/voice_notify_config.py setup --voice female --language ko
python3 scripts/voice_notify_config.py review-hooks
# 명시적 승인 후 <approvalDigest>를 현재 검토에서 반환된 값으로 바꿉니다:
python3 scripts/voice_notify_config.py approve-hooks --approve "<approvalDigest>"
python3 scripts/voice_notify_config.py show
python3 scripts/voice_notify_config.py set --voice male --language en
python3 scripts/voice_notify_config.py test --event Stop
python3 scripts/voice_notify_config.py mute
```

기본값은 `female`, `ko`, 최소 재생 간격 450ms, 이벤트 8종 활성화입니다. `PreToolUse`와 `PostToolUse`는 사용 가능하지만 기본적으로 꺼져 있습니다. `PermissionRequest`는 Codex가 실제로 권한을 요청할 때만 재생됩니다.

## 문제 해결

- `doctor`를 먼저 실행합니다. 진단은 설정을 바꾸거나 훅을 승인하거나 오디오를 재생하지 않습니다. 로컬 출력에 경로가 포함될 수 있으므로 공유 전 가리십시오.
- `/hooks`가 없다면 선택한 CLI와 버전을 확인하고 사용자 승인 후 업데이트합니다. 데스크톱 앱과 별도 CLI는 서로 다른 버전일 수 있습니다.
- 시험 음성만 들리면 훅 승인 상태를 확인하고 해당 Codex 프로세스를 완전히 종료·재실행한 뒤 활성 실제 이벤트를 시험합니다.
- PowerShell이 `codex.ps1`·`npm.ps1`을 차단하면 `codex.cmd`·`npm.cmd`를 사용합니다. `-ExecutionPolicy Bypass`는 설정 프로세스에만 적용되며 시스템 정책을 바꾸지 않습니다.
- Linux에는 Python 3, 지원 재생기, 접근 가능한 오디오 장치·서버가 필요합니다. SSH·컨테이너·WSL·headless 환경은 재생기가 있어도 실제 소리가 들리지 않을 수 있습니다. 패키지는 자동 설치하지 않습니다.

## 호환성

버전 0.2.0은 macOS, Windows, Linux를 지원합니다. macOS 일반 재생·설정에는 Python이 필요 없고 Windows는 기본 PowerShell을 사용합니다. Linux에는 Python 3와 지원 로컬 재생기 하나가 필요합니다. 훅 승인 자동화는 macOS 기본 `osascript` JXA, Windows 기본 PowerShell, Linux Python 3를 사용하며 선택한 CLI의 공식 로컬 app-server 인터페이스가 필요합니다. 해당 인터페이스가 없으면 `/hooks` 수동 검토를 사용합니다. Codex CLI `0.145.0` 이상이 필요합니다. 지원 표기는 모든 데스크톱 릴리스·오디오 환경·headless 세션의 실제 청취 검증을 뜻하지 않습니다.

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
