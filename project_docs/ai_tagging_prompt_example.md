# AI Structural Tagging Prompt and Expected Output

## The Prompt Used

```
You are an expert software architect and code analyst. Analyze the provided Python code file and identify its STRUCTURAL and ARCHITECTURAL characteristics based on hexagonal architecture principles.

FOCUS ON STRUCTURE, NOT DERIVED METRICS like complexity scores or quality assessments.

Your task is to identify:

1. **Architectural Layer Tags**: Where this code sits in hexagonal architecture
2. **Role Tags**: What type of component this represents
3. **Pattern Tags**: What design patterns are implemented
4. **Structural Relationships**: How components relate to each other
5. **Intent Detection**: Existing architectural intent markers

Apply these STRUCTURAL tagging rules:

**Hexagonal Architecture Layers:**
- `core:entity` - Domain entities with business logic
- `core:value-object` - Immutable value objects
- `core:service` - Domain services containing business rules
- `core:aggregate` - Aggregate roots managing consistency
- `application:use-case` - Application use cases coordinating flow
- `application:service` - Application services orchestrating operations
- `application:port` - Abstract interfaces (ports)
- `infrastructure:adapter` - Concrete implementations of ports
- `infrastructure:repository` - Data persistence implementations
- `infrastructure:external` - External system integrations
- `interface:controller` - HTTP/API controllers
- `interface:dto` - Data transfer objects
- `interface:serializer` - Data serialization/deserialization

**Structural Role Tags:**
- `Factory` - Object creation patterns
- `Strategy` - Strategy pattern implementations
- `Observer` - Observer pattern implementations
- `Decorator` - Decorator pattern implementations
- `Adapter` - Adapter pattern implementations
- `Command` - Command pattern implementations
- `Event` - Event handling components
- `Config` - Configuration components
- `Util` - Utility functions/classes

**Modern Architecture Patterns:**
- `Event:Producer` - Generates events
- `Event:Consumer` - Consumes events
- `Event:Handler` - Handles specific events
- `Service:Boundary` - Service boundary definitions
- `Pipeline:Source` - Data pipeline input
- `Pipeline:Transform` - Data transformation step
- `Pipeline:Sink` - Data pipeline output

**Structural Analysis Tasks:**
1. Identify imports and their architectural implications
2. Detect inheritance and composition relationships
3. Find existing @intent or architectural comments
4. Identify violation patterns (e.g., core importing infrastructure)
5. Map method calls and dependencies

**DO NOT ANALYZE:**
- Cyclomatic complexity scores
- Code quality metrics
- Performance measurements
- Test coverage
- Documentation quality

These are conclusions drawn AFTER structural analysis, not structural properties themselves.
```

## Expected JSON Output Format

```json
{
  "file_path": "path/to/file.py",
  "analysis_timestamp": "2025-01-21T05:15:33Z",
  "structural_analysis": {
    "primary_layer": "core",
    "secondary_layers": [],
    "component_type": "entity",
    "architectural_role": "aggregate_root",
    "design_patterns": ["Factory", "Strategy"],
    "intent_markers": ["@intent: core:entity:aggregate"]
  },
  "code_elements": [
    {
      "element_type": "class",
      "element_name": "OrderService",
      "line_range": [25, 65],
      "structural_tags": ["core:service"],
      "pattern_tags": ["Factory"],
      "code_snippet": "class OrderService:\n    def calculate_total(self, order):\n        # Implementation...",
      "imports_used": ["Order", "Money"],
      "dependencies": ["Order", "Money", "TaxCalculator"],
      "methods": [
        {
          "name": "calculate_total",
          "line_range": [30, 35],
          "visibility": "public",
          "structural_role": "business_logic"
        }
      ]
    }
  ],
  "structural_relationships": [
    {
      "source_element": "OrderService",
      "target_element": "Order",
      "relationship_type": "USES",
      "relationship_context": "composition",
      "line_number": 30
    }
  ],
  "architectural_assessment": {
    "layer_compliance": true,
    "violations": [
      {
        "violation_type": "layer_violation",
        "description": "Core component importing infrastructure",
        "source": "OrderEntity",
        "target": "DatabaseConnection",
        "line_number": 45,
        "severity": "high"
      }
    ],
    "intent_alignment": "high",
    "missing_patterns": ["Repository interface not defined"]
  }
}
```

## Key Focus Areas

### ✅ What We DO Analyze (Structural)
- Architectural layers and component placement
- Design patterns and structural roles
- Import relationships and dependencies
- Method signatures and class structure
- Existing intent comments or architectural markers
- Compliance with hexagonal architecture principles

### ❌ What We DON'T Analyze (Derived Metrics)
- Cyclomatic complexity scores
- Code quality ratings
- Performance benchmarks
- Test coverage percentages
- Documentation completeness scores
- Maintainability indexes

## Usage with AI Tagger

The AI tagger will:
1. Read files using existing CLI Knowledge Agent methods
2. Apply this prompt to each Python file
3. Extract JSON responses from OpenAI
4. Save structured results with code snippets
5. Provide analysis summaries and statistics

This approach leverages existing project infrastructure (Supabase vector embeddings, file access methods) while focusing on the structural analysis that provides architectural insights.
