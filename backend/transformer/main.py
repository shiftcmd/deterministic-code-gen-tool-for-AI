"""
Main orchestrator for the Transformation Domain.

This module coordinates the transformation phase, converting extraction data
from Phase 1 into standardized Neo4j tuples ready for Phase 3 upload.
"""

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, AsyncIterator
from datetime import datetime

from .core.tuple_generator import TupleGenerator
from .models.tuples import TupleSet
from .models.metadata import TransformationMetadata, TransformationResult, TransformationStatus
from .services.progress_service import ProgressService, NullProgressService
from .formatters.neo4j_formatter import Neo4jFormatter

logger = logging.getLogger(__name__)


class TransformationOrchestrator:
    """
    Main orchestrator for the transformation phase.
    
    Coordinates the transformation pipeline from extraction data
    to Neo4j-ready tuples with progress reporting and error handling.
    """
    
    def __init__(
        self,
        job_id: Optional[str] = None,
        orchestrator_url: Optional[str] = None,
        enable_progress_reporting: bool = True
    ):
        """
        Initialize the transformation orchestrator.
        
        Args:
            job_id: Unique job identifier (auto-generated if not provided)
            orchestrator_url: URL of the main orchestrator for progress reporting
            enable_progress_reporting: Whether to enable progress reporting
        """
        self.job_id = job_id or str(uuid.uuid4())
        
        # Initialize services
        if enable_progress_reporting:
            self.progress_service = ProgressService(self.job_id, orchestrator_url)
        else:
            self.progress_service = NullProgressService(self.job_id)
            
        self.tuple_generator = TupleGenerator()
        self.neo4j_formatter = Neo4jFormatter()
        
        logger.info(f"Initialized TransformationOrchestrator with job_id: {self.job_id}")
    
    async def transform_extraction_data(
        self,
        extraction_data: Dict[str, Any],
        output_formats: List[str] = ["neo4j"],
        output_directory: Optional[str] = None
    ) -> TransformationResult:
        """
        Transform extraction data into Neo4j tuples.
        
        Args:
            extraction_data: Raw extraction data from Phase 1
            output_formats: List of output formats to generate
            output_directory: Directory to write output files
            
        Returns:
            TransformationResult with metadata and output file paths
        """
        result = TransformationResult(
            job_id=self.job_id,
            metadata=self.progress_service.get_metadata()
        )
        
        try:
            # Validate input data
            if not extraction_data or "modules" not in extraction_data:
                raise ValueError("Invalid extraction data: missing 'modules' section")
            
            modules = extraction_data["modules"]
            if not modules:
                raise ValueError("No modules found in extraction data")
            
            # Calculate input statistics
            input_stats = self._calculate_input_stats(extraction_data)
            
            # Report transformation start
            self.progress_service.start_transformation(input_stats)
            logger.info(f"Starting transformation of {len(modules)} modules")
            
            # Generate tuples for all modules
            all_tuples = TupleSet()
            total_modules = len(modules)
            
            for i, (module_path, module_data) in enumerate(modules.items()):
                try:
                    # Generate tuples for this module
                    module_tuples = self.tuple_generator.generate_module_tuples(
                        module_path, module_data
                    )
                    
                    # Merge with overall tuple set
                    all_tuples = all_tuples.merge(module_tuples)
                    
                    # Report progress
                    self.progress_service.report_progress(
                        current=i + 1,
                        total=total_modules,
                        step="tuple_generation",
                        message=f"Generated tuples for {module_data.get('name', 'unknown')}"
                    )
                    
                except Exception as e:
                    logger.warning(f"Failed to process module {module_path}: {e}")
                    result.add_warning(f"Module {module_path}: {str(e)}")
            
            # Report tuple generation completion
            self.progress_service.report_step_completed("tuple_generation")
            
            # Generate output in requested formats
            output_directory = output_directory or "."
            output_dir_path = Path(output_directory)
            output_dir_path.mkdir(parents=True, exist_ok=True)
            
            for format_name in output_formats:
                try:
                    output_file = await self._generate_output_format(
                        format_name, all_tuples, output_dir_path
                    )
                    result.add_output_file(format_name, str(output_file))
                    
                except Exception as e:
                    logger.error(f"Failed to generate {format_name} output: {e}")
                    result.add_error(f"Output format {format_name}: {str(e)}")
            
            # Update final statistics
            final_stats = {
                "nodes": all_tuples.node_count,
                "relationships": all_tuples.relationship_count,
                "total_tuples": all_tuples.size
            }
            
            result.metadata.output_nodes_count = all_tuples.node_count
            result.metadata.output_relationships_count = all_tuples.relationship_count
            
            # Report completion
            if not result.has_errors:
                self.progress_service.complete_transformation(
                    result.output_files, final_stats
                )
                logger.info(f"Transformation completed successfully: {final_stats}")
            else:
                self.progress_service.report_error(
                    f"Transformation completed with {len(result.errors)} errors"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Transformation failed: {e}")
            result.add_error(str(e))
            self.progress_service.report_error(str(e))
            return result
    
    async def stream_transform(
        self,
        extraction_stream: AsyncIterator[Dict[str, Any]],
        batch_size: int = 100
    ) -> AsyncIterator[TupleSet]:
        """
        Transform extraction data in streaming fashion.
        
        Args:
            extraction_stream: Async iterator of extraction data
            batch_size: Number of modules to process per batch
            
        Yields:
            TupleSet objects for each batch of processed modules
        """
        batch_tuples = TupleSet()
        batch_count = 0
        module_count = 0
        
        try:
            async for extraction_data in extraction_stream:
                # Extract modules from current data
                modules = extraction_data.get("modules", {})
                
                for module_path, module_data in modules.items():
                    try:
                        # Generate tuples for this module
                        module_tuples = self.tuple_generator.generate_module_tuples(
                            module_path, module_data
                        )
                        
                        # Add to current batch
                        batch_tuples = batch_tuples.merge(module_tuples)
                        module_count += 1
                        
                        # Yield batch when it reaches target size
                        if module_count >= batch_size:
                            batch_count += 1
                            self.progress_service.report_batch_processed(
                                batch_count, batch_tuples.size, 0.0  # TODO: Track timing
                            )
                            
                            yield batch_tuples
                            
                            # Reset for next batch
                            batch_tuples = TupleSet()
                            module_count = 0
                            
                    except Exception as e:
                        logger.warning(f"Failed to process module {module_path}: {e}")
            
            # Yield final batch if it has any tuples
            if batch_tuples.size > 0:
                batch_count += 1
                self.progress_service.report_batch_processed(
                    batch_count, batch_tuples.size, 0.0
                )
                yield batch_tuples
                
        except Exception as e:
            logger.error(f"Stream transformation failed: {e}")
            self.progress_service.report_error(str(e))
            raise
    
    def _calculate_input_stats(self, extraction_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate statistics about input data."""
        modules = extraction_data.get("modules", {})
        
        stats = {
            "modules": len(modules),
            "classes": 0,
            "functions": 0,
            "variables": 0,
            "imports": 0
        }
        
        for module_data in modules.values():
            stats["classes"] += len(module_data.get("classes", []))
            stats["functions"] += len(module_data.get("functions", []))
            stats["variables"] += len(module_data.get("variables", []))
            stats["imports"] += len(module_data.get("imports", []))
            
            # Count methods in classes
            for class_data in module_data.get("classes", []):
                stats["functions"] += len(class_data.get("methods", []))
        
        return stats
    
    async def _generate_output_format(
        self,
        format_name: str,
        tuple_set: TupleSet,
        output_directory: Path
    ) -> Path:
        """
        Generate output in specified format.
        
        Args:
            format_name: Name of the output format
            tuple_set: TupleSet to format
            output_directory: Directory to write output
            
        Returns:
            Path to generated output file
        """
        if format_name == "neo4j":
            output_file = output_directory / f"neo4j_commands_{self.job_id}.cypher"
            cypher_commands = self.neo4j_formatter.format(tuple_set)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(cypher_commands)
                
            logger.info(f"Generated Neo4j output: {output_file}")
            return output_file
            
        elif format_name == "json":
            output_file = output_directory / f"tuples_{self.job_id}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(tuple_set.to_dict(), f, indent=2)
                
            logger.info(f"Generated JSON output: {output_file}")
            return output_file
            
        else:
            raise ValueError(f"Unsupported output format: {format_name}")
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get current job status and metadata."""
        return self.progress_service.get_metadata().to_dict()
    
    def clear_caches(self) -> None:
        """Clear all internal caches."""
        self.tuple_generator.clear_cache()


# Convenience function for simple transformations
async def transform_file(
    input_file: str,
    output_directory: str = ".",
    output_formats: List[str] = ["neo4j"],
    job_id: Optional[str] = None
) -> TransformationResult:
    """
    Transform a single extraction file.
    
    Args:
        input_file: Path to extraction JSON file
        output_directory: Directory for output files
        output_formats: List of output formats to generate
        job_id: Optional job ID
        
    Returns:
        TransformationResult
    """
    # Load extraction data
    with open(input_file, 'r', encoding='utf-8') as f:
        extraction_data = json.load(f)
    
    # Create orchestrator and transform
    orchestrator = TransformationOrchestrator(job_id=job_id)
    return await orchestrator.transform_extraction_data(
        extraction_data, output_formats, output_directory
    )