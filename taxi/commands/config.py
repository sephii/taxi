import click

from .base import cli


@cli.command(short_help="Open configuration file in your editor.")
@click.pass_context
def config(ctx):
    editor = ctx.obj['settings']['editor']
    edit_kwargs = {
        'filename': ctx.obj['settings'].filepath,
    }
    if editor:
        edit_kwargs['editor'] = editor

    click.edit(**edit_kwargs)
