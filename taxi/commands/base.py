from __future__ import unicode_literals

import datetime

import six

from ..exceptions import UsageError
from ..settings import Settings
from ..timesheet import (
    Timesheet, TimesheetCollection, TimesheetFile
)
from ..timesheet.entry import EntriesCollection
from ..utils import file as file_utils
from ..utils.structures import OrderedSet


class BaseCommand(object):
    def __init__(self, app_container):
        self.options = app_container.options
        self.arguments = app_container.arguments
        self.view = app_container.view
        self.projects_db = app_container.projects_db
        self.settings = app_container.settings

    def setup(self):
        pass

    def validate(self):
        pass

    def run(self):
        pass


class BaseTimesheetCommand(BaseCommand):
    def get_timesheet_collection(self, skip_cache=False):
        timesheet_collection = getattr(self, '_current_timesheet_collection',
                                       None)
        if timesheet_collection is not None and not skip_cache:
            return timesheet_collection

        timesheet_collection = TimesheetCollection()

        timesheet_files = self.get_files(
            self.options['unparsed_file'],
            int(self.settings.get('nb_previous_files'))
        )

        for file_path in timesheet_files:
            timesheet_file = TimesheetFile(file_path)
            try:
                timesheet_contents = timesheet_file.read()
            except IOError:
                timesheet_contents = ''

            t = Timesheet(
                EntriesCollection(
                    timesheet_contents,
                    self.settings.get('date_format')
                ),
                timesheet_file
            )

            # Force new entries direction if necessary
            if (self.settings.get('auto_add') in [
                    Settings.AUTO_ADD_OPTIONS['TOP'],
                    Settings.AUTO_ADD_OPTIONS['BOTTOM']]):
                t.entries.add_date_to_bottom = (
                    self.settings.get('auto_add') ==
                    Settings.AUTO_ADD_OPTIONS['BOTTOM']
                )

            timesheet_collection.timesheets.append(t)

        # Fix `add_date_to_bottom` attribute of timesheet entries based on
        # previous timesheets. When a new timesheet is started it won't have
        # any direction defined, so we take the one from the previous
        # timesheet, if any
        previous_timesheet = None
        for timesheet in reversed(timesheet_collection.timesheets):
            if (timesheet.entries.add_date_to_bottom is None
                    and previous_timesheet
                    and previous_timesheet.entries.add_date_to_bottom
                    is not None):
                timesheet.entries.add_date_to_bottom = (
                    previous_timesheet.entries.add_date_to_bottom
                )
            previous_timesheet = timesheet

        setattr(self, '_current_timesheet_collection', timesheet_collection)

        return timesheet_collection

    def get_files(self, filename, nb_previous_files):
        date_units = ['m', 'Y']
        smallest_unit = None

        for date in date_units:
            if '%%%s' % date in filename:
                smallest_unit = date
                break

        if smallest_unit is None:
            return OrderedSet([filename])

        files = OrderedSet()
        file_date = datetime.date.today()
        for i in six.moves.xrange(0, nb_previous_files + 1):
            files.add(file_utils.expand_filename(filename, file_date))

            if smallest_unit == 'm':
                if file_date.month == 1:
                    file_date = file_date.replace(day=1,
                                                  month=12,
                                                  year=file_date.year - 1)
                else:
                    file_date = file_date.replace(day=1,
                                                  month=file_date.month - 1)

            elif smallest_unit == 'Y':
                file_date = file_date.replace(day=1, year=file_date.year - 1)

        return files


class HelpCommand(BaseCommand):
    """
    YO DAWG you asked for help for the help command. Try to search Google in
    Google instead.

    """
    def __init__(self, application_container):
        super(HelpCommand, self).__init__(application_container)
        self.commands_mapping = application_container.commands_mapping

    def setup(self):
        if len(self.arguments) == 0:
            raise UsageError()
        else:
            self.command = self.arguments[0]

    def run(self):
        if self.command == 'help':
            self.view.command_usage(self)
        else:
            if self.command in self.commands_mapping:
                self.view.command_usage(self.commands_mapping[self.command])
            else:
                self.view.err("Command %s doesn't exist." % self.command)
