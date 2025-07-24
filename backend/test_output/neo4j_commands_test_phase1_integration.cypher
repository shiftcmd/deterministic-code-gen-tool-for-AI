// Neo4j Cypher Commands - Transformation Output
// Generated at: 2025-07-24T16:43:34.831028
// Job ID: unknown
// Total queries: 55

// IMPORTANT: These are parameterized queries.
// Use with Neo4j driver's session.run(query, parameters) method.
// For manual execution, see the batch script section below.

// Metadata:
// {
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "module_name": "test_sample_module",
  "generated_at": "2025-07-24T16:43:34.830559",
  "line_count": 172
}

// === PARAMETERIZED QUERIES ===

// Query 1
// --------------------------------------------------
MERGE (n:Module {path: $path})
SET n.path = $path, n.name = $name, n.line_count = $line_count, n.size_bytes = $size_bytes, n.last_modified = $last_modified, n.docstring = $docstring
// Parameters:
{
  "unique_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "name": "test_sample_module",
  "line_count": 172,
  "size_bytes": 5002,
  "last_modified": null,
  "docstring": "Test sample module for Phase 1 extraction testing.\n\nThis module contains various Python constructs to test the extraction\nand transformation pipeline comprehensively."
}

// Query 2
// --------------------------------------------------
MERGE (n:Class {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators
// Parameters:
{
  "unique_key": "class:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:BaseProcessor",
  "name": "BaseProcessor",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "docstring": "Base class for all data processors.",
  "line_start": 23,
  "line_end": 33,
  "decorators": []
}

// Query 3
// --------------------------------------------------
MERGE (n:Class {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators
// Parameters:
{
  "unique_key": "class:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:DataProcessor",
  "name": "DataProcessor",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "docstring": "Concrete data processor implementation.",
  "line_start": 36,
  "line_end": 86,
  "decorators": []
}

// Query 4
// --------------------------------------------------
MERGE (n:Class {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators
// Parameters:
{
  "unique_key": "class:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:UtilityMixin",
  "name": "UtilityMixin",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "docstring": "Mixin class with utility methods.",
  "line_start": 89,
  "line_end": 95,
  "decorators": []
}

// Query 5
// --------------------------------------------------
MERGE (n:Class {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators
// Parameters:
{
  "unique_key": "class:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:ProcessingError",
  "name": "ProcessingError",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "docstring": "Custom exception for processing errors.",
  "line_start": 147,
  "line_end": 154,
  "decorators": []
}

// Query 6
// --------------------------------------------------
MERGE (n:Function {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.signature = $signature, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators, n.return_type = $return_type
// Parameters:
{
  "unique_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:load_config",
  "name": "load_config",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "signature": "load_config(config_path)",
  "docstring": "Load configuration from file.",
  "line_start": 98,
  "line_end": 106,
  "decorators": [],
  "return_type": "Dict[str, Any]"
}

// Query 7
// --------------------------------------------------
MERGE (n:Function {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.signature = $signature, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators, n.return_type = $return_type
// Parameters:
{
  "unique_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:async_fetch_data",
  "name": "async_fetch_data",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "signature": "async async_fetch_data(url)",
  "docstring": "Async function to fetch data from URL.",
  "line_start": 109,
  "line_end": 114,
  "decorators": [],
  "return_type": "Optional[Dict]"
}

// Query 8
// --------------------------------------------------
MERGE (n:Function {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.signature = $signature, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators, n.return_type = $return_type
// Parameters:
{
  "unique_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:decorated_method",
  "name": "decorated_method",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "signature": "decorated_method(self)",
  "docstring": "Property decorator example.",
  "line_start": 118,
  "line_end": 120,
  "decorators": [
    "property"
  ],
  "return_type": "str"
}

// Query 9
// --------------------------------------------------
MERGE (n:Function {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.signature = $signature, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators, n.return_type = $return_type
// Parameters:
{
  "unique_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:factory_function",
  "name": "factory_function",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "signature": "factory_function(processor_type)",
  "docstring": "Factory function to create processors.",
  "line_start": 123,
  "line_end": 128,
  "decorators": [],
  "return_type": "BaseProcessor"
}

// Query 10
// --------------------------------------------------
MERGE (n:Function {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.signature = $signature, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators, n.return_type = $return_type
// Parameters:
{
  "unique_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:complex_function",
  "name": "complex_function",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "signature": "complex_function(required_param, optional_param)",
  "docstring": "Function with complex parameter signature.",
  "line_start": 132,
  "line_end": 143,
  "decorators": [],
  "return_type": "Union[str, int]"
}

// Query 11
// --------------------------------------------------
MERGE (n:Function {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.signature = $signature, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators, n.return_type = $return_type
// Parameters:
{
  "unique_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:__init__",
  "name": "__init__",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "signature": "__init__(self, name)",
  "docstring": "Initialize processor with name.",
  "line_start": 26,
  "line_end": 29,
  "decorators": [],
  "return_type": null
}

// Query 12
// --------------------------------------------------
MERGE (n:Function {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.signature = $signature, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators, n.return_type = $return_type
// Parameters:
{
  "unique_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:process",
  "name": "process",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "signature": "process(self, data)",
  "docstring": "Process data - to be implemented by subclasses.",
  "line_start": 31,
  "line_end": 33,
  "decorators": [],
  "return_type": "Any"
}

// Query 13
// --------------------------------------------------
MERGE (n:Function {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.signature = $signature, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators, n.return_type = $return_type
// Parameters:
{
  "unique_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:__init__",
  "name": "__init__",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "signature": "__init__(self, name, config)",
  "docstring": "Initialize data processor.",
  "line_start": 39,
  "line_end": 43,
  "decorators": [],
  "return_type": null
}

// Query 14
// --------------------------------------------------
MERGE (n:Function {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.signature = $signature, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators, n.return_type = $return_type
// Parameters:
{
  "unique_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:cache_size",
  "name": "cache_size",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "signature": "cache_size(self)",
  "docstring": "Get current cache size.",
  "line_start": 46,
  "line_end": 48,
  "decorators": [
    "property"
  ],
  "return_type": "int"
}

// Query 15
// --------------------------------------------------
MERGE (n:Function {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.signature = $signature, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators, n.return_type = $return_type
// Parameters:
{
  "unique_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:validate_data",
  "name": "validate_data",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "signature": "validate_data(data)",
  "docstring": "Static method to validate input data.",
  "line_start": 51,
  "line_end": 53,
  "decorators": [
    "staticmethod"
  ],
  "return_type": "bool"
}

// Query 16
// --------------------------------------------------
MERGE (n:Function {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.signature = $signature, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators, n.return_type = $return_type
// Parameters:
{
  "unique_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:create_default",
  "name": "create_default",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "signature": "create_default(cls)",
  "docstring": "Class method to create default processor.",
  "line_start": 56,
  "line_end": 58,
  "decorators": [
    "classmethod"
  ],
  "return_type": "'DataProcessor'"
}

// Query 17
// --------------------------------------------------
MERGE (n:Function {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.signature = $signature, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators, n.return_type = $return_type
// Parameters:
{
  "unique_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:process",
  "name": "process",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "signature": "process(self, data)",
  "docstring": "Process input data and return results.",
  "line_start": 60,
  "line_end": 82,
  "decorators": [],
  "return_type": "Dict[str, Any]"
}

// Query 18
// --------------------------------------------------
MERGE (n:Function {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.signature = $signature, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators, n.return_type = $return_type
// Parameters:
{
  "unique_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:clear_cache",
  "name": "clear_cache",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "signature": "clear_cache(self)",
  "docstring": "Clear the internal cache.",
  "line_start": 84,
  "line_end": 86,
  "decorators": [],
  "return_type": null
}

// Query 19
// --------------------------------------------------
MERGE (n:Function {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.signature = $signature, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators, n.return_type = $return_type
// Parameters:
{
  "unique_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:log_message",
  "name": "log_message",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "signature": "log_message(self, message)",
  "docstring": "Log a message.",
  "line_start": 92,
  "line_end": 95,
  "decorators": [],
  "return_type": "None"
}

// Query 20
// --------------------------------------------------
MERGE (n:Function {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.signature = $signature, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators, n.return_type = $return_type
// Parameters:
{
  "unique_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:__init__",
  "name": "__init__",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "signature": "__init__(self, message, error_code)",
  "docstring": "Initialize processing error.",
  "line_start": 150,
  "line_end": 154,
  "decorators": [],
  "return_type": null
}

// Query 21
// --------------------------------------------------
MERGE (n:Function {name: $name, module_path: $module_path})
SET n.name = $name, n.module_path = $module_path, n.signature = $signature, n.docstring = $docstring, n.line_start = $line_start, n.line_end = $line_end, n.decorators = $decorators, n.return_type = $return_type
// Parameters:
{
  "unique_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:transform_item",
  "name": "transform_item",
  "module_path": "/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "signature": "transform_item(key, value)",
  "docstring": "Transform individual data item.",
  "line_start": 66,
  "line_end": 73,
  "decorators": [],
  "return_type": "Any"
}

// Query 22
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Module {unique_key: $target_key})
MERGE (source)-[r:IMPORTS {import_name: $import_name, asname: $asname, fromname: $fromname, is_star: $is_star, line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "module:os",
  "import_name": "os",
  "asname": null,
  "fromname": null,
  "is_star": false,
  "line_start": 8,
  "line_end": 8
}

// Query 23
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Module {unique_key: $target_key})
MERGE (source)-[r:IMPORTS {import_name: $import_name, asname: $asname, fromname: $fromname, is_star: $is_star, line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "module:sys",
  "import_name": "sys",
  "asname": null,
  "fromname": null,
  "is_star": false,
  "line_start": 9,
  "line_end": 9
}

// Query 24
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Module {unique_key: $target_key})
MERGE (source)-[r:IMPORTS {import_name: $import_name, asname: $asname, fromname: $fromname, is_star: $is_star, line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "module:json",
  "import_name": "json",
  "asname": null,
  "fromname": null,
  "is_star": false,
  "line_start": 10,
  "line_end": 10
}

// Query 25
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Module {unique_key: $target_key})
MERGE (source)-[r:IMPORTS {import_name: $import_name, asname: $asname, fromname: $fromname, is_star: $is_star, line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "module:typing",
  "import_name": "Dict",
  "asname": null,
  "fromname": "typing",
  "is_star": false,
  "line_start": 11,
  "line_end": 11
}

// Query 26
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Module {unique_key: $target_key})
MERGE (source)-[r:IMPORTS {import_name: $import_name, asname: $asname, fromname: $fromname, is_star: $is_star, line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "module:typing",
  "import_name": "List",
  "asname": null,
  "fromname": "typing",
  "is_star": false,
  "line_start": 11,
  "line_end": 11
}

// Query 27
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Module {unique_key: $target_key})
MERGE (source)-[r:IMPORTS {import_name: $import_name, asname: $asname, fromname: $fromname, is_star: $is_star, line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "module:typing",
  "import_name": "Optional",
  "asname": null,
  "fromname": "typing",
  "is_star": false,
  "line_start": 11,
  "line_end": 11
}

// Query 28
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Module {unique_key: $target_key})
MERGE (source)-[r:IMPORTS {import_name: $import_name, asname: $asname, fromname: $fromname, is_star: $is_star, line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "module:typing",
  "import_name": "Any",
  "asname": null,
  "fromname": "typing",
  "is_star": false,
  "line_start": 11,
  "line_end": 11
}

// Query 29
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Module {unique_key: $target_key})
MERGE (source)-[r:IMPORTS {import_name: $import_name, asname: $asname, fromname: $fromname, is_star: $is_star, line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "module:typing",
  "import_name": "Union",
  "asname": null,
  "fromname": "typing",
  "is_star": false,
  "line_start": 11,
  "line_end": 11
}

// Query 30
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Module {unique_key: $target_key})
MERGE (source)-[r:IMPORTS {import_name: $import_name, asname: $asname, fromname: $fromname, is_star: $is_star, line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "module:pathlib",
  "import_name": "Path",
  "asname": null,
  "fromname": "pathlib",
  "is_star": false,
  "line_start": 12,
  "line_end": 12
}

// Query 31
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Module {unique_key: $target_key})
MERGE (source)-[r:IMPORTS {import_name: $import_name, asname: $asname, fromname: $fromname, is_star: $is_star, line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "module:datetime",
  "import_name": "datetime",
  "asname": null,
  "fromname": "datetime",
  "is_star": false,
  "line_start": 13,
  "line_end": 13
}

// Query 32
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Module {unique_key: $target_key})
MERGE (source)-[r:IMPORTS {import_name: $import_name, asname: $asname, fromname: $fromname, is_star: $is_star, line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "module:collections",
  "import_name": "defaultdict",
  "asname": null,
  "fromname": "collections",
  "is_star": false,
  "line_start": 14,
  "line_end": 14
}

// Query 33
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Module {unique_key: $target_key})
MERGE (source)-[r:IMPORTS {import_name: $import_name, asname: $asname, fromname: $fromname, is_star: $is_star, line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "module:asyncio",
  "import_name": "asyncio",
  "asname": null,
  "fromname": null,
  "is_star": false,
  "line_start": 112,
  "line_end": 112
}

// Query 34
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Class {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "class:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:BaseProcessor",
  "line_start": 23,
  "line_end": 33
}

// Query 35
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Class {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "class:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:DataProcessor",
  "line_start": 36,
  "line_end": 86
}

// Query 36
// --------------------------------------------------
MATCH (source:Class {unique_key: $source_key})
MATCH (target:Class {unique_key: $target_key})
MERGE (source)-[r:INHERITS_FROM {inheritance_order: $inheritance_order, line_number: $line_number}]->(target)
// Parameters:
{
  "source_key": "class:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:DataProcessor",
  "target_key": "class:BaseProcessor",
  "inheritance_order": 0,
  "line_number": 0
}

// Query 37
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Class {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "class:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:UtilityMixin",
  "line_start": 89,
  "line_end": 95
}

// Query 38
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Class {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "class:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:ProcessingError",
  "line_start": 147,
  "line_end": 154
}

// Query 39
// --------------------------------------------------
MATCH (source:Class {unique_key: $source_key})
MATCH (target:Class {unique_key: $target_key})
MERGE (source)-[r:INHERITS_FROM {inheritance_order: $inheritance_order, line_number: $line_number}]->(target)
// Parameters:
{
  "source_key": "class:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:ProcessingError",
  "target_key": "class:Exception",
  "inheritance_order": 0,
  "line_number": 0
}

// Query 40
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Function {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:load_config",
  "line_start": 98,
  "line_end": 106
}

// Query 41
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Function {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:async_fetch_data",
  "line_start": 109,
  "line_end": 114
}

// Query 42
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Function {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:decorated_method",
  "line_start": 118,
  "line_end": 120
}

// Query 43
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Function {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:factory_function",
  "line_start": 123,
  "line_end": 128
}

// Query 44
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Function {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:complex_function",
  "line_start": 132,
  "line_end": 143
}

// Query 45
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Function {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:__init__",
  "line_start": 26,
  "line_end": 29
}

// Query 46
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Function {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:process",
  "line_start": 31,
  "line_end": 33
}

// Query 47
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Function {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:__init__",
  "line_start": 39,
  "line_end": 43
}

// Query 48
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Function {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:cache_size",
  "line_start": 46,
  "line_end": 48
}

// Query 49
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Function {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:validate_data",
  "line_start": 51,
  "line_end": 53
}

// Query 50
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Function {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:create_default",
  "line_start": 56,
  "line_end": 58
}

// Query 51
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Function {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:process",
  "line_start": 60,
  "line_end": 82
}

// Query 52
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Function {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:clear_cache",
  "line_start": 84,
  "line_end": 86
}

// Query 53
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Function {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:log_message",
  "line_start": 92,
  "line_end": 95
}

// Query 54
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Function {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:__init__",
  "line_start": 150,
  "line_end": 154
}

// Query 55
// --------------------------------------------------
MATCH (source:Module {unique_key: $source_key})
MATCH (target:Function {unique_key: $target_key})
MERGE (source)-[r:CONTAINS {line_start: $line_start, line_end: $line_end}]->(target)
// Parameters:
{
  "source_key": "module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py",
  "target_key": "function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:transform_item",
  "line_start": 66,
  "line_end": 73
}


// === BATCH EXECUTION SCRIPT ===
// For Neo4j Browser or cypher-shell
// ==================================================

// Batch Query 1
MERGE (n:Module {path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.name = 'test_sample_module', n.line_count = 172, n.size_bytes = 5002, n.last_modified = null, n.docstring = 'Test sample module for Phase 1 extraction testing.

This module contains various Python constructs to test the extraction
and transformation pipeline comprehensively.';

// Batch Query 2
MERGE (n:Class {name: 'BaseProcessor', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'BaseProcessor', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.docstring = 'Base class for all data processors.', n.line_start = 23, n.line_end = 33, n.decorators = '[]';

// Batch Query 3
MERGE (n:Class {name: 'DataProcessor', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'DataProcessor', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.docstring = 'Concrete data processor implementation.', n.line_start = 36, n.line_end = 86, n.decorators = '[]';

// Batch Query 4
MERGE (n:Class {name: 'UtilityMixin', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'UtilityMixin', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.docstring = 'Mixin class with utility methods.', n.line_start = 89, n.line_end = 95, n.decorators = '[]';

// Batch Query 5
MERGE (n:Class {name: 'ProcessingError', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'ProcessingError', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.docstring = 'Custom exception for processing errors.', n.line_start = 147, n.line_end = 154, n.decorators = '[]';

// Batch Query 6
MERGE (n:Function {name: 'load_config', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'load_config', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.signature = 'load_config(config_path)', n.docstring = 'Load configuration from file.', n.line_start = 98, n.line_end = 106, n.decorators = '[]', n.return_type = 'Dict[str, Any]';

// Batch Query 7
MERGE (n:Function {name: 'async_fetch_data', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'async_fetch_data', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.signature = 'async async_fetch_data(url)', n.docstring = 'Async function to fetch data from URL.', n.line_start = 109, n.line_end = 114, n.decorators = '[]', n.return_type = 'Optional[Dict]';

// Batch Query 8
MERGE (n:Function {name: 'decorated_method', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'decorated_method', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.signature = 'decorated_method(self)', n.docstring = 'Property decorator example.', n.line_start = 118, n.line_end = 120, n.decorators = '["property"]', n.return_type = 'str';

// Batch Query 9
MERGE (n:Function {name: 'factory_function', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'factory_function', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.signature = 'factory_function(processor_type)', n.docstring = 'Factory function to create processors.', n.line_start = 123, n.line_end = 128, n.decorators = '[]', n.return_type = 'BaseProcessor';

// Batch Query 10
MERGE (n:Function {name: 'complex_function', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'complex_function', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.signature = 'complex_function(required_param, optional_param)', n.docstring = 'Function with complex parameter signature.', n.line_start = 132, n.line_end = 143, n.decorators = '[]', n.return_type = 'Union[str, int]';

// Batch Query 11
MERGE (n:Function {name: '__init__', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = '__init__', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.signature = '__init__(self, name)', n.docstring = 'Initialize processor with name.', n.line_start = 26, n.line_end = 29, n.decorators = '[]', n.return_type = null;

// Batch Query 12
MERGE (n:Function {name: 'process', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'process', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.signature = 'process(self, data)', n.docstring = 'Process data - to be implemented by subclasses.', n.line_start = 31, n.line_end = 33, n.decorators = '[]', n.return_type = 'Any';

// Batch Query 13
MERGE (n:Function {name: '__init__', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = '__init__', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.signature = '__init__(self, name, config)', n.docstring = 'Initialize data processor.', n.line_start = 39, n.line_end = 43, n.decorators = '[]', n.return_type = null;

// Batch Query 14
MERGE (n:Function {name: 'cache_size', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'cache_size', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.signature = 'cache_size(self)', n.docstring = 'Get current cache size.', n.line_start = 46, n.line_end = 48, n.decorators = '["property"]', n.return_type = 'int';

// Batch Query 15
MERGE (n:Function {name: 'validate_data', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'validate_data', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.signature = 'validate_data(data)', n.docstring = 'Static method to validate input data.', n.line_start = 51, n.line_end = 53, n.decorators = '["staticmethod"]', n.return_type = 'bool';

// Batch Query 16
MERGE (n:Function {name: 'create_default', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'create_default', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.signature = 'create_default(cls)', n.docstring = 'Class method to create default processor.', n.line_start = 56, n.line_end = 58, n.decorators = '["classmethod"]', n.return_type = '\'DataProcessor\'';

// Batch Query 17
MERGE (n:Function {name: 'process', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'process', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.signature = 'process(self, data)', n.docstring = 'Process input data and return results.', n.line_start = 60, n.line_end = 82, n.decorators = '[]', n.return_type = 'Dict[str, Any]';

// Batch Query 18
MERGE (n:Function {name: 'clear_cache', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'clear_cache', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.signature = 'clear_cache(self)', n.docstring = 'Clear the internal cache.', n.line_start = 84, n.line_end = 86, n.decorators = '[]', n.return_type = null;

// Batch Query 19
MERGE (n:Function {name: 'log_message', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'log_message', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.signature = 'log_message(self, message)', n.docstring = 'Log a message.', n.line_start = 92, n.line_end = 95, n.decorators = '[]', n.return_type = 'None';

// Batch Query 20
MERGE (n:Function {name: '__init__', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = '__init__', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.signature = '__init__(self, message, error_code)', n.docstring = 'Initialize processing error.', n.line_start = 150, n.line_end = 154, n.decorators = '[]', n.return_type = null;

// Batch Query 21
MERGE (n:Function {name: 'transform_item', module_path: '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
SET n.name = 'transform_item', n.module_path = '/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py', n.signature = 'transform_item(key, value)', n.docstring = 'Transform individual data item.', n.line_start = 66, n.line_end = 73, n.decorators = '[]', n.return_type = 'Any';

// Batch Query 22
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Module {unique_key: 'module:os'})
MERGE (source)-[r:IMPORTS {import_name: 'os', asname: null, fromname: null, is_star: false, line_start: 8, line_end: 8}]->(target);

// Batch Query 23
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Module {unique_key: 'module:sys'})
MERGE (source)-[r:IMPORTS {import_name: 'sys', asname: null, fromname: null, is_star: false, line_start: 9, line_end: 9}]->(target);

// Batch Query 24
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Module {unique_key: 'module:json'})
MERGE (source)-[r:IMPORTS {import_name: 'json', asname: null, fromname: null, is_star: false, line_start: 10, line_end: 10}]->(target);

// Batch Query 25
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Module {unique_key: 'module:typing'})
MERGE (source)-[r:IMPORTS {import_name: 'Dict', asname: null, fromname: 'typing', is_star: false, line_start: 11, line_end: 11}]->(target);

// Batch Query 26
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Module {unique_key: 'module:typing'})
MERGE (source)-[r:IMPORTS {import_name: 'List', asname: null, fromname: 'typing', is_star: false, line_start: 11, line_end: 11}]->(target);

// Batch Query 27
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Module {unique_key: 'module:typing'})
MERGE (source)-[r:IMPORTS {import_name: 'Optional', asname: null, fromname: 'typing', is_star: false, line_start: 11, line_end: 11}]->(target);

// Batch Query 28
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Module {unique_key: 'module:typing'})
MERGE (source)-[r:IMPORTS {import_name: 'Any', asname: null, fromname: 'typing', is_star: false, line_start: 11, line_end: 11}]->(target);

// Batch Query 29
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Module {unique_key: 'module:typing'})
MERGE (source)-[r:IMPORTS {import_name: 'Union', asname: null, fromname: 'typing', is_star: false, line_start: 11, line_end: 11}]->(target);

// Batch Query 30
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Module {unique_key: 'module:pathlib'})
MERGE (source)-[r:IMPORTS {import_name: 'Path', asname: null, fromname: 'pathlib', is_star: false, line_start: 12, line_end: 12}]->(target);

// Batch Query 31
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Module {unique_key: 'module:datetime'})
MERGE (source)-[r:IMPORTS {import_name: 'datetime', asname: null, fromname: 'datetime', is_star: false, line_start: 13, line_end: 13}]->(target);

// Batch Query 32
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Module {unique_key: 'module:collections'})
MERGE (source)-[r:IMPORTS {import_name: 'defaultdict', asname: null, fromname: 'collections', is_star: false, line_start: 14, line_end: 14}]->(target);

// Batch Query 33
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Module {unique_key: 'module:asyncio'})
MERGE (source)-[r:IMPORTS {import_name: 'asyncio', asname: null, fromname: null, is_star: false, line_start: 112, line_end: 112}]->(target);

// Batch Query 34
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Class {unique_key: 'class:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:BaseProcessor'})
MERGE (source)-[r:CONTAINS {line_start: 23, line_end: 33}]->(target);

// Batch Query 35
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Class {unique_key: 'class:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:DataProcessor'})
MERGE (source)-[r:CONTAINS {line_start: 36, line_end: 86}]->(target);

// Batch Query 36
MATCH (source:Class {unique_key: 'class:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:DataProcessor'})
MATCH (target:Class {unique_key: 'class:BaseProcessor'})
MERGE (source)-[r:INHERITS_FROM {inheritance_order: 0, line_number: 0}]->(target);

// Batch Query 37
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Class {unique_key: 'class:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:UtilityMixin'})
MERGE (source)-[r:CONTAINS {line_start: 89, line_end: 95}]->(target);

// Batch Query 38
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Class {unique_key: 'class:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:ProcessingError'})
MERGE (source)-[r:CONTAINS {line_start: 147, line_end: 154}]->(target);

// Batch Query 39
MATCH (source:Class {unique_key: 'class:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:ProcessingError'})
MATCH (target:Class {unique_key: 'class:Exception'})
MERGE (source)-[r:INHERITS_FROM {inheritance_order: 0, line_number: 0}]->(target);

// Batch Query 40
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Function {unique_key: 'function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:load_config'})
MERGE (source)-[r:CONTAINS {line_start: 98, line_end: 106}]->(target);

// Batch Query 41
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Function {unique_key: 'function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:async_fetch_data'})
MERGE (source)-[r:CONTAINS {line_start: 109, line_end: 114}]->(target);

// Batch Query 42
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Function {unique_key: 'function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:decorated_method'})
MERGE (source)-[r:CONTAINS {line_start: 118, line_end: 120}]->(target);

// Batch Query 43
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Function {unique_key: 'function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:factory_function'})
MERGE (source)-[r:CONTAINS {line_start: 123, line_end: 128}]->(target);

// Batch Query 44
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Function {unique_key: 'function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:complex_function'})
MERGE (source)-[r:CONTAINS {line_start: 132, line_end: 143}]->(target);

// Batch Query 45
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Function {unique_key: 'function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:__init__'})
MERGE (source)-[r:CONTAINS {line_start: 26, line_end: 29}]->(target);

// Batch Query 46
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Function {unique_key: 'function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:process'})
MERGE (source)-[r:CONTAINS {line_start: 31, line_end: 33}]->(target);

// Batch Query 47
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Function {unique_key: 'function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:__init__'})
MERGE (source)-[r:CONTAINS {line_start: 39, line_end: 43}]->(target);

// Batch Query 48
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Function {unique_key: 'function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:cache_size'})
MERGE (source)-[r:CONTAINS {line_start: 46, line_end: 48}]->(target);

// Batch Query 49
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Function {unique_key: 'function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:validate_data'})
MERGE (source)-[r:CONTAINS {line_start: 51, line_end: 53}]->(target);

// Batch Query 50
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Function {unique_key: 'function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:create_default'})
MERGE (source)-[r:CONTAINS {line_start: 56, line_end: 58}]->(target);

// Batch Query 51
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Function {unique_key: 'function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:process'})
MERGE (source)-[r:CONTAINS {line_start: 60, line_end: 82}]->(target);

// Batch Query 52
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Function {unique_key: 'function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:clear_cache'})
MERGE (source)-[r:CONTAINS {line_start: 84, line_end: 86}]->(target);

// Batch Query 53
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Function {unique_key: 'function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:log_message'})
MERGE (source)-[r:CONTAINS {line_start: 92, line_end: 95}]->(target);

// Batch Query 54
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Function {unique_key: 'function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:__init__'})
MERGE (source)-[r:CONTAINS {line_start: 150, line_end: 154}]->(target);

// Batch Query 55
MATCH (source:Module {unique_key: 'module:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py'})
MATCH (target:Function {unique_key: 'function:/home/amo/coding_projects/python_debug_tool/backend/test_sample_module.py:transform_item'})
MERGE (source)-[r:CONTAINS {line_start: 66, line_end: 73}]->(target);


// === EXECUTION STATISTICS ===
// Total nodes: 21
// Total relationships: 34
// Total queries: 55
