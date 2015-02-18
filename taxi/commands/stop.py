from __future__ import unicode_literals

import datetime

from ..timesheet import NoActivityInProgressError
from ..timesheet.parser import ParseError
from .base import BaseTimesheetCommand


class StopCommand(BaseTimesheetCommand):
    """
    Usage: stop [description]

    Use it when you stop working on the current task. You can add a description
    to what you've done.

    """
    def setup(self):
        if len(self.arguments) == 0:
            self.description = None
        else:
            self.description = ' '.join(self.arguments)

    def run(self):
        try:
            timesheet_collection = self.get_timesheet_collection()
            current_timesheet = timesheet_collection.timesheets[0]
            current_timesheet.continue_entry(
                datetime.date.today(),
                datetime.datetime.now().time(),
                self.description
            )
        except ParseError as e:
            self.view.err(e)
        except NoActivityInProgressError:
            self.view.err("You don't have any activity in progress for today")
        else:
            current_timesheet.file.write(current_timesheet.entries)
