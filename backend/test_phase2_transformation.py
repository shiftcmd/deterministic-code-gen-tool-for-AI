#!/usr/bin/env python3
"""
Test script to verify Phase 2 transformation can consume Phase 1 output.
This script uses the sample Phase 1 output to test tuple generation.
"""

import json
import sys
from pathlib import Path

# Add transformer to path
sys.path.append(str(Path(__file__).parent))

sys.path.append(str(Path(__file__).parent / "transformer"))
from core.tuple_generator import TupleGenerator

def test_phase2_with_sample_data():
    """Test Phase 2 transformation with sample Phase 1 output."""
    
    # Load the sample Phase 1 output
    sample_file = Path(__file__).parent / "sample_phase1_output.json"
    
    if not sample_file.exists():
        print("Error: Sample Phase 1 output not found. Run test_extraction_format.py first.")
        return
    
    with open(sample_file, 'r') as f:
        phase1_data = json.load(f)
    
    print("TESTING PHASE 2 TRANSFORMATION")
    print("=" * 60)
    print(f"Input data: {sample_file}")
    print(f"Module: {phase1_data.get('name', 'unknown')}")
    print(f"Functions: {len(phase1_data.get('functions', []))}")
    print(f"Classes: {len(phase1_data.get('classes', []))}")
    print(f"Imports: {len(phase1_data.get('imports', []))}")
    print()
    
    # Initialize tuple generator
    try:
        generator = TupleGenerator()
        print("✓ TupleGenerator initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize TupleGenerator: {e}")
        return
    
    # Test transformation
    try:
        print("\nGenerating tuples from Phase 1 data...")
        tuple_set = generator.generate_module_tuples(phase1_data['path'], phase1_data)
        
        print(f"✓ Generated tuple set with {tuple_set.size} tuples successfully")
        
        # Display sample tuples
        print("\nSAMPLE GENERATED NODES:")
        print("=" * 60)
        for i, node_tuple in enumerate(tuple_set.nodes[:5]):  # Show first 5 nodes
            print(f"{i+1:2d}. {node_tuple.label}: {node_tuple.unique_key}")
            print(f"     Properties: {node_tuple.properties}")
        
        print("\nSAMPLE GENERATED RELATIONSHIPS:")
        print("=" * 60)
        for i, rel_tuple in enumerate(tuple_set.relationships[:5]):  # Show first 5 relationships
            print(f"{i+1:2d}. {rel_tuple.source_key} -[{rel_tuple.relationship_type}]-> {rel_tuple.target_key}")
            print(f"     Properties: {rel_tuple.properties}")
        
        # Save tuples for inspection
        output_file = Path(__file__).parent / "sample_phase2_output.json"
        tuple_dict = {
            "metadata": tuple_set.metadata,
            "nodes": [node.to_dict() for node in tuple_set.nodes],
            "relationships": [rel.to_dict() for rel in tuple_set.relationships]
        }
        with open(output_file, "w") as f:
            json.dump(tuple_dict, f, indent=2, default=str)
        
        print(f"\nTuples saved to: {output_file}")
        
        # Analysis
        print("\nTUPLE ANALYSIS:")
        print("=" * 60)
        print(f"  Nodes: {len(tuple_set.nodes)}")
        print(f"  Relationships: {len(tuple_set.relationships)}")
        
        node_types = {}
        for node in tuple_set.nodes:
            node_type = node.label
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        rel_types = {}
        for rel in tuple_set.relationships:
            rel_type = rel.relationship_type
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
        
        print("\n  Node types:")
        for node_type, count in sorted(node_types.items()):
            print(f"    {node_type}: {count}")
            
        print("\n  Relationship types:")
        for rel_type, count in sorted(rel_types.items()):
            print(f"    {rel_type}: {count}")
        
        return tuple_set
        
    except Exception as e:
        print(f"✗ Failed to generate tuples: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_specific_entities():
    """Test specific entity types from the sample data."""
    
    sample_file = Path(__file__).parent / "sample_phase1_output.json"
    
    if not sample_file.exists():
        print("Error: Sample Phase 1 output not found.")
        return
    
    with open(sample_file, 'r') as f:
        phase1_data = json.load(f)
    
    print("\nTESTING SPECIFIC ENTITY TRANSFORMATIONS:")
    print("=" * 60)
    
    generator = TupleGenerator()
    module_path = phase1_data['path']
    
    # Test function transformation
    functions = phase1_data.get('functions', [])
    if functions:
        print(f"\nTesting {len(functions)} functions:")
        for func in functions:
            print(f"  - {func['name']}: {func['signature']}")
            try:
                func_tuples = generator._create_function_tuples(module_path, func)
                print(f"    Generated {func_tuples.size} tuples ({len(func_tuples.nodes)} nodes, {len(func_tuples.relationships)} relationships)")
            except Exception as e:
                print(f"    Error: {e}")
    
    # Test class transformation
    classes = phase1_data.get('classes', [])
    if classes:
        print(f"\nTesting {len(classes)} classes:")
        for cls in classes:
            print(f"  - {cls['name']}: {cls.get('bases', [])}")
            try:
                class_tuples = generator._create_class_tuples(module_path, cls)
                print(f"    Generated {class_tuples.size} tuples ({len(class_tuples.nodes)} nodes, {len(class_tuples.relationships)} relationships)")
            except Exception as e:
                print(f"    Error: {e}")
    
    # Test import transformation
    imports = phase1_data.get('imports', [])
    if imports:
        print(f"\nTesting {len(imports)} imports:")
        for imp in imports:
            name = imp['name']
            fromname = imp.get('fromname')
            print(f"  - {'from ' + fromname + ' ' if fromname else ''}import {name}")
            try:
                import_rel = generator._create_import_relationship(module_path, imp)
                if import_rel:
                    print(f"    Generated 1 relationship tuple")
                else:
                    print(f"    No relationship generated")
            except Exception as e:
                print(f"    Error: {e}")

if __name__ == "__main__":
    # Run basic transformation test
    tuple_set = test_phase2_with_sample_data()
    
    if tuple_set is not None:
        print("\n" + "=" * 60)
        print("PHASE 2 TRANSFORMATION TEST: PASSED ✓")
        
        # Run detailed entity tests
        test_specific_entities()
    else:
        print("\n" + "=" * 60)
        print("PHASE 2 TRANSFORMATION TEST: FAILED ✗")