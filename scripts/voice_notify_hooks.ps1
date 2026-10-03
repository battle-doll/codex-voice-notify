# Native Windows/.NET hook review. No Python, model turn or direct trust-file edit.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('doctor','review-hooks','approve-hooks')][string]$Action,
    [string]$Approve,
    [Alias('CodexCommand')][string]$Codex,
    [string]$PluginRoot = (Split-Path -Parent $PSScriptRoot)
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
$script:PluginName = 'codex-voice-notify'
$script:HashPattern = '^[0-9a-fA-F]{64}$'
$script:CurrentHashPattern = '^(?:sha256:)?[0-9a-fA-F]{64}$'

function Stop-HookAction([string]$Message) { throw ('Voice Notify: ' + $Message) }
function Get-CanonicalPath([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { Stop-HookAction 'Required local plugin file was not found.' }
    return [IO.Path]::GetFullPath((Get-Item -LiteralPath $Path).FullName)
}
function Test-SamePath([string]$Left, [string]$Right) {
    $comparison = [StringComparison]::Ordinal
    if ([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT) { $comparison = [StringComparison]::OrdinalIgnoreCase }
    return [string]::Equals($Left, $Right, $comparison)
}
function Read-PluginBytes([string]$Path) {
    $item = Get-Item -LiteralPath $Path
    if ($item.Length -gt 1048576) { Stop-HookAction 'Local plugin file exceeds the size limit.' }
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { Stop-HookAction 'A plugin source file is a link. Refusing approval.' }
    return ,([IO.File]::ReadAllBytes($item.FullName))
}
function Get-Sha256([byte[]]$Bytes) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
function ConvertTo-StableJson($Value) {
    if ($null -eq $Value) { return 'null' }
    if ($Value -is [string] -or $Value -is [bool] -or $Value -is [ValueType]) { return (ConvertTo-Json -InputObject $Value -Compress) }
    if ($Value -is [Collections.IDictionary]) {
        $keys = [string[]]@($Value.Keys); [Array]::Sort($keys, [StringComparer]::Ordinal)
        $parts = @(); foreach ($key in $keys) { $parts += ((ConvertTo-Json -InputObject $key -Compress) + ':' + (ConvertTo-StableJson $Value[$key])) }
        return ('{' + ($parts -join ',') + '}')
    }
    if ($Value -is [Collections.IEnumerable]) {
        $parts = @(); foreach ($item in $Value) { $parts += (ConvertTo-StableJson $item) }
        return ('[' + ($parts -join ',') + ']')
    }
    $properties = @{}; foreach ($property in $Value.PSObject.Properties) { $properties[$property.Name] = $property.Value }
    return (ConvertTo-StableJson $properties)
}
function Get-ApprovalDigest($Snapshot) {
    $bound = @{}; foreach ($key in $Snapshot.Keys) { if ($key -ne 'hooks') { $bound[$key] = $Snapshot[$key] } }
    $bound.targetEnabled = $true; $bound.hooks = @()
    foreach ($hook in $Snapshot.hooks) { $item = @{}; foreach ($key in $hook.Keys) { if ($key -ne 'enabled' -and $key -ne 'trustStatus') { $item[$key] = $hook[$key] } }; $bound.hooks += $item }
    return (Get-Sha256 ([Text.Encoding]::UTF8.GetBytes((ConvertTo-StableJson $bound))))
}
function Find-Codex([string]$Explicit) {
    if ($Explicit) {
        if (Test-Path -LiteralPath $Explicit -PathType Leaf) { return (Resolve-CodexExecutable (Get-CanonicalPath $Explicit)) }
        $command = Get-Command $Explicit -CommandType Application -ErrorAction SilentlyContinue
        if ($command) { return (Resolve-CodexExecutable $command.Source) }
        Stop-HookAction 'Codex executable was not found. Update or install Codex first.'
    }
    $command = Get-Command codex -CommandType Application -ErrorAction SilentlyContinue
    if ($command) { return (Resolve-CodexExecutable $command.Source) }
    $candidates = @()
    if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA 'Programs\Codex\resources\codex.exe') }
    foreach ($candidate in $candidates) { if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate } }
    Stop-HookAction 'Codex executable was not found. Update or install Codex first.'
}
function Resolve-CodexExecutable([string]$Path) {
    $path = Get-CanonicalPath $Path
    $extension = [IO.Path]::GetExtension($path).ToLowerInvariant()
    if (@('.cmd','.bat','.ps1') -notcontains $extension) { return $path }
    # Never invoke cmd.exe/PowerShell or parse executable shell-wrapper text.
    if ([IO.Path]::GetFileNameWithoutExtension($path).ToLowerInvariant() -ne 'codex') { Stop-HookAction 'A shell wrapper cannot be used here. Select the native Codex executable.' }
    $architecture = $env:PROCESSOR_ARCHITEW6432
    if (-not $architecture) { $architecture = $env:PROCESSOR_ARCHITECTURE }
    if (-not $architecture) { $architecture = 'AMD64' }
    if (@('ARM64','aarch64') -contains $architecture) { $target = 'aarch64-pc-windows-msvc'; $package = 'codex-win32-arm64' }
    elseif (@('AMD64','x86_64','x64') -contains $architecture) { $target = 'x86_64-pc-windows-msvc'; $package = 'codex-win32-x64' }
    else { Stop-HookAction 'This Codex npm shim has an unsupported Windows architecture. Select the native executable.' }
    $directory = Split-Path -Parent $path
    $scopes = @((Join-Path $directory 'node_modules/@openai'))
    if ([IO.Path]::GetFileName($directory) -eq '.bin') { $scopes += (Join-Path (Split-Path -Parent $directory) '@openai') }
    foreach ($scope in $scopes) {
        $main = Join-Path $scope 'codex'; $manifestPath = Join-Path $main 'package.json'
        try {
            if ((Get-Item -LiteralPath $manifestPath).Length -gt 65536) { continue }
            $manifest = [IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
            if ($manifest.name -cne '@openai/codex') { continue }
        } catch { continue }
        $roots = @((Join-Path $scope $package), (Join-Path $main ('node_modules/@openai/' + $package)), $main)
        foreach ($root in $roots) {
            foreach ($location in @('bin','codex')) {
                $candidate = Join-Path $root ('vendor/' + $target + '/' + $location + '/codex.exe')
                if (Test-Path -LiteralPath $candidate -PathType Leaf) { return (Get-CanonicalPath $candidate) }
            }
        }
    }
    Stop-HookAction 'The npm Codex native executable is missing. Reinstall Codex or select its native executable.'
}
function Quote-ProcessArgument([string]$Argument) {
    # ProcessStartInfo.Arguments is a Windows command line, never a shell command.
    return ('"' + [regex]::Replace([regex]::Replace($Argument, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1') + '"')
}
function Start-LocalServer([string]$Executable, [string]$Cwd) {
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $Executable; $info.WorkingDirectory = $Cwd
    $info.UseShellExecute = $false; $info.CreateNoWindow = $true
    $info.RedirectStandardInput = $true; $info.RedirectStandardOutput = $true; $info.RedirectStandardError = $true
    # Codex JSON-RPC is UTF-8. Windows PowerShell 5.1 otherwise uses the console
    # code page for redirected Process streams, corrupting non-ASCII paths.
    $utf8 = [Text.UTF8Encoding]::new($false, $true)
    # .NET Framework creates its own StandardInput writer with AutoFlush=true
    # during Start(). Set a BOM-free input encoding before that writer exists.
    [Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
    $info.StandardOutputEncoding = $utf8; $info.StandardErrorEncoding = $utf8
    $arguments = @('app-server', '--listen', 'stdio://', '-c', 'analytics.enabled=false', '-c', 'feedback.enabled=false', '-c', 'otel.exporter="none"', '-c', 'mcp_servers={}')
    if ($info.PSObject.Properties.Name -contains 'ArgumentList') { foreach ($argument in $arguments) { $info.ArgumentList.Add($argument) } }
    else { $info.Arguments = (($arguments | ForEach-Object { Quote-ProcessArgument $_ }) -join ' ') }
    $process = [Diagnostics.Process]::new(); $process.StartInfo = $info
    if (-not $process.Start()) { Stop-HookAction 'Could not start the local Codex app-server.' }
    $process.BeginErrorReadLine() # Discard private stderr; never print or retain it.
    $writer = [IO.StreamWriter]::new($process.StandardInput.BaseStream, $utf8, 1024, $true)
    $writer.AutoFlush = $true
    $server = @{ Process = $process; Writer = $writer; Id = 0; Pending = $null }
    try {
        $server.InitializeResult = Invoke-LocalRequest $server 'initialize' @{ clientInfo = @{ name = $script:PluginName; version = '0.2.0' }; capabilities = @{ experimentalApi = $true } }
        $writer.WriteLine('{"method":"initialized"}')
        return $server
    } catch { Stop-LocalServer $server; throw }
}
function Stop-LocalServer($Server) {
    if ($null -eq $Server) { return }
    $process = $Server.Process
    try { if ($Server.Writer) { $Server.Writer.Dispose() } } catch {}
    try { if (-not $process.HasExited) { $process.Kill(); $null = $process.WaitForExit(2000) } } catch {}
    $process.Dispose()
}
function Invoke-LocalRequest($Server, [string]$Method, $Params) {
    $Server.Id++; $identifier = $Server.Id
    $message = @{ id = $identifier; method = $Method; params = $Params } | ConvertTo-Json -Depth 50 -Compress
    $Server.Writer.WriteLine($message)
    $deadline = [DateTime]::UtcNow.AddSeconds(20)
    while ([DateTime]::UtcNow -lt $deadline) {
        if ($null -eq $Server.Pending) { $Server.Pending = $Server.Process.StandardOutput.ReadLineAsync() }
        if (-not $Server.Pending.Wait(50)) { continue }
        $line = $Server.Pending.GetAwaiter().GetResult(); $Server.Pending = $null
        if ($null -eq $line) { Stop-HookAction 'The local Codex app-server stopped.' }
        if ($line.Length -gt 2097152) { Stop-HookAction 'The local API response exceeded the size limit.' }
        try { $response = $line | ConvertFrom-Json } catch { Stop-HookAction 'The local Codex API returned invalid JSON.' }
        if ($response.method -and $null -ne $response.id) { Stop-HookAction 'Unexpected interactive API request; no action was approved.' }
        if ($response.id -ne $identifier) { continue }
        if ($response.error) { Stop-HookAction ('Codex API ' + $Method + ' failed. Update Codex or use its /hooks review.') }
        if ($null -eq $response.result) { Stop-HookAction 'The local Codex API returned an invalid result.' }
        return $response.result
    }
    Stop-HookAction 'The local Codex API timed out. Update Codex and retry.'
}
function Get-Source([string]$Root) {
    $rootPath = Get-CanonicalPath $Root; $hooksDirectory = Join-Path $rootPath 'hooks'
    if (((Get-Item -LiteralPath $hooksDirectory).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { Stop-HookAction 'The hook source is outside this plugin. Refusing approval.' }
    $sourcePath = Get-CanonicalPath (Join-Path $hooksDirectory 'hooks.json')
    $manifest = [Text.Encoding]::UTF8.GetString((Read-PluginBytes (Join-Path $rootPath '.codex-plugin/plugin.json'))) | ConvertFrom-Json
    $sourceBytes = Read-PluginBytes $sourcePath
    $document = [Text.Encoding]::UTF8.GetString($sourceBytes) | ConvertFrom-Json
    if ($manifest.name -ne $script:PluginName -or $manifest.hooks -ne './hooks/hooks.json') { Stop-HookAction 'This root is not the Voice Notify plugin hook source.' }
    if (-not $document.hooks) { Stop-HookAction 'The plugin hook source is invalid.' }
    $specs = @()
    foreach ($property in $document.hooks.PSObject.Properties) {
        $eventName = $property.Name.Substring(0,1).ToLowerInvariant() + $property.Name.Substring(1)
        $groupIndex = 0
        foreach ($group in $property.Value) {
            $handlerIndex = 0
            foreach ($handler in $group.hooks) {
                if ($handler.type -ne 'command' -or $handler.command -isnot [string] -or $handler.commandWindows -isnot [string]) { Stop-HookAction 'Both bundled Unix and Windows command hooks must be present for review.' }
                $timeout = 600; if ($null -ne $handler.timeout) { $timeout = $handler.timeout }
                $async = $false; if ($null -ne $handler.async) { $async = $handler.async }
                $snakeEvent = [regex]::Replace($property.Name, '(?<!^)(?=[A-Z])', '_').ToLowerInvariant()
                $specs += @{ eventName = $eventName; matcher = $group.matcher; command = $handler.command; commandWindows = $handler.commandWindows; timeoutSec = $timeout; async = $async; keySuffix = ('hooks/hooks.json:' + $snakeEvent + ':' + $groupIndex + ':' + $handlerIndex) }
                $handlerIndex++
            }
            $groupIndex++
        }
    }
    if (-not $specs.Count) { Stop-HookAction 'No Voice Notify command hooks were found.' }
    return @{ root = $rootPath; path = $sourcePath; manifest = $manifest; sourceSha256 = Get-Sha256 $sourceBytes; specs = $specs }
}
function Test-CommandMatches([string]$Command, $Spec, [string]$Root) {
    foreach ($key in @('command','commandWindows')) {
        $raw = $Spec[$key]
        if ($Command -ceq $raw -or $Command -ceq $raw.Replace('${PLUGIN_ROOT}', $Root) -or $Command -ceq $raw.Replace('${PLUGIN_ROOT}', $Root.Replace('/', '\'))) { return $true }
    }
    return $false
}
function Get-Review([string]$Root, $Listing) {
    $source = Get-Source $Root
    if (@($Listing.data).Count -ne 1) { Stop-HookAction 'The hook listing did not identify one local workspace.' }
    $entry = @($Listing.data)[0]
    if (@($entry.errors).Count -gt 0 -or $null -eq $entry.hooks) { Stop-HookAction 'Codex reported a hook configuration error. Fix it before review.' }
    $selected = @(); $keys = @{}
    foreach ($hook in $entry.hooks) {
        if ($hook.sourcePath -isnot [string]) { Stop-HookAction 'Codex returned an invalid hook source path.' }
        $listedPath = [IO.Path]::GetFullPath($hook.sourcePath)
        $same = ($hook.pluginId -is [string]) -and $hook.pluginId.Split('@')[0] -ceq $script:PluginName
        if ($same -and -not (Test-SamePath $listedPath $source.path)) { Stop-HookAction 'Multiple Voice Notify plugin roots are active. Remove the duplicate before review.' }
        if (-not (Test-SamePath $listedPath $source.path)) { continue }
        if ($hook.source -ne 'plugin' -or -not $same) { Stop-HookAction 'The exact hook source is not an installed Voice Notify plugin.' }
        if ($hook.isManaged -or $hook.trustStatus -eq 'managed') { Stop-HookAction "Managed hooks require the administrator's Codex controls." }
        if ($hook.handlerType -ne 'command' -or $hook.key -isnot [string] -or -not $hook.key -or $hook.currentHash -notmatch $script:CurrentHashPattern -or @('trusted','modified','untrusted') -notcontains $hook.trustStatus) { Stop-HookAction 'Codex did not provide valid exact command hook state.' }
        if ($keys.ContainsKey($hook.key)) { Stop-HookAction 'The installed hook list is incomplete or ambiguous. Refusing approval.' }
        $keys[$hook.key] = $true; $selected += $hook
    }
    if (-not $selected.Count) { Stop-HookAction 'Voice Notify is not active in this Codex workspace. Install and enable it first.' }
    if ($selected.Count -ne $source.specs.Count) { Stop-HookAction 'The installed hook list is incomplete or ambiguous. Refusing approval.' }
    $remaining = [Collections.ArrayList]::new(); foreach ($spec in $source.specs) { $null = $remaining.Add($spec) }
    $reviewed = @(); $selected = @($selected | Sort-Object eventName,key)
    foreach ($hook in $selected) {
        $index = -1
        for ($i = 0; $i -lt $remaining.Count; $i++) {
            $spec = $remaining[$i]; $async = $false; if ($null -ne $hook.async) { $async = $hook.async }
            if ($spec.eventName -ceq $hook.eventName -and $spec.matcher -ceq $hook.matcher -and $spec.timeoutSec -eq $hook.timeoutSec -and $spec.async -eq $async -and $hook.key -ceq ($hook.pluginId + ':' + $spec.keySuffix) -and (Test-CommandMatches $hook.command $spec $source.root)) { $index = $i; break }
        }
        if ($index -lt 0) { Stop-HookAction 'A listed hook differs from the installed commands. Refusing approval.' }
        $item = @{}; foreach ($key in $remaining[$index].Keys) { $item[$key] = $remaining[$index][$key] }; $remaining.RemoveAt($index)
        $item.key = $hook.key; $item.currentHash = $hook.currentHash; $item.listedCommand = $hook.command; $item.pluginId = $hook.pluginId; $item.enabled = $hook.enabled; $item.trustStatus = $hook.trustStatus; $reviewed += $item
    }
    $files = @{}; foreach ($name in @('play_notify.sh','play_notify.py','play_notify.ps1')) {
        $path = Join-Path $source.root ('hooks/' + $name)
        if (Test-Path -LiteralPath $path -PathType Leaf) { $files['hooks/' + $name] = Get-Sha256 (Read-PluginBytes $path) }
    }
    return @{ snapshot = @{ protocol = 'voice-notify-hook-approval-v1'; pluginName = $script:PluginName; pluginVersion = $source.manifest.version; pluginRoot = $source.root; sourcePath = $source.path; sourceSha256 = $source.sourceSha256; playbackSha256 = $files; hooks = $reviewed }; hooks = $selected }
}
function Get-PublicReview($Snapshot) {
    $hooks = @(); foreach ($hook in $Snapshot.hooks) { $item = @{}; foreach ($key in @('eventName','matcher','command','commandWindows','timeoutSec','async','currentHash','enabled','trustStatus')) { $item[$key] = $hook[$key] }; $hooks += $item }
    return @{ plugin = $script:PluginName; version = $Snapshot.pluginVersion; source = 'hooks/hooks.json'; sourceSha256 = $Snapshot.sourceSha256; playbackSha256 = $Snapshot.playbackSha256; hooks = $hooks; approvalDigest = Get-ApprovalDigest $Snapshot; approvalEffect = 'Trust these exact installed hashes and enable only these Voice Notify hooks.'; next = 'After reviewing every command, explicitly approve this approvalDigest.' }
}
function Get-LocalStatus($Initialize) {
    $version = $null
    if ([string]$Initialize.userAgent -match '(?<![0-9])(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)') { $version = $Matches[1] }
    $path = Join-Path $HOME '.config/codex-voice-notify/settings.json'
    if ($env:CODEX_VOICE_NOTIFY_CONFIG) { $path = $env:CODEX_VOICE_NOTIFY_CONFIG }
    $configured = Test-Path -LiteralPath $path -PathType Leaf; $valid = $true; $settings = $null
    if ($configured) { try { if ((Get-Item -LiteralPath $path).Length -gt 65536) { throw 'size' }; $settings = [IO.File]::ReadAllText($path) | ConvertFrom-Json; if ($null -eq $settings -or $settings -is [array]) { throw 'type' } } catch { $valid = $false; $settings = $null } }
    $enabled = $true; if ($null -ne $settings -and $settings.enabled -is [bool]) { $enabled = $settings.enabled }
    $desired = @(); foreach ($eventName in @('SessionStart','UserPromptSubmit','PreToolUse','PostToolUse','PermissionRequest','PreCompact','PostCompact','SubagentStart','SubagentStop','Stop')) {
        $eventEnabled = @('PreToolUse','PostToolUse') -notcontains $eventName
        if ($null -ne $settings -and $null -ne $settings.events -and $settings.events.$eventName -is [bool]) { $eventEnabled = $settings.events.$eventName }
        if ($eventEnabled) { $desired += $eventName }
    }
    $prerelease = $null; if ($version) { $prerelease = $version.Contains('-') }
    return @{ codexVersion = $version; codexPrerelease = $prerelease; settingsConfigured = $configured; settingsValid = $valid; voiceEnabled = $enabled; desiredVoiceEvents = $desired; audioPlayer = 'System.Media.SoundPlayer'; playerAvailable = $true }
}

$server = $null
try {
    if ($Action -eq 'approve-hooks' -and (-not $Approve -or $Approve -notmatch $script:HashPattern)) { Stop-HookAction 'Run review-hooks and obtain explicit user approval of its digest first.' }
    if ($Action -ne 'approve-hooks' -and $Approve) { Stop-HookAction '-Approve is only accepted with approve-hooks.' }
    $cwd = (Get-Location).ProviderPath
    $server = Start-LocalServer (Find-Codex $Codex) $cwd
    $listing = Invoke-LocalRequest $server 'hooks/list' @{ cwds = @($cwd) }
    if ($Action -eq 'doctor') {
        try {
            $checked = Get-Review $PluginRoot $listing
            $trusted = @($checked.hooks | Where-Object { $_.trustStatus -eq 'trusted' }).Count
            $enabled = @($checked.hooks | Where-Object { $_.enabled -eq $true }).Count
            $result = @{ plugin = $script:PluginName; version = $checked.snapshot.pluginVersion; source = 'hooks/hooks.json'; installedHooks = $checked.hooks.Count; trustedHooks = $trusted; enabledHooks = $enabled; ready = ($trusted -eq $checked.hooks.Count -and $enabled -eq $checked.hooks.Count); lifecyclePlaybackVerified = $false }
        } catch {
            if (-not $_.Exception.Message.StartsWith('Voice Notify: ')) { throw }
            $result = @{ plugin = $script:PluginName; source = 'hooks/hooks.json'; ready = $false; reason = $_.Exception.Message.Substring(14); lifecyclePlaybackVerified = $false }
        }
        $localStatus = Get-LocalStatus $server.InitializeResult; foreach ($key in $localStatus.Keys) { $result[$key] = $localStatus[$key] }
    } else {
        $checked = Get-Review $PluginRoot $listing
        if ($Action -eq 'review-hooks') { $result = Get-PublicReview $checked.snapshot }
        else {
            if ((Get-ApprovalDigest $checked.snapshot) -cne $Approve.ToLowerInvariant()) { Stop-HookAction 'Approval is stale: the hook review changed. Run review-hooks again and request fresh approval.' }
            $states = @{}; foreach ($hook in $checked.hooks) { $states[$hook.key] = @{ trusted_hash = $hook.currentHash; enabled = $true } }
            $null = Invoke-LocalRequest $server 'config/batchWrite' @{ edits = @(@{ keyPath = 'hooks.state'; value = $states; mergeStrategy = 'upsert' }); filePath = $null; expectedVersion = $null; reloadUserConfig = $true }
            $after = Get-Review $PluginRoot (Invoke-LocalRequest $server 'hooks/list' @{ cwds = @($cwd) })
            $beforeHashes = @{}; foreach ($hook in $checked.hooks) { $beforeHashes[$hook.key] = $hook.currentHash }
            $afterHashes = @{}; foreach ($hook in $after.hooks) { $afterHashes[$hook.key] = $hook.currentHash }
            if ((ConvertTo-StableJson $beforeHashes) -cne (ConvertTo-StableJson $afterHashes) -or $checked.snapshot.sourceSha256 -cne $after.snapshot.sourceSha256 -or (ConvertTo-StableJson $checked.snapshot.playbackSha256) -cne (ConvertTo-StableJson $after.snapshot.playbackSha256)) { Stop-HookAction 'Hook content changed during approval; run a fresh review before using hooks.' }
            if (@($after.hooks | Where-Object { $_.trustStatus -ne 'trusted' -or $_.enabled -ne $true }).Count) { Stop-HookAction 'Codex did not confirm every reviewed hook as trusted and enabled.' }
            $result = @{ plugin = $script:PluginName; source = 'hooks/hooks.json'; approvedHooks = $checked.hooks.Count; trusted = $true; enabled = $true; approvalDigest = $Approve.ToLowerInvariant(); lifecyclePlaybackVerified = $false; next = 'Start a new Codex session and test a natural lifecycle event.' }
        }
    }
    ConvertTo-Json -InputObject $result -Depth 50
} catch {
    $message = $_.Exception.Message
    if (-not $message.StartsWith('Voice Notify: ')) { $message = 'Voice Notify: The local Codex API or plugin files could not be accessed safely.' }
    [Console]::Error.WriteLine($message)
    exit 2
} finally { Stop-LocalServer $server }
exit 0
