from __future__ import unicode_literals

import click

from ..aliases import aliases_database, Mapping
from ..projects import Project
from .base import cli


@cli.command(short_help="Show aliases or add a mapping.")
@click.argument('alias', required=False)
@click.argument('mapping', required=False)
@click.argument('backend', required=False)
@click.pass_context
def alias(ctx, alias, mapping, backend):
    """
    Usage: alias [alias]
           alias [project_id]
           alias [project_id/activity_id]
           alias [alias] [project_id/activity_id] [backend]

    - The first form will display the mappings whose aliases start with the
      search string you entered
    - The second form will display the mapping(s) you've defined for this
      project and all of its activities
    - The third form will display the mapping you've defined for this exact
      project/activity tuple
    - The last form will add a new alias in your configuration file

    You can also run this command without any argument to view all your
    mappings.

    """
    if all([alias, mapping, backend]):
        add_mapping(ctx, alias, mapping, backend)
    elif alias:
        show_mapping(ctx, alias)
    else:
        show_alias(ctx, alias)


def add_mapping(ctx, alias, mapping, backend):
    mapping = Project.str_to_tuple(mapping)
    if mapping is None:
        raise click.UsageError(
            "The mapping must be in the format xxx/yyy"
        )

    mapping = Mapping(mapping=mapping, backend=backend)

    if alias in aliases_database:
        existing_mapping = aliases_database[alias]
        confirm = ctx.obj['view'].view.overwrite_alias(
            alias, existing_mapping, False
        )

        if not confirm:
            return

    ctx.obj['settings'].add_alias(alias, mapping)
    ctx.obj['settings'].write_config()

    ctx.obj['view'].alias_added(alias, mapping.mapping)


def show_mapping(ctx, mapping_str):
    mapping = Project.str_to_tuple(mapping_str)

    if mapping is not None:
        for alias, m in aliases_database.filter_from_mapping(mapping).items():
            ctx.obj['view'].mapping_detail(
                (alias, m.mapping if m is not None else None),
                ctx.obj['projects_db'].get(m.mapping[0], m.backend)
                if m is not None else None
            )
    else:
        show_alias(ctx, mapping_str)


def show_alias(ctx, alias):
    for alias, m in aliases_database.filter_from_alias(alias).items():
        ctx.obj['view'].alias_detail(
            (alias, m.mapping if m is not None else None),
            ctx.obj['projects_db'].get(m.mapping[0], m.backend)
            if m is not None else None
        )
