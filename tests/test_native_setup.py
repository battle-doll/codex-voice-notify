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
import time
import ctypes

ROOT = pathlib.Path(__file__).resolve().parents[1]
WINDOWS_POWERSHELL = (shutil.which("powershell.exe") or shutil.which("powershell")) if os.name == "nt" else None
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


@unittest.skipUnless(WINDOWS_POWERSHELL, "Windows native version probes require Windows PowerShell")
class WindowsNativeVersionProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory(prefix="voice-version-test-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.directory = pathlib.Path(cls.temp.name)
        cls.native = cls.directory / "native CLI & fixture" / "codex.exe"
        cls.native.parent.mkdir()
        source = cls.directory / "fake-version.cs"
        source.write_text('''using System;
using System.Diagnostics;
using System.IO;
using System.Threading;
public class FakeCodexVersion {
    public static int Main(string[] args) {
        if (args.Length != 1 || args[0] != "--version") return 9;
        string mode = Environment.GetEnvironmentVariable("VOICE_FAKE_VERSION_MODE");
        if (mode == "timeout") {
            File.WriteAllText(Environment.GetEnvironmentVariable("VOICE_FAKE_VERSION_PID"), Process.GetCurrentProcess().Id.ToString());
            Thread.Sleep(60000);
        }
        if (mode == "invalid") Console.WriteLine("unrelated 1.2.3");
        else Console.WriteLine("codex-cli 0.159.0-alpha.12.1");
        if (mode == "warning" || mode == "nonzero") {
            for (int i = 0; i < 4096; i++) Console.Error.WriteLine("PRIVATE_FAKE_VERSION_STDERR_WARNING " + new string('x', 192));
        }
        return mode == "nonzero" ? 7 : 0;
    }
}
''', encoding="ascii")
        compiler = cls.directory / "compile-fixture.ps1"
        compiler.write_text('''param([string]$Source,[string]$Destination)
$ErrorActionPreference='Stop'
Add-Type -TypeDefinition ([IO.File]::ReadAllText($Source)) -OutputAssembly $Destination -OutputType ConsoleApplication
''', encoding="ascii")
        result = subprocess.run([WINDOWS_POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(compiler),
                                 "-Source", str(source), "-Destination", str(cls.native)], capture_output=True, timeout=30)
        if result.returncode:
            raise AssertionError("The isolated native fixture could not be compiled: " + result.stderr.decode("utf-8", "replace"))
        cls.engines = [WINDOWS_POWERSHELL]
        modern = shutil.which("pwsh")
        if modern:
            cls.engines.append(modern)

    def run_setup(self, engine: str, mode: str, codex: pathlib.Path | None = None, dry_run: bool = False):
        folder = pathlib.Path(tempfile.mkdtemp(dir=self.directory, prefix="probe-"))
        settings = folder / "settings.json"
        baseline = b'{"enabled":false,"voice":"male"}\n'
        settings.write_bytes(baseline)
        pid_file = folder / "native.pid"
        environment = dict(os.environ, CODEX_VOICE_NOTIFY_CONFIG=str(settings),
                           VOICE_FAKE_VERSION_MODE=mode, VOICE_FAKE_VERSION_PID=str(pid_file))
        command = [engine, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "scripts/voice_notify_config.ps1"),
                   "setup", "-SkipAudioTest", "-CodexCommand", str(codex or self.native)]
        if dry_run:
            command.append("-DryRun")
        started = time.monotonic()
        result = subprocess.run(command, env=environment, capture_output=True, timeout=35)
        self.assertEqual(settings.read_bytes(), baseline, "A rejected or dry-run probe changed preferences")
        self.assertNotIn(b"PRIVATE_FAKE_VERSION_STDERR_WARNING", result.stdout + result.stderr)
        return result, time.monotonic() - started, pid_file

    def test_native_version_warning_and_large_stderr_do_not_block_setup(self) -> None:
        for engine in self.engines:
            with self.subTest(engine=engine):
                result, elapsed, _ = self.run_setup(engine, "warning", dry_run=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertLess(elapsed, 15)

    def test_nonzero_and_unrelated_native_stdout_reject_without_saving(self) -> None:
        for engine in self.engines:
            for mode in ("nonzero", "invalid"):
                with self.subTest(engine=engine, mode=mode):
                    result, _, _ = self.run_setup(engine, mode)
                    self.assertEqual(result.returncode, 3, result.stderr)

    def test_native_probe_times_out_and_kills_only_its_started_process(self) -> None:
        result, elapsed, pid_file = self.run_setup(WINDOWS_POWERSHELL, "timeout")
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertTrue(pid_file.is_file(), "The fake executable did not start")
        self.assertGreaterEqual(elapsed, 18)
        self.assertLess(elapsed, 30)
        pid = int(pid_file.read_text())
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = (ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32)
        kernel.OpenProcess.restype = ctypes.c_void_p
        handle = kernel.OpenProcess(0x1000, False, pid)
        if handle:
            try:
                status = ctypes.c_uint32()
                kernel.GetExitCodeProcess.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32))
                self.assertTrue(kernel.GetExitCodeProcess(handle, ctypes.byref(status)))
                self.assertNotEqual(status.value, 259, "The timed-out fake executable is still running")
            finally:
                kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
                kernel.CloseHandle(handle)

    def test_recognized_npm_shim_uses_native_probe_without_running_shell_text(self) -> None:
        prefix = self.directory / "npm prefix & fixture"
        main = prefix / "node_modules/@openai/codex"
        main.mkdir(parents=True)
        (main / "package.json").write_text('{"name":"@openai/codex"}', encoding="ascii")
        machine = (os.environ.get("PROCESSOR_ARCHITEW6432") or os.environ.get("PROCESSOR_ARCHITECTURE") or "AMD64").lower()
        arm = machine in {"arm64", "aarch64"}
        target = "aarch64-pc-windows-msvc" if arm else "x86_64-pc-windows-msvc"
        package = "codex-win32-arm64" if arm else "codex-win32-x64"
        native = prefix / "node_modules/@openai" / package / "vendor" / target / "bin/codex.exe"
        native.parent.mkdir(parents=True)
        shutil.copy2(self.native, native)
        shim = prefix / "codex.cmd"
        shim.write_text("@echo CMD_SHIM_MUST_NOT_EXECUTE\n", encoding="ascii")
        for engine in self.engines:
            with self.subTest(engine=engine):
                result, _, _ = self.run_setup(engine, "warning", codex=shim, dry_run=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn(b"CMD_SHIM_MUST_NOT_EXECUTE", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
