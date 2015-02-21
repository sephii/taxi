from __future__ import unicode_literals

import click

from .base import cli


@cli.command(short_help="Show the details and activities of a project.")
@click.argument('project_id', type=int)
@click.argument('backend', required=False)
@click.pass_context
def show(ctx, project_id, backend):
    """
    Usage: show project_id [backend]

    Shows the details of the given project_id (you can find it with the search
    command).

    """
    try:
        project = ctx.obj['projects_db'].get(project_id, backend)
    except IOError:
        raise Exception("Error: the projects database file doesn't exist. "
                        "Please run `taxi update` to create it")

    if project is None:
        ctx.obj['view'].err(
            "Could not find project `%s`" % (project_id)
        )
    else:
        ctx.obj['view'].project_with_activities(project)
