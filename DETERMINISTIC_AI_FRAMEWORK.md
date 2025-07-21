# Deterministic AI Code Generation Framework

A comprehensive framework for generating clean, hallucination-free, executable Python code using knowledge graphs, embeddings, and multi-layer validation.

## 🎯 Overview

This framework leverages your existing work in Neo4j knowledge graphs, embeddings, and database integration to create a deterministic AI code generation system that:

- **Prevents hallucinations** through knowledge graph validation
- **Ensures executability** via multi-layer validation
- **Maintains architecture compliance** through pattern detection
- **Provides iterative refinement** with feedback loops

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Deterministic AI Framework                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌─────────────────┐   ┌─────────────┐ │
│  │   Template    │    │    Knowledge    │   │   Pattern   │ │
│  │   Engine      │    │     Graph       │   │  Detector   │ │
│  │              │    │   (Neo4j)       │   │             │ │
│  └──────┬───────┘    └────────┬────────┘   └──────┬──────┘ │
│         │                      │                     │      │
│         └──────────┬───────────┼─────────────────────┘      │
│                    │           │                            │
│         ┌──────────▼───────────▼─────────────────────┐      │
│         │         Generation Engine                   │      │
│         │  • Template Selection                       │      │
│         │  • AI Generation with Context               │      │
│         │  • Hybrid Approach                          │      │
│         └────────────────┬───────────────────────────┘      │
│                          │                                  │
│         ┌────────────────▼───────────────────────────┐      │
│         │         Validation Pipeline                 │      │
│         │  1. AST Syntax Validation                  │      │
│         │  2. Knowledge Graph Existence Check        │      │
│         │  3. Hallucination Pattern Detection        │      │
│         │  4. Architecture Compliance                │      │
│         │  5. Risk Assessment                        │      │
│         └────────────────┬───────────────────────────┘      │
│                          │                                  │
│         ┌────────────────▼───────────────────────────┐      │
│         │         Refinement Loop                     │      │
│         │  • Feedback Generation                     │      │
│         │  • Prompt Enhancement                      │      │
│         │  • Iterative Improvement                   │      │
│         └────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Install dependencies
pip install neo4j psycopg2-binary openai sentence-transformers chromadb pyyaml

# Start services (using Docker)
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password neo4j:latest

docker run -d --name postgres -p 5432:5432 \
  -e POSTGRES_PASSWORD=password postgres:latest
```

### 2. Configure the Framework

Create `.ai_assistant.yml`:

```yaml
neo4j:
  uri: "bolt://localhost:7687"
  user: "neo4j"
  password: "password"

postgresql:
  connection_string: "postgresql://postgres:password@localhost/postgres"

openai:
  api_key: "${OPENAI_API_KEY}"

generation:
  default_type: "hybrid"
  max_iterations: 3
  max_risk_level: "medium"
```

### 3. Basic Usage

#### Interactive Mode
```bash
python ai_code_assistant.py --interactive
```

#### Command Line Generation
```bash
python ai_code_assistant.py --requirement "Create a REST API client for user management" --output client.py
```

#### Validation Only
```bash
python dev_validator.py existing_code.py
```

## 💡 Core Components

### 1. Knowledge Graph Validator (`KnowledgeGraphValidator`)

Validates generated code against your Neo4j knowledge graph:

- **API Existence**: Checks if imported modules and functions exist
- **Relationship Validation**: Ensures method calls are valid
- **Dependency Checking**: Validates import relationships

```python
# Example: Validate API exists
validator.validate_api_exists("requests", "get")  # True
validator.validate_api_exists("fake_module", "magic_method")  # False
```

### 2. Hallucination Detector (`HallucinationDetector`)

Detects common AI hallucination patterns:

- **Suspicious Prefixes**: `auto_`, `smart_`, `enhanced_`, `magic_`
- **Non-existent Methods**: `.strip_all()`, `.remove_whitespace()`
- **Fake Parameters**: `auto_detect=True`, `smart_mode=True`
- **Placeholder Code**: `TODO`, `FIXME`, `...` in code body

```python
# Example patterns detected:
✗ obj.auto_detect_issues()  # Suspicious 'auto_' method
✗ from magic import solve   # Suspicious 'magic' import
✗ text.strip_all()         # Non-existent string method
```

### 3. Template Engine (`TemplateEngine`)

Provides deterministic code generation using predefined templates:

**Available Templates:**
- `api_client`: REST API client with error handling
- `data_processor`: Data processing pipeline with validation

```python
# Template usage
template = engine.get_template("api_client")
code = engine.generate_from_template("api_client", {
    "class_name": "UserAPIClient",
    "service_name": "User Management API",
    "method_name": "get_user",
    "parameters": "user_id: int"
})
```

### 4. Main Generator (`DeterministicCodeGenerator`)

Orchestrates the entire generation process with three approaches:

#### Template Generation (Most Deterministic)
- Uses predefined templates
- AI extracts parameters
- High confidence, low risk

#### AI-Guided Generation (Flexible)
- AI generates code with constraints
- Knowledge graph provides context
- Iterative refinement based on validation

#### Hybrid Generation (Balanced)
- Tries template first
- Falls back to AI if template doesn't match
- Best of both approaches

## 🛠️ Usage Patterns

### Pattern 1: Development Workflow Integration

```bash
# 1. Generate code
python ai_code_assistant.py -r "Create a user authentication service" -o auth.py

# 2. Validate before commit
python dev_validator.py auth.py

# 3. Set up pre-commit hook
cp pre-commit-config.yaml .pre-commit-config.yaml
pre-commit install
```

### Pattern 2: IDE Integration

Create a VS Code task in `.vscode/tasks.json`:

```json
{
    "label": "Validate AI Code",
    "type": "shell",
    "command": "python",
    "args": ["dev_validator.py", "${file}"],
    "group": "build",
    "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
    }
}
```

### Pattern 3: CI/CD Pipeline

```yaml
# .github/workflows/validate-code.yml
name: Validate Generated Code
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Start Neo4j
        run: docker run -d --name neo4j -p 7687:7687 -e NEO4J_AUTH=neo4j/test neo4j:latest
      - name: Run Validation
        run: python dev_validator.py src/ --fail-on-issues
```

### Pattern 4: Interactive Development

```python
# Interactive session example
$ python ai_code_assistant.py -i

🚀 AI Code Assistant - Interactive Mode
💡 What would you like to generate? Create a function to validate email addresses

🤖 Generating code for: Create a function to validate email addresses
✅ Code generated successfully!
🎯 Confidence: 95.0%
⚠️  Risk Level: LOW

📝 Generated Code:
----------------------------------------
import re
from typing import bool

def validate_email(email: str) -> bool:
    """Validate email address format using regex pattern"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
----------------------------------------

💾 Save to file? (y/N): y
📁 Filename: email_validator.py
💾 Code saved to: email_validator.py
```

## 🔧 Configuration Options

### Validation Configuration (`.validator.yml`)

```yaml
validation:
  check_imports: true        # Validate imports against knowledge graph
  check_methods: true        # Validate method calls
  check_hallucinations: true # Check for AI hallucination patterns
  max_risk_level: "medium"   # Maximum acceptable risk level

patterns:
  suspicious_prefixes:       # Method prefixes to flag
    - "auto_"
    - "smart_"
    - "enhanced_"
  
  blocked_imports:          # Imports to block
    - "magic"
    - "utils.helpers"
  
  placeholder_patterns:     # Code patterns to flag
    - "TODO"
    - "FIXME"
    - "..."
```

### Generation Configuration (`.ai_assistant.yml`)

```yaml
generation:
  default_type: "hybrid"     # template, ai_guided, hybrid
  max_iterations: 3          # Maximum refinement iterations
  max_risk_level: "medium"   # Risk threshold for auto-approval

output:
  save_to_file: true        # Auto-save valid code
  show_validation: true     # Show validation details
  format_code: true         # Format output code
```

## 📊 Risk Assessment

The framework provides five risk levels:

### ✅ LOW RISK
- No validation issues
- All APIs exist in knowledge graph
- No hallucination patterns detected
- Executable code

### ⚠️ MEDIUM RISK
- 1-2 minor issues
- Non-critical API usage
- Acceptable for development

### 🚨 HIGH RISK
- 3-5 validation issues
- Missing API references
- Multiple hallucination patterns
- Requires review before use

### 🛑 CRITICAL RISK
- Syntax errors
- Blocked imports detected
- Major architectural violations
- Manual review required

## 🎯 Integration with Existing Components

### From Your `example_code/` Directory:

#### 1. AST Dependency Extraction
```python
# Integrated into KnowledgeGraphValidator
# Extracts relationships for validation
ast_extractor = ASTDependencyExtractor()
relationships = ast_extractor.extract_dependencies(code)
```

#### 2. Hallucination Detection
```python
# Multiple detectors combined
comprehensive_detector = ComprehensiveHallucinationDetector()
regex_detector = RegexHallucinationDetector()
```

#### 3. Bridge to Neo4j
```python
# Knowledge graph integration
bridge = SupabaseNeo4jBridge()
bridge.enrich_with_architectural_metadata(code_components)
```

#### 4. Enhanced AST Analysis
```python
# Type validation and architectural analysis
analyzer = EnhancedASTAnalyzer()
analysis = analyzer.analyze_with_stubs(code, stub_files)
```

## 🧪 Testing and Validation

### Unit Tests

```python
# test_framework.py
def test_template_generation():
    engine = TemplateEngine()
    code = engine.generate_from_template("api_client", {
        "class_name": "TestClient",
        "service_name": "Test API"
    })
    assert "class TestClient" in code
    assert "Test API" in code

def test_hallucination_detection():
    detector = HallucinationDetector()
    result = detector.detect_hallucinations("obj.auto_magic_fix()")
    assert not result.valid
    assert "auto_" in str(result.issues)
```

### Integration Tests

```python
# test_integration.py
def test_end_to_end_generation():
    generator = DeterministicCodeGenerator(config)
    code, validation = generator.generate_code(
        "Create a simple API client"
    )
    assert validation.valid
    assert "class" in code
    assert "def " in code
```

## 🔄 Continuous Improvement

### Feedback Loop

1. **Generation** → AI creates code based on requirement
2. **Validation** → Multi-layer checking against knowledge graph
3. **Feedback** → Specific issues converted to improvement prompts
4. **Refinement** → AI adjusts code based on validation feedback
5. **Iteration** → Repeat until validation passes or max iterations reached

### Learning from Failures

```python
# Track common failures for pattern improvement
failure_tracker = {
    "missing_imports": ["requests", "json", "typing"],
    "hallucinated_methods": [".auto_detect()", ".smart_parse()"],
    "architectural_violations": ["domain→infrastructure dependency"]
}
```

## 🚀 Advanced Usage

### Custom Templates

```python
# Add custom template
template_engine.templates["my_template"] = CodeTemplate(
    name="my_template",
    description="Custom processing template",
    template="""
class {class_name}:
    def process(self, data: {input_type}) -> {output_type}:
        {implementation}
    """,
    parameters=["class_name", "input_type", "output_type", "implementation"],
    validation_rules=["valid_python_identifier", "valid_type_annotation"]
)
```

### Custom Validation Rules

```python
# Add custom validator
class CustomValidator:
    def validate_business_rules(self, code: str) -> ValidationResult:
        # Custom business logic validation
        pass

# Integrate with main validator
generator.add_custom_validator(CustomValidator())
```

### Extending Knowledge Graph

```python
# Add new API documentation
with neo4j_session() as session:
    session.run("""
        CREATE (m:Module {name: 'my_api'})
        CREATE (f:Function {name: 'process_data', signature: 'process_data(data: List[str]) -> Dict'})
        CREATE (m)-[:DEFINES]->(f)
    """)
```

## 📈 Monitoring and Metrics

### Key Metrics to Track

1. **Generation Success Rate**: % of valid code generated
2. **Risk Distribution**: Distribution across risk levels
3. **Iteration Count**: Average iterations needed for valid code
4. **Common Failures**: Most frequent validation failures
5. **Template Usage**: Template vs AI generation usage

### Logging and Monitoring

```python
# Built-in logging
logger.info(f"Generated code with confidence: {validation.confidence}")
logger.warning(f"High risk code generated: {validation.risk_level}")

# Metrics collection
metrics = {
    "generation_time": time.time() - start_time,
    "iterations_used": iteration_count,
    "final_confidence": validation.confidence,
    "risk_level": validation.risk_level.value
}
```

## 🔗 Related Documentation

- [Project PRD](project_docs/final_python_debugging_utility_prd.md)
- [Example Code Components](example_code/README.md)
- [Integration Patterns](example_code/INTEGRATION_PSEUDOCODE.md)
- [Task Master Integration](CLAUDE.md)

## 🤝 Contributing

1. **Add New Templates**: Create templates for common patterns
2. **Improve Validation**: Add new hallucination patterns
3. **Extend Knowledge Graph**: Add API documentation
4. **Create Integrations**: Build IDE plugins, CI/CD integrations

## 📄 License

This framework is part of the Python Debug Tool project and follows the same licensing terms.

---

*This framework provides deterministic, validated AI code generation by leveraging knowledge graphs, pattern detection, and iterative refinement to eliminate hallucinations and ensure code quality.*