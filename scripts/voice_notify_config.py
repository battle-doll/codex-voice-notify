#!/usr/bin/env python3
"""Configure and test Voice Notify for Codex without external dependencies."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import tempfile


PLUGIN_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "hooks"))
import play_notify  # noqa: E402


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
    set_parser.add_argument("--language", choices=sorted(play_notify.LANGUAGES))
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
    test_parser.add_argument("--language", choices=sorted(play_notify.LANGUAGES))
    test_parser.add_argument("--dry-run", action="store_true")
    return parser


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
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
