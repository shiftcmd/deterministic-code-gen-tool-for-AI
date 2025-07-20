# Performance Configuration Guide

## Overview

This guide covers all configuration options for the performance optimization features including parallel processing, memory-efficient parsing, and hash-based caching.

## Quick Start

### Basic Configuration

```python
from backend.parser.config import get_parser_config
from backend.parser.codebase_parser import CodebaseParser

# Use preset configuration
config = get_parser_config("standard")
parser = CodebaseParser(config)

# Parse with optimizations enabled
results = parser.parse_codebase("/path/to/project")
```

### Environment Variables

Create a `.env` file in your project root:

```bash
# Essential Performance Settings
PARSER_CACHE_ENABLED=true
PARSER_PARALLEL_PROCESSING=true
PARSER_MAX_WORKERS=auto

# Memory Management
PARSER_MAX_MEMORY_MB=2048
PARSER_MEMORY_THRESHOLD_MB=512
PARSER_CHUNK_SIZE_KB=256

# Cache Settings
PARSER_CACHE_DIR=.cache/parser
PARSER_CACHE_MAX_SIZE_MB=1024
PARSER_CACHE_CLEANUP_DAYS=30
```

## Configuration Presets

### 1. Minimal Preset
**Use Case**: Resource-constrained environments, CI/CD pipelines

```python
config = get_parser_config("minimal")
```

**Settings**:
- **Parallel Workers**: 2
- **Memory Limit**: 512 MB
- **Cache**: Disabled
- **Strategy**: Thread-based only
- **Chunk Size**: 128 KB

**Best For**:
- Docker containers with limited resources
- Shared CI/CD runners
- Development environments with other memory-intensive applications

### 2. Standard Preset (Recommended)
**Use Case**: Most development environments

```python
config = get_parser_config("standard")
```

**Settings**:
- **Parallel Workers**: CPU count
- **Memory Limit**: 1024 MB  
- **Cache**: Enabled with 30-day cleanup
- **Strategy**: Adaptive
- **Chunk Size**: 256 KB

**Best For**:
- Local development
- Code analysis workflows
- Regular codebase exploration

### 3. Performance Preset
**Use Case**: High-performance analysis, large codebases

```python
config = get_parser_config("performance")
```

**Settings**:
- **Parallel Workers**: CPU count × 2
- **Memory Limit**: 4096 MB
- **Cache**: Enabled with aggressive prefetching
- **Strategy**: Hybrid with process-based fallback
- **Chunk Size**: 512 KB

**Best For**:
- Large enterprise codebases
- Batch processing jobs
- Performance-critical analysis

### 4. Comprehensive Preset
**Use Case**: Maximum analysis depth with all features enabled

```python
config = get_parser_config("comprehensive")
```

**Settings**:
- **Parallel Workers**: CPU count × 1.5
- **Memory Limit**: 2048 MB
- **Cache**: Enabled with relationship caching
- **Strategy**: Adaptive with memory-efficient parsing
- **Features**: All relationship extraction, cross-file analysis

**Best For**:
- Research and deep analysis
- Architecture reviews
- Complete codebase documentation

## Detailed Configuration Options

### Parallel Processing Configuration

```python
config.tool_options['parallel'] = {
    'max_workers': 8,              # Number of parallel workers
    'strategy': 'adaptive',        # Processing strategy
    'max_memory_mb': 2048,         # Memory limit per worker
    'progress_tracking': True,     # Enable progress observers
    'error_recovery': True,        # Enable error recovery
    'retry_attempts': 3,           # Max retry attempts
    'retry_delay': 1.0,           # Delay between retries (seconds)
}
```

#### Processing Strategies

**Thread-Based** (`thread_based`)
```python
config.tool_options['parallel']['strategy'] = 'thread_based'
```
- **Best For**: I/O-bound tasks, many small files
- **Memory Usage**: Lower
- **CPU Usage**: Limited by GIL
- **Concurrency**: High for I/O operations

**Process-Based** (`process_based`)
```python
config.tool_options['parallel']['strategy'] = 'process_based'
```
- **Best For**: CPU-intensive analysis, large files
- **Memory Usage**: Higher (per process)
- **CPU Usage**: Full multi-core utilization
- **Concurrency**: True parallelism

**Hybrid** (`hybrid`)
```python
config.tool_options['parallel']['strategy'] = 'hybrid'
```
- **Best For**: Mixed workloads
- **Behavior**: Thread pool for I/O, process pool for CPU tasks
- **Memory Usage**: Dynamic based on task type
- **CPU Usage**: Optimal for varied workloads

**Adaptive** (`adaptive`) - **Recommended**
```python
config.tool_options['parallel']['strategy'] = 'adaptive'
```
- **Best For**: Unknown or varying workloads
- **Behavior**: Automatically selects optimal strategy
- **Decision Factors**: File sizes, system resources, task count
- **Fallback**: Graceful degradation on resource constraints

### Memory-Efficient Parsing Configuration

```python
config.tool_options['memory'] = {
    'use_efficient_parsing_mb': 512,    # Threshold for efficient parsing (KB)
    'chunk_size_kb': 256,               # Size of processing chunks
    'chunk_overlap_lines': 10,          # Overlap between chunks  
    'chunking_strategy': 'ast_based',   # Chunking method
    'memory_limit_mb': 1024,            # Memory limit for parsing
    'memory_warning_mb': 800,           # Warning threshold
    'gc_threshold': 1000,               # Objects before GC
    'object_pool_size': 50,             # Size of object pool
}
```

#### Chunking Strategies

**AST-Based** (`ast_based`) - **Recommended**
```python
config.tool_options['memory']['chunking_strategy'] = 'ast_based'
```
- **Behavior**: Splits at function/class boundaries
- **Advantages**: Preserves code structure integrity
- **Use Case**: Most Python files with clear structure

**Line-Based** (`line_based`)
```python
config.tool_options['memory']['chunking_strategy'] = 'line_based'
```
- **Behavior**: Fixed line-count chunks
- **Advantages**: Predictable, simple
- **Use Case**: Scripts, configuration files

**Size-Based** (`size_based`)
```python
config.tool_options['memory']['chunking_strategy'] = 'size_based'
```
- **Behavior**: Fixed byte-size chunks
- **Advantages**: Consistent memory usage
- **Use Case**: Large generated files, data files

### Hash-Based Cache Configuration

```python
config.tool_options['cache'] = {
    'cache_dir': '.cache/parser',       # Cache directory
    'max_cache_size_mb': 1024,          # Maximum cache size
    'cleanup_interval_hours': 24,       # Automatic cleanup interval
    'max_age_days': 30,                # Maximum cache entry age
    'compression_enabled': True,        # Enable cache compression
    'validation_enabled': True,         # Enable cache validation
    'hash_algorithm': 'blake2b',        # Hashing algorithm
    'batch_size': 100,                 # Batch size for operations
}
```

#### Cache Strategies

**Aggressive Caching**
```python
config.tool_options['cache'].update({
    'max_cache_size_mb': 2048,
    'max_age_days': 90,
    'prefetch_enabled': True,
})
```
- **Use Case**: Development environments, frequent re-analysis
- **Trade-offs**: Higher disk usage, faster subsequent runs

**Conservative Caching** 
```python
config.tool_options['cache'].update({
    'max_cache_size_mb': 256,
    'max_age_days': 7,
    'cleanup_interval_hours': 6,
})
```
- **Use Case**: Limited disk space, infrequent analysis
- **Trade-offs**: Lower disk usage, more cache misses

**Disabled Caching**
```python
config.cache_results = False
```
- **Use Case**: One-time analysis, debugging, CI/CD
- **Trade-offs**: No disk usage, slower on repeat analysis

## Advanced Configuration

### Custom Configuration

```python
from backend.parser.config import ParserConfig

# Create custom configuration
config = ParserConfig(
    cache_results=True,
    parallel_processing=True,
    max_file_size_mb=50,
    ignore_patterns=['.git', '__pycache__', '*.pyc'],
    tool_options={
        'parallel': {
            'max_workers': 4,
            'strategy': 'hybrid',
            'max_memory_mb': 1024,
        },
        'memory': {
            'use_efficient_parsing_mb': 256 * 1024,  # 256KB
            'chunk_size_kb': 128,
            'chunking_strategy': 'ast_based',
        },
        'cache': {
            'cache_dir': '/tmp/parser_cache',
            'max_cache_size_mb': 512,
            'max_age_days': 15,
        }
    }
)
```

### Dynamic Configuration

```python
# Adjust configuration based on system resources
import psutil

def get_optimized_config():
    memory_gb = psutil.virtual_memory().total / (1024**3)
    cpu_count = psutil.cpu_count()
    
    if memory_gb < 4:
        return get_parser_config("minimal")
    elif memory_gb < 8:
        return get_parser_config("standard")
    else:
        config = get_parser_config("performance")
        config.tool_options['parallel']['max_workers'] = min(cpu_count * 2, 16)
        return config
```

### Environment-Specific Configurations

#### Docker/Container Environment
```python
config = get_parser_config("minimal")
config.tool_options.update({
    'parallel': {
        'max_workers': 2,
        'max_memory_mb': 512,
        'strategy': 'thread_based',
    },
    'memory': {
        'memory_limit_mb': 256,
        'chunk_size_kb': 64,
    }
})
```

#### High-Memory Server
```python
config = get_parser_config("performance")
config.tool_options.update({
    'parallel': {
        'max_workers': 32,
        'max_memory_mb': 8192,
        'strategy': 'process_based',
    },
    'memory': {
        'memory_limit_mb': 2048,
        'chunk_size_kb': 1024,
    },
    'cache': {
        'max_cache_size_mb': 4096,
        'max_age_days': 90,
    }
})
```

## Monitoring and Tuning

### Performance Metrics

```python
# Get processing metrics
metrics = parser.get_processing_metrics()
print(f"Processing rate: {metrics['files_per_second']:.1f} files/sec")
print(f"Memory utilization: {metrics['memory_utilization']:.1f}%")
print(f"Cache hit rate: {metrics['cache_stats']['hit_rate_percent']:.1f}%")
```

### Tuning Guidelines

#### Low Cache Hit Rate
```python
# Increase cache size and retention
config.tool_options['cache'].update({
    'max_cache_size_mb': config.tool_options['cache']['max_cache_size_mb'] * 2,
    'max_age_days': 60,
})
```

#### High Memory Usage
```python
# Reduce memory limits and chunk sizes  
config.tool_options['memory'].update({
    'memory_limit_mb': 512,
    'chunk_size_kb': 128,
    'use_efficient_parsing_mb': 256 * 1024,  # 256KB
})
```

#### Slow Processing Speed
```python
# Increase parallelism
config.tool_options['parallel'].update({
    'max_workers': psutil.cpu_count() * 2,
    'strategy': 'adaptive',
})
```

## Troubleshooting

### Common Issues

#### Out of Memory Errors
```python
# Solution: Enable memory-efficient parsing
config.tool_options['memory'].update({
    'use_efficient_parsing_mb': 128 * 1024,  # 128KB threshold
    'memory_limit_mb': 256,
    'chunk_size_kb': 64,
})
```

#### Cache Corruption
```python
# Solution: Clear and rebuild cache
parser.clear_cache()
# Cache will rebuild automatically on next parse
```

#### Slow Performance
```python
# Solution: Check system resources and adjust
import psutil

print(f"CPU usage: {psutil.cpu_percent()}%")
print(f"Memory usage: {psutil.virtual_memory().percent}%")
print(f"Disk usage: {psutil.disk_usage('/').percent}%")

# Adjust configuration based on resource availability
```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging
config.tool_options['debug'] = {
    'verbose_logging': True,
    'performance_tracking': True,
    'memory_profiling': True,
}
```

## Best Practices

### Development Environment
- Use **"standard"** preset
- Enable caching for faster iterative development
- Monitor memory usage during large codebase analysis

### CI/CD Environment  
- Use **"minimal"** preset
- Disable caching to ensure clean runs
- Set conservative memory limits

### Production Analysis
- Use **"performance"** or **"comprehensive"** preset
- Enable aggressive caching
- Monitor and tune based on actual workloads

### Large Codebases (>10k files)
- Use **"performance"** preset
- Enable memory-efficient parsing for all files
- Use process-based strategy for true parallelism
- Monitor cache hit rates and adjust retention policies

This configuration guide provides the foundation for optimizing the Python Debug Tool's performance across different environments and use cases.
