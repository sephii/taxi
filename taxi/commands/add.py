import click

from .base import cli
from .project import alias


@cli.group(invoke_without_command=True)
@click.argument('search', nargs=-1)
@click.pass_context
def add(ctx, search):
    """
    List or manage aliases.
    """
    ctx.obj['view'].warn(
        "Deprecation warning: the `add` command has been superseded by the "
        "`project alias` command and will be removed in the next Taxi version."
    )
    ctx.forward(alias)
