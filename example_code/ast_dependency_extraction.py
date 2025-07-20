import ast
import os
from typing import Dict, List, Set, Tuple
from pathlib import Path

class DependencyExtractor(ast.NodeVisitor):
    """Extract code dependencies using Python AST for Neo4j relationship creation"""
    
    def __init__(self, file_path: str, module_name: str):
        self.file_path = file_path
        self.module_name = module_name
        self.current_class = None
        self.current_function = None
        
        # Relationships to be created in Neo4j
        self.imports = []  # (:File)-[:IMPORTS]->(:File)
        self.function_calls = []  # (:Function)-[:CALLS]->(:Function) 
        self.method_calls = []  # (:Method)-[:CALLS]->(:Method)
        self.class_inheritance = []  # (:Class)-[:INHERITS_FROM]->(:Class)
        self.interface_implementations = []  # (:Class)-[:IMPLEMENTS]->(:Interface)
        self.class_usage = []  # (:Function)-[:USES]->(:Class)
        self.variable_assignments = []  # Track variable types
        
    def visit_Import(self, node):
        """Extract import statements: import module"""
        for alias in node.names:
            imported_module = alias.name
            self.imports.append({
                'from_file': self.file_path,
                'from_module': self.module_name,
                'to_module': imported_module,
                'import_type': 'import',
                'alias': alias.asname
            })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Extract from imports: from module import item"""
        if node.module:
            for alias in node.names:
                self.imports.append({
                    'from_file': self.file_path,
                    'from_module': self.module_name,
                    'to_module': node.module,
                    'imported_item': alias.name,
                    'import_type': 'from_import',
                    'alias': alias.asname,
                    'level': node.level  # For relative imports
                })
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Extract class definitions and inheritance"""
        old_class = self.current_class
        self.current_class = node.name
        
        # Extract inheritance relationships
        for base in node.bases:
            base_name = self._get_name_from_node(base)
            if base_name:
                self.class_inheritance.append({
                    'child_class': node.name,
                    'child_module': self.module_name,
                    'parent_class': base_name,
                    'file_path': self.file_path
                })
        
        # Extract interface implementations (look for ABC or Protocol)
        for base in node.bases:
            base_name = self._get_name_from_node(base)
            if base_name and ('ABC' in base_name or 'Protocol' in base_name):
                self.interface_implementations.append({
                    'implementing_class': node.name,
                    'implementing_module': self.module_name,
                    'interface': base_name,
                    'file_path': self.file_path
                })
        
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node):
        """Extract function definitions and track context"""
        old_function = self.current_function
        self.current_function = node.name
        
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node):
        """Handle async functions same as regular functions"""
        self.visit_FunctionDef(node)
    
    def visit_Call(self, node):
        """Extract function/method calls"""
        called_name = self._get_name_from_node(node.func)
        
        if called_name and self.current_function:
            call_info = {
                'caller_function': self.current_function,
                'caller_class': self.current_class,
                'caller_module': self.module_name,
                'called_function': called_name,
                'file_path': self.file_path,
                'line_number': node.lineno
            }
            
            # Determine if it's a method call or function call
            if isinstance(node.func, ast.Attribute):
                # Method call: obj.method()
                obj_name = self._get_name_from_node(node.func.value)
                call_info['called_object'] = obj_name
                call_info['call_type'] = 'method_call'
                self.method_calls.append(call_info)
            else:
                # Function call: function()
                call_info['call_type'] = 'function_call'
                self.function_calls.append(call_info)
        
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Extract variable assignments and type usage"""
        # Track when classes are instantiated
        if isinstance(node.value, ast.Call):
            class_name = self._get_name_from_node(node.value.func)
            if class_name and self.current_function:
                self.class_usage.append({
                    'using_function': self.current_function,
                    'using_class': self.current_class,
                    'using_module': self.module_name,
                    'used_class': class_name,
                    'usage_type': 'instantiation',
                    'file_path': self.file_path,
                    'line_number': node.lineno
                })
        
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node):
        """Extract type annotations"""
        if node.annotation:
            type_name = self._get_name_from_node(node.annotation)
            if type_name and self.current_function:
                self.class_usage.append({
                    'using_function': self.current_function,
                    'using_class': self.current_class,
                    'using_module': self.module_name,
                    'used_class': type_name,
                    'usage_type': 'type_annotation',
                    'file_path': self.file_path,
                    'line_number': node.lineno
                })
        
        self.generic_visit(node)
    
    def _get_name_from_node(self, node) -> str:
        """Extract name from various AST node types"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_name_from_node(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

def extract_dependencies_from_file(file_path: str) -> DependencyExtractor:
    """Extract all dependencies from a single Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=file_path)
        
        # Determine module name from file path
        module_name = Path(file_path).stem
        
        extractor = DependencyExtractor(file_path, module_name)
        extractor.visit(tree)
        
        return extractor
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def extract_dependencies_from_directory(directory: str) -> List[DependencyExtractor]:
    """Extract dependencies from all Python files in a directory"""
    extractors = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                extractor = extract_dependencies_from_file(file_path)
                if extractor:
                    extractors.append(extractor)
    
    return extractors

def generate_neo4j_cypher_queries(extractors: List[DependencyExtractor]) -> List[str]:
    """Generate Cypher queries to create relationships in Neo4j"""
    queries = []
    
    # Create IMPORTS relationships
    for extractor in extractors:
        for imp in extractor.imports:
            query = f"""
            MATCH (from_file:File {{path: '{imp['from_file']}'}})
            MERGE (to_module:File {{module_name: '{imp['to_module']}'}})
            MERGE (from_file)-[:IMPORTS {{
                import_type: '{imp['import_type']}',
                imported_item: '{imp.get('imported_item', '')}',
                alias: '{imp.get('alias', '')}'
            }}]->(to_module)
            """
            queries.append(query)
    
    # Create INHERITS_FROM relationships
    for extractor in extractors:
        for inheritance in extractor.class_inheritance:
            query = f"""
            MATCH (child:Class {{name: '{inheritance['child_class']}', module: '{inheritance['child_module']}'}})
            MERGE (parent:Class {{name: '{inheritance['parent_class']}'}})
            MERGE (child)-[:INHERITS_FROM]->(parent)
            """
            queries.append(query)
    
    # Create CALLS relationships for functions
    for extractor in extractors:
        for call in extractor.function_calls:
            if call['caller_class']:
                # Method calling function
                query = f"""
                MATCH (caller:Method {{name: '{call['caller_function']}', class: '{call['caller_class']}'}})
                MERGE (called:Function {{name: '{call['called_function']}'}})
                MERGE (caller)-[:CALLS {{line_number: {call['line_number']}}}]->(called)
                """
            else:
                # Function calling function
                query = f"""
                MATCH (caller:Function {{name: '{call['caller_function']}', module: '{call['caller_module']}'}})
                MERGE (called:Function {{name: '{call['called_function']}'}})
                MERGE (caller)-[:CALLS {{line_number: {call['line_number']}}}]->(called)
                """
            queries.append(query)
    
    # Create CALLS relationships for methods
    for extractor in extractors:
        for call in extractor.method_calls:
            if call['caller_class']:
                query = f"""
                MATCH (caller:Method {{name: '{call['caller_function']}', class: '{call['caller_class']}'}})
                MERGE (called:Method {{name: '{call['called_function']}'}})
                MERGE (caller)-[:CALLS {{
                    line_number: {call['line_number']},
                    called_object: '{call.get('called_object', '')}'
                }}]->(called)
                """
                queries.append(query)
    
    # Create USES relationships
    for extractor in extractors:
        for usage in extractor.class_usage:
            if usage['using_class']:
                # Method uses class
                query = f"""
                MATCH (user:Method {{name: '{usage['using_function']}', class: '{usage['using_class']}'}})
                MERGE (used:Class {{name: '{usage['used_class']}'}})
                MERGE (user)-[:USES {{
                    usage_type: '{usage['usage_type']}',
                    line_number: {usage['line_number']}
                }}]->(used)
                """
            else:
                # Function uses class
                query = f"""
                MATCH (user:Function {{name: '{usage['using_function']}', module: '{usage['using_module']}'}})
                MERGE (used:Class {{name: '{usage['used_class']}'}})
                MERGE (user)-[:USES {{
                    usage_type: '{usage['usage_type']}',
                    line_number: {usage['line_number']}
                }}]->(used)
                """
            queries.append(query)
    
    return queries

# Example usage
if __name__ == "__main__":
    # Extract from a single file
    file_extractor = extract_dependencies_from_file("process_folder_for_embeddings.py")
    
    if file_extractor:
        print("IMPORTS:")
        for imp in file_extractor.imports:
            print(f"  {imp}")
        
        print("\nFUNCTION CALLS:")
        for call in file_extractor.function_calls:
            print(f"  {call}")
        
        print("\nMETHOD CALLS:")
        for call in file_extractor.method_calls:
            print(f"  {call}")
        
        print("\nCLASS INHERITANCE:")
        for inheritance in file_extractor.class_inheritance:
            print(f"  {inheritance}")
        
        print("\nCLASS USAGE:")
        for usage in file_extractor.class_usage:
            print(f"  {usage}")
    
    # Extract from entire directory
    # extractors = extract_dependencies_from_directory("./src")
    # cypher_queries = generate_neo4j_cypher_queries(extractors)
    
    # Print first few queries
    # for i, query in enumerate(cypher_queries[:5]):
    #     print(f"Query {i+1}:")
    #     print(query)
    #     print("-" * 50)
