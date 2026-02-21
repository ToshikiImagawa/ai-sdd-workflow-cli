"""CLI definition for sdd-cli."""

import os
from pathlib import Path

import click


def root_option(f):
    """Common --root option for commands that operate on SDD documents."""
    return click.option(
        "--root",
        type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
        default=lambda: Path(os.environ.get("SDD_ROOT", ".sdd")),
        help="SDD root directory (default: $SDD_ROOT or .sdd)",
    )(f)


class SDDGroup(click.Group):
    """Custom Click group with unified error handling."""

    def invoke(self, ctx):
        try:
            return super().invoke(ctx)
        except click.exceptions.Exit:
            raise
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            ctx.exit(1)


@click.group(cls=SDDGroup)
@click.version_option()
def main():
    """SDD CLI - AI-SDD Workflow Document Management Tool.

    Provides indexing, search, and visualization features for SDD documents.
    """


@main.command()
@root_option
@click.option(
    "--quiet",
    is_flag=True,
    help="Suppress output messages",
)
def index(root, quiet):
    """Build or rebuild the document index.

    Scans all documents in the SDD root directory and creates a full-text
    search index using SQLite FTS5.
    """
    from sdd_cli.commands.index import build_index

    build_index(root, quiet)


@main.command()
@click.argument("query", required=False)
@root_option
@click.option(
    "--feature-id",
    help="Filter by feature ID",
)
@click.option(
    "--tag",
    help="Filter by tag",
)
@click.option(
    "--dir",
    "directory",
    type=click.Choice(["requirement", "specification", "task"]),
    help="Filter by directory type",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (default: text)",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    help="Output file path (default: stdout)",
)
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Maximum number of results (default: 10)",
)
def search(query, root, feature_id, tag, directory, output_format, output, limit):
    """Search SDD documents.

    Performs full-text search across all indexed documents with optional
    filtering by feature ID, tags, or directory type.

    Examples:
        sdd-cli search "ログイン機能"
        sdd-cli search --feature-id user-login
        sdd-cli search "認証" --tag security --dir specification
    """
    from sdd_cli.commands.search import search_documents

    results = search_documents(
        root=root,
        query=query,
        feature_id=feature_id,
        tag=tag,
        directory=directory,
        output_format=output_format,
        limit=limit,
    )

    if output:
        output.write_text(results)
        if output_format == "text":
            click.echo(f"✓ Results written to {output}")
    else:
        click.echo(results)


@main.command()
@root_option
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    help="Output file path for exporting graph JSON",
)
@click.option(
    "--filter-dir",
    type=click.Choice(["requirement", "specification", "task"]),
    help="Only visualize documents in specific directory",
)
@click.option(
    "--feature-id",
    help="Only visualize documents related to specific feature",
)
def visualize(root, output, filter_dir, feature_id):
    """Generate a dependency graph visualization and start an HTML viewer.

    Analyzes document dependencies and starts an interactive HTML viewer
    showing relationships between requirements, specifications, and designs.

    Examples:
        sdd-cli visualize
        sdd-cli visualize --filter-dir specification
        sdd-cli visualize --feature-id user-login
    """
    from sdd_cli.commands.visualize import generate_visualization

    generate_visualization(
        root=root,
        output=output,
        filter_dir=filter_dir,
        feature_id=feature_id,
    )


@main.group()
def cache():
    """Manage cache directories.

    Commands for listing and cleaning cached project indexes.
    """
    pass


@cache.command("list")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (default: text)",
)
def cache_list(output_format):
    """List all cached projects.

    Shows project name, size, last modified time, and document count.

    Examples:
        sdd-cli cache list
        sdd-cli cache list --format json
    """
    from sdd_cli.commands.cache import list_cache_projects_formatted

    click.echo(list_cache_projects_formatted(output_format))


@cache.command("clean")
@click.option(
    "--project",
    help="Project name pattern to delete (supports wildcards like 'my-project*')",
)
@click.option(
    "--all",
    "all_projects",
    is_flag=True,
    help="Delete all cached projects",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without actually deleting",
)
def cache_clean(project, all_projects, dry_run):
    """Clean cache directories.

    Delete cached project indexes to free up disk space.

    Examples:
        # List what would be deleted
        sdd-cli cache clean --all --dry-run

        # Delete specific project
        sdd-cli cache clean --project slide-presentation-app

        # Delete all projects matching pattern
        sdd-cli cache clean --project 'test-*'

        # Delete all cached projects
        sdd-cli cache clean --all
    """
    from sdd_cli.commands.cache import clean_cache

    result = clean_cache(project_pattern=project, all_projects=all_projects, dry_run=dry_run)
    click.echo(result)
