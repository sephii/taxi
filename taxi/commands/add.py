from __future__ import unicode_literals

import click

from ..aliases import aliases_database, Mapping
from ..exceptions import CancelException
from .base import cli


@cli.command(short_help="Search for a project and add a mapping.")
@click.argument('search', nargs=-1)
@click.pass_context
def add(ctx, search):
    """
    Usage: add search_string

    Searches and prompts for project, activity and alias and adds that as a new
    entry to .taxirc.

    """
    projects = ctx.obj['projects_db'].search(search, active_only=True)
    projects = sorted(projects, key=lambda project: project.name)

    if len(projects) == 0:
        ctx.obj['view'].msg(
            "No active project matches your search string '%s'" %
            ''.join(search)
        )
        return

    ctx.obj['view'].projects_list(projects, True)

    try:
        number = ctx.obj['view'].select_project(projects)
    except CancelException:
        return

    project = projects[number]
    ctx.obj['view'].project_with_activities(project, numbered_activities=True)

    try:
        number = ctx.obj['view'].select_activity(project.activities)
    except CancelException:
        return

    retry = True
    while retry:
        try:
            alias = ctx.obj['view'].select_alias()
        except CancelException:
            return

        if alias in aliases_database:
            mapping = aliases_database[alias]
            overwrite = ctx.obj['view'].overwrite_alias(alias, mapping)

            if not overwrite:
                return
            elif overwrite:
                retry = False
            # User chose "retry"
            else:
                retry = True
        else:
            retry = False

    activity = project.activities[number]
    mapping = Mapping(mapping=(project.id, activity.id),
                      backend=project.backend)
    ctx.obj['settings'].add_alias(alias, mapping)
    ctx.obj['settings'].write_config()

    ctx.obj['view'].alias_added(alias, (project.id, activity.id))
