from __future__ import unicode_literals

import datetime

import click

from ..exceptions import ParseError
from ..timesheet import Entry
from .base import cli, get_timesheet_collection_for_context


@cli.command(short_help="Add entry with the current time to the entries file.")
@click.argument('alias')
@click.option('-f', '--file', 'f', type=click.Path(dir_okay=False),
              help="Path to the entries file to use.")
@click.pass_context
def start(ctx, alias, f):
    """
    Use it when you start working on the given activity. This will add the
    activity and the current time to your entries file. When you're finished,
    use the stop command.
    """
    today = datetime.date.today()

    try:
        timesheet_collection = get_timesheet_collection_for_context(ctx, f)
    except ParseError as e:
        ctx.obj['view'].err(e)
        return

    t = timesheet_collection.latest()

    # If there's a previous entry on the same date, check if we can use its
    # end time as a start time for the newly started entry
    today_entries = t.entries.filter(date=today)
    if(today in today_entries and today_entries[today]
            and isinstance(today_entries[today][-1].duration, tuple)
            and today_entries[today][-1].duration[1] is not None):
        new_entry_start_time = today_entries[today][-1].duration[1]
    else:
        new_entry_start_time = datetime.datetime.now()

    duration = (new_entry_start_time, None)
    e = Entry(alias, duration, '?')
    t.entries[today].append(e)
    t.save()
