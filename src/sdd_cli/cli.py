"""CLI definition for sdd-cli."""

from pathlib import Path

import click


def root_option(f):
    """Common --root option for commands that operate on SDD documents."""
    return click.option(
        "--root",
        type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
        default=lambda: Path.cwd(),
        help="Project root directory (default: current directory)",
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
    "--env",
    is_flag=True,
    help="Output export statements for SDD environment variables (for eval)",
)
def init(root, env):
    """Initialize SDD project.

    Creates .sdd-config.json under the project root.

    With --env, outputs shell export statements to stdout so that
    environment variables can be set via: eval $(sdd-cli init --env)

    Examples:
        sdd-cli init
        sdd-cli init --root /path/to/project
        eval $(sdd-cli init --env)
    """
    from sdd_cli.commands.init import initialize_project

    initialize_project(root, env=env)


@main.command()
@root_option
@click.option("--json", "json_output", is_flag=True, default=False, help="Output results in JSON format")
@click.option("--quiet", is_flag=True, default=False, help="Suppress output when no issues found")
def lint(root, json_output, quiet):
    """Run static analysis on SDD documents.

    Checks for circular dependencies, broken links, missing required fields,
    and ID integrity issues in .sdd/ documents.

    Examples:
        sdd-cli lint
        sdd-cli lint --json
        sdd-cli lint --root /path/to/project --quiet
    """
    from sdd_cli.commands.lint import run_lint

    output, has_errors = run_lint(root, json_output, quiet)
    if output:
        click.echo(output)
    if has_errors:
        raise SystemExit(1)


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
    "--filter",
    "filter_strs",
    multiple=True,
    help='Filter by metadata field: "field:op:value" (op: exact/contains/regex). Repeatable.',
)
@click.option(
    "--or",
    "or_operator",
    is_flag=True,
    default=False,
    help="Combine --filter conditions with OR (default: AND)",
)
@click.option(
    "--parent",
    help="Retrieve all descendant documents of the specified parent feature_id",
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
def search(query, root, feature_id, tag, directory, filter_strs, or_operator, parent, output_format, output, limit):
    """Search SDD documents.

    Performs full-text search across all indexed documents with optional
    filtering by feature ID, tags, or directory type.

    Examples:
        sdd-cli search "authentication"
        sdd-cli search --feature-id user-login
        sdd-cli search "login" --tag security --dir specification
        sdd-cli search --filter "status:exact:approved"
        sdd-cli search --filter "type:exact:spec" --filter "type:exact:design" --or
        sdd-cli search --parent document-search
    """
    from sdd_cli.commands.search import _parse_filter, search_documents
    from sdd_cli.types import FilterCondition

    # Parse --filter strings into FilterCondition list
    filters: list[FilterCondition] = []
    for f in filter_strs:
        filters.append(_parse_filter(f))

    results = search_documents(
        root=root,
        query=query,
        feature_id=feature_id,
        tag=tag,
        directory=directory,
        filters=filters or None,
        or_operator=or_operator,
        parent=parent,
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
