from __future__ import unicode_literals

from six.moves.configparser import NoOptionError

from ..settings import Settings
from ..timesheet.parser import ParseError
from ..utils import file as file_utils
from .base import BaseTimesheetCommand


class EditCommand(BaseTimesheetCommand):
    """
    Usage: edit

    Opens your zebra file in your favourite editor.

    """
    def run(self):
        timesheet_collection = None

        try:
            timesheet_collection = self.get_timesheet_collection()
        except ParseError:
            pass

        if timesheet_collection:
            t = timesheet_collection.timesheets[0]

            if (self.settings.get('auto_add') !=
                    Settings.AUTO_ADD_OPTIONS['NO']
                    and not self.options.get('forced_file')):
                auto_fill_days = self.settings.get_auto_fill_days()
                if auto_fill_days:
                    t.prefill(auto_fill_days, limit=None)

                t.file.write(t.entries)

        try:
            editor = self.settings.get('editor')
        except NoOptionError:
            editor = None

        file_utils.spawn_editor(self.options['file'], editor)

        try:
            timesheet_collection = self.get_timesheet_collection(True)
        except ParseError as e:
            self.view.err(e)
        else:
            self.view.show_status(
                timesheet_collection.get_entries(regroup=True),
                self.settings
            )
