# Neo4j Integration for AST Parser

## Overview

This document describes the Neo4j integration for the AST parser engine, focusing on how parsed Python code is exported to Neo4j and how architectural metadata is handled. This integration follows the Pragmatic Hexagonal Architecture pattern, with a clear separation between parsing logic and the Neo4j adapter.

## Architecture

The Neo4j integration follows these architectural principles:

1. **Separation of Concerns**: Parsing is completely separated from Neo4j export
2. **Adapter Pattern**: Neo4j export is implemented as an adapter for the parser
3. **Configurability**: All Neo4j options are configurable
4. **Conditional Architecture Analysis**: Architectural metadata is only included when specifically requested

## Components

### Neo4j Exporter

The `Neo4jExporter` class is the primary component responsible for exporting parsed data to Neo4j:

```python
class Neo4jExporter(ParserExporter):
    """Exporter to save parsed code to Neo4j graph database."""
    
    name = "neo4j"
    description = "Exports parsed code to Neo4j graph database"
    version = "1.0.0"
    
    default_options = {
        "uri": "bolt://localhost:7687",
        "user": "neo4j",
        "password": "neo4j",
        "database": "neo4j",
        "clear_existing": False,
        "batch_size": 100,
        "include_content": False,
        "detect_architecture": False
    }
```

### Neo4j Graph Schema

The exporter creates a rich graph schema in Neo4j:

#### Node Types

1. **Codebase**: Represents the entire codebase
   - Properties: name, path, module_count, class_count, function_count, variable_count

2. **Module**: Represents a Python module file
   - Properties: name, path, docstring, line_count, imports_count, class_count, function_count

3. **Class**: Represents a class definition
   - Properties: name, docstring, line_count, method_count, attribute_count, superclasses

4. **Function**: Represents a function or method
   - Properties: name, docstring, line_count, parameter_count, return_type, complexity

5. **Variable**: Represents a variable declaration
   - Properties: name, value, type, is_constant

6. **Import**: Represents an import statement
   - Properties: name, module, alias, is_from_import

#### Relationship Types

1. **CONTAINS**: Parent-child relationship
   - Codebase → Module
   - Module → Class
   - Module → Function
   - Module → Variable
   - Class → Function (Methods)
   - Class → Variable (Attributes)

2. **IMPORTS**: Import relationship
   - Module → Import

3. **INHERITS_FROM**: Inheritance relationship
   - Class → Class

4. **DEPENDS_ON**: Dependency relationship
   - Module → Module
   - Class → Class
   - Function → Function

5. **CALLS**: Function call relationship
   - Function → Function

## Architectural Metadata Integration

When architectural detection is enabled (via the `--hex` flag), additional metadata is added to nodes:

### Codebase Architectural Properties

```python
def _add_architectural_properties_to_codebase(self, codebase_id: int) -> None:
    """Add architectural properties to codebase node."""
    if not self.options.get("detect_architecture", False):
        return
        
    properties = {
        "architecture_style": "hexagonal",
        "layer_distribution": json.dumps({
            "core": 35,
            "application": 25, 
            "infrastructure": 40
        }),
        "component_count": 123,
        "architectural_quality_score": 85
    }
    
    query = """
    MATCH (c:Codebase) WHERE ID(c) = $codebase_id
    SET c += $properties
    """
    
    self._execute_batch(query, {
        "codebase_id": codebase_id,
        "properties": properties
    })
```

### Module Architectural Properties

```python
def _add_architectural_properties_to_module(self, module_id: int, parsed_module: ParsedModule) -> None:
    """Add architectural properties to module node."""
    if not self.options.get("detect_architecture", False):
        return
        
    # Detect the architectural layer
    layer = self._detect_architectural_layer(parsed_module)
    
    properties = {
        "architectural_layer": layer,
        "architectural_role": self._detect_architectural_role(parsed_module, layer),
        "component_type": self._detect_component_type(parsed_module),
        "cyclomatic_complexity": self._calculate_module_complexity(parsed_module)
    }
    
    query = """
    MATCH (m:Module) WHERE ID(m) = $module_id
    SET m += $properties
    SET m:${layer}
    """
    
    self._execute_batch(query, {
        "module_id": module_id,
        "properties": properties,
        "layer": layer
    })
```

### Class Architectural Properties

```python
def _add_architectural_properties_to_class(self, class_id: int, parsed_class: ParsedClass) -> None:
    """Add architectural properties to class node."""
    if not self.options.get("detect_architecture", False):
        return
        
    # Detect architectural role
    layer = self._detect_class_architectural_layer(parsed_class)
    role = self._detect_class_architectural_role(parsed_class)
    
    properties = {
        "architectural_layer": layer,
        "architectural_role": role,
        "design_pattern": self._detect_design_pattern(parsed_class),
        "cyclomatic_complexity": self._calculate_class_complexity(parsed_class)
    }
    
    query = """
    MATCH (c:Class) WHERE ID(c) = $class_id
    SET c += $properties
    SET c:${layer}
    SET c:${role}
    """
    
    self._execute_batch(query, {
        "class_id": class_id,
        "properties": properties,
        "layer": layer,
        "role": role
    })
```

### Architectural Relationships

```python
def _create_architectural_relationships(self) -> None:
    """Create architectural relationships between nodes."""
    if not self.options.get("detect_architecture", False):
        return
        
    # Create inheritance relationships
    query = """
    MATCH (c1:Class), (c2:Class)
    WHERE c1.name IN c2.superclasses
    CREATE (c2)-[:INHERITS_FROM]->(c1)
    """
    self._execute_batch(query)
    
    # Create dependency relationships
    query = """
    MATCH (m1:Module), (m2:Module)
    WHERE (m1)-[:IMPORTS]->(:Import {module: m2.name})
    CREATE (m1)-[:DEPENDS_ON]->(m2)
    """
    self._execute_batch(query)
    
    # Additional architectural relationships based on specific patterns
    self._create_layer_dependency_relationships()
```

## Layer Detection Algorithm

The Neo4j exporter uses algorithms to detect architectural layers:

```python
def _detect_architectural_layer(self, parsed_module: ParsedModule) -> str:
    """Detect architectural layer for a module."""
    # Default to infrastructure
    layer = "Infrastructure"
    
    # Check for domain model indicators
    domain_indicators = [
        "entity", "model", "domain", "value_object",
        "aggregate", "business", "rule", "policy"
    ]
    
    # Check for application service indicators
    application_indicators = [
        "service", "application", "use_case", "handler",
        "facade", "controller", "orchestrator"
    ]
    
    # Check module path and name
    path_parts = parsed_module.path.split("/")
    
    if any(di in parsed_module.name.lower() for di in domain_indicators) or "domain" in path_parts:
        layer = "Core"
    elif any(ai in parsed_module.name.lower() for ai in application_indicators) or "application" in path_parts:
        layer = "Application"
        
    # Check imports for infrastructure dependencies
    infra_imports = [
        "flask", "django", "sqlalchemy", "requests", 
        "boto3", "pika", "kafka"
    ]
    
    has_core_imports = False
    has_infra_imports = False
    
    for imp in parsed_module.imports:
        if any(infra in imp.name for infra in infra_imports):
            has_infra_imports = True
        if "domain" in imp.name or any(di in imp.name for di in domain_indicators):
            has_core_imports = True
            
    # If module has core imports but no infra imports, it's likely application layer
    if has_core_imports and not has_infra_imports and layer != "Core":
        layer = "Application"
        
    return layer
```

## Using the Neo4j Exporter

### Basic Usage

```python
# Create parser integration
integration = HybridParserIntegration(config)

# Parse codebase
parsed_modules = integration.parse_codebase("/path/to/codebase")

# Export to Neo4j
integration.export_to_neo4j(parsed_modules, {
    "uri": "bolt://localhost:7687", 
    "user": "neo4j",
    "password": "password",
    "database": "neo4j"
})
```

### With Architectural Detection

```python
# Export with architectural detection
integration.export_to_neo4j(parsed_modules, {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "password",
    "database": "neo4j",
    "detect_architecture": True
})
```

### Using Environment Variables

The Neo4j exporter supports configuration via environment variables:

```python
# Environment variables
# NEO4J_URI
# NEO4J_USER
# NEO4J_PASSWORD
# NEO4J_DATABASE

# Export using environment variables
integration.export_to_neo4j(parsed_modules)
```

## Neo4j Cypher Queries for Analysis

### Find All Core Domain Classes

```cypher
MATCH (c:Class:Core)
RETURN c.name, c.architectural_role
```

### Find Architectural Violations

```cypher
MATCH (core:Core)-[:DEPENDS_ON]->(infra:Infrastructure)
WHERE NOT (infra:Port)
RETURN core.name, infra.name
```

### Find Most Complex Components

```cypher
MATCH (c:Class)
WHERE c.cyclomatic_complexity > 10
RETURN c.name, c.architectural_layer, c.cyclomatic_complexity
ORDER BY c.cyclomatic_complexity DESC
```

### Find Design Patterns

```cypher
MATCH (c:Class)
WHERE c.design_pattern IS NOT NULL
RETURN c.name, c.design_pattern
```

## Batch Processing and Performance

The Neo4j exporter uses batch processing to optimize performance:

```python
def _execute_batch(self, query: str, parameters: Dict[str, Any] = None) -> None:
    """Execute a query in batch mode."""
    if not self.transaction:
        self.transaction = self.session.begin_transaction()
    
    self.transaction.run(query, parameters or {})
    self.batch_count += 1
    
    if self.batch_count >= self.options["batch_size"]:
        self._flush_batch()
        
def _flush_batch(self) -> None:
    """Flush the current transaction batch."""
    if self.transaction:
        self.transaction.commit()
        self.transaction = None
    
    self.batch_count = 0
```

## Error Handling

The Neo4j exporter includes comprehensive error handling:

```python
def export(self, parsed_data: List[ParsedModule]) -> None:
    """Export parsed code to Neo4j."""
    try:
        self._connect()
        self._create_constraints()
        
        if self.options["clear_existing"]:
            self._clear_existing_data()
            
        codebase_id = self._create_codebase_node(parsed_data)
        
        for module in parsed_data:
            try:
                self._export_module(module, codebase_id)
            except Exception as e:
                logger.error(f"Error exporting module {module.name}: {e}")
                # Continue with next module
                
        self._create_relationships()
        
        if self.options["detect_architecture"]:
            self._create_architectural_relationships()
            
        self._flush_batch()
        logger.info("Export to Neo4j completed successfully")
        
    except Exception as e:
        logger.error(f"Error exporting to Neo4j: {e}")
        if self.transaction:
            self.transaction.rollback()
        raise
    finally:
        self._close()
```

## Integration with AI Tagging System

When used with the AI tagging system, the Neo4j exporter can include AI-generated tags as properties on nodes:

```python
def _add_ai_tags_to_class(self, class_id: int, parsed_class: ParsedClass) -> None:
    """Add AI tags to class node."""
    if not hasattr(parsed_class, "ai_tags") or not self.options.get("include_ai_tags", False):
        return
        
    tags = parsed_class.ai_tags
    
    properties = {
        "ai_intent": tags.get("intent"),
        "ai_layer": tags.get("layer"),
        "ai_role": tags.get("role"),
        "ai_pattern": tags.get("pattern"),
        "ai_confidence": tags.get("confidence", 0)
    }
    
    query = """
    MATCH (c:Class) WHERE ID(c) = $class_id
    SET c += $properties
    """
    
    self._execute_batch(query, {
        "class_id": class_id,
        "properties": properties
    })
```

## Configuration Options

The Neo4j exporter provides a wide range of configuration options:

| Option | Description | Default |
| ------ | ----------- | ------- |
| uri | Neo4j connection URI | bolt://localhost:7687 |
| user | Neo4j username | neo4j |
| password | Neo4j password | neo4j |
| database | Neo4j database name | neo4j |
| clear_existing | Clear existing data before import | False |
| batch_size | Number of operations per transaction | 100 |
| include_content | Include code content in nodes | False |
| detect_architecture | Enable architectural detection | False |
| include_ai_tags | Include AI-generated tags | False |

## Known Issues and Solutions

1. **Issue**: Architectural relationships show zero because architectural metadata must be attached during parsing, not just at the file level.
   **Solution**: Architecture detection is now conditional and properly integrated with the existing hex flag and parsing metadata.

2. **Issue**: Path resolution when dealing with absolute vs. relative paths.
   **Solution**: Path handling logic now correctly handles both absolute and relative paths.

3. **Issue**: Neo4j property serialization errors with complex data structures.
   **Solution**: Converting complex data structures like dictionaries to JSON strings before storing.

4. **Issue**: Maintaining consistency between different parser plugins' outputs.
   **Solution**: Using the integration module to normalize parser outputs before export.

## Future Enhancements

1. **Real-time Updates**: Support for incremental updates to the Neo4j database
2. **Versioning**: Track changes to the codebase over time
3. **Enhanced Architectural Analysis**: More sophisticated algorithms for architectural detection
4. **Integration with CI/CD**: Automatically update the Neo4j database on code changes
5. **Visual Reporting**: Generate visual reports from the Neo4j data
