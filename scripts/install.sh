#!/bin/bash
# install.sh - Full Scribbulus installation
#
# Usage: ./scripts/install.sh [OPTIONS]
#
# Options:
#   -f, --force    Force reinstall of dependencies
#   -q, --quiet    Suppress non-error output
#   -h, --help     Show this help message
#
# Exit codes:
#   0  Success
#   1  General error

set -o errexit
set -o nounset
set -o pipefail

# Get script directory for relative script calls
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly RED='\033[0;31m'
readonly NC='\033[0m'

# Defaults
FORCE=0
QUIET=0
FORCE_FLAG=""
QUIET_FLAG=""

# Print help message from script header
show_help() {
    sed -n '2,13p' "$0" | sed 's/^# //' | sed 's/^#//'
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
            FORCE_FLAG="--force"
            shift
            ;;
        -q|--quiet)
            QUIET=1
            QUIET_FLAG="--quiet"
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

log_info "=== Scribbulus Installation ==="
if [[ "${QUIET}" -eq 0 ]]; then
    printf '\n'
fi

# Step 1: Install uv
log_info "Step 1/3: Installing uv package manager..."
# shellcheck disable=SC2086 # Word splitting intended for flags
"${SCRIPT_DIR}/install-uv.sh" ${FORCE_FLAG} ${QUIET_FLAG}

# Ensure uv is available (may need to source env)
if ! command -v uv &> /dev/null; then
    if [[ -f "${HOME}/.local/bin/env" ]]; then
        # shellcheck disable=SC1091 # File may not exist at lint time
        source "${HOME}/.local/bin/env"
    fi
fi

# Verify uv is now available
if ! command -v uv &> /dev/null; then
    log_error "uv is still not available after installation."
    log_error "Please restart your shell and run this script again."
    exit 1
fi

# Step 2: Install ffmpeg if not present
log_info "Step 2/3: Checking ffmpeg..."
if ! command -v ffmpeg &> /dev/null || [[ "${FORCE}" -eq 1 ]]; then
    log_warn "Installing ffmpeg..."
    # shellcheck disable=SC2086 # Word splitting intended for flags
    "${SCRIPT_DIR}/install-ffmpeg.sh" ${FORCE_FLAG} ${QUIET_FLAG}
else
    log_info "ffmpeg is already installed."
fi

# Step 3: Install Python package
log_info "Step 3/3: Installing scribbulus Python package..."
uv sync
uv pip install -e .

# Success message
printf '\n'
log_info "========================================"
log_info "Installation complete!"
log_info "========================================"
printf '\n'
log_warn "Quick start:"
printf '  scribbulus transcribe video.mp4 -o transcript.txt\n'
printf '\n'
log_warn "For speaker diarization, set your HuggingFace token:"
printf '  export HF_TOKEN=your_token_here\n'
printf '\n'
log_warn "Get help:"
printf '  scribbulus --help\n'
