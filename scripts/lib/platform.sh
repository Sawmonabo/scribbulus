#!/bin/bash
# platform.sh - Cross-platform detection helper for Scribbulus
#
# Source this at the start of installer scripts:
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   source "${SCRIPT_DIR}/lib/platform.sh"
#
# Exported variables:
#   OS_TYPE          - "linux" | "macos" | "windows" | "wsl" | "unknown"
#   OS_FAMILY        - "unix" | "windows"
#   PKG_MANAGER      - "apt" | "brew" | "dnf" | "pacman" | "zypper" | "apk" |
#                      "winget" | "choco" | "scoop" | "unknown"
#   IS_WINDOWS_SHELL - "1" | "0"
#   HAS_SUDO         - "1" | "0"
#   PLATFORM_SUPPORT - "full" | "best-effort" | "unsupported"
#
# Functions:
#   platform_info     - Print platform detection results
#   platform_require  - Assert platform requirements
#   platform_warn     - Warn about best-effort support
#   run_privileged    - Run command with sudo if needed
#   pkg_install       - Install package using detected package manager

# Prevent multiple sourcing
if [[ -n "${_PLATFORM_SH_LOADED:-}" ]]; then
    return 0
fi
readonly _PLATFORM_SH_LOADED=1

# =============================================================================
# OS Detection
# =============================================================================

_detect_os_type() {
    local uname_out
    uname_out="$(uname -s)"

    case "${uname_out}" in
        Linux*)
            # Check for WSL
            if grep -qEi "(Microsoft|WSL)" /proc/version 2>/dev/null; then
                echo "wsl"
            else
                echo "linux"
            fi
            ;;
        Darwin*)
            echo "macos"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            echo "windows"
            ;;
        *)
            # Fallback to $OSTYPE for edge cases
            case "${OSTYPE:-}" in
                linux*)   echo "linux" ;;
                darwin*)  echo "macos" ;;
                cygwin*|msys*|mingw*) echo "windows" ;;
                *)        echo "unknown" ;;
            esac
            ;;
    esac
}

_detect_os_family() {
    case "${OS_TYPE}" in
        linux|macos|wsl) echo "unix" ;;
        windows) echo "windows" ;;
        *) echo "unknown" ;;
    esac
}

_is_windows_shell() {
    local uname_out
    uname_out="$(uname -s)"
    case "${uname_out}" in
        CYGWIN*|MINGW*|MSYS*) echo "1" ;;
        *) echo "0" ;;
    esac
}

_has_sudo() {
    if [[ "${OS_TYPE}" == "windows" ]]; then
        echo "0"
        return
    fi

    if [[ "$(id -u)" -eq 0 ]]; then
        echo "1"  # Running as root
    elif command -v sudo &>/dev/null; then
        echo "1"
    else
        echo "0"
    fi
}

# =============================================================================
# Package Manager Detection
# =============================================================================

_detect_pkg_manager() {
    case "${OS_TYPE}" in
        macos)
            if command -v brew &>/dev/null; then
                echo "brew"
            else
                echo "unknown"
            fi
            ;;
        linux|wsl)
            if command -v apt &>/dev/null; then
                echo "apt"
            elif command -v dnf &>/dev/null; then
                echo "dnf"
            elif command -v yum &>/dev/null; then
                echo "yum"
            elif command -v pacman &>/dev/null; then
                echo "pacman"
            elif command -v zypper &>/dev/null; then
                echo "zypper"
            elif command -v apk &>/dev/null; then
                echo "apk"
            else
                echo "unknown"
            fi
            ;;
        windows)
            # Priority: winget > chocolatey > scoop
            if command -v winget &>/dev/null; then
                echo "winget"
            elif command -v choco &>/dev/null; then
                echo "choco"
            elif command -v scoop &>/dev/null; then
                echo "scoop"
            else
                echo "unknown"
            fi
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# =============================================================================
# Platform Support Level
# =============================================================================

_detect_platform_support() {
    case "${OS_TYPE}" in
        linux|macos|wsl)
            echo "full"
            ;;
        windows)
            # Windows with a package manager gets full support
            if [[ "${PKG_MANAGER}" != "unknown" ]]; then
                echo "full"
            else
                echo "best-effort"
            fi
            ;;
        *)
            echo "unsupported"
            ;;
    esac
}

# =============================================================================
# Export Variables
# =============================================================================

OS_TYPE="$(_detect_os_type)"
readonly OS_TYPE
export OS_TYPE

OS_FAMILY="$(_detect_os_family)"
readonly OS_FAMILY
export OS_FAMILY

IS_WINDOWS_SHELL="$(_is_windows_shell)"
readonly IS_WINDOWS_SHELL
export IS_WINDOWS_SHELL

HAS_SUDO="$(_has_sudo)"
readonly HAS_SUDO
export HAS_SUDO

PKG_MANAGER="$(_detect_pkg_manager)"
readonly PKG_MANAGER
export PKG_MANAGER

PLATFORM_SUPPORT="$(_detect_platform_support)"
readonly PLATFORM_SUPPORT
export PLATFORM_SUPPORT

# =============================================================================
# Helper Functions
# =============================================================================

# Print platform info (for debugging)
platform_info() {
    cat <<EOF
OS_TYPE:          ${OS_TYPE}
OS_FAMILY:        ${OS_FAMILY}
PKG_MANAGER:      ${PKG_MANAGER}
IS_WINDOWS_SHELL: ${IS_WINDOWS_SHELL}
HAS_SUDO:         ${HAS_SUDO}
PLATFORM_SUPPORT: ${PLATFORM_SUPPORT}
EOF
}

# Assert platform is supported
# Usage: platform_require [full|best-effort]
platform_require() {
    local required_level="${1:-full}"

    case "${required_level}" in
        full)
            if [[ "${PLATFORM_SUPPORT}" != "full" ]]; then
                printf 'Error: This script requires full platform support.\n' >&2
                printf 'Current platform: %s (%s support)\n' "${OS_TYPE}" "${PLATFORM_SUPPORT}" >&2
                return 1
            fi
            ;;
        best-effort)
            if [[ "${PLATFORM_SUPPORT}" == "unsupported" ]]; then
                printf 'Error: This platform is unsupported.\n' >&2
                printf 'Current platform: %s\n' "${OS_TYPE}" >&2
                return 1
            fi
            ;;
    esac
    return 0
}

# Warn about best-effort support
platform_warn() {
    if [[ "${PLATFORM_SUPPORT}" == "best-effort" ]]; then
        printf 'Warning: %s is a best-effort platform. Some features may not work.\n' "${OS_TYPE}" >&2
    fi
}

# Run command with sudo if available and needed
# Usage: run_privileged apt install -y ffmpeg
run_privileged() {
    if [[ "$(id -u)" -eq 0 ]]; then
        "$@"
    elif [[ "${HAS_SUDO}" == "1" ]]; then
        sudo "$@"
    else
        printf 'Error: This command requires root privileges but sudo is not available.\n' >&2
        return 1
    fi
}

# Install package using detected package manager
# Usage: pkg_install ffmpeg
# Returns: 0 on success, 1 on failure, 2 if no package manager available
pkg_install() {
    local package="$1"

    case "${PKG_MANAGER}" in
        apt)
            run_privileged apt update
            run_privileged apt install -y "${package}"
            ;;
        dnf)
            run_privileged dnf install -y "${package}"
            ;;
        yum)
            run_privileged yum install -y "${package}"
            ;;
        pacman)
            run_privileged pacman -S --noconfirm "${package}"
            ;;
        zypper)
            run_privileged zypper install -y "${package}"
            ;;
        apk)
            run_privileged apk add "${package}"
            ;;
        brew)
            brew install "${package}"
            ;;
        winget)
            winget install --silent --accept-package-agreements --accept-source-agreements "${package}"
            ;;
        choco)
            choco install -y "${package}"
            ;;
        scoop)
            scoop install "${package}"
            ;;
        *)
            printf 'Error: No supported package manager found.\n' >&2
            printf 'Please install %s manually.\n' "${package}" >&2
            return 2
            ;;
    esac
}

# Get the ffmpeg package name for the current platform
# Some package managers use different names
get_ffmpeg_package() {
    case "${PKG_MANAGER}" in
        winget)
            echo "Gyan.FFmpeg"
            ;;
        choco)
            echo "ffmpeg"
            ;;
        scoop)
            echo "ffmpeg"
            ;;
        *)
            echo "ffmpeg"
            ;;
    esac
}
