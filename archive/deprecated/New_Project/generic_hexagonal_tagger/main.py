#!/usr/bin/env python3
"""
Main entry point for the Generic Hexagonal Architecture Tagging System.
This script provides a simple command-line interface to run the tagging system.
"""

import sys
from pathlib import Path

# Add the parent directory to the Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generic_hexagonal_tagger.interfaces.cli import cli

if __name__ == "__main__":
    cli()
