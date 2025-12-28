#!/bin/bash
# doctor.sh - Diagnose Scribbulus installation issues
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

# Track issues found
ISSUES_FOUND=0

# Print help message
show_help() {
    cat <<'EOF'
doctor.sh - Diagnose Scribbulus installation issues

Usage: ./scripts/doctor.sh [OPTIONS]

Options:
  -q, --quiet    Only show issues, suppress OK messages
  -h, --help     Show this help message

Checks:
  - Python/uv environment
  - Scribbulus package importability
  - CLI entrypoint resolution
  - ffmpeg availability
  - libsndfile availability (audio backend)
  - HuggingFace token for diarization

Exit codes:
  0  All checks passed
  1  One or more issues found
EOF
}

# Parse arguments
QUIET=0
while [[ $# -gt 0 ]]; do
    case "$1" in
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
            show_help
            exit 1
            ;;
    esac
done

# Helper to report check results
check_ok() {
    [[ "${QUIET}" -eq 0 ]] && log_success "[OK] $1"
}

check_warn() {
    log_warn "[WARN] $1"
}

check_fail() {
    log_error "[FAIL] $1"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
}

# =============================================================================
# Diagnostic Checks
# =============================================================================

log_success "=== Scribbulus Doctor ==="
log_blank
log_step "Running diagnostics..."
log_blank

# -----------------------------------------------------------------------------
# Check 1: uv is available
# -----------------------------------------------------------------------------
log_step "Checking uv package manager..."
if has_command uv; then
    UV_VERSION=$(uv --version 2>/dev/null || echo "unknown")
    check_ok "uv is installed: ${UV_VERSION}"
else
    check_fail "uv is not installed"
    log_blank
    printf '  Remediation: Install uv with:\n'
    printf '    curl -LsSf https://astral.sh/uv/install.sh | sh\n'
    log_blank
fi

# -----------------------------------------------------------------------------
# Check 2: Scribbulus package is importable
# -----------------------------------------------------------------------------
log_step "Checking scribbulus package..."
if uv run python -c "import scribbulus" 2>/dev/null; then
    VERSION=$(uv run python -c "import scribbulus; print(scribbulus.__version__)" 2>/dev/null || echo "unknown")
    check_ok "scribbulus package is importable: v${VERSION}"
else
    check_fail "scribbulus package cannot be imported"
    log_blank
    printf '  Remediation: Install the package with:\n'
    printf '    uv pip install -e .\n'
    printf '  Or if that fails:\n'
    printf '    uv pip install -e . --force-reinstall\n'
    log_blank
fi

# -----------------------------------------------------------------------------
# Check 3: CLI entrypoint works
# -----------------------------------------------------------------------------
log_step "Checking CLI entrypoint..."
if uv run scribbulus --version >/dev/null 2>&1; then
    CLI_VERSION=$(uv run scribbulus --version 2>/dev/null || echo "unknown")
    check_ok "CLI entrypoint works: ${CLI_VERSION}"
else
    check_fail "CLI entrypoint 'scribbulus' is not working"
    log_blank
    printf '  Remediation: Reinstall the package with:\n'
    printf '    uv pip install -e . --force-reinstall\n'
    log_blank
fi

# -----------------------------------------------------------------------------
# Check 4: ffmpeg is available
# -----------------------------------------------------------------------------
log_step "Checking ffmpeg..."
if has_command ffmpeg; then
    FFMPEG_VERSION=$(ffmpeg -version 2>/dev/null | head -1 || echo "unknown")
    check_ok "ffmpeg is installed: ${FFMPEG_VERSION}"
else
    check_fail "ffmpeg is not installed"
    log_blank
    printf '  Remediation: Install ffmpeg with:\n'
    printf '    ./scripts/install-ffmpeg.sh\n'
    log_blank
fi

# -----------------------------------------------------------------------------
# Check 5: ffprobe is available
# -----------------------------------------------------------------------------
log_step "Checking ffprobe..."
if has_command ffprobe; then
    check_ok "ffprobe is installed"
else
    check_warn "ffprobe is not installed (bundled with ffmpeg)"
    log_blank
    printf '  Note: ffprobe is usually bundled with ffmpeg.\n'
    printf '  If ffmpeg is installed, try reinstalling it.\n'
    log_blank
fi

# -----------------------------------------------------------------------------
# Check 6: libsndfile is available (for soundfile backend)
# -----------------------------------------------------------------------------
log_step "Checking libsndfile (audio backend)..."
LIBSNDFILE_OK=0
case "${OS_TYPE}" in
    macos)
        if brew list libsndfile &>/dev/null 2>&1; then
            LIBSNDFILE_OK=1
        fi
        ;;
    linux|wsl)
        case "${PKG_MANAGER}" in
            apt)
                if dpkg -s libsndfile1 &>/dev/null 2>&1; then
                    LIBSNDFILE_OK=1
                fi
                ;;
            dnf|yum|zypper)
                if rpm -q libsndfile &>/dev/null 2>&1; then
                    LIBSNDFILE_OK=1
                fi
                ;;
            pacman)
                if pacman -Q libsndfile &>/dev/null 2>&1; then
                    LIBSNDFILE_OK=1
                fi
                ;;
            apk)
                if apk info -e libsndfile &>/dev/null 2>&1; then
                    LIBSNDFILE_OK=1
                fi
                ;;
            *)
                # Cannot check, assume it might be there
                LIBSNDFILE_OK=1
                check_warn "Cannot verify libsndfile for ${PKG_MANAGER}"
                ;;
        esac
        ;;
    windows)
        # On Windows, libsndfile is bundled with Python soundfile
        LIBSNDFILE_OK=1
        ;;
esac

if [[ "${LIBSNDFILE_OK}" -eq 1 ]]; then
    check_ok "libsndfile is available"
else
    check_warn "libsndfile may not be installed"
    log_blank
    printf '  Note: libsndfile is needed for the soundfile audio backend.\n'
    printf '  Install with: ./scripts/install-ffmpeg.sh\n'
    log_blank
fi

# -----------------------------------------------------------------------------
# Check 7: Python soundfile module works
# -----------------------------------------------------------------------------
log_step "Checking soundfile Python module..."
if uv run python -c "import soundfile" 2>/dev/null; then
    check_ok "soundfile Python module is importable"
else
    check_warn "soundfile Python module cannot be imported"
    log_blank
    printf '  Note: soundfile is required for the audio backend.\n'
    printf '  It should be installed automatically with scribbulus.\n'
    printf '  Try: uv pip install soundfile\n'
    log_blank
fi

# -----------------------------------------------------------------------------
# Check 8: torchaudio backend
# -----------------------------------------------------------------------------
log_step "Checking torchaudio backend..."
BACKEND_OUTPUT=$(uv run python -c "
import torchaudio
backends = torchaudio.list_audio_backends()
print(','.join(backends))
" 2>/dev/null || echo "")

if [[ -n "${BACKEND_OUTPUT}" ]]; then
    if [[ "${BACKEND_OUTPUT}" == *"soundfile"* ]]; then
        check_ok "torchaudio has soundfile backend: ${BACKEND_OUTPUT}"
    elif [[ "${BACKEND_OUTPUT}" == *"sox_io"* ]]; then
        check_ok "torchaudio has sox_io backend: ${BACKEND_OUTPUT}"
    else
        check_warn "torchaudio backends: ${BACKEND_OUTPUT} (soundfile preferred)"
    fi
else
    check_warn "Could not determine torchaudio backends"
fi

# -----------------------------------------------------------------------------
# Check 9: HuggingFace token for diarization
# -----------------------------------------------------------------------------
log_step "Checking HuggingFace token (for diarization)..."
if [[ -n "${HF_TOKEN:-}" ]]; then
    # Mask the token for display
    TOKEN_PREVIEW="${HF_TOKEN:0:8}..."
    check_ok "HF_TOKEN is set: ${TOKEN_PREVIEW}"
else
    check_warn "HF_TOKEN is not set"
    log_blank
    printf '  Note: HF_TOKEN is required for speaker diarization.\n'
    printf '  Get a token from: https://huggingface.co/settings/tokens\n'
    printf '  Accept model terms at: https://huggingface.co/pyannote/speaker-diarization-3.1\n'
    printf '  Set with: export HF_TOKEN=your_token_here\n'
    log_blank
fi

# =============================================================================
# Summary
# =============================================================================

log_blank
log_success "========================================="
if [[ "${ISSUES_FOUND}" -eq 0 ]]; then
    log_success "All checks passed!"
    log_success "========================================="
    log_blank
    printf 'Scribbulus is ready to use.\n'
    log_blank
    printf 'Quick start:\n'
    printf '  scribbulus transcribe video.mp4 -o transcript.txt\n'
    log_blank
    exit 0
else
    log_error "${ISSUES_FOUND} issue(s) found"
    log_success "========================================="
    log_blank
    printf 'Please address the issues above and run this script again.\n'
    log_blank
    exit 1
fi
