#!/usr/bin/env python3
"""
Demonstration of the Deterministic AI Code Generation Framework

This script shows practical examples of how to use the framework for 
generating clean, validated Python code.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

# Mock classes for demonstration (replace with actual imports when services are available)
class MockValidator:
    """Mock validator for demonstration"""
    def validate_file(self, filepath: str):
        return True, [], {"risk_level": "low"}

class MockGenerator:
    """Mock generator for demonstration"""
    def generate_code(self, requirement: str, **kwargs):
        # Example generated code based on requirement
        if "api client" in requirement.lower():
            code = '''import requests
from typing import Dict, Any, Optional

class APIClient:
    """REST API client with error handling"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request to API endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
'''
        elif "email validator" in requirement.lower():
            code = '''import re
from typing import bool

def validate_email(email: str) -> bool:
    """Validate email address format using regex pattern"""
    if not isinstance(email, str):
        return False
    
    # Email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_email_strict(email: str) -> bool:
    """Strict email validation with additional checks"""
    if not validate_email(email):
        return False
    
    # Additional checks
    local, domain = email.split('@')
    
    # Local part shouldn't start or end with dots
    if local.startswith('.') or local.endswith('.'):
        return False
    
    # Domain shouldn't start or end with hyphens
    if domain.startswith('-') or domain.endswith('-'):
        return False
    
    return True
'''
        elif "data processor" in requirement.lower():
            code = '''import pandas as pd
from typing import List, Dict, Any
from pathlib import Path

class CSVProcessor:
    """Process CSV files with validation and error handling"""
    
    def __init__(self):
        self.processed_files = []
    
    def process_file(self, filepath: str) -> Dict[str, Any]:
        """Process a single CSV file"""
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        if not path.suffix.lower() == '.csv':
            raise ValueError(f"Expected CSV file, got: {path.suffix}")
        
        try:
            # Read CSV with error handling
            df = pd.read_csv(filepath)
            
            # Basic validation
            if df.empty:
                raise ValueError("CSV file is empty")
            
            # Process data
            result = {
                "filepath": str(path),
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "dtypes": df.dtypes.to_dict(),
                "null_counts": df.isnull().sum().to_dict()
            }
            
            self.processed_files.append(result)
            return result
            
        except Exception as e:
            raise Exception(f"Failed to process {filepath}: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all processed files"""
        return {
            "total_files": len(self.processed_files),
            "total_rows": sum(f["rows"] for f in self.processed_files),
            "files": self.processed_files
        }
'''
        else:
            code = f'''# Generated code for: {requirement}

def generated_function():
    """Auto-generated function based on requirement"""
    # Implementation would be generated based on specific requirement
    pass
'''
        
        # Mock validation result
        class MockValidation:
            def __init__(self):
                self.valid = True
                self.confidence = 0.95
                self.risk_level = type('RiskLevel', (), {'value': 'low'})()
                self.issues = []
                self.suggestions = []
        
        return code, MockValidation()


def demonstrate_api_client_generation():
    """Demonstrate API client generation"""
    print("🔧 Demo 1: API Client Generation")
    print("-" * 40)
    
    requirement = "Create a REST API client for user management with GET and POST methods"
    print(f"Requirement: {requirement}")
    
    # Mock generation
    generator = MockGenerator()
    code, validation = generator.generate_code(requirement)
    
    print(f"\n✅ Generated code (Confidence: {validation.confidence:.1%}):")
    print("```python")
    print(code)
    print("```")
    
    # Demonstrate validation
    validator = MockValidator()
    valid, issues, metadata = validator.validate_file("generated_api_client.py")
    
    if valid:
        print(f"✅ Validation passed - Risk level: {metadata['risk_level']}")
    else:
        print(f"❌ Validation failed: {issues}")


def demonstrate_email_validator():
    """Demonstrate email validator generation"""
    print("\n🔧 Demo 2: Email Validator Generation")
    print("-" * 40)
    
    requirement = "Create an email validator function with strict validation rules"
    print(f"Requirement: {requirement}")
    
    generator = MockGenerator()
    code, validation = generator.generate_code(requirement)
    
    print(f"\n✅ Generated code (Confidence: {validation.confidence:.1%}):")
    print("```python")
    print(code)
    print("```")
    
    # Show how the generated code would work
    print("\n🧪 Testing generated code:")
    
    # Extract and execute the generated function (in real usage)
    test_emails = [
        "user@example.com",      # Valid
        "test.email@domain.co",  # Valid
        "invalid-email",         # Invalid
        "@domain.com",           # Invalid
        "user@.com"             # Invalid
    ]
    
    print("Test results (simulated):")
    for email in test_emails:
        # Simulate validation (in real usage, we'd execute the generated code)
        is_valid = "@" in email and "." in email.split("@")[-1] and not email.startswith("@")
        status = "✅ Valid" if is_valid else "❌ Invalid"
        print(f"  {email:<20} → {status}")


def demonstrate_data_processor():
    """Demonstrate data processor generation"""
    print("\n🔧 Demo 3: Data Processor Generation")
    print("-" * 40)
    
    requirement = "Create a CSV data processor with validation and error handling"
    print(f"Requirement: {requirement}")
    
    generator = MockGenerator()
    code, validation = generator.generate_code(requirement)
    
    print(f"\n✅ Generated code (Confidence: {validation.confidence:.1%}):")
    print("```python")
    print(code[:500] + "..." if len(code) > 500 else code)
    print("```")
    
    print("\n🧪 Simulated usage:")
    print("processor = CSVProcessor()")
    print("result = processor.process_file('data.csv')")
    print("# Result: {'filepath': 'data.csv', 'rows': 100, 'columns': 5, ...}")


def demonstrate_validation_levels():
    """Demonstrate different validation risk levels"""
    print("\n🔧 Demo 4: Validation Risk Levels")
    print("-" * 40)
    
    examples = {
        "low_risk": {
            "code": '''import json
def parse_data(data: str) -> dict:
    return json.loads(data)
''',
            "issues": [],
            "risk": "low"
        },
        "medium_risk": {
            "code": '''import requests
def fetch_data(url):  # Missing type hints
    return requests.get(url).json()  # No error handling
''',
            "issues": ["Missing type hints", "No error handling"],
            "risk": "medium"
        },
        "high_risk": {
            "code": '''import magic_library  # Non-existent library
def auto_solve_problem(data):  # Suspicious naming
    return magic_library.solve(data)
''',
            "issues": ["Unknown module: magic_library", "Suspicious 'auto_' prefix"],
            "risk": "high"
        },
        "critical_risk": {
            "code": '''def broken_function(
    # Syntax error - missing closing parenthesis
    return "incomplete"
''',
            "issues": ["Syntax error: unexpected EOF", "Incomplete function definition"],
            "risk": "critical"
        }
    }
    
    for risk_level, example in examples.items():
        print(f"\n{risk_level.upper().replace('_', ' ')} Example:")
        print(f"Risk Level: {example['risk']}")
        if example['issues']:
            print(f"Issues: {', '.join(example['issues'])}")
        print("Code:")
        print("```python")
        print(example['code'])
        print("```")


def demonstrate_template_vs_ai():
    """Demonstrate template vs AI generation approaches"""
    print("\n🔧 Demo 5: Template vs AI Generation")
    print("-" * 40)
    
    print("🏗️  TEMPLATE APPROACH (Most Deterministic)")
    print("✅ Pros: Guaranteed structure, fast, predictable")
    print("❌ Cons: Limited flexibility, requires predefined patterns")
    
    template_example = '''# Template: api_client
class {class_name}:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def {method_name}(self, {parameters}) -> {return_type}:
        """{docstring}"""
        # Template-based implementation
        pass
'''
    
    print("\nTemplate Structure:")
    print("```python")
    print(template_example)
    print("```")
    
    print("\n🤖 AI-GUIDED APPROACH (Most Flexible)")
    print("✅ Pros: Handles complex requirements, creative solutions")
    print("❌ Cons: Potential hallucinations, less predictable")
    
    print("\nAI Generation Process:")
    print("1. Analyze requirement")
    print("2. Query knowledge graph for context")
    print("3. Generate code with constraints")
    print("4. Validate against multiple layers")
    print("5. Refine based on feedback")
    
    print("\n🔄 HYBRID APPROACH (Balanced)")
    print("✅ Pros: Best of both worlds")
    print("1. Try template matching first")
    print("2. Fall back to AI if no template matches")
    print("3. Use AI to fill template parameters")


def demonstrate_integration_workflow():
    """Demonstrate development workflow integration"""
    print("\n🔧 Demo 6: Development Workflow Integration")
    print("-" * 40)
    
    workflow_steps = [
        "1. 📝 Developer describes requirement",
        "2. 🤖 Framework generates code",
        "3. 🔍 Multi-layer validation runs",
        "4. ✅ Code approved or refined",
        "5. 💾 Code saved to project",
        "6. 🔗 Pre-commit hook validates",
        "7. 🚀 CI/CD pipeline checks quality"
    ]
    
    print("Integrated Development Workflow:")
    for step in workflow_steps:
        print(f"  {step}")
    
    print("\n🛠️ Available Tools:")
    tools = {
        "ai_code_assistant.py": "Interactive code generation",
        "dev_validator.py": "File validation",
        "pre-commit hooks": "Automatic validation on commit",
        "CI/CD integration": "Pipeline quality checks"
    }
    
    for tool, description in tools.items():
        print(f"  • {tool:<20} - {description}")


def main():
    """Run all demonstrations"""
    print("🚀 Deterministic AI Code Generation Framework")
    print("=" * 60)
    print("Live Demonstrations")
    print("=" * 60)
    
    try:
        demonstrate_api_client_generation()
        demonstrate_email_validator()
        demonstrate_data_processor()
        demonstrate_validation_levels()
        demonstrate_template_vs_ai()
        demonstrate_integration_workflow()
        
        print("\n" + "=" * 60)
        print("🎉 All demonstrations completed!")
        print("\n📚 Next Steps:")
        print("  1. Run: python setup_framework.py")
        print("  2. Configure your API keys")
        print("  3. Try: python ai_code_assistant.py --interactive")
        print("  4. Read: DETERMINISTIC_AI_FRAMEWORK.md")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")


if __name__ == "__main__":
    main()