from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("linux_play_notify", ROOT / "hooks" / "play_notify.py")
assert SPEC and SPEC.loader
play_notify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(play_notify)
CONFIG_SPEC = importlib.util.spec_from_file_location("linux_voice_config", ROOT / "scripts" / "voice_notify_config.py")
assert CONFIG_SPEC and CONFIG_SPEC.loader
voice_config = importlib.util.module_from_spec(CONFIG_SPEC)
CONFIG_SPEC.loader.exec_module(voice_config)


@unittest.skipIf(os.name == "nt", "Linux/POSIX audio tests run on macOS and Linux")
class LinuxNotifyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.platform = mock.patch.object(play_notify.sys, "platform", "linux")
        self.platform.start()
        self.addCleanup(self.platform.stop)

    def test_xdg_paths_follow_absolute_overrides_and_ignore_relative_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory)
            with mock.patch.dict(os.environ, {
                "HOME": str(base), "XDG_CONFIG_HOME": str(base / "config"),
                "XDG_CACHE_HOME": str(base / "cache"),
            }, clear=True):
                self.assertEqual(play_notify.user_settings_path(), base / "config/codex-voice-notify/settings.json")
                self.assertEqual(play_notify._runtime_dir(), base / "cache/codex-voice-notify")
            with mock.patch.dict(os.environ, {
                "HOME": str(base), "XDG_CONFIG_HOME": "relative", "XDG_CACHE_HOME": "relative",
            }, clear=True):
                self.assertEqual(play_notify.user_settings_path(), base / ".config/codex-voice-notify/settings.json")
                self.assertEqual(play_notify._runtime_dir(), base / ".cache/codex-voice-notify")

    def test_settings_writer_and_hook_reader_use_same_linux_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": directory}, clear=True):
                settings = play_notify.normalize_settings({"voice": "male", "language": "ru"})
                path = voice_config.write_settings(settings)
                self.assertEqual(path, play_notify.user_settings_path())
                self.assertEqual(play_notify.load_settings(), settings)
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_plugin_runtime_and_settings_overrides_take_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory)
            with mock.patch.dict(os.environ, {
                "CODEX_VOICE_NOTIFY_CONFIG": str(base / "prefs.json"),
                "PLUGIN_DATA": str(base / "runtime"),
                "XDG_CONFIG_HOME": str(base / "config"), "XDG_CACHE_HOME": str(base / "cache"),
            }, clear=True):
                self.assertEqual(play_notify.user_settings_path(), base / "prefs.json")
                self.assertEqual(play_notify._runtime_dir(), base / "runtime")

    def test_linux_player_priority_and_ffplay_arguments(self) -> None:
        available = {name: "/usr/bin/" + name for name, _ in play_notify.LINUX_PLAYERS}
        with mock.patch.object(play_notify.shutil, "which", side_effect=available.get):
            self.assertEqual(play_notify.player_command()[0], "/usr/bin/pw-play")
        for name, arguments in play_notify.LINUX_PLAYERS:
            with self.subTest(player=name):
                with mock.patch.object(play_notify.shutil, "which", side_effect=lambda value: "/usr/bin/" + value if value == name else None):
                    self.assertEqual(play_notify.player_command(), ("/usr/bin/" + name,) + arguments)
        with mock.patch.object(play_notify.shutil, "which", return_value=None):
            self.assertFalse(play_notify.player_available())
            with mock.patch.object(play_notify.subprocess, "run") as run:
                self.assertEqual(play_notify.play_audio_sync(pathlib.Path("/tmp/test.wav")), 1)
            run.assert_not_called()

    def test_player_gets_local_audio_environment_and_no_codex_secrets(self) -> None:
        with mock.patch.dict(os.environ, {
            "PATH": "/usr/bin:/bin", "HOME": "/tmp/test-home", "LANG": "en_US.UTF-8",
            "XDG_RUNTIME_DIR": "/run/user/1000", "XDG_CONFIG_HOME": "/tmp/test-home/.config",
            "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus",
            "OPENAI_API_KEY": "PRIVATE_SENTINEL", "CODEX_AUTH_TOKEN": "PRIVATE_SENTINEL",
            "PRIVATE_PROMPT": "PRIVATE_SENTINEL",
        }, clear=True):
            with mock.patch.object(play_notify, "player_command", return_value=("/usr/bin/paplay",)):
                with mock.patch.object(play_notify.subprocess, "run", return_value=mock.Mock(returncode=0)) as run:
                    self.assertEqual(play_notify.play_audio_sync(pathlib.Path("/tmp/test.wav")), 0)
        self.assertEqual(run.call_args.args[0], ("/usr/bin/paplay", "/tmp/test.wav"))
        environment = run.call_args.kwargs["env"]
        self.assertEqual(environment["XDG_RUNTIME_DIR"], "/run/user/1000")
        self.assertEqual(environment["HOME"], "/tmp/test-home")
        self.assertNotIn("PRIVATE_SENTINEL", repr(environment))
        self.assertEqual(run.call_args.kwargs["timeout"], 20)

    def test_detached_hook_dispatch_excludes_payload_and_credentials(self) -> None:
        payload = json.dumps({"hook_event_name": "Stop", "prompt": "PRIVATE_SENTINEL"}).encode()
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.dict(os.environ, {
                "PLUGIN_ROOT": str(ROOT), "PLUGIN_DATA": directory,
                "CODEX_VOICE_NOTIFY_CONFIG": str(pathlib.Path(directory) / "absent.json"),
                "XDG_RUNTIME_DIR": "/run/user/1000", "OPENAI_API_KEY": "PRIVATE_SENTINEL",
            }, clear=True):
                with mock.patch("sys.stdin.buffer.read", return_value=payload):
                    with mock.patch.object(play_notify.sys, "argv", ["play_notify.py"]):
                        with mock.patch.object(play_notify.subprocess, "Popen") as popen:
                            self.assertEqual(play_notify.main(), 0)
        popen.assert_called_once()
        self.assertNotIn("PRIVATE_SENTINEL", repr(popen.call_args))
        self.assertEqual(popen.call_args.kwargs["stdin"], play_notify.subprocess.DEVNULL)
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        self.assertTrue(popen.call_args.kwargs["close_fds"])
        self.assertEqual(popen.call_args.kwargs["env"]["XDG_RUNTIME_DIR"], "/run/user/1000")

    def test_worker_skips_recent_event_and_recovers_clock_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory)
            audio = base / "audio.wav"
            audio.write_bytes(b"mock WAV")
            lock = base / "playback.lock"
            timestamp = base / "playback.timestamp"
            with mock.patch.object(play_notify, "player_available", return_value=True):
                with mock.patch.object(play_notify.time, "time", return_value=1000.0):
                    with mock.patch.object(play_notify, "play_audio_sync", return_value=0) as play:
                        timestamp.write_text("999.9", encoding="ascii")
                        self.assertEqual(play_notify._play_worker(audio, lock, 450), 0)
                        play.assert_not_called()
                        timestamp.write_text("2000.0", encoding="ascii")
                        self.assertEqual(play_notify._play_worker(audio, lock, 450), 0)
                        play.assert_called_once_with(audio)

    def test_busy_playback_lock_drops_overlapping_event(self) -> None:
        if os.name == "nt":
            self.skipTest("POSIX file lock coverage runs on macOS and Linux")
        import fcntl
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory)
            audio = base / "audio.wav"
            audio.write_bytes(b"mock WAV")
            lock = base / "playback.lock"
            with lock.open("w") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                with mock.patch.object(play_notify, "player_available", return_value=True):
                    with mock.patch.object(play_notify, "play_audio_sync") as play:
                        self.assertEqual(play_notify._play_worker(audio, lock, 0), 0)
                play.assert_not_called()


class LinuxSetupTests(unittest.TestCase):
    def test_prerelease_and_build_versions_are_accepted_without_unrelated_numbers(self) -> None:
        for value in (
            "codex-cli 0.159.0-alpha.12.1", "codex-cli 0.159.0+build.5",
            "OpenAI Codex (v0.159.0-alpha.12.1+build.5)",
        ):
            with self.subTest(value=value):
                self.assertEqual(voice_config.parse_codex_version(value), (0, 159, 0))
        for value in ("codex-cli 0.159.0-alpha..1", "Version 0.159.0", "codex-cli 0.159.0\nextra"):
            self.assertIsNone(voice_config.parse_codex_version(value))

    def test_headless_linux_keeps_manual_review_available_without_launch(self) -> None:
        with mock.patch.object(voice_config.sys, "platform", "linux"):
            with mock.patch.dict(os.environ, {}, clear=True):
                with mock.patch.object(voice_config.subprocess, "Popen") as popen:
                    self.assertFalse(voice_config.open_hook_trust_terminal(pathlib.Path("/usr/bin/codex"), pathlib.Path("/tmp")))
        popen.assert_not_called()

    def test_linux_terminal_quotes_cli_and_working_directory_and_keeps_review(self) -> None:
        command = pathlib.Path("/opt/Codex CLI/codex")
        cwd = pathlib.Path("/tmp/user's workspace")
        with mock.patch.object(voice_config.sys, "platform", "linux"):
            with mock.patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True):
                with mock.patch.object(voice_config.shutil, "which", side_effect=lambda name: "/usr/bin/x-terminal-emulator" if name == "x-terminal-emulator" else None):
                    with mock.patch.object(voice_config.subprocess, "Popen") as popen:
                        self.assertTrue(voice_config.open_hook_trust_terminal(command, cwd))
        argv = popen.call_args.args[0]
        self.assertEqual(argv[:4], ("/usr/bin/x-terminal-emulator", "-e", "/bin/sh", "-c"))
        self.assertIn("exec %s --no-alt-screen -C %s" % (voice_config.shlex.quote(str(command)), voice_config.shlex.quote(str(cwd))), argv[4])
        self.assertIn("Type /hooks here", argv[4])


if __name__ == "__main__":
    unittest.main()
