#!/usr/bin/env python3
"""Review and narrowly approve installed hooks through the Codex local API.

No model turn, conversation read, direct trust-file edit, or global hook change.
The approval digest is an explicit, content-bound consent boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import platform
import queue
import re
import shutil
import subprocess
import sys
import threading
from typing import Any

PLUGIN_NAME = "codex-voice-notify"
ROOT = pathlib.Path(__file__).resolve().parents[1]
APP_OVERRIDES = ["-c", "analytics.enabled=false", "-c", "feedback.enabled=false",
                 "-c", 'otel.exporter="none"', "-c", "mcp_servers={}"]
HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")
CURRENT_HASH_RE = re.compile(r"^(?:sha256:)?[0-9a-fA-F]{64}$")


class HookError(RuntimeError):
    """A bounded, privacy-safe error suitable for local display."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def find_codex(explicit: str | None = None) -> str:
    if explicit:
        path = pathlib.Path(explicit).expanduser()
        if path.is_file():
            return resolve_codex_executable(path)
        found = shutil.which(explicit)
        if found:
            return resolve_codex_executable(pathlib.Path(found))
        raise HookError("Codex executable was not found. Update or install Codex first.")
    # Prefer the app's current binary to a potentially stale standalone CLI.
    candidates = [
        "/Applications/Codex.app/Contents/Resources/codex",
        "/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex",
    ]
    for candidate in candidates:
        if pathlib.Path(candidate).is_file():
            return candidate
    found = shutil.which("codex")
    if found:
        return resolve_codex_executable(pathlib.Path(found))
    raise HookError("Codex executable was not found. Update or install Codex first.")


def resolve_codex_executable(path: pathlib.Path, architecture: str | None = None) -> str:
    """Resolve an npm Windows shim to its associated native Codex, never a shell.

    Official npm layouts use a platform package's vendor/<target>/bin; older
    releases use vendor/<target>/codex. Both are accepted without executing or
    interpreting the .cmd/.bat/.ps1 wrapper itself.
    """
    path = path.resolve(strict=True)
    if path.suffix.lower() not in {".cmd", ".bat", ".ps1"}:
        return str(path)
    if path.stem.lower() != "codex":
        raise HookError("A shell wrapper cannot be used here. Select the native Codex executable.")
    machine = (architecture or os.environ.get("PROCESSOR_ARCHITEW6432") or
               os.environ.get("PROCESSOR_ARCHITECTURE") or platform.machine()).lower()
    if machine in {"arm64", "aarch64"}:
        target, package = "aarch64-pc-windows-msvc", "codex-win32-arm64"
    elif machine in {"amd64", "x86_64", "x64"}:
        target, package = "x86_64-pc-windows-msvc", "codex-win32-x64"
    else:
        raise HookError("This Codex npm shim has an unsupported Windows architecture. Select the native executable.")
    scopes = [path.parent / "node_modules" / "@openai"]
    if path.parent.name.lower() == ".bin":
        scopes.append(path.parent.parent / "@openai")
    for scope in scopes:
        main = scope / "codex"
        try:
            if (main / "package.json").stat().st_size > 65536:
                continue
            manifest = json.loads((main / "package.json").read_text("utf-8"))
            if manifest.get("name") != "@openai/codex":
                continue
        except (OSError, ValueError, AttributeError):
            continue
        roots = [scope / package, main / "node_modules" / "@openai" / package, main]
        for root in roots:
            for directory in ("bin", "codex"):
                candidate = root / "vendor" / target / directory / "codex.exe"
                if candidate.is_file():
                    return str(candidate.resolve())
    raise HookError("The npm Codex native executable is missing. Reinstall Codex or select its native executable.")


class AppServer:
    """Only initialize, hooks/list and the reviewed config/batchWrite are used."""
    def __init__(self, executable: str, cwd: pathlib.Path, timeout: float = 20):
        self.timeout = timeout
        self.request_id = 0
        self.messages: queue.Queue[Any] = queue.Queue()
        try:
            self.process = subprocess.Popen(
                [executable, "app-server", "--listen", "stdio://", *APP_OVERRIDES],
                cwd=str(cwd), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
        except OSError as exc:
            raise HookError("Could not start the local Codex app-server.") from exc
        threading.Thread(target=self._read, daemon=True).start()
        try:
            self.initialize_result = self.request("initialize", {
                "clientInfo": {"name": "codex-voice-notify", "version": "0.2.0"},
                "capabilities": {"experimentalApi": True}})
            self._send({"method": "initialized"})
        except BaseException:
            self.close()
            raise

    def _read(self) -> None:
        assert self.process.stdout
        try:
            while True:
                line = self.process.stdout.readline(2 * 1024 * 1024 + 1)
                if not line:
                    self.messages.put(HookError("The local Codex app-server stopped."))
                    return
                if len(line) > 2 * 1024 * 1024:
                    self.messages.put(HookError("The local API response exceeded the size limit."))
                    return
                try:
                    self.messages.put(json.loads(line))
                except ValueError:
                    self.messages.put(HookError("The local Codex API returned invalid JSON."))
                    return
        except (OSError, ValueError):
            self.messages.put(HookError("The local Codex API connection closed."))

    def _send(self, message: dict[str, Any]) -> None:
        assert self.process.stdin
        try:
            self.process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise HookError("The local Codex API connection closed.") from exc

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self.request_id += 1
        identifier = self.request_id
        self._send({"id": identifier, "method": method, "params": params})
        # Notifications never grant approval and are never exposed to output.
        import time
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                message = self.messages.get(timeout=max(0.001, deadline - time.monotonic()))
            except queue.Empty as exc:
                raise HookError("The local Codex API timed out. Update Codex and retry.") from exc
            if isinstance(message, HookError):
                raise message
            if not isinstance(message, dict):
                raise HookError("The local Codex API returned an invalid response.")
            if "method" in message and "id" in message:
                raise HookError("Unexpected interactive API request; no action was approved.")
            if message.get("id") != identifier:
                if time.monotonic() >= deadline:
                    raise HookError("The local Codex API timed out.")
                continue
            if "error" in message:
                # Server errors can include user paths or config values; keep them local/redacted.
                code = message["error"].get("code", "unknown") if isinstance(message["error"], dict) else "unknown"
                raise HookError(f"Codex API {method} failed (code {code}). Update Codex or use its /hooks review.")
            result = message.get("result")
            if not isinstance(result, dict):
                raise HookError("The local Codex API returned an invalid result.")
            return result

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        for pipe in (self.process.stdin, self.process.stdout):
            if pipe:
                pipe.close()

    def __enter__(self) -> "AppServer":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


def load_source(root: pathlib.Path) -> tuple[pathlib.Path, dict[str, Any], str, list[dict[str, Any]]]:
    root = root.resolve(strict=True)
    source = (root / "hooks" / "hooks.json").resolve(strict=True)
    if source.parent != root / "hooks":
        raise HookError("The hook source is outside this plugin. Refusing approval.")
    try:
        manifest = json.loads((root / ".codex-plugin" / "plugin.json").read_text("utf-8"))
        raw = source.read_bytes()
        document = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise HookError("Voice Notify's manifest or hook source is unavailable or invalid.") from exc
    if manifest.get("name") != PLUGIN_NAME or manifest.get("hooks") != "./hooks/hooks.json":
        raise HookError("This root is not the Voice Notify plugin hook source.")
    if len(raw) > 1024 * 1024:
        raise HookError("The hook source exceeded the size limit.")
    specifications = []
    groups_by_event = document.get("hooks", {})
    if not isinstance(groups_by_event, dict):
        raise HookError("The plugin hook source has an invalid event table.")
    for event, groups in groups_by_event.items():
        if not isinstance(event, str) or not isinstance(groups, list):
            raise HookError("The plugin hook source is invalid.")
        for group_index, group in enumerate(groups):
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                raise HookError("The plugin hook source is invalid.")
            for handler_index, handler in enumerate(group["hooks"]):
                if not isinstance(handler, dict) or handler.get("type") != "command":
                    raise HookError("Only the bundled command hooks can be reviewed here.")
                if not isinstance(handler.get("command"), str) or not isinstance(handler.get("commandWindows"), str):
                    raise HookError("Both Unix and Windows commands must be present for review.")
                specifications.append({"eventName": event[0].lower() + event[1:],
                    "matcher": group.get("matcher"), "command": handler["command"],
                    "commandWindows": handler["commandWindows"],
                    "timeoutSec": handler.get("timeout", 600), "async": handler.get("async", False),
                    "keySuffix": "hooks/hooks.json:" + re.sub(r"(?<!^)(?=[A-Z])", "_", event).lower()
                                 + f":{group_index}:{handler_index}"})
    if not specifications:
        raise HookError("No Voice Notify command hooks were found.")
    return source, manifest, hashlib.sha256(raw).hexdigest(), specifications


def command_matches(command: str, specification: dict[str, Any], root: pathlib.Path) -> bool:
    options = set()
    for key in ("command", "commandWindows"):
        raw = specification[key]
        options.update((raw, raw.replace("${PLUGIN_ROOT}", str(root)),
                        raw.replace("${PLUGIN_ROOT}", str(root).replace("/", "\\"))))
    return command in options


def build_review(root: pathlib.Path, listing: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    root = root.resolve(strict=True)
    source, manifest, source_hash, specifications = load_source(root)
    entries = listing.get("data")
    if not isinstance(entries, list) or len(entries) != 1:
        raise HookError("The hook listing did not identify one local workspace.")
    entry = entries[0]
    if not isinstance(entry, dict) or entry.get("errors"):
        raise HookError("Codex reported a hook configuration error. Fix it before review.")
    hooks = entry.get("hooks")
    if not isinstance(hooks, list):
        raise HookError("Codex returned an invalid hook listing.")
    selected = []
    for hook in hooks:
        if not isinstance(hook, dict):
            raise HookError("Codex returned an invalid hook entry.")
        try:
            listed_path = pathlib.Path(hook.get("sourcePath", "")).resolve()
        except (OSError, ValueError):
            raise HookError("Codex returned an invalid hook source path.")
        plugin_id = hook.get("pluginId") or ""
        same_name = isinstance(plugin_id, str) and plugin_id.split("@")[0] == PLUGIN_NAME
        if same_name and listed_path != source:
            raise HookError("Multiple Voice Notify plugin roots are active. Remove the duplicate before review.")
        if listed_path != source:
            continue
        if hook.get("source") != "plugin" or not same_name:
            raise HookError("The exact hook source is not an installed Voice Notify plugin.")
        if hook.get("isManaged") or hook.get("trustStatus") == "managed":
            raise HookError("Managed hooks require the administrator's Codex controls.")
        if hook.get("handlerType") != "command":
            raise HookError("Only Voice Notify command hooks may be approved.")
        if not isinstance(hook.get("key"), str) or not hook["key"]:
            raise HookError("Codex did not provide the exact hook state key.")
        if not isinstance(hook.get("currentHash"), str) or not CURRENT_HASH_RE.fullmatch(hook["currentHash"]):
            raise HookError("Codex did not provide a valid current hook hash.")
        if hook.get("trustStatus") not in {"untrusted", "modified", "trusted"}:
            raise HookError("Codex returned an unsupported hook trust state.")
        selected.append(hook)
    if not selected:
        raise HookError("Voice Notify is not active in this Codex workspace. Install and enable it first.")
    if len(selected) != len(specifications) or len({item["key"] for item in selected}) != len(selected):
        raise HookError("The installed hook list is incomplete or ambiguous. Refusing approval.")
    remaining = list(specifications)
    reviewed = []
    for hook in sorted(selected, key=lambda item: (item["eventName"], item["key"])):
        match = next((spec for spec in remaining if spec["eventName"] == hook.get("eventName")
                      and spec["matcher"] == hook.get("matcher")
                      and spec["timeoutSec"] == hook.get("timeoutSec")
                      and spec["async"] == hook.get("async", False)
                      and hook["key"] == hook["pluginId"] + ":" + spec["keySuffix"]
                      and command_matches(hook.get("command", ""), spec, root)), None)
        if match is None:
            raise HookError("A listed hook differs from the installed commands. Refusing approval.")
        remaining.remove(match)
        reviewed.append({**match, "key": hook["key"], "currentHash": hook["currentHash"],
                         "listedCommand": hook["command"], "pluginId": hook["pluginId"],
                         "enabled": hook["enabled"], "trustStatus": hook["trustStatus"]})
    files = {}
    for name in ("play_notify.sh", "play_notify.py", "play_notify.ps1"):
        path = root / "hooks" / name
        if path.is_file():
            if path.resolve().parent != root / "hooks":
                raise HookError("A playback script is outside this plugin. Refusing approval.")
            files["hooks/" + name] = hashlib.sha256(path.read_bytes()).hexdigest()
    snapshot = {"protocol": "voice-notify-hook-approval-v1", "pluginName": PLUGIN_NAME,
                "pluginVersion": manifest.get("version"), "pluginRoot": str(root),
                "sourcePath": str(source), "sourceSha256": source_hash,
                "playbackSha256": files, "hooks": reviewed}
    return snapshot, selected


def approval_digest(snapshot: dict[str, Any]) -> str:
    # Consent binds content and the requested enabled=true plan, not current state.
    # This permits retry after a successful write whose response was interrupted.
    bound = {**snapshot, "hooks": [{key: value for key, value in item.items()
                                  if key not in {"enabled", "trustStatus"}}
                                  for item in snapshot["hooks"]], "targetEnabled": True}
    return hashlib.sha256(canonical_json(bound)).hexdigest()


def public_review(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {"plugin": PLUGIN_NAME, "version": snapshot["pluginVersion"],
            "source": "hooks/hooks.json", "sourceSha256": snapshot["sourceSha256"],
            "playbackSha256": snapshot["playbackSha256"],
            "hooks": [{key: item[key] for key in ("eventName", "matcher", "command",
                       "commandWindows", "timeoutSec", "async", "currentHash", "enabled", "trustStatus")}
                      for item in snapshot["hooks"]],
            "approvalDigest": approval_digest(snapshot),
            "approvalEffect": "Trust these exact installed hashes and enable only these Voice Notify hooks.",
            "next": "After reviewing every command, explicitly approve this approvalDigest."}


def list_hooks(server: AppServer, cwd: pathlib.Path) -> dict[str, Any]:
    return server.request("hooks/list", {"cwds": [str(cwd.resolve())]})


def approve(server: AppServer, root: pathlib.Path, cwd: pathlib.Path, digest: str) -> dict[str, Any]:
    if not HASH_RE.fullmatch(digest):
        raise HookError("Explicit approval requires the 64-character digest from review-hooks.")
    snapshot, hooks = build_review(root, list_hooks(server, cwd))
    if approval_digest(snapshot) != digest.lower():
        raise HookError("Approval is stale: the hook review changed. Run review-hooks again and request fresh approval.")
    states = {item["key"]: {"trusted_hash": item["currentHash"], "enabled": True} for item in hooks}
    server.request("config/batchWrite", {"edits": [{"keyPath": "hooks.state", "value": states,
                   "mergeStrategy": "upsert"}], "filePath": None, "expectedVersion": None,
                   "reloadUserConfig": True})
    after_snapshot, after_hooks = build_review(root, list_hooks(server, cwd))
    before = {item["key"]: item["currentHash"] for item in hooks}
    after = {item["key"]: item["currentHash"] for item in after_hooks}
    if before != after or snapshot["sourceSha256"] != after_snapshot["sourceSha256"] or snapshot["playbackSha256"] != after_snapshot["playbackSha256"]:
        raise HookError("Hook content changed during approval; run a fresh review before using hooks.")
    if any(item["trustStatus"] != "trusted" or item["enabled"] is not True for item in after_hooks):
        raise HookError("Codex did not confirm every reviewed hook as trusted and enabled.")
    return {"plugin": PLUGIN_NAME, "source": "hooks/hooks.json", "approvedHooks": len(hooks),
            "trusted": True, "enabled": True, "approvalDigest": digest.lower(),
            "lifecyclePlaybackVerified": False,
            "next": "Start a new Codex session and test a natural lifecycle event."}


def doctor(root: pathlib.Path, listing: dict[str, Any]) -> dict[str, Any]:
    try:
        snapshot, hooks = build_review(root, listing)
    except HookError as exc:
        return {"plugin": PLUGIN_NAME, "source": "hooks/hooks.json", "ready": False,
                "reason": str(exc), "lifecyclePlaybackVerified": False}
    return {"plugin": PLUGIN_NAME, "version": snapshot["pluginVersion"], "source": "hooks/hooks.json",
            "installedHooks": len(hooks), "trustedHooks": sum(h["trustStatus"] == "trusted" for h in hooks),
            "enabledHooks": sum(h["enabled"] is True for h in hooks),
            "ready": all(h["trustStatus"] == "trusted" and h["enabled"] is True for h in hooks),
            "lifecyclePlaybackVerified": False}


def local_runtime_status(initialize_result: dict[str, Any]) -> dict[str, Any]:
    version_match = re.search(r"(?<![0-9])(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)",
                              str(initialize_result.get("userAgent", "")))
    version = version_match.group(1) if version_match else None
    event_names = ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "PermissionRequest",
                   "PreCompact", "PostCompact", "SubagentStart", "SubagentStop", "Stop")
    settings: dict[str, Any] = {}
    override = os.environ.get("CODEX_VOICE_NOTIFY_CONFIG")
    config_base = os.environ.get("XDG_CONFIG_HOME", "") if sys.platform.startswith("linux") else ""
    base = pathlib.Path(config_base) if config_base and pathlib.Path(config_base).is_absolute() else pathlib.Path.home() / ".config"
    path = pathlib.Path(override).expanduser() if override else base / PLUGIN_NAME / "settings.json"
    configured = path.is_file()
    valid = True
    try:
        if configured:
            if path.stat().st_size > 65536:
                raise ValueError("size")
            settings = json.loads(path.read_text("utf-8"))
            if not isinstance(settings, dict):
                raise ValueError("type")
    except (OSError, ValueError):
        valid = False
        settings = {}
    preferences = settings.get("events", {})
    if not isinstance(preferences, dict):
        preferences = {}
    enabled = settings.get("enabled", True)
    if not isinstance(enabled, bool):
        enabled = True
    desired = [event for event in event_names if (preferences.get(event) if isinstance(preferences.get(event), bool)
                                                 else event not in {"PreToolUse", "PostToolUse"})]
    if sys.platform == "darwin":
        player = "afplay" if pathlib.Path("/usr/bin/afplay").is_file() else None
    elif os.name == "nt":
        player = "System.Media.SoundPlayer"
    else:
        player = next((name for name in ("pw-play", "paplay", "aplay", "ffplay") if shutil.which(name)), None)
    return {"codexVersion": version, "codexPrerelease": ("-" in version) if version else None,
            "settingsConfigured": configured, "settingsValid": valid, "voiceEnabled": enabled,
            "desiredVoiceEvents": desired, "audioPlayer": player, "playerAvailable": player is not None}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("doctor", "review-hooks", "approve-hooks"))
    parser.add_argument("--approve", help="Exact digest approved by the user after review-hooks")
    parser.add_argument("--codex", "--codex-command", dest="codex", help="Current local Codex executable")
    parser.add_argument("--plugin-root", type=pathlib.Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        if args.action == "approve-hooks" and not args.approve:
            raise HookError("Run review-hooks and obtain explicit user approval of its digest first.")
        if args.action != "approve-hooks" and args.approve:
            raise HookError("--approve is only accepted with approve-hooks.")
        cwd = pathlib.Path.cwd()
        with AppServer(find_codex(args.codex), cwd) as server:
            if args.action == "approve-hooks":
                result = approve(server, args.plugin_root, cwd, args.approve)
            else:
                listing = list_hooks(server, cwd)
                result = doctor(args.plugin_root, listing) if args.action == "doctor" else public_review(build_review(args.plugin_root, listing)[0])
                if args.action == "doctor":
                    result.update(local_runtime_status(server.initialize_result))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (HookError, OSError, ValueError) as exc:
        # Filesystem exceptions contain personal paths. Only custom bounded messages are exposed.
        message = str(exc) if isinstance(exc, HookError) else "The local plugin files could not be read safely."
        print("Voice Notify: " + message, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
