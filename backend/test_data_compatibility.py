#!/usr/bin/env python3
"""
Test script to verify Phase 1 and Phase 2 data format compatibility.
This checks the data structure without importing the actual transformation code.
"""

import json
from pathlib import Path

def analyze_phase1_output():
    """Analyze the Phase 1 output format."""
    
    sample_file = Path(__file__).parent / "sample_phase1_output.json"
    
    if not sample_file.exists():
        print("Error: Sample Phase 1 output not found. Run test_extraction_format.py first.")
        return None
    
    with open(sample_file, 'r') as f:
        phase1_data = json.load(f)
    
    print("PHASE 1 OUTPUT ANALYSIS")
    print("=" * 60)
    print(f"Module: {phase1_data.get('name', 'unknown')}")
    print(f"Path: {phase1_data.get('path', 'unknown')}")
    print(f"Line count: {phase1_data.get('line_count', 0)}")
    print(f"Size bytes: {phase1_data.get('size_bytes', 0)}")
    print()
    
    # Analyze data structure
    required_fields = ["name", "path", "docstring", "imports", "classes", "functions", "variables"]
    missing_fields = []
    
    print("REQUIRED FIELDS CHECK:")
    print("-" * 30)
    for field in required_fields:
        if field in phase1_data:
            value = phase1_data[field]
            if isinstance(value, list):
                print(f"✓ {field}: {len(value)} items")
            else:
                print(f"✓ {field}: {type(value).__name__}")
        else:
            print(f"✗ {field}: MISSING")
            missing_fields.append(field)
    
    if missing_fields:
        print(f"\nWARNING: Missing required fields: {missing_fields}")
    
    # Analyze imports
    imports = phase1_data.get("imports", [])
    if imports:
        print(f"\nIMPORTS ANALYSIS ({len(imports)} items):")
        print("-" * 30)
        sample_import = imports[0]
        import_fields = ["name", "asname", "fromname", "line_start", "line_end", "is_star", "symbols"]
        
        for field in import_fields:
            if field in sample_import:
                print(f"✓ {field}: {type(sample_import[field]).__name__}")
            else:
                print(f"✗ {field}: MISSING")
    
    # Analyze functions
    functions = phase1_data.get("functions", [])
    if functions:
        print(f"\nFUNCTIONS ANALYSIS ({len(functions)} items):")
        print("-" * 30)
        sample_function = functions[0]
        function_fields = ["name", "signature", "docstring", "parameters", "return_type", 
                          "variables", "nested_functions", "line_start", "line_end", 
                          "decorators", "is_method", "is_static", "is_class_method", 
                          "complexity", "imports"]
        
        for field in function_fields:
            if field in sample_function:
                value = sample_function[field]
                if isinstance(value, list):
                    print(f"✓ {field}: list with {len(value)} items")
                else:
                    print(f"✓ {field}: {type(value).__name__}")
            else:
                print(f"✗ {field}: MISSING")
    
    # Analyze classes
    classes = phase1_data.get("classes", [])
    if classes:
        print(f"\nCLASSES ANALYSIS ({len(classes)} items):")
        print("-" * 30)
        sample_class = classes[0]
        class_fields = ["name", "bases", "docstring", "methods", "attributes", 
                       "line_start", "line_end", "decorators", "inner_classes", 
                       "imported_types", "metaclass"]
        
        for field in class_fields:
            if field in sample_class:
                value = sample_class[field]
                if isinstance(value, list):
                    print(f"✓ {field}: list with {len(value)} items")
                else:
                    print(f"✓ {field}: {type(value).__name__}")
            else:
                print(f"✗ {field}: MISSING")
    
    return phase1_data

def validate_tuple_generation_requirements():
    """Validate that Phase 1 data has required fields for tuple generation."""
    
    sample_file = Path(__file__).parent / "sample_phase1_output.json"
    
    if not sample_file.exists():
        return False
    
    with open(sample_file, 'r') as f:
        phase1_data = json.load(f)
    
    print("\nTUPLE GENERATION REQUIREMENTS CHECK:")
    print("=" * 60)
    
    # Check module-level requirements
    module_requirements = {
        "path": "string",
        "name": "string",
        "docstring": "string or null",
        "line_count": "number",
        "size_bytes": "number"
    }
    
    print("Module node requirements:")
    all_passed = True
    for field, expected_type in module_requirements.items():
        if field in phase1_data:
            value = phase1_data[field]
            if "string" in expected_type and isinstance(value, str):
                print(f"  ✓ {field}: string")
            elif "number" in expected_type and isinstance(value, int):
                print(f"  ✓ {field}: number")
            elif "null" in expected_type and (value is None or isinstance(value, str)):
                print(f"  ✓ {field}: {type(value).__name__}")
            else:
                print(f"  ✗ {field}: expected {expected_type}, got {type(value).__name__}")
                all_passed = False
        else:
            print(f"  ✗ {field}: MISSING")
            all_passed = False
    
    # Check import requirements
    imports = phase1_data.get("imports", [])
    if imports:
        print(f"\nImport relationship requirements ({len(imports)} imports):")
        sample_import = imports[0]
        import_requirements = {
            "name": "string",
            "fromname": "string or null",
            "line_start": "number",
            "line_end": "number"
        }
        
        for field, expected_type in import_requirements.items():
            if field in sample_import:
                value = sample_import[field]
                if "string" in expected_type and isinstance(value, str):
                    print(f"  ✓ {field}: string")
                elif "number" in expected_type and isinstance(value, int):
                    print(f"  ✓ {field}: number") 
                elif "null" in expected_type and (value is None or isinstance(value, str)):
                    print(f"  ✓ {field}: {type(value).__name__}")
                else:
                    print(f"  ✗ {field}: expected {expected_type}, got {type(value).__name__}")
                    all_passed = False
            else:
                print(f"  ✗ {field}: MISSING")
                all_passed = False
    
    # Check function requirements
    functions = phase1_data.get("functions", [])
    if functions:
        print(f"\nFunction node requirements ({len(functions)} functions):")
        sample_function = functions[0]
        function_requirements = {
            "name": "string",
            "signature": "string",
            "line_start": "number",
            "line_end": "number"
        }
        
        for field, expected_type in function_requirements.items():
            if field in sample_function:
                value = sample_function[field]
                if "string" in expected_type and isinstance(value, str):
                    print(f"  ✓ {field}: string")
                elif "number" in expected_type and isinstance(value, int):
                    print(f"  ✓ {field}: number")
                else:
                    print(f"  ✗ {field}: expected {expected_type}, got {type(value).__name__}")
                    all_passed = False
            else:
                print(f"  ✗ {field}: MISSING")
                all_passed = False
    
    # Check class requirements
    classes = phase1_data.get("classes", [])
    if classes:
        print(f"\nClass node requirements ({len(classes)} classes):")
        sample_class = classes[0]
        class_requirements = {
            "name": "string",
            "bases": "list",
            "line_start": "number",
            "line_end": "number"
        }
        
        for field, expected_type in class_requirements.items():
            if field in sample_class:
                value = sample_class[field]
                if "string" in expected_type and isinstance(value, str):
                    print(f"  ✓ {field}: string")
                elif "list" in expected_type and isinstance(value, list):
                    print(f"  ✓ {field}: list")
                elif "number" in expected_type and isinstance(value, int):
                    print(f"  ✓ {field}: number")
                else:
                    print(f"  ✗ {field}: expected {expected_type}, got {type(value).__name__}")
                    all_passed = False
            else:
                print(f"  ✗ {field}: MISSING")
                all_passed = False
    
    return all_passed

def create_mock_phase2_output():
    """Create a mock Phase 2 output based on the Phase 1 data structure."""
    
    sample_file = Path(__file__).parent / "sample_phase1_output.json"
    
    if not sample_file.exists():
        return None
    
    with open(sample_file, 'r') as f:
        phase1_data = json.load(f)
    
    print("\nMOCK PHASE 2 OUTPUT GENERATION:")
    print("=" * 60)
    
    # Mock tuple generation
    nodes = []
    relationships = []
    
    # Create module node
    module_path = phase1_data.get("path", "")
    module_node = {
        "label": "Module",
        "unique_key": f"module:{module_path}",
        "properties": {
            "path": module_path,
            "name": phase1_data.get("name", ""),
            "line_count": phase1_data.get("line_count", 0),
            "size_bytes": phase1_data.get("size_bytes", 0),
            "docstring": phase1_data.get("docstring", "")
        },
        "merge_properties": ["path"]
    }
    nodes.append(module_node)
    
    # Create function nodes and relationships
    for func_data in phase1_data.get("functions", []):
        func_name = func_data.get("name", "")
        func_key = f"function:{module_path}:{func_name}"
        
        function_node = {
            "label": "Function",
            "unique_key": func_key,
            "properties": {
                "name": func_name,
                "module_path": module_path,
                "signature": func_data.get("signature", ""),
                "docstring": func_data.get("docstring", ""),
                "line_start": func_data.get("line_start", 0),
                "line_end": func_data.get("line_end", 0),
                "return_type": func_data.get("return_type", "")
            },
            "merge_properties": ["name", "module_path"]
        }
        nodes.append(function_node)
        
        # Create CONTAINS relationship
        contains_rel = {
            "source_key": f"module:{module_path}",
            "target_key": func_key,
            "relationship_type": "CONTAINS",
            "properties": {
                "line_start": func_data.get("line_start", 0),
                "line_end": func_data.get("line_end", 0)
            },
            "source_label": "Module",
            "target_label": "Function"
        }
        relationships.append(contains_rel)
    
    # Create class nodes and relationships
    for class_data in phase1_data.get("classes", []):
        class_name = class_data.get("name", "")
        class_key = f"class:{module_path}:{class_name}"
        
        class_node = {
            "label": "Class",
            "unique_key": class_key,
            "properties": {
                "name": class_name,
                "module_path": module_path,
                "docstring": class_data.get("docstring", ""),
                "line_start": class_data.get("line_start", 0),
                "line_end": class_data.get("line_end", 0),
                "bases": class_data.get("bases", [])
            },
            "merge_properties": ["name", "module_path"]
        }
        nodes.append(class_node)
        
        # Create CONTAINS relationship
        contains_rel = {
            "source_key": f"module:{module_path}",
            "target_key": class_key,
            "relationship_type": "CONTAINS",
            "properties": {
                "line_start": class_data.get("line_start", 0),
                "line_end": class_data.get("line_end", 0)
            },
            "source_label": "Module",
            "target_label": "Class"
        }
        relationships.append(contains_rel)
    
    # Create import relationships
    for import_data in phase1_data.get("imports", []):
        target_module = import_data.get("fromname") or import_data.get("name", "")
        if target_module:
            import_rel = {
                "source_key": f"module:{module_path}",
                "target_key": f"module:{target_module}",
                "relationship_type": "IMPORTS",
                "properties": {
                    "import_name": import_data.get("name", ""),
                    "asname": import_data.get("asname", ""),
                    "fromname": import_data.get("fromname", ""),
                    "line_start": import_data.get("line_start", 0)
                },
                "source_label": "Module",
                "target_label": "Module"
            }
            relationships.append(import_rel)
    
    mock_output = {
        "metadata": {
            "module_path": module_path,
            "module_name": phase1_data.get("name", ""),
            "generated_at": "2025-01-24T12:00:00Z",
            "line_count": phase1_data.get("line_count", 0)
        },
        "nodes": nodes,
        "relationships": relationships
    }
    
    # Save mock output
    output_file = Path(__file__).parent / "mock_phase2_output.json"
    with open(output_file, "w") as f:
        json.dump(mock_output, f, indent=2)
    
    print(f"Mock Phase 2 output generated with:")
    print(f"  - {len(nodes)} nodes")
    print(f"  - {len(relationships)} relationships")
    print(f"  - Saved to: {output_file}")
    
    return mock_output

if __name__ == "__main__":
    # Analyze Phase 1 output
    phase1_data = analyze_phase1_output()
    
    if phase1_data:
        # Validate requirements
        requirements_passed = validate_tuple_generation_requirements()
        
        # Create mock Phase 2 output
        mock_output = create_mock_phase2_output()
        
        print("\n" + "=" * 60)
        if requirements_passed:
            print("DATA COMPATIBILITY TEST: PASSED ✓")
            print("Phase 1 output format is compatible with Phase 2 transformation")
        else:
            print("DATA COMPATIBILITY TEST: ISSUES FOUND ⚠")
            print("Some requirements for Phase 2 transformation are not met")
    else:
        print("DATA COMPATIBILITY TEST: FAILED ✗")
        print("Could not analyze Phase 1 output")