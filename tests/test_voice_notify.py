from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import tempfile
import types
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "play_notify", ROOT / "hooks" / "play_notify.py"
)
assert SPEC and SPEC.loader
play_notify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(play_notify)

CONFIG_SPEC = importlib.util.spec_from_file_location(
    "voice_notify_config", ROOT / "scripts" / "voice_notify_config.py"
)
assert CONFIG_SPEC and CONFIG_SPEC.loader
voice_notify_config = importlib.util.module_from_spec(CONFIG_SPEC)
CONFIG_SPEC.loader.exec_module(voice_notify_config)


class VoiceNotifyTests(unittest.TestCase):
    def test_defaults_are_female_korean_and_enabled(self) -> None:
        settings = play_notify.normalize_settings(None)
        self.assertTrue(settings["enabled"])
        self.assertEqual(settings["voice"], "female")
        self.assertEqual(settings["language"], "ko")
        self.assertFalse(settings["events"]["PreToolUse"])
        self.assertFalse(settings["events"]["PostToolUse"])
        for event_name in play_notify.EVENT_FILES:
            if event_name not in {"PreToolUse", "PostToolUse"}:
                self.assertTrue(settings["events"][event_name])

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

    def test_tool_events_are_silent_by_default(self) -> None:
        settings = play_notify.normalize_settings(None)
        self.assertIsNone(play_notify.select_audio_path(ROOT, "PreToolUse", settings))
        self.assertIsNone(play_notify.select_audio_path(ROOT, "PostToolUse", settings))

    def test_tool_events_can_be_enabled_explicitly(self) -> None:
        settings = play_notify.normalize_settings(
            {"events": {"PreToolUse": True, "PostToolUse": True}}
        )
        self.assertIsNotNone(play_notify.select_audio_path(ROOT, "PreToolUse", settings))
        self.assertIsNotNone(play_notify.select_audio_path(ROOT, "PostToolUse", settings))

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


class VoiceNotifySetupTests(unittest.TestCase):
    def setup_args(self, **overrides: object) -> types.SimpleNamespace:
        values = {
            "voice": "female",
            "language": "ko",
            "skip_audio_test": False,
            "open_hooks": True,
            "codex_command": None,
            "dry_run": True,
        }
        values.update(overrides)
        return types.SimpleNamespace(**values)

    def test_parse_codex_version(self) -> None:
        self.assertEqual(
            voice_notify_config.parse_codex_version("codex-cli 0.145.0"),
            (0, 145, 0),
        )
        self.assertEqual(
            voice_notify_config.parse_codex_version("OpenAI Codex (v0.145.0)"),
            (0, 145, 0),
        )
        self.assertIsNone(
            voice_notify_config.parse_codex_version(
                "Microsoft Windows [Version 10.0.26200.0]"
            )
        )
        self.assertIsNone(
            voice_notify_config.parse_codex_version("codex-cli 0.145.0-alpha.1")
        )
        self.assertIsNone(voice_notify_config.parse_codex_version("unknown"))

    def test_failed_version_command_is_not_accepted(self) -> None:
        completed = mock.Mock(returncode=1, stdout="codex-cli 0.145.0")
        with mock.patch.object(
            voice_notify_config,
            "find_codex_command",
            return_value=pathlib.Path("/usr/local/bin/codex"),
        ):
            with mock.patch.object(
                voice_notify_config.subprocess, "run", return_value=completed
            ):
                command, version, output = voice_notify_config.inspect_codex()
        self.assertEqual(command, pathlib.Path("/usr/local/bin/codex"))
        self.assertIsNone(version)
        self.assertEqual(output, "codex-cli 0.145.0")

    def test_setup_requires_codex_with_hooks_support(self) -> None:
        settings = play_notify.normalize_settings(None)
        with mock.patch.object(
            voice_notify_config,
            "inspect_codex",
            return_value=(pathlib.Path("/usr/local/bin/codex"), (0, 116, 0), "0.116.0"),
        ):
            with mock.patch.object(voice_notify_config, "write_settings") as write:
                with mock.patch.object(
                    voice_notify_config, "open_hook_trust_terminal"
                ) as open_terminal:
                    status = voice_notify_config.run_setup(self.setup_args(), settings)
        self.assertEqual(status, 3)
        write.assert_not_called()
        open_terminal.assert_not_called()

    def test_setup_dry_run_reaches_hook_step(self) -> None:
        settings = play_notify.normalize_settings(None)
        with mock.patch.object(
            voice_notify_config,
            "inspect_codex",
            return_value=(pathlib.Path("/usr/local/bin/codex"), (0, 145, 0), "0.145.0"),
        ):
            status = voice_notify_config.run_setup(self.setup_args(), settings)
        self.assertEqual(status, 0)

    def test_setup_saves_selected_preferences(self) -> None:
        settings = play_notify.normalize_settings(None)
        with tempfile.TemporaryDirectory() as directory:
            destination = pathlib.Path(directory) / "settings.json"
            with mock.patch.object(
                voice_notify_config.play_notify,
                "user_settings_path",
                return_value=destination,
            ):
                with mock.patch.object(
                    voice_notify_config,
                    "inspect_codex",
                    return_value=(
                        pathlib.Path("/usr/local/bin/codex"),
                        (0, 145, 0),
                        "0.145.0",
                    ),
                ):
                    status = voice_notify_config.run_setup(
                        self.setup_args(
                            voice="male",
                            language="ja",
                            skip_audio_test=True,
                            open_hooks=False,
                            dry_run=False,
                        ),
                        settings,
                    )
            saved = json.loads(destination.read_text(encoding="utf-8"))
        self.assertEqual(status, 0)
        self.assertTrue(saved["enabled"])
        self.assertEqual(saved["voice"], "male")
        self.assertEqual(saved["language"], "ja")

    def test_macos_hook_terminal_command_keeps_human_review(self) -> None:
        completed = mock.Mock(returncode=0)
        codex_path = pathlib.PurePosixPath("/Applications/Codex CLI/codex")
        working_directory = pathlib.PurePosixPath("/tmp/user's example")
        with mock.patch.object(voice_notify_config.sys, "platform", "darwin"):
            with mock.patch.object(
                voice_notify_config.pathlib.Path, "is_file", return_value=True
            ):
                with mock.patch.object(
                    voice_notify_config.subprocess, "run", return_value=completed
                ) as run:
                    opened = voice_notify_config.open_hook_trust_terminal(
                        codex_path,
                        working_directory,
                    )
        self.assertTrue(opened)
        command = run.call_args.args[0]
        self.assertEqual(command[0].replace("\\", "/"), "/usr/bin/osascript")
        self.assertEqual(command[1], "-e")
        self.assertIn("/hooks", command[2])
        self.assertIn('tell application "Terminal"', command[2])
        self.assertIn("activate", command[2])
        self.assertIn("do script", command[2])
        expected_exec = "exec %s --no-alt-screen -C %s" % (
            voice_notify_config.shlex.quote(str(codex_path)),
            voice_notify_config.shlex.quote(str(working_directory)),
        )
        self.assertIn(
            voice_notify_config._apple_script_string(expected_exec),
            command[2],
        )
        self.assertNotIn("--dangerously-bypass-hook-trust", command[2])


if __name__ == "__main__":
    unittest.main()
