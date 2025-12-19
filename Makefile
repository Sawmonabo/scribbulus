# Scribbulus Makefile
# Cross-platform installation and development commands

# Detect OS
UNAME := $(shell uname -s)
ifeq ($(UNAME),Darwin)
    OS := macos
    BREW := $(shell command -v brew 2> /dev/null)
endif
ifeq ($(UNAME),Linux)
    OS := linux
    APT := $(shell command -v apt 2> /dev/null)
    DNF := $(shell command -v dnf 2> /dev/null)
    PACMAN := $(shell command -v pacman 2> /dev/null)
endif

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help install install-uv install-ffmpeg install-deps dev test lint format clean check-ffmpeg check-uv

# Default target
help:
	@echo "$(GREEN)Scribbulus - Media Transcription Tool$(NC)"
	@echo ""
	@echo "$(YELLOW)Usage:$(NC)"
	@echo "  make install       Install scribbulus and all dependencies"
	@echo "  make install-deps  Install system dependencies (ffmpeg)"
	@echo "  make dev           Install in development mode with dev dependencies"
	@echo "  make test          Run tests"
	@echo "  make lint          Run linter (ruff)"
	@echo "  make format        Auto-format code"
	@echo "  make clean         Clean build artifacts"
	@echo ""
	@echo "$(YELLOW)System Info:$(NC)"
	@echo "  Detected OS: $(OS)"
ifeq ($(OS),macos)
	@echo "  Package Manager: Homebrew"
else ifeq ($(OS),linux)
ifdef APT
	@echo "  Package Manager: apt (Debian/Ubuntu)"
else ifdef DNF
	@echo "  Package Manager: dnf (Fedora)"
else ifdef PACMAN
	@echo "  Package Manager: pacman (Arch)"
else
	@echo "  Package Manager: $(RED)Not detected$(NC)"
endif
endif

# Check if uv is installed
check-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo "$(RED)Error: uv is not installed$(NC)"; \
		echo "Run 'make install-uv' first or install manually:"; \
		echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 1; \
	}

# Check if ffmpeg is installed
check-ffmpeg:
	@command -v ffmpeg >/dev/null 2>&1 || { \
		echo "$(RED)Error: ffmpeg is not installed$(NC)"; \
		echo "Run 'make install-ffmpeg' first"; \
		exit 1; \
	}

# Install uv package manager
install-uv:
	@echo "$(GREEN)Checking for uv...$(NC)"
	@command -v uv >/dev/null 2>&1 && { \
		echo "$(GREEN)uv is already installed$(NC)"; \
		uv --version; \
	} || { \
		echo "$(YELLOW)Installing uv...$(NC)"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "$(GREEN)uv installed successfully$(NC)"; \
		echo "$(YELLOW)Note: You may need to restart your shell or run:$(NC)"; \
		echo '  source $$HOME/.local/bin/env'; \
	}

# Install ffmpeg
install-ffmpeg:
	@echo "$(GREEN)Installing ffmpeg...$(NC)"
ifeq ($(OS),macos)
ifndef BREW
	@echo "$(RED)Error: Homebrew not found$(NC)"
	@echo "Install Homebrew first: https://brew.sh"
	@exit 1
endif
	@echo "Installing ffmpeg via Homebrew..."
	@brew install ffmpeg
else ifeq ($(OS),linux)
ifdef APT
	@echo "Installing ffmpeg via apt..."
	@sudo apt update && sudo apt install -y ffmpeg
else ifdef DNF
	@echo "Installing ffmpeg via dnf..."
	@sudo dnf install -y ffmpeg
else ifdef PACMAN
	@echo "Installing ffmpeg via pacman..."
	@sudo pacman -S --noconfirm ffmpeg
else
	@echo "$(RED)Error: No supported package manager found$(NC)"
	@echo "Please install ffmpeg manually"
	@exit 1
endif
else
	@echo "$(RED)Error: Unsupported OS$(NC)"
	@exit 1
endif
	@echo "$(GREEN)FFmpeg installed successfully$(NC)"
	@ffmpeg -version | head -1

# Install system dependencies
install-deps: install-ffmpeg
	@echo "$(GREEN)System dependencies installed$(NC)"

# Full installation
install: install-uv
	@echo "$(GREEN)Checking for ffmpeg...$(NC)"
	@command -v ffmpeg >/dev/null 2>&1 || { \
		echo "$(YELLOW)FFmpeg not found. Installing...$(NC)"; \
		$(MAKE) install-ffmpeg; \
	}
	@echo "$(GREEN)Installing scribbulus...$(NC)"
	@uv sync
	@uv pip install -e .
	@echo ""
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)Installation complete!$(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo ""
	@echo "$(YELLOW)Quick start:$(NC)"
	@echo "  scribbulus-transcribe video.mp4 -o transcript.txt"
	@echo ""
	@echo "$(YELLOW)For speaker diarization, set your HuggingFace token:$(NC)"
	@echo "  export HF_TOKEN=your_token_here"
	@echo ""
	@echo "$(YELLOW)Get help:$(NC)"
	@echo "  scribbulus-transcribe --help"

# Development installation
dev: install-uv
	@echo "$(GREEN)Setting up development environment...$(NC)"
	@uv sync --all-extras
	@uv pip install -e .
	@echo "$(GREEN)Development environment ready$(NC)"
	@echo ""
	@echo "$(YELLOW)Available commands:$(NC)"
	@echo "  make test    - Run tests"
	@echo "  make lint    - Run linter"
	@echo "  make format  - Auto-format code"

# Run tests
test: check-uv
	@echo "$(GREEN)Running tests...$(NC)"
	@uv run pytest tests/ -v

# Run tests with coverage
test-cov: check-uv
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	@uv run pytest tests/ -v --cov=src/scribbulus --cov-report=html --cov-report=term

# Run linter
lint: check-uv
	@echo "$(GREEN)Running linter...$(NC)"
	@uv run ruff check src/ tests/
	@uv run ruff format --check src/ tests/
	@echo "$(GREEN)Running markdown linter...$(NC)"
	@npx markdownlint-cli "docs/**/*.md" "*.md" 2>/dev/null || echo "$(YELLOW)Note: Install markdownlint-cli for markdown linting$(NC)"

# Auto-format code
format: check-uv
	@echo "$(GREEN)Formatting code...$(NC)"
	@uv run ruff format src/ tests/
	@uv run ruff check --fix src/ tests/
	@echo "$(GREEN)Formatting markdown...$(NC)"
	@npx markdownlint-cli --fix "docs/**/*.md" "*.md" 2>/dev/null || true
	@echo "$(GREEN)Code formatted$(NC)"

# Type checking
typecheck: check-uv
	@echo "$(GREEN)Running type checker...$(NC)"
	@uv run mypy src/

# Clean build artifacts
clean:
	@echo "$(GREEN)Cleaning build artifacts...$(NC)"
	@rm -rf build/ dist/ *.egg-info/
	@rm -rf .cache/
	@rm -rf htmlcov/ .coverage coverage.xml
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete$(NC)"

# Deep clean (includes venv)
clean-all: clean
	@echo "$(YELLOW)Removing virtual environment...$(NC)"
	@rm -rf .venv/
	@echo "$(GREEN)Deep clean complete$(NC)"
