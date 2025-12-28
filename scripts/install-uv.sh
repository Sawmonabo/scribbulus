#!/bin/bash
# install-uv.sh - Install the uv package manager for Scribbulus
# Run with --help for usage information.

set -o errexit
set -o nounset
set -o pipefail

# Get script directory for relative script calls
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source shared libraries
# shellcheck source=lib/output.sh
source "${SCRIPT_DIR}/lib/output.sh"
# shellcheck source=lib/args.sh
source "${SCRIPT_DIR}/lib/args.sh"

# Print help message
show_help() {
    cat <<'EOF'
install-uv.sh - Install the uv package manager for Scribbulus

Usage: ./scripts/install-uv.sh [OPTIONS]

Options:
  -f, --force    Force reinstall even if uv is present
  -q, --quiet    Suppress non-error output
  -h, --help     Show this help message

Exit codes:
  0  Success (installed or already present)
  1  General error
  5  Network/download error
EOF
}

# Parse arguments (FORCE and QUIET exported by args.sh)
parse_args "$@"

log_success "=== uv Package Manager Installer ==="
log_blank

# Check if already installed
if has_command uv; then
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
log_step "Installing uv..."
if ! curl --connect-timeout 30 --max-time 120 -LsSf https://astral.sh/uv/install.sh | sh; then
    log_error "Failed to install uv"
    log_blank
    log_warn "If this is a network issue, check your connection and retry."
    log_warn "For manual installation, see: https://docs.astral.sh/uv/"
    exit 5
fi

log_blank
log_success "uv installed successfully!"
log_blank
log_warn "Note: You may need to restart your shell or run:"
# shellcheck disable=SC2016 # Intentionally unexpanded - showing literal command
printf '  source $HOME/.local/bin/env\n'
log_blank

# Verify installation if uv is now available
if has_command uv; then
    log_info "Verification:"
    uv --version
fi
