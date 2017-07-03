from __future__ import unicode_literals

from collections import defaultdict
import datetime
import itertools

import click
import six

from ..aliases import aliases_database
from ..backends import PushEntriesFailed
from ..plugins import plugins_registry
from .base import AliasedCommand, cli, date_options, get_timesheet_collection_for_context, populate_backends


@cli.command(cls=AliasedCommand, aliases=['ci'], short_help="Commit entries to the backend.")
@click.option('-f', '--file', 'f',
              type=click.Path(exists=True, dir_okay=False),
              help="Path to the file to commit.")
@click.option('-y', '--yes', 'force_yes', is_flag=True,
              help="Don't ask confirmation.")
@date_options
@click.pass_context
def commit(ctx, f, force_yes, date):
    """
    Commits your work to the server. The [date] option can be used either as a
    single date (eg. 20.01.2014), as a range (eg. 20.01.2014-22.01.2014), or as
    a range with one of the dates omitted (eg. -22.01.2014).
    """
    populate_backends(ctx.obj['settings'].get_backends())

    timesheet_collection = get_timesheet_collection_for_context(ctx, f)

    if not date and not force_yes:
        non_workday_entries = timesheet_collection.entries.filter(ignored=False, pushed=False, current_workday=False)

        if non_workday_entries:
            if not ctx.obj['view'].confirm_commit_entries(non_workday_entries):
                ctx.obj['view'].msg("Ok then.")
                return

    ctx.obj['view'].pushing_entries()
    backends_entries = defaultdict(list)

    try:
        # Push entries
        for timesheet in timesheet_collection.timesheets:
            entries_to_push = get_entries_to_push(
                timesheet, date, ctx.obj['settings']['regroup_entries']
            )

            for (entries_date, entries) in entries_to_push.items():
                for entry in entries:
                    backend_name = aliases_database[entry.alias].backend
                    backend = plugins_registry.get_backend(backend_name)
                    backends_entries[backend].append(entry)

                    try:
                        backend.push_entry(entries_date, entry)
                    except Exception as e:
                        entry.push_error = six.text_type(e)
                    except KeyboardInterrupt:
                        entry.push_error = ("Interrupted, check status in"
                                            " backend")
                        raise
                    else:
                        entry.push_error = None
                    finally:
                        ctx.obj['view'].pushed_entry(entry)

        # Call post_push_entries on backends
        backends_post_push(backends_entries)
    except KeyboardInterrupt:
        pass
    finally:
        comment_timesheets_entries(timesheet_collection, date)

    ignored_entries = timesheet_collection.entries.filter(date=date, ignored=True, unmapped=False, pushed=False)
    ignored_entries_list = []
    for (entries_date, entries) in six.iteritems(ignored_entries):
        ignored_entries_list.extend(entries)

    all_entries = itertools.chain(*backends_entries.values())
    ctx.obj['view'].pushed_entries_summary(list(all_entries),
                                           ignored_entries_list)


def backends_post_push(backends_entries):
    for backend, entries in six.iteritems(backends_entries):
        try:
            backend.post_push_entries()
        except PushEntriesFailed as e:
            if e.entries:
                for entry, error in six.iteritems(e.entries):
                    entry.push_error = error if error else six.text_type(e)
            else:
                for entry in entries:
                    entry.push_error = six.text_type(e)
        except Exception as e:
            for entry in entries:
                entry.push_error = six.text_type(e)


def comment_timesheets_entries(timesheet_collection, date):
    for timesheet in timesheet_collection.timesheets:
        pushed_entries = get_entries_to_push(timesheet, date)

        for (entries_date, entries) in pushed_entries.items():
            for entry in entries:
                if hasattr(entry, 'push_error') and entry.push_error is None:
                    entry.pushed = True

        timesheet.save()


def get_entries_to_push(timesheet, date, regroup=True):
    return timesheet.entries.filter(date, regroup=regroup, ignored=False, unmapped=False, pushed=False)
