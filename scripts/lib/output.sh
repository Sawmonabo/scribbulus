#!/bin/bash
# output.sh - Shared output utilities for Scribbulus installers
#
# Source this at the start of installer scripts:
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   source "${SCRIPT_DIR}/lib/output.sh"
#
# Provides:
#   - TTY-aware colored output
#   - NO_COLOR standard compliance (https://no-color.org/)
#   - CI environment detection
#   - Consistent logging functions
#
# Exported variables:
#   IS_TTY      - "1" if stdout is a terminal, "0" otherwise
#   IS_CI       - "1" if running in CI environment, "0" otherwise
#   USE_COLOR   - "1" if colors should be used, "0" otherwise
#
# Log functions (all respect QUIET variable):
#   log_info    - Green, informational messages
#   log_warn    - Yellow, warning messages (to stderr)
#   log_error   - Red, error messages (to stderr, ignores QUIET)
#   log_step    - Blue, numbered step indicators
#   log_success - Green bold, completion messages
#   log_blank   - Empty line (respects QUIET)

# Prevent multiple sourcing
if [[ -n "${_OUTPUT_SH_LOADED:-}" ]]; then
    return 0
fi
readonly _OUTPUT_SH_LOADED=1

# =============================================================================
# Environment Detection
# =============================================================================

# Detect if stdout is a TTY
IS_TTY=0
if [[ -t 1 ]]; then
    IS_TTY=1
fi
readonly IS_TTY
export IS_TTY

# Detect CI environments
IS_CI=0
if [[ -n "${CI:-}" ]] || \
   [[ -n "${GITHUB_ACTIONS:-}" ]] || \
   [[ -n "${GITLAB_CI:-}" ]] || \
   [[ -n "${JENKINS_URL:-}" ]] || \
   [[ -n "${TRAVIS:-}" ]] || \
   [[ -n "${CIRCLECI:-}" ]]; then
    IS_CI=1
fi
readonly IS_CI
export IS_CI

# Determine if colors should be used
# Respect NO_COLOR standard: https://no-color.org/
USE_COLOR=0
if [[ "${IS_TTY}" -eq 1 ]] && [[ -z "${NO_COLOR:-}" ]]; then
    USE_COLOR=1
fi
readonly USE_COLOR
export USE_COLOR

# =============================================================================
# Color Definitions
# =============================================================================

if [[ "${USE_COLOR}" -eq 1 ]]; then
    readonly _RED='\033[0;31m'
    readonly _GREEN='\033[0;32m'
    readonly _YELLOW='\033[0;33m'
    readonly _BLUE='\033[0;34m'
    readonly _BOLD='\033[1m'
    readonly _NC='\033[0m'  # No Color
else
    readonly _RED=''
    readonly _GREEN=''
    readonly _YELLOW=''
    readonly _BLUE=''
    readonly _BOLD=''
    readonly _NC=''
fi

# =============================================================================
# Logging Functions
# =============================================================================

# Print informational message (green)
# Respects QUIET variable
log_info() {
    if [[ "${QUIET:-0}" -eq 1 ]]; then
        return
    fi
    printf '%b==>%b %s\n' "${_GREEN}${_BOLD}" "${_NC}" "$1"
}

# Print warning message (yellow, to stderr)
# Respects QUIET variable
log_warn() {
    if [[ "${QUIET:-0}" -eq 1 ]]; then
        return
    fi
    printf '%b==>%b %bWarning:%b %s\n' "${_YELLOW}${_BOLD}" "${_NC}" "${_YELLOW}" "${_NC}" "$1" >&2
}

# Print error message (red, to stderr)
# ALWAYS prints (ignores QUIET)
log_error() {
    printf '%b==>%b %bError:%b %s\n' "${_RED}${_BOLD}" "${_NC}" "${_RED}" "${_NC}" "$1" >&2
}

# Print step indicator (blue)
# Respects QUIET variable
# Usage: log_step "Step 1/3: Installing dependencies..."
log_step() {
    if [[ "${QUIET:-0}" -eq 1 ]]; then
        return
    fi
    printf '%b==>%b %s\n' "${_BLUE}${_BOLD}" "${_NC}" "$1"
}

# Print success/completion message (green bold)
# Respects QUIET variable
log_success() {
    if [[ "${QUIET:-0}" -eq 1 ]]; then
        return
    fi
    printf '%b==>%b %s\n' "${_GREEN}${_BOLD}" "${_NC}" "$1"
}

# Print a blank line
# Respects QUIET variable
log_blank() {
    if [[ "${QUIET:-0}" -eq 1 ]]; then
        return
    fi
    printf '\n'
}

# =============================================================================
# Utility Functions
# =============================================================================

# Print a command before executing it (for debugging)
# Only prints if SCRIBBULUS_DEBUG is set
# Usage: run_cmd git status
run_cmd() {
    if [[ -n "${SCRIBBULUS_DEBUG:-}" ]]; then
        printf '%b[DEBUG]%b Running: %s\n' "${_BOLD}" "${_NC}" "$*" >&2
    fi
    "$@"
}

# Exit with error message
# Usage: die "Something went wrong"
die() {
    log_error "$1"
    exit "${2:-1}"
}

# Check if a command exists
# Usage: if has_command curl; then ...
has_command() {
    command -v "$1" &>/dev/null
}
