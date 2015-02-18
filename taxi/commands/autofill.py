from __future__ import unicode_literals

import calendar
import datetime

from .base import BaseTimesheetCommand


class AutofillCommand(BaseTimesheetCommand):
    """
    Usage: autofill

    Fills your timesheet up to today, for the defined auto_fill_days.

    """
    def run(self):
        auto_fill_days = self.settings.get_auto_fill_days()

        if auto_fill_days:
            today = datetime.date.today()
            last_day = calendar.monthrange(today.year, today.month)
            last_date = datetime.date(today.year, today.month, last_day[1])

            timesheet_collection = self.get_timesheet_collection()
            t = timesheet_collection.timesheets[0]
            t.prefill(auto_fill_days, last_date)
            t.file.write(t.entries)

            self.view.msg("Your entries file has been filled.")
        else:
            self.view.err("The parameter `auto_fill_days` must be set to "
                          "use this command.")
