#!/usr/bin/env python3
"""Build a deterministic checksum manifest for the release WAV files."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import tempfile
import wave


ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIO_ROOT = ROOT / "assets" / "audio"


def main() -> int:
    plugin_manifest = json.loads(
        (ROOT / ".codex-plugin" / "plugin.json").read_text("utf-8")
    )
    phrases = json.loads((AUDIO_ROOT / "phrases.json").read_text("utf-8"))
    records = []
    for voice in ("female", "male"):
        for language in ("ko", "ja", "en"):
            for event, phrase in phrases.items():
                path = AUDIO_ROOT / voice / language / phrase["file"]
                payload = path.read_bytes()
                with wave.open(str(path), "rb") as wav:
                    record = {
                        "event": event,
                        "voice": voice,
                        "language": language,
                        "path": path.relative_to(ROOT).as_posix(),
                        "text": phrase[language],
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "bytes": len(payload),
                        "duration_seconds": round(
                            wav.getnframes() / float(wav.getframerate()), 6
                        ),
                        "sample_rate": wav.getframerate(),
                        "channels": wav.getnchannels(),
                        "sample_width_bytes": wav.getsampwidth(),
                    }
                records.append(record)

    manifest = {
        "schema_version": 1,
        "release": plugin_manifest["version"],
        "asset_count": len(records),
        "files": records,
    }
    destination = AUDIO_ROOT / "manifest.json"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(AUDIO_ROOT),
        prefix=".manifest.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary = pathlib.Path(handle.name)
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, destination)
    print("Wrote %s with %d files" % (destination, len(records)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
