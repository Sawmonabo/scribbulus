#!/bin/bash
# install-ffmpeg.sh - Cross-platform FFmpeg installer for Scribbulus
#
# Usage: ./scripts/install-ffmpeg.sh
#
# Supports:
#   - macOS (via Homebrew)
#   - Ubuntu/Debian (via apt)
#   - Fedora (via dnf)
#   - Arch Linux (via pacman)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== FFmpeg Installer for Scribbulus ===${NC}"
echo ""

# Check if ffmpeg is already installed
if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}FFmpeg is already installed:${NC}"
    ffmpeg -version | head -1
    echo ""
    read -p "Do you want to reinstall/upgrade? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping installation."
        exit 0
    fi
fi

# Detect OS
OS="$(uname -s)"
echo -e "${YELLOW}Detected OS: ${OS}${NC}"

case "$OS" in
    Darwin)
        echo "Platform: macOS"
        echo ""

        # Check for Homebrew
        if ! command -v brew &> /dev/null; then
            echo -e "${RED}Error: Homebrew not found${NC}"
            echo ""
            echo "Homebrew is required to install FFmpeg on macOS."
            echo "Install Homebrew first:"
            echo ""
            echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            echo ""
            exit 1
        fi

        echo "Installing FFmpeg via Homebrew..."
        brew install ffmpeg
        ;;

    Linux)
        echo "Platform: Linux"
        echo ""

        # Detect package manager and install
        if command -v apt &> /dev/null; then
            echo "Package manager: apt (Debian/Ubuntu)"
            echo "Installing FFmpeg..."
            sudo apt update
            sudo apt install -y ffmpeg

        elif command -v dnf &> /dev/null; then
            echo "Package manager: dnf (Fedora)"
            echo "Installing FFmpeg..."
            sudo dnf install -y ffmpeg

        elif command -v pacman &> /dev/null; then
            echo "Package manager: pacman (Arch Linux)"
            echo "Installing FFmpeg..."
            sudo pacman -S --noconfirm ffmpeg

        elif command -v zypper &> /dev/null; then
            echo "Package manager: zypper (openSUSE)"
            echo "Installing FFmpeg..."
            sudo zypper install -y ffmpeg

        elif command -v apk &> /dev/null; then
            echo "Package manager: apk (Alpine)"
            echo "Installing FFmpeg..."
            sudo apk add ffmpeg

        else
            echo -e "${RED}Error: No supported package manager found${NC}"
            echo ""
            echo "Please install FFmpeg manually for your distribution."
            echo "Visit: https://ffmpeg.org/download.html"
            exit 1
        fi
        ;;

    CYGWIN*|MINGW*|MSYS*)
        echo "Platform: Windows (via Cygwin/MinGW/MSYS)"
        echo ""
        echo -e "${YELLOW}Note: Windows support is best-effort.${NC}"
        echo ""
        echo "Recommended installation methods for Windows:"
        echo ""
        echo "1. Using Chocolatey:"
        echo "   choco install ffmpeg"
        echo ""
        echo "2. Using Scoop:"
        echo "   scoop install ffmpeg"
        echo ""
        echo "3. Manual download:"
        echo "   https://ffmpeg.org/download.html#build-windows"
        echo ""
        exit 1
        ;;

    *)
        echo -e "${RED}Error: Unsupported operating system: ${OS}${NC}"
        echo ""
        echo "Please install FFmpeg manually."
        echo "Visit: https://ffmpeg.org/download.html"
        exit 1
        ;;
esac

# Verify installation
echo ""
echo -e "${GREEN}Verifying installation...${NC}"

if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}FFmpeg installed successfully!${NC}"
    echo ""
    ffmpeg -version | head -3
    echo ""

    # Check for ffprobe
    if command -v ffprobe &> /dev/null; then
        echo -e "${GREEN}ffprobe is also available.${NC}"
    else
        echo -e "${YELLOW}Warning: ffprobe not found. Some features may not work.${NC}"
    fi
else
    echo -e "${RED}Error: FFmpeg installation failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== Installation Complete ===${NC}"
echo ""
echo "You can now use Scribbulus for audio/video transcription."
echo ""
echo "Quick start:"
echo "  scribbulus-transcribe video.mp4 -o transcript.txt"
