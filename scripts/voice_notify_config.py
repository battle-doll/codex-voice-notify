#!/usr/bin/env python3
"""Configure and test Voice Notify for Codex without external dependencies."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from typing import Optional, Tuple


PLUGIN_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "hooks"))
import play_notify  # noqa: E402


MIN_HOOKS_CODEX_VERSION = (0, 145, 0)
LANGUAGE_CHOICES = tuple(sorted(play_notify.LANGUAGES))
CODEX_VERSION_PATTERN = re.compile(
    r"(?i)^\s*(?:openai\s+)?codex(?:-cli)?\s+"
    r"(?:\(\s*)?v?(\d+)\.(\d+)\.(\d+)\s*\)?\s*$"
)


def parse_codex_version(output: str) -> Optional[Tuple[int, int, int]]:
    match = CODEX_VERSION_PATTERN.search(output)
    if match is None:
        return None
    return tuple(int(part) for part in match.groups())


def find_codex_command(override: Optional[str] = None) -> Optional[pathlib.Path]:
    selected = override or os.environ.get("CODEX_VOICE_NOTIFY_CODEX")
    if selected:
        return pathlib.Path(selected).expanduser()
    discovered = shutil.which("codex")
    return pathlib.Path(discovered) if discovered else None


def inspect_codex(override: Optional[str] = None) -> Tuple[
    Optional[pathlib.Path], Optional[Tuple[int, int, int]], str
]:
    command = find_codex_command(override)
    if command is None:
        return None, None, ""
    try:
        completed = subprocess.run(
            (str(command), "--version"),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return command, None, ""
    output = completed.stdout.strip()
    if completed.returncode != 0:
        return command, None, output
    return command, parse_codex_version(output), output


def _apple_script_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def open_hook_trust_terminal(command: pathlib.Path, cwd: pathlib.Path) -> bool:
    if sys.platform != "darwin":
        return False
    osascript = pathlib.Path("/usr/bin/osascript")
    if not osascript.is_file():
        return False
    shell_command = (
        "printf '\\nVoice Notify opened this new Codex CLI terminal. "
        "Type /hooks here and review the bundled hook.\\n\\n'; "
        "exec %s --no-alt-screen -C %s"
        % (shlex.quote(str(command)), shlex.quote(str(cwd)))
    )
    apple_script = (
        'tell application "Terminal"\n'
        "activate\n"
        'do script "%s"\n'
        "end tell"
        % _apple_script_string(shell_command)
    )
    try:
        completed = subprocess.run(
            (str(osascript), "-e", apple_script),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def write_settings(settings: dict) -> pathlib.Path:
    destination = play_notify.user_settings_path()
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(destination.parent),
        prefix=".settings.",
        suffix=".tmp",
        delete=False,
    )
    temporary = pathlib.Path(handle.name)
    try:
        with handle:
            json.dump(settings, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configure Voice Notify for Codex")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("show", help="Show effective settings")
    subparsers.add_parser("mute", help="Disable notifications")
    subparsers.add_parser("unmute", help="Enable notifications")
    subparsers.add_parser("reset", help="Restore built-in defaults")

    set_parser = subparsers.add_parser("set", help="Change voice, language, or events")
    set_parser.add_argument("--voice", choices=sorted(play_notify.VOICES))
    set_parser.add_argument("--language", choices=LANGUAGE_CHOICES)
    set_parser.add_argument("--min-interval-ms", type=int)
    set_parser.add_argument(
        "--enable-event", action="append", choices=sorted(play_notify.EVENT_FILES)
    )
    set_parser.add_argument(
        "--disable-event", action="append", choices=sorted(play_notify.EVENT_FILES)
    )

    test_parser = subparsers.add_parser("test", help="Play one notification")
    test_parser.add_argument("--event", choices=sorted(play_notify.EVENT_FILES), default="Stop")
    test_parser.add_argument("--voice", choices=sorted(play_notify.VOICES))
    test_parser.add_argument("--language", choices=LANGUAGE_CHOICES)
    test_parser.add_argument("--dry-run", action="store_true")

    setup_parser = subparsers.add_parser(
        "setup", help="Run guided first-time setup"
    )
    setup_parser.add_argument("--voice", choices=sorted(play_notify.VOICES))
    setup_parser.add_argument("--language", choices=LANGUAGE_CHOICES)
    setup_parser.add_argument("--skip-audio-test", action="store_true")
    setup_parser.add_argument("--open-hooks", action="store_true")
    setup_parser.add_argument("--codex-command")
    setup_parser.add_argument("--dry-run", action="store_true")
    return parser


def run_setup(args: argparse.Namespace, settings: dict) -> int:
    if args.voice:
        settings["voice"] = args.voice
    if args.language:
        settings["language"] = args.language
    settings["enabled"] = True

    codex_command, codex_version, codex_output = inspect_codex(args.codex_command)
    if codex_command is None:
        print(
            "Codex CLI was not found. Install or expose Codex on PATH, then rerun setup.",
            file=sys.stderr,
        )
        return 3
    if codex_version is None:
        print(
            "Could not determine the Codex CLI version from: %s"
            % (codex_output or codex_command),
            file=sys.stderr,
        )
        return 3
    version_text = ".".join(str(part) for part in codex_version)
    minimum_text = ".".join(str(part) for part in MIN_HOOKS_CODEX_VERSION)
    print("Codex CLI: %s (%s)" % (version_text, codex_command))
    if codex_version < MIN_HOOKS_CODEX_VERSION:
        print(
            "Codex CLI %s or newer is required for /hooks. Update Codex, then rerun setup."
            % minimum_text,
            file=sys.stderr,
        )
        return 3

    test_settings = dict(settings)
    test_settings["events"] = dict(settings["events"])
    test_settings["events"]["Stop"] = True
    audio_path = play_notify.select_audio_path(PLUGIN_ROOT, "Stop", test_settings)
    if audio_path is None:
        print("Stop audio file is unavailable.", file=sys.stderr)
        return 1
    print("Stop audio: %s" % audio_path)
    if not args.dry_run and not args.skip_audio_test:
        if not play_notify.player_available():
            print("No supported system WAV player is available.", file=sys.stderr)
            return 1
        playback_status = play_notify.play_audio_sync(audio_path)
        if playback_status != 0:
            return playback_status

    if args.dry_run:
        print(
            "Dry run: would save voice=%s language=%s."
            % (settings["voice"], settings["language"])
        )
    else:
        destination = write_settings(settings)
        print("Saved %s" % destination)

    if args.open_hooks:
        if args.dry_run:
            print(
                "Dry run: would open a new terminal and start Codex CLI "
                "for manual /hooks review."
            )
        elif open_hook_trust_terminal(codex_command, pathlib.Path.cwd()):
            print(
                "Started Codex CLI in a new Terminal window. Type /hooks in "
                "that window, review the Voice Notify hook, and trust it."
            )
        else:
            print(
                "Could not open a new Codex CLI Terminal automatically. Start "
                "Codex CLI yourself, enter /hooks, and review the Voice Notify hook.",
                file=sys.stderr,
            )
            return 4
    else:
        print("Next: run Codex, enter /hooks, and review the Voice Notify hook.")
    print("After trust is granted, fully restart Codex before testing lifecycle events.")
    return 0


def main() -> int:
    args = build_parser().parse_args()
    settings = play_notify.load_settings()

    if args.command == "show":
        print(json.dumps(settings, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "reset":
        try:
            play_notify.user_settings_path().unlink()
        except FileNotFoundError:
            pass
        print("Defaults restored.")
        return 0
    if args.command in ("mute", "unmute"):
        settings["enabled"] = args.command == "unmute"
        destination = write_settings(settings)
        print("Saved %s" % destination)
        return 0
    if args.command == "set":
        if args.voice:
            settings["voice"] = args.voice
        if args.language:
            settings["language"] = args.language
        if args.min_interval_ms is not None:
            settings["min_interval_ms"] = max(0, min(args.min_interval_ms, 10_000))
        for event in args.enable_event or ():
            settings["events"][event] = True
        for event in args.disable_event or ():
            settings["events"][event] = False
        destination = write_settings(settings)
        print("Saved %s" % destination)
        return 0
    if args.command == "test":
        if args.voice:
            settings["voice"] = args.voice
        if args.language:
            settings["language"] = args.language
        settings["enabled"] = True
        settings["events"][args.event] = True
        audio_path = play_notify.select_audio_path(PLUGIN_ROOT, args.event, settings)
        if audio_path is None:
            print("Audio file is unavailable.", file=sys.stderr)
            return 1
        print(str(audio_path))
        if args.dry_run:
            return 0
        if not play_notify.player_available():
            print("No supported system WAV player is available.", file=sys.stderr)
            return 1
        return play_notify.play_audio_sync(audio_path)
    if args.command == "setup":
        return run_setup(args, settings)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
