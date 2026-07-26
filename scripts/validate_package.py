#!/usr/bin/env python3
"""Run the minimal release checks for a Voice Notify package."""

from __future__ import annotations

import array
import hashlib
import json
import pathlib
import re
import sys
import wave


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_EVENTS = {
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
}


def fail(message: str) -> None:
    raise AssertionError(message)


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
    if manifest.get("name") != "codex-voice-notify":
        fail("unexpected plugin name")
    if manifest.get("hooks") != "./hooks/hooks.json":
        fail("plugin manifest must register hooks/hooks.json")
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
    default_prompts = manifest.get("interface", {}).get("defaultPrompt", ())
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
    skill_text = (
        ROOT / "skills" / "voice-notify-settings" / "SKILL.md"
    ).read_text("utf-8")
    for required_text in (
        "## First-time setup",
        "natural-language",
        "--open-hooks",
        "-OpenHooks",
        "voice_notify_config.sh",
    ):
        if required_text not in skill_text:
            fail("settings skill is missing setup guidance: %s" % required_text)
    safe_trust_guidance = re.compile(
        r"Never edit the trust\s+store or use\s+"
        r"`--dangerously-bypass-hook-trust`\."
    )
    if not safe_trust_guidance.search(skill_text):
        fail("settings skill must preserve the mandatory hook trust boundary")
    setup_launchers = (
        ROOT / "scripts" / "voice_notify_config.py",
        ROOT / "scripts" / "voice_notify_config.ps1",
        ROOT / "scripts" / "voice_notify_config.sh",
    )
    for launcher_path in setup_launchers:
        launcher_text = launcher_path.read_text("utf-8")
        if "--dangerously-bypass-hook-trust" in launcher_text:
            fail("setup launcher must not bypass hook trust: %s" % launcher_path)
        if "/hooks" not in launcher_text:
            fail("setup launcher must hand off visibly to /hooks: %s" % launcher_path)
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
    if "/usr/bin/plutil -extract hook_event_name raw -- -" not in macos_hook_text:
        fail("macOS hook must read its JSON payload from plutil's stdin marker")
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

    audio_files = sorted((ROOT / "assets" / "audio").glob("*/*/*.wav"))
    if len(audio_files) != 60:
        fail("expected 60 WAV files, found %d" % len(audio_files))

    durations = []
    for audio_file in audio_files:
        with wave.open(str(audio_file), "rb") as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 24000):
                fail("invalid WAV format: %s" % audio_file)
            frames = wav.readframes(wav.getnframes())
            duration = wav.getnframes() / float(wav.getframerate())
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
        durations.append(duration)

    audio_manifest = json.loads(
        (ROOT / "assets" / "audio" / "manifest.json").read_text("utf-8")
    )
    phrases = json.loads(
        (ROOT / "assets" / "audio" / "phrases.json").read_text("utf-8")
    )
    records = audio_manifest.get("files", ())
    if audio_manifest.get("asset_count") != 60 or len(records) != 60:
        fail("audio manifest must contain 60 files")
    if audio_manifest.get("release") != manifest.get("version"):
        fail("audio manifest release must match the plugin version")
    expected_paths = {
        path.relative_to(ROOT).as_posix() for path in audio_files
    }
    record_paths = [record.get("path") for record in records]
    if len(set(record_paths)) != 60 or set(record_paths) != expected_paths:
        fail("audio manifest paths must match the 60 release WAV files")
    for record in records:
        event = record.get("event")
        language = record.get("language")
        if event not in phrases or language not in {"ko", "ja", "en"}:
            fail("invalid audio manifest event or language")
        if record.get("text") != phrases[event][language]:
            fail("audio manifest text does not match phrases.json")
        path = ROOT / record["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != record["sha256"]:
            fail("audio checksum mismatch: %s" % path)

    evals = json.loads((ROOT / "evals" / "cases.json").read_text("utf-8"))
    if len(evals.get("positive", ())) != 5 or len(evals.get("negative", ())) != 3:
        fail("submission evals must contain exactly 5 positive and 3 negative cases")

    print(
        "PASS: manifest, guided setup, system-native macOS runtime, 10 hooks, "
        "60 WAVs, checksums, format, signal, clipping, and 5+3 evals "
        "(%.2f-%.2fs)" % (min(durations), max(durations))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
