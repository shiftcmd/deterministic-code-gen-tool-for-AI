# AST Parser Engine Architecture

## Overview

The AST Parser Engine is a core component of the Python Debug Tool, designed to extract structural elements from Python codebases with a focus on configurability, extensibility, and comprehensive analysis. Following the Hexagonal Architecture principles, we've separated the core parsing logic from external dependencies and persistence mechanisms.

## Architecture Principles

The parser engine follows these key principles:

1. **Plugin-Based Architecture**: Parsing capabilities are provided by plugins that can be selected by users
2. **Separation of Concerns**: Parsing logic is separated from data persistence (e.g., Neo4j graph creation)
3. **Configuration-Driven**: Users can select which parser to use for different code elements
4. **Comprehensive Analysis over Performance**: The system prioritizes detailed code analysis over execution speed

## Components

The parser engine consists of the following components:

### Core Domain

#### Parser Plugins

A plugin system that allows different parsing strategies to be used. Each plugin implements a common interface:

- **Base ParserPlugin Class**: Defines the interface for all plugins with methods for parsing modules, classes, functions, and variables
- **Plugin Registry**: Manages plugin discovery, registration, and selection

Specific plugins include:

- **AST Parser Plugin**: Uses Python's built-in `ast` module for basic parsing
- **Astroid Parser Plugin**: Uses the `astroid` library for enhanced type inference and OOP analysis
- **Inspect4py Parser Plugin**: Uses `inspect4py` for comprehensive module and package analysis

#### Parser Models

Data structures representing parsed Python code elements:

- **ParsedModule**: Represents a Python module file
- **ParsedClass**: Represents a class definition
- **ParsedFunction**: Represents a function or method
- **ParsedVariable**: Represents a variable declaration
- **ParsedImport**: Represents an import statement

### Application Layer

#### Integration Module

Connects the plugin system with the existing codebase parser:

- **HybridParserIntegration**: Acts as a bridge between the existing parser and the new plugin system
- **Plugin Selection Logic**: Selects appropriate plugins based on configuration

#### Configuration System

Manages parser configuration:

- **ParserType Enum**: Defines available parser types
- **ParserConfig**: Contains configuration options for the parser
- **Presets**: Predefined configuration sets for different use cases

### Infrastructure Layer (Adapters)

#### Exporters

Converts parsed data to different formats and destinations:

- **Base ParserExporter**: Defines the exporter interface
- **Neo4j Exporter**: Exports parsed data to Neo4j graph database

## Data Flow

1. User selects parser configuration
2. CodebaseParser scans the codebase for Python files
3. For each file, ModuleParser uses the selected plugin to parse the file
4. Parsed data is collected and processed
5. Data is optionally exported to Neo4j through the Neo4j exporter

## Plugin Registration and Discovery

Plugins are automatically discovered and registered:

```python
def register_plugin(plugin_class: Type[ParserPlugin]) -> None:
    """Register a parser plugin."""
    if not issubclass(plugin_class, ParserPlugin):
        raise TypeError("Plugin must be a subclass of ParserPlugin")
    
    _plugins[plugin_class.name] = plugin_class
    logger.debug(f"Registered parser plugin: {plugin_class.name}")
```

## Neo4j Integration

The Neo4j exporter creates a rich graph schema:

- **Nodes**: Codebase, Module, Class, Function, Variable, Import
- **Relationships**: CONTAINS, DEFINES, IMPORTS, INHERITS_FROM, DEPENDS_ON, CALLS

## Configuration Options

Users can configure:

1. Which parser to use for each element type (module, class, function, variable)
2. Performance options (parallel processing, caching)
3. Analysis options (type inference, complexity calculation)
4. Neo4j export options (clear existing data, include content)

## User Interface Integration

The plugin system generates UI configuration schemas to allow users to configure parsing options through the frontend.

## Error Handling

The system includes comprehensive error handling:

- Graceful degradation when a plugin fails
- Fallback to simpler parsers when advanced ones fail
- Detailed error reporting

## Testing Strategy

The parser engine is tested with:

1. Unit tests for each plugin
2. Integration tests for the complete pipeline
3. Performance tests with large codebases
4. Edge case tests with malformed Python files

## Future Extensions

The architecture allows for easy extension:

1. New parser plugins can be added without modifying existing code
2. New exporters can be added for different data destinations
3. Additional analysis capabilities can be added to existing plugins
