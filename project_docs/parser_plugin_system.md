# Parser Plugin System Technical Documentation

## Overview

This document provides detailed technical information about the Parser Plugin System implementation, which is a core part of the AST Parser Engine in the Python Debug Tool. The system follows the Pragmatic Hexagonal Architecture pattern as specified in the project rules, with a strong emphasis on separating core business logic from external concerns.

## AI Intent Tagging

Our code includes AI Intent Tags that help document architectural boundaries and intentions:

```python
# AI-Intent: Core-Domain
# Intent: This module contains core business logic for parsing Python code
# Confidence: High
```

These tags categorize code into three main architectural layers:
1. **Core Domain** - Business logic and domain entities
2. **Application** - Use cases and orchestration logic
3. **Infrastructure** - External adapters and frameworks

## Architecture Implementation

### Core Domain Components

The parser plugin system is structured according to the Hexagonal Architecture pattern:

#### Domain Models (`models.py`)

```python
@dataclass
class ParsedModule:
    """Represents a parsed Python module."""
    name: str
    path: str
    classes: List[ParsedClass] = field(default_factory=list)
    functions: List[ParsedFunction] = field(default_factory=list)
    variables: List[ParsedVariable] = field(default_factory=list)
    imports: List[ParsedImport] = field(default_factory=list)
    docstring: str = ""
    line_count: int = 0
    error: Optional[str] = None
    parsed_with: str = "unknown"
```

#### Core Plugin Interface (`plugins/__init__.py`)

The plugin interface is a pure Python implementation with no external dependencies, allowing for clean core business logic:

```python
class ParserPlugin:
    """Base class for parser plugins."""
    
    name: str = "base"
    description: str = "Base parser plugin"
    version: str = "0.1.0"
    supported_types: Set[str] = {"module", "class", "function", "variable"}
    requires_dependencies: List[str] = []
    default_options: Dict[str, Any] = {}
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize the plugin with options."""
        self.options = self.default_options.copy()
        if options:
            self.options.update(options)
```

### Application Layer

#### Integration Module (`integration.py`)

The integration module orchestrates the plugins and serves as the application layer:

```python
class HybridParserIntegration:
    """
    Integrates the plugin system with the codebase parser and module parser.
    
    This class acts as a bridge between the existing parser architecture
    and the new plugin-based approach.
    """
    
    def __init__(self, config: ParserConfig = None):
        """Initialize the parser integration."""
        self.config = config or ParserConfig()
        self._discover_plugins()
```

#### Configuration System (`config.py`)

The configuration system controls the behavior of the parsing system:

```python
@dataclass
class ParserConfig:
    module_parser: ParserType = ParserType.BUILT_IN_AST
    class_parser: ParserType = ParserType.BUILT_IN_AST
    function_parser: ParserType = ParserType.BUILT_IN_AST
    variable_parser: ParserType = ParserType.BUILT_IN_AST
    # Additional configuration options...
```

### Infrastructure Layer (Adapters)

#### Parser Plugins

1. **AST Parser Plugin** (`plugins/ast_parser_plugin.py`)
   - Uses Python's built-in `ast` module
   - No external dependencies
   - Focuses on basic structure extraction

2. **Astroid Parser Plugin** (`plugins/astroid_parser_plugin.py`)
   - Uses the `astroid` library
   - Provides enhanced type inference
   - Handles complex OOP relationships

3. **Inspect4py Parser Plugin** (`plugins/inspect4py_parser_plugin.py`)
   - Uses the `inspect4py` library
   - Specializes in package-level analysis
   - Handles module dependencies and structure

#### Neo4j Exporter (`exporters/neo4j_exporter.py`)

The Neo4j exporter is an infrastructure adapter that converts parsed data to a graph database:

```python
class Neo4jExporter(ParserExporter):
    """Exporter to save parsed code to Neo4j graph database."""
    
    name = "neo4j"
    description = "Exports parsed code to Neo4j graph database"
    version = "1.0.0"
```

## Plugin Implementation Details

### Plugin Registration Mechanism

Plugins register themselves through a decorator pattern:

```python
def register_plugin(plugin_class: Type[ParserPlugin]) -> None:
    """Register a parser plugin."""
    if not issubclass(plugin_class, ParserPlugin):
        raise TypeError("Plugin must be a subclass of ParserPlugin")
    
    _plugins[plugin_class.name] = plugin_class
    logger.debug(f"Registered parser plugin: {plugin_class.name}")
```

### Plugin Discovery

Plugins are automatically discovered through Python's module system:

```python
def _discover_plugins(self) -> None:
    """Discover and initialize available parser plugins."""
    import importlib
    import pkgutil
    from . import plugins
    
    for _, name, _ in pkgutil.iter_modules(plugins.__path__, plugins.__name__ + '.'):
        try:
            importlib.import_module(name)
            logger.debug(f"Imported plugin module: {name}")
        except ImportError as e:
            logger.warning(f"Could not import plugin module {name}: {e}")
```

### Plugin Selection Logic

The system selects plugins based on configuration:

```python
def get_plugin_for_type(self, parser_type: ParserType) -> Optional[ParserPlugin]:
    """Get a parser plugin for the given parser type."""
    # Map parser types to plugin names
    plugin_map = {
        ParserType.BUILT_IN_AST: "ast",
        ParserType.ASTROID: "astroid",
        ParserType.INSPECT4PY: "inspect4py"
    }
    
    # Get the plugin name for this parser type
    plugin_name = plugin_map.get(parser_type)
    if not plugin_name:
        logger.warning(f"No plugin mapping for parser type: {parser_type}")
        return None
    
    # Try to get the plugin
    try:
        plugin_options = self.config.tool_options.get(plugin_name, {})
        return get_plugin(plugin_name, plugin_options)
    except ValueError:
        logger.warning(f"Parser plugin not found: {plugin_name}")
        return None
```

## Neo4j Integration Details

### Graph Schema

The Neo4j exporter creates the following node types:

- **Codebase**: Represents the entire codebase
- **Module**: Represents a Python module file
- **Class**: Represents a class definition
- **Function**: Represents a function or method
- **Variable**: Represents a variable declaration
- **Import**: Represents an import statement

### Relationship Types

The following relationship types are created:

- **CONTAINS**: Parent-child relationship (Codebase → Module → Class/Function)
- **DEFINES**: Class defines method/attribute
- **IMPORTS**: Module imports another module
- **INHERITS_FROM**: Class inheritance relationship
- **DEPENDS_ON**: Module depends on another module
- **CALLS**: Function calls another function

### Batch Processing

The Neo4j exporter uses batch processing for performance:

```python
def _execute_batch(self, query: str, parameters: Dict[str, Any] = None) -> None:
    """Execute a query in batch mode."""
    if not self.transaction:
        self.transaction = self.session.begin_transaction()
    
    self.transaction.run(query, parameters or {})
    self.batch_count += 1
    
    if self.batch_count >= self.options["batch_size"]:
        self._flush_batch()
```

## Error Handling Strategy

The system implements a robust error handling strategy:

1. **Plugin Level**: Each plugin handles its own errors and provides fallback mechanisms
2. **Integration Level**: The integration module catches plugin errors and falls back to other plugins
3. **Exporter Level**: Exporters handle database errors and provide retries

Example:

```python
def parse_file(self, file_path: str) -> ParsedModule:
    """Parse a Python file using the configured plugins."""
    try:
        # Try using the plugin integration first
        return integration.parse_file(file_path)
    except Exception as e:
        logger.warning(f"Plugin-based parsing failed for {file_path}: {e}")
        logger.warning("Falling back to original parser")
        # Fall back to the original method
        return original_parse_file(file_path)
```

## Using the Parser Plugin System

### Basic Usage

```python
# Create a configuration
config = ParserConfig(
    module_parser=ParserType.INSPECT4PY,
    class_parser=ParserType.ASTROID,
    function_parser=ParserType.ASTROID,
    variable_parser=ParserType.BUILT_IN_AST
)

# Create a parser integration
integration = HybridParserIntegration(config)

# Parse a file
parsed_module = integration.parse_file("path/to/file.py")

# Export to Neo4j
integration.export_to_neo4j(parsed_modules, {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "password"
})
```

### Advanced Configuration

```python
# Configure specific plugin options
config = ParserConfig(
    module_parser=ParserType.ASTROID,
    tool_options={
        "astroid": {
            "infer_types": True,
            "calculate_complexity": True,
            "detect_design_patterns": True
        },
        "neo4j": {
            "batch_size": 500,
            "clear_existing": True,
            "detect_architecture": True
        }
    }
)
```

## Testing Approach

The system includes comprehensive tests:

1. **Unit Tests**: Test each plugin in isolation
2. **Integration Tests**: Test the complete pipeline
3. **Performance Tests**: Test with large codebases
4. **Edge Case Tests**: Test with malformed Python files

## Pragmatic Architecture Decisions

In line with our project's pragmatic approach to Hexagonal Architecture, we made the following decisions:

1. The Neo4j exporter is a separate component from the parsing logic, ensuring clean separation of concerns
2. Plugin interfaces are pure Python with no dependencies, ensuring a clean core domain
3. The integration module bridges between the existing codebase parser and the new plugin system
4. Configuration drives the behavior of the system, allowing for user customization
