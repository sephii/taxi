from __future__ import unicode_literals

import click

from ..aliases import aliases_database, Mapping
from ..exceptions import CancelException
from .base import cli


@cli.group(invoke_without_command=True,
           short_help="List and show projects, add aliases for activities.")
@click.option('--backend', '-b', help="Limit search to given backend.")
@click.pass_context
def project(ctx, backend):
    if ctx.invoked_subcommand is None:
        ctx.forward(list_)


@project.command(name='list', short_help="List all projects, optionally"
                                         " filter by name.")
@click.option('--backend', '-b', help="Limit search to given backend.")
@click.argument('search', nargs=-1)
@click.pass_context
def list_(ctx, search, backend):
    """
    Searches for a project by its name. The letter in the first column
    indicates the status of the project: [N]ot started, [A]ctive, [F]inished,
    [C]ancelled.
    """
    projects = ctx.obj['projects_db'].search(search, backend=backend)
    projects = sorted(projects, key=lambda project: project.name.lower())
    ctx.obj['view'].search_results(projects)


@project.command(short_help="Add an alias for a project.")
@click.option('--backend', '-b', help="Limit search to given backend.")
@click.argument('search', nargs=-1)
@click.pass_context
def alias(ctx, search, backend):
    """
    Searches for the given project and interactively add an alias for it.
    """
    projects = ctx.obj['projects_db'].search(search, active_only=True)
    projects = sorted(projects, key=lambda project: project.name)

    if len(projects) == 0:
        ctx.obj['view'].msg(
            "No active project matches your search string '%s'." %
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


@project.command(name='show', short_help="Show the details of the given "
                                         "project id.")
@click.option('--backend', '-b', help="Show project of given backend.")
@click.argument('project_id', type=int)
@click.pass_context
def show(ctx, project_id, backend):
    """
    Shows the details of the given project id.
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
