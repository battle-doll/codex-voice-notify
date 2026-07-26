#!/bin/sh
# Privacy-preserving, non-blocking local WAV playback for Codex hooks on macOS.

umask 077
LC_ALL=C
export LC_ALL

event_slug() {
    case "$1" in
        SessionStart) printf '%s\n' "session-start" ;;
        UserPromptSubmit) printf '%s\n' "user-prompt-submit" ;;
        PreToolUse) printf '%s\n' "pre-tool-use" ;;
        PostToolUse) printf '%s\n' "post-tool-use" ;;
        PermissionRequest) printf '%s\n' "permission-request" ;;
        PreCompact) printf '%s\n' "pre-compact" ;;
        PostCompact) printf '%s\n' "post-compact" ;;
        SubagentStart) printf '%s\n' "subagent-start" ;;
        SubagentStop) printf '%s\n' "subagent-stop" ;;
        Stop) printf '%s\n' "stop" ;;
        *) return 1 ;;
    esac
}

release_playback_lock() {
    /bin/rm -f "$LOCK_DIRECTORY/pid" 2>/dev/null
    /bin/rmdir "$LOCK_DIRECTORY" 2>/dev/null
}

acquire_playback_lock() {
    if /bin/mkdir "$LOCK_DIRECTORY" 2>/dev/null; then
        printf '%s\n' "$$" >"$LOCK_DIRECTORY/pid"
        return 0
    fi

    lock_pid=""
    if [ -r "$LOCK_DIRECTORY/pid" ]; then
        IFS= read -r lock_pid <"$LOCK_DIRECTORY/pid"
    fi
    case "$lock_pid" in
        ''|*[!0-9]*) lock_pid="" ;;
    esac
    if [ -n "$lock_pid" ] && kill -0 "$lock_pid" 2>/dev/null; then
        return 1
    fi

    # Avoid racing a worker that created the directory but has not written its
    # PID yet. A directory without a live PID is reclaimed only after 30 seconds.
    now_seconds=$(/bin/date +%s 2>/dev/null)
    lock_seconds=$(/usr/bin/stat -f %m "$LOCK_DIRECTORY" 2>/dev/null)
    case "$now_seconds" in ''|*[!0-9]*) return 1 ;; esac
    case "$lock_seconds" in ''|*[!0-9]*) return 1 ;; esac
    if [ $((now_seconds - lock_seconds)) -lt 30 ]; then
        return 1
    fi

    /bin/rm -f "$LOCK_DIRECTORY/pid" 2>/dev/null
    /bin/rmdir "$LOCK_DIRECTORY" 2>/dev/null || return 1
    /bin/mkdir "$LOCK_DIRECTORY" 2>/dev/null || return 1
    printf '%s\n' "$$" >"$LOCK_DIRECTORY/pid"
    return 0
}

play_worker() {
    audio_path=$1
    runtime_directory=$2
    interval_ms=$3
    # Keep a directory-specific name so upgrades do not collide with the
    # regular playback.lock file created by the legacy Python hook.
    LOCK_DIRECTORY="$runtime_directory/playback.lockdir"

    [ -f "$audio_path" ] || return 0
    [ -x /usr/bin/afplay ] || return 0
    /bin/mkdir -p "$runtime_directory" 2>/dev/null || return 0
    /bin/chmod 700 "$runtime_directory" 2>/dev/null
    acquire_playback_lock || return 0
    trap 'release_playback_lock' 0
    trap 'exit 0' 1 2 3 15

    now_ms=$(
        /usr/bin/osascript -l JavaScript -e 'Math.floor(Date.now())' 2>/dev/null
    )
    case "$now_ms" in
        ''|*[!0-9]*)
            now_seconds=$(/bin/date +%s 2>/dev/null)
            case "$now_seconds" in
                ''|*[!0-9]*) return 0 ;;
            esac
            now_ms=$((now_seconds * 1000))
            ;;
    esac

    timestamp_path="$runtime_directory/playback.timestamp"
    previous_ms=0
    if [ -r "$timestamp_path" ]; then
        IFS= read -r previous_ms <"$timestamp_path"
    fi
    case "$previous_ms" in
        ''|*[!0-9]*) previous_ms=0 ;;
    esac
    elapsed_ms=$((now_ms - previous_ms))
    if [ "$elapsed_ms" -ge 0 ] && [ "$elapsed_ms" -lt "$interval_ms" ]; then
        return 0
    fi

    temporary_timestamp="$runtime_directory/.playback.timestamp.$$"
    printf '%s\n' "$now_ms" >"$temporary_timestamp" &&
        /bin/mv -f "$temporary_timestamp" "$timestamp_path"
    /usr/bin/afplay "$audio_path" >/dev/null 2>&1
    return 0
}

if [ "${1:-}" = "--play" ]; then
    [ "$#" -eq 4 ] || exit 0
    play_worker "$2" "$3" "$4"
    exit 0
fi

event_name=$(
    /usr/bin/head -c 1048577 |
        /usr/bin/osascript -l JavaScript -e '
            ObjC.import("Foundation");
            var input = $.NSFileHandle.fileHandleWithStandardInput
                .readDataToEndOfFile;
            var text = ObjC.unwrap(
                $.NSString.alloc.initWithDataEncoding(
                    input,
                    $.NSUTF8StringEncoding
                )
            );
            var eventName = "";
            try {
                var payload = JSON.parse(text);
                if (
                    payload &&
                    typeof payload.hook_event_name === "string"
                ) {
                    eventName = payload.hook_event_name;
                }
            } catch (error) {}
            eventName;
        ' 2>/dev/null
) || exit 0
event_file=$(event_slug "$event_name") || exit 0

enabled=true
voice=female
language=ko
minimum_interval=450
case "$event_name" in
    PreToolUse|PostToolUse) event_enabled=false ;;
    *) event_enabled=true ;;
esac

config_path=${CODEX_VOICE_NOTIFY_CONFIG:-"${HOME:-}/.config/codex-voice-notify/settings.json"}
if [ -f "$config_path" ]; then
    config_bytes=$(
        /usr/bin/wc -c <"$config_path" 2>/dev/null |
            /usr/bin/tr -d '[:space:]'
    )
    case "$config_bytes" in
        ''|*[!0-9]*) config_bytes=65537 ;;
    esac
    if [ "$config_bytes" -le 65536 ] &&
        /usr/bin/plutil -lint -- "$config_path" >/dev/null 2>&1; then
        configured=$(
            /usr/bin/plutil -extract enabled raw -- "$config_path" 2>/dev/null
        )
        case "$configured" in
            true|false) enabled=$configured ;;
        esac
        configured=$(
            /usr/bin/plutil -extract voice raw -- "$config_path" 2>/dev/null
        )
        case "$configured" in
            female|male) voice=$configured ;;
        esac
        configured=$(
            /usr/bin/plutil -extract language raw -- "$config_path" 2>/dev/null
        )
        case "$configured" in
            ko|ja|en) language=$configured ;;
        esac
        configured=$(
            /usr/bin/plutil -extract min_interval_ms raw -- "$config_path" 2>/dev/null
        )
        case "$configured" in
            ''|*[!0-9]*) ;;
            *)
                if [ "$configured" -gt 10000 ]; then
                    minimum_interval=10000
                else
                    minimum_interval=$configured
                fi
                ;;
        esac
        configured=$(
            /usr/bin/plutil -extract "events.$event_name" raw -- "$config_path" 2>/dev/null
        )
        case "$configured" in
            true|false) event_enabled=$configured ;;
        esac
    fi
fi

[ "$enabled" = true ] || exit 0
[ "$event_enabled" = true ] || exit 0

script_directory=$(
    CDPATH= cd "$(/usr/bin/dirname "$0")" 2>/dev/null && pwd -P
) || exit 0
plugin_root=${PLUGIN_ROOT:-"$script_directory/.."}
audio_path="$plugin_root/assets/audio/$voice/$language/$event_file.wav"
[ -f "$audio_path" ] || exit 0

if [ -n "${PLUGIN_DATA:-}" ]; then
    runtime_directory=$PLUGIN_DATA
else
    runtime_directory="${HOME:-}/Library/Caches/codex-voice-notify"
fi
[ -n "$runtime_directory" ] || exit 0

[ "${CODEX_VOICE_NOTIFY_NO_PLAY:-}" = "1" ] && exit 0
/usr/bin/nohup /bin/sh "$script_directory/play_notify.sh" \
    --play "$audio_path" "$runtime_directory" "$minimum_interval" \
    </dev/null >/dev/null 2>&1 &
exit 0
