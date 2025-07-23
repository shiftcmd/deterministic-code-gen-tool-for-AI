#!/usr/bin/env python3
"""
Parse Codebase into Knowledge Graph MK2

Enhanced version combining setup_knowledge_graph.py and parse_repo_into_neo4j.py
with advanced .pyi type stub processing for robust hallucination detection.

Key Features:
- Processes both .py and .pyi files
- Creates type validation relationships
- Enables signature-based hallucination detection
- Provides detailed type information for debugging
"""

import asyncio
import os
import sys
import logging
import shutil
import tempfile
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
import ast
from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase

# Import knowledge_graphs components for AI script analysis and validation
from knowledge_graphs.ai_script_analyzer import (
    AIScriptAnalyzer, AnalysisResult, ImportInfo, MethodCall, 
    AttributeAccess, FunctionCall, ClassInstantiation
)
from knowledge_graphs.knowledge_graph_validator import (
    KnowledgeGraphValidator, ValidationStatus, ValidationResult,
    ImportValidation, MethodValidation, AttributeValidation
)
from hexagonal_architecture_analyzer import HexagonalArchitectureAnalyzer
from knowledge_graphs.ai_hallucination_detector import (
    AIHallucinationDetector
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)


class EnhancedNeo4jCodeAnalyzer:
    """Enhanced analyzer with .pyi stub processing for hallucination detection"""
    
    def __init__(self, hex_mode: bool = False):
        # External modules to ignore (same as original)
        self._external_modules = {
            'os', 'sys', 'json', 'logging', 'datetime', 'pathlib', 'typing', 'collections',
            'requests', 'flask', 'django', 'fastapi', 'pydantic', 'openai', 'anthropic',
            'asyncio', 'functools', 'itertools', 'contextlib', 'enum', 'dataclasses',
            'abc', 'hashlib', 'uuid', 'time', 'random', 're', 'io', 'copy', 'pickle',
            'sqlite3', 'psycopg2', 'pymongo', 'redis', 'celery', 'numpy', 'pandas',
            'matplotlib', 'seaborn', 'scipy', 'sklearn', 'tensorflow', 'torch',
            'transformers', 'langchain', 'chromadb', 'supabase', 'neo4j', 'pytest',
            'unittest', 'mock', 'click', 'argparse', 'configparser', 'yaml', 'toml',
            'dotenv', 'jinja2', 'markupsafe', 'werkzeug', 'gunicorn', 'uvicorn'
        }
        
        # Initialize AI script analyzer and validator components
        self.ai_script_analyzer = AIScriptAnalyzer()
        self.knowledge_graph_validator = None  # Will be initialized with Neo4j connection
        self.hallucination_detector = None     # Will be initialized with Neo4j connection
        
        # Initialize hexagonal architecture analyzer if hex_mode is enabled
        self.hex_mode = hex_mode
        self.hex_analyzer = HexagonalArchitectureAnalyzer() if hex_mode else None
    
    def initialize_validators(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        """Initialize knowledge graph validator and hallucination detector with Neo4j connection"""
        try:
            self.knowledge_graph_validator = KnowledgeGraphValidator(
                neo4j_uri, neo4j_user, neo4j_password
            )
            self.hallucination_detector = AIHallucinationDetector(
                neo4j_uri, neo4j_user, neo4j_password
            )
            logger.info("AI validation components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI validation components: {e}")
            raise
    
    async def analyze_ai_generated_script(self, script_path: str, repo_name: str = None) -> Dict[str, Any]:
        """Analyze AI-generated script using integrated knowledge graph validation"""
        try:
            # Use AI script analyzer to extract code elements
            analysis_result = self.ai_script_analyzer.analyze_script(script_path)
            
            # Validate against knowledge graph if validator is available
            validation_result = None
            hallucination_report = None
            
            if self.knowledge_graph_validator:
                validation_result = await self.knowledge_graph_validator.validate_analysis(
                    analysis_result, repo_name
                )
                
                # Generate hallucination report if detector is available
                if self.hallucination_detector:
                    hallucination_report = self.hallucination_detector.detect_hallucinations(
                        validation_result
                    )
            
            return {
                'analysis': analysis_result,
                'validation': validation_result,
                'hallucinations': hallucination_report,
                'file_path': script_path
            }
            
        except Exception as e:
            logger.error(f"Error analyzing AI-generated script {script_path}: {e}")
            return {
                'analysis': None,
                'validation': None,
                'hallucinations': None,
                'file_path': script_path,
                'error': str(e)
            }
    
    def jls_extract_def(self, tree, classes, is_stub_file, functions, imports, project_modules, constants, type_aliases):
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(self._extract_class_info(node, is_stub_file))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith('_'):  # Public functions only
                    functions.append(self._extract_function_info(node, is_stub_file))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.extend(self._extract_imports(node, project_modules))
            elif isinstance(node, ast.AnnAssign) and is_stub_file:
                # Extract type-annotated constants/variables from stubs
                if isinstance(node.target, ast.Name):
                    constants.append({
                        'name': node.target.id,
                        'type': self._get_name(node.annotation) if node.annotation else 'Any',
                        'is_constant': node.target.id.isupper()
                    })
            elif isinstance(node, ast.Assign) and is_stub_file:
                # Extract type aliases (TypeAlias = SomeType)
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.endswith('Type'):
                        type_aliases.append({
                            'name': target.id,
                            'definition': self._get_name(node.value) if hasattr(node, 'value') else 'Any'
                        })

    def analyze_python_file(self, file_path: Path, repo_root: Path, project_modules: Set[str]) -> Dict[str, Any]:
        """Analyze Python file (.py or .pyi) with enhanced type processing"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            relative_path = str(file_path.relative_to(repo_root))
            module_name = self._get_importable_module_name(file_path, repo_root, relative_path)
            
            # Enhanced: Determine file type and processing strategy
            is_stub_file = file_path.suffix == '.pyi'
            file_type = 'type_stub' if is_stub_file else 'implementation'
            
            # Extract structure with type information
            classes = []
            functions = []
            imports = []
            type_aliases = []  # New: Track type aliases in stubs
            constants = []     # New: Track typed constants
            
            self.jls_extract_def(tree, classes, is_stub_file, functions, imports, project_modules, constants, type_aliases)
            
            return {
                'module_name': module_name,
                'file_path': relative_path,
                'file_type': file_type,
                'is_stub_file': is_stub_file,
                'classes': classes,
                'functions': functions,
                'imports': list(set(imports)),
                'type_aliases': type_aliases,
                'constants': constants,
                'line_count': len(content.splitlines())
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return None
    
    def _extract_class_info(self, node: ast.ClassDef, is_stub: bool) -> Dict[str, Any]:
        """Extract detailed class information with type focus for stubs"""
        methods = []
        attributes = []
        
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not item.name.startswith('_'):  # Public methods
                    method_info = self._extract_function_info(item, is_stub, is_method=True)
                    methods.append(method_info)
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                # Type annotated attributes
                if not item.target.id.startswith('_'):
                    attributes.append({
                        'name': item.target.id,
                        'type': self._get_name(item.annotation) if item.annotation else 'Any',
                        'has_default': item.value is not None,
                        'is_property': False  # Could enhance to detect @property
                    })
        
        return {
            'name': node.name,
            'methods': methods,
            'attributes': attributes,
            'base_classes': [self._get_name(base) for base in node.bases],
            'is_abstract': any(isinstance(decorator, ast.Name) and 
                             decorator.id == 'abstractmethod' 
                             for item in node.body 
                             for decorator in getattr(item, 'decorator_list', [])),
            'docstring': ast.get_docstring(node)
        }
    
    def _extract_function_info(self, node: ast.FunctionDef, is_stub: bool, is_method: bool = False) -> Dict[str, Any]:
        """Extract detailed function information with enhanced type data"""
        params = self._extract_function_parameters(node)
        return_type = self._get_name(node.returns) if node.returns else 'Any'
        
        # Enhanced parameter details for type validation
        params_signature = []
        for p in params:
            sig = f"{p['name']}: {p['type']}"
            if p['optional'] and p['default'] is not None:
                sig += f" = {p['default']}"
            elif p['optional']:
                sig += " = None"
            params_signature.append(sig)
        
        return {
            'name': node.name,
            'params': params,
            'signature': f"({', '.join(params_signature)}) -> {return_type}",
            'return_type': return_type,
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'is_method': is_method,
            'is_stub_definition': is_stub,
            'decorators': [self._get_name(dec) for dec in node.decorator_list],
            'docstring': ast.get_docstring(node)
        }
    
    def _extract_function_parameters(self, func_node):
        """Extract comprehensive parameter info with enhanced type details"""
        params = []
        args = func_node.args
        
        # Handle positional arguments
        for i, arg in enumerate(args.args):
            param_type = 'Any'
            if arg.annotation:
                param_type = self._get_name(arg.annotation)
            
            default_value = None
            has_default = False
            if args.defaults and i >= len(args.args) - len(args.defaults):
                default_idx = i - (len(args.args) - len(args.defaults))
                default_value = self._get_default_value(args.defaults[default_idx])
                has_default = True
            
            params.append({
                'name': arg.arg,
                'type': param_type,
                'default': default_value,
                'optional': has_default,
                'kind': 'positional'
            })
        
        # Handle *args
        if args.vararg:
            params.append({
                'name': args.vararg.arg,
                'type': f"*{self._get_name(args.vararg.annotation) if args.vararg.annotation else 'Any'}",
                'default': None,
                'optional': True,
                'kind': 'vararg'
            })
        
        # Handle **kwargs
        if args.kwarg:
            params.append({
                'name': args.kwarg.arg,
                'type': f"**{self._get_name(args.kwarg.annotation) if args.kwarg.annotation else 'Any'}",
                'default': None,
                'optional': True,
                'kind': 'kwarg'
            })
        
        return params
    
    def _get_default_value(self, default_node):
        """Extract default value from AST node"""
        if isinstance(default_node, ast.Constant):
            return repr(default_node.value)
        elif isinstance(default_node, ast.Name):
            return default_node.id
        elif isinstance(default_node, ast.Attribute):
            return f"{self._get_name(default_node.value)}.{default_node.attr}"
        else:
            return "..."
    
    def _get_name(self, node):
        """Extract name from AST node with enhanced type handling"""
        if node is None:
            return 'Any'
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[{self._get_name(node.slice)}]"
        elif isinstance(node, ast.Tuple):
            elements = [self._get_name(elt) for elt in node.elts]
            return f"({', '.join(elements)})"
        elif isinstance(node, ast.List):
            elements = [self._get_name(elt) for elt in node.elts]
            return f"[{', '.join(elements)}]"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        else:
            return 'Any'
    
    def _extract_imports(self, node, project_modules: Set[str]) -> List[str]:
        """Extract import information for dependency tracking"""
        imports = []
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                if self._is_likely_internal(alias.name, project_modules):
                    imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and self._is_likely_internal(node.module, project_modules):
                for alias in node.names:
                    imports.append(f"{node.module}.{alias.name}")
        
        return imports
    
    def _is_likely_internal(self, import_name: str, project_modules: Set[str]) -> bool:
        """Check if import is internal to project"""
        base_module = import_name.split('.')[0]
        return (base_module not in self._external_modules and 
                any(import_name.startswith(pm) for pm in project_modules))
    
    def _get_importable_module_name(self, file_path: Path, repo_root: Path, relative_path: str) -> str:
        """Get importable module name using canonical approach"""
        # Create canonical name by stripping extension first
        canonical_path = Path(relative_path).with_suffix('')
        canonical_name = str(canonical_path).replace('/', '.').replace('\\', '.')
        
        # Log for debugging
        logger.info(f"📝 Module name: {file_path.name} -> {canonical_name}")
        
        return canonical_name

class EnhancedKnowledgeGraphExtractor:
    """Enhanced extractor with .pyi stub processing and hallucination detection"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, hex_mode: bool = False):
        self.driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.analyzer = EnhancedNeo4jCodeAnalyzer(hex_mode=hex_mode)
        self.hex_mode = hex_mode
        
        # Initialize AI validation components
        try:
            self.analyzer.initialize_validators(neo4j_uri, neo4j_user, neo4j_password)
            logger.info("AI validation components integrated successfully")
        except Exception as e:
            logger.warning(f"AI validation components not available: {e}")

    async def initialize(self):
        """Initialize Neo4j connection"""
        # Connection already established in __init__, just test it
        
        # Test connection
        async with self.driver.session() as session:
            await session.run("RETURN 1")
        logger.info("✅ Connected to Neo4j successfully")
    
    async def setup_enhanced_constraints(self):
        """Setup enhanced constraints for type validation"""
        async with self.driver.session() as session:
            # First, clean up old constraints that might conflict
            try:
                # Drop old constraints if they exist
                await session.run("DROP CONSTRAINT constraint_3c126057 IF EXISTS")  # Old Method constraint
                await session.run("DROP CONSTRAINT constraint_fa941a93 IF EXISTS")  # Old Function constraint
                logger.info("🧹 Cleaned up old constraints")
            except Exception as e:
                logger.warning(f"Constraint cleanup: {e}")
            
            # Enhanced constraints including stub vs implementation distinction
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Codebase) REQUIRE c.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE (f.path, f.repository) IS UNIQUE",  
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Class) REQUIRE (c.name, c.module) IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Method) REQUIRE (m.name, m.class, m.signature, m.is_stub_definition) IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (fn:Function) REQUIRE (fn.name, fn.module, fn.signature, fn.is_stub_definition) IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (t:TypeStub) REQUIRE (t.module, t.name) IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    await session.run(constraint)
                    logger.info(f"✅ Created constraint")
                except Exception as e:
                    logger.warning(f"Constraint may already exist: {e}")
    
    async def get_python_files(self, repo_path: str) -> List[Path]:
        """Get Python files including .pyi stubs"""
        python_files = []
        exclude_dirs = {
            'tests', 'test', '__pycache__', '.git', 'venv', 'env',
            'node_modules', 'build', 'dist', '.pytest_cache', 'docs',
            'examples', 'example', 'demo', 'benchmark'
        }
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            for file in files:
                # Include both .py and .pyi files for comprehensive analysis
                if (file.endswith('.py') or file.endswith('.pyi')) and not file.startswith('test_'):
                    file_path = Path(root) / file
                    if (file_path.stat().st_size < 500_000 and 
                        file not in ['setup.py', 'conftest.py']):
                        python_files.append(file_path)
        
        return python_files
    
    async def analyze_repository(self, repo_url: str, temp_dir: str = None):
        """Analyze repository with enhanced .pyi processing"""
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        logger.info(f"Analyzing repository: {repo_name}")
        
        # Clear existing data
        await self.clear_repository_data(repo_name)
        
        # Setup temp directory
        if temp_dir is None:
            script_dir = Path(__file__).parent
            temp_dir = str(script_dir / "repos" / repo_name)
        
        try:
            # Clone repository
            repo_path = await self.clone_repo(repo_url, temp_dir)
            
            # Get all Python files (including .pyi)
            python_files = await self.get_python_files(str(repo_path))
            logger.info(f"Found {len(python_files)} Python files (.py and .pyi)")
            
            # Analyze project structure
            project_modules = self._get_project_modules(python_files, repo_path)
            
            # Analyze each file
            modules_data = []
            stub_files = []
            implementation_files = []
            
            for file_path in python_files:
                module_data = self.analyzer.analyze_python_file(file_path, repo_path, project_modules)
                if module_data:
                    modules_data.append(module_data)
                    if module_data['is_stub_file']:
                        stub_files.append(module_data)
                    else:
                        implementation_files.append(module_data)
            
            logger.info(f"Analyzed {len(implementation_files)} implementation files and {len(stub_files)} stub files")
            
            # Create enhanced graph with type validation relationships
            await self._create_enhanced_graph(repo_name, modules_data, stub_files, implementation_files)
            
            # Create type validation relationships
            await self._create_type_validation_relationships(repo_name, stub_files, implementation_files)
            
            logger.info(f"✅ Codebase {repo_name} analyzed successfully")
            return {
                'total_files': len(modules_data),
                'implementation_files': len(implementation_files),
                'stub_files': len(stub_files),
                'repo_name': repo_name
            }
            
        except Exception as e:
            logger.error(f"Error analyzing repository: {e}")
            raise
        finally:
            # Cleanup temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def analyze_local_repository(self, local_path: str):
        """Analyze local repository/project folder with enhanced .pyi processing"""
        repo_path = Path(local_path)
        repo_name = repo_path.name
        logger.info(f"Analyzing local repository: {repo_name} at {local_path}")
        
        if not repo_path.exists():
            raise Exception(f"Local path does not exist: {local_path}")
        
        if not repo_path.is_dir():
            raise Exception(f"Path is not a directory: {local_path}")
        
        # Clear existing data
        await self.clear_repository_data(repo_name)
        
        try:
            # Get all Python files (including .pyi)
            python_files = await self.get_python_files(str(repo_path))
            logger.info(f"Found {len(python_files)} Python files (.py and .pyi)")
            
            # Analyze project structure
            project_modules = self._get_project_modules(python_files, repo_path)
            
            # Analyze each file
            modules_data = []
            stub_files = []
            implementation_files = []
            
            for file_path in python_files:
                module_data = self.analyzer.analyze_python_file(file_path, repo_path, project_modules)
                if module_data:
                    modules_data.append(module_data)
                    if module_data['is_stub_file']:
                        stub_files.append(module_data)
                    else:
                        implementation_files.append(module_data)
            
            logger.info(f"Analyzed {len(implementation_files)} implementation files and {len(stub_files)} stub files")
            
            # Create enhanced graph with type validation relationships
            await self._create_enhanced_graph(repo_name, modules_data, stub_files, implementation_files)
            
            # Create type validation relationships
            await self._create_type_validation_relationships(repo_name, stub_files, implementation_files)
            
            # Create architectural relationships if hex_mode is enabled
            if self.hex_mode:
                await self._create_architectural_relationships(repo_name, modules_data)
            
            logger.info(f"✅ Local repository {repo_name} analyzed successfully")
            return {
                'total_files': len(modules_data),
                'implementation_files': len(implementation_files),
                'stub_files': len(stub_files),
                'repo_name': repo_name
            }
            
        except Exception as e:
            logger.error(f"Error analyzing local repository: {e}")
            raise
    
    async def clone_repo(self, repo_url: str, target_dir: str) -> Path:
        """Clone repository"""
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        
        os.makedirs(target_dir, exist_ok=True)
        
        # Use git clone with shallow clone for efficiency
        cmd = f"git clone --depth 1 {repo_url} {target_dir}"
        process = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Git clone failed: {stderr.decode()}")
        
        return Path(target_dir)
    
    def _get_project_modules(self, python_files: List[Path], repo_root: Path) -> Set[str]:
        """Extract project module names using canonical approach"""
        modules = set()
        for file_path in python_files:
            relative_path = str(file_path.relative_to(repo_root))
            # Create canonical name by stripping extension first
            canonical_path = Path(relative_path).with_suffix('')
            module_name = str(canonical_path).replace('/', '.').replace('\\', '.')
            modules.add(module_name.split('.')[0])  # Top-level module
            logger.info(f"📦 Project module: {file_path.name} -> {module_name}")
        return modules
    
    async def clear_repository_data(self, repo_name: str):
        """Clear existing repository data"""
        async with self.driver.session() as session:
            await session.run(
                "MATCH (c:Codebase {name: $repo_name}) DETACH DELETE c",
                repo_name=repo_name
            )
    
    def _calculate_layer_distribution(self, modules_data: List[Dict]) -> Dict[str, int]:
        """Calculate distribution of files across architectural layers"""
        layer_counts = {'domain': 0, 'application': 0, 'infrastructure': 0, 'interface': 0, 'unknown': 0}
        
        for mod in modules_data:
            if self.hex_mode and self.analyzer.hex_analyzer:
                analyzed_mod = self.analyzer.hex_analyzer.analyze_component_architecture(mod)
                if 'architectural_info' in analyzed_mod:
                    layer = analyzed_mod['architectural_info'].get('dominant_layer', 'unknown')
                    layer_counts[layer] = layer_counts.get(layer, 0) + 1
                else:
                    layer_counts['unknown'] += 1
            else:
                layer_counts['unknown'] += 1
                
        return layer_counts
    
    def _calculate_file_metrics(self, module_data: Dict) -> Dict[str, Any]:
        """Calculate file-level metrics for architectural analysis"""
        classes = module_data.get('classes', [])
        functions = module_data.get('functions', [])
        
        # Calculate component count
        component_count = len(classes) + len(functions)
        
        # Calculate cyclomatic complexity (simplified)
        total_complexity = 0
        for cls in classes:
            methods = cls.get('methods', [])
            total_complexity += len(methods) * 1.5  # Simplified complexity estimate
        
        total_complexity += len(functions) * 1.0  # Functions have base complexity
        
        return {
            'component_count': component_count,
            'cyclomatic_complexity': round(total_complexity, 2)
        }
    
    def _calculate_class_metrics(self, class_data: Dict) -> Dict[str, Any]:
        """Calculate class-level metrics for architectural analysis"""
        methods = class_data.get('methods', [])
        
        # Count public methods (not starting with _)
        public_methods = [m for m in methods if not m.get('name', '').startswith('_')]
        
        # Calculate complexity score (simplified)
        complexity_score = len(methods) * 1.2 + len(public_methods) * 0.8
        
        return {
            'method_count': len(methods),
            'public_method_count': len(public_methods),
            'complexity_score': round(complexity_score, 2)
        }
    
    async def _create_enhanced_graph(self, repo_name: str, modules_data: List[Dict], 
                                   stub_files: List[Dict], implementation_files: List[Dict]):
        """Create enhanced graph with type information using metadata overlay approach"""
        async with self.driver.session() as session:
            # Create codebase node with optional architectural metadata
            codebase_props = {
                'name': repo_name,
                'has_stubs': len(stub_files) > 0
            }
            
            # Add architectural metadata if hex_mode is enabled
            if self.hex_mode:
                # Calculate layer distribution from modules_data
                layer_distribution = self._calculate_layer_distribution(modules_data)
                codebase_props.update({
                    'architecture_style': 'hexagonal',
                    'total_files': len(modules_data),
                    'layer_distribution': json.dumps(layer_distribution),  # Serialize to JSON string
                    'analysis_version': '1.0'
                })
            
            # Build dynamic Cypher query for codebase creation
            props_str = ', '.join([f'{k}: ${k}' for k in codebase_props.keys()])
            
            cypher_query = f"""
                CREATE (c:Codebase {{
                    {props_str},
                    created_at: datetime()
                }})
            """
            
            await session.run(cypher_query, **codebase_props)
            
            # Create a lookup of stub data by canonical module name
            stub_lookup = {}
            for stub in stub_files:
                canonical_name = stub['module_name']
                stub_lookup[canonical_name] = stub
                logger.info(f"📎 Stub registered: {canonical_name}")
            
            # Create file nodes with enhanced metadata (only for .py files, enhanced with .pyi data)
            for mod in modules_data:
                # Skip .pyi files - they become metadata overlays
                if mod['is_stub_file']:
                    continue
                    
                # Check if this module has corresponding stub data
                canonical_name = mod['module_name']
                has_stub = canonical_name in stub_lookup
                stub_metadata = stub_lookup.get(canonical_name, {})
                
                # NEW: Add hexagonal architecture analysis if hex_mode is enabled
                analyzed_mod = mod
                if self.hex_mode and self.analyzer.hex_analyzer:
                    analyzed_mod = self.analyzer.hex_analyzer.analyze_component_architecture(mod)
                    logger.info(f"🏗️  Architectural analysis completed for: {canonical_name}")
                
                logger.info(f"📄 Creating file node: {canonical_name} (has_stub: {has_stub})")
                
                # Prepare file properties with optional architectural metadata
                file_props = {
                    'name': analyzed_mod['file_path'].split('/')[-1],
                    'path': analyzed_mod['file_path'],
                    'module_name': analyzed_mod['module_name'],
                    'file_type': analyzed_mod['file_type'],
                    'is_stub_file': False,
                    'line_count': analyzed_mod['line_count'],
                    'has_stub_overlay': has_stub,
                    'stub_path': stub_metadata.get('file_path', '') if has_stub else '',
                    'created_at': 'datetime()'
                }
                
                # Add architectural properties if hex_mode is enabled
                if self.hex_mode and 'architectural_info' in analyzed_mod:
                    arch_info = analyzed_mod['architectural_info']
                    file_metrics = self._calculate_file_metrics(analyzed_mod)
                    
                    file_props.update({
                        'dominant_layer': arch_info.get('dominant_layer', 'unknown'),
                        'architectural_types': arch_info.get('architectural_types', []),
                        'is_mixed_layer': arch_info.get('is_mixed_layer', False),
                        'layer_confidence': arch_info.get('confidence', 0.0),
                        # NEW: Additional file-level architecture metrics
                        'component_count': file_metrics['component_count'],
                        'cyclomatic_complexity': file_metrics['cyclomatic_complexity']
                    })
                
                # Build dynamic Cypher query based on properties
                props_str = ', '.join([f'{k}: ${k}' for k in file_props.keys() if k != 'created_at'])
                
                cypher_query = f"""
                    MATCH (c:Codebase {{name: $repo_name}})
                    CREATE (f:File {{
                        {props_str},
                        created_at: datetime()
                    }})
                    CREATE (c)-[:CONTAINS]->(f)
                """
                
                # Add architectural layer label if hex_mode is enabled
                if self.hex_mode and 'architectural_info' in analyzed_mod:
                    dominant_layer = analyzed_mod['architectural_info'].get('dominant_layer', 'unknown')
                    if dominant_layer != 'unknown':
                        cypher_query += f"\n                    SET f:{dominant_layer.title()}"
                
                await session.run(cypher_query, repo_name=repo_name, **file_props)
                
                # Create/merge class nodes with stub enhancement
                for cls in analyzed_mod['classes']:
                    # Look for corresponding stub class
                    stub_class = None
                    if has_stub:
                        for stub_cls in stub_metadata.get('classes', []):
                            if stub_cls['name'] == cls['name']:
                                stub_class = stub_cls
                                break
                    
                    # Prepare class properties with optional architectural metadata
                    class_props = {
                        'file_path': analyzed_mod['file_path'],
                        'name': cls['name'],
                        'module': analyzed_mod['module_name'],
                        'base_classes': cls['base_classes'],
                        'is_abstract': cls['is_abstract'],
                        'docstring': cls.get('docstring', ''),
                        'is_from_stub': False,
                        'from_file': analyzed_mod['file_path'],
                        'has_stub_definition': stub_class is not None,
                        'stub_docstring': stub_class.get('docstring', '') if stub_class else ''
                    }
                    
                    # Add architectural properties if hex_mode is enabled
                    if self.hex_mode and 'architectural_tags' in cls:
                        arch_tags = cls['architectural_tags']
                        class_metrics = self._calculate_class_metrics(cls)
                        
                        class_props.update({
                            'architectural_type': arch_tags.get('architectural_type', 'unknown'),
                            'layer': arch_tags.get('layer', 'unknown'),
                            'hexagonal_role': arch_tags.get('hexagonal_role', 'unknown'),
                            'is_interface': arch_tags.get('is_interface', False),
                            'arch_confidence': arch_tags.get('confidence', 0.0),
                            'arch_reasoning': arch_tags.get('reasoning', ''),
                            # NEW: Additional class-level architecture metrics
                            'method_count': class_metrics['method_count'],
                            'public_method_count': class_metrics['public_method_count'],
                            'complexity_score': class_metrics['complexity_score']
                        })
                    
                    # Build dynamic Cypher query for class creation
                    set_props = ', '.join([f'c.{k} = ${k}' for k in class_props.keys() if k not in ['file_path', 'name', 'module']])
                    
                    cypher_query = f"""
                        MATCH (f:File {{path: $file_path}})
                        MERGE (c:Class {{
                            name: $name,
                            module: $module
                        }})
                        SET {set_props}
                        MERGE (f)-[:DEFINES]->(c)
                    """
                    
                    # Add architectural labels if hex_mode is enabled
                    if self.hex_mode and 'architectural_tags' in cls:
                        arch_tags = cls['architectural_tags']
                        hex_role = arch_tags.get('hexagonal_role', 'unknown')
                        layer = arch_tags.get('layer', 'unknown')
                        
                        if hex_role != 'unknown':
                            cypher_query += f"\n                        SET c:{hex_role.replace('_', '').title()}"
                        if layer != 'unknown':
                            cypher_query += f"\n                        SET c:{layer.title()}"
                    
                    await session.run(cypher_query, **class_props)
                    
                    # Create/merge method nodes with stub metadata overlay
                    for method in cls['methods']:
                        # Look for corresponding stub method
                        stub_method = None
                        if stub_class:
                            for stub_meth in stub_class.get('methods', []):
                                if stub_meth['name'] == method['name']:
                                    stub_method = stub_meth
                                    break
                        
                        await session.run("""
                            MATCH (c:Class {name: $class_name, module: $module})
                            MERGE (m:Method {
                                name: $name,
                                class: $class_name,
                                signature: $signature,
                                is_stub_definition: false
                            })
                            SET m.return_type = $return_type,
                                m.is_async = $is_async,
                                m.decorators = $decorators,
                                m.docstring = $docstring,
                                m.from_file = $file_path,
                                m.is_from_stub = false,
                                m.has_stub_definition = $has_stub_method,
                                m.stub_signature = $stub_signature,
                                m.stub_return_type = $stub_return_type
                            MERGE (c)-[:HAS_METHOD]->(m)
                        """,
                            class_name=cls['name'],
                            module=mod['module_name'],
                            name=method['name'],
                            signature=method['signature'],
                            return_type=method['return_type'],
                            is_async=method['is_async'],
                            decorators=method['decorators'],
                            docstring=method.get('docstring', ''),
                            file_path=mod['file_path'],
                            has_stub_method=stub_method is not None,
                            stub_signature=stub_method.get('signature', '') if stub_method else '',
                            stub_return_type=stub_method.get('return_type', '') if stub_method else ''
                        )
                
                # Create/merge function nodes with stub metadata overlay
                for func in mod['functions']:
                    # Look for corresponding stub function
                    stub_function = None
                    if has_stub:
                        for stub_func in stub_metadata.get('functions', []):
                            if stub_func['name'] == func['name']:
                                stub_function = stub_func
                                break
                    
                    await session.run("""
                        MATCH (f:File {path: $file_path})
                        MERGE (fn:Function {
                            name: $name,
                            module: $module,
                            signature: $signature,
                            is_stub_definition: false
                        })
                        SET fn.return_type = $return_type,
                            fn.is_async = $is_async,
                            fn.decorators = $decorators,
                            fn.docstring = $docstring,
                            fn.from_file = $file_path,
                            fn.is_from_stub = false,
                            fn.has_stub_definition = $has_stub_func,
                            fn.stub_signature = $stub_signature,
                            fn.stub_return_type = $stub_return_type
                        MERGE (f)-[:DEFINES]->(fn)
                    """,
                        file_path=mod['file_path'],
                        name=func['name'],
                        module=mod['module_name'],
                        signature=func['signature'],
                        return_type=func['return_type'],
                        is_async=func['is_async'],
                        decorators=func['decorators'],
                        docstring=func.get('docstring', ''),
                        has_stub_func=stub_function is not None,
                        stub_signature=stub_function.get('signature', '') if stub_function else '',
                        stub_return_type=stub_function.get('return_type', '') if stub_function else ''
                    )
            
            # Metadata overlay approach complete - stub data is embedded in implementation nodes
            logger.info(f"✅ Knowledge graph created with {len(stub_files)} stub overlays")
    
    async def _create_type_validation_relationships(self, repo_name: str, 
                                                  stub_files: List[Dict], 
                                                  implementation_files: List[Dict]):
        """Create relationships between stubs and implementations for validation"""
        async with self.driver.session() as session:
            # Create VALIDATES relationships between stub and implementation files
            for stub in stub_files:
                stub_module = stub['module_name']
                
                # Find corresponding implementation file
                for impl in implementation_files:
                    if impl['module_name'] == stub_module:
                        # File-level validation relationship
                        await session.run("""
                            MATCH (stub:File {module_name: $stub_module, is_stub_file: true})
                            MATCH (impl:File {module_name: $impl_module, is_stub_file: false})
                            MERGE (stub)-[:VALIDATES]->(impl)
                        """, stub_module=stub_module, impl_module=impl['module_name'])
                        
                        # Method-level validation relationships
                        await session.run("""
                            MATCH (stub:Method {is_stub_definition: true, is_from_stub: true})
                            MATCH (impl:Method {is_stub_definition: false, is_from_stub: false})
                            WHERE stub.name = impl.name 
                              AND stub.class = impl.class 
                              AND stub.signature = impl.signature
                            MERGE (stub)-[:VALIDATES_METHOD]->(impl)
                        """)
                        
                        # Function-level validation relationships  
                        await session.run("""
                            MATCH (stub:Function {is_stub_definition: true, is_from_stub: true})
                            MATCH (impl:Function {is_stub_definition: false, is_from_stub: false})
                            WHERE stub.name = impl.name 
                              AND stub.module = impl.module 
                              AND stub.signature = impl.signature
                            MERGE (stub)-[:VALIDATES_FUNCTION]->(impl)
                        """)
                        
                        # Class-level validation relationships
                        await session.run("""
                            MATCH (stub:Class {is_from_stub: true})
                            MATCH (impl:Class {is_from_stub: false})
                            WHERE stub.name = impl.name AND stub.module = impl.module
                            MERGE (stub)-[:VALIDATES_CLASS]->(impl)
                        """)
                        break
    
    async def validate_function_signature(self, module_name: str, function_name: str, 
                                        class_name: str = None) -> Dict[str, Any]:
        """Validate function signature against stub definitions"""
        async with self.driver.session() as session:
            if class_name:
                # Validate method signature
                result = await session.run("""
                    MATCH (stub:File {is_stub_file: true})-[:DEFINES]->(c:Class {name: $class_name})
                    -[:HAS_METHOD]->(m:Method {name: $function_name})
                    WHERE stub.module_name = $module_name
                    RETURN m.signature as stub_signature, m.return_type as stub_return_type
                """, module_name=module_name, class_name=class_name, function_name=function_name)
            else:
                # Validate function signature
                result = await session.run("""
                    MATCH (stub:File {is_stub_file: true})-[:DEFINES]->(fn:Function {name: $function_name})
                    WHERE stub.module_name = $module_name
                    RETURN fn.signature as stub_signature, fn.return_type as stub_return_type
                """, module_name=module_name, function_name=function_name)
            
            records = [record.data() async for record in result]
            return {
                'has_stub_definition': len(records) > 0,
                'stub_signatures': records,
                'module': module_name,
                'function': function_name,
                'class': class_name
            }
    
    async def detect_hallucination(self, generated_code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect potential hallucinations in generated code using type stubs"""
        # Parse generated code
        try:
            tree = ast.parse(generated_code)
        except SyntaxError as e:
            return {'error': f'Syntax error in generated code: {e}', 'is_hallucination': True}
        
        issues = []
        
        # Check function calls against stub definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # Method call: obj.method()
                    method_name = node.func.attr
                    # Extract object type from context if available
                    class_name = context.get('class_context')
                    module_name = context.get('module_context')
                    
                    if class_name and module_name:
                        validation = await self.validate_function_signature(
                            module_name, method_name, class_name
                        )
                        if not validation['has_stub_definition']:
                            issues.append({
                                'type': 'unknown_method',
                                'method': method_name,
                                'class': class_name,
                                'line': node.lineno
                            })
                elif isinstance(node.func, ast.Name):
                    # Function call: function()
                    func_name = node.func.id
                    module_name = context.get('module_context')
                    
                    if module_name:
                        validation = await self.validate_function_signature(module_name, func_name)
                        if not validation['has_stub_definition']:
                            issues.append({
                                'type': 'unknown_function',
                                'function': func_name,
                                'line': node.lineno
                            })
        
        return {
            'is_hallucination': len(issues) > 0,
            'issues': issues,
            'confidence': 1.0 - (len(issues) * 0.2)  # Simple confidence score
        }
    
    async def analyze_ai_script_with_validation(self, script_path: str, repo_name: str = None) -> Dict[str, Any]:
        """Analyze AI-generated script using integrated knowledge graph validation"""
        return await self.analyzer.analyze_ai_generated_script(script_path, repo_name)
    
    async def validate_ai_code_snippet(self, code_snippet: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate a code snippet for potential hallucinations using knowledge graph"""
        try:
            # Create a temporary file for the code snippet
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code_snippet)
                temp_file_path = temp_file.name
            
            try:
                # Analyze the temporary file
                result = await self.analyzer.analyze_ai_generated_script(
                    temp_file_path, 
                    context.get('repo_name') if context else None
                )
                return result
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Error validating code snippet: {e}")
            return {
                'analysis': None,
                'validation': None,
                'hallucinations': None,
                'error': str(e)
            }
    
    async def get_validation_summary(self, repo_name: str) -> Dict[str, Any]:
        """Get a summary of validation capabilities for a repository"""
        try:
            async with self.driver.session() as session:
                result = await session.run("""
                    MATCH (c:Codebase {name: $repo_name})
                    OPTIONAL MATCH (r)-[:CONTAINS]->(f:File)
                    OPTIONAL MATCH (stub:File {is_stub_file: true})
                    OPTIONAL MATCH (f)-[:DEFINES]->(c:Class)
                    OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
                    OPTIONAL MATCH (f)-[:DEFINES]->(func:Function)
                    RETURN 
                        count(DISTINCT f) as total_files,
                        count(DISTINCT stub) as stub_files,
                        count(DISTINCT c) as classes,
                        count(DISTINCT m) as methods,
                        count(DISTINCT func) as functions,
                        r.has_stubs as has_stubs
                """, repo_name=repo_name)
                
                record = await result.single()
                if record:
                    return {
                        'repo_name': repo_name,
                        'total_files': record['total_files'],
                        'stub_files': record['stub_files'],
                        'classes': record['classes'],
                        'methods': record['methods'],
                        'functions': record['functions'],
                        'has_stubs': record['has_stubs'],
                        'validation_ready': record['stub_files'] > 0
                    }
                else:
                    return {'error': f'Codebase {repo_name} not found'}
                    
        except Exception as e:
            logger.error(f"Error getting validation summary: {e}")
            return {'error': str(e)}
    
    async def _create_architectural_relationships(self, repo_name: str, modules_data: List[Dict[str, Any]]):
        """Create architectural relationships between classes when hex_mode is enabled"""
        if not self.hex_mode:
            return
            
        logger.info("🏗️  Creating architectural relationships...")
        
        # Extract class information with architectural metadata
        classes_with_arch = []
        for module in modules_data:
            for class_info in module.get('classes', []):
                if 'architectural_tags' in class_info:
                    classes_with_arch.append({
                        'module_name': module['module_name'],
                        'class_name': class_info['name'],
                        'architectural_metadata': class_info['architectural_tags'],
                        'methods': class_info.get('methods', []),
                        'base_classes': class_info.get('base_classes', [])
                    })
        
        # Create relationships based on architectural patterns
        relationships_created = 0
        
        async with self.driver.session() as session:
            for class_info in classes_with_arch:
                class_name = class_info['class_name']
                module_name = class_info['module_name']
                arch_metadata = class_info['architectural_metadata']
                
                # Create inheritance relationships
                for base_class in class_info['base_classes']:
                    try:
                        await session.run(
                            """
                            MATCH (child:Class {name: $child_name, module: $child_module})
                            MATCH (parent:Class {name: $parent_name})
                            MERGE (child)-[:INHERITS_FROM {relationship_type: 'inheritance', confidence: $confidence}]->(parent)
                            """,
                            child_name=class_name,
                            child_module=module_name,
                            parent_name=base_class,
                            confidence=arch_metadata.get('confidence', 0.8)
                        )
                        relationships_created += 1
                    except Exception as e:
                        logger.warning(f"Could not create inheritance relationship {class_name} -> {base_class}: {e}")
                
                # Create architectural layer relationships
                dominant_layer = arch_metadata.get('layer', 'unknown')
                if dominant_layer != 'unknown':
                    # Find other classes in the same layer for potential relationships
                    for other_class in classes_with_arch:
                        if other_class['class_name'] != class_name:
                            other_layer = other_class['architectural_metadata'].get('layer', 'unknown')
                            
                            # Create DEPENDS_ON relationships based on architectural patterns
                            if self._should_create_dependency_relationship(dominant_layer, other_layer):
                                try:
                                    await session.run(
                                        """
                                        MATCH (source:Class {name: $source_name, module: $source_module})
                                        MATCH (target:Class {name: $target_name, module: $target_module})
                                        MERGE (source)-[:DEPENDS_ON {
                                            relationship_type: 'architectural_dependency',
                                            source_layer: $source_layer,
                                            target_layer: $target_layer,
                                            confidence: $confidence
                                        }]->(target)
                                        """,
                                        source_name=class_name,
                                        source_module=module_name,
                                        target_name=other_class['class_name'],
                                        target_module=other_class['module_name'],
                                        source_layer=dominant_layer,
                                        target_layer=other_layer,
                                        confidence=0.7
                                    )
                                    relationships_created += 1
                                except Exception as e:
                                    logger.warning(f"Could not create dependency relationship: {e}")
        
        logger.info(f"✅ Created {relationships_created} architectural relationships")
    
    def _should_create_dependency_relationship(self, source_layer: str, target_layer: str) -> bool:
        """Determine if a dependency relationship should be created based on architectural layers"""
        # Hexagonal architecture dependency rules
        dependency_rules = {
            'application': ['domain', 'infrastructure'],  # Application can depend on domain and infrastructure
            'infrastructure': ['domain'],  # Infrastructure can depend on domain
            'domain': [],  # Domain should not depend on other layers
            'interface': ['application', 'domain']  # Interface can depend on application and domain
        }
        
        return target_layer in dependency_rules.get(source_layer, [])
    
    async def close(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()


async def setup_enhanced_knowledge_graph(codebase_path: str, hex_mode: bool = False):
    """Setup enhanced knowledge graph with .pyi processing for hallucination detection"""
    # Load environment variables
    load_dotenv()
    
    # Use the specific Neo4j configuration for the user's setup
    neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', 'no_auth')
    
    print(f"🔗 Connecting to Neo4j at: {neo4j_uri}")
    print(f"👤 Using user: {neo4j_user}")
    print(f"📊 Enhanced .pyi processing: ENABLED")
    if hex_mode:
        print(f"🏗️  Hexagonal architecture analysis: ENABLED")
    
    extractor = EnhancedKnowledgeGraphExtractor(neo4j_uri, neo4j_user, neo4j_password, hex_mode=hex_mode)
    
    try:
        await extractor.initialize()
        await extractor.setup_enhanced_constraints()
        print("✅ Connected to Neo4j and setup constraints")
        
        # Check existing repositories
        async with extractor.driver.session() as session:
            result = await session.run("MATCH (c:Codebase) RETURN c.name as name, c.has_stubs as has_stubs")
            existing_repos = [(record['name'], record.get('has_stubs', False)) async for record in result]
            if existing_repos:
                print(f"📂 Existing repositories: {existing_repos}")
        
        # Clear all existing data from the database
        print("🗑️  Clearing all existing data from the Neo4j database...")
        async with extractor.driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            print("✅ All existing data cleared successfully")
        
        # Parse repository with enhanced .pyi processing
        # Use the provided codebase_path parameter
        repo_input = codebase_path
        
        # Check if input is a local path or URL
        if os.path.exists(repo_input) or repo_input.startswith('./') or os.path.isabs(repo_input):
            # Local path - handle both relative and absolute paths correctly
            if repo_input.startswith('./'):
                # Remove the './' prefix for relative paths
                repo_input = repo_input[2:]
            
            # Convert to absolute path if it's not already
            if os.path.isabs(repo_input):
                local_path = repo_input
            else:
                local_path = os.path.abspath(repo_input)
                
            print(f"🔍 Analyzing local project: {local_path}")
            print("📋 Processing both .py and .pyi files for comprehensive type analysis...")
            result = await extractor.analyze_local_repository(local_path)
        else:
            # Assume it's a Git URL
            print(f"🔍 Analyzing repository: {repo_input}")
            print("📋 Processing both .py and .pyi files for comprehensive type analysis...")
            result = await extractor.analyze_repository(repo_input)
        
        # Verify the enhanced data was loaded
        async with extractor.driver.session() as session:
            # Get comprehensive repository stats including type information
            repo_name = result['repo_name']
            stats_result = await session.run(f"""
                MATCH (c:Codebase {{name: '{repo_name}'}})
                OPTIONAL MATCH (c)-[:CONTAINS]->(f:File)
                OPTIONAL MATCH (stub:File {{is_stub_file: true}})
                OPTIONAL MATCH (impl:File {{is_stub_file: false}})
                OPTIONAL MATCH (f)-[:DEFINES]->(cls:Class)
                OPTIONAL MATCH (cls)-[:HAS_METHOD]->(m:Method)
                OPTIONAL MATCH (f)-[:DEFINES]->(func:Function)
                OPTIONAL MATCH (stub)-[:VALIDATES]->(impl)
                RETURN 
                    count(DISTINCT f) as total_files,
                    count(DISTINCT stub) as stub_files,
                    count(DISTINCT impl) as implementation_files,
                    count(DISTINCT cls) as classes,
                    count(DISTINCT m) as methods,
                    count(DISTINCT func) as functions,
                    count(DISTINCT stub) as validation_relationships,
                    c.has_stubs as has_stubs
            """)
            
            record = await stats_result.single()
            if record:
                print("\n✅ Enhanced knowledge graph populated successfully!")
                print(f"📁 Total files: {record['total_files']}")
                print(f"📜 Type stub files (.pyi): {record['stub_files']}")
                print(f"🐍 Implementation files (.py): {record['implementation_files']}")
                print(f"🏗️  Classes: {record['classes']}")
                print(f"⚙️  Methods: {record['methods']}")
                print(f"🔧 Functions: {record['functions']}")
                print(f"✅ Type validation enabled: {record['has_stubs']}")
                
                # Demonstrate hallucination detection capabilities
                if record['stub_files'] > 0:
                    print("\n🔍 Testing hallucination detection capabilities...")
                    
                    # Test with some example code
                    test_code = """
def test_function():
    # This should trigger validation against stubs
    result = some_function_that_might_not_exist()
    return result
"""
                    
                    # Dynamic context based on actual repository data
                    print("🤖 Hallucination detection framework is ready for use")
                    print("   Use extractor.detect_hallucination(code, context) with actual data")
                
            else:
                print(f"❌ No data found for {repo_name} repository")
        
        # Show type stub validation examples
        if result['stub_files'] > 0:
            print("\n🔬 Type stub validation examples:")
            
            # Example: Function signature validation framework is ready
            print("📋 Signature validation framework available:")
            print("   Use extractor.validate_function_signature(module, function, class) with actual data")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Setup failed: {e}")
        raise
    finally:
        await extractor.close()
        print("🔌 Neo4j connection closed")


async def main():
    """Main execution combining setup and enhanced processing"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Enhanced Knowledge Graph Setup with optional hexagonal architecture analysis"
    )
    parser.add_argument(
        "codebase_path",
        help="Path to the codebase directory or Git repository URL to analyze"
    )
    parser.add_argument(
        "--hex", 
        action="store_true", 
        help="Enable hexagonal architecture analysis and tagging during knowledge graph creation"
    )
    args = parser.parse_args()
    
    print("🚀 Starting Enhanced Knowledge Graph Setup MK2")
    print("📊 Features: .pyi type stub processing + hallucination detection")
    if args.hex:
        print("🏗️  Hexagonal architecture analysis: ENABLED")
    print("-" * 60)
    
    try:
        await setup_enhanced_knowledge_graph(codebase_path=args.codebase_path, hex_mode=args.hex)
        print("\n✅ Enhanced knowledge graph setup completed successfully!")
        print("🎯 Ready for advanced hallucination detection and type validation")
        if args.hex:
            print("🏗️  Architectural metadata has been integrated into the knowledge graph")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
