"""Exercise native setup against prerelease CLI versions without saving preferences."""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import importlib.util

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("native_release_privacy", ROOT / "scripts/build_release.py")
RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RELEASE)


class ReleasePrivacyTests(unittest.TestCase):
    def test_secret_content_is_rejected_without_printing_secret(self) -> None:
        for secret in (b"sk" + b"-" + b"x" * 40, b"gh" + b"p_" + b"x" * 40,
                       b"token=" + b"x" * 40, b"-----BEGIN " + b"PRIVATE KEY-----"):
            with self.subTest(prefix=secret[:2]):
                with self.assertRaises(RELEASE.ReleaseBuildError) as caught:
                    RELEASE._check_snapshot_limits({"README.md": secret})
                self.assertNotIn(secret.decode(), str(caught.exception))

    def test_public_nickname_is_allowed(self) -> None:
        RELEASE._check_snapshot_limits({"README.md": b"Developer: battle-doll\n"})


class NativeSetupTests(unittest.TestCase):
    def _setup(self, version: str, warning: bool = False) -> tuple[int, bool]:
        with tempfile.TemporaryDirectory() as directory:
            temp = pathlib.Path(directory)
            settings = temp / "settings.json"
            environment = dict(os.environ, CODEX_VOICE_NOTIFY_CONFIG=str(settings))
            if os.name == "nt":
                fake = temp / "codex.cmd"
                fake.write_text(("@echo Compatibility warning 1>&2\n" if warning else "") + "@echo " + version + "\n", encoding="ascii")
                executable = shutil.which("powershell.exe") or shutil.which("pwsh")
                if not executable:
                    self.skipTest("PowerShell is unavailable")
                command = [executable, "-NoProfile", "-ExecutionPolicy", "Bypass",
                           "-File", str(ROOT / "scripts/voice_notify_config.ps1"),
                           "setup", "-DryRun", "-SkipAudioTest", "-CodexCommand", str(fake)]
            else:
                fake = temp / "codex"
                fake.write_text("#!/bin/sh\n" + ("printf '%s\\n' 'Compatibility warning' >&2\n" if warning else "") + "printf '%s\\n' '" + version + "'\n", encoding="ascii")
                fake.chmod(0o700)
                command = ["/bin/sh", str(ROOT / "scripts/voice_notify_config.sh"),
                           "setup", "--dry-run", "--skip-audio-test", "--codex-command", str(fake)]
            completed = subprocess.run(command, env=environment, capture_output=True, timeout=20)
            return completed.returncode, settings.exists()

    def test_current_desktop_prerelease_and_build_versions(self) -> None:
        for version in ("codex-cli 0.159.0-alpha.12.1", "codex-cli 0.159.0+desktop.1", "codex-cli 0.159.0"):
            with self.subTest(version=version):
                status, saved = self._setup(version)
                self.assertEqual(status, 0)
                self.assertFalse(saved)

    def test_old_and_malformed_versions_fail_without_saving(self) -> None:
        for version in ("codex-cli 0.144.9", "codex-cli 0.159.0-unexpected output", "unrelated 1.2.3"):
            with self.subTest(version=version):
                status, saved = self._setup(version)
                self.assertEqual(status, 3)
                self.assertFalse(saved)

    def test_valid_version_survives_unrelated_stderr_warning(self) -> None:
        status, saved = self._setup("codex-cli 0.159.0-alpha.12.1", warning=True)
        self.assertEqual(status, 0)
        self.assertFalse(saved)


if __name__ == "__main__":
    unittest.main()
