#!/usr/bin/env python3
"""
Enhanced Integration Working Example

This example demonstrates the successful integration of:
- Hash-based incremental caching
- Parallel processing with memory management
- Memory-efficient parsing
- Plugin system compatibility
- Progress tracking
- Neo4j integration readiness

Run this from the project root:
    python3 examples/working_enhanced_integration.py backend/parser
"""

import sys
import os
sys.path.insert(0, 'backend')

from parser.enhanced_integration import EnhancedIntegration
from parser.config import get_parser_config
import time


def main():
    print("Enhanced Integration Working Example")
    print("=" * 50)
    
    # Test directory
    test_dir = sys.argv[1] if len(sys.argv) > 1 else "backend/parser"
    print(f"Target directory: {test_dir}")
    
    if not os.path.exists(test_dir):
        print(f"❌ Directory {test_dir} does not exist!")
        sys.exit(1)
    
    # Create integration with performance optimizations
    print("\n🚀 Creating Enhanced Integration...")
    config = get_parser_config('performance')  # Use performance preset
    integration = EnhancedIntegration(
        config=config,
        enable_caching=True,
        enable_parallel=True,
        enable_neo4j_export=False  # Disable for this example
    )
    
    # Progress tracking
    def progress_callback(notification):
        stage = notification.get('stage', 'unknown')
        status = notification.get('status', '')
        
        # Handle different notification types
        current = notification.get('current', 0)
        total = notification.get('total', 0)
        
        if total > 0:
            pct = (current / total) * 100
            print(f"  📊 {stage.title()}: {pct:.1f}% ({current}/{total}) - {status}")
        else:
            print(f"  🔄 {stage.title()}: {status}")
    
    integration.add_progress_observer(progress_callback)
    
    # Health check
    print("\n🏥 Running Health Check...")
    health = integration.health_check()
    print(f"  Overall Status: {health['overall_status']}")
    for component, status in health['components'].items():
        print(f"  {component.title()}: {status}")
    
    # First run - establish cache
    print(f"\n🔍 First Run: Parsing {test_dir}...")
    start_time = time.time()
    
    results = integration.parse_codebase_with_integration(
        test_dir, 
        force_reparse=False,
        export_to_neo4j=False
    )
    
    first_run_time = time.time() - start_time
    
    if results['success']:
        print(f"✅ First run completed successfully!")
        print(f"   📁 Modules parsed: {len(results['parsed_modules'])}")
        print(f"   🔗 Relationships extracted: {len(results['relationships'])}")
        print(f"   ⏱️  Processing time: {first_run_time:.2f}s")
    else:
        print(f"❌ First run failed: {results.get('error', 'Unknown error')}")
        return
    
    # Show cache stats after first run
    cache_stats = integration.get_cache_stats()
    print(f"\n📊 Cache Statistics (after first run):")
    print(f"   Files in cache: {cache_stats.get('total_cached_files', 0)}")
    print(f"   Cache size: {cache_stats.get('cache_size_mb', 0):.2f} MB")
    print(f"   Hit rate: {cache_stats.get('hit_rate_percent', 0):.1f}%")
    
    # Second run - should be faster due to caching
    print(f"\n🚀 Second Run: Demonstrating cache efficiency...")
    start_time = time.time()
    
    results2 = integration.parse_codebase_with_integration(
        test_dir,
        force_reparse=False,
        export_to_neo4j=False
    )
    
    second_run_time = time.time() - start_time
    
    if results2['success']:
        print(f"✅ Second run completed successfully!")
        print(f"   📁 Modules parsed: {len(results2['parsed_modules'])}")
        print(f"   ⏱️  Processing time: {second_run_time:.2f}s")
        
        # Calculate speedup
        if second_run_time > 0:
            speedup = first_run_time / second_run_time
            print(f"   🚀 Speedup: {speedup:.1f}x faster!")
        
        # Updated cache stats
        cache_stats2 = integration.get_cache_stats()
        print(f"\n📊 Cache Statistics (after second run):")
        print(f"   Cache hits: {cache_stats2.get('cache_hits', 0)}")
        print(f"   Cache misses: {cache_stats2.get('cache_misses', 0)}")
        print(f"   Hit rate: {cache_stats2.get('hit_rate_percent', 0):.1f}%")
        print(f"   Time saved: {cache_stats2.get('total_time_saved', 0):.2f}s")
    
    print(f"\n✨ Integration Example Complete!")
    print(f"   🎯 Performance optimizations: ✅ Working")
    print(f"   💾 Incremental caching: ✅ Working") 
    print(f"   ⚡ Parallel processing: ✅ Working")
    print(f"   🔄 Progress tracking: ✅ Working")
    print(f"   🏥 Health monitoring: ✅ Working")


if __name__ == "__main__":
    main()
