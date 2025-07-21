"""
Command-line interface for the Generic Hexagonal Architecture Tagging System.

This module provides a comprehensive CLI for analyzing codebases, generating reports,
and managing the tagging system configuration.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..application.services.tagging_service import TaggingService
from ..config.logging import get_logger, setup_logging
from ..config.settings import get_settings
from ..core.domain.code_component import CodeComponent, Relationship

console = Console()
logger = get_logger(__name__)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option(
    "--config", type=click.Path(exists=True), help="Path to configuration file"
)
@click.pass_context
def cli(ctx: click.Context, debug: bool, config: Optional[str]) -> None:
    """Generic Hexagonal Architecture Tagging System CLI."""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    ctx.obj["config"] = config

    # Setup logging
    setup_logging()

    if debug:
        console.print("[bold yellow]Debug mode enabled[/bold yellow]")


@cli.command()
@click.argument(
    "codebase_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option(
    "--output", "-o", type=click.Path(), help="Output file for results (JSON format)"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "table", "summary"]),
    default="summary",
    help="Output format",
)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Analyze subdirectories recursively",
)
@click.option(
    "--include-metrics", is_flag=True, help="Include detailed metrics in output"
)
@click.pass_context
def analyze(
    ctx: click.Context,
    codebase_path: str,
    output: Optional[str],
    output_format: str,
    recursive: bool,
    include_metrics: bool,
) -> None:
    """Analyze a codebase and generate architectural tags."""

    try:
        console.print(f"[bold green]Analyzing codebase:[/bold green] {codebase_path}")

        # Initialize tagging service
        tagging_service = TaggingService()

        # Perform analysis with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Analyzing codebase...", total=None)

            components, relationships = tagging_service.analyze_codebase(
                codebase_path, recursive=recursive
            )

            progress.update(task, description="Generating summary...")
            summary = tagging_service.get_analysis_summary(components)

        # Display results based on format
        if output_format == "summary":
            _display_summary(summary, components, relationships)
        elif output_format == "table":
            _display_table(components, relationships, include_metrics)
        elif output_format == "json":
            _display_json(components, relationships, summary)

        # Save to file if requested
        if output:
            _save_results(output, components, relationships, summary)
            console.print(f"[green]Results saved to:[/green] {output}")

        console.print(f"[bold green]Analysis completed successfully![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error during analysis:[/bold red] {e}")
        if ctx.obj.get("debug"):
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.argument(
    "file_path", type=click.Path(exists=True, file_okay=True, dir_okay=False)
)
@click.option(
    "--output", "-o", type=click.Path(), help="Output file for results (JSON format)"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "table", "summary"]),
    default="summary",
    help="Output format",
)
@click.pass_context
def analyze_file(
    ctx: click.Context, file_path: str, output: Optional[str], output_format: str
) -> None:
    """Analyze a single source code file."""

    try:
        console.print(f"[bold green]Analyzing file:[/bold green] {file_path}")

        # Initialize tagging service
        tagging_service = TaggingService()

        # Perform analysis
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Analyzing file...", total=None)

            components, relationships = tagging_service.analyze_file(file_path)

        if not components:
            console.print("[yellow]No components found in file[/yellow]")
            return

        # Display results
        if output_format == "summary":
            _display_file_summary(components, relationships)
        elif output_format == "table":
            _display_table(components, relationships, True)
        elif output_format == "json":
            _display_json(components, relationships, {})

        # Save to file if requested
        if output:
            _save_results(output, components, relationships, {})
            console.print(f"[green]Results saved to:[/green] {output}")

    except Exception as e:
        console.print(f"[bold red]Error during file analysis:[/bold red] {e}")
        if ctx.obj.get("debug"):
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option("--category", type=str, help="Filter tags by category")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def list_tags(category: Optional[str], output_format: str) -> None:
    """List available tags in the system."""

    from ..core.domain.tag import TagCategory, get_tag_registry

    registry = get_tag_registry()

    if category:
        try:
            cat = TagCategory(category)
            tags = registry.get_tags_by_category(cat)
        except ValueError:
            console.print(f"[red]Invalid category:[/red] {category}")
            console.print(
                f"[yellow]Available categories:[/yellow] {', '.join([c.value for c in TagCategory])}"
            )
            return
    else:
        tags = registry.get_all_tags()

    if output_format == "table":
        _display_tags_table(tags)
    else:
        _display_tags_json(tags)


@cli.command()
def config_info() -> None:
    """Display current configuration information."""

    settings = get_settings()

    # Create configuration summary
    config_data = {
        "project_name": settings.project_name,
        "version": settings.version,
        "debug": settings.debug,
        "neo4j": {
            "uri": settings.neo4j.uri,
            "database": settings.neo4j.database,
            "username": settings.neo4j.username,
        },
        "ai": {
            "provider": settings.ai.provider.value,
            "model": settings.ai.model,
            "api_key_configured": bool(settings.ai.api_key),
        },
        "analysis": {
            "enable_ai_tagging": settings.analysis.enable_ai_tagging,
            "enable_static_analysis": settings.analysis.enable_static_analysis,
            "min_confidence_threshold": settings.analysis.min_confidence_threshold,
            "parallel_processing": settings.analysis.parallel_processing,
            "max_workers": settings.analysis.max_workers,
        },
    }

    console.print(
        Panel(JSON.from_data(config_data), title="Configuration", expand=False)
    )


def _display_summary(
    summary: Dict[str, Any],
    components: List[CodeComponent],
    relationships: List[Relationship],
) -> None:
    """Display analysis summary in a formatted panel."""

    summary_text = f"""
[bold]Analysis Summary[/bold]

📊 [cyan]Components:[/cyan] {summary.get('total_components', 0)}
📁 [cyan]Lines of Code:[/cyan] {summary.get('total_lines_of_code', 0):,}
🔗 [cyan]Relationships:[/cyan] {len(relationships)}
⚡ [cyan]Avg Complexity:[/cyan] {summary.get('average_complexity', 0)}
⚠️  [cyan]High Complexity:[/cyan] {summary.get('high_complexity_components', 0)}

[bold]Component Types:[/bold]
"""

    for comp_type, count in summary.get("component_types", {}).items():
        summary_text += f"  • {comp_type}: {count}\n"

    summary_text += "\n[bold]Architectural Layers:[/bold]\n"
    for layer, count in summary.get("architectural_layers", {}).items():
        summary_text += f"  • {layer}: {count}\n"

    console.print(Panel(summary_text, title="Codebase Analysis Results", expand=False))


def _display_file_summary(
    components: List[CodeComponent], relationships: List[Relationship]
) -> None:
    """Display file analysis summary."""

    if not components:
        return

    file_component = components[0]  # First component should be the file

    summary_text = f"""
[bold]File Analysis Summary[/bold]

📄 [cyan]File:[/cyan] {file_component.name}
📊 [cyan]Components:[/cyan] {len(components)}
📁 [cyan]Lines of Code:[/cyan] {file_component.metrics.lines_of_code}
🔗 [cyan]Relationships:[/cyan] {len(relationships)}
🏷️  [cyan]Tags:[/cyan] {len(file_component.tags.tags)}

[bold]Components Found:[/bold]
"""

    for component in components[1:]:  # Skip file component
        tags_str = ", ".join([tag.name for tag in component.tags.tags])
        comp_type = (
            component.component_type
            if isinstance(component.component_type, str)
            else component.component_type.value
        )
        summary_text += f"  • {comp_type}: {component.name} [{tags_str}]\n"

    console.print(Panel(summary_text, title="File Analysis Results", expand=False))


def _display_table(
    components: List[CodeComponent],
    relationships: List[Relationship],
    include_metrics: bool,
) -> None:
    """Display components in a table format."""

    table = Table(title="Code Components")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Layer", style="green")
    table.add_column("Tags", style="yellow")

    if include_metrics:
        table.add_column("LOC", justify="right", style="blue")
        table.add_column("Complexity", justify="right", style="red")

    for component in components:
        tags_str = ", ".join([tag.name for tag in component.tags.tags])
        layer = component.architectural_layer or "Unknown"

        row = [
            component.name,
            component.component_type
            if isinstance(component.component_type, str)
            else component.component_type.value,
            layer,
            tags_str,
        ]

        if include_metrics:
            row.extend(
                [
                    str(component.metrics.lines_of_code),
                    f"{component.metrics.complexity_score:.1f}",
                ]
            )

        table.add_row(*row)

    console.print(table)


def _display_json(
    components: List[CodeComponent],
    relationships: List[Relationship],
    summary: Dict[str, Any],
) -> None:
    """Display results in JSON format."""

    # Convert components to serializable format
    components_data = []
    for component in components:
        comp_data = {
            "id": str(component.id),
            "name": component.name,
            "type": component.component_type
            if isinstance(component.component_type, str)
            else component.component_type.value,
            "file_path": component.file_path,
            "line_number": component.line_number,
            "tags": [tag.name for tag in component.tags.tags],
            "architectural_layer": component.architectural_layer,
            "metrics": component.metrics.to_dict(),
            "confidence": component.confidence,
        }
        components_data.append(comp_data)

    # Convert relationships to serializable format
    relationships_data = []
    for relationship in relationships:
        rel_data = {
            "id": str(relationship.id),
            "source_id": str(relationship.source_id),
            "target_id": str(relationship.target_id),
            "type": relationship.relationship_type.value,
            "confidence": relationship.confidence,
        }
        relationships_data.append(rel_data)

    result = {
        "summary": summary,
        "components": components_data,
        "relationships": relationships_data,
    }

    console.print(JSON.from_data(result))


def _display_tags_table(tags: List) -> None:
    """Display tags in a table format."""

    table = Table(title="Available Tags")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="magenta")
    table.add_column("Type", style="green")
    table.add_column("Description", style="yellow")

    for tag in tags:
        table.add_row(tag.name, tag.category.value, tag.tag_type.value, tag.description)

    console.print(table)


def _display_tags_json(tags: List) -> None:
    """Display tags in JSON format."""

    tags_data = []
    for tag in tags:
        tag_data = {
            "name": tag.name,
            "category": tag.category.value,
            "type": tag.tag_type.value,
            "description": tag.description,
            "confidence": tag.confidence,
        }
        tags_data.append(tag_data)

    console.print(JSON.from_data(tags_data))


def _save_results(
    output_path: str,
    components: List[CodeComponent],
    relationships: List[Relationship],
    summary: Dict[str, Any],
) -> None:
    """Save analysis results to a JSON file."""

    # Convert to serializable format (reuse JSON display logic)
    components_data = []
    for component in components:
        comp_data = {
            "id": str(component.id),
            "name": component.name,
            "type": component.component_type
            if isinstance(component.component_type, str)
            else component.component_type.value,
            "file_path": component.file_path,
            "line_number": component.line_number,
            "end_line_number": component.end_line_number,
            "tags": [tag.name for tag in component.tags.tags],
            "architectural_layer": component.architectural_layer,
            "primary_role": component.primary_role,
            "metrics": component.metrics.to_dict(),
            "confidence": component.confidence,
            "metadata": component.metadata,
        }
        components_data.append(comp_data)

    relationships_data = []
    for relationship in relationships:
        rel_data = {
            "id": str(relationship.id),
            "source_id": str(relationship.source_id),
            "target_id": str(relationship.target_id),
            "type": relationship.relationship_type.value,
            "confidence": relationship.confidence,
            "metadata": relationship.metadata,
        }
        relationships_data.append(rel_data)

    result = {
        "summary": summary,
        "components": components_data,
        "relationships": relationships_data,
        "metadata": {
            "generated_by": "Generic Hexagonal Architecture Tagging System",
            "version": "0.1.0",
            "timestamp": str(Path().cwd()),  # Simple timestamp placeholder
        },
    }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
