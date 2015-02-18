from __future__ import unicode_literals

import six

from ..alias import alias_database
from ..backends import PushEntryFailed
from ..backends.registry import backends_registry
from .base import BaseTimesheetCommand


class CommitCommand(BaseTimesheetCommand):
    """
    Usage: commit

    Commits your work to the server.

    """
    def run(self):
        timesheet_collection = self.get_timesheet_collection()

        if (self.options.get('date', None) is None
                and not self.options.get('ignore_date_error', False)):
            non_workday_entries = (
                timesheet_collection.get_non_current_workday_entries()
            )

            if non_workday_entries:
                self.view.non_working_dates_commit_error(
                    non_workday_entries.keys()
                )

                return

        self.view.pushing_entries()
        all_pushed_entries = []
        all_failed_entries = []

        for timesheet in timesheet_collection.timesheets:
            pushed_entries = []
            failed_entries = []

            entries_to_push = timesheet.get_entries(
                self.options.get('date', None), exclude_ignored=True,
                exclude_local=True, exclude_unmapped=True, regroup=True
            )

            for (date, entries) in entries_to_push.items():
                for entry in entries:
                    error = None
                    backend_name = alias_database[entry.alias].backend
                    backend = backends_registry[backend_name]

                    try:
                        backend.push_entry(date, entry)
                    except PushEntryFailed as e:
                        failed_entries.append(entry)
                        error = e.message
                    else:
                        pushed_entries.append(entry)
                    finally:
                        self.view.pushed_entry(entry, error)

            local_entries = timesheet.get_local_entries(
                self.options.get('date', None)
            )
            local_entries_list = []
            for (date, entries) in six.iteritems(local_entries):
                local_entries_list.extend(entries)

            for entry in local_entries_list + pushed_entries:
                entry.commented = True

            for (entry, _) in failed_entries:
                entry.fix_start_time()

            # Also fix start time for ignored entries. Since they won't get
            # pushed, there's a chance their previous sibling gets commented
            for (date, entries) in timesheet.get_ignored_entries().items():
                for entry in entries:
                    entry.fix_start_time()

            timesheet.file.write(timesheet.entries)

            all_pushed_entries.extend(pushed_entries)
            all_failed_entries.extend(failed_entries)

        ignored_entries = timesheet_collection.get_ignored_entries(
            self.options.get('date', None)
        )
        ignored_entries_list = []
        for (date, entries) in six.iteritems(ignored_entries):
            ignored_entries_list.extend(entries)

        self.view.pushed_entries_summary(all_pushed_entries,
                                         all_failed_entries,
                                         ignored_entries_list)
