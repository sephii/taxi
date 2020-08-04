import datetime

import click

from ..exceptions import (
    EntriesCollectionValidationError,
    NoActivityInProgressError,
    ParseError,
    StopInThePastError
)
from .base import cli, get_timesheet_collection_for_context


@cli.command(short_help="Record time spent on an activity.")
@click.argument('description', nargs=-1)
@click.option('-f', '--file', 'f', type=click.Path(dir_okay=False),
              help="Path to the entries file to use.")
@click.pass_context
def stop(ctx, description, f):
    """
    Use it when you stop working on the current task. You can add a description
    to what you've done.
    """
    description = ' '.join(description).strip()
    try:
        timesheet_collection = get_timesheet_collection_for_context(ctx, f)
        current_timesheet = timesheet_collection.latest()
        current_timesheet.continue_entry(
            datetime.date.today(),
            datetime.datetime.now().time(),
            rounded_to_minutes=ctx.obj['settings']['round_entries'],
            description=description or None,
        )
    except (EntriesCollectionValidationError, NoActivityInProgressError, ParseError, StopInThePastError) as e:
        ctx.obj['view'].err(e)
    else:
        current_timesheet.save()
