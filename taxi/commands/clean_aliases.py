import click

from .base import cli


@cli.command(name='clean-aliases',
             short_help="Remove aliases mapping to closed or inexistent "
                        "activities.")
@click.option('-y', '--yes', 'force_yes', is_flag=True,
              help="Don't ask confirmation.")
@click.pass_context
def clean_aliases(ctx, force_yes):
    """
    Removes aliases from your config file that point to inactive projects.
    """
    inactive_aliases = []

    for alias, mapping in ctx.obj['settings'].get_aliases().items():
        # Ignore local aliases
        if mapping.mapping is None:
            continue

        project = ctx.obj['projects_db'].get(mapping.mapping[0],
                                             mapping.backend)

        if (project is None or not project.is_active() or
                (mapping.mapping[1] is not None
                 and project.get_activity(mapping.mapping[1]) is None)):
            inactive_aliases.append(((alias, mapping), project))

    if not inactive_aliases:
        ctx.obj['view'].msg("No inactive aliases found.")
        return

    if not force_yes:
        confirm = ctx.obj['view'].clean_inactive_aliases(inactive_aliases)

    if force_yes or confirm:
        ctx.obj['settings'].remove_aliases(
            [item[0] for item in inactive_aliases]
        )
        ctx.obj['settings'].write_config()
        ctx.obj['view'].msg("%d inactive aliases have been successfully"
                            " cleaned." % len(inactive_aliases))
