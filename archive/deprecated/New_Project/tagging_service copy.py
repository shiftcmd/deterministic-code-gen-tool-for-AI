"""
Main tagging service for orchestrating the analysis and tagging process.

This service coordinates between static analysis, AI-assisted tagging, and validation
to provide comprehensive code component tagging within a hexagonal architecture framework.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from ...config.logging import get_logger, log_analysis_event, log_performance
from ...config.settings import get_settings
from ...core.domain.code_component import CodeComponent, Relationship
from ...core.domain.tag import Tag, TagCollection, get_tag_registry
from ...infrastructure.adapters.ast_analyzer import StaticCodeAnalyzer


class TaggingService:
    """
    Application service for orchestrating the code tagging process.

    This service coordinates static analysis, AI-assisted tagging, validation,
    and result aggregation to provide comprehensive architectural analysis.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.tag_registry = get_tag_registry()
        self.static_analyzer = StaticCodeAnalyzer()

        # Analysis state
        self.analysis_results: Dict[
            str, Tuple[List[CodeComponent], List[Relationship]]
        ] = {}
        self.validation_results: Dict[str, Dict[str, Any]] = {}

    def analyze_codebase(
        self, codebase_path: str, recursive: bool = True
    ) -> Tuple[List[CodeComponent], List[Relationship]]:
        """
        Analyze an entire codebase and return tagged components and relationships.

        Args:
            codebase_path: Path to the codebase root directory
            recursive: Whether to analyze subdirectories recursively

        Returns:
            Tuple of (all_components, all_relationships) with tags applied
        """
        start_time = time.time()

        try:
            self.logger.info(f"Starting codebase analysis: {codebase_path}")
            log_analysis_event(
                "codebase_analysis_started",
                codebase_path=codebase_path,
                recursive=recursive,
            )

            # Step 1: Static analysis
            components, relationships = self._perform_static_analysis(
                codebase_path, recursive
            )

            # Step 2: AI-assisted tagging (if enabled)
            if self.settings.should_use_ai_tagging():
                components = self._enhance_with_ai_tagging(components)

            # Step 3: Validation and confidence scoring
            if self.settings.analysis.enable_validation:
                self._validate_analysis_results(components, relationships)

            # Step 4: Create codebase-level component
            codebase_component = self._create_codebase_component(
                codebase_path, components, relationships
            )
            components.insert(0, codebase_component)

            # Step 5: Add codebase containment relationships
            self._add_codebase_relationships(codebase_component, components[1:])

            duration = time.time() - start_time
            log_performance(
                "codebase_analysis",
                duration,
                component_count=len(components),
                relationship_count=len(relationships),
            )

            log_analysis_event(
                "codebase_analysis_completed",
                codebase_path=codebase_path,
                component_count=len(components),
                relationship_count=len(relationships),
                duration_seconds=round(duration, 2),
            )

            self.logger.info(
                f"Codebase analysis completed: {len(components)} components, {len(relationships)} relationships"
            )

            return components, relationships

        except Exception as e:
            self.logger.error(f"Error during codebase analysis: {e}")
            log_analysis_event(
                "codebase_analysis_failed", codebase_path=codebase_path, error=str(e)
            )
            raise

    def analyze_file(
        self, file_path: str
    ) -> Tuple[List[CodeComponent], List[Relationship]]:
        """
        Analyze a single file and return tagged components and relationships.

        Args:
            file_path: Path to the source code file

        Returns:
            Tuple of (components, relationships) with tags applied
        """
        start_time = time.time()

        try:
            self.logger.info(f"Analyzing file: {file_path}")

            # Check if file should be included
            if not self.settings.is_file_included(file_path):
                self.logger.debug(f"File excluded by configuration: {file_path}")
                return [], []

            # Perform static analysis
            components, relationships = self.static_analyzer.analyze_file(file_path)

            # AI-assisted tagging (if enabled)
            if self.settings.should_use_ai_tagging() and components:
                components = self._enhance_with_ai_tagging(components)

            duration = time.time() - start_time
            log_performance(
                "file_analysis",
                duration,
                file_path=file_path,
                component_count=len(components),
                relationship_count=len(relationships),
            )

            return components, relationships

        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {e}")
            return [], []

    def get_analysis_summary(self, components: List[CodeComponent]) -> Dict[str, Any]:
        """
        Generate a summary of the analysis results.

        Args:
            components: List of analyzed components

        Returns:
            Dictionary containing analysis summary statistics
        """
        if not components:
            return {}

        # Component type distribution
        type_distribution = {}
        for component in components:
            comp_type = (
                component.component_type
                if isinstance(component.component_type, str)
                else component.component_type.value
            )
            type_distribution[comp_type] = type_distribution.get(comp_type, 0) + 1

        # Tag category distribution
        tag_categories = {}
        for component in components:
            for tag in component.tags.tags:
                category = (
                    tag.category
                    if isinstance(tag.category, str)
                    else tag.category.value
                )
                tag_categories[category] = tag_categories.get(category, 0) + 1

        # Architectural layer distribution
        layer_distribution = {}
        for component in components:
            layer = component.architectural_layer
            if layer:
                layer_distribution[layer] = layer_distribution.get(layer, 0) + 1

        # Quality metrics
        total_complexity = sum(comp.metrics.complexity_score for comp in components)
        avg_complexity = total_complexity / len(components) if components else 0

        total_loc = sum(comp.metrics.lines_of_code for comp in components)

        return {
            "total_components": len(components),
            "component_types": type_distribution,
            "tag_categories": tag_categories,
            "architectural_layers": layer_distribution,
            "total_lines_of_code": total_loc,
            "average_complexity": round(avg_complexity, 2),
            "high_complexity_components": len(
                [c for c in components if c.metrics.complexity_score > 7.0]
            ),
        }

    def _perform_static_analysis(
        self, codebase_path: str, recursive: bool
    ) -> Tuple[List[CodeComponent], List[Relationship]]:
        """Perform static analysis on the codebase."""
        self.logger.info("Performing static analysis...")

        start_time = time.time()
        components, relationships = self.static_analyzer.analyze_directory(
            codebase_path, recursive
        )
        duration = time.time() - start_time

        log_performance(
            "static_analysis",
            duration,
            component_count=len(components),
            relationship_count=len(relationships),
        )

        return components, relationships

    def _enhance_with_ai_tagging(
        self, components: List[CodeComponent]
    ) -> List[CodeComponent]:
        """
        Enhance components with AI-assisted tagging.

        This is a placeholder for AI integration - would connect to OpenAI/Anthropic
        to analyze code semantics and suggest additional tags.
        """
        self.logger.info(
            "AI-assisted tagging not yet implemented - using static analysis only"
        )

        # TODO: Implement AI-assisted tagging
        # - Group components by file or logical units
        # - Send to AI service with structured prompts
        # - Parse AI responses for tag suggestions
        # - Apply tags with confidence scores
        # - Validate against existing tags

        return components

    def _validate_analysis_results(
        self, components: List[CodeComponent], relationships: List[Relationship]
    ) -> None:
        """
        Validate analysis results for consistency and quality.

        Performs cross-validation between different analysis methods and
        checks for potential issues or inconsistencies.
        """
        self.logger.info("Validating analysis results...")

        validation_issues = []

        # Check for components without tags
        untagged_components = [c for c in components if not c.tags.tags]
        if untagged_components:
            validation_issues.append(
                f"Found {len(untagged_components)} components without tags"
            )

        # Check for very low confidence components
        low_confidence = [
            c
            for c in components
            if c.confidence < self.settings.analysis.min_confidence_threshold
        ]
        if low_confidence:
            validation_issues.append(
                f"Found {len(low_confidence)} components with low confidence"
            )

        # Check for orphaned relationships
        component_ids = {c.id for c in components}
        orphaned_rels = [
            r
            for r in relationships
            if r.source_id not in component_ids or r.target_id not in component_ids
        ]
        if orphaned_rels:
            validation_issues.append(
                f"Found {len(orphaned_rels)} orphaned relationships"
            )

        if validation_issues:
            self.logger.warning(
                f"Validation issues found: {'; '.join(validation_issues)}"
            )
            log_analysis_event("validation_issues", issues=validation_issues)
        else:
            self.logger.info("Validation completed successfully")

    def _create_codebase_component(
        self,
        codebase_path: str,
        components: List[CodeComponent],
        relationships: List[Relationship],
    ) -> CodeComponent:
        """Create a top-level component representing the entire codebase."""
        from ...core.domain.code_component import CodeMetrics, ComponentType

        codebase_name = Path(codebase_path).name

        # Calculate aggregate metrics
        total_loc = sum(c.metrics.lines_of_code for c in components)
        total_complexity = sum(c.metrics.complexity_score for c in components)
        avg_complexity = total_complexity / len(components) if components else 0

        # Count components by type
        file_count = len(
            [
                c
                for c in components
                if (
                    c.component_type
                    if isinstance(c.component_type, str)
                    else c.component_type.value
                )
                == "file"
            ]
        )
        class_count = len(
            [
                c
                for c in components
                if (
                    c.component_type
                    if isinstance(c.component_type, str)
                    else c.component_type.value
                )
                == "class"
            ]
        )
        method_count = len(
            [
                c
                for c in components
                if (
                    c.component_type
                    if isinstance(c.component_type, str)
                    else c.component_type.value
                )
                == "method"
            ]
        )
        function_count = len(
            [
                c
                for c in components
                if (
                    c.component_type
                    if isinstance(c.component_type, str)
                    else c.component_type.value
                )
                == "function"
            ]
        )

        metrics = CodeMetrics(
            lines_of_code=total_loc, dependency_count=len(relationships)
        )

        # Determine architectural style and layer distribution
        layer_distribution = {}
        for component in components:
            layer = component.architectural_layer
            if layer:
                layer_distribution[layer] = layer_distribution.get(layer, 0) + 1

        # Infer tags for the codebase
        tags = set()
        codebase_tag = self.tag_registry.get_tag("Codebase")
        if codebase_tag:
            tags.add(codebase_tag)

        return CodeComponent(
            name=codebase_name,
            component_type=ComponentType.CODEBASE,
            file_path=codebase_path,
            tags=TagCollection(tags=tags),
            metrics=metrics,
            metadata={
                "architecture_style": "hexagonal",  # Since this is a hexagonal architecture tagger
                "layer_distribution": layer_distribution,
                "component_count": len(components),
                "file_count": file_count,
                "class_count": class_count,
                "method_count": method_count,
                "function_count": function_count,
                "average_complexity": round(avg_complexity, 2),
                "total_relationships": len(relationships),
            },
        )

    def _add_codebase_relationships(
        self, codebase_component: CodeComponent, file_components: List[CodeComponent]
    ) -> None:
        """Add containment relationships from codebase to top-level files."""
        from ...core.domain.code_component import Relationship, RelationshipType

        for component in file_components:
            comp_type = (
                component.component_type
                if isinstance(component.component_type, str)
                else component.component_type.value
            )
            if comp_type == "file":
                relationship = Relationship(
                    source_id=codebase_component.id,
                    target_id=component.id,
                    relationship_type=RelationshipType.CONTAINS,
                )
                codebase_component.add_relationship(relationship)
