# Python Debug Tool - Development Makefile

.PHONY: help install serve test test-cov format lint check clean

# Default target
help:
	@echo "Python Debug Tool - Development Commands"
	@echo "========================================"
	@echo ""
	@echo "Setup:"
	@echo "  install     Install/update dependencies"
	@echo "  setup       Initial project setup (venv + deps)"
	@echo ""
	@echo "Development:"
	@echo "  serve       Start development server"
	@echo "  test        Run tests"
	@echo "  test-cov    Run tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  format      Format code (black + isort)"
	@echo "  lint        Run linting (flake8 + mypy)"
	@echo "  check       Run all checks (format + lint + test)"
	@echo ""
	@echo "Utilities:"
	@echo "  clean       Clean up generated files"
	@echo "  status      Show project status"

# Setup commands
setup:
	@echo "🚀 Setting up Python Debug Tool development environment..."
	python3 -m venv venv
	@echo "📦 Installing dependencies..."
	./scripts/dev.py install
	@echo "✅ Setup complete! Run 'make serve' to start the development server."

install:
	@./scripts/dev.py install

# Development commands
serve:
	@./scripts/dev.py serve

test:
	@./scripts/dev.py test

test-cov:
	@./scripts/dev.py test-cov

# Code quality commands
format:
	@./scripts/dev.py format

lint:
	@./scripts/dev.py lint

check:
	@./scripts/dev.py check

# Utility commands
clean:
	@./scripts/dev.py clean

status:
	@echo "Python Debug Tool - Project Status"
	@echo "=================================="
	@echo ""
	@echo "Virtual Environment:"
	@if [ -d "venv" ]; then \
		echo "  ✅ Virtual environment exists"; \
		if [ -f "venv/bin/python" ]; then \
			echo "  🐍 Python version: $$(venv/bin/python --version)"; \
		fi; \
	else \
		echo "  ❌ Virtual environment not found"; \
	fi
	@echo ""
	@echo "Dependencies:"
	@if [ -f "venv/bin/pip" ]; then \
		echo "  📦 Installed packages: $$(venv/bin/pip list | wc -l) packages"; \
	else \
		echo "  ❌ pip not available"; \
	fi
	@echo ""
	@echo "Project Structure:"
	@echo "  📁 Backend modules: $$(find backend -name "*.py" | wc -l) files"
	@echo "  🧪 Test files: $$(find tests -name "*.py" | wc -l) files"
	@echo ""
	@echo "Git Status:"
	@if [ -d ".git" ]; then \
		echo "  📋 Current branch: $$(git branch --show-current)"; \
		echo "  📝 Uncommitted changes: $$(git status --porcelain | wc -l) files"; \
	else \
		echo "  ❌ Not a git repository"; \
	fi
