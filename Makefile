# Scribbulus Makefile
# Thin orchestration layer - complex logic lives in ./scripts/

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m

.PHONY: help install install-uv install-ffmpeg install-deps dev test test-cov \
        lint lint-ruff lint-shell format typecheck clean clean-all check-uv check-ffmpeg

help:
	@echo "$(GREEN)Scribbulus - Media Transcription Tool$(NC)"
	@echo ""
	@echo "$(YELLOW)Installation:$(NC)"
	@echo "  make install       Install scribbulus and all dependencies"
	@echo "  make install-deps  Install system dependencies (ffmpeg)"
	@echo "  make install-uv    Install uv package manager"
	@echo "  make dev           Install in development mode with dev dependencies"
	@echo ""
	@echo "$(YELLOW)Development:$(NC)"
	@echo "  make test          Run tests"
	@echo "  make test-cov      Run tests with coverage"
	@echo "  make lint          Run all linters (ruff, shellcheck, mypy)"
	@echo "  make lint-ruff     Run Python linter only (ruff)"
	@echo "  make lint-shell    Run shell script linter only (shellcheck)"
	@echo "  make format        Auto-format code"
	@echo "  make typecheck     Run type checker (mypy)"
	@echo ""
	@echo "$(YELLOW)Cleanup:$(NC)"
	@echo "  make clean         Clean build artifacts"
	@echo "  make clean-all     Clean all including virtual environment"

# =============================================================================
# Installation (delegated to scripts)
# =============================================================================

install:
	@./scripts/install.sh

install-uv:
	@./scripts/install.sh --uv

install-ffmpeg:
	@./scripts/install.sh --ffmpeg

install-deps:
	@./scripts/install.sh --deps

# =============================================================================
# Validation
# =============================================================================

check-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo "$(YELLOW)Error: uv is not installed$(NC)"; \
		echo "Run 'make install-uv' first"; \
		exit 1; \
	}

check-ffmpeg:
	@command -v ffmpeg >/dev/null 2>&1 || { \
		echo "$(YELLOW)Error: ffmpeg is not installed$(NC)"; \
		echo "Run 'make install-ffmpeg' first"; \
		exit 1; \
	}

# =============================================================================
# Development
# =============================================================================

dev: check-uv
	@echo "$(GREEN)Setting up development environment...$(NC)"
	@uv sync --all-extras
	@uv pip install -e .
	@echo "$(GREEN)Development environment ready$(NC)"

test: check-uv
	@echo "$(GREEN)Running tests...$(NC)"
	@uv run pytest tests/ -v

test-cov: check-uv
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	@uv run pytest tests/ -v --cov=src/scribbulus --cov-report=html --cov-report=term

lint: lint-ruff lint-shell typecheck

lint-ruff: check-uv
	@echo "$(GREEN)Running ruff linter...$(NC)"
	@uv run ruff check src/ tests/
	@uv run ruff format --check src/ tests/

lint-shell:
	@echo "$(GREEN)Running shell script linter...$(NC)"
	@shellcheck --severity=warning scripts/*.sh scripts/lib/*.sh
	@echo "$(GREEN)Shell scripts passed!$(NC)"

format: check-uv
	@echo "$(GREEN)Formatting code...$(NC)"
	@uv run ruff format src/ tests/
	@uv run ruff check --fix src/ tests/
	@echo "$(GREEN)Formatting markdown...$(NC)"
	@npx markdownlint-cli --fix "docs/**/*.md" "*.md" 2>/dev/null || true
	@echo "$(GREEN)Code formatted$(NC)"

typecheck: check-uv
	@echo "$(GREEN)Running type checker...$(NC)"
	@uv run mypy src/

# =============================================================================
# Cleanup
# =============================================================================

clean:
	@echo "$(GREEN)Cleaning build artifacts...$(NC)"
	@rm -rf build/ dist/ *.egg-info/
	@rm -rf .cache/
	@rm -rf htmlcov/ .coverage coverage.xml
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete$(NC)"

clean-all: clean
	@echo "$(YELLOW)Removing virtual environment...$(NC)"
	@rm -rf .venv/
	@echo "$(GREEN)Deep clean complete$(NC)"
