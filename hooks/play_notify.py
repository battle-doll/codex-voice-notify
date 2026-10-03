#!/usr/bin/env python3
"""Privacy-preserving, non-blocking local WAV playback for Codex hooks."""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, Optional

if os.name == "nt":
    import msvcrt
    import winsound
else:
    import fcntl


EVENT_FILES = {
    "SessionStart": "session-start",
    "UserPromptSubmit": "user-prompt-submit",
    "PreToolUse": "pre-tool-use",
    "PostToolUse": "post-tool-use",
    "PermissionRequest": "permission-request",
    "PreCompact": "pre-compact",
    "PostCompact": "post-compact",
    "SubagentStart": "subagent-start",
    "SubagentStop": "subagent-stop",
    "Stop": "stop",
}
VOICES = frozenset(("female", "male"))
LANGUAGES = frozenset(("ko", "ja", "en", "ru", "zh-CN"))
DEFAULT_DISABLED_EVENTS = frozenset(("PreToolUse", "PostToolUse"))
DEFAULT_SETTINGS = {
    "enabled": True,
    "voice": "female",
    "language": "ko",
    "min_interval_ms": 450,
    "events": {
        event: event not in DEFAULT_DISABLED_EVENTS for event in EVENT_FILES
    },
}
MAX_INPUT_BYTES = 1024 * 1024
MAX_SETTINGS_BYTES = 64 * 1024
MACOS_PLAYER = pathlib.Path("/usr/bin/afplay")
LINUX_PLAYERS = (
    ("pw-play", ()),
    ("paplay", ()),
    ("aplay", ("-q",)),
    ("ffplay", ("-nodisp", "-autoexit", "-loglevel", "quiet")),
)


def _xdg_directory(variable: str, fallback: str) -> pathlib.Path:
    """The XDG specification ignores empty and relative base directories."""
    candidate = os.environ.get(variable, "")
    if candidate and pathlib.Path(candidate).is_absolute():
        return pathlib.Path(candidate)
    return pathlib.Path.home() / fallback


def user_settings_path() -> pathlib.Path:
    override = os.environ.get("CODEX_VOICE_NOTIFY_CONFIG")
    if override:
        return pathlib.Path(override).expanduser()
    if sys.platform.startswith("linux"):
        return _xdg_directory("XDG_CONFIG_HOME", ".config") / "codex-voice-notify" / "settings.json"
    return pathlib.Path.home() / ".config" / "codex-voice-notify" / "settings.json"


def _copy_defaults() -> Dict[str, Any]:
    return {
        "enabled": DEFAULT_SETTINGS["enabled"],
        "voice": DEFAULT_SETTINGS["voice"],
        "language": DEFAULT_SETTINGS["language"],
        "min_interval_ms": DEFAULT_SETTINGS["min_interval_ms"],
        "events": dict(DEFAULT_SETTINGS["events"]),
    }


def normalize_settings(candidate: Any) -> Dict[str, Any]:
    settings = _copy_defaults()
    if not isinstance(candidate, dict):
        return settings

    if isinstance(candidate.get("enabled"), bool):
        settings["enabled"] = candidate["enabled"]
    if candidate.get("voice") in VOICES:
        settings["voice"] = candidate["voice"]
    if candidate.get("language") in LANGUAGES:
        settings["language"] = candidate["language"]

    interval = candidate.get("min_interval_ms")
    if isinstance(interval, int) and not isinstance(interval, bool):
        settings["min_interval_ms"] = max(0, min(interval, 10_000))

    event_settings = candidate.get("events")
    if isinstance(event_settings, dict):
        for event in EVENT_FILES:
            value = event_settings.get(event)
            if isinstance(value, bool):
                settings["events"][event] = value
    return settings


def load_settings(path: Optional[pathlib.Path] = None) -> Dict[str, Any]:
    settings_path = path or user_settings_path()
    try:
        if not settings_path.is_file() or settings_path.stat().st_size > MAX_SETTINGS_BYTES:
            return _copy_defaults()
        with settings_path.open("r", encoding="utf-8") as handle:
            return normalize_settings(json.load(handle))
    except (OSError, UnicodeError, ValueError, TypeError):
        return _copy_defaults()


def select_audio_path(
    plugin_root: pathlib.Path, event_name: str, settings: Dict[str, Any]
) -> Optional[pathlib.Path]:
    event_file = EVENT_FILES.get(event_name)
    if not settings.get("enabled") or not event_file:
        return None
    if not settings["events"].get(event_name, True):
        return None

    audio_root = (plugin_root / "assets" / "audio").resolve()
    audio_path = (
        audio_root
        / settings["voice"]
        / settings["language"]
        / (event_file + ".wav")
    ).resolve()
    try:
        if os.path.commonpath((str(audio_root), str(audio_path))) != str(audio_root):
            return None
    except ValueError:
        return None
    if not audio_path.is_file():
        return None
    return audio_path


def _runtime_dir() -> pathlib.Path:
    plugin_data = os.environ.get("PLUGIN_DATA")
    if plugin_data:
        base = pathlib.Path(plugin_data)
    elif os.name == "nt":
        base = pathlib.Path(
            os.environ.get("LOCALAPPDATA", pathlib.Path.home() / "AppData" / "Local")
        ) / "codex-voice-notify"
    elif sys.platform.startswith("linux"):
        base = _xdg_directory("XDG_CACHE_HOME", ".cache") / "codex-voice-notify"
    else:
        base = pathlib.Path.home() / "Library" / "Caches" / "codex-voice-notify"
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    return base


def _player_environment() -> Dict[str, str]:
    # Retain only system/audio variables. Hook payloads, Codex credentials,
    # arbitrary environment values, and conversation text never reach players.
    environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    names = ["LANG", "LC_ALL", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP"]
    if sys.platform.startswith("linux"):
        names.extend(("HOME", "XDG_RUNTIME_DIR", "XDG_CONFIG_HOME", "DBUS_SESSION_BUS_ADDRESS"))
    for name in names:
        if name in os.environ:
            environment[name] = os.environ[name]
    return environment


def dispatch_playback(audio_path: pathlib.Path, min_interval_ms: int) -> None:
    if os.environ.get("CODEX_VOICE_NOTIFY_NO_PLAY") == "1":
        return
    try:
        runtime_dir = _runtime_dir()
        lock_path = runtime_dir / "playback.lock"
        subprocess.Popen(
            (
                sys.executable,
                str(pathlib.Path(__file__).resolve()),
                "--play",
                str(audio_path),
                str(lock_path),
                str(min_interval_ms),
            ),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
            env=_player_environment(),
        )
    except (OSError, ValueError):
        return


def _play_worker(audio_path: pathlib.Path, lock_path: pathlib.Path, interval_ms: int) -> int:
    if not player_available() or not audio_path.is_file():
        return 0
    try:
        lock_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
    except OSError:
        return 0

    try:
        try:
            if os.name == "nt":
                if os.fstat(descriptor).st_size == 0:
                    os.write(descriptor, b"0")
                    os.fsync(descriptor)
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return 0

        now = time.time()
        timestamp_path = lock_path.with_suffix(".timestamp")
        try:
            previous_raw = timestamp_path.read_text(encoding="ascii").strip()
            previous = float(previous_raw) if previous_raw else 0.0
        except (OSError, ValueError):
            previous = 0.0
        elapsed = now - previous
        if 0 <= elapsed < max(0, interval_ms) / 1000.0:
            return 0

        try:
            timestamp_path.write_text("%.6f" % now, encoding="ascii")
        except OSError:
            pass

        try:
            play_audio_sync(audio_path)
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            pass
        return 0
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass


def player_available() -> bool:
    return os.name == "nt" or player_command() is not None


def player_command() -> Optional[tuple]:
    if sys.platform == "darwin":
        return (str(MACOS_PLAYER),) if MACOS_PLAYER.is_file() else None
    if sys.platform.startswith("linux"):
        for executable, arguments in LINUX_PLAYERS:
            path = shutil.which(executable)
            if path:
                return (str(pathlib.Path(path).resolve()),) + arguments
    return None


def play_audio_sync(audio_path: pathlib.Path) -> int:
    if os.name == "nt":
        winsound.PlaySound(str(audio_path), winsound.SND_FILENAME)
        return 0
    command = player_command()
    if command is None:
        return 1
    completed = subprocess.run(
        command + (str(audio_path),),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=20,
        check=False,
        env=_player_environment(),
    )
    return completed.returncode


def main() -> int:
    if len(sys.argv) == 5 and sys.argv[1] == "--play":
        try:
            interval_ms = int(sys.argv[4])
        except ValueError:
            interval_ms = int(DEFAULT_SETTINGS["min_interval_ms"])
        return _play_worker(pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), interval_ms)

    try:
        raw_input = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw_input) > MAX_INPUT_BYTES:
            return 0
        payload = json.loads(raw_input.decode("utf-8"))
        event_name = payload.get("hook_event_name") if isinstance(payload, dict) else None
    except (OSError, UnicodeError, ValueError, TypeError):
        return 0
    if not isinstance(event_name, str):
        return 0

    plugin_root = pathlib.Path(os.environ.get("PLUGIN_ROOT", pathlib.Path(__file__).parents[1]))
    settings = load_settings()
    audio_path = select_audio_path(plugin_root, event_name, settings)
    if audio_path is not None:
        dispatch_playback(audio_path, int(settings["min_interval_ms"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
