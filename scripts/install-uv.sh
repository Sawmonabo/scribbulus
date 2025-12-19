#!/bin/bash
# install-uv.sh - Install the uv package manager for Scribbulus
#
# Usage: ./scripts/install-uv.sh [OPTIONS]
#
# Options:
#   -f, --force    Force reinstall even if uv is present
#   -q, --quiet    Suppress non-error output
#   -h, --help     Show this help message
#
# Exit codes:
#   0  Success (installed or already present)
#   1  General error
#   5  Network/download error

set -o errexit
set -o nounset
set -o pipefail

# Colors
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly RED='\033[0;31m'
readonly NC='\033[0m'

# Defaults
FORCE=0
QUIET=0

# Print help message from script header
show_help() {
    sed -n '2,14p' "$0" | sed 's/^# //' | sed 's/^#//'
}

# Logging functions
log_info() {
    if [[ "${QUIET}" -eq 0 ]]; then
        printf '%b%s%b\n' "${GREEN}" "$1" "${NC}"
    fi
}

log_warn() {
    if [[ "${QUIET}" -eq 0 ]]; then
        printf '%b%s%b\n' "${YELLOW}" "$1" "${NC}"
    fi
}

log_error() {
    printf '%b%s%b\n' "${RED}" "$1" "${NC}" >&2
}

# Parse arguments
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
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            printf 'Use --help for usage.\n'
            exit 1
            ;;
    esac
done

log_info "=== uv Package Manager Installer ==="
if [[ "${QUIET}" -eq 0 ]]; then
    printf '\n'
fi

# Check if already installed
if command -v uv &> /dev/null; then
    log_info "uv is already installed:"
    if [[ "${QUIET}" -eq 0 ]]; then
        uv --version
    fi
    if [[ "${FORCE}" -eq 0 ]]; then
        log_info "Use --force to reinstall."
        exit 0
    fi
    log_warn "Force reinstall requested..."
fi

# Install via official installer
log_warn "Installing uv..."
if ! curl -LsSf https://astral.sh/uv/install.sh | sh; then
    log_error "Failed to install uv"
    exit 5
fi

printf '\n'
log_info "uv installed successfully!"
printf '\n'
log_warn "Note: You may need to restart your shell or run:"
# shellcheck disable=SC2016 # Intentionally unexpanded - showing literal command
printf '  source $HOME/.local/bin/env\n'
printf '\n'

# Verify installation if uv is now available
if command -v uv &> /dev/null; then
    log_info "Verification:"
    uv --version
fi
