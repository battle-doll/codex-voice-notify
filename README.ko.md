# 코덱스 보이스 노티

macOS·Windows용 오프라인 다국어 Codex 생명주기 음성 알림 플러그인입니다.
밝고 따뜻한 여성 음성과 낮고 밝은 남성 음성을 한국어·일본어·영어로 제공합니다.

OpenAI와 제휴하거나 OpenAI가 보증한 공식 플러그인이 아닙니다. 코드는 MIT
오픈소스이며 음성 자산에는 별도 라이선스가 적용됩니다.

## 주요 기능

- Codex 이벤트 10종을 각각 음성으로 알림
- 여성·남성 음성과 한국어·일본어·영어 조합 60개 WAV
- 완전 로컬 재생, 네트워크 통신과 텔레메트리 없음
- 프롬프트·메시지·도구 입력·출력을 저장하지 않음
- 비동기 재생 및 중복 재생 방지

설치:

```bash
codex plugin marketplace add battle-doll/codex-voice-notify --ref main
codex plugin add codex-voice-notify@codex-voice-notify
```

Codex에 GitHub 저장소 링크를 주고 “이 플러그인을 설치해줘”라고 요청해도 같은
절차로 설치할 수 있습니다. 공식 디렉터리 등록 후에는 플러그인 메뉴에서 검색
설치할 수 있습니다.

설치 후 Codex를 재시작하고 `/hooks`에서 명령을 직접 검토한 뒤 신뢰해야 합니다.
기존 Codex 알림 설정은 수정하지 않습니다.

설정 예:

```bash
/usr/bin/python3 scripts/voice_notify_config.py set --voice female --language ko
/usr/bin/python3 scripts/voice_notify_config.py set --voice male --language ja
/usr/bin/python3 scripts/voice_notify_config.py test --event Stop
/usr/bin/python3 scripts/voice_notify_config.py mute
```

Windows에서는 `scripts\voice_notify_config.ps1`을 사용합니다.

코드는 MIT 라이선스입니다. `assets/audio/`의 WAV에는 MIT가 적용되지 않으며
[ASSET_LICENSE.md](ASSET_LICENSE.md)의 별도 조건을 따릅니다.
