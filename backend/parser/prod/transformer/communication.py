"""
Communication module for the Transformer domain.

This reuses the communication infrastructure from the extractor domain.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to access extractor
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Import from extractor directory
from extractor.communication import StatusReporter, NullStatusReporter

# Re-export for local use
__all__ = ['StatusReporter', 'NullStatusReporter']