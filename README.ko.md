# 코덱스 보이스 노티

macOS·Windows용 오프라인 다국어 Codex 생명주기 음성 알림 플러그인입니다.
따뜻한 허스키 여성 음성과 낮고 밝은 남성 음성을 한국어·일본어·영어로
제공합니다.

OpenAI와 제휴하거나 OpenAI가 보증한 공식 플러그인이 아닙니다. 코드는 MIT
오픈소스이며 음성 자산에는 별도 라이선스가 적용됩니다.

## 주요 기능

- Codex 이벤트 10종을 각각 음성으로 알림
- 여성·남성 음성과 한국어·일본어·영어 조합 60개 WAV
- 완전 로컬 재생, 네트워크 통신과 텔레메트리 없음
- 프롬프트·메시지·도구 입력·출력을 저장하지 않음
- 비동기 재생 및 중복 재생 방지
- macOS에서 Python이나 Xcode Command Line Tools 없이 시스템 도구만 사용

macOS 설치:

```bash
codex plugin marketplace add battle-doll/codex-voice-notify --ref main
codex plugin add codex-voice-notify@codex-voice-notify
```

Windows PowerShell 설치:

```powershell
codex.cmd plugin marketplace add battle-doll/codex-voice-notify --ref main
codex.cmd plugin add codex-voice-notify@codex-voice-notify
```

Codex에 GitHub 저장소 링크를 주고 “이 플러그인을 설치해줘”라고 요청해도 같은
절차로 설치할 수 있습니다. 공식 디렉터리 등록 후에는 플러그인 메뉴에서 검색
설치할 수 있습니다.

## 최초 1회 설정

설치 후 플러그인의 **최초 설정 완료** 프롬프트를 선택하거나 Codex에 자연어로
요청하십시오.

> Voice Notify를 여성 한국어 음성으로 최초 설정해줘. 필요한 경우 Codex CLI도
> 확인해서 업데이트해줘.

이 프롬프트는 안전하게 다시 실행할 수 있습니다. 현재 Codex 플러그인 UI는
최초 실행 후 프롬프트를 조건부로 숨기지 않으므로 복구나 재설정을 위해 계속
표시됩니다.

최초 설정은 다음 작업을 진행합니다.

1. `/hooks`를 지원하는 Codex CLI 버전을 확인하고, 위 프롬프트처럼 명시적으로
   허용한 경우 npm 또는 Homebrew 설치를 필요에 따라 업데이트합니다.
2. 선택한 성별과 언어를 저장합니다.
3. 로컬 `Stop` 알림을 시험 재생합니다.
4. `/hooks` 안내가 표시된 Codex 터미널을 엽니다.

번들 설정 스크립트는 호환성만 확인하며 호스트 설치를 임의로 변경하지 않습니다.
Codex가 npm, Homebrew cask 또는 다른 설치 경로를 확인한 뒤 명시적으로 허용된
업데이트를 수행합니다.

터미널에서 `/hooks`를 입력하고 번들 명령을 직접 검토한 뒤 신뢰하십시오.
신뢰 처리 후에는 실제 이벤트를 테스트하기 전에 Codex를 완전히 종료하고 다시
실행해야 합니다. 플러그인은 훅 신뢰를 우회하거나 기존 Codex 알림 설정을
수정하지 않습니다.

실행 중인 CLI 파일 때문에 업데이트가 실패하면 해당 CLI를 종료하고, 안내된
업데이트 명령을 별도 터미널에서 실행한 뒤 최초 설정을 다시 시작하십시오.

## 자연어로 설정하기

평소에는 지금처럼 자연어로 요청하면 됩니다.

- “여성 영어 음성으로 바꿔줘.”
- “Voice Notify를 남성 일본어로 설정해줘.”
- “여성 한국어로 변경해줘.”
- “음성 알림을 음소거해줘.”
- “Stop 알림을 테스트해줘.”

지원하는 선택지는 여성·남성과 한국어/한글(`ko`)·일본어(`ja`)·영어(`en`)입니다.
직접 실행하려면 다음 명령을 사용할 수 있습니다.

macOS:

```bash
/bin/sh scripts/voice_notify_config.sh setup --voice female --language ko --open-hooks
/bin/sh scripts/voice_notify_config.sh set --voice female --language ko
/bin/sh scripts/voice_notify_config.sh set --voice male --language ja
/bin/sh scripts/voice_notify_config.sh test --event Stop
/bin/sh scripts/voice_notify_config.sh mute
```

Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 setup -Voice female -Language ko -OpenHooks
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice female -Language ko
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 test -Event Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 mute
```

기본값은 여성 한국어 음성, 최소 재생 간격 450ms, 이벤트 8종 활성화입니다.
지나치게 잦은 알림을 피하도록 `PreToolUse`와 `PostToolUse`는 기본적으로
꺼져 있으며 설정 명령으로 다시 켤 수 있습니다.

## 문제 해결

- `/hooks`가 인식되지 않으면 Codex CLI를 0.145.0 이상으로 업데이트하고 최초
  설정을 다시 시작하십시오.
- PowerShell이 `codex.ps1` 또는 `npm.ps1` 실행을 차단하면 `codex.cmd` 또는
  `npm.cmd`를 사용하십시오. 번들 Windows 설정 명령의
  `-ExecutionPolicy Bypass`는 해당 프로세스에만 적용되며 시스템 실행 정책을
  변경하지 않습니다.
- 시험 음성은 들리지만 실제 알림이 나오지 않으면 `/hooks`에서 훅을 검토하고
  신뢰한 다음 Codex를 완전히 재시작하십시오.

## 호환성

버전 0.1.3은 macOS와 Windows를 지원합니다. macOS에서는 Python이나 Xcode
Command Line Tools가 필요하지 않습니다. `/hooks` 안내가 포함된 최초 설정은
Codex CLI 0.145.0 이상이 필요합니다. Linux는 아직 지원하지 않습니다.

코드는 MIT 라이선스입니다. `assets/audio/`의 WAV에는 MIT가 적용되지 않으며
[ASSET_LICENSE.md](ASSET_LICENSE.md)의 별도 조건을 따릅니다. 남성 알림
세트 대부분은 Fish Audio로 생성되었고, 한국어 서브 에이전트 파일 2개는
현재 문구에 맞게 Qwen Base로 재생성했습니다. 비상업용 자산 경계와 상세
출처는 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)에 기록되어
있습니다.
