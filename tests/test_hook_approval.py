from __future__ import annotations

import copy
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("voice_notify_hooks", ROOT / "scripts/voice_notify_hooks.py")
assert SPEC and SPEC.loader
hooks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hooks)


class FakeServer:
    def __init__(self, listing: dict, confirm: bool = True):
        self.listing = copy.deepcopy(listing)
        self.writes: list[dict] = []
        self.confirm = confirm

    def request(self, method: str, params: dict) -> dict:
        if method == "hooks/list":
            return copy.deepcopy(self.listing)
        if method == "config/batchWrite":
            self.writes.append(copy.deepcopy(params))
            if self.confirm:
                state = params["edits"][0]["value"]
                for item in self.listing["data"][0]["hooks"]:
                    if item["key"] in state:
                        item["enabled"] = state[item["key"]]["enabled"]
                        item["trustStatus"] = "trusted"
            return {"status": "ok"}
        raise AssertionError(method)


class HookApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="voice-hook-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name) / "private-user" / "plugin"
        (self.root / "hooks").mkdir(parents=True)
        (self.root / ".codex-plugin").mkdir()
        self.root = self.root.resolve()
        (self.root / ".codex-plugin/plugin.json").write_text(json.dumps({"name":"codex-voice-notify", "version":"0.2.0", "hooks":"./hooks/hooks.json"}))
        self.doc = {"hooks": {"Stop":[{"hooks":[{"type":"command", "command":'/bin/sh "${PLUGIN_ROOT}/hooks/play_notify.sh"', "commandWindows":'powershell.exe -File "${PLUGIN_ROOT}\\hooks\\play_notify.ps1"', "timeout":5}]}]}}
        (self.root / "hooks/hooks.json").write_text(json.dumps(self.doc))
        (self.root / "hooks/play_notify.sh").write_text("#!/bin/sh\nexit 0\n")
        (self.root / "hooks/play_notify.py").write_text("# inert playback fixture\n")
        (self.root / "hooks/play_notify.ps1").write_text("# inert playback fixture\n")
        self.plugin_id = 'codex-voice-notify@local.name "quoted"'
        self.own = {"source":"plugin", "sourcePath":str(self.root / "hooks/hooks.json"), "pluginId":self.plugin_id,
                    "handlerType":"command", "command":self.doc["hooks"]["Stop"][0]["hooks"][0]["command"].replace("${PLUGIN_ROOT}",str(self.root)),
                    "eventName":"stop", "matcher":None, "timeoutSec":5, "async":False, "isManaged":False,
                    "key":self.plugin_id+":hooks/hooks.json:stop:0:0", "currentHash":"sha256:"+"a"*64,
                    "enabled":False, "trustStatus":"untrusted", "displayOrder":0}
        other_file = pathlib.Path(self.temp.name) / "other-hooks.json"; other_file.write_text("{}")
        self.other = {**self.own,"sourcePath":str(other_file),"pluginId":"other-plugin@market","key":"other-plugin:untouched","currentHash":"sha256:"+"b"*64}
        self.listing = {"data":[{"cwd":str(self.root),"errors":[],"warnings":[],"hooks":[self.own,self.other]}]}

    def snapshot(self, listing=None):
        return hooks.build_review(self.root, listing or self.listing)[0]

    def test_review_discloses_both_platform_commands_without_private_paths(self):
        review = hooks.public_review(self.snapshot())
        self.assertEqual(review["hooks"][0]["currentHash"], self.own["currentHash"])
        self.assertIn("${PLUGIN_ROOT}", review["hooks"][0]["command"])
        self.assertIn("powershell.exe", review["hooks"][0]["commandWindows"])
        self.assertNotIn(str(self.temp.name), json.dumps(review))
        self.assertRegex(review["approvalDigest"], r"^[0-9a-f]{64}$")

    def test_approval_upserts_only_exact_keys_and_verifies_trust(self):
        server = FakeServer(self.listing)
        digest = hooks.approval_digest(self.snapshot())
        result = hooks.approve(server,self.root,self.root,digest)
        self.assertTrue(result["trusted"])
        self.assertFalse(result["lifecyclePlaybackVerified"])
        self.assertEqual(server.writes,[{"edits":[{"keyPath":"hooks.state","value":{self.own["key"]:{"trusted_hash":self.own["currentHash"],"enabled":True}},"mergeStrategy":"upsert"}],"filePath":None,"expectedVersion":None,"reloadUserConfig":True}])
        self.assertEqual(server.listing["data"][0]["hooks"][1], self.other)
        # A lost response can be safely retried with identical content and plan.
        self.assertTrue(hooks.approve(server,self.root,self.root,digest)["trusted"])

    def test_missing_approval_does_not_start_codex(self):
        result = subprocess.run([sys.executable,str(ROOT / "scripts/voice_notify_hooks.py"),"approve-hooks","--codex","does-not-exist"],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertIn("explicit user approval",result.stderr)
        self.assertNotIn("executable",result.stderr)

    def test_changed_runtime_hash_rejects_before_write(self):
        digest = hooks.approval_digest(self.snapshot())
        changed = copy.deepcopy(self.listing); changed["data"][0]["hooks"][0]["currentHash"]="sha256:"+"c"*64
        server = FakeServer(changed)
        with self.assertRaisesRegex(hooks.HookError,"stale"):
            hooks.approve(server,self.root,self.root,digest)
        self.assertEqual(server.writes,[])

    def test_changed_source_and_playback_reject_before_write(self):
        for path in (self.root / "hooks/hooks.json",self.root / "hooks/play_notify.sh"):
            digest = hooks.approval_digest(self.snapshot()); path.write_text(path.read_text()+"\n")
            server = FakeServer(self.listing)
            with self.assertRaisesRegex(hooks.HookError,"stale"):
                hooks.approve(server,self.root,self.root,digest)
            self.assertEqual(server.writes,[])

    def test_forged_other_plugin_state_key_is_rejected(self):
        changed=copy.deepcopy(self.listing); changed["data"][0]["hooks"][0]["key"]=self.other["key"]
        with self.assertRaisesRegex(hooks.HookError,"differs"):
            self.snapshot(changed)

    def test_changed_commands_managed_missing_and_duplicate_are_rejected(self):
        changes=[{"command":"run-unreviewed-command"},{"isManaged":True},{"source":"user"},{"currentHash":"invalid"}]
        for change in changes:
            with self.subTest(change=change):
                changed=copy.deepcopy(self.listing); changed["data"][0]["hooks"][0].update(change)
                with self.assertRaises(hooks.HookError): self.snapshot(changed)
        missing=copy.deepcopy(self.listing); missing["data"][0]["hooks"]=[self.other]
        self.assertFalse(hooks.doctor(self.root,missing)["ready"])
        duplicate=copy.deepcopy(self.listing); duplicate["data"][0]["hooks"].append({**self.own,"sourcePath":self.other["sourcePath"]})
        with self.assertRaisesRegex(hooks.HookError,"Multiple"): self.snapshot(duplicate)

    def test_unconfirmed_trust_fails_after_api_write(self):
        server=FakeServer(self.listing,confirm=False)
        with self.assertRaisesRegex(hooks.HookError,"did not confirm"):
            hooks.approve(server,self.root,self.root,hooks.approval_digest(self.snapshot()))
        self.assertEqual(len(server.writes),1)

    def make_fake_executable(self):
        # Every helper launches [executable, "app-server", ...]. A real Python
        # executable + a private cwd/app-server fixture works with CreateProcess
        # on Windows as well as POSIX, with no shebang or shell-wrapper reliance.
        fake=pathlib.Path(sys.executable)
        fake_script=self.root/"app-server"
        listing=pathlib.Path(self.temp.name)/"listing.json"; listing.write_text(json.dumps(self.listing))
        writes=pathlib.Path(self.temp.name)/"writes.json"
        fake_script.write_text('''import json, os, sys
path=os.environ["VOICE_FAKE_LISTING"]
listing=json.load(open(path))
for line in sys.stdin:
    message=json.loads(line)
    if "id" not in message: continue
    method=message["method"]
    if method=="initialize": result={"userAgent":"fake-local"}
    elif method=="hooks/list": result=listing
    elif method=="config/batchWrite":
        json.dump(message["params"],open(os.environ["VOICE_FAKE_WRITES"],"w"))
        state=message["params"]["edits"][0]["value"]
        for hook in listing["data"][0]["hooks"]:
            if hook["key"] in state: hook.update(enabled=True,trustStatus="trusted")
        result={"status":"ok"}
    else: raise RuntimeError("Unexpected API method")
    print(json.dumps({"id":message["id"],"result":result}),flush=True)
''')
        return fake,writes,{**os.environ,"VOICE_FAKE_LISTING":str(listing),"VOICE_FAKE_WRITES":str(writes)}

    def test_python_stdio_wire_and_config_override_scope(self):
        fake,writes,environment=self.make_fake_executable()
        command=[sys.executable,str(ROOT / "scripts/voice_notify_hooks.py"),"approve-hooks","--approve",hooks.approval_digest(self.snapshot()),"--plugin-root",str(self.root),"--codex-command",str(fake)]
        result=subprocess.run(command,cwd=self.root,env=environment,capture_output=True,text=True,timeout=25)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(json.loads(result.stdout)["trusted"])
        self.assertEqual(set(json.loads(writes.read_text())["edits"][0]["value"]),{self.own["key"]})
        self.assertIn("analytics.enabled=false",hooks.APP_OVERRIDES)
        self.assertIn("mcp_servers={}",hooks.APP_OVERRIDES)
        self.assertNotIn("hooks.enabled=true",hooks.APP_OVERRIDES)

    def make_npm_shim(self, architecture="x64", legacy=False, local_bin=False):
        prefix=pathlib.Path(self.temp.name)/"npm prefix & 100%! (local)"
        scope=prefix/"node_modules/@openai"
        main=scope/"codex"; main.mkdir(parents=True,exist_ok=True)
        (main/"package.json").write_text(json.dumps({"name":"@openai/codex"}))
        shim_dir=prefix/"node_modules/.bin" if local_bin else prefix
        shim_dir.mkdir(parents=True,exist_ok=True)
        shim=shim_dir/"codex.cmd"
        # The helper must never execute or interpret this shell text.
        marker=prefix/"shim-must-not-execute"
        shim.write_text('@echo off\r\necho bad > "'+str(marker)+'"\r\n')
        target="aarch64-pc-windows-msvc" if architecture=="arm64" else "x86_64-pc-windows-msvc"
        package="codex-win32-arm64" if architecture=="arm64" else "codex-win32-x64"
        root=main if legacy else scope/package
        native=root/"vendor"/target/("codex" if legacy else "bin")/"codex.exe"
        native.parent.mkdir(parents=True,exist_ok=True); native.write_bytes(b"MZ-inert-native-path-fixture")
        return shim,native,marker

    def test_windows_npm_shims_resolve_current_legacy_arm64_and_local_layouts_without_shell(self):
        for architecture,legacy,local_bin in (("x64",False,False),("arm64",False,False),("x64",True,True)):
            with self.subTest(architecture=architecture,legacy=legacy,local_bin=local_bin):
                shim,native,marker=self.make_npm_shim(architecture,legacy,local_bin)
                # Remove previously-created alternate current layout for the legacy case.
                if legacy:
                    current=native.parents[4]/"codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe"
                    if current.is_file(): current.unlink()
                resolved=hooks.resolve_codex_executable(shim,architecture)
                self.assertEqual(resolved,str(native.resolve()))
                self.assertFalse(marker.exists())

    def test_windows_shell_shim_without_official_native_codex_fails_closed(self):
        shim,native,marker=self.make_npm_shim()
        native.unlink()
        with self.assertRaisesRegex(hooks.HookError,"native executable is missing"):
            hooks.resolve_codex_executable(shim,"x64")
        self.assertFalse(marker.exists())
        unrelated=shim.with_name("arbitrary.cmd"); unrelated.write_text(shim.read_text())
        with self.assertRaisesRegex(hooks.HookError,"shell wrapper"):
            hooks.resolve_codex_executable(unrelated,"x64")

    @unittest.skipUnless(shutil.which("pwsh"),"PowerShell runtime unavailable")
    def test_powershell_resolves_npm_native_executable_without_invoking_cmd(self):
        shim,native,marker=self.make_npm_shim()
        runner=pathlib.Path(self.temp.name)/"resolve-native.ps1"
        runner.write_text('''param([string]$Helper,[string]$Shim)
$ErrorActionPreference='Stop'
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($Helper,[ref]$tokens,[ref]$errors)
if($errors.Count) { throw 'Helper syntax is invalid' }
foreach($name in @('Stop-HookAction','Get-CanonicalPath','Resolve-CodexExecutable')) {
    $function=$ast.Find({param($item) $item -is [Management.Automation.Language.FunctionDefinitionAst] -and $item.Name -eq $name},$true)
    . ([scriptblock]::Create($function.Extent.Text))
}
$env:PROCESSOR_ARCHITECTURE='AMD64'; $env:PROCESSOR_ARCHITEW6432=''
Resolve-CodexExecutable $Shim
''')
        result=subprocess.run([shutil.which("pwsh"),"-NoProfile","-File",str(runner),"-Helper",str(ROOT/"scripts/voice_notify_hooks.ps1"),"-Shim",str(shim)],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(pathlib.Path(result.stdout.strip()),native)
        self.assertFalse(marker.exists())

    @unittest.skipUnless(sys.platform=="darwin" and pathlib.Path("/usr/bin/osascript").exists(),"native macOS JXA required")
    def test_native_macos_review_digest_matches_python_and_approval_is_scoped(self):
        fake,writes,environment=self.make_fake_executable()
        base=["/usr/bin/osascript","-l","JavaScript",str(ROOT / "scripts/voice_notify_hooks.js")]
        options=["--plugin-root",str(self.root),"--codex-command",str(fake)]
        review=subprocess.run(base+["review-hooks"]+options,cwd=self.root,env=environment,capture_output=True,text=True,timeout=25)
        self.assertEqual(review.returncode,0,review.stderr)
        digest=json.loads(review.stdout)["approvalDigest"]
        self.assertEqual(digest,hooks.approval_digest(self.snapshot()))
        self.assertFalse(writes.exists())
        result=subprocess.run(base+["approve-hooks","--approve",digest]+options,cwd=self.root,env=environment,capture_output=True,text=True,timeout=25)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(json.loads(result.stdout)["trusted"])
        self.assertEqual(set(json.loads(writes.read_text())["edits"][0]["value"]),{self.own["key"]})

    @unittest.skipUnless(shutil.which("pwsh"),"PowerShell runtime unavailable")
    def test_native_powershell_review_and_approval_are_scoped(self):
        fake,writes,environment=self.make_fake_executable()
        base=[shutil.which("pwsh"),"-NoProfile","-File",str(ROOT / "scripts/voice_notify_hooks.ps1")]
        options=["-PluginRoot",str(self.root),"-Codex",str(fake)]
        review=subprocess.run(base+["-Action","review-hooks"]+options,cwd=self.root,env=environment,capture_output=True,text=True,timeout=25)
        self.assertEqual(review.returncode,0,review.stderr)
        digest=json.loads(review.stdout)["approvalDigest"]
        self.assertFalse(writes.exists())
        result=subprocess.run(base+["-Action","approve-hooks","-Approve",digest]+options,cwd=self.root,env=environment,capture_output=True,text=True,timeout=25)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(json.loads(result.stdout)["trusted"])
        self.assertEqual(set(json.loads(writes.read_text())["edits"][0]["value"]),{self.own["key"]})


if __name__ == "__main__": unittest.main()
