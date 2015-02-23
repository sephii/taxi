from __future__ import unicode_literals

import click
import six

from ..aliases import Mapping
from ..backends.registry import backends_registry
from .base import cli


@cli.command(short_help="Fetch projects and shared aliases from backends.")
@click.pass_context
def update(ctx):
    """
    Usage: update

    Synchronizes your project database with the server and updates the shared
    aliases.

    """
    ctx.obj['view'].updating_projects_database()

    projects = []

    for backend_name, backend_uri in ctx.obj['settings'].get_backends():
        backend = backends_registry[backend_name]
        backend_projects = backend.get_projects()

        for project in backend_projects:
            project.backend = backend_name

        projects += backend_projects

    ctx.obj['projects_db'].update(projects)

    # Put the shared aliases in the config file
    shared_aliases = {}
    backends_to_clear = set()
    for project in projects:
        if project.is_active():
            for alias, activity_id in six.iteritems(project.aliases):
                mapping = Mapping(mapping=(project.id, activity_id),
                                  backend=project.backend)
                shared_aliases[alias] = mapping
                backends_to_clear.add(project.backend)

    for backend in backends_to_clear:
        ctx.obj['settings'].clear_shared_aliases(backend)

    for alias, mapping in shared_aliases.items():
        ctx.obj['settings'].add_shared_alias(alias, mapping)

    aliases_after_update = ctx.obj['settings'].get_aliases()

    ctx.obj['settings'].write_config()

    ctx.obj['view'].projects_database_update_success(
        aliases_after_update, ctx.obj['projects_db']
    )
