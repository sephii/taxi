from __future__ import unicode_literals

import click

from ..timesheet.parser import ParseError
from .base import cli, get_timesheet_collection_for_context
from .types import DateRange


@cli.command(short_help="Show a summary of your entries.")
@click.option('-d', '--date', type=DateRange(),
              help="Only show entries of the given date.")
@click.option('-f', '--file', 'f', type=click.Path(dir_okay=False),
              help="Path to the entries file to use.")
@click.pass_context
def status(ctx, date, f):
    """
    Usage: status

    Shows the summary of what's going to be committed to the server.

    """
    try:
        timesheet_collection = get_timesheet_collection_for_context(ctx, f)
    except ParseError as e:
        ctx.obj['view'].err(e)
    else:
        ctx.obj['view'].show_status(
            timesheet_collection.get_entries(
                date, regroup=ctx.obj['settings']['regroup_entries']
            )
        )
