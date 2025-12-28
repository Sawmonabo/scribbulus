#!/bin/bash
# install-ffmpeg.sh - Cross-platform FFmpeg installer for Scribbulus
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
install-ffmpeg.sh - Cross-platform FFmpeg installer for Scribbulus

Usage: ./scripts/install-ffmpeg.sh [OPTIONS]

Options:
  -f, --force    Force reinstall even if ffmpeg is present
  -q, --quiet    Suppress non-error output
  -h, --help     Show this help message

Supports:
  - macOS (via Homebrew)
  - Ubuntu/Debian (via apt)
  - Fedora (via dnf)
  - Arch Linux (via pacman)
  - openSUSE (via zypper)
  - Alpine (via apk)
  - Windows (via winget, Chocolatey, or Scoop)

Exit codes:
  0  Success (installed or already present)
  1  General error
  2  Missing dependency (e.g., Homebrew, package manager)
EOF
}

# Parse arguments (FORCE and QUIET exported by args.sh)
parse_args "$@"

log_success "=== FFmpeg Installer for Scribbulus ==="
log_blank

# Show detected platform info
log_step "Detected: ${OS_TYPE} with ${PKG_MANAGER} package manager"
log_blank

# =============================================================================
# Dependency checking helpers
# =============================================================================

# Check if libsndfile is installed (platform-specific)
is_libsndfile_installed() {
    case "${OS_TYPE}" in
        macos)
            brew list libsndfile &>/dev/null 2>&1
            ;;
        linux|wsl)
            case "${PKG_MANAGER}" in
                apt)        dpkg -s libsndfile1 &>/dev/null 2>&1 ;;
                dnf|yum|zypper) rpm -q libsndfile &>/dev/null 2>&1 ;;
                pacman)     pacman -Q libsndfile &>/dev/null 2>&1 ;;
                apk)        apk info -e libsndfile &>/dev/null 2>&1 ;;
                *)          return 1 ;;
            esac
            ;;
        windows)
            return 0  # Bundled with Python soundfile package
            ;;
        *)
            return 1
            ;;
    esac
}

# Check if all required dependencies are installed
all_deps_installed() {
    has_command ffmpeg && has_command ffprobe && is_libsndfile_installed
}

# Early exit if all dependencies present (unless --force)
if all_deps_installed; then
    log_success "All dependencies are already installed:"
    if [[ "${QUIET}" -eq 0 ]]; then
        log_info "  ffmpeg:    $(ffmpeg -version 2>&1 | head -1)"
        log_info "  ffprobe:   available"
        log_info "  libsndfile: available"
    fi
    if [[ "${FORCE}" -eq 0 ]]; then
        log_blank
        log_info "Use --force to reinstall."
        exit 0
    fi
    log_warn "Force reinstall requested..."
fi
log_blank

# =============================================================================
# Platform-specific installation
# =============================================================================

case "${OS_TYPE}" in
    macos)
        if [[ "${PKG_MANAGER}" != "brew" ]]; then
            log_error "Homebrew not found"
            log_blank
            printf 'Homebrew is required to install FFmpeg on macOS.\n'
            printf 'Install Homebrew first:\n'
            log_blank
            # shellcheck disable=SC2016 # Intentionally unexpanded - showing literal command
            printf '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"\n'
            log_blank
            exit 2
        fi

        log_step "Installing FFmpeg via Homebrew..."
        brew install ffmpeg
        ;;

    linux|wsl)
        case "${PKG_MANAGER}" in
            apt)
                log_step "Installing FFmpeg via apt..."
                run_privileged apt update
                run_privileged apt install -y ffmpeg
                ;;
            dnf)
                log_step "Installing FFmpeg via dnf..."
                run_privileged dnf install -y ffmpeg
                ;;
            yum)
                log_step "Installing FFmpeg via yum..."
                run_privileged yum install -y ffmpeg
                ;;
            pacman)
                log_step "Installing FFmpeg via pacman..."
                run_privileged pacman -S --noconfirm ffmpeg
                ;;
            zypper)
                log_step "Installing FFmpeg via zypper..."
                run_privileged zypper install -y ffmpeg
                ;;
            apk)
                log_step "Installing FFmpeg via apk..."
                run_privileged apk add ffmpeg
                ;;
            *)
                log_error "No supported package manager found"
                log_blank
                printf 'Please install FFmpeg manually for your distribution.\n'
                printf 'Visit: https://ffmpeg.org/download.html\n'
                exit 2
                ;;
        esac
        ;;

    windows)
        case "${PKG_MANAGER}" in
            winget)
                log_step "Installing FFmpeg via winget..."
                winget install --silent --accept-package-agreements --accept-source-agreements Gyan.FFmpeg
                ;;
            choco)
                log_step "Installing FFmpeg via Chocolatey..."
                choco install -y ffmpeg
                ;;
            scoop)
                log_step "Installing FFmpeg via Scoop..."
                scoop install ffmpeg
                ;;
            *)
                log_warn "No Windows package manager found (winget, choco, scoop)"
                log_blank
                printf 'Recommended installation methods for Windows:\n'
                log_blank
                printf '1. Using winget (Windows Package Manager):\n'
                printf '   winget install Gyan.FFmpeg\n'
                log_blank
                printf '2. Using Chocolatey:\n'
                printf '   choco install ffmpeg\n'
                log_blank
                printf '3. Using Scoop:\n'
                printf '   scoop install ffmpeg\n'
                log_blank
                printf '4. Manual download:\n'
                printf '   https://ffmpeg.org/download.html#build-windows\n'
                log_blank
                exit 2
                ;;
        esac
        ;;

    *)
        log_error "Unsupported operating system: ${OS_TYPE}"
        log_blank
        printf 'Please install FFmpeg manually.\n'
        printf 'Visit: https://ffmpeg.org/download.html\n'
        exit 1
        ;;
esac

# =============================================================================
# Install libsndfile (required for soundfile audio backend)
# =============================================================================

install_libsndfile() {
    # Skip if already installed (unless --force)
    if is_libsndfile_installed && [[ "${FORCE}" -eq 0 ]]; then
        log_info "libsndfile is already installed."
        return 0
    fi

    log_step "Installing libsndfile for audio backend..."
    case "${OS_TYPE}" in
        macos)
            brew install libsndfile
            ;;
        linux|wsl)
            case "${PKG_MANAGER}" in
                apt)        run_privileged apt install -y libsndfile1 ;;
                dnf|yum)    run_privileged "${PKG_MANAGER}" install -y libsndfile ;;
                pacman)     run_privileged pacman -S --noconfirm libsndfile ;;
                zypper)     run_privileged zypper install -y libsndfile ;;
                apk)        run_privileged apk add libsndfile ;;
                *)
                    log_warn "Cannot auto-install libsndfile for ${PKG_MANAGER}."
                    log_warn "Please install libsndfile manually for audio backend support."
                    return 1
                    ;;
            esac
            ;;
        windows)
            log_info "libsndfile will be bundled with Python soundfile package."
            ;;
    esac
}

# Install libsndfile after ffmpeg
install_libsndfile

# =============================================================================
# Verify installation
# =============================================================================

log_blank
log_step "Verifying installation..."

VERIFY_FAILED=0

if has_command ffmpeg; then
    log_success "ffmpeg: OK"
    if [[ "${QUIET}" -eq 0 ]]; then
        ffmpeg -version 2>&1 | head -1 | sed 's/^/    /'
    fi
else
    log_error "ffmpeg: FAILED"
    VERIFY_FAILED=1
fi

if has_command ffprobe; then
    log_success "ffprobe: OK"
else
    log_warn "ffprobe: MISSING (some features may not work)"
fi

if is_libsndfile_installed; then
    log_success "libsndfile: OK"
else
    log_warn "libsndfile: MISSING (audio backend may not work)"
fi

if [[ "${VERIFY_FAILED}" -eq 1 ]]; then
    log_blank
    log_error "Installation verification failed"
    exit 1
fi

log_blank
log_success "=== Installation Complete ==="
log_blank
printf 'You can now use Scribbulus for audio/video transcription.\n'
log_blank
printf 'Quick start:\n'
printf '  scribbulus transcribe video.mp4 -o transcript.txt\n'
