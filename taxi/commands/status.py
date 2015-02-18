from __future__ import unicode_literals

from ..timesheet.parser import ParseError
from .base import BaseTimesheetCommand


class StatusCommand(BaseTimesheetCommand):
    """
    Usage: status

    Shows the summary of what's going to be committed to the server.

    """

    def setup(self):
        self.date = self.options.get('date', None)

    def run(self):
        try:
            timesheet_collection = self.get_timesheet_collection()
        except ParseError as e:
            self.view.err(e)
        else:
            self.view.show_status(
                timesheet_collection.get_entries(self.date, regroup=True),
                self.settings
            )
