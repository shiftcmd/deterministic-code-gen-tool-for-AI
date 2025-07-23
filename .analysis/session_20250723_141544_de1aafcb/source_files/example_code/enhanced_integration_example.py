#!/usr/bin/env python3
"""
Enhanced Integration Example - Demonstrating Task 2.5 Integration

This example shows how to use the new EnhancedIntegration class that combines:
- Hash-based incremental caching
- Parallel processing with memory management  
- Memory-efficient parsing
- Neo4j graph database export
- Progress tracking and comprehensive metrics

Usage:
    python examples/enhanced_integration_example.py [path_to_codebase]
"""

import os
import sys
import time
from pathlib import Path

# Add the backend path to sys.path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from parser.enhanced_integration import EnhancedIntegration
from parser.config import get_parser_config


def progress_callback(notification):
    """Progress callback for real-time updates."""
    stage = notification.get('stage', 'unknown')
    status = notification.get('status', 'unknown')
    
    if stage == 'discovery':
        if status == 'discovering_files':
            print("🔍 Discovering Python files...")
        elif status == 'completed':
            files_found = notification.get('files_found', 0)
            print(f"✅ Found {files_found} Python files")
    
    elif stage == 'cache_analysis':
        if status == 'analyzing_cache':
            print("🗄️  Analyzing cache...")
        elif status == 'completed':
            changed = notification.get('changed_files', 0)
            cached = notification.get('cached_files', 0)
            hit_rate = notification.get('hit_rate', 0) * 100
            print(f"✅ Cache analysis: {changed} changed, {cached} cached ({hit_rate:.1f}% hit rate)")
    
    elif stage == 'parsing':
        if status == 'parsing_files':
            files_to_parse = notification.get('files_to_parse', 0)
            print(f"⚙️  Parsing {files_to_parse} files...")
        elif status == 'completed':
            files_parsed = notification.get('files_parsed', 0)
            duration = notification.get('duration', 0)
            print(f"✅ Parsed {files_parsed} files in {duration:.2f}s")
    
    elif stage == 'relationships':
        if status == 'extracting_relationships':
            modules = notification.get('modules_to_process', 0)
            print(f"🔗 Extracting relationships from {modules} modules...")
        elif status == 'completed':
            relationships = notification.get('relationships_extracted', 0)
            duration = notification.get('duration', 0)
            print(f"✅ Extracted {relationships} relationships in {duration:.2f}s")
    
    elif stage == 'cache_update':
        if status == 'updating_cache':
            print("💾 Updating cache...")
        elif status == 'completed':
            print("✅ Cache updated")
    
    elif stage == 'neo4j_export':
        if status == 'exporting_to_neo4j':
            modules = notification.get('modules_to_export', 0)
            print(f"🎯 Exporting {modules} modules to Neo4j...")
        elif status == 'completed':
            nodes = notification.get('nodes_created', 0)
            relationships = notification.get('relationships_created', 0)
            duration = notification.get('duration', 0)
            print(f"✅ Neo4j export: {nodes} nodes, {relationships} relationships in {duration:.2f}s")
    
    elif stage == 'completed':
        total_duration = notification.get('total_duration', 0)
        print(f"🎉 Integration completed in {total_duration:.2f}s")
    
    elif stage == 'error':
        error = notification.get('error', 'Unknown error')
        print(f"❌ Error: {error}")


def main():
    """Main demonstration function."""
    print("Enhanced Integration Example")
    print("=" * 40)
    
    # Get target directory
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        # Default to parsing the backend directory itself
        target_dir = str(Path(__file__).parent.parent / "backend")
    
    if not os.path.exists(target_dir):
        print(f"Error: Directory '{target_dir}' does not exist")
        sys.exit(1)
    
    print(f"Target directory: {target_dir}")
    print()
    
    # Demo 1: Performance-optimized configuration
    print("🚀 Demo 1: Performance-Optimized Integration")
    print("-" * 45)
    
    # Use performance preset for maximum speed
    config = get_parser_config("performance")
    
    # Neo4j configuration
    neo4j_options = {
        "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "password"),
        "database": "python_debug_tool",
        "batch_size": 1000,  # Large batches for performance
        "clear_existing": False,  # Don't clear existing data
        "detect_architecture": True,  # Enable architectural analysis
        "include_content": False  # Exclude code content for performance
    }
    
    # Create integration instance
    integration = EnhancedIntegration(
        config=config,
        neo4j_options=neo4j_options,
        enable_caching=True,
        enable_parallel=True,
        enable_neo4j_export=True
    )
    
    # Add progress observer
    integration.add_progress_observer(progress_callback)
    
    # Health check first
    print("🔍 Performing health check...")
    health = integration.health_check()
    print(f"System health: {health['overall_status']}")
    for component, status in health['components'].items():
        print(f"  {component}: {status}")
    
    if health['overall_status'] != 'healthy':
        print("⚠️  System not fully healthy, but continuing...")
    
    print()
    
    # Run the integration
    start_time = time.time()
    results = integration.parse_codebase_with_integration(
        root_path=target_dir,
        force_reparse=False,  # Use cache when possible
        export_to_neo4j=True
    )
    
    print()
    print("📊 Results Summary")
    print("-" * 20)
    
    if results['success']:
        metrics = results['metrics']
        print(f"Total files: {metrics['total_files']}")
        print(f"Cached files: {metrics['cached_files']}")
        print(f"Parsed files: {metrics['parsed_files']}")
        print(f"Failed files: {metrics['failed_files']}")
        print(f"Cache hit rate: {metrics['cache_hit_rate']:.1%}")
        print(f"Relationships extracted: {metrics['relationships_extracted']}")
        
        if results.get('neo4j_export', {}).get('enabled'):
            neo4j = results['neo4j_export']
            print(f"Neo4j nodes created: {neo4j['nodes_created']}")
            print(f"Neo4j relationships created: {neo4j['relationships_created']}")
        
        print()
        print("⏱️  Performance Breakdown")
        print(f"Parsing: {metrics['parsing_duration']:.2f}s")
        print(f"Relationship extraction: {metrics['relationship_extraction_duration']:.2f}s")
        print(f"Neo4j export: {metrics['neo4j_export_duration']:.2f}s")
        print(f"Total: {metrics['total_duration']:.2f}s")
        
        # Calculate throughput
        if metrics['total_duration'] > 0:
            files_per_sec = metrics['total_files'] / metrics['total_duration']
            print(f"Throughput: {files_per_sec:.1f} files/second")
    
    else:
        print(f"❌ Integration failed: {results.get('error', 'Unknown error')}")
    
    print()
    
    # Demo 2: Cache efficiency demonstration
    print("🗄️  Demo 2: Cache Efficiency Test")
    print("-" * 35)
    
    if results['success']:
        # Run again to show cache performance
        print("Running again to demonstrate cache efficiency...")
        
        start_time = time.time()
        results2 = integration.parse_codebase_with_integration(
            root_path=target_dir,
            force_reparse=False,
            export_to_neo4j=False  # Skip Neo4j export for cache demo
        )
        
        if results2['success']:
            metrics2 = results2['metrics']
            print(f"Second run - Cache hit rate: {metrics2['cache_hit_rate']:.1%}")
            print(f"Second run - Total duration: {metrics2['total_duration']:.2f}s")
            
            # Compare performance
            speedup = results['metrics']['total_duration'] / metrics2['total_duration']
            print(f"Speedup from caching: {speedup:.1f}x")
    
    print()
    
    # Demo 3: Cache management
    print("🧹 Demo 3: Cache Management")
    print("-" * 28)
    
    if integration.cache:
        cache_stats = integration.cache.get_cache_stats()
        print("Cache statistics:")
        for key, value in cache_stats.items():
            print(f"  {key}: {value}")
        
        print()
        print("Cache management operations:")
        
        # Demonstrate cache cleanup
        print("- Cleaning up stale cache entries...")
        removed = integration.cache.cleanup_stale_cache(max_age_days=0)  # Remove very old entries
        print(f"  Removed {removed} stale entries")
        
        # Show cache size
        cache_size_mb = integration.cache._get_cache_size_mb()
        print(f"- Current cache size: {cache_size_mb:.2f} MB")
    
    print()
    print("✅ Enhanced Integration Example Complete!")


if __name__ == "__main__":
    main()
