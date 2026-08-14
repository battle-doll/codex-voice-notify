#!/usr/bin/env python3
"""Run the minimal release checks for a Voice Notify package."""

from __future__ import annotations

import array
import hashlib
import json
import math
import pathlib
import re
import statistics
import struct
import sys
import wave
from urllib.parse import urlparse


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_EVENTS = frozenset({
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PostToolUse",
    "PermissionRequest",
    "PreCompact",
    "PostCompact",
    "SubagentStart",
    "SubagentStop",
    "Stop",
})
EXPECTED_VOICES = frozenset(("female", "male"))
EXPECTED_LANGUAGES = frozenset(("ko", "ja", "en", "ru", "zh-CN"))
EXPECTED_ASSET_COUNT = (
    len(EXPECTED_VOICES) * len(EXPECTED_LANGUAGES) * len(EXPECTED_EVENTS)
)
EXPECTED_PLUGIN_MANIFEST_KEYS = frozenset({
    "name",
    "version",
    "license",
    "description",
    "author",
    "homepage",
    "repository",
    "keywords",
    "skills",
    "hooks",
    "interface",
})
EXPECTED_AUTHOR_KEYS = frozenset(("name", "url"))
EXPECTED_INTERFACE_KEYS = frozenset({
    "displayName",
    "shortDescription",
    "longDescription",
    "developerName",
    "category",
    "capabilities",
    "websiteURL",
    "privacyPolicyURL",
    "termsOfServiceURL",
    "defaultPrompt",
    "brandColor",
    "composerIcon",
    "logo",
})
EXPECTED_AUDIO_MANIFEST_KEYS = frozenset({
    "schema_version",
    "release",
    "asset_count",
    "files",
})
EXPECTED_AUDIO_RECORD_KEYS = frozenset({
    "event",
    "voice",
    "language",
    "path",
    "text",
    "sha256",
    "bytes",
    "duration_seconds",
    "sample_rate",
    "channels",
    "sample_width_bytes",
})
EXPECTED_EVAL_KEYS = frozenset(("positive", "negative"))
EXPECTED_EVAL_CASE_KEYS = frozenset(("prompt", "expected"))
EXPECTED_README_FILES = (
    "README.md",
    "README.ko.md",
    "README.ja.md",
    "README.zh-CN.md",
    "README.ru.md",
)
README_LANGUAGE_SWITCHER = (
    "[English](README.md) | [한국어](README.ko.md) | "
    "[日本語](README.ja.md) | [简体中文](README.zh-CN.md) | "
    "[Русский](README.ru.md)"
)
README_VERSION_PREFIXES = {
    "README.md": "Version ",
    "README.ko.md": "버전 ",
    "README.ja.md": "バージョン ",
    "README.zh-CN.md": "版本 ",
    "README.ru.md": "Версия ",
}
README_ASSET_SCOPE_MARKERS = {
    "README.md": (
        "All WAV files under `assets/audio/`",
        "only without modification",
        "personal, non-commercial notification playback",
        "records generation provenance",
        "provenance details do not change",
    ),
    "README.ko.md": (
        "`assets/audio/` 아래의 모든 WAV",
        "수정하지 않은 무료 Voice",
        "개인적·비상업적 알림 재생 용도로만",
        "생성 출처만 기록합니다",
        "사용 조건을 변경하지 않습니다",
    ),
    "README.ja.md": (
        "`assets/audio/` 以下のすべての WAV",
        "未改変かつ無償の Voice Notify for Codex",
        "個人的・非商用の通知再生目的でのみ",
        "生成来歴のみを記録します",
        "利用条件が変わることはありません",
    ),
    "README.zh-CN.md": (
        "`assets/audio/` 下的所有 WAV",
        "未经修改的免费 Voice Notify for Codex",
        "个人、非商业通知播放",
        "仅记录生成来源",
        "不会改变语音资源的使用条款",
    ),
    "README.ru.md": (
        "Все WAV-файлы в `assets/audio/`",
        "неизменённой бесплатной",
        "личного некоммерческого воспроизведения",
        "содержит только сведения о",
        "не изменяют условия использования голосовых ресурсов",
    ),
}
README_PRIVACY_MARKERS = {
    "README.md": (
        "no network code or telemetry",
        "never stores prompts, messages, tool input, or tool output",
    ),
    "README.ko.md": (
        "네트워크 코드와 텔레메트리가",
        "프롬프트·메시지·도구 입력·도구 출력을 저장하지 않습니다",
    ),
    "README.ja.md": (
        "ネットワークコードや",
        "テレメトリはなく",
        "ツール入力、ツール出力を保存しません",
    ),
    "README.zh-CN.md": (
        "不包含网络代码或遥测",
        "不会存储提示词、消息",
        "工具输入或工具输出",
    ),
    "README.ru.md": (
        "нет сетевого кода и телеметрии",
        "не сохраняет запросы, сообщения",
        "входные или выходные данные инструментов",
    ),
}
README_HOOK_TRUST_MARKERS = {
    "README.md": (
        "enter `/hooks`, inspect the bundled",
        "explicitly trust it",
        "fully restart Codex before testing",
    ),
    "README.ko.md": (
        "`/hooks`를 입력하고 번들 명령을 검토",
        "신뢰하십시오",
        "Codex를 완전히 종료하고 다시 실행",
    ),
    "README.ja.md": (
        "`/hooks` と入力し、同梱コマンドを確認",
        "明示的に信頼してください",
        "Codex を完全に終了して再起動",
    ),
    "README.zh-CN.md": (
        "输入 `/hooks`，检查插件自带的命令",
        "明确选择信任",
        "彻底退出并重新启动 Codex",
    ),
    "README.ru.md": (
        "введите `/hooks`, проверьте встроенную команду",
        "явно подтвердите доверие",
        "полностью закройте и заново запустите",
    ),
}
COMMON_README_MARKERS = (
    "100 WAV",
    "`SessionStart`",
    "`PreToolUse`",
    "`PostToolUse`",
    "`PermissionRequest`",
    "`/hooks`",
    "`0.145.0`",
    "[ASSET_LICENSE.md](ASSET_LICENSE.md)",
    "[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)",
    "codex plugin marketplace add battle-doll/codex-voice-notify --ref main",
    "codex plugin add codex-voice-notify@codex-voice-notify",
    "codex.cmd plugin marketplace add battle-doll/codex-voice-notify --ref main",
    "codex.cmd plugin add codex-voice-notify@codex-voice-notify",
    "voice_notify_config.sh setup",
    "voice_notify_config.sh show",
    "voice_notify_config.sh set",
    "voice_notify_config.sh test",
    "voice_notify_config.sh mute",
    "voice_notify_config.ps1 setup",
    "voice_notify_config.ps1 show",
    "voice_notify_config.ps1 set",
    "voice_notify_config.ps1 test",
    "voice_notify_config.ps1 mute",
)
EVAL_LOCALE_MARKERS = {
    "ko": ("korean", "한국어", "한국"),
    "ja": ("japanese", "日本語", "일본어"),
    "en": ("english", "영어"),
    "ru": ("russian", "русск", "러시아"),
    "zh-CN": ("zh-cn", "simplified chinese", "简体中文", "중국어"),
}
ACTIVE_WINDOW_SECONDS = 0.020
ACTIVE_WINDOW_MIN_DBFS = -45.0
MAX_GROUP_ACTIVE_RMS_DROP_DB = 8.0
DESCRIPTION_MAX_CHARS = 256
AUTHOR_NAME_MAX_CHARS = 128
INTERFACE_TEXT_LIMITS = {
    "displayName": 64,
    "shortDescription": 80,
    "longDescription": 1024,
    "developerName": 128,
    "category": 64,
}
MAX_CAPABILITIES = 20
MAX_CAPABILITY_CHARS = 80
MAX_KEYWORDS = 20
MAX_KEYWORD_CHARS = 64
MAX_URL_CHARS = 2048
CANONICAL_WAV_HEADER_BYTES = 44
CANONICAL_WAV_FORMAT = (1, 2, 24000)


def fail(message: str) -> None:
    raise AssertionError(message)


def require_bounded_text(
    payload: dict,
    field: str,
    maximum: int,
    label: str,
) -> str:
    value = payload.get(field)
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
    ):
        fail("%s must be a non-empty string of at most %d characters" % (label, maximum))
    return value


def require_https_url(value: object, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_URL_CHARS
        or value != value.strip()
        or any(character.isspace() for character in value)
    ):
        fail("%s must be a non-empty HTTPS URL" % label)
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        fail("%s must be an absolute HTTPS URL without credentials" % label)


def require_plugin_asset(raw_path: object, label: str) -> None:
    if not isinstance(raw_path, str) or not raw_path.startswith("./"):
        fail("%s must be a plugin-relative path starting with ./" % label)
    relative_text = raw_path[2:]
    parts = relative_text.split("/")
    if (
        not relative_text
        or "\\" in relative_text
        or any(part in ("", ".", "..") for part in parts)
    ):
        fail("%s must stay inside the plugin root" % label)
    plugin_root = ROOT.resolve()
    candidate = ROOT.joinpath(*parts)
    resolved = candidate.resolve()
    if plugin_root not in resolved.parents or not resolved.is_file():
        fail("%s must resolve to a regular file inside the plugin root" % label)


def require_plugin_directory(raw_path: object, expected: str, label: str) -> None:
    if raw_path != expected:
        fail("%s must be %s" % (label, expected))
    relative_text = expected[2:].rstrip("/")
    resolved = (ROOT / relative_text).resolve()
    plugin_root = ROOT.resolve()
    if (
        plugin_root not in resolved.parents
        or not resolved.is_dir()
        or (ROOT / relative_text).is_symlink()
    ):
        fail("%s must resolve to a real directory inside the plugin root" % label)


def validate_multilingual_readmes(version: str) -> None:
    """Require structurally complete, release-matched localized READMEs."""

    for filename in EXPECTED_README_FILES:
        path = ROOT / filename
        if not path.is_file() or path.stat().st_size == 0:
            fail("missing multilingual README: %s" % filename)
        text = path.read_text("utf-8")
        lines = text.splitlines()
        if len(lines) < 3 or lines[2] != README_LANGUAGE_SWITCHER:
            fail("README language switcher mismatch: %s" % filename)
        version_marker = README_VERSION_PREFIXES[filename] + version
        if text.count(version_marker) != 2:
            fail("README must contain both current-version anchors: %s" % filename)
        if text.count("\n## ") != 7:
            fail("README must contain the seven release sections: %s" % filename)
        if text.count("```") != 8:
            fail("README must contain four complete command blocks: %s" % filename)
        missing_markers = [
            marker for marker in COMMON_README_MARKERS if marker not in text
        ]
        if missing_markers:
            fail(
                "README is missing release-parity markers (%s): %s"
                % (", ".join(missing_markers), filename)
            )
        localized_boundaries = (
            ("complete voice-asset scope", README_ASSET_SCOPE_MARKERS[filename]),
            ("offline privacy boundary", README_PRIVACY_MARKERS[filename]),
            ("manual hook trust boundary", README_HOOK_TRUST_MARKERS[filename]),
        )
        for boundary_name, boundary_markers in localized_boundaries:
            missing_boundary_markers = [
                marker for marker in boundary_markers if marker not in text
            ]
            if missing_boundary_markers:
                fail(
                    "README is missing %s (%s): %s"
                    % (
                        boundary_name,
                        ", ".join(missing_boundary_markers),
                        filename,
                    )
                )


def validate_canonical_pcm_wav(payload: bytes, audio_file: pathlib.Path) -> int:
    """Validate the release's exact 44-byte RIFF/PCM/data layout."""

    if len(payload) < CANONICAL_WAV_HEADER_BYTES:
        fail("truncated WAV header: %s" % audio_file)
    (
        riff_id,
        riff_size,
        wave_id,
        fmt_id,
        fmt_size,
        audio_format,
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        data_id,
        data_size,
    ) = struct.unpack(
        "<4sI4s4sIHHIIHH4sI",
        payload[:CANONICAL_WAV_HEADER_BYTES],
    )
    expected_block_align = channels * bits_per_sample // 8
    expected_byte_rate = sample_rate * expected_block_align
    if (
        riff_id != b"RIFF"
        or riff_size != len(payload) - 8
        or wave_id != b"WAVE"
        or fmt_id != b"fmt "
        or fmt_size != 16
        or audio_format != 1
        or (channels, bits_per_sample // 8, sample_rate) != CANONICAL_WAV_FORMAT
        or bits_per_sample != 16
        or block_align != expected_block_align
        or byte_rate != expected_byte_rate
        or data_id != b"data"
        or data_size != len(payload) - CANONICAL_WAV_HEADER_BYTES
        or data_size % block_align != 0
    ):
        fail(
            "WAV must use the canonical 44-byte mono 16-bit 24 kHz PCM layout "
            "with exact RIFF and data sizes: %s" % audio_file
        )
    return data_size // block_align


def active_rms_dbfs(samples: array.array[int], sample_rate: int) -> float:
    """Return RMS inside the first/last non-silent 20 ms speech windows."""

    window_size = max(1, round(sample_rate * ACTIVE_WINDOW_SECONDS))
    minimum_rms = 32768.0 * (10.0 ** (ACTIVE_WINDOW_MIN_DBFS / 20.0))
    active_windows = []
    for start in range(0, len(samples), window_size):
        window = samples[start : start + window_size]
        if not window:
            continue
        rms = math.sqrt(sum(sample * sample for sample in window) / len(window))
        if rms >= minimum_rms:
            active_windows.append((start, min(start + window_size, len(samples))))
    if not active_windows:
        return float("-inf")

    active_samples = samples[active_windows[0][0] : active_windows[-1][1]]
    rms = math.sqrt(
        sum(sample * sample for sample in active_samples) / len(active_samples)
    )
    return 20.0 * math.log10(rms / 32768.0)


def main() -> int:
    fish_license = ROOT / "FISH_AUDIO_RESEARCH_LICENSE.md"
    if not fish_license.is_file() or fish_license.stat().st_size == 0:
        fail("Fish Audio Research License text must be bundled")
    for forbidden in (
        ROOT / "platform",
        ROOT / "scripts" / "studio_platform.py",
        ROOT / "skills" / "voice-notify-studio",
    ):
        if forbidden.exists():
            fail("public package contains private Studio content: %s" % forbidden)

    manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text("utf-8"))
    hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text("utf-8"))
    if (
        not isinstance(manifest, dict)
        or set(manifest) != EXPECTED_PLUGIN_MANIFEST_KEYS
    ):
        fail("plugin manifest must contain exactly the release contract keys")
    if manifest["name"] != "codex-voice-notify":
        fail("unexpected plugin name")
    if manifest["license"] != "MIT":
        fail("plugin license must be MIT")
    if manifest["hooks"] != "./hooks/hooks.json":
        fail("plugin manifest must register hooks/hooks.json")
    require_plugin_directory(manifest["skills"], "./skills/", "plugin skills path")
    keywords = manifest["keywords"]
    if (
        not isinstance(keywords, list)
        or not 1 <= len(keywords) <= MAX_KEYWORDS
        or any(
            not isinstance(keyword, str)
            or not keyword.strip()
            or keyword != keyword.strip()
            or len(keyword) > MAX_KEYWORD_CHARS
            for keyword in keywords
        )
        or len({keyword.casefold() for keyword in keywords}) != len(keywords)
    ):
        fail(
            "plugin keywords must contain 1-%d unique non-empty strings of at "
            "most %d characters" % (MAX_KEYWORDS, MAX_KEYWORD_CHARS)
        )
    require_bounded_text(
        manifest,
        "description",
        DESCRIPTION_MAX_CHARS,
        "plugin description",
    )
    author = manifest.get("author")
    if not isinstance(author, dict) or set(author) != EXPECTED_AUTHOR_KEYS:
        fail("plugin author must contain exactly name and url")
    require_bounded_text(
        author,
        "name",
        AUTHOR_NAME_MAX_CHARS,
        "plugin author name",
    )
    require_https_url(author.get("url"), "plugin author URL")
    for url_field in ("homepage", "repository"):
        require_https_url(manifest.get(url_field), "plugin %s" % url_field)

    interface = manifest.get("interface")
    if not isinstance(interface, dict) or set(interface) != EXPECTED_INTERFACE_KEYS:
        fail("plugin interface must contain exactly the release contract keys")
    for interface_field, maximum in INTERFACE_TEXT_LIMITS.items():
        require_bounded_text(
            interface,
            interface_field,
            maximum,
            "plugin interface.%s" % interface_field,
        )
    capabilities = interface.get("capabilities")
    if (
        not isinstance(capabilities, list)
        or not 1 <= len(capabilities) <= MAX_CAPABILITIES
        or any(
            not isinstance(capability, str)
            or not capability.strip()
            or len(capability) > MAX_CAPABILITY_CHARS
            for capability in capabilities
        )
        or len({capability.casefold() for capability in capabilities}) != len(capabilities)
    ):
        fail(
            "plugin interface.capabilities must contain 1-%d unique non-empty "
            "strings of at most %d characters"
            % (MAX_CAPABILITIES, MAX_CAPABILITY_CHARS)
        )
    for url_field in (
        "websiteURL",
        "privacyPolicyURL",
        "termsOfServiceURL",
    ):
        require_https_url(
            interface.get(url_field),
            "plugin interface.%s" % url_field,
        )
    brand_color = interface.get("brandColor")
    if not isinstance(brand_color, str) or not re.fullmatch(
        r"#[0-9A-Fa-f]{6}", brand_color
    ):
        fail("plugin interface.brandColor must use #RRGGBB")
    for asset_field in ("composerIcon", "logo"):
        require_plugin_asset(
            interface.get(asset_field),
            "plugin interface.%s" % asset_field,
        )
    if set(hooks.get("hooks", {})) != EXPECTED_EVENTS:
        fail("hook event set does not match the release contract")
    expected_macos_hook = '/bin/sh "${PLUGIN_ROOT}/hooks/play_notify.sh"'
    expected_windows_hook = (
        'powershell.exe -NoLogo -NoProfile -NonInteractive '
        '-ExecutionPolicy Bypass -File "${PLUGIN_ROOT}\\hooks\\play_notify.ps1"'
    )
    for event_name, groups in hooks["hooks"].items():
        handlers = [
            handler
            for group in groups
            for handler in group.get("hooks", ())
        ]
        if len(handlers) != 1:
            fail("%s must register exactly one command hook" % event_name)
        if handlers[0].get("command") != expected_macos_hook:
            fail("%s must use the system-native macOS shell hook" % event_name)
        if handlers[0].get("commandWindows") != expected_windows_hook:
            fail("%s must preserve the Windows PowerShell hook" % event_name)
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(manifest.get("version", ""))):
        fail("plugin version must be a three-part semantic version")
    validate_multilingual_readmes(manifest["version"])
    default_prompts = interface.get("defaultPrompt", ())
    if (
        not isinstance(default_prompts, list)
        or not 1 <= len(default_prompts) <= 3
        or any(
            not isinstance(prompt, str)
            or not prompt.strip()
            or len(prompt) > 128
            for prompt in default_prompts
        )
    ):
        fail("default prompts must contain 1-3 non-empty strings of at most 128 characters")
    if not any(
        marker in default_prompts[0].lower()
        for marker in ("first-time setup", "set up voice notify")
    ):
        fail("the first default prompt must offer guided first-time setup")
    if "new codex cli terminal" not in default_prompts[0].lower():
        fail("the first default prompt must request a new Codex CLI terminal")
    skill_text = (
        ROOT / "skills" / "voice-notify-settings" / "SKILL.md"
    ).read_text("utf-8")
    for required_text in (
        "## First-time setup",
        "natural-language",
        "--open-hooks",
        "-OpenHooks",
        "voice_notify_config.sh",
        "new visible terminal",
        "starts the verified Codex CLI",
    ):
        if required_text not in skill_text:
            fail("settings skill is missing setup guidance: %s" % required_text)
    safe_trust_guidance = re.compile(
        r"Never edit the trust\s+store or use\s+"
        r"`--dangerously-bypass-hook-trust`\."
    )
    if not safe_trust_guidance.search(skill_text):
        fail("settings skill must preserve the mandatory hook trust boundary")
    setup_launchers = {
        ROOT / "scripts" / "voice_notify_config.py": (
            "/usr/bin/osascript",
            'tell application "Terminal"',
            "activate",
            "exec %s --no-alt-screen -C %s",
        ),
        ROOT / "scripts" / "voice_notify_config.ps1": (
            "Start-Process",
            "-WindowStyle Normal",
            "& '$EscapedCodexPath' --no-alt-screen -C '$EscapedWorkingDirectory'",
        ),
        ROOT / "scripts" / "voice_notify_config.sh": (
            "/usr/bin/osascript",
            "do script terminalCommand",
            'exec $(shell_quote "$codex_path") --no-alt-screen -C',
        ),
    }
    for launcher_path, required_markers in setup_launchers.items():
        launcher_text = launcher_path.read_text("utf-8")
        if "--dangerously-bypass-hook-trust" in launcher_text:
            fail("setup launcher must not bypass hook trust: %s" % launcher_path)
        if "/hooks" not in launcher_text:
            fail("setup launcher must hand off visibly to /hooks: %s" % launcher_path)
        for marker in required_markers:
            if marker not in launcher_text:
                fail(
                    "setup launcher must start the verified Codex CLI in a new "
                    "terminal (%s): %s" % (marker, launcher_path)
                )
    macos_runtime_paths = (
        ROOT / "hooks" / "play_notify.sh",
        ROOT / "scripts" / "voice_notify_config.sh",
    )
    for runtime_path in macos_runtime_paths:
        if not runtime_path.is_file() or runtime_path.stat().st_size == 0:
            fail("missing system-native macOS runtime: %s" % runtime_path)
        runtime_text = runtime_path.read_text("utf-8")
        for forbidden_reference in (
            "/usr/bin/python3",
            "play_notify.py",
            "/dev/stdin",
        ):
            if forbidden_reference in runtime_text:
                fail(
                    "macOS runtime contains an unsupported dependency or stdin path: %s"
                    % runtime_path
                )
    macos_hook_text = (ROOT / "hooks" / "play_notify.sh").read_text("utf-8")
    for required_parser_text in (
        "fileHandleWithStandardInput",
        "JSON.parse(text)",
    ):
        if required_parser_text not in macos_hook_text:
            fail(
                "macOS hook must parse its JSON payload in memory: %s"
                % required_parser_text
            )
    for required_tool in (
        "/bin/sh",
        "/usr/bin/plutil",
        "/usr/bin/afplay",
        "/usr/bin/osascript",
    ):
        if not any(
            required_tool in path.read_text("utf-8")
            for path in macos_runtime_paths
        ):
            fail("macOS runtime is missing system tool reference: %s" % required_tool)

    phrases = json.loads(
        (ROOT / "assets" / "audio" / "phrases.json").read_text("utf-8")
    )
    if set(phrases) != EXPECTED_EVENTS:
        fail("phrases.json event set does not match the release contract")
    expected_phrase_keys = {"file", *EXPECTED_LANGUAGES}
    for event, phrase in phrases.items():
        if not isinstance(phrase, dict) or set(phrase) != expected_phrase_keys:
            fail("%s must contain file plus all five release languages" % event)
        if (
            not isinstance(phrase["file"], str)
            or pathlib.PurePosixPath(phrase["file"]).name != phrase["file"]
            or not phrase["file"].endswith(".wav")
        ):
            fail("invalid release WAV filename for event: %s" % event)
        if any(
            not isinstance(phrase[language], str) or not phrase[language].strip()
            for language in EXPECTED_LANGUAGES
        ):
            fail("missing release phrase text for event: %s" % event)
    if len({phrase["file"] for phrase in phrases.values()}) != len(EXPECTED_EVENTS):
        fail("release events must use distinct WAV filenames")

    expected_matrix = {
        (voice, language, event)
        for voice in EXPECTED_VOICES
        for language in EXPECTED_LANGUAGES
        for event in EXPECTED_EVENTS
    }
    expected_path_by_key = {
        (voice, language, event): (
            pathlib.PurePosixPath("assets")
            / "audio"
            / voice
            / language
            / phrases[event]["file"]
        ).as_posix()
        for voice, language, event in expected_matrix
    }
    expected_paths = set(expected_path_by_key.values())
    if len(expected_paths) != EXPECTED_ASSET_COUNT:
        fail("release audio matrix must contain exactly 100 unique paths")

    audio_files = sorted((ROOT / "assets" / "audio").glob("*/*/*.wav"))
    actual_paths = {
        path.relative_to(ROOT).as_posix() for path in audio_files
    }
    if len(audio_files) != EXPECTED_ASSET_COUNT or actual_paths != expected_paths:
        fail(
            "release WAV paths must match the exact 2-voice, 5-language, "
            "10-event matrix (expected %d, found %d)"
            % (EXPECTED_ASSET_COUNT, len(audio_files))
        )

    durations = []
    wav_metadata_by_path = {}
    active_rms_by_group = {
        (voice, language): []
        for voice in EXPECTED_VOICES
        for language in EXPECTED_LANGUAGES
    }
    for audio_file in audio_files:
        payload = audio_file.read_bytes()
        canonical_frame_count = validate_canonical_pcm_wav(payload, audio_file)
        with wave.open(str(audio_file), "rb") as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 24000):
                fail("invalid WAV format: %s" % audio_file)
            channels = wav.getnchannels()
            sample_width_bytes = wav.getsampwidth()
            sample_rate = wav.getframerate()
            frame_count = wav.getnframes()
            if frame_count != canonical_frame_count or wav.getcomptype() != "NONE":
                fail("WAV header metadata does not match PCM frames: %s" % audio_file)
            frames = wav.readframes(frame_count)
            duration = frame_count / float(sample_rate)
        if frames != payload[CANONICAL_WAV_HEADER_BYTES:]:
            fail("WAV data bytes do not match the canonical data chunk: %s" % audio_file)
        if not 0.3 <= duration <= 20.0:
            fail("invalid duration: %s" % audio_file)
        samples = array.array("h")
        samples.frombytes(frames)
        if sys.byteorder != "little":
            samples.byteswap()
        if not samples or max(abs(sample) for sample in samples) == 0:
            fail("silent WAV: %s" % audio_file)
        clipped = sum(1 for sample in samples if abs(sample) >= 32767)
        if clipped / float(len(samples)) > 0.005:
            fail("excessive clipping: %s" % audio_file)
        relative_path = audio_file.relative_to(ROOT).as_posix()
        wav_metadata_by_path[relative_path] = {
            "bytes": len(payload),
            "duration_seconds": round(duration, 6),
            "sample_rate": sample_rate,
            "channels": channels,
            "sample_width_bytes": sample_width_bytes,
        }
        group = (audio_file.parent.parent.name, audio_file.parent.name)
        active_rms_by_group[group].append(
            (audio_file, active_rms_dbfs(samples, sample_rate))
        )
        durations.append(duration)

    for (voice, language), levels in active_rms_by_group.items():
        group_median = statistics.median(level for _, level in levels)
        for audio_file, level in levels:
            drop = group_median - level
            if drop > MAX_GROUP_ACTIVE_RMS_DROP_DB:
                fail(
                    "low-volume WAV is %.2f dB below the %s/%s active-RMS "
                    "median (limit %.2f dB): %s"
                    % (
                        drop,
                        voice,
                        language,
                        MAX_GROUP_ACTIVE_RMS_DROP_DB,
                        audio_file,
                    )
                )

    audio_manifest = json.loads(
        (ROOT / "assets" / "audio" / "manifest.json").read_text("utf-8")
    )
    if (
        not isinstance(audio_manifest, dict)
        or set(audio_manifest) != EXPECTED_AUDIO_MANIFEST_KEYS
    ):
        fail("audio manifest must contain exactly the release schema keys")
    if type(audio_manifest["schema_version"]) is not int or audio_manifest["schema_version"] != 1:
        fail("audio manifest schema_version must be integer 1")
    if type(audio_manifest["asset_count"]) is not int:
        fail("audio manifest asset_count must be an integer")
    records = audio_manifest["files"]
    if (
        not isinstance(records, list)
        or audio_manifest["asset_count"] != EXPECTED_ASSET_COUNT
        or len(records) != EXPECTED_ASSET_COUNT
    ):
        fail("audio manifest must contain exactly 100 files")
    if (
        not isinstance(audio_manifest["release"], str)
        or audio_manifest["release"] != manifest.get("version")
    ):
        fail("audio manifest release must match the plugin version")
    record_keys = set()
    record_paths = set()
    for record in records:
        if (
            not isinstance(record, dict)
            or set(record) != EXPECTED_AUDIO_RECORD_KEYS
        ):
            fail("audio manifest records must contain exactly the release record keys")
        event = record["event"]
        voice = record["voice"]
        language = record["language"]
        key = (voice, language, event)
        if key not in expected_matrix or key in record_keys:
            fail("invalid or duplicate audio manifest matrix record")
        record_keys.add(key)
        expected_path = expected_path_by_key[key]
        if record["path"] != expected_path:
            fail("audio manifest path does not match voice, language, and event")
        record_paths.add(expected_path)
        if record["text"] != phrases[event][language]:
            fail("audio manifest text does not match phrases.json")
        path = ROOT / expected_path
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if (
            not isinstance(record["sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", record["sha256"])
            or digest != record["sha256"]
        ):
            fail("audio checksum mismatch: %s" % path)
        expected_metadata = wav_metadata_by_path[expected_path]
        for field, expected_value in expected_metadata.items():
            actual_value = record[field]
            if field == "duration_seconds":
                valid_type = type(actual_value) in (int, float)
            else:
                valid_type = type(actual_value) is int
            if not valid_type or actual_value != expected_value:
                fail(
                    "audio manifest %s mismatch for %s (expected %r, found %r)"
                    % (field, path, expected_value, actual_value)
                )
    if record_keys != expected_matrix or record_paths != expected_paths:
        fail("audio manifest must cover the exact 100-file release matrix")

    evals = json.loads((ROOT / "evals" / "cases.json").read_text("utf-8"))
    if not isinstance(evals, dict) or set(evals) != EXPECTED_EVAL_KEYS:
        fail("submission evals must contain exactly positive and negative lists")
    if (
        not isinstance(evals["positive"], list)
        or not isinstance(evals["negative"], list)
        or len(evals["positive"]) != 7
        or len(evals["negative"]) != 3
    ):
        fail("submission evals must contain exactly 7 positive and 3 negative cases")
    normalized_prompts = set()
    for category in ("positive", "negative"):
        for case in evals[category]:
            if not isinstance(case, dict) or set(case) != EXPECTED_EVAL_CASE_KEYS:
                fail("each submission eval must contain exactly prompt and expected")
            for field in EXPECTED_EVAL_CASE_KEYS:
                if not isinstance(case[field], str) or not case[field].strip():
                    fail("submission eval %s must be a non-empty string" % field)
            normalized_prompt = " ".join(case["prompt"].split()).casefold()
            if normalized_prompt in normalized_prompts:
                fail("submission eval prompts must be unique")
            normalized_prompts.add(normalized_prompt)
    positive_eval_text = "\n".join(
        "%s\n%s" % (case["prompt"], case["expected"])
        for case in evals["positive"]
    ).casefold()
    missing_eval_locales = sorted(
        language
        for language, markers in EVAL_LOCALE_MARKERS.items()
        if not any(marker.casefold() in positive_eval_text for marker in markers)
    )
    if missing_eval_locales:
        fail(
            "positive submission evals must cover all five release locales; "
            "missing: %s" % ", ".join(missing_eval_locales)
        )

    print(
        "PASS: manifest, guided setup, system-native macOS runtime, 10 hooks, "
        "%d WAVs, checksums, format, signal, clipping, and 7+3 evals "
        "(%.2f-%.2fs)"
        % (EXPECTED_ASSET_COUNT, min(durations), max(durations))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
