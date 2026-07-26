#!/usr/bin/env python3
"""Run the minimal release checks for a Voice Notify package."""

from __future__ import annotations

import array
import hashlib
import json
import pathlib
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
    manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text("utf-8"))
    hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text("utf-8"))
    if manifest.get("name") != "codex-voice-notify":
        fail("unexpected plugin name")
    if set(hooks.get("hooks", {})) != EXPECTED_EVENTS:
        fail("hook event set does not match the release contract")

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
    records = audio_manifest.get("files", ())
    if audio_manifest.get("asset_count") != 60 or len(records) != 60:
        fail("audio manifest must contain 60 files")
    for record in records:
        path = ROOT / record["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != record["sha256"]:
            fail("audio checksum mismatch: %s" % path)

    evals = json.loads((ROOT / "evals" / "cases.json").read_text("utf-8"))
    if len(evals.get("positive", ())) != 5 or len(evals.get("negative", ())) != 3:
        fail("submission evals must contain exactly 5 positive and 3 negative cases")

    print(
        "PASS: manifest, 10 hooks, 60 WAVs, checksums, format, signal, clipping, and 5+3 evals "
        "(%.2f-%.2fs)" % (min(durations), max(durations))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
