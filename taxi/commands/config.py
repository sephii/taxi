import click

from .base import cli


@cli.command(short_help="Open configuration file in your editor.")
@click.pass_context
def config(ctx):
    click.edit(filename=ctx.obj["config_path"])
