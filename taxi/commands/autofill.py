import calendar
import datetime

import click

from .base import cli, get_timesheet_collection_for_context


@cli.command(short_help="Fill the entries file with all dates of the month.")
@click.option('-f', '--file', 'f',
              type=click.Path(dir_okay=False, writable=True))
@click.pass_context
def autofill(ctx, f):
    """
    Fills your timesheet up to today, for the defined auto_fill_days.
    """
    auto_fill_days = ctx.obj['settings']['auto_fill_days']

    if not auto_fill_days:
        ctx.obj['view'].view.err("The parameter `auto_fill_days` must be set "
                                 "to use this command.")
        return

    today = datetime.date.today()
    last_day = calendar.monthrange(today.year, today.month)
    last_date = datetime.date(today.year, today.month, last_day[1])

    timesheet_collection = get_timesheet_collection_for_context(
        ctx, f
    )
    t = timesheet_collection.latest()
    t.prefill(auto_fill_days, last_date)
    t.save()

    ctx.obj['view'].msg("Your entries file has been filled.")
