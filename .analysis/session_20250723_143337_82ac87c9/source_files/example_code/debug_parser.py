#!/usr/bin/env python3
"""
Debug script to test the parsing functionality
"""
import os
import ast
from pathlib import Path
from Parse_into_knowledge_graph_repo_MK2 import EnhancedNeo4jCodeAnalyzer

def debug_parsing(repo_path: str = "."):
    """Debug the parsing to see what's happening"""
    print(f"🔍 Debugging parsing for: {repo_path}")
    
    # Initialize analyzer
    analyzer = EnhancedNeo4jCodeAnalyzer()
    
    # Get Python files
    python_files = []
    exclude_dirs = {
        'tests', 'test', '__pycache__', '.git', 'venv', 'env',
        'node_modules', 'build', 'dist', '.pytest_cache', 'docs',
        'examples', 'example', 'demo', 'benchmark'
    }
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py') and not file.startswith('test_'):
                file_path = Path(root) / file
                if file_path.stat().st_size < 500_000 and file not in ['setup.py', 'conftest.py']:
                    python_files.append(file_path)
    
    print(f"📁 Found {len(python_files)} Python files")
    
    # Test parsing on first few files
    repo_root = Path(repo_path)
    project_modules = set()
    
    total_classes = 0
    total_methods = 0
    total_functions = 0
    
    for i, file_path in enumerate(python_files[:10]):  # Test first 10 files
        print(f"\n🔍 Analyzing file {i+1}: {file_path.name}")
        
        try:
            module_data = analyzer.analyze_python_file(file_path, repo_root, project_modules)
            
            if module_data:
                classes = module_data.get('classes', [])
                functions = module_data.get('functions', [])
                
                print(f"   📊 Classes: {len(classes)}")
                print(f"   📊 Functions: {len(functions)}")
                
                # Show class details
                for cls in classes:
                    methods = cls.get('methods', [])
                    print(f"      🏗️  Class: {cls['name']} ({len(methods)} methods)")
                    for method in methods:
                        print(f"         ⚙️  Method: {method['name']}")
                        total_methods += 1
                    total_classes += 1
                
                # Show function details
                for func in functions:
                    print(f"      🔧 Function: {func['name']}")
                    total_functions += 1
                    
            else:
                print(f"   ❌ Failed to analyze {file_path}")
                
        except Exception as e:
            print(f"   ❌ Error analyzing {file_path}: {e}")
    
    print(f"\n📊 Summary from first 10 files:")
    print(f"   Total classes: {total_classes}")
    print(f"   Total methods: {total_methods}")
    print(f"   Total functions: {total_functions}")
    
    # Test a specific file with detailed debugging
    print(f"\n🔍 Detailed debugging of Parse_into_knowledge_graph_repo_MK2.py:")
    test_file = Path(repo_path) / "Parse_into_knowledge_graph_repo_MK2.py"
    
    if test_file.exists():
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Manual AST walk to debug
            classes_found = []
            functions_found = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes_found.append(node.name)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.name.startswith('_'):
                        functions_found.append(node.name)
            
            print(f"   📊 AST Walk Results:")
            print(f"      Classes: {len(classes_found)} - {classes_found[:5]}...")
            print(f"      Functions: {len(functions_found)} - {functions_found[:5]}...")
            
            # Test the analyzer on this specific file
            module_data = analyzer.analyze_python_file(test_file, repo_root, project_modules)
            if module_data:
                classes = module_data.get('classes', [])
                functions = module_data.get('functions', [])
                print(f"   📊 Analyzer Results:")
                print(f"      Classes: {len(classes)}")
                print(f"      Functions: {len(functions)}")
                
                if len(classes) != len(classes_found):
                    print(f"   ⚠️  MISMATCH: AST found {len(classes_found)} classes, analyzer found {len(classes)}")
                
                if len(functions) != len(functions_found):
                    print(f"   ⚠️  MISMATCH: AST found {len(functions_found)} functions, analyzer found {len(functions)}")
                    
        except Exception as e:
            print(f"   ❌ Error in detailed debugging: {e}")

if __name__ == "__main__":
    debug_parsing()