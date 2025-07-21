#!/usr/bin/env python3
"""
AI Structural Code Tagger

Builds on existing CLI Knowledge Agent to analyze Python files and apply
structural/architectural tagging rules from ai_tagging_rules.md.

This script:
1. Uses existing file reading methods from CLI Knowledge Agent
2. Focuses on structural analysis (not derived metrics like complexity)
3. Applies hexagonal architecture tagging
4. Saves results in JSON format with code snippets
5. Leverages existing Supabase vector embeddings context
6. Read-only operation - never modifies source files

Usage:
    python ai_codebase_tagger.py --analyze-all
    python ai_codebase_tagger.py --file backend/main.py
    python ai_codebase_tagger.py --directory backend/ --max-files 10
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import fnmatch
import time

# Optional YAML support
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai_tagger.log')
    ]
)
logger = logging.getLogger(__name__)

# Add paths to import existing tools
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools', 'agents'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts', 'utilities'))

# Import existing CLI Knowledge Agent
try:
    from cli_knowledge_agent import CLIKnowledgeAgent
    logger.info("CLI Knowledge Agent imported successfully")
except ImportError as e:
    logger.error(f"Failed to import CLI Knowledge Agent: {e}")
    logger.error("Make sure tools/agents/cli_knowledge_agent.py is available")
    sys.exit(1)

# Define the structural tagging prompt focused on architecture, not derived metrics
STRUCTURAL_TAGGING_PROMPT = """
You are an expert software architect and code analyst. Analyze the provided Python code file and identify its STRUCTURAL and ARCHITECTURAL characteristics based on hexagonal architecture principles.

FOCUS ON STRUCTURE, NOT DERIVED METRICS like complexity scores or quality assessments.

Your task is to identify:

1. **Architectural Layer Tags**: Where this code sits in hexagonal architecture
2. **Role Tags**: What type of component this represents
3. **Pattern Tags**: What design patterns are implemented
4. **Structural Relationships**: How components relate to each other
5. **Intent Detection**: Existing architectural intent markers

Apply these STRUCTURAL tagging rules:

**Hexagonal Architecture Layers:**
- `core:entity` - Domain entities with business logic
- `core:value-object` - Immutable value objects
- `core:service` - Domain services containing business rules
- `core:aggregate` - Aggregate roots managing consistency
- `application:use-case` - Application use cases coordinating flow
- `application:service` - Application services orchestrating operations
- `application:port` - Abstract interfaces (ports)
- `infrastructure:adapter` - Concrete implementations of ports
- `infrastructure:repository` - Data persistence implementations
- `infrastructure:external` - External system integrations
- `interface:controller` - HTTP/API controllers
- `interface:dto` - Data transfer objects
- `interface:serializer` - Data serialization/deserialization

**Structural Role Tags:**
- `Factory` - Object creation patterns
- `Strategy` - Strategy pattern implementations
- `Observer` - Observer pattern implementations
- `Decorator` - Decorator pattern implementations
- `Adapter` - Adapter pattern implementations
- `Command` - Command pattern implementations
- `Event` - Event handling components
- `Config` - Configuration components
- `Util` - Utility functions/classes

**Modern Architecture Patterns:**
- `Event:Producer` - Generates events
- `Event:Consumer` - Consumes events
- `Event:Handler` - Handles specific events
- `Service:Boundary` - Service boundary definitions
- `Pipeline:Source` - Data pipeline input
- `Pipeline:Transform` - Data transformation step
- `Pipeline:Sink` - Data pipeline output

**Structural Analysis Tasks:**
1. Identify imports and their architectural implications
2. Detect inheritance and composition relationships
3. Find existing @intent or architectural comments
4. Identify violation patterns (e.g., core importing infrastructure)
5. Map method calls and dependencies
6. Assign confidence scores (0.0-1.0) for each structural determination

**Confidence Scoring Guidelines:**
- 0.9-1.0: Very clear indicators (explicit patterns, obvious layer placement)
- 0.7-0.8: Strong indicators (clear imports, naming conventions)
- 0.5-0.6: Moderate confidence (some ambiguity, mixed signals)
- 0.3-0.4: Low confidence (unclear patterns, generic code)
- 0.0-0.2: Very uncertain (insufficient information)

**DO NOT ANALYZE:**
- Cyclomatic complexity scores
- Code quality metrics
- Performance measurements
- Test coverage
- Documentation quality

These are conclusions drawn AFTER structural analysis, not structural properties themselves.

Return ONLY a JSON object (no markdown formatting) with this exact structure:

{
  "file_path": "path/to/file.py",
  "analysis_timestamp": "2025-01-21T05:15:33Z",
  "structural_analysis": {
    "primary_layer": "core",
    "primary_layer_confidence": 0.95,
    "secondary_layers": [],
    "component_type": "entity",
    "component_type_confidence": 0.90,
    "architectural_role": "aggregate_root",
    "architectural_role_confidence": 0.85,
    "design_patterns": [{"pattern": "Factory", "confidence": 0.80}, {"pattern": "Strategy", "confidence": 0.75}],
    "intent_markers": ["@intent: core:entity:aggregate"],
    "overall_confidence": 0.87
  },
  "code_elements": [
    {
      "element_type": "class",
      "element_name": "OrderService",
      "line_range": [25, 65],
      "structural_tags": [{"tag": "core:service", "confidence": 0.90}],
      "pattern_tags": [{"tag": "Factory", "confidence": 0.75}],
      "code_snippet": "class OrderService:\n    def calculate_total(self, order):\n        # Implementation...",
      "imports_used": ["Order", "Money"],
      "dependencies": ["Order", "Money", "TaxCalculator"],
      "element_confidence": 0.88,
      "methods": [
        {
          "name": "calculate_total",
          "line_range": [30, 35],
          "visibility": "public",
          "structural_role": "business_logic"
        }
      ]
    }
  ],
  "structural_relationships": [
    {
      "source_element": "OrderService",
      "target_element": "Order",
      "relationship_type": "USES",
      "relationship_context": "composition",
      "line_number": 30
    }
  ],
  "architectural_assessment": {
    "layer_compliance": true,
    "violations": [
      {
        "violation_type": "layer_violation",
        "description": "Core component importing infrastructure",
        "source": "OrderEntity",
        "target": "DatabaseConnection",
        "line_number": 45,
        "severity": "high"
      }
    ],
    "intent_alignment": "high",
    "missing_patterns": ["Repository interface not defined"]
  },
  "source_citations": [
    {
      "citation_id": "ref_1",
      "cited_for": "architectural_pattern_identification",
      "supporting_evidence": "Documentation shows similar hexagonal architecture implementation",
      "confidence_boost": 0.1
    }
  ]
}

**Citation Instructions:**
If relevant documentation context is provided above (marked with [ref_X] citations), use these sources to:
1. **Increase confidence scores** when patterns match documented examples
2. **Provide supporting evidence** in your analysis
3. **Reference citations** in your assessment using citation_id
4. **Boost confidence** when architectural decisions align with documented best practices

Analyze the file thoroughly and provide structural tags focusing on architectural layers, design patterns, and component relationships.
"""

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from JSON or YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.lower().endswith(('.yaml', '.yml')):
                if not YAML_AVAILABLE:
                    logger.error("PyYAML not installed. Install with: pip install pyyaml")
                    sys.exit(1)
                config = yaml.safe_load(f)
            else:
                config = json.load(f)
        
        logger.info(f"Loaded configuration from {config_path}")
        return config
        
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        logger.error(f"Error parsing configuration file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)

class AIStructuralTagger:
    """
    AI-powered structural code tagger that builds on existing CLI Knowledge Agent.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize the tagger with existing CLI Knowledge Agent.
        
        Args:
            model: OpenAI model to use for analysis
        """
        try:
            self.agent = CLIKnowledgeAgent(model=model, temperature=0.1)
            logger.info(f"Initialized AI Structural Tagger with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize CLI Knowledge Agent: {e}")
            raise
    
    def find_python_files(self, directories: List[str] = None, exclude_patterns: List[str] = None) -> List[str]:
        """
        Find Python files using existing agent's file listing capabilities.
        
        Args:
            directories: List of directories to search (defaults to ["."])
            exclude_patterns: Patterns to exclude
            
        Returns:
            List of Python file paths
        """
        if directories is None:
            directories = ["."]
        if exclude_patterns is None:
            exclude_patterns = ['*test*', '*example*', '__pycache__*', '.git*', 'venv*', 'node_modules*']
        
        all_python_files = []
        
        for root_dir in directories:
            logger.info(f"Searching directory: {root_dir}")
            python_files = self._find_python_files_in_directory(root_dir, exclude_patterns)
            all_python_files.extend(python_files)
        
        return sorted(list(set(all_python_files)))
    
    def _find_python_files_in_directory(self, root_dir: str, exclude_patterns: List[str]) -> List[str]:
        """
        Find Python files in a single directory using the agent's capabilities.
        
        Args:
            root_dir: Directory to search (relative to project root)
            exclude_patterns: Patterns to exclude
            
        Returns:
            List of Python file paths
        """
        python_files = []
        
        try:
            # Use direct filesystem access like CLI Knowledge Agent
            project_root = Path(__file__).parent.absolute()
            search_path = project_root / root_dir if root_dir != "." else project_root
            
            if not search_path.exists():
                logger.warning(f"Directory does not exist: {root_dir}")
                return []
            
            # Find all Python files recursively
            for py_file in search_path.rglob('*.py'):
                # Get relative path from project root
                try:
                    rel_path = py_file.relative_to(project_root)
                    file_path = str(rel_path)
                    
                    # Check exclusion patterns
                    should_exclude = False
                    for pattern in exclude_patterns:
                        if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(py_file.name, pattern):
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        python_files.append(file_path)
                        
                except ValueError:
                    # File is outside project root, skip it
                    continue
            
            return python_files
            
        except Exception as e:
            logger.error(f"Error finding Python files in {root_dir}: {e}")
            return []
    
    def search_relevant_vectors(self, file_path: str, code_content: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search Supabase vector database for relevant documentation and examples.
        
        Args:
            file_path: Path to the file being analyzed
            code_content: Content of the file
            max_results: Maximum number of vector results to return
            
        Returns:
            List of relevant vector search results with sources
        """
        try:
            # Create search query from file path and key code elements
            search_query = f"""Analyze structural patterns in {file_path}.
            
Code content preview:
{code_content[:500]}...
            
Find relevant architectural patterns, design principles, and similar code examples."""
            
            logger.debug(f"Searching vectors for: {file_path}")
            
            # Use CLI Knowledge Agent to search vectors via Supabase
            vector_question = f"""Search for relevant architectural patterns and code examples related to this file: {file_path}
            
Code characteristics:
{code_content[:300]}...
            
Find similar patterns, architectural guidance, and relevant documentation."""
            
            response = self.agent.ask_question(vector_question, conversation_context=False)
            
            # Extract vector sources from the knowledge assistant's response
            # The ProjectKnowledgeAssistant should return contextual information
            vector_sources = []
            
            if response and len(response) > 50:  # Non-empty meaningful response
                vector_sources.append({
                    'source_type': 'supabase_vector_search',
                    'query': search_query[:100] + '...',
                    'content_preview': response[:200] + '...' if len(response) > 200 else response,
                    'relevance_score': 0.85,  # Estimated relevance
                    'source_metadata': {
                        'search_timestamp': datetime.now(timezone.utc).isoformat(),
                        'file_context': file_path,
                        'vector_table': 'python_code_chunks'
                    }
                })
                
                logger.info(f"Found {len(vector_sources)} vector sources for {file_path}")
            else:
                logger.warning(f"No relevant vector sources found for {file_path}")
                
            return vector_sources[:max_results]
            
        except Exception as e:
            logger.error(f"Error searching vectors for {file_path}: {e}")
            return []
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a single file for structural patterns using AI with vector search and citations.
        
        Args:
            file_path: Path to the Python file to analyze
            
        Returns:
            Analysis result dictionary with vector sources and citations (never None)
        """
        logger.info(f"Analyzing file: {file_path}")
        
        # Base result structure - always returned
        base_result = {
            'file_path': file_path,
            'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            'analysis_status': 'unknown',
            'raw_response': None,
            'file_metadata': {},
            'structured_analysis': {},
            'vector_sources': [],
            'source_citations': [],
            'error': None
        }
        
        try:
            # Read file directly with security checks (like CLI Knowledge Agent)
            project_root = Path(__file__).parent.absolute()
            full_path = project_root / file_path
            
            # Security check - ensure the file is within the project directory
            if not str(full_path.absolute()).startswith(str(project_root)):
                base_result.update({
                    'analysis_status': 'file_read_failed',
                    'file_metadata': {
                        'read_success': False,
                        'error': 'Access denied: File path outside project directory'
                    },
                    'error': 'Access denied: File path outside project directory'
                })
                return base_result
            
            # Check if file exists
            if not full_path.exists():
                base_result.update({
                    'analysis_status': 'file_read_failed', 
                    'file_metadata': {
                        'read_success': False,
                        'error': 'File not found'
                    },
                    'error': 'File not found'
                })
                return base_result
                
            # Read the file content
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                max_lines = 500  # Reasonable limit for analysis
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip('\n\r'))
                
                file_content = '\n'.join(lines)
            
            # Get file stats
            file_stats = full_path.stat()
            
            # Update file metadata 
            base_result['file_metadata'] = {
                'read_success': True,
                'file_path': file_path,
                'lines_read': len(lines),
                'max_lines_reached': len(lines) == max_lines,
                'file_size_bytes': file_stats.st_size,
                'content_length': len(file_content),
                'last_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
            }
            
            # Search for relevant vectors and documentation
            logger.info(f"Searching for relevant documentation vectors for {file_path}")
            vector_sources = self.search_relevant_vectors(file_path, file_content, max_results=3)
            base_result['vector_sources'] = vector_sources
            
            # Create source citations from vector results
            source_citations = []
            vector_context = ""
            
            if vector_sources:
                vector_context = "\n\nRelevant Documentation Context:\n"
                for i, source in enumerate(vector_sources, 1):
                    citation = {
                        'citation_id': f"ref_{i}",
                        'source_type': source['source_type'],
                        'relevance_score': source['relevance_score'],
                        'content_preview': source['content_preview'],
                        'metadata': source['source_metadata']
                    }
                    source_citations.append(citation)
                    vector_context += f"[{citation['citation_id']}] {source['content_preview']}\n"
            
            base_result['source_citations'] = source_citations
            
            # Create enhanced analysis prompt with vector context and citations
            analysis_question = f"""
            Please analyze the Python file '{file_path}' for structural and architectural characteristics.
            
            File Content:
            ```python
            {file_content}
            ```
            {vector_context}
            
            {STRUCTURAL_TAGGING_PROMPT}
            """
            
            # Use agent's ask_question method to get OpenAI analysis
            logger.info(f"Requesting analysis for {file_path}...")
            response = self.agent.ask_question(
                question=analysis_question,
                conversation_context=False  # Don't use conversation context for file analysis
            )
            
            # Always capture the raw response
            base_result['raw_response'] = response
            base_result['raw_response_length'] = len(response)
            
            # Try to extract JSON from response
            try:
                # Look for JSON in the response (multiple patterns)
                import re
                
                # Try different JSON extraction patterns
                json_patterns = [
                    r'\{[^{}]*"file_path"[^{}]*\{.*?\}.*?\}',  # Look for our expected structure
                    r'\{.*"structural_analysis".*?\}',        # Look for structural_analysis key
                    r'\{.*\}',                                 # Any JSON object
                ]
                
                analysis_result = None
                for pattern in json_patterns:
                    json_match = re.search(pattern, response, re.DOTALL)
                    if json_match:
                        try:
                            analysis_result = json.loads(json_match.group())
                            break
                        except json.JSONDecodeError:
                            continue
                
                if analysis_result:
                    # Successful analysis - merge with base result
                    base_result.update({
                        'analysis_status': 'success',
                        'structured_analysis': analysis_result
                    })
                    
                    # Ensure required fields are present
                    if 'file_path' not in analysis_result:
                        base_result['structured_analysis']['file_path'] = file_path
                    if 'analysis_timestamp' not in analysis_result:
                        base_result['structured_analysis']['analysis_timestamp'] = base_result['analysis_timestamp']
                    
                    logger.info(f"✓ Successfully analyzed {file_path}")
                    return base_result
                
                else:
                    # No valid JSON found - save raw response
                    logger.warning(f"No valid JSON found in response for {file_path}")
                    base_result.update({
                        'analysis_status': 'json_extraction_failed',
                        'error': 'No valid JSON found in OpenAI response',
                        'response_preview': response[:300] + '...' if len(response) > 300 else response
                    })
                    return base_result
                    
            except Exception as je:
                logger.error(f"JSON processing error for {file_path}: {je}")
                base_result.update({
                    'analysis_status': 'json_processing_error',
                    'error': f'JSON processing error: {str(je)}',
                    'response_preview': response[:300] + '...' if len(response) > 300 else response
                })
                return base_result
                
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            base_result.update({
                'analysis_status': 'analysis_error',
                'error': f'Analysis error: {str(e)}'
            })
            return base_result
    
    def analyze_codebase(self, target_files: List[str] = None, directories: List[str] = None, 
                        exclude_patterns: List[str] = None, max_files: int = None) -> List[Dict[str, Any]]:
        """
        Analyze multiple files or entire codebase.
        
        Args:
            target_files: Specific files to analyze, or None for directory search
            directories: List of directories to search (if target_files is None)
            exclude_patterns: Patterns to exclude from search
            max_files: Maximum number of files to analyze
            
        Returns:
            List of analysis results
        """
        if target_files is None:
            logger.info("Finding Python files in specified directories...")
            target_files = self.find_python_files(directories, exclude_patterns)
        
        if max_files and len(target_files) > max_files:
            target_files = target_files[:max_files]
            logger.info(f"Limited analysis to {max_files} files")
        
        logger.info(f"Analyzing {len(target_files)} Python files")
        
        results = []
        for i, file_path in enumerate(target_files):
            logger.info(f"Analyzing file {i+1}/{len(target_files)}: {file_path}")
            
            # analyze_file now always returns a dict, never None
            analysis = self.analyze_file(file_path)
            results.append(analysis)
            
            # Log based on analysis status
            status = analysis.get('analysis_status', 'unknown')
            if status == 'success':
                logger.info(f"✓ Successfully analyzed {file_path}")
            else:
                logger.warning(f"✗ Analysis issues for {file_path}: {status}")
            
            # Small delay to respect API limits
            time.sleep(0.5)
        
        return results
    
    def save_results(self, results: List[Dict[str, Any]], output_dir: str = "ai_tagging_results") -> str:
        """
        Save analysis results to JSON file.
        
        Args:
            results: Analysis results
            output_dir: Directory to save results
            
        Returns:
            Path to saved file
        """
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"structural_analysis_{timestamp}.json"
        output_path = os.path.join(output_dir, filename)
        
        # Calculate detailed statistics
        successful_analyses = len([r for r in results if r.get('analysis_status') == 'success'])
        failed_analyses = len([r for r in results if r.get('analysis_status') != 'success'])
        
        # Group by status for detailed breakdown
        status_breakdown = {}
        for result in results:
            status = result.get('analysis_status', 'unknown')
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        # Calculate confidence statistics for successful analyses
        confidence_stats = {
            'avg_confidence': 0.0,
            'min_confidence': 1.0,
            'max_confidence': 0.0,
            'confidence_distribution': {}
        }
        
        successful_results = [r for r in results if r.get('analysis_status') == 'success']
        if successful_results:
            confidences = []
            for result in successful_results:
                structured = result.get('structured_analysis', {})
                overall_confidence = structured.get('structural_analysis', {}).get('overall_confidence')
                if overall_confidence is not None:
                    confidences.append(overall_confidence)
            
            if confidences:
                confidence_stats['avg_confidence'] = sum(confidences) / len(confidences)
                confidence_stats['min_confidence'] = min(confidences)
                confidence_stats['max_confidence'] = max(confidences)
        
        # Prepare final output with enhanced metadata
        final_output = {
            "metadata": {
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "total_files_analyzed": len(results),
                "successful_analyses": successful_analyses,
                "failed_analyses": failed_analyses,
                "success_rate": successful_analyses / len(results) if results else 0.0,
                "status_breakdown": status_breakdown,
                "confidence_statistics": confidence_stats,
                "tool_version": "1.1.0",
                "analysis_type": "structural_architectural_tagging_with_confidence",
                "features": [
                    "robust_data_capture",
                    "confidence_scoring",
                    "raw_response_preservation",
                    "detailed_error_tracking"
                ]
            },
            "results": results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {output_path}")
        return output_path

def main():
    """Main function for the AI Structural Tagger."""
    parser = argparse.ArgumentParser(
        description="AI Structural Code Tagger - Builds on CLI Knowledge Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ai_codebase_tagger.py --analyze-all
  python ai_codebase_tagger.py --file backend/main.py
  python ai_codebase_tagger.py --directory backend/ --max-files 5
  python ai_codebase_tagger.py --analyze-all --max-files 10
        """
    )
    
    parser.add_argument("--analyze-all", action="store_true",
                       help="Analyze all Python files in the codebase")
    parser.add_argument("--file", type=str, 
                       help="Analyze a single specific file")
    parser.add_argument("--directory", type=str, default=".",
                       help="Directory to search for Python files (default: project root)")
    parser.add_argument("--config", type=str,
                       help="Configuration file (JSON/YAML) specifying directories and settings")
    parser.add_argument("--output-dir", type=str, default="ai_tagging_results", 
                       help="Directory to save results (default: ai_tagging_results)")
    parser.add_argument("--max-files", type=int, default=None, 
                       help="Maximum number of files to analyze")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", 
                       help="OpenAI model to use (default: gpt-4o-mini)")
    parser.add_argument("--debug", action="store_true", 
                       help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration if provided
    config = {}
    if args.config:
        config = load_config(args.config)
        logger.info(f"Using configuration file: {args.config}")
    
    # Validate arguments (config file can override requirement)
    if not args.analyze_all and not args.file and not config.get('directories'):
        logger.error("Must specify either --analyze-all, --file, or provide --config with directories")
        parser.print_help()
        sys.exit(1)
    
    # Merge config with command line arguments (CLI args take precedence)
    directories = config.get('directories', [args.directory]) if not args.file else None
    exclude_patterns = config.get('exclude_patterns', ['*test*', '*example*', '__pycache__*', '.git*', 'venv*', 'node_modules*'])
    output_dir = args.output_dir or config.get('output_dir', 'ai_tagging_results')
    max_files = args.max_files or config.get('max_files')
    model = args.model or config.get('model', 'gpt-4o-mini')
    
    logger.info("Starting AI Structural Code Tagging")
    if directories:
        logger.info(f"Target directories: {directories}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Model: {model}")
    if exclude_patterns:
        logger.info(f"Exclude patterns: {exclude_patterns}")
    
    try:
        # Initialize the AI Structural Tagger
        tagger = AIStructuralTagger(model=model)
        logger.info("AI Structural Tagger initialized successfully")
        
        # Determine files to analyze
        if args.file:
            # Single file analysis
            target_files = [args.file]
            logger.info(f"Analyzing single file: {args.file}")
            
            # Analyze the file
            analysis = tagger.analyze_file(args.file)
            results = [analysis]  # analyze_file always returns a dict now
        
        else:
            # Multi-directory codebase analysis
            logger.info("Analyzing codebase using configured directories...")
            results = tagger.analyze_codebase(
                target_files=None,
                directories=directories,
                exclude_patterns=exclude_patterns,
                max_files=max_files
            )
        
        # Save results
        output_file = tagger.save_results(results, output_dir)
        
        # Calculate detailed summary statistics
        successful = len([r for r in results if r.get('analysis_status') == 'success'])
        failed = len([r for r in results if r.get('analysis_status') != 'success'])
        
        # Status breakdown
        status_counts = {}
        for result in results:
            status = result.get('analysis_status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"\n=== AI STRUCTURAL TAGGING COMPLETE ===")
        print(f"Total files processed: {len(results)}")
        print(f"Successful analyses: {len([r for r in results if r.get('analysis_status') == 'success'])}")
        print(f"Failed/Partial analyses: {len(results) - len([r for r in results if r.get('analysis_status') == 'success'])}")
        
        # Show confidence statistics for successful analyses
        successful = len([r for r in results if r.get('analysis_status') == 'success'])
        if successful > 0:
            confidences = []
            for result in results:
                if (result.get('analysis_status') == 'success' and 
                    result.get('structured_analysis', {}).get('structural_analysis', {}).get('overall_confidence')):
                    confidences.append(result['structured_analysis']['structural_analysis']['overall_confidence'])
            
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                min_confidence = min(confidences)
                max_confidence = max(confidences)
                print(f"\nConfidence Statistics:")
                print(f"  Average: {avg_confidence:.2f}")
                print(f"  Range: {min_confidence:.2f} - {max_confidence:.2f}")
        
        elif len(results) == 0:
            print("\nNo files were found for analysis. Check your directory paths and exclude patterns.")
        
        # Show sample result if debug enabled
        if args.debug and successful > 0:
            sample_result = next((r for r in results if r.get('analysis_status') == 'success'), None)
            if sample_result:
                print(f"\n=== SAMPLE SUCCESSFUL ANALYSIS ===")
                # Show structured analysis if available
                structured = sample_result.get('structured_analysis', {})
                if structured:
                    sample_copy = dict(structured)
                    # Truncate long content for display
                    if 'code_elements' in sample_copy:
                        for element in sample_copy['code_elements']:
                            if 'code_snippet' in element and len(element['code_snippet']) > 200:
                                element['code_snippet'] = element['code_snippet'][:200] + '...'
                    print(json.dumps(sample_copy, indent=2))
                else:
                    print("No structured analysis available in sample.")
            
            # Also show a sample of any failures for debugging
            if failed > 0:
                failed_sample = next((r for r in results if r.get('analysis_status') != 'success'), None)
                if failed_sample:
                    print(f"\n=== SAMPLE FAILED ANALYSIS DEBUG INFO ===")
                    print(f"File: {failed_sample.get('file_path')}")
                    print(f"Status: {failed_sample.get('analysis_status')}")
                    print(f"Error: {failed_sample.get('error', 'No error message')}")
                    if failed_sample.get('response_preview'):
                        print(f"Response preview: {failed_sample.get('response_preview')[:200]}...")
    
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
