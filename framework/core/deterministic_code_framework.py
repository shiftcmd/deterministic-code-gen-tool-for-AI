#!/usr/bin/env python3
"""
Deterministic AI Code Generation Framework

This framework leverages Neo4j knowledge graphs, embeddings, and multi-layer validation
to generate clean, hallucination-free, executable code.
"""

import json
import ast
import re
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path
import openai
from sentence_transformers import SentenceTransformer
import chromadb
from neo4j import GraphDatabase
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for generated code"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GenerationType(Enum):
    """Type of code generation approach"""
    TEMPLATE = "template"
    AI_GUIDED = "ai_guided"
    HYBRID = "hybrid"


@dataclass
class ValidationResult:
    """Result of code validation"""
    valid: bool
    confidence: float
    risk_level: RiskLevel
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeTemplate:
    """Code template definition"""
    name: str
    description: str
    template: str
    parameters: List[str]
    validation_rules: List[str]
    tags: Set[str] = field(default_factory=set)


class KnowledgeGraphValidator:
    """Validates code against Neo4j knowledge graph"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
    def validate_api_exists(self, module: str, function: str) -> bool:
        """Check if API exists in knowledge graph"""
        query = """
        MATCH (m:Module {name: $module})-[:DEFINES]->(f:Function {name: $function})
        RETURN COUNT(f) > 0 as exists
        """
        with self.driver.session() as session:
            result = session.run(query, module=module, function=function)
            return result.single()["exists"]
    
    def get_function_signature(self, module: str, function: str) -> Optional[Dict]:
        """Get function signature from knowledge graph"""
        query = """
        MATCH (m:Module {name: $module})-[:DEFINES]->(f:Function {name: $function})
        RETURN f.signature as signature, f.parameters as parameters, 
               f.return_type as return_type, f.docstring as docstring
        """
        with self.driver.session() as session:
            result = session.run(query, module=module, function=function)
            record = result.single()
            if record:
                return {
                    "signature": record["signature"],
                    "parameters": record["parameters"],
                    "return_type": record["return_type"],
                    "docstring": record["docstring"]
                }
        return None
    
    def get_available_apis(self, context: str = None) -> List[Dict]:
        """Get available APIs based on context"""
        query = """
        MATCH (m:Module)-[:DEFINES]->(f:Function)
        WHERE m.domain = $context OR $context IS NULL
        RETURN m.name as module, collect({
            name: f.name,
            signature: f.signature,
            description: f.docstring
        }) as functions
        LIMIT 100
        """
        with self.driver.session() as session:
            result = session.run(query, context=context)
            return [dict(record) for record in result]
    
    def validate_relationships(self, code_ast: ast.AST) -> ValidationResult:
        """Validate code relationships against knowledge graph"""
        issues = []
        
        # Extract relationships from AST
        for node in ast.walk(code_ast):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not self._module_exists(alias.name):
                        issues.append(f"Module '{alias.name}' not found in knowledge graph")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and not self._module_exists(node.module):
                    issues.append(f"Module '{node.module}' not found in knowledge graph")
            
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # Validate method calls
                    if isinstance(node.func.value, ast.Name):
                        obj_name = node.func.value.id
                        method_name = node.func.attr
                        if not self._method_exists(obj_name, method_name):
                            issues.append(f"Method '{obj_name}.{method_name}' not found")
        
        confidence = 1.0 - (len(issues) * 0.1)
        risk_level = self._calculate_risk_level(len(issues))
        
        return ValidationResult(
            valid=len(issues) == 0,
            confidence=max(0, confidence),
            risk_level=risk_level,
            issues=issues
        )
    
    def _module_exists(self, module_name: str) -> bool:
        """Check if module exists in knowledge graph"""
        query = "MATCH (m:Module {name: $name}) RETURN COUNT(m) > 0 as exists"
        with self.driver.session() as session:
            result = session.run(query, name=module_name)
            return result.single()["exists"]
    
    def _method_exists(self, class_name: str, method_name: str) -> bool:
        """Check if method exists for class"""
        query = """
        MATCH (c:Class {name: $class_name})-[:DEFINES]->(m:Method {name: $method_name})
        RETURN COUNT(m) > 0 as exists
        """
        with self.driver.session() as session:
            result = session.run(query, class_name=class_name, method=method_name)
            return result.single()["exists"]
    
    def _calculate_risk_level(self, issue_count: int) -> RiskLevel:
        """Calculate risk level based on issue count"""
        if issue_count == 0:
            return RiskLevel.LOW
        elif issue_count <= 2:
            return RiskLevel.MEDIUM
        elif issue_count <= 5:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL


class HallucinationDetector:
    """Detects AI hallucinations in generated code"""
    
    # Common hallucination patterns
    HALLUCINATION_PATTERNS = [
        # Fake method patterns
        (r'\.auto_[a-zA-Z_]+\(', "Suspicious 'auto_' method"),
        (r'\.smart_[a-zA-Z_]+\(', "Suspicious 'smart_' method"),
        (r'\.enhanced_[a-zA-Z_]+\(', "Suspicious 'enhanced_' method"),
        (r'\.optimize_automatically\(', "Suspicious automatic optimization"),
        
        # Non-existent string methods
        (r'\.strip_all\(', "Non-existent string method 'strip_all'"),
        (r'\.remove_whitespace\(', "Non-existent string method 'remove_whitespace'"),
        
        # Fake parameters
        (r'auto_detect\s*=\s*True', "Suspicious 'auto_detect' parameter"),
        (r'smart_mode\s*=\s*True', "Suspicious 'smart_mode' parameter"),
        
        # Common AI inventions
        (r'from\s+utils\.helpers\s+import', "Generic 'utils.helpers' import"),
        (r'import\s+magic', "Suspicious 'magic' import"),
    ]
    
    def detect_hallucinations(self, code: str) -> ValidationResult:
        """Detect potential hallucinations in code"""
        issues = []
        
        for pattern, description in self.HALLUCINATION_PATTERNS:
            if re.search(pattern, code):
                issues.append(description)
        
        # Check for placeholder comments
        if re.search(r'#\s*TODO:|#\s*FIXME:|#\s*Your code here', code):
            issues.append("Contains placeholder comments")
        
        # Check for ellipsis in actual code
        if '...' in code and not inside_string_or_comment(code, '...'):
            issues.append("Contains ellipsis in code body")
        
        confidence = 1.0 - (len(issues) * 0.15)
        risk_level = self._calculate_risk(issues)
        
        return ValidationResult(
            valid=len(issues) == 0,
            confidence=max(0, confidence),
            risk_level=risk_level,
            issues=issues
        )
    
    def _calculate_risk(self, issues: List[str]) -> RiskLevel:
        """Calculate risk based on hallucination patterns found"""
        critical_patterns = ["magic import", "ellipsis in code"]
        
        if any(pattern in issue for issue in issues for pattern in critical_patterns):
            return RiskLevel.CRITICAL
        elif len(issues) > 3:
            return RiskLevel.HIGH
        elif len(issues) > 0:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW


class TemplateEngine:
    """Manages code templates for deterministic generation"""
    
    def __init__(self):
        self.templates: Dict[str, CodeTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default code templates"""
        # API Client Template
        self.templates["api_client"] = CodeTemplate(
            name="api_client",
            description="REST API client with error handling",
            template='''import requests
from typing import Dict, Any, Optional
import logging

class {class_name}:
    """API client for {service_name}"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
        self.logger = logging.getLogger(__name__)
    
    def {method_name}(self, {parameters}) -> Dict[str, Any]:
        """{method_docstring}"""
        try:
            response = self.session.{http_method}(
                f"{self.base_url}/{endpoint}",
                {request_kwargs}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise
''',
            parameters=["class_name", "service_name", "method_name", "parameters", 
                       "method_docstring", "http_method", "endpoint", "request_kwargs"],
            validation_rules=["valid_python_identifier", "http_method_valid"]
        )
        
        # Data Processor Template
        self.templates["data_processor"] = CodeTemplate(
            name="data_processor",
            description="Data processing pipeline with validation",
            template='''from typing import List, Dict, Any
import pandas as pd
from dataclasses import dataclass

@dataclass
class {processor_name}:
    """{processor_description}"""
    
    def process(self, data: {input_type}) -> {output_type}:
        """Process input data and return results"""
        # Validate input
        self._validate_input(data)
        
        # Transform data
        result = self._transform(data)
        
        # Validate output
        self._validate_output(result)
        
        return result
    
    def _validate_input(self, data: {input_type}) -> None:
        """Validate input data"""
        {input_validation}
    
    def _transform(self, data: {input_type}) -> {output_type}:
        """Transform data"""
        {transformation_logic}
    
    def _validate_output(self, result: {output_type}) -> None:
        """Validate output data"""
        {output_validation}
''',
            parameters=["processor_name", "processor_description", "input_type", 
                       "output_type", "input_validation", "transformation_logic", 
                       "output_validation"],
            validation_rules=["valid_type_annotation", "valid_python_code"]
        )
    
    def get_template(self, name: str) -> Optional[CodeTemplate]:
        """Get template by name"""
        return self.templates.get(name)
    
    def generate_from_template(self, template_name: str, parameters: Dict[str, str]) -> str:
        """Generate code from template"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Validate all required parameters are provided
        missing = set(template.parameters) - set(parameters.keys())
        if missing:
            raise ValueError(f"Missing parameters: {missing}")
        
        # Generate code
        code = template.template
        for param, value in parameters.items():
            code = code.replace(f"{{{param}}}", value)
        
        return code


class DeterministicCodeGenerator:
    """Main framework for deterministic AI code generation"""
    
    def __init__(self, 
                 neo4j_uri: str,
                 neo4j_user: str,
                 neo4j_password: str,
                 pg_connection_string: str,
                 chroma_collection_name: str = "code_embeddings",
                 openai_api_key: Optional[str] = None):
        
        # Initialize components
        self.kg_validator = KnowledgeGraphValidator(neo4j_uri, neo4j_user, neo4j_password)
        self.hallucination_detector = HallucinationDetector()
        self.template_engine = TemplateEngine()
        
        # Initialize embeddings
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.create_collection(
            name=chroma_collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # PostgreSQL connection
        self.pg_conn = psycopg2.connect(pg_connection_string)
        
        # OpenAI setup
        if openai_api_key:
            openai.api_key = openai_api_key
    
    def generate_code(self, 
                     requirement: str,
                     generation_type: GenerationType = GenerationType.HYBRID,
                     context_files: Optional[List[str]] = None,
                     max_iterations: int = 3) -> Tuple[str, ValidationResult]:
        """Generate code based on requirement"""
        
        logger.info(f"Generating code for: {requirement}")
        
        # Step 1: Analyze requirement and determine approach
        approach = self._determine_approach(requirement, generation_type)
        
        # Step 2: Gather context
        context = self._gather_context(requirement, context_files)
        
        # Step 3: Generate code based on approach
        if approach == GenerationType.TEMPLATE:
            code = self._generate_from_template(requirement, context)
        elif approach == GenerationType.AI_GUIDED:
            code = self._generate_with_ai(requirement, context, max_iterations)
        else:  # HYBRID
            code = self._generate_hybrid(requirement, context, max_iterations)
        
        # Step 4: Final validation
        validation = self._validate_code(code)
        
        return code, validation
    
    def _determine_approach(self, requirement: str, preferred_type: GenerationType) -> GenerationType:
        """Determine best generation approach"""
        # Check if requirement matches a template
        template_keywords = {
            "api client": "api_client",
            "rest client": "api_client",
            "data processor": "data_processor",
            "data pipeline": "data_processor"
        }
        
        requirement_lower = requirement.lower()
        for keyword, template in template_keywords.items():
            if keyword in requirement_lower:
                return GenerationType.TEMPLATE
        
        # Use preferred type if no template match
        return preferred_type
    
    def _gather_context(self, requirement: str, context_files: Optional[List[str]]) -> Dict[str, Any]:
        """Gather relevant context from knowledge graph and embeddings"""
        context = {
            "requirement": requirement,
            "available_apis": [],
            "similar_code": [],
            "architectural_patterns": []
        }
        
        # Get available APIs from knowledge graph
        context["available_apis"] = self.kg_validator.get_available_apis()
        
        # Find similar code using embeddings
        requirement_embedding = self.embedder.encode(requirement)
        results = self.collection.query(
            query_embeddings=[requirement_embedding.tolist()],
            n_results=5
        )
        
        if results and results['documents']:
            context["similar_code"] = results['documents'][0]
        
        # Load context files if provided
        if context_files:
            context["context_files"] = []
            for file_path in context_files:
                try:
                    with open(file_path, 'r') as f:
                        context["context_files"].append({
                            "path": file_path,
                            "content": f.read()
                        })
                except Exception as e:
                    logger.warning(f"Failed to load context file {file_path}: {e}")
        
        return context
    
    def _generate_from_template(self, requirement: str, context: Dict[str, Any]) -> str:
        """Generate code using templates"""
        # Extract parameters from requirement using AI
        parameters = self._extract_template_parameters(requirement, context)
        
        # Determine template
        template_name = self._identify_template(requirement)
        
        # Generate code
        return self.template_engine.generate_from_template(template_name, parameters)
    
    def _generate_with_ai(self, requirement: str, context: Dict[str, Any], max_iterations: int) -> str:
        """Generate code using AI with validation feedback loop"""
        
        iteration = 0
        code = ""
        validation_feedback = []
        
        while iteration < max_iterations:
            # Build prompt with context and feedback
            prompt = self._build_generation_prompt(requirement, context, validation_feedback)
            
            # Generate code
            code = self._call_ai_api(prompt)
            
            # Validate generated code
            validation = self._validate_code(code)
            
            if validation.valid or validation.risk_level == RiskLevel.LOW:
                break
            
            # Add validation feedback for next iteration
            validation_feedback = validation.issues
            iteration += 1
            
            logger.info(f"Iteration {iteration}: Validation failed, refining...")
        
        return code
    
    def _generate_hybrid(self, requirement: str, context: Dict[str, Any], max_iterations: int) -> str:
        """Generate code using hybrid approach"""
        # Try template first
        try:
            template_name = self._identify_template(requirement)
            if template_name:
                parameters = self._extract_template_parameters(requirement, context)
                code = self.template_engine.generate_from_template(template_name, parameters)
                
                # Validate template output
                validation = self._validate_code(code)
                if validation.valid:
                    return code
        except Exception as e:
            logger.info(f"Template generation failed: {e}, falling back to AI")
        
        # Fall back to AI generation
        return self._generate_with_ai(requirement, context, max_iterations)
    
    def _validate_code(self, code: str) -> ValidationResult:
        """Comprehensive code validation"""
        issues = []
        validations = []
        
        # Step 1: AST validation
        try:
            tree = ast.parse(code)
            ast_valid = True
        except SyntaxError as e:
            ast_valid = False
            issues.append(f"Syntax error: {e}")
        
        # Step 2: Knowledge graph validation
        if ast_valid:
            kg_validation = self.kg_validator.validate_relationships(tree)
            validations.append(kg_validation)
            issues.extend(kg_validation.issues)
        
        # Step 3: Hallucination detection
        hallucination_validation = self.hallucination_detector.detect_hallucinations(code)
        validations.append(hallucination_validation)
        issues.extend(hallucination_validation.issues)
        
        # Calculate overall metrics
        avg_confidence = sum(v.confidence for v in validations) / len(validations) if validations else 0
        max_risk = max((v.risk_level for v in validations), default=RiskLevel.LOW)
        
        return ValidationResult(
            valid=len(issues) == 0,
            confidence=avg_confidence,
            risk_level=max_risk,
            issues=issues,
            metadata={
                "ast_valid": ast_valid,
                "validations": len(validations)
            }
        )
    
    def _build_generation_prompt(self, requirement: str, context: Dict[str, Any], 
                                feedback: List[str] = None) -> str:
        """Build AI generation prompt with context"""
        
        # Extract available APIs
        api_list = []
        for api in context.get("available_apis", [])[:20]:  # Limit to 20 APIs
            api_list.append(f"- {api['module']}.{api['functions'][0]['name']}: {api['functions'][0].get('description', 'N/A')}")
        
        prompt = f"""Generate Python code for the following requirement:

REQUIREMENT: {requirement}

CONSTRAINTS:
1. Use ONLY the APIs listed below (do not invent new ones)
2. Include proper error handling
3. Add type hints for all functions
4. Follow PEP 8 style guidelines
5. Do not use placeholder comments like TODO or FIXME
6. Do not use ellipsis (...) in the code

AVAILABLE APIS:
{chr(10).join(api_list)}

"""
        
        # Add similar code examples if available
        if context.get("similar_code"):
            prompt += f"\nSIMILAR CODE EXAMPLES:\n{context['similar_code'][0][:500]}...\n"
        
        # Add validation feedback if this is a retry
        if feedback:
            prompt += f"\nPREVIOUS VALIDATION ISSUES TO FIX:\n"
            for issue in feedback:
                prompt += f"- {issue}\n"
        
        prompt += "\nCODE:\n```python\n"
        
        return prompt
    
    def _call_ai_api(self, prompt: str) -> str:
        """Call OpenAI API for code generation"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a Python code generator. Generate only valid, executable Python code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Lower temperature for more deterministic output
                max_tokens=2000
            )
            
            # Extract code from response
            code = response.choices[0].message.content
            
            # Remove markdown code blocks if present
            code = re.sub(r'^```python\n', '', code)
            code = re.sub(r'\n```$', '', code)
            
            return code.strip()
            
        except Exception as e:
            logger.error(f"AI API call failed: {e}")
            raise
    
    def _extract_template_parameters(self, requirement: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Extract template parameters using AI"""
        # This would use AI to extract structured parameters from the requirement
        # For now, return a simple example
        return {
            "class_name": "APIClient",
            "service_name": "Example Service",
            "method_name": "get_data",
            "parameters": "resource_id: str",
            "method_docstring": "Retrieve data for a specific resource",
            "http_method": "get",
            "endpoint": "resources/{resource_id}",
            "request_kwargs": "params={'format': 'json'}"
        }
    
    def _identify_template(self, requirement: str) -> Optional[str]:
        """Identify which template to use based on requirement"""
        requirement_lower = requirement.lower()
        
        if "api client" in requirement_lower or "rest client" in requirement_lower:
            return "api_client"
        elif "data processor" in requirement_lower or "data pipeline" in requirement_lower:
            return "data_processor"
        
        return None
    
    def save_generated_code(self, code: str, validation: ValidationResult, metadata: Dict[str, Any]):
        """Save generated code with validation results"""
        with self.pg_conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO generated_code 
                (code, valid, confidence, risk_level, issues, metadata, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, (
                code,
                validation.valid,
                validation.confidence,
                validation.risk_level.value,
                json.dumps(validation.issues),
                json.dumps(metadata)
            ))
            self.pg_conn.commit()
            return cursor.fetchone()[0]


def inside_string_or_comment(code: str, pattern: str) -> bool:
    """Check if pattern is inside a string or comment"""
    # Simplified check - in production, use proper AST analysis
    lines = code.split('\n')
    for line in lines:
        if pattern in line:
            # Check if it's in a comment
            if '#' in line and line.index('#') < line.index(pattern):
                return True
            # Check if it's in a string (simplified)
            if (line.count('"') >= 2 or line.count("'") >= 2):
                return True
    return False


# Example usage
if __name__ == "__main__":
    # Initialize the framework
    generator = DeterministicCodeGenerator(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
        pg_connection_string="postgresql://user:password@localhost/codedb",
        openai_api_key="your-api-key"
    )
    
    # Example 1: Generate API client
    requirement = "Create a REST API client for user management with get, create, update, and delete methods"
    code, validation = generator.generate_code(requirement, GenerationType.TEMPLATE)
    
    print(f"Generated Code:\n{code}")
    print(f"\nValidation: {validation}")
    
    # Example 2: Generate with AI
    requirement = "Create a function that processes CSV files and detects anomalies using statistical methods"
    code, validation = generator.generate_code(requirement, GenerationType.AI_GUIDED)
    
    print(f"\nGenerated Code:\n{code}")
    print(f"\nValidation: {validation}")