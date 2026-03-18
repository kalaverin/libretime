#!/usr/bin/env zsh

local -Ax Error=(
    [Ok]=0
    [Generic]=1
    [NotProject]=2
    [NotRunning]=3
    [StartFailed]=4
    [UnknownMethod]=5
)

local -Ax Method=(
    [Unknown]=0
    [VirtualEnv]=1
    [AstralUv]=2
    [SystemWide]=3
)

local DIR_RUN="var/run"


function get_root {
    local dir

    (( $# )) || {
        print -u2 " == fail ($0): missing argument: <this-file-path>"
        return $Error[Generic]
    }

    # abosulufy, then head one -> etc/, head two -> ../

    dir="${1:A:h:h}" || return $?

    [[ -d "$dir/$DIR_RUN" && -x "$dir/$DIR_RUN" && -f "$dir/etc/$name.conf" ]] || {
        print -u2 " == fail ($0): not a project root: '$dir'"
        return $Error[NoProject]
    }

    printf '%s' "$dir"
    return $Error[Ok]
}


function load_environment {
    local dir

    (( $# )) || {
        print -u2 " == fail ($0): missing argument: <project-root-dir>"
        return $Error[Generic]
    }
    dir="${1:A}" || return $?

    if [[ -x "$commands[direnv]" && -f "$dir/.envrc" ]]; then
        print -u2 " -- info ($0): use direnv environment from '$dir/.envrc'"
        eval "$(direnv export zsh)" || return $?
    fi

    if [[ -x "$commands[mise]" && -f "$dir/.mise.toml" ]]; then
        print -u2 " -- info ($0): use mise environment from '$dir/.mise.toml'"
        eval "$(mise activate)" || return $?
    fi

    return $Error[Ok]
}


function is_started {
    local dir
    local -i pid

    (( $# )) || {
        print -u2 " == fail ($0): missing argument: <project-root-dir>"
        return $Error[Generic]
    }
    dir="${1:A}" || return $?


    [[ -f "$dir/$DIR_RUN/$name.pid" ]] || {
        return $Error[NotRunning]
    }

    pid="$(pgrep -F "$dir/$DIR_RUN/$name.pid")"

    [[ -n "$pid" && "$pid" -gt 0 && -S "$dir/$DIR_RUN/$name.sock" ]] || {
        return $Error[NotRunning]
    }

    return $Error[Ok]
}


function get_start_method {
    # first, if we are in virtualenv, use it

    if [[ -n "$VIRTUAL_ENV" && -x "$VIRTUAL_ENV/bin/$name" ]]; then
        print -u2 " -- info ($0): use supervisord from $VIRTUAL_ENV"
        return $Method[VirtualEnv]

    # then, try to start directly

    elif (( $+commands[supervisord] )); then
        print -u2 " -- info ($0): use system-wide $commands[supervisord]"
        return $Method[SystemWide]

    # otherwise, try to start via uvx

    elif (( $+commands[uvx] )); then
        print -u2 " -- info ($0): use supervisord via $commands[uvx]"
        return $Method[AstralUv]

    fi

    return $Method[Unknown]
}

# main logic

local root
local -i error=0 method=0
local -r name="supervisord"

local -a uv_args=(
    --no-progress
    --quiet
    --color always
    --from supervisor
)

root="$(get_root "$0")" || return $?

local -a supervisord_args=(
    --silent
    --configuration
    "$root/etc/$name.conf"
)

is_started "$root"; error=$?

if (( error == Error[Ok] )); then
    # already running
    return $error

elif (( error != Error[NotRunning] )); then
    # any unexpected error
    print -u2 " == fail ($0): unexpected error: $error"
    return $error
fi

# supervisord is not running, let start it!

# switch to project root

builtin cd "$root" || return "$?"

# load environment

load_environment "$root" || return $?

# ensure log dirs exist

if [[ ! -d "$root/log/errors" ]]; then
    print -u2 " -- info ($0): create errors log dir in '$root/log/errors'"

    mkdir -p "$root/log/errors" || {
        print -u2 " == fail ($0): cannot create errors log dir"
        return $?
    }
fi

# determine start method

get_start_method; method=$?

(( method )) || {
    print -u2 " == fail ($0): cannot determine start method in '$root'"
    return $Error[UnknownMethod]
}

# report active virtualenv if any

if (( $+VIRTUAL_ENV )); then
    print -u2 " -- info ($0): active virtualenv: $VIRTUAL_ENV"
fi

# start supervisord according to determined method

if (( method == Method[VirtualEnv] )); then

    $VIRTUAL_ENV/bin/$name $supervisord_args[@] || {
        error=$?
        print -u2 " == fail ($0): start in virtualenv failed ($error)" >&2
        return $error
    }

elif (( method == Method[AstralUv] )); then

    uvx $uv_args[@] $name $supervisord_args[@] || {
        error=$?
        print -u2 " == fail ($0): start via uvx failed ($error)"
        return $error
    }

elif (( method == Method[SystemWide] )); then

    supervisord $supervisord_args[@] || {
        error=$?
        print -u2 " == fail ($0): direct start failed ($error)"
        return $error
    }

else
    print -u2 " == fail ($0): unknown start method: $method"
    return $Error[UnknownMethod]
fi

# wait a bit and check is started

print -u2 " -- info ($0): supervisord starting up, wait.." && \
    sleep 1.0 && \
    is_started "$root"

error=$?
(( error )) && {
    print -u2 " == fail ($0): supervisord start failed ($error)"
    return $error
}
