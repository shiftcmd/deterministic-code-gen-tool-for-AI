#!/usr/bin/env python3
"""
Example demonstrating incremental parsing with hash-based caching.

This example shows how the Task 2.3 implementation provides significant
performance improvements for large codebases through intelligent caching.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any

# Set up logging to see the caching in action
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import our enhanced parser components
from backend.parser.codebase_parser import CodebaseParser
from backend.parser.config import get_parser_config

logger = logging.getLogger(__name__)


def demonstrate_incremental_parsing():
    """Demonstrate the benefits of incremental parsing with caching."""
    
    print("=" * 80)
    print("INCREMENTAL PARSING WITH HASH-BASED CACHING DEMONSTRATION")
    print("=" * 80)
    
    # Use the project's own codebase as test data
    project_root = Path(__file__).parent.parent
    backend_dir = project_root / "backend"
    
    if not backend_dir.exists():
        print(f"Backend directory not found: {backend_dir}")
        print("Please run this example from the project root directory.")
        return
    
    # Configure parser with caching enabled
    config = get_parser_config("standard")
    config.cache_results = True
    config.parallel_processing = True
    
    parser = CodebaseParser(config)
    
    # First run - cold cache
    print("\n🔥 FIRST RUN - Cold Cache")
    print("-" * 40)
    
    start_time = time.time()
    results_first = parser.parse_codebase(str(backend_dir))
    first_duration = time.time() - start_time
    
    first_metrics = parser.get_processing_metrics()
    cache_stats = parser.get_cache_stats()
    
    print(f"✅ First run completed in {first_duration:.2f} seconds")
    print(f"📁 Parsed {len(results_first)} files")
    print(f"📊 Processing metrics:")
    print(f"   - Files processed: {first_metrics['processed_files']}")
    print(f"   - Success rate: {first_metrics['success_rate']:.1f}%")
    print(f"   - Files per second: {first_metrics['files_per_second']:.1f}")
    print(f"🗂️ Cache stats after first run:")
    print(f"   - Cache hits: {cache_stats['cache_hits']}")
    print(f"   - Cache misses: {cache_stats['cache_misses']}")
    print(f"   - Total cached files: {cache_stats['total_cached_files']}")
    print(f"   - Cache size: {cache_stats['cache_size_mb']:.2f} MB")
    
    # Second run - warm cache (no changes)
    print("\n🚀 SECOND RUN - Warm Cache (No Changes)")
    print("-" * 40)
    
    start_time = time.time()
    results_second = parser.parse_codebase(str(backend_dir))
    second_duration = time.time() - start_time
    
    second_metrics = parser.get_processing_metrics()
    cache_stats = parser.get_cache_stats()
    
    print(f"✅ Second run completed in {second_duration:.2f} seconds")
    print(f"📁 Parsed {len(results_second)} files")
    print(f"⚡ Speed improvement: {(first_duration / second_duration):.1f}x faster")
    print(f"📊 Processing metrics:")
    print(f"   - Files processed: {second_metrics['processed_files']}")
    print(f"   - Success rate: {second_metrics['success_rate']:.1f}%")
    print(f"🗂️ Cache stats after second run:")
    print(f"   - Cache hits: {cache_stats['cache_hits']}")
    print(f"   - Hit rate: {cache_stats['hit_rate_percent']:.1f}%")
    print(f"   - Time saved: {cache_stats['total_time_saved']:.2f} seconds")
    
    # Simulate file change by invalidating cache for one file
    print("\n🔄 SIMULATING FILE CHANGE")
    print("-" * 40)
    
    if results_first:
        sample_file = list(results_first.keys())[0]
        print(f"📝 Invalidating cache for: {Path(sample_file).name}")
        parser.invalidate_file_cache(sample_file)
        
        start_time = time.time()
        results_changed = parser.parse_codebase(str(backend_dir))
        changed_duration = time.time() - start_time
        
        changed_metrics = parser.get_processing_metrics()
        cache_stats = parser.get_cache_stats()
        
        print(f"✅ Run with changed file completed in {changed_duration:.2f} seconds")
        print(f"📊 Only changed files were re-parsed:")
        print(f"   - Files processed: {changed_metrics['processed_files']}")
        print(f"   - Cache hits: {cache_stats['cache_hits']}")
        print(f"   - Hit rate: {cache_stats['hit_rate_percent']:.1f}%")
    
    # Cache management demonstration
    print("\n🧹 CACHE MANAGEMENT")
    print("-" * 40)
    
    cache_stats = parser.get_cache_stats()
    print(f"📈 Current cache statistics:")
    print(f"   - Total cached files: {cache_stats['total_cached_files']}")
    print(f"   - Cache size: {cache_stats['cache_size_mb']:.2f} MB")
    print(f"   - Hit rate: {cache_stats['hit_rate_percent']:.1f}%")
    
    # Cleanup old cache entries (demo with 0 days to show functionality)
    print("\n🗑️ Cleaning up stale cache entries...")
    removed_count = parser.cleanup_stale_cache(max_age_days=0)  # Remove all for demo
    print(f"   - Removed {removed_count} stale entries")
    
    # Show final cache stats
    final_cache_stats = parser.get_cache_stats()
    print(f"📊 Cache stats after cleanup:")
    print(f"   - Total cached files: {final_cache_stats['total_cached_files']}")
    print(f"   - Cache size: {final_cache_stats['cache_size_mb']:.2f} MB")
    
    print("\n" + "=" * 80)
    print("🎉 INCREMENTAL PARSING DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\nKey Benefits Demonstrated:")
    print("• ⚡ Significant speed improvements on subsequent runs")
    print("• 🎯 Selective re-parsing of only changed files")
    print("• 📊 Comprehensive cache performance metrics")
    print("• 🧹 Intelligent cache management and cleanup")
    print("• 💾 Persistent caching across application restarts")
    print("\nThis is the power of Task 2.3: Hash-based Caching!")


def show_cache_configuration_options():
    """Show different cache configuration options."""
    
    print("\n" + "=" * 60)
    print("CACHE CONFIGURATION OPTIONS")
    print("=" * 60)
    
    configs = {
        "Minimal": get_parser_config("minimal"),
        "Standard": get_parser_config("standard"), 
        "Performance": get_parser_config("performance"),
        "Comprehensive": get_parser_config("comprehensive")
    }
    
    for name, config in configs.items():
        print(f"\n{name} Configuration:")
        print(f"  - Cache enabled: {config.cache_results}")
        print(f"  - Parallel processing: {config.parallel_processing}")
        
        if 'parallel' in config.tool_options:
            parallel_opts = config.tool_options['parallel']
            print(f"  - Max memory: {parallel_opts.get('max_memory_mb', 'default')} MB")
            print(f"  - Strategy: {parallel_opts.get('strategy', 'default')}")
            print(f"  - Progress tracking: {parallel_opts.get('progress_tracking', False)}")


if __name__ == "__main__":
    try:
        demonstrate_incremental_parsing()
        show_cache_configuration_options()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Please make sure you're running from the project root directory")
        print("and that all dependencies are installed.")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
