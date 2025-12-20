#!/bin/bash
# install-ffmpeg.sh - Cross-platform FFmpeg installer for Scribbulus
#
# Usage: ./scripts/install-ffmpeg.sh [OPTIONS]
#
# Options:
#   -f, --force    Force reinstall even if ffmpeg is present
#   -q, --quiet    Suppress non-error output
#   -h, --help     Show this help message
#
# Supports:
#   - macOS (via Homebrew)
#   - Ubuntu/Debian (via apt)
#   - Fedora (via dnf)
#   - Arch Linux (via pacman)
#   - openSUSE (via zypper)
#   - Alpine (via apk)
#
# Exit codes:
#   0  Success (installed or already present)
#   1  General error
#   2  Missing dependency (e.g., Homebrew)

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
    sed -n '2,22p' "$0" | sed 's/^# //' | sed 's/^#//'
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

log_info "=== FFmpeg Installer for Scribbulus ==="
if [[ "${QUIET}" -eq 0 ]]; then
    printf '\n'
fi

# Check if ffmpeg is already installed
if command -v ffmpeg &> /dev/null; then
    log_info "FFmpeg is already installed:"
    if [[ "${QUIET}" -eq 0 ]]; then
        ffmpeg -version | head -1
    fi
    if [[ "${FORCE}" -eq 0 ]]; then
        log_info "Use --force to reinstall."
        exit 0
    fi
    log_warn "Force reinstall requested..."
fi

# Detect OS
os_name="$(uname -s)"
log_warn "Detected OS: ${os_name}"

case "${os_name}" in
    Darwin)
        printf 'Platform: macOS\n'
        printf '\n'

        # Check for Homebrew
        if ! command -v brew &> /dev/null; then
            log_error "Error: Homebrew not found"
            printf '\n'
            printf 'Homebrew is required to install FFmpeg on macOS.\n'
            printf 'Install Homebrew first:\n'
            printf '\n'
            # shellcheck disable=SC2016 # Intentionally unexpanded - showing literal command
            printf '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"\n'
            printf '\n'
            exit 2
        fi

        printf 'Installing FFmpeg via Homebrew...\n'
        brew install ffmpeg
        ;;

    Linux)
        printf 'Platform: Linux\n'
        printf '\n'

        # Detect package manager and install
        if command -v apt &> /dev/null; then
            printf 'Package manager: apt (Debian/Ubuntu)\n'
            printf 'Installing FFmpeg...\n'
            sudo apt update
            sudo apt install -y ffmpeg

        elif command -v dnf &> /dev/null; then
            printf 'Package manager: dnf (Fedora)\n'
            printf 'Installing FFmpeg...\n'
            sudo dnf install -y ffmpeg

        elif command -v pacman &> /dev/null; then
            printf 'Package manager: pacman (Arch Linux)\n'
            printf 'Installing FFmpeg...\n'
            sudo pacman -S --noconfirm ffmpeg

        elif command -v zypper &> /dev/null; then
            printf 'Package manager: zypper (openSUSE)\n'
            printf 'Installing FFmpeg...\n'
            sudo zypper install -y ffmpeg

        elif command -v apk &> /dev/null; then
            printf 'Package manager: apk (Alpine)\n'
            printf 'Installing FFmpeg...\n'
            sudo apk add ffmpeg

        else
            log_error "Error: No supported package manager found"
            printf '\n'
            printf 'Please install FFmpeg manually for your distribution.\n'
            printf 'Visit: https://ffmpeg.org/download.html\n'
            exit 1
        fi
        ;;

    CYGWIN*|MINGW*|MSYS*)
        printf 'Platform: Windows (via Cygwin/MinGW/MSYS)\n'
        printf '\n'
        log_warn "Note: Windows support is best-effort."
        printf '\n'
        printf 'Recommended installation methods for Windows:\n'
        printf '\n'
        printf '1. Using Chocolatey:\n'
        printf '   choco install ffmpeg\n'
        printf '\n'
        printf '2. Using Scoop:\n'
        printf '   scoop install ffmpeg\n'
        printf '\n'
        printf '3. Manual download:\n'
        printf '   https://ffmpeg.org/download.html#build-windows\n'
        printf '\n'
        exit 1
        ;;

    *)
        log_error "Error: Unsupported operating system: ${os_name}"
        printf '\n'
        printf 'Please install FFmpeg manually.\n'
        printf 'Visit: https://ffmpeg.org/download.html\n'
        exit 1
        ;;
esac

# Verify installation
printf '\n'
log_info "Verifying installation..."

if command -v ffmpeg &> /dev/null; then
    log_info "FFmpeg installed successfully!"
    printf '\n'
    ffmpeg -version | head -3
    printf '\n'

    # Check for ffprobe
    if command -v ffprobe &> /dev/null; then
        log_info "ffprobe is also available."
    else
        log_warn "Warning: ffprobe not found. Some features may not work."
    fi
else
    log_error "Error: FFmpeg installation failed"
    exit 1
fi

printf '\n'
log_info "=== Installation Complete ==="
printf '\n'
printf 'You can now use Scribbulus for audio/video transcription.\n'
printf '\n'
printf 'Quick start:\n'
printf '  scribbulus transcribe video.mp4 -o transcript.txt\n'
