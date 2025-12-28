#!/bin/bash
# install.sh - Full Scribbulus installation
# Run with --help for usage information.

set -o errexit
set -o nounset
set -o pipefail

# Get script directory for relative script calls
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source shared libraries
# shellcheck source=lib/output.sh
source "${SCRIPT_DIR}/lib/output.sh"
# shellcheck source=lib/platform.sh
source "${SCRIPT_DIR}/lib/platform.sh"
# shellcheck source=lib/args.sh
source "${SCRIPT_DIR}/lib/args.sh"

# Print help message
show_help() {
    cat <<'EOF'
install.sh - Full Scribbulus installation

Usage: ./scripts/install.sh [OPTIONS] [COMPONENT]

Components:
  --all      Install everything (default)
  --uv       Install only uv package manager
  --ffmpeg   Install only ffmpeg
  --deps     Install only system dependencies (ffmpeg)

Options:
  -f, --force    Force reinstall of dependencies
  -q, --quiet    Suppress non-error output
  -h, --help     Show this help message

Exit codes:
  0  Success
  1  General error
EOF
}

# Parse arguments (FORCE and QUIET exported by args.sh)
parse_args "$@"

# Default to --all if no component specified
if [[ "${INSTALL_UV}" -eq 0 ]] && \
   [[ "${INSTALL_FFMPEG}" -eq 0 ]] && \
   [[ "${INSTALL_DEPS}" -eq 0 ]] && \
   [[ "${INSTALL_ALL}" -eq 0 ]]; then
    INSTALL_ALL=1
fi

# Build flags for child scripts
CHILD_FLAGS=()
[[ "${FORCE}" -eq 1 ]] && CHILD_FLAGS+=("--force")
[[ "${QUIET}" -eq 1 ]] && CHILD_FLAGS+=("--quiet")

# =============================================================================
# Installation Functions
# =============================================================================

install_uv() {
    log_step "Installing uv package manager..."
    "${SCRIPT_DIR}/install-uv.sh" "${CHILD_FLAGS[@]+"${CHILD_FLAGS[@]}"}"

    # Ensure uv is available (may need to source env)
    if ! has_command uv; then
        if [[ -f "${HOME}/.local/bin/env" ]]; then
            # shellcheck disable=SC1091 # File may not exist at lint time
            source "${HOME}/.local/bin/env"
        fi
    fi

    # Verify uv is now available
    if ! has_command uv; then
        log_error "uv is still not available after installation."
        log_error "Please restart your shell and run this script again."
        exit 1
    fi
}

install_ffmpeg() {
    if ! has_command ffmpeg || [[ "${FORCE}" -eq 1 ]]; then
        log_step "Installing ffmpeg..."
        "${SCRIPT_DIR}/install-ffmpeg.sh" "${CHILD_FLAGS[@]+"${CHILD_FLAGS[@]}"}"
    else
        log_info "ffmpeg is already installed."
    fi
}

install_python_package() {
    log_step "Installing scribbulus Python package..."
    uv sync
    uv pip install -e .

    # Validate installation - ensure the package is importable
    log_step "Validating installation..."
    if ! uv run python -c "import scribbulus" 2>/dev/null; then
        log_error "Installation validation failed: cannot import scribbulus"
        log_error "Try: uv pip install -e . --force-reinstall"
        exit 1
    fi

    # Validate CLI entrypoint
    if ! uv run scribbulus --version >/dev/null 2>&1; then
        log_error "CLI entrypoint validation failed: scribbulus command not working"
        exit 1
    fi

    log_info "Installation validated successfully."
}

# =============================================================================
# Main Installation Logic
# =============================================================================

log_success "=== Scribbulus Installation ==="
log_blank

# Handle component-specific installation
if [[ "${INSTALL_ALL}" -eq 1 ]]; then
    # Full installation
    log_step "Step 1/3: Installing uv package manager..."
    install_uv

    log_step "Step 2/3: Checking ffmpeg..."
    install_ffmpeg

    log_step "Step 3/3: Installing Python package..."
    install_python_package

    # Success message
    log_blank
    log_success "========================================"
    log_success "Installation complete!"
    log_success "========================================"
    log_blank
    log_warn "Quick start:"
    printf '  scribbulus transcribe video.mp4 -o transcript.txt\n'
    log_blank
    log_warn "For speaker diarization, set your HuggingFace token:"
    printf '  export HF_TOKEN=your_token_here\n'
    log_blank
    log_warn "Get help:"
    printf '  scribbulus --help\n'

elif [[ "${INSTALL_UV}" -eq 1 ]]; then
    install_uv
    log_success "uv installation complete!"

elif [[ "${INSTALL_FFMPEG}" -eq 1 ]]; then
    install_ffmpeg
    log_success "ffmpeg installation complete!"

elif [[ "${INSTALL_DEPS}" -eq 1 ]]; then
    install_ffmpeg
    log_success "System dependencies installation complete!"
fi
