"""
Extractor domain for the AST parsing pipeline.

This package contains all components for extracting code structure
from Python source files.
"""

from .main import ExtractorMain
from .codebase_parser import CodebaseParser
from .module_parser import ModuleParser
from .ast_visitors import CombinedVisitor
from .models import ParsedModule, ParsedClass, ParsedFunction
from .serialization import Serializer
from .communication import StatusReporter

__all__ = [
    'ExtractorMain',
    'CodebaseParser',
    'ModuleParser',
    'CombinedVisitor',
    'ParsedModule',
    'ParsedClass',
    'ParsedFunction',
    'Serializer',
    'StatusReporter'
]