"""
Parser integration module for Python Debug Tool.

This module integrates the plugin system with the codebase parser and module parser,
providing a unified interface for configurable, hybrid parsing.

# AI-Intent: Application
# Intent: Integrates plugin system with existing parser components
# Confidence: High
"""

import importlib
import logging
import pkgutil
from typing import Any, Dict, List, Optional, Set, Tuple

from .config import ParserConfig, ParserType
from .exporters import ParserExporter, get_exporter, list_exporters
from .models import ParsedModule
from .plugins import ParserPlugin, get_plugin, list_plugins

logger = logging.getLogger(__name__)


class HybridParserIntegration:
    """
    Integrates the plugin system with the codebase parser and module parser.

    This class acts as a bridge between the existing parser architecture
    and the new plugin-based approach, allowing for a gradual transition
    and ensuring backward compatibility.
    """

    def __init__(self, config: ParserConfig = None):
        """
        Initialize the parser integration.

        Args:
            config: Parser configuration
        """
        self.config = config or ParserConfig()
        self._discover_plugins()

    def _discover_plugins(self) -> None:
        """
        Discover and initialize available parser plugins.

        This method imports all modules in the plugins package to ensure
        they register themselves with the plugin system.
        """
        import importlib
        import pkgutil

        from . import plugins

        for _, name, _ in pkgutil.iter_modules(
            plugins.__path__, plugins.__name__ + "."
        ):
            try:
                importlib.import_module(name)
                logger.debug(f"Imported plugin module: {name}")
            except ImportError as e:
                logger.warning(f"Could not import plugin module {name}: {e}")

    def get_plugin_for_type(self, parser_type: ParserType) -> Optional[ParserPlugin]:
        """
        Get a parser plugin for the given parser type.

        Args:
            parser_type: Type of parser to get

        Returns:
            A parser plugin instance, or None if no suitable plugin is found
        """
        # Map parser types to plugin names
        plugin_map = {
            ParserType.BUILT_IN_AST: "ast",
            ParserType.ASTROID: "astroid",
            ParserType.INSPECT4PY: "inspect4py",
        }

        # Get the plugin name for this parser type
        plugin_name = plugin_map.get(parser_type)
        if not plugin_name:
            logger.warning(f"No plugin mapping for parser type: {parser_type}")
            return None

        # Try to get the plugin
        try:
            plugin_options = self.config.tool_options.get(plugin_name, {})
            return get_plugin(plugin_name, plugin_options)
        except ValueError:
            logger.warning(f"Parser plugin not found: {plugin_name}")
            return None

    def get_active_plugins(self) -> List[ParserPlugin]:
        """
        Get all active parser plugins based on the current configuration.

        Returns:
            List of active parser plugins
        """
        active_plugins = []

        # Add module parser plugin
        module_plugin = self.get_plugin_for_type(self.config.module_parser)
        if module_plugin and module_plugin not in active_plugins:
            active_plugins.append(module_plugin)

        # Add class parser plugin
        class_plugin = self.get_plugin_for_type(self.config.class_parser)
        if class_plugin and class_plugin not in active_plugins:
            active_plugins.append(class_plugin)

        # Add function parser plugin
        function_plugin = self.get_plugin_for_type(self.config.function_parser)
        if function_plugin and function_plugin not in active_plugins:
            active_plugins.append(function_plugin)

        # Add variable parser plugin
        variable_plugin = self.get_plugin_for_type(self.config.variable_parser)
        if variable_plugin and variable_plugin not in active_plugins:
            active_plugins.append(variable_plugin)

        return active_plugins

    def parse_file(self, file_path: str) -> ParsedModule:
        """
        Parse a Python file using the configured plugins.

        This method delegates to the appropriate parser plugin based on
        the configuration. It supports hybrid parsing, where different
        parts of the code are parsed by different plugins.

        Args:
            file_path: Path to the Python file to parse

        Returns:
            Parsed module information
        """
        logger.info(f"Parsing file: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            # Return a minimal module structure
            return ParsedModule(
                name=file_path.split("/")[-1].replace(".py", ""),
                path=file_path,
                classes=[],
                functions=[],
                variables=[],
                imports=[],
                error=str(e),
            )

        # Create an empty parsed module
        parsed_module = ParsedModule(
            name=file_path.split("/")[-1].replace(".py", ""),
            path=file_path,
            classes=[],
            functions=[],
            variables=[],
            imports=[],
        )

        # Get the module parser plugin
        module_plugin = self.get_plugin_for_type(self.config.module_parser)
        if not module_plugin:
            logger.error(
                f"No module parser plugin found for {self.config.module_parser}"
            )
            parsed_module.error = (
                f"No module parser plugin found for {self.config.module_parser}"
            )
            return parsed_module

        # Parse the module
        try:
            module_result = module_plugin.parse_module(file_path, content)

            # Update the parsed module with the results
            self._update_parsed_module(parsed_module, module_result)

            # Set the parser used
            parsed_module.parsed_with = module_plugin.name

        except Exception as e:
            logger.error(
                f"Error parsing module {file_path} with {module_plugin.name}: {e}"
            )
            parsed_module.error = f"Error parsing with {module_plugin.name}: {str(e)}"

        return parsed_module

    def _update_parsed_module(
        self, parsed_module: ParsedModule, module_result: Dict[str, Any]
    ) -> None:
        """
        Update a ParsedModule object with results from a parser plugin.

        Args:
            parsed_module: ParsedModule object to update
            module_result: Parser plugin results
        """
        # Update basic module information
        if "docstring" in module_result:
            parsed_module.docstring = module_result["docstring"]
        if "line_count" in module_result:
            parsed_module.line_count = module_result["line_count"]

        # Convert classes
        for class_data in module_result.get("classes", []):
            parsed_class = self._convert_class(class_data)
            if parsed_class:
                parsed_module.classes.append(parsed_class)

        # Convert standalone functions
        for function_data in module_result.get("functions", []):
            if not function_data.get("is_method", False):
                parsed_function = self._convert_function(function_data)
                if parsed_function:
                    parsed_module.functions.append(parsed_function)

        # Convert variables
        for variable_data in module_result.get("variables", []):
            parsed_variables = self._convert_variable(variable_data)
            if parsed_variables:
                parsed_module.variables.extend(parsed_variables)

        # Convert imports
        for import_data in module_result.get("imports", []):
            parsed_import = self._convert_import(import_data)
            if parsed_import:
                parsed_module.imports.append(parsed_import)

    def _convert_class(self, class_data: Dict[str, Any]) -> Optional[ParsedClass]:
        """
        Convert class data from parser plugin format to ParsedClass.

        Args:
            class_data: Class data from parser plugin

        Returns:
            ParsedClass object or None if conversion failed
        """
        from .models import ParsedClass, ParsedFunction, ParsedVariable

        try:
            # Create basic class object
            parsed_class = ParsedClass(
                name=class_data.get("name", ""),
                docstring=class_data.get("docstring", ""),
                line_start=class_data.get("line_start", 0),
                line_end=class_data.get("line_end", 0),
                methods=[],
                class_variables=[],
            )

            # Add methods
            for method_data in class_data.get("methods", []):
                parsed_method = self._convert_function(method_data, is_method=True)
                if parsed_method:
                    parsed_class.methods.append(parsed_method)

            # Add class variables
            for var_data in class_data.get("class_variables", []):
                parsed_vars = self._convert_variable(var_data, scope="class")
                if parsed_vars:
                    parsed_class.class_variables.extend(parsed_vars)

            # Add bases if available
            if "bases" in class_data:
                parsed_class.bases = class_data["bases"]

            # Add complexity if available
            if "complexity" in class_data:
                parsed_class.complexity = class_data["complexity"]

            return parsed_class
        except Exception as e:
            logger.error(f"Error converting class data: {e}")
            return None

    def _convert_function(
        self, function_data: Dict[str, Any], is_method: bool = False
    ) -> Optional[ParsedFunction]:
        """
        Convert function data from parser plugin format to ParsedFunction.

        Args:
            function_data: Function data from parser plugin
            is_method: Whether this function is a method

        Returns:
            ParsedFunction object or None if conversion failed
        """
        from .models import ParsedFunction, ParsedVariable

        try:
            # Create function object
            parsed_function = ParsedFunction(
                name=function_data.get("name", ""),
                docstring=function_data.get("docstring", ""),
                line_start=function_data.get("line_start", 0),
                line_end=function_data.get("line_end", 0),
                is_method=is_method or function_data.get("is_method", False),
                parameters=function_data.get("parameters", []),
                local_variables=[],
            )

            # Add special method flags
            parsed_function.is_static = function_data.get("is_static", False)
            parsed_function.is_class = function_data.get("is_class_method", False)
            parsed_function.is_property = function_data.get("is_property", False)

            # Add return annotation if available
            if "return_annotation" in function_data:
                parsed_function.return_annotation = function_data["return_annotation"]

            # Add complexity if available
            if "complexity" in function_data:
                parsed_function.complexity = function_data["complexity"]

            # Add local variables
            for var_data in function_data.get("local_variables", []):
                parsed_vars = self._convert_variable(var_data, scope="local")
                if parsed_vars:
                    parsed_function.local_variables.extend(parsed_vars)

            return parsed_function
        except Exception as e:
            logger.error(f"Error converting function data: {e}")
            return None

    def _convert_variable(
        self, variable_data: Dict[str, Any], scope: str = "module"
    ) -> List[ParsedVariable]:
        """
        Convert variable data from parser plugin format to ParsedVariable.

        Args:
            variable_data: Variable data from parser plugin
            scope: Variable scope (module, class, local)

        Returns:
            List of ParsedVariable objects
        """
        from .models import ParsedVariable

        try:
            result = []

            # Single variable assignment
            if not isinstance(variable_data.get("name", ""), list):
                parsed_var = ParsedVariable(
                    name=variable_data.get("name", ""),
                    line_start=variable_data.get("line_start", 0),
                    line_end=variable_data.get(
                        "line_end", variable_data.get("line_start", 0)
                    ),
                    inferred_type=variable_data.get("inferred_type", "unknown"),
                    is_constant=variable_data.get("is_constant", False),
                )
                result.append(parsed_var)
            else:
                # Multiple variable assignment (a, b = 1, 2)
                for name in variable_data.get("name", []):
                    parsed_var = ParsedVariable(
                        name=name,
                        line_start=variable_data.get("line_start", 0),
                        line_end=variable_data.get(
                            "line_end", variable_data.get("line_start", 0)
                        ),
                        inferred_type=variable_data.get("inferred_type", "unknown"),
                        is_constant=variable_data.get("is_constant", False),
                    )
                    result.append(parsed_var)

            return result
        except Exception as e:
            logger.error(f"Error converting variable data: {e}")
            return []

    def _convert_import(self, import_data: Dict[str, Any]) -> Optional[ParsedImport]:
        """
        Convert import data from parser plugin format to ParsedImport.

        Args:
            import_data: Import data from parser plugin

        Returns:
            ParsedImport object or None if conversion failed
        """
        from .models import ParsedImport

        try:
            import_type = import_data.get("type", "import")

            parsed_import = ParsedImport(
                name=import_data.get("name", ""),
                line_start=import_data.get("line_start", 0),
                line_end=import_data.get("line_end", import_data.get("line_start", 0)),
                is_from=import_type == "importfrom" or "fromname" in import_data,
            )

            # Add from import information
            if parsed_import.is_from:
                parsed_import.from_module = import_data.get("fromname", "")

            # Add as import information
            if "asname" in import_data and import_data["asname"]:
                parsed_import.as_name = import_data["asname"]

            # Add star import flag
            parsed_import.is_star = import_data.get("is_star", False)

            return parsed_import
        except Exception as e:
            logger.error(f"Error converting import data: {e}")
            return None

    def export_to_neo4j(
        self,
        parsed_modules: Dict[str, ParsedModule],
        neo4j_options: Dict[str, Any] = None,
    ) -> bool:
        """
        Export parsed modules to Neo4j database.

        Args:
            parsed_modules: Dictionary mapping file paths to parsed modules
            neo4j_options: Neo4j exporter options

        Returns:
            True if export succeeded, False otherwise
        """
        try:
            # Prepare the data for export
            export_data = {
                "name": "parsed_codebase",
                "path": list(parsed_modules.keys())[0].split("/")[0]
                if parsed_modules
                else "unknown",
                "modules": list(parsed_modules.values()),
                "parsed_with": "hybrid",
            }

            # Get the Neo4j exporter
            exporter = get_exporter("neo4j", neo4j_options)

            # Export the data
            return exporter.export(export_data)

        except Exception as e:
            logger.error(f"Error exporting to Neo4j: {e}")
            return False


def integrate_parser_plugins(codebase_parser) -> None:
    """
    Integrate parser plugins with an existing CodebaseParser instance.

    This function enhances a CodebaseParser with plugin capabilities
    by monkey-patching its parse_file method.

    Args:
        codebase_parser: An instance of CodebaseParser to enhance
    """
    integration = HybridParserIntegration(codebase_parser.config)

    # Store the original method
    original_parse_file = codebase_parser.parse_file

    # Create a new parse_file method that uses plugins
    def enhanced_parse_file(file_path):
        # Try using the plugin integration first
        try:
            return integration.parse_file(file_path)
        except Exception as e:
            logger.warning(f"Plugin-based parsing failed for {file_path}: {e}")
            logger.warning("Falling back to original parser")
            # Fall back to the original method
            return original_parse_file(file_path)

    # Replace the method
    codebase_parser.parse_file = enhanced_parse_file

    # Add the integration instance to the codebase parser
    codebase_parser.plugin_integration = integration

    # Add the export to Neo4j method
    codebase_parser.export_to_neo4j = (
        lambda neo4j_options=None: integration.export_to_neo4j(
            codebase_parser.parsed_modules, neo4j_options
        )
    )
