from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "play_notify", ROOT / "hooks" / "play_notify.py"
)
assert SPEC and SPEC.loader
play_notify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(play_notify)


class VoiceNotifyTests(unittest.TestCase):
    def test_defaults_are_female_korean_and_enabled(self) -> None:
        settings = play_notify.normalize_settings(None)
        self.assertTrue(settings["enabled"])
        self.assertEqual(settings["voice"], "female")
        self.assertEqual(settings["language"], "ko")

    def test_invalid_settings_are_bounded(self) -> None:
        settings = play_notify.normalize_settings(
            {"voice": "../escape", "language": "xx", "min_interval_ms": 999999}
        )
        self.assertEqual(settings["voice"], "female")
        self.assertEqual(settings["language"], "ko")
        self.assertEqual(settings["min_interval_ms"], 10000)

    def test_malformed_config_falls_back_without_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "settings.json"
            path.write_text("{broken", encoding="utf-8")
            self.assertEqual(play_notify.load_settings(path)["voice"], "female")

    def test_select_audio_uses_whitelisted_path(self) -> None:
        settings = play_notify.normalize_settings({"voice": "male", "language": "en"})
        selected = play_notify.select_audio_path(ROOT, "Stop", settings)
        self.assertEqual(selected, ROOT / "assets" / "audio" / "male" / "en" / "stop.wav")

    def test_disabled_event_is_silent(self) -> None:
        settings = play_notify.normalize_settings(
            {"events": {"PreToolUse": False}}
        )
        self.assertIsNone(play_notify.select_audio_path(ROOT, "PreToolUse", settings))

    def test_unknown_event_is_silent(self) -> None:
        settings = play_notify.normalize_settings(None)
        self.assertIsNone(play_notify.select_audio_path(ROOT, "Unknown", settings))

    def test_no_play_mode_does_not_spawn(self) -> None:
        with mock.patch.dict(os.environ, {"CODEX_VOICE_NOTIFY_NO_PLAY": "1"}):
            with mock.patch.object(play_notify.subprocess, "Popen") as popen:
                play_notify.dispatch_playback(pathlib.Path("/tmp/example.wav"), 450)
        popen.assert_not_called()

    def test_hook_payload_is_not_forwarded_to_player(self) -> None:
        payload = {
            "hook_event_name": "Stop",
            "prompt": "PRIVATE_SENTINEL",
            "tool_input": {"secret": "PRIVATE_SENTINEL"},
        }
        with tempfile.TemporaryDirectory() as directory:
            config = pathlib.Path(directory) / "settings.json"
            config.write_text(json.dumps({"enabled": False}), encoding="utf-8")
            with mock.patch.dict(
                os.environ,
                {
                    "PLUGIN_ROOT": str(ROOT),
                    "CODEX_VOICE_NOTIFY_CONFIG": str(config),
                },
            ):
                with mock.patch("sys.stdin.buffer.read", return_value=json.dumps(payload).encode()):
                    self.assertEqual(play_notify.main(), 0)


if __name__ == "__main__":
    unittest.main()
