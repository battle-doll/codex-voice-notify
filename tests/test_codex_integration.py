"""Opt-in real Codex integration in a disposable, unauthenticated profile.

The supplied CLI must already be installed. These tests never install a SDK,
use a user's Codex profile, start a model turn, play sound, or publish a plugin.
The digest approval below is synthetic consent for this test's isolated hooks.
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SELECTED_CODEX = os.environ.get("VOICE_NOTIFY_INTEGRATION_CODEX")
SPEC = importlib.util.spec_from_file_location(
    "integration_voice_hooks", ROOT / "scripts" / "voice_notify_hooks.py"
)
assert SPEC and SPEC.loader
hooks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hooks)

SAFE_FIELDS = (
    "installedHooks", "trustedHooks", "enabledHooks", "approvedHooks", "ready",
    "trusted", "enabled", "voiceEnabled", "settingsConfigured", "settingsValid",
    "playerAvailable", "lifecyclePlaybackVerified",
)


@unittest.skipUnless(SELECTED_CODEX, "Set VOICE_NOTIFY_INTEGRATION_CODEX to an installed CLI")
class RealCodexIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.codex = hooks.find_codex(SELECTED_CODEX)
        except (hooks.HookError, OSError, ValueError):
            self.fail("The integration CLI could not be resolved to a native executable.")
        self.directory = tempfile.TemporaryDirectory(prefix="voice-cli-test-")
        self.addCleanup(self.directory.cleanup)
        self.base = pathlib.Path(self.directory.name).resolve()
        self.profile = self.base / "codex-profile"
        self.workspace = self.base / "workspace"
        for directory in (self.profile, self.workspace, self.base / "home", self.base / "system-temp"):
            directory.mkdir(mode=0o700)
        # Do not inherit API keys, auth tokens, Codex session IDs or user profiles.
        system_names = ("PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC",
                        "LANG", "LC_ALL", "PROCESSOR_ARCHITECTURE", "PROCESSOR_ARCHITEW6432")
        self.environment = {name: os.environ[name] for name in system_names if name in os.environ}
        self.environment.update({
            "CODEX_HOME": str(self.profile),
            "HOME": str(self.base / "home"),
            "USERPROFILE": str(self.base / "home"),
            "APPDATA": str(self.base / "appdata"),
            "LOCALAPPDATA": str(self.base / "localappdata"),
            "XDG_CONFIG_HOME": str(self.base / "config"),
            "XDG_CACHE_HOME": str(self.base / "cache"),
            "CODEX_VOICE_NOTIFY_CONFIG": str(self.base / "voice-settings.json"),
            "PLUGIN_DATA": str(self.base / "voice-runtime"),
            "CODEX_VOICE_NOTIFY_NO_PLAY": "1",
            # Codex refuses PATH helper aliases when CODEX_HOME is below its
            # active OS temp directory. Keep these isolated siblings instead.
            "TMPDIR": str(self.base / "system-temp"),
            "TMP": str(self.base / "system-temp"), "TEMP": str(self.base / "system-temp"),
        })

    def run_local(self, command: list[str], stage: str, *, parse_json: bool = False) -> dict:
        try:
            completed = subprocess.run(
                command, cwd=self.workspace, env=self.environment,
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace", timeout=45, check=False,
            )
        except subprocess.TimeoutExpired:
            self.fail(stage + " timed out; private CLI output was suppressed.")
        except OSError:
            self.fail(stage + " could not start; private CLI output was suppressed.")
        if completed.returncode != 0:
            self.fail(stage + " failed (exit " + str(completed.returncode) + "); private CLI output was suppressed.")
        if not parse_json:
            return {}
        try:
            result = json.loads(completed.stdout)
        except ValueError:
            self.fail(stage + " did not return a JSON object; private CLI output was suppressed.")
        if not isinstance(result, dict):
            self.fail(stage + " did not return a JSON object; private CLI output was suppressed.")
        return result

    def require(self, condition: bool, stage: str, result: dict) -> None:
        if not condition:
            # Never expose source paths, commands, API errors, userAgent or full hook listings.
            safe = {key: result[key] for key in SAFE_FIELDS
                    if key in result and isinstance(result[key], (bool, int, type(None)))}
            self.fail(stage + " verification failed: " + json.dumps(safe, sort_keys=True))

    def installed_root(self) -> pathlib.Path:
        cache = self.profile / "plugins" / "cache"
        candidates = []
        for manifest in cache.glob("*/codex-voice-notify/*/.codex-plugin/plugin.json"):
            try:
                document = json.loads(manifest.read_text(encoding="utf-8"))
                plugin_root = manifest.parent.parent.resolve()
            except (OSError, ValueError):
                continue
            if document.get("name") == "codex-voice-notify" and cache.resolve() in plugin_root.parents:
                candidates.append(plugin_root)
        if len(candidates) != 1:
            self.fail("The isolated installation did not yield one Voice Notify cache root.")
        return candidates[0]

    def native_command(self, root: pathlib.Path, action: str, digest: str | None = None) -> list[str]:
        if os.name == "nt":
            # Exercise the shipped Windows PowerShell 5.1 path, not only PowerShell 7.
            system_root = os.environ.get("SYSTEMROOT") or os.environ.get("WINDIR")
            powershell = (pathlib.Path(system_root) / "System32/WindowsPowerShell/v1.0/powershell.exe") if system_root else None
            if powershell is None or not powershell.is_file():
                self.fail("Windows PowerShell 5.1 is required for the Windows integration test.")
            command = [str(powershell), "-NoLogo", "-NoProfile", "-NonInteractive",
                       "-ExecutionPolicy", "Bypass", "-File",
                       str(root / "scripts/voice_notify_config.ps1"), action,
                       "-CodexCommand", self.codex]
            if action == "setup":
                command.extend(("-Voice", "female", "-Language", "ko", "-SkipAudioTest"))
            if digest:
                command.extend(("-Approve", digest))
            return command
        if sys.platform == "darwin":
            command = ["/bin/sh", str(root / "scripts/voice_notify_config.sh"), action,
                       "--codex-command", self.codex]
        elif sys.platform.startswith("linux"):
            script = "voice_notify_config.py" if action == "setup" else "voice_notify_hooks.py"
            command = [sys.executable, str(root / "scripts" / script), action,
                       "--codex-command", self.codex]
        else:
            self.fail("This integration test supports Windows, macOS and Linux.")
        if action == "setup":
            command.extend(("--voice", "female", "--language", "ko", "--skip-audio-test"))
        if digest:
            command.extend(("--approve", digest))
        return command

    def test_isolated_install_setup_review_approval_and_retry(self) -> None:
        common = [self.codex, *hooks.APP_OVERRIDES]
        self.run_local(common + ["plugin", "marketplace", "add", str(ROOT), "--json"], "marketplace add")
        self.run_local(common + ["plugin", "add", "codex-voice-notify@codex-voice-notify", "--json"], "plugin add")
        root = self.installed_root()
        self.run_local(self.native_command(root, "setup"), "native setup")
        try:
            settings = json.loads((self.base / "voice-settings.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.fail("Native setup did not save valid isolated preferences.")
        self.require(settings.get("enabled") is True and settings.get("voice") == "female"
                     and settings.get("language") == "ko", "saved preferences", settings)
        before = self.run_local(self.native_command(root, "doctor"), "doctor before approval", parse_json=True)
        self.require(before.get("installedHooks") == 10 and before.get("trustedHooks") == 0
                     and before.get("ready") is False and before.get("lifecyclePlaybackVerified") is False,
                     "untrusted installed hooks", before)
        review = self.run_local(self.native_command(root, "review-hooks"), "native hook review", parse_json=True)
        digest = review.get("approvalDigest")
        self.require(isinstance(digest, str) and hooks.HASH_RE.fullmatch(digest) is not None
                     and isinstance(review.get("hooks"), list) and len(review["hooks"]) == 10,
                     "review digest", review)
        # TEST-ONLY consent: the isolated source and this digest are owned by this
        # disposable test. This never stands in for a real user's hook approval.
        approved = self.run_local(self.native_command(root, "approve-hooks", digest),
                                  "isolated test approval", parse_json=True)
        self.require(approved.get("approvedHooks") == 10 and approved.get("trusted") is True
                     and approved.get("enabled") is True and approved.get("lifecyclePlaybackVerified") is False,
                     "exact test approval", approved)
        after = self.run_local(self.native_command(root, "doctor"), "doctor after approval", parse_json=True)
        self.require(after.get("installedHooks") == 10 and after.get("trustedHooks") == 10
                     and after.get("enabledHooks") == 10 and after.get("ready") is True
                     and after.get("lifecyclePlaybackVerified") is False, "confirmed approval", after)
        retry = self.run_local(self.native_command(root, "approve-hooks", digest),
                               "idempotent test approval", parse_json=True)
        self.require(retry.get("approvedHooks") == 10 and retry.get("trusted") is True
                     and retry.get("enabled") is True and retry.get("approvalDigest") == digest
                     and retry.get("lifecyclePlaybackVerified") is False, "same-digest retry", retry)
        self.require(not (self.profile / "auth.json").exists(), "unauthenticated profile", {})
        version = after.get("codexVersion")
        self.require(isinstance(version, str) and re.fullmatch(
            r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.+-]+)?", version
        ) is not None, "verified CLI version", {})
        print("Real Codex integration passed: CLI " + version + "; isolated hooks 10/10, audio unverified.")


if __name__ == "__main__":
    unittest.main()
