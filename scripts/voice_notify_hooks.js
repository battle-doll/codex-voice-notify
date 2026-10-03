#!/usr/bin/osascript -l JavaScript
// Native macOS: Foundation + the bundled Codex executable; no Python or Node.
ObjC.import("Foundation");
ObjC.bindFunction("realpath", ["char *", ["char *", "void *"]]);
var PLUGIN = "codex-voice-notify";
var HASH = /^[0-9a-fA-F]{64}$/;
var CURRENT_HASH = /^(?:sha256:)?[0-9a-fA-F]{64}$/;
var fm = $.NSFileManager.defaultManager;

function fail(message) { throw new Error("Voice Notify: " + message); }
function data(text) { return $(text).dataUsingEncoding($.NSUTF8StringEncoding); }
function string(bytes) { return ObjC.unwrap($.NSString.alloc.initWithDataEncoding(bytes, $.NSUTF8StringEncoding)); }
function exists(path) { return Boolean(fm.fileExistsAtPath($(path))); }
function canonical(path) {
    if (!exists(path)) fail("Required local plugin file was not found.");
    // NSString deliberately folds /private/var to /var; realpath matches the
    // physical source identity used by Codex and the other native helpers.
    var resolved=$.realpath(path,null);
    if (!resolved) fail("Required local plugin file could not be resolved.");
    return resolved;
}
function read(path) {
    var bytes = $.NSData.dataWithContentsOfFile($(path));
    if (!bytes || Number(bytes.length) > 1048576) fail("Local plugin file is missing or exceeds the size limit.");
    return bytes;
}
function stable(value) {
    if (Array.isArray(value)) return "[" + value.map(stable).join(",") + "]";
    if (value !== null && typeof value === "object") return "{" + Object.keys(value).sort().map(function(k) { return JSON.stringify(k) + ":" + stable(value[k]); }).join(",") + "}";
    return JSON.stringify(value);
}
function sha(bytes) {
    var task = $.NSTask.alloc.init, input = $.NSPipe.pipe, output = $.NSPipe.pipe;
    task.launchPath = $("/usr/bin/shasum"); task.arguments = $( ["-a", "256"] );
    task.standardInput = input; task.standardOutput = output; task.standardError = $.NSFileHandle.fileHandleWithNullDevice;
    task.launch;
    input.fileHandleForWriting.writeData(bytes); input.fileHandleForWriting.closeFile;
    var result = string(output.fileHandleForReading.readDataToEndOfFile).split(/\s/)[0];
    task.waitUntilExit;
    if (Number(task.terminationStatus) !== 0 || !HASH.test(result)) fail("The local SHA256 tool failed.");
    return result;
}
function parse(bytes) { try { return JSON.parse(string(bytes)); } catch(e) { fail("Local JSON file is invalid."); } }
function codexPath(explicit) {
    if (explicit) return canonical(explicit);
    var choices = ["/Applications/Codex.app/Contents/Resources/codex", "/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex", "/opt/homebrew/bin/codex", "/usr/local/bin/codex"];
    for (var i=0;i<choices.length;i++) if (exists(choices[i])) return canonical(choices[i]);
    fail("Codex executable was not found. Update or install Codex first.");
}
function Server(executable, cwd) {
    // A private ephemeral transport spool gives bounded reads on every supported
    // macOS JXA version. It is removed on exit and is never a review/source file.
    this.directory = ObjC.unwrap($.NSTemporaryDirectory()) + "voice-notify-api-" + ObjC.unwrap($.NSUUID.UUID.UUIDString);
    if (!fm.createDirectoryAtPathWithIntermediateDirectoriesAttributesError($(this.directory), false, $({NSFilePosixPermissions: 448}), null)) fail("Could not create a private local API transport.");
    this.outputPath = this.directory + "/response";
    if (!fm.createFileAtPathContentsAttributes($(this.outputPath), $.NSData.data, $({NSFilePosixPermissions: 384}))) fail("Could not create a private local API transport.");
    this.output = $.NSFileHandle.fileHandleForWritingAtPath($(this.outputPath));
    this.input = $.NSPipe.pipe; this.task = $.NSTask.alloc.init; this.id = 0; this.consumed = 0;
    this.task.launchPath = $(executable);
    this.task.arguments = $(["app-server", "--listen", "stdio://", "-c", "analytics.enabled=false", "-c", "feedback.enabled=false", "-c", 'otel.exporter="none"', "-c", "mcp_servers={}"]);
    this.task.currentDirectoryPath = $(cwd); this.task.standardInput = this.input;
    this.task.standardOutput = this.output; this.task.standardError = $.NSFileHandle.fileHandleWithNullDevice;
    try {
        this.task.launch;
        this.initializeResult=this.request("initialize", {clientInfo: {name: PLUGIN, version: "0.2.0"}, capabilities: {experimentalApi: true}});
        this.send({method: "initialized"});
    } catch(e) { this.close(); throw e; }
}
Server.prototype.send = function(message) { this.input.fileHandleForWriting.writeData(data(JSON.stringify(message) + "\n")); };
Server.prototype.request = function(method, params) {
    var id = ++this.id, deadline = Date.now() + 20000;
    this.send({id:id, method:method, params:params});
    while (Date.now() < deadline) {
        var bytes = $.NSData.dataWithContentsOfFile($(this.outputPath));
        if (Number(bytes.length) > 2097152) fail("The local API response exceeded the size limit.");
        var text = string(bytes);
        if (typeof text === "string") {
            var lines = text.split("\n");
            while (this.consumed < lines.length-1) {
                var message;
                try { message = JSON.parse(lines[this.consumed++]); } catch(e) { fail("The local Codex API returned invalid JSON."); }
                if (message.method && message.id !== undefined) fail("Unexpected interactive API request; no action was approved.");
                if (message.id !== id) continue;
                if (message.error) fail("Codex API " + method + " failed. Update Codex or use its /hooks review.");
                if (!message.result || typeof message.result !== "object") fail("The local Codex API returned an invalid result.");
                return message.result;
            }
        }
        if (!this.task.running) fail("The local Codex app-server stopped.");
        $.NSThread.sleepForTimeInterval(0.05);
    }
    fail("The local Codex API timed out. Update Codex and retry.");
};
Server.prototype.close = function() {
    try { if (this.task && this.task.running) this.task.terminate; } catch(e) {}
    try { if (this.input) this.input.fileHandleForWriting.closeFile; } catch(e) {}
    try { if (this.output) this.output.closeFile; } catch(e) {}
    if (this.directory) fm.removeItemAtPathError($(this.directory), null);
};
function source(root) {
    root = canonical(root); var path = canonical(root + "/hooks/hooks.json");
    if (path !== root + "/hooks/hooks.json") fail("The hook source is outside this plugin. Refusing approval.");
    var manifest = parse(read(root + "/.codex-plugin/plugin.json")), bytes = read(path), doc = parse(bytes), specs=[];
    if (manifest.name !== PLUGIN || manifest.hooks !== "./hooks/hooks.json") fail("This root is not the Voice Notify plugin hook source.");
    if (!doc.hooks || typeof doc.hooks !== "object" || Array.isArray(doc.hooks)) fail("The plugin hook source is invalid.");
    Object.keys(doc.hooks).forEach(function(event) {
        if (!Array.isArray(doc.hooks[event]) || !event) fail("The plugin hook source is invalid.");
        doc.hooks[event].forEach(function(group,groupIndex) {
            if (!Array.isArray(group.hooks)) fail("The plugin hook source is invalid.");
            group.hooks.forEach(function(hook,handlerIndex) {
                if (hook.type !== "command" || typeof hook.command !== "string" || typeof hook.commandWindows !== "string") fail("Both bundled Unix and Windows command hooks must be present for review.");
                specs.push({eventName:event.charAt(0).toLowerCase()+event.slice(1), matcher:group.matcher===undefined?null:group.matcher, command:hook.command, commandWindows:hook.commandWindows, timeoutSec:hook.timeout===undefined?600:hook.timeout, async:hook.async===undefined?false:hook.async,keySuffix:"hooks/hooks.json:"+event.replace(/([A-Z])/g,"_$1").replace(/^_/,"").toLowerCase()+":"+groupIndex+":"+handlerIndex});
            });
        });
    });
    if (!specs.length) fail("No Voice Notify command hooks were found.");
    return {root:root, path:path, manifest:manifest, sourceSha256:sha(bytes), specs:specs};
}
function matches(command, spec, root) {
    return ["command","commandWindows"].some(function(key) {
        var raw=spec[key];
        return command===raw || command===raw.split("${PLUGIN_ROOT}").join(root) || command===raw.split("${PLUGIN_ROOT}").join(root.replace(/\//g,"\\"));
    });
}
function review(root, listing) {
    var src=source(root), selected=[], entry;
    if (!Array.isArray(listing.data) || listing.data.length!==1) fail("The hook listing did not identify one local workspace.");
    entry=listing.data[0];
    if ((entry.errors||[]).length || !Array.isArray(entry.hooks)) fail("Codex reported a hook configuration error. Fix it before review.");
    entry.hooks.forEach(function(hook) {
        if (typeof hook.sourcePath!=="string") fail("Codex returned an invalid hook source path.");
        var path=canonical(hook.sourcePath), same=typeof hook.pluginId==="string" && hook.pluginId.split("@")[0]===PLUGIN;
        if (same && path!==src.path) fail("Multiple Voice Notify plugin roots are active. Remove the duplicate before review.");
        if (path!==src.path) return;
        if (hook.source!=="plugin" || !same) fail("The exact hook source is not an installed Voice Notify plugin.");
        if (hook.isManaged || hook.trustStatus==="managed") fail("Managed hooks require the administrator's Codex controls.");
        if (hook.handlerType!=="command" || typeof hook.key!=="string" || !hook.key || !CURRENT_HASH.test(hook.currentHash||"") || ["trusted","modified","untrusted"].indexOf(hook.trustStatus)<0) fail("Codex did not provide valid exact command hook state.");
        selected.push(hook);
    });
    if (!selected.length) fail("Voice Notify is not active in this Codex workspace. Install and enable it first.");
    var keys={}; selected.forEach(function(h) { if (Object.prototype.hasOwnProperty.call(keys,h.key)) fail("The installed hook list is incomplete or ambiguous. Refusing approval."); keys[h.key]=true; });
    if (selected.length!==src.specs.length) fail("The installed hook list is incomplete or ambiguous. Refusing approval.");
    var remaining=src.specs.slice(), reviewed=[];
    selected.sort(function(a,b) { var x=a.eventName+"\u0000"+a.key,y=b.eventName+"\u0000"+b.key; return x<y?-1:x>y?1:0; });
    selected.forEach(function(h) {
        var index=-1;
        for (var i=0;i<remaining.length;i++) { var s=remaining[i]; if (s.eventName===h.eventName && s.matcher===(h.matcher===undefined?null:h.matcher) && s.timeoutSec===h.timeoutSec && s.async===(h.async||false) && h.key===h.pluginId+":"+s.keySuffix && matches(h.command,s,src.root)) {index=i; break;} }
        if (index<0) fail("A listed hook differs from the installed commands. Refusing approval.");
        var item=JSON.parse(JSON.stringify(remaining.splice(index,1)[0]));
        item.key=h.key; item.currentHash=h.currentHash; item.listedCommand=h.command; item.pluginId=h.pluginId; item.enabled=h.enabled; item.trustStatus=h.trustStatus; reviewed.push(item);
    });
    var files={}; ["play_notify.sh","play_notify.py","play_notify.ps1"].forEach(function(name) {
        var path=src.root+"/hooks/"+name;
        if (exists(path)) { if (canonical(path)!==path) fail("A playback script is outside this plugin. Refusing approval."); files["hooks/"+name]=sha(read(path)); }
    });
    return {snapshot:{protocol:"voice-notify-hook-approval-v1",pluginName:PLUGIN,pluginVersion:src.manifest.version===undefined?null:src.manifest.version,pluginRoot:src.root,sourcePath:src.path,sourceSha256:src.sourceSha256,playbackSha256:files,hooks:reviewed},hooks:selected};
}
function digest(snapshot) {
    var bound=JSON.parse(JSON.stringify(snapshot)); bound.targetEnabled=true;
    bound.hooks.forEach(function(h){delete h.enabled;delete h.trustStatus;});
    return sha(data(stable(bound)));
}
function publicReview(snapshot) {
    return {plugin:PLUGIN,version:snapshot.pluginVersion,source:"hooks/hooks.json",sourceSha256:snapshot.sourceSha256,playbackSha256:snapshot.playbackSha256,hooks:snapshot.hooks.map(function(h) { var item={}; ["eventName","matcher","command","commandWindows","timeoutSec","async","currentHash","enabled","trustStatus"].forEach(function(k){item[k]=h[k];}); return item; }),approvalDigest:digest(snapshot),approvalEffect:"Trust these exact installed hashes and enable only these Voice Notify hooks.",next:"After reviewing every command, explicitly approve this approvalDigest."};
}
function localStatus(initialize) {
    var match=String(initialize.userAgent||"").match(/(?:^|[^0-9])(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)/),version=match?match[1]:null;
    var environment=$.NSProcessInfo.processInfo.environment,override=ObjC.unwrap(environment.objectForKey($("CODEX_VOICE_NOTIFY_CONFIG")));
    var path=override || ObjC.unwrap($.NSHomeDirectory())+"/.config/"+PLUGIN+"/settings.json";
    var configured=exists(path),valid=true,settings={};
    if(configured) try {var bytes=read(path);if(Number(bytes.length)>65536) throw new Error("size");settings=parse(bytes);if(!settings||typeof settings!=="object"||Array.isArray(settings)) throw new Error("type");} catch(e){valid=false;settings={};}
    var preferences=settings.events||{},enabled=typeof settings.enabled==="boolean"?settings.enabled:true;
    var events=["SessionStart","UserPromptSubmit","PreToolUse","PostToolUse","PermissionRequest","PreCompact","PostCompact","SubagentStart","SubagentStop","Stop"];
    var player=exists("/usr/bin/afplay");
    return {codexVersion:version,codexPrerelease:version?version.indexOf("-")>=0:null,settingsConfigured:configured,settingsValid:valid,voiceEnabled:enabled,desiredVoiceEvents:events.filter(function(event){return typeof preferences[event]==="boolean"?preferences[event]:event!=="PreToolUse"&&event!=="PostToolUse";}),audioPlayer:player?"afplay":null,playerAvailable:player};
}
function run(argv) {
    var action=argv.shift(), root=null, executable=null, approved=null;
    if (["doctor","review-hooks","approve-hooks"].indexOf(action)<0) fail("Use doctor, review-hooks or approve-hooks.");
    while (argv.length) {
        var option=argv.shift(); if (!argv.length) fail("An option is missing its value."); var value=argv.shift();
        if (option==="--plugin-root") root=value;
        else if (option==="--codex" || option==="--codex-command") executable=value;
        else if (option==="--approve") approved=value;
        else fail("Unknown option.");
    }
    if (action==="approve-hooks" && (!approved || !HASH.test(approved))) fail("Run review-hooks and obtain explicit user approval of its digest first.");
    if (action!=="approve-hooks" && approved) fail("--approve is only accepted with approve-hooks.");
    if (!root) {
        var args=ObjC.deepUnwrap($.NSProcessInfo.processInfo.arguments), script=null;
        for(var i=0;i<args.length;i++) if (/voice_notify_hooks\.js$/.test(args[i])) {script=args[i];break;}
        if (!script) fail("Pass --plugin-root for this installed plugin.");
        root=ObjC.unwrap($(canonical(script)).stringByDeletingLastPathComponent.stringByDeletingLastPathComponent);
    }
    var cwd=ObjC.unwrap(fm.currentDirectoryPath), server, result;
    try {
        server=new Server(codexPath(executable),cwd);
        var listing=server.request("hooks/list",{cwds:[cwd]}), checked;
        if(action==="doctor") {
            try {checked=review(root,listing); result={plugin:PLUGIN,version:checked.snapshot.pluginVersion,source:"hooks/hooks.json",installedHooks:checked.hooks.length,trustedHooks:checked.hooks.filter(function(h){return h.trustStatus==="trusted";}).length,enabledHooks:checked.hooks.filter(function(h){return h.enabled===true;}).length,ready:checked.hooks.every(function(h){return h.trustStatus==="trusted" && h.enabled===true;}),lifecyclePlaybackVerified:false};}
            catch(e) {result={plugin:PLUGIN,source:"hooks/hooks.json",ready:false,reason:String(e.message).replace(/^Voice Notify: /,""),lifecyclePlaybackVerified:false};}
            var status=localStatus(server.initializeResult);Object.keys(status).forEach(function(k){result[k]=status[k];});
        } else {
            checked=review(root,listing);
            if(action==="review-hooks") result=publicReview(checked.snapshot);
            else {
                if(digest(checked.snapshot)!==approved.toLowerCase()) fail("Approval is stale: the hook review changed. Run review-hooks again and request fresh approval.");
                var states=Object.create(null); checked.hooks.forEach(function(h){states[h.key]={trusted_hash:h.currentHash,enabled:true};});
                server.request("config/batchWrite",{edits:[{keyPath:"hooks.state",value:states,mergeStrategy:"upsert"}],filePath:null,expectedVersion:null,reloadUserConfig:true});
                var after=review(root,server.request("hooks/list",{cwds:[cwd]}));
                var beforeHashes=checked.hooks.map(function(h){return [h.key,h.currentHash];}),afterHashes=after.hooks.map(function(h){return [h.key,h.currentHash];});
                if(stable(beforeHashes)!==stable(afterHashes) || checked.snapshot.sourceSha256!==after.snapshot.sourceSha256 || stable(checked.snapshot.playbackSha256)!==stable(after.snapshot.playbackSha256)) fail("Hook content changed during approval; run a fresh review before using hooks.");
                if(!after.hooks.every(function(h){return h.trustStatus==="trusted" && h.enabled===true;})) fail("Codex did not confirm every reviewed hook as trusted and enabled.");
                result={plugin:PLUGIN,source:"hooks/hooks.json",approvedHooks:checked.hooks.length,trusted:true,enabled:true,approvalDigest:approved.toLowerCase(),lifecyclePlaybackVerified:false,next:"Start a new Codex session and test a natural lifecycle event."};
            }
        }
    } catch(e) { if (!/^Voice Notify: /.test(String(e.message))) fail("The local Codex API or plugin files could not be accessed safely."); throw e; }
    finally {if(server) server.close();}
    return JSON.stringify(result,null,2);
}
