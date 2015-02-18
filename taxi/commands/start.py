from __future__ import unicode_literals

import datetime

from ..exceptions import UsageError
from ..timesheet.entry import TimesheetEntry
from ..timesheet.parser import ParseError
from .base import BaseTimesheetCommand


class StartCommand(BaseTimesheetCommand):
    """
    Usage: start project_name

    Use it when you start working on the project project_name. This will add
    the project name and the current time to your entries file. When you're
    finished, use the stop command.

    """
    def validate(self):
        if len(self.arguments) != 1:
            raise UsageError()

    def setup(self):
        self.project_name = self.arguments[0]

    def run(self):
        today = datetime.date.today()

        try:
            timesheet_collection = self.get_timesheet_collection()
        except ParseError as e:
            self.view.err(e)
            return

        t = timesheet_collection.timesheets[0]

        # If there's a previous entry on the same date, check if we can use its
        # end time as a start time for the newly started entry
        today_entries = t.get_entries(today)
        if(today in today_entries and today_entries[today]
                and isinstance(today_entries[today][-1].duration, tuple)
                and today_entries[today][-1].duration[1] is not None):
            new_entry_start_time = today_entries[today][-1].duration[1]
        else:
            new_entry_start_time = datetime.datetime.now()

        duration = (new_entry_start_time, None)
        e = TimesheetEntry(self.project_name, duration, '?')
        t.entries[today].append(e)
        t.file.write(t.entries)
