#!/bin/bash
# args.sh - Shared argument parsing for Scribbulus installers
#
# Source this in installer scripts after output.sh:
#   source "${SCRIPT_DIR}/lib/args.sh"
#
# Scripts must define show_help() before calling parse_args.
# Scripts may define parse_custom_arg() for additional flags.

# Prevent multiple sourcing
if [[ -n "${_ARGS_SH_LOADED:-}" ]]; then
    return 0
fi
readonly _ARGS_SH_LOADED=1

# =============================================================================
# Default values (can be inherited from parent via environment)
# =============================================================================

FORCE="${FORCE:-0}"
QUIET="${QUIET:-0}"

# Install component flags (used by install.sh)
INSTALL_ALL="${INSTALL_ALL:-0}"
INSTALL_UV="${INSTALL_UV:-0}"
INSTALL_FFMPEG="${INSTALL_FFMPEG:-0}"
INSTALL_DEPS="${INSTALL_DEPS:-0}"

# =============================================================================
# Core parsing function
# =============================================================================

# Parse command line arguments
# Scripts should define show_help() and optionally parse_custom_arg()
# Usage: parse_args "$@"
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--force)
                FORCE=1
                shift
                ;;
            -q|--quiet)
                QUIET=1
                shift
                ;;
            -h|--help)
                if declare -f show_help > /dev/null; then
                    show_help
                else
                    printf 'No help available.\n'
                fi
                exit 0
                ;;
            --all)
                INSTALL_ALL=1
                shift
                ;;
            --uv)
                INSTALL_UV=1
                shift
                ;;
            --ffmpeg)
                INSTALL_FFMPEG=1
                shift
                ;;
            --deps)
                INSTALL_DEPS=1
                shift
                ;;
            *)
                _args_handle_unknown "$1"
                ;;
        esac
    done

    export FORCE
    export QUIET
}

# Handle unknown argument - exits with error
_args_handle_unknown() {
    if declare -f log_error > /dev/null; then
        log_error "Unknown option: $1"
    else
        printf 'Error: Unknown option: %s\n' "$1" >&2
    fi
    printf 'Use --help for usage.\n'
    exit 1
}
