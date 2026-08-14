#!/bin/sh
# Configure and test Voice Notify on macOS without Python or developer tools.

umask 077
LC_ALL=C
export LC_ALL

script_directory=$(
    CDPATH= cd "$(/usr/bin/dirname "$0")" 2>/dev/null && pwd -P
) || exit 1
plugin_root=$(
    CDPATH= cd "$script_directory/.." 2>/dev/null && pwd -P
) || exit 1
config_path=${CODEX_VOICE_NOTIFY_CONFIG:-"${HOME:-}/.config/codex-voice-notify/settings.json"}
config_directory=$(/usr/bin/dirname "$config_path")
minimum_hooks_version="0.145.0"

usage_error() {
    printf '%s\n' "$1" >&2
    exit 2
}

valid_voice() {
    case "$1" in female|male) return 0 ;; *) return 1 ;; esac
}

valid_language() {
    case "$1" in ko|ja|en|ru|zh-CN) return 0 ;; *) return 1 ;; esac
}

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

set_default_settings() {
    enabled=true
    voice=female
    language=ko
    minimum_interval=450
    event_session_start=true
    event_user_prompt_submit=true
    event_pre_tool_use=false
    event_post_tool_use=false
    event_permission_request=true
    event_pre_compact=true
    event_post_compact=true
    event_subagent_start=true
    event_subagent_stop=true
    event_stop=true
}

plist_raw() {
    /usr/bin/plutil -extract "$1" raw -- "$config_path" 2>/dev/null
}

configured_boolean() {
    configured_value=$(plist_raw "$1") || {
        printf '%s\n' "$2"
        return
    }
    case "$configured_value" in
        true|false) printf '%s\n' "$configured_value" ;;
        *) printf '%s\n' "$2" ;;
    esac
}

load_settings() {
    set_default_settings
    [ -f "$config_path" ] || return
    config_bytes=$(
        /usr/bin/wc -c <"$config_path" 2>/dev/null |
            /usr/bin/tr -d '[:space:]'
    )
    case "$config_bytes" in
        ''|*[!0-9]*) return ;;
    esac
    [ "$config_bytes" -le 65536 ] || return

    configured_value=$(plist_raw enabled) || configured_value=""
    case "$configured_value" in true|false) enabled=$configured_value ;; esac
    configured_value=$(plist_raw voice) || configured_value=""
    case "$configured_value" in female|male) voice=$configured_value ;; esac
    configured_value=$(plist_raw language) || configured_value=""
    case "$configured_value" in ko|ja|en|ru|zh-CN) language=$configured_value ;; esac
    configured_value=$(plist_raw min_interval_ms) || configured_value=""
    case "$configured_value" in
        ''|*[!0-9]*) ;;
        *)
            if [ "$configured_value" -gt 10000 ]; then
                minimum_interval=10000
            else
                minimum_interval=$configured_value
            fi
            ;;
    esac

    event_session_start=$(configured_boolean events.SessionStart "$event_session_start")
    event_user_prompt_submit=$(configured_boolean events.UserPromptSubmit "$event_user_prompt_submit")
    event_pre_tool_use=$(configured_boolean events.PreToolUse "$event_pre_tool_use")
    event_post_tool_use=$(configured_boolean events.PostToolUse "$event_post_tool_use")
    event_permission_request=$(configured_boolean events.PermissionRequest "$event_permission_request")
    event_pre_compact=$(configured_boolean events.PreCompact "$event_pre_compact")
    event_post_compact=$(configured_boolean events.PostCompact "$event_post_compact")
    event_subagent_start=$(configured_boolean events.SubagentStart "$event_subagent_start")
    event_subagent_stop=$(configured_boolean events.SubagentStop "$event_subagent_stop")
    event_stop=$(configured_boolean events.Stop "$event_stop")
}

emit_settings() {
    printf '%s\n' \
        '{' \
        "  \"enabled\": $enabled," \
        "  \"voice\": \"$voice\"," \
        "  \"language\": \"$language\"," \
        "  \"min_interval_ms\": $minimum_interval," \
        '  "events": {' \
        "    \"SessionStart\": $event_session_start," \
        "    \"UserPromptSubmit\": $event_user_prompt_submit," \
        "    \"PreToolUse\": $event_pre_tool_use," \
        "    \"PostToolUse\": $event_post_tool_use," \
        "    \"PermissionRequest\": $event_permission_request," \
        "    \"PreCompact\": $event_pre_compact," \
        "    \"PostCompact\": $event_post_compact," \
        "    \"SubagentStart\": $event_subagent_start," \
        "    \"SubagentStop\": $event_subagent_stop," \
        "    \"Stop\": $event_stop" \
        '  }' \
        '}'
}

save_settings() {
    if [ ! -d "$config_directory" ]; then
        /bin/mkdir -p "$config_directory" || return 1
        /bin/chmod 700 "$config_directory" 2>/dev/null
    fi
    temporary_path="$config_directory/.settings.$$"
    emit_settings >"$temporary_path" || {
        /bin/rm -f "$temporary_path"
        return 1
    }
    /bin/chmod 600 "$temporary_path" 2>/dev/null
    /bin/mv -f "$temporary_path" "$config_path" || {
        /bin/rm -f "$temporary_path"
        return 1
    }
    printf 'Saved %s\n' "$config_path"
}

set_event_value() {
    event_name=$1
    event_value=$2
    case "$event_name" in
        SessionStart) event_session_start=$event_value ;;
        UserPromptSubmit) event_user_prompt_submit=$event_value ;;
        PreToolUse) event_pre_tool_use=$event_value ;;
        PostToolUse) event_post_tool_use=$event_value ;;
        PermissionRequest) event_permission_request=$event_value ;;
        PreCompact) event_pre_compact=$event_value ;;
        PostCompact) event_post_compact=$event_value ;;
        SubagentStart) event_subagent_start=$event_value ;;
        SubagentStop) event_subagent_stop=$event_value ;;
        Stop) event_stop=$event_value ;;
        *) return 1 ;;
    esac
}

apply_choices() {
    if [ -n "$voice_choice" ]; then
        valid_voice "$voice_choice" || usage_error "Voice must be female or male."
        voice=$voice_choice
    fi
    if [ -n "$language_choice" ]; then
        valid_language "$language_choice" ||
            usage_error "Language must be ko, ja, en, ru, or zh-CN."
        language=$language_choice
    fi
    if [ -n "$interval_choice" ]; then
        case "$interval_choice" in
            ''|*[!0-9]*) usage_error "Minimum interval must be a non-negative integer." ;;
        esac
        if [ "$interval_choice" -gt 10000 ]; then
            minimum_interval=10000
        else
            minimum_interval=$interval_choice
        fi
    fi
    for event_name in $enable_events; do
        set_event_value "$event_name" true ||
            usage_error "Unsupported event: $event_name"
    done
    for event_name in $disable_events; do
        set_event_value "$event_name" false ||
            usage_error "Unsupported event: $event_name"
    done
}

selected_audio_path() {
    selected_event=$1
    selected_slug=$(event_slug "$selected_event") || return 1
    printf '%s\n' "$plugin_root/assets/audio/$voice/$language/$selected_slug.wav"
}

find_codex_command() {
    if [ -n "$codex_choice" ]; then
        printf '%s\n' "$codex_choice"
        return
    fi
    if [ -n "${CODEX_VOICE_NOTIFY_CODEX:-}" ]; then
        printf '%s\n' "$CODEX_VOICE_NOTIFY_CODEX"
        return
    fi
    command -v codex 2>/dev/null
}

inspect_codex() {
    codex_path=$(find_codex_command) || codex_path=""
    if [ -z "$codex_path" ]; then
        printf '%s\n' \
            "Codex CLI was not found. Install or expose Codex on PATH, then rerun setup." >&2
        return 3
    fi
    codex_output=$("$codex_path" --version 2>&1)
    codex_status=$?
    if [ "$codex_status" -ne 0 ]; then
        printf 'Could not determine the Codex CLI version from %s.\n' "$codex_path" >&2
        return 3
    fi
    case "$codex_output" in
        *'
'*)
            printf 'Could not determine the Codex CLI version from %s.\n' "$codex_path" >&2
            return 3
            ;;
    esac
    version_parts=$(
        printf '%s' "$codex_output" |
            /usr/bin/tr '[:upper:]' '[:lower:]' |
            /usr/bin/sed -nE \
                's/^[[:space:]]*(openai[[:space:]]+)?codex(-cli)?[[:space:]]+\(?v?([0-9]+)\.([0-9]+)\.([0-9]+)\)?[[:space:]]*$/\3 \4 \5/p'
    )
    set -- $version_parts
    if [ "$#" -ne 3 ]; then
        printf 'Could not determine the Codex CLI version from %s.\n' "$codex_path" >&2
        return 3
    fi
    codex_major=$1
    codex_minor=$2
    codex_patch=$3
    printf 'Codex CLI: %s.%s.%s (%s)\n' \
        "$codex_major" "$codex_minor" "$codex_patch" "$codex_path"
    if [ "$codex_major" -lt 0 ] ||
        { [ "$codex_major" -eq 0 ] && [ "$codex_minor" -lt 145 ]; }; then
        printf 'Codex CLI %s or newer is required for /hooks. Update Codex, then rerun setup.\n' \
            "$minimum_hooks_version" >&2
        return 3
    fi
    return 0
}

shell_quote() {
    quoted_value=$(
        printf '%s' "$1" | /usr/bin/sed "s/'/'\\\\''/g"
    )
    printf "'%s'" "$quoted_value"
}

open_hook_terminal() {
    working_directory=$(pwd -P)
    terminal_command="printf '\\nVoice Notify opened this new Codex CLI terminal. Type /hooks here and review the bundled hook.\\n\\n'; exec $(shell_quote "$codex_path") --no-alt-screen -C $(shell_quote "$working_directory")"
    /usr/bin/osascript \
        -e 'on run argv' \
        -e 'set terminalCommand to item 1 of argv' \
        -e 'tell application "Terminal"' \
        -e 'activate' \
        -e 'do script terminalCommand' \
        -e 'end tell' \
        -e 'end run' \
        -- "$terminal_command" >/dev/null 2>&1
}

command_name=${1:-show}
if [ "$#" -gt 0 ]; then
    shift
fi
voice_choice=""
language_choice=""
interval_choice=""
enable_events=""
disable_events=""
event_choice="Stop"
dry_run=false
skip_audio_test=false
open_hooks=false
codex_choice=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --voice)
            [ "$#" -ge 2 ] || usage_error "--voice requires a value."
            voice_choice=$2
            shift 2
            ;;
        --language)
            [ "$#" -ge 2 ] || usage_error "--language requires a value."
            language_choice=$2
            shift 2
            ;;
        --min-interval-ms)
            [ "$#" -ge 2 ] || usage_error "--min-interval-ms requires a value."
            interval_choice=$2
            shift 2
            ;;
        --enable-event)
            [ "$#" -ge 2 ] || usage_error "--enable-event requires a value."
            event_slug "$2" >/dev/null ||
                usage_error "Unsupported event: $2"
            enable_events="$enable_events $2"
            shift 2
            ;;
        --disable-event)
            [ "$#" -ge 2 ] || usage_error "--disable-event requires a value."
            event_slug "$2" >/dev/null ||
                usage_error "Unsupported event: $2"
            disable_events="$disable_events $2"
            shift 2
            ;;
        --event)
            [ "$#" -ge 2 ] || usage_error "--event requires a value."
            event_slug "$2" >/dev/null ||
                usage_error "Unsupported event: $2"
            event_choice=$2
            shift 2
            ;;
        --dry-run)
            dry_run=true
            shift
            ;;
        --skip-audio-test)
            skip_audio_test=true
            shift
            ;;
        --open-hooks)
            open_hooks=true
            shift
            ;;
        --codex-command)
            [ "$#" -ge 2 ] || usage_error "--codex-command requires a value."
            codex_choice=$2
            shift 2
            ;;
        *)
            usage_error "Unknown option: $1"
            ;;
    esac
done

load_settings

case "$command_name" in
    show)
        emit_settings
        ;;
    reset)
        /bin/rm -f "$config_path"
        printf '%s\n' "Defaults restored."
        ;;
    mute)
        enabled=false
        save_settings || exit 1
        ;;
    unmute)
        enabled=true
        save_settings || exit 1
        ;;
    set)
        apply_choices
        save_settings || exit 1
        ;;
    test)
        apply_choices
        enabled=true
        set_event_value "$event_choice" true || exit 2
        audio_path=$(selected_audio_path "$event_choice") || exit 2
        if [ ! -f "$audio_path" ]; then
            printf 'Audio file is unavailable: %s\n' "$audio_path" >&2
            exit 1
        fi
        printf '%s\n' "$audio_path"
        if [ "$dry_run" = false ]; then
            [ -x /usr/bin/afplay ] || {
                printf '%s\n' "The macOS afplay command is unavailable." >&2
                exit 1
            }
            /usr/bin/afplay "$audio_path" || exit $?
        fi
        ;;
    setup)
        apply_choices
        enabled=true
        inspect_codex || exit $?
        audio_path=$(selected_audio_path Stop) || exit 1
        if [ ! -f "$audio_path" ]; then
            printf 'Stop audio file is unavailable: %s\n' "$audio_path" >&2
            exit 1
        fi
        printf 'Stop audio: %s\n' "$audio_path"
        if [ "$dry_run" = false ] && [ "$skip_audio_test" = false ]; then
            [ -x /usr/bin/afplay ] || {
                printf '%s\n' "The macOS afplay command is unavailable." >&2
                exit 1
            }
            /usr/bin/afplay "$audio_path" || exit $?
        fi
        if [ "$dry_run" = true ]; then
            printf 'Dry run: would save voice=%s language=%s.\n' "$voice" "$language"
        else
            save_settings || exit 1
        fi
        if [ "$open_hooks" = true ]; then
            if [ "$dry_run" = true ]; then
                printf '%s\n' \
                    "Dry run: would open a new terminal and start Codex CLI for manual /hooks review."
            elif open_hook_terminal; then
                printf '%s\n' \
                    "Started Codex CLI in a new Terminal window. Type /hooks in that window, review the Voice Notify hook, and trust it."
            else
                printf '%s\n' \
                    "Could not open a new Codex CLI Terminal automatically. Start Codex CLI yourself, enter /hooks, and review the Voice Notify hook." >&2
                exit 4
            fi
        else
            printf '%s\n' "Next: run Codex, enter /hooks, and review the Voice Notify hook."
        fi
        printf '%s\n' \
            "After trust is granted, fully restart Codex before testing lifecycle events."
        ;;
    *)
        usage_error "Command must be show, set, mute, unmute, reset, test, or setup."
        ;;
esac
exit 0
