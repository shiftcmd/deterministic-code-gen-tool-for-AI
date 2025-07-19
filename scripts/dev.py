#!/usr/bin/env python3
"""
Development utility script for the Python Debug Tool.

This script provides common development tasks like running the server,
running tests, formatting code, etc.
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python"
VENV_ACTIVATE = PROJECT_ROOT / "venv" / "bin" / "activate"


def run_command(cmd: list[str], cwd: Path = PROJECT_ROOT) -> int:
    """Run a command with the virtual environment activated."""
    if not VENV_PYTHON.exists():
        print(
            "❌ Virtual environment not found. Please run 'python3 -m venv venv' first."
        )
        return 1

    # Activate venv and run command using bash
    full_cmd = f"source {VENV_ACTIVATE} && {' '.join(cmd)}"
    result = subprocess.run(full_cmd, shell=True, cwd=cwd, executable="/bin/bash")
    return result.returncode


def serve():
    """Start the development server."""
    print("🚀 Starting development server...")
    return run_command(
        [
            "uvicorn",
            "backend.main:app",
            "--reload",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ]
    )


def test(args: list[str] = None):
    """Run tests."""
    print("🧪 Running tests...")
    cmd = ["python", "-m", "pytest", "tests/", "-v"]
    if args:
        cmd.extend(args)
    return run_command(cmd)


def test_coverage():
    """Run tests with coverage report."""
    print("📊 Running tests with coverage...")
    return run_command(
        [
            "python",
            "-m",
            "pytest",
            "tests/",
            "--cov=backend",
            "--cov-report=html",
            "--cov-report=term",
        ]
    )


def format_code():
    """Format code using black and isort."""
    print("🎨 Formatting code...")

    # Run black
    print("  Running black...")
    black_result = run_command(["black", "backend/", "tests/", "scripts/"])

    # Run isort
    print("  Running isort...")
    isort_result = run_command(["isort", "backend/", "tests/", "scripts/"])

    return max(black_result, isort_result)


def lint():
    """Run linting checks."""
    print("🔍 Running linting checks...")

    # Run flake8
    print("  Running flake8...")
    flake8_result = run_command(["flake8", "backend/", "tests/"])

    # Run mypy
    print("  Running mypy...")
    mypy_result = run_command(["mypy", "backend/"])

    return max(flake8_result, mypy_result)


def check():
    """Run all checks (format, lint, test)."""
    print("✅ Running all checks...")

    format_result = format_code()
    lint_result = lint()
    test_result = test()

    if format_result == 0 and lint_result == 0 and test_result == 0:
        print("🎉 All checks passed!")
        return 0
    else:
        print("❌ Some checks failed.")
        return 1


def install():
    """Install/update dependencies."""
    print("📦 Installing dependencies...")

    # Upgrade pip first
    pip_result = run_command(["python", "-m", "pip", "install", "--upgrade", "pip"])
    if pip_result != 0:
        return pip_result

    # Install requirements
    req_result = run_command(["pip", "install", "-r", "requirements-dev.txt"])
    return req_result


def clean():
    """Clean up generated files."""
    print("🧹 Cleaning up...")

    # Remove Python cache files
    cache_result = run_command(
        [
            "find",
            ".",
            "-type",
            "d",
            "-name",
            "__pycache__",
            "-exec",
            "rm",
            "-rf",
            "{}",
            "+",
        ]
    )

    # Remove pytest cache
    pytest_cache = PROJECT_ROOT / ".pytest_cache"
    if pytest_cache.exists():
        run_command(["rm", "-rf", str(pytest_cache)])

    # Remove coverage files
    coverage_files = [".coverage", "htmlcov"]
    for file in coverage_files:
        file_path = PROJECT_ROOT / file
        if file_path.exists():
            run_command(["rm", "-rf", str(file_path)])

    print("✨ Cleanup complete!")
    return cache_result


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Python Debug Tool development utilities"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Serve command
    subparsers.add_parser("serve", help="Start the development server")

    # Test commands
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("args", nargs="*", help="Additional pytest arguments")

    subparsers.add_parser("test-cov", help="Run tests with coverage")

    # Code quality commands
    subparsers.add_parser("format", help="Format code with black and isort")
    subparsers.add_parser("lint", help="Run linting checks")
    subparsers.add_parser("check", help="Run all checks (format, lint, test)")

    # Utility commands
    subparsers.add_parser("install", help="Install/update dependencies")
    subparsers.add_parser("clean", help="Clean up generated files")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute the command
    if args.command == "serve":
        return serve()
    elif args.command == "test":
        return test(args.args if hasattr(args, "args") else None)
    elif args.command == "test-cov":
        return test_coverage()
    elif args.command == "format":
        return format_code()
    elif args.command == "lint":
        return lint()
    elif args.command == "check":
        return check()
    elif args.command == "install":
        return install()
    elif args.command == "clean":
        return clean()
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
