import datetime
import sys

import click

from .base import cli, get_timesheet_collection_for_context


@cli.command(short_help="Show the current entry in progress.")
@click.option('-f', '--file', 'f',
              type=click.Path(exists=True, dir_okay=False),
              help="Path to the file to check for the entry in progress.")
@click.option('--format', 'format',
              type=str,
              help="Output format. See https://pyformat.info/ for help with"
              " formatting. Available variables: alias, hours, minutes,"
              " description, start_time. Default is \"{alias} {hours:02d}h{minutes:02d}m\".",
              default='{alias} {hours:02d}h{minutes:02d}m')
@click.pass_context
def current(ctx, f, format):
    """
    Show the most recent entry in progress (ie. that doesn't have an end time),
    as created for example with the `start` command. An entry is considered "in
    progress" if it's using a start_time-end_time format and its end_time is set
    to "?". For example:

    alias 15:00-? Description
    """
    timesheet_collection = get_timesheet_collection_for_context(ctx, f)
    current_timesheet = timesheet_collection.latest()

    current_entry = get_entry_in_progress(current_timesheet)

    if not current_entry:
        click.echo("No entry in progress.")
        sys.exit(1)

    current_entry.duration = (current_entry.duration[0], datetime.datetime.now().time())
    total_time_hours = current_entry.hours
    hours, minutes = int(total_time_hours), int(total_time_hours % 1 * 60)
    start_time = current_entry.get_start_time().strftime("%H:%M")

    click.echo(format.format(
        alias=current_entry.alias, hours=hours, minutes=minutes,
        description=current_entry.description, start_time=start_time
    ))


def get_entry_in_progress(timesheet):
    """
    Return the entry in progress for the current date, or `None` if there is no
    such entry.
    """
    today = datetime.date.today()

    try:
        current_entry = timesheet.entries[today][-1]
    except IndexError:
        return None
    else:
        return current_entry if current_entry.in_progress else None
