import click

from .base import cli
from .project import list_


@cli.group(invoke_without_command=True)
@click.argument('search', nargs=-1)
@click.pass_context
def search(ctx, search):
    """
    List or manage aliases.
    """
    ctx.obj['view'].warn(
        "Deprecation warning: the `search` command has been superseded by the "
        "`project list` command and will be removed in the next Taxi version."
    )
    ctx.forward(list_)
