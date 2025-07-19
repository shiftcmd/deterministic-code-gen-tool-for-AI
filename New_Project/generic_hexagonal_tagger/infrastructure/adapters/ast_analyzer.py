"""
AST-based static code analyzer for the Generic Hexagonal Architecture Tagging System.

This module provides comprehensive static analysis capabilities using Python's AST module
to extract structural information, dependencies, and patterns from source code files.
"""

import ast
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4

from ...config.logging import get_logger
from ...core.domain.code_component import (
    CodeComponent,
    CodeMetrics,
    ComponentType,
    Relationship,
    RelationshipType,
)
from ...core.domain.tag import Tag, TagCategory, TagCollection, get_tag_registry

logger = get_logger(__name__)


class PythonASTVisitor(ast.NodeVisitor):
    """
    AST visitor for extracting code components and relationships from Python source code.

    Traverses the AST and builds a comprehensive model of the code structure,
    including classes, methods, functions, and their relationships.
    """

    def __init__(self, file_path: str, source_code: str) -> None:
        self.file_path = file_path
        self.source_code = source_code
        self.source_lines = source_code.splitlines()

        # Component tracking
        self.components: List[CodeComponent] = []
        self.relationships: List[Relationship] = []
        self.current_class: Optional[CodeComponent] = None
        self.current_function: Optional[CodeComponent] = None

        # Analysis state
        self.imports: Set[str] = set()
        self.dependencies: Set[str] = set()
        self.call_graph: Dict[str, Set[str]] = {}

        # Tag registry
        self.tag_registry = get_tag_registry()

    def analyze(self) -> Tuple[List[CodeComponent], List[Relationship]]:
        """Analyze the source code and return components and relationships."""
        try:
            tree = ast.parse(self.source_code)
            self.visit(tree)

            # Create file-level component
            file_component = self._create_file_component()
            self.components.insert(0, file_component)

            # Add containment relationships
            self._add_containment_relationships(file_component)

            # Add dependency relationships
            self._add_dependency_relationships()

            logger.debug(
                f"Analyzed {self.file_path}: {len(self.components)} components, {len(self.relationships)} relationships"
            )

            return self.components, self.relationships

        except SyntaxError as e:
            logger.error(f"Syntax error in {self.file_path}: {e}")
            return [], []
        except Exception as e:
            logger.error(f"Error analyzing {self.file_path}: {e}")
            return [], []

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statements."""
        for alias in node.names:
            self.imports.add(alias.name)
            self.dependencies.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from-import statements."""
        if node.module:
            self.imports.add(node.module)
            self.dependencies.add(node.module)

            for alias in node.names:
                full_name = f"{node.module}.{alias.name}"
                self.imports.add(full_name)
                self.dependencies.add(full_name)

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions."""
        # Create class component
        class_component = self._create_class_component(node)
        self.components.append(class_component)

        # Set current class context
        previous_class = self.current_class
        self.current_class = class_component

        # Process class body
        self.generic_visit(node)

        # Restore previous context
        self.current_class = previous_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions."""
        # Determine if this is a method or standalone function
        if self.current_class:
            component = self._create_method_component(node)
        else:
            component = self._create_function_component(node)

        self.components.append(component)

        # Set current function context
        previous_function = self.current_function
        self.current_function = component

        # Process function body
        self.generic_visit(node)

        # Restore previous context
        self.current_function = previous_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definitions."""
        # Handle similar to regular functions but mark as async
        if self.current_class:
            component = self._create_method_component(node, is_async=True)
        else:
            component = self._create_function_component(node, is_async=True)

        self.components.append(component)

        # Set current function context
        previous_function = self.current_function
        self.current_function = component

        # Process function body
        self.generic_visit(node)

        # Restore previous context
        self.current_function = previous_function

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function calls to build call graph."""
        if self.current_function:
            call_name = self._get_call_name(node)
            if call_name:
                func_name = self.current_function.name
                if func_name not in self.call_graph:
                    self.call_graph[func_name] = set()
                self.call_graph[func_name].add(call_name)

        self.generic_visit(node)

    def _create_file_component(self) -> CodeComponent:
        """Create a component representing the entire file."""
        file_name = Path(self.file_path).stem

        # Calculate file metrics
        metrics = CodeMetrics(
            lines_of_code=len([line for line in self.source_lines if line.strip()]),
            dependency_count=len(self.dependencies),
        )

        # Determine file tags based on patterns
        tags = self._infer_file_tags()

        return CodeComponent(
            name=file_name,
            component_type=ComponentType.FILE,
            file_path=self.file_path,
            line_number=1,
            end_line_number=len(self.source_lines),
            tags=TagCollection(tags=tags),
            metrics=metrics,
            metadata={
                "imports": list(self.imports),
                "dependencies": list(self.dependencies),
                "file_extension": Path(self.file_path).suffix,
            },
        )

    def _create_class_component(self, node: ast.ClassDef) -> CodeComponent:
        """Create a component for a class definition."""
        # Calculate class metrics
        methods = [
            n
            for n in node.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        metrics = CodeMetrics(
            lines_of_code=node.end_lineno - node.lineno + 1 if node.end_lineno else 1,
            method_count=len(methods),
            dependency_count=len(node.bases) + len(getattr(node, "decorator_list", [])),
        )

        # Infer class tags
        tags = self._infer_class_tags(node)

        return CodeComponent(
            name=node.name,
            component_type=ComponentType.CLASS,
            file_path=self.file_path,
            line_number=node.lineno,
            end_line_number=node.end_lineno,
            parent_id=None,  # Will be set when adding containment relationships
            tags=TagCollection(tags=tags),
            metrics=metrics,
            metadata={
                "bases": [self._get_name(base) for base in node.bases],
                "decorators": [
                    self._get_name(dec) for dec in getattr(node, "decorator_list", [])
                ],
                "docstring": ast.get_docstring(node),
            },
        )

    def _create_method_component(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool = False
    ) -> CodeComponent:
        """Create a component for a method definition."""
        # Calculate method metrics
        metrics = CodeMetrics(
            lines_of_code=node.end_lineno - node.lineno + 1 if node.end_lineno else 1,
            parameter_count=len(node.args.args),
            cyclomatic_complexity=self._calculate_cyclomatic_complexity(node),
        )

        # Infer method tags
        tags = self._infer_method_tags(node, is_async)

        return CodeComponent(
            name=node.name,
            component_type=ComponentType.METHOD,
            file_path=self.file_path,
            line_number=node.lineno,
            end_line_number=node.end_lineno,
            parent_id=self.current_class.id if self.current_class else None,
            tags=TagCollection(tags=tags),
            metrics=metrics,
            metadata={
                "is_async": is_async,
                "decorators": [
                    self._get_name(dec) for dec in getattr(node, "decorator_list", [])
                ],
                "docstring": ast.get_docstring(node),
                "is_property": any(
                    self._get_name(dec) == "property"
                    for dec in getattr(node, "decorator_list", [])
                ),
                "is_static": any(
                    self._get_name(dec) == "staticmethod"
                    for dec in getattr(node, "decorator_list", [])
                ),
                "is_class_method": any(
                    self._get_name(dec) == "classmethod"
                    for dec in getattr(node, "decorator_list", [])
                ),
            },
        )

    def _create_function_component(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool = False
    ) -> CodeComponent:
        """Create a component for a function definition."""
        # Calculate function metrics
        metrics = CodeMetrics(
            lines_of_code=node.end_lineno - node.lineno + 1 if node.end_lineno else 1,
            parameter_count=len(node.args.args),
            cyclomatic_complexity=self._calculate_cyclomatic_complexity(node),
        )

        # Infer function tags
        tags = self._infer_function_tags(node, is_async)

        return CodeComponent(
            name=node.name,
            component_type=ComponentType.FUNCTION,
            file_path=self.file_path,
            line_number=node.lineno,
            end_line_number=node.end_lineno,
            tags=TagCollection(tags=tags),
            metrics=metrics,
            metadata={
                "is_async": is_async,
                "decorators": [
                    self._get_name(dec) for dec in getattr(node, "decorator_list", [])
                ],
                "docstring": ast.get_docstring(node),
            },
        )

    def _infer_file_tags(self) -> Set[Tag]:
        """Infer tags for a file based on its content and patterns."""
        tags = set()

        # Add basic file tag
        file_tag = self.tag_registry.get_tag("File")
        if file_tag:
            tags.add(file_tag)

        # Infer architectural layer from file path
        path_parts = Path(self.file_path).parts

        if any(part in ["core", "domain"] for part in path_parts):
            core_tag = self.tag_registry.get_tag("Core")
            if core_tag:
                tags.add(core_tag)
        elif any(part in ["application", "app", "services"] for part in path_parts):
            app_tag = self.tag_registry.get_tag("Application")
            if app_tag:
                tags.add(app_tag)
        elif any(
            part in ["infrastructure", "adapters", "external"] for part in path_parts
        ):
            infra_tag = self.tag_registry.get_tag("Infrastructure")
            if infra_tag:
                tags.add(infra_tag)

        # Check for test files
        if "test" in Path(self.file_path).name.lower():
            # Could add test-specific tags here
            pass

        return tags

    def _infer_class_tags(self, node: ast.ClassDef) -> Set[Tag]:
        """Infer tags for a class based on its characteristics."""
        tags = set()

        # Add basic class tag
        class_tag = self.tag_registry.get_tag("Class")
        if class_tag:
            tags.add(class_tag)

        # Check for common patterns in class name
        class_name = node.name.lower()

        if class_name.endswith("service"):
            service_tag = self.tag_registry.get_tag("Service")
            if service_tag:
                tags.add(service_tag)
        elif class_name.endswith("repository"):
            repo_tag = self.tag_registry.get_tag("Repository")
            if repo_tag:
                tags.add(repo_tag)
        elif class_name.endswith("factory"):
            factory_tag = self.tag_registry.get_tag("Factory")
            if factory_tag:
                tags.add(factory_tag)
        elif class_name.endswith("entity"):
            entity_tag = self.tag_registry.get_tag("Entity")
            if entity_tag:
                tags.add(entity_tag)

        # Check for inheritance patterns
        if node.bases:
            # Has base classes - might be an entity or value object
            pass

        # Check for decorators that indicate patterns
        decorators = [
            self._get_name(dec) for dec in getattr(node, "decorator_list", [])
        ]
        if "dataclass" in decorators:
            # Likely a value object or entity
            pass

        return tags

    def _infer_method_tags(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool
    ) -> Set[Tag]:
        """Infer tags for a method based on its characteristics."""
        tags = set()

        # Add basic method tag
        method_tag = self.tag_registry.get_tag("Method")
        if method_tag:
            tags.add(method_tag)

        # Add async tag if applicable
        if is_async:
            async_tag = self.tag_registry.get_tag("Async")
            if async_tag:
                tags.add(async_tag)
        else:
            sync_tag = self.tag_registry.get_tag("Sync")
            if sync_tag:
                tags.add(sync_tag)

        # Check decorators for special method types
        decorators = [
            self._get_name(dec) for dec in getattr(node, "decorator_list", [])
        ]

        if "property" in decorators:
            prop_tag = self.tag_registry.get_tag("Property")
            if prop_tag:
                tags.add(prop_tag)

        return tags

    def _infer_function_tags(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool
    ) -> Set[Tag]:
        """Infer tags for a function based on its characteristics."""
        tags = set()

        # Add basic function tag
        function_tag = self.tag_registry.get_tag("Function")
        if function_tag:
            tags.add(function_tag)

        # Add async tag if applicable
        if is_async:
            async_tag = self.tag_registry.get_tag("Async")
            if async_tag:
                tags.add(async_tag)
        else:
            sync_tag = self.tag_registry.get_tag("Sync")
            if sync_tag:
                tags.add(sync_tag)

        return tags

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a function or method."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1

        return complexity

    def _get_name(self, node: ast.AST) -> str:
        """Extract name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return str(node)

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """Extract the name of a function call."""
        try:
            return self._get_name(node.func)
        except:
            return None

    def _add_containment_relationships(self, file_component: CodeComponent) -> None:
        """Add CONTAINS relationships between parent and child components."""
        for component in self.components[1:]:  # Skip file component
            if component.parent_id:
                # Find parent component
                parent = next(
                    (c for c in self.components if c.id == component.parent_id), None
                )
                if parent:
                    relationship = Relationship(
                        source_id=parent.id,
                        target_id=component.id,
                        relationship_type=RelationshipType.CONTAINS,
                    )
                    self.relationships.append(relationship)
            else:
                # Top-level component contained by file
                relationship = Relationship(
                    source_id=file_component.id,
                    target_id=component.id,
                    relationship_type=RelationshipType.CONTAINS,
                )
                self.relationships.append(relationship)

    def _add_dependency_relationships(self) -> None:
        """Add dependency relationships based on imports and calls."""
        # Add call relationships
        for caller, callees in self.call_graph.items():
            caller_component = next(
                (c for c in self.components if c.name == caller), None
            )
            if caller_component:
                for callee in callees:
                    callee_component = next(
                        (c for c in self.components if c.name == callee), None
                    )
                    if callee_component and callee_component.id != caller_component.id:
                        relationship = Relationship(
                            source_id=caller_component.id,
                            target_id=callee_component.id,
                            relationship_type=RelationshipType.CALLS,
                        )
                        self.relationships.append(relationship)


class StaticCodeAnalyzer:
    """
    Main static code analyzer that orchestrates AST analysis for different file types.

    Provides a unified interface for analyzing source code files and extracting
    structural information, components, and relationships.
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def analyze_file(
        self, file_path: str
    ) -> Tuple[List[CodeComponent], List[Relationship]]:
        """
        Analyze a single source code file.

        Args:
            file_path: Path to the source code file

        Returns:
            Tuple of (components, relationships) found in the file
        """
        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            # Determine file type and use appropriate analyzer
            if file_path.endswith(".py"):
                return self._analyze_python_file(file_path, source_code)
            else:
                self.logger.warning(f"Unsupported file type: {file_path}")
                return [], []

        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {e}")
            return [], []

    def analyze_directory(
        self, directory_path: str, recursive: bool = True
    ) -> Tuple[List[CodeComponent], List[Relationship]]:
        """
        Analyze all supported files in a directory.

        Args:
            directory_path: Path to the directory to analyze
            recursive: Whether to analyze subdirectories recursively

        Returns:
            Tuple of (all_components, all_relationships) found in the directory
        """
        all_components = []
        all_relationships = []

        directory = Path(directory_path)
        if not directory.exists():
            self.logger.error(f"Directory does not exist: {directory_path}")
            return [], []

        # Find all Python files
        pattern = "**/*.py" if recursive else "*.py"
        python_files = list(directory.glob(pattern))

        self.logger.info(
            f"Analyzing {len(python_files)} Python files in {directory_path}"
        )

        for file_path in python_files:
            components, relationships = self.analyze_file(str(file_path))
            all_components.extend(components)
            all_relationships.extend(relationships)

        self.logger.info(
            f"Analysis complete: {len(all_components)} components, {len(all_relationships)} relationships"
        )

        return all_components, all_relationships

    def _analyze_python_file(
        self, file_path: str, source_code: str
    ) -> Tuple[List[CodeComponent], List[Relationship]]:
        """Analyze a Python source file using AST."""
        visitor = PythonASTVisitor(file_path, source_code)
        return visitor.analyze()
