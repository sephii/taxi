from __future__ import unicode_literals

import click

from .base import cli


@cli.command(short_help="Search a project by its name.")
@click.argument('search', nargs=-1)
@click.pass_context
def search(ctx, search):
    """
    Usage: search search_string

    Searches for a project by its name. The letter in the first column
    indicates the status of the project: [N]ot started, [A]ctive, [F]inished,
    [C]ancelled.

    """
    projects = ctx.obj['projects_db'].search(search)
    projects = sorted(projects, key=lambda project: project.name.lower())
    ctx.obj['view'].search_results(projects)
