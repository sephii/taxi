from __future__ import unicode_literals

import datetime

import click
import six

from ..alias import alias_database
from ..backends import PushEntryFailed
from ..backends.registry import backends_registry
from .base import cli, get_timesheet_collection_for_context, AliasedCommand
from .types import DateRange


@cli.command(cls=AliasedCommand, aliases=['ci'],
             short_help="Commit entries to the backend.")
@click.option('-f', '--file', 'f',
              type=click.Path(exists=True, dir_okay=False),
              help="Path to the file to commit.")
@click.option('-y', '--yes', 'force_yes', is_flag=True,
              help="Don't ask confirmation.")
@click.option('-d', '--date', type=DateRange(),
              help="Only process entries of the given date.")
@click.option('--not-today', is_flag=True,
              help="Ignore today's entries")
@click.pass_context
def commit(ctx, f, force_yes, date, not_today):
    """
    Usage: commit

    Commits your work to the server.

    """
    timesheet_collection = get_timesheet_collection_for_context(ctx, f)
    if not_today:
        yesterday = datetime.date.today() - datetime.timedelta(days=1)

        if not date:
            date = (None, yesterday)
        else:
            date = (date[0], yesterday)

    if not date and not force_yes:
        non_workday_entries = (
            timesheet_collection.get_non_current_workday_entries()
        )

        if non_workday_entries:
            if not ctx.obj['view'].confirm_commit_entries(non_workday_entries):
                ctx.obj['view'].msg("Ok then.")
                return

    ctx.obj['view'].pushing_entries()
    all_pushed_entries = []
    all_failed_entries = []

    for timesheet in timesheet_collection.timesheets:
        pushed_entries = []
        failed_entries = []

        entries_to_push = timesheet.get_entries(
            date, exclude_ignored=True,
            exclude_local=True, exclude_unmapped=True, regroup=True
        )

        for (entries_date, entries) in entries_to_push.items():
            for entry in entries:
                error = None
                backend_name = alias_database[entry.alias].backend
                backend = backends_registry[backend_name]

                try:
                    backend.push_entry(entries_date, entry)
                except PushEntryFailed as e:
                    failed_entries.append(entry)
                    error = six.text_type(e)
                else:
                    pushed_entries.append(entry)
                finally:
                    ctx.obj['view'].pushed_entry(entry, error)

        local_entries = timesheet.get_local_entries(date)
        local_entries_list = []
        for (entries_date, entries) in six.iteritems(local_entries):
            local_entries_list.extend(entries)

        for entry in local_entries_list + pushed_entries:
            entry.commented = True

        for entry in failed_entries:
            entry.fix_start_time()

        # Also fix start time for ignored entries. Since they won't get
        # pushed, there's a chance their previous sibling gets commented
        for (entries_date,
             entries) in timesheet.get_ignored_entries(date).items():
            for entry in entries:
                entry.fix_start_time()

        timesheet.file.write(timesheet.entries)

        all_pushed_entries.extend(pushed_entries)
        all_failed_entries.extend(failed_entries)

    ignored_entries = timesheet_collection.get_ignored_entries(date)
    ignored_entries_list = []
    for (entries_date, entries) in six.iteritems(ignored_entries):
        ignored_entries_list.extend(entries)

    ctx.obj['view'].pushed_entries_summary(
        all_pushed_entries, all_failed_entries, ignored_entries_list
    )
